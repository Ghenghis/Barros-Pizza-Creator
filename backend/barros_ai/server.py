from __future__ import annotations

import base64
import hmac
import json
import os
import threading
import time
from collections import defaultdict, deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .attachments import AttachmentError, normalize_attachment, normalize_attachments
from .history import HistoryStore
from .inspiration import InspirationLibrary
from .music import MusicLibrary
from .orchestrator import PizzaOrchestrator
from .proof_status import ProofStatusError, latest_proof_status
from .providers import ProviderClient, ProviderError, ProviderSettings
from .remote_bridge import LocalRemoteInbox, RemoteBridgeStore
from .tts import AzureSpeechService


MAX_BODY = 16 * 1024 * 1024
TRUTH_STATES = ("not_run", "pass", "fail", "blocked")


class App:
    def __init__(self, root: Path, settings_path: Path):
        self.root = root
        self.settings_path = settings_path
        self.settings = ProviderSettings.load(settings_path)
        self.provider = ProviderClient(self.settings)
        self.inspiration = InspirationLibrary(root / "data" / "inspiration")
        self.orchestrator = PizzaOrchestrator(self.provider, self.inspiration)
        self.tts = AzureSpeechService(self.settings)
        assets_root = root.parent / "assets" if (root.parent / "assets").is_dir() else root / "assets"
        self.music = MusicLibrary(assets_root / "music")
        self.history = HistoryStore(root / "data" / "conversation_history.json")
        self.remote_bridge = RemoteBridgeStore(root / "data" / "remote_bridge.json")
        self.remote_inbox = LocalRemoteInbox()
        self.api_token = os.getenv("BARROS_API_TOKEN", "").strip()
        configured_origins = os.getenv("BARROS_ALLOWED_ORIGINS", "").strip()
        self.allowed_origins = {
            item.strip().rstrip("/")
            for item in configured_origins.split(",")
            if item.strip()
        }
        if not self.allowed_origins:
            self.allowed_origins = {
                "http://127.0.0.1",
                "http://localhost",
                "http://127.0.0.1:48173",
                "http://localhost:48173",
            }
        self.rate_limit = max(10, min(int(os.getenv("BARROS_RATE_LIMIT_PER_MINUTE", "120")), 2000))
        self.rate_windows: dict[str, deque[float]] = defaultdict(deque)
        self.rate_lock = threading.Lock()
        self.started = time.time()
        self.server: ThreadingHTTPServer | None = None

    def reload(self) -> None:
        self.settings = ProviderSettings.load(self.settings_path)
        self.provider = ProviderClient(self.settings)
        self.orchestrator = PizzaOrchestrator(self.provider, self.inspiration)
        self.tts = AzureSpeechService(self.settings)

    def _contract_path(self) -> Path:
        """Resolve the RC contract in source and installed layouts.

        ``backend/main.py`` deliberately passes the backend directory as the App
        root. In a source checkout the contract is therefore one level above it;
        the installer mirrors that layout as ``BarrosAI/backend`` plus
        ``BarrosAI/contracts``. Keeping both candidates also supports focused
        tests that construct an App directly at a temporary package root.
        """
        candidates = (
            self.root / "contracts" / "rc1.acceptance.json",
            self.root.parent / "contracts" / "rc1.acceptance.json",
        )
        for path in candidates:
            if path.is_file():
                return path
        checked = ", ".join(str(path) for path in candidates)
        raise ValueError(f"Acceptance contract not found; checked: {checked}")

    def contract_status(self) -> dict[str, Any]:
        """Expose the static acceptance contract without fabricating runtime proof.

        The Creator sidecar can prove what contract is installed and what gates it
        requires. It cannot infer that Windows/game runtime gates passed merely
        because the contract file exists, so certification remains explicitly
        not evaluated here. Authoritative PASS promotion still belongs to the
        proof harness with retained evidence.
        """
        path = self._contract_path()
        contract = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(contract, dict):
            raise ValueError("Acceptance contract root must be a JSON object.")

        layers = contract.get("layers")
        if not isinstance(layers, list):
            raise ValueError("Acceptance contract layers must be a JSON array.")

        gates: list[dict[str, Any]] = []
        layer_summary: list[dict[str, Any]] = []
        for layer in layers:
            if not isinstance(layer, dict):
                raise ValueError("Acceptance contract layers must contain JSON objects.")
            layer_gates = layer.get("gates")
            if not isinstance(layer_gates, list) or not all(isinstance(row, dict) for row in layer_gates):
                raise ValueError("Acceptance contract gates must be a JSON array of objects.")
            gates.extend(layer_gates)
            layer_summary.append({
                "id": layer.get("id", ""),
                "name": layer.get("name", ""),
                "runs_on": layer.get("runs_on", ""),
                "gate_count": len(layer_gates),
            })

        counts = {state: 0 for state in TRUTH_STATES}
        counts["unknown"] = 0
        for gate in gates:
            state = str(gate.get("state", "not_run")).lower()
            counts[state if state in counts else "unknown"] += 1
        required = [gate for gate in gates if bool(gate.get("release_required", True))]

        return {
            "ok": True,
            "contract_id": contract.get("contract_id", ""),
            "schema_version": contract.get("schema_version", ""),
            "release": contract.get("release", ""),
            "target": contract.get("target", {}),
            "truth_policy": contract.get("truth_policy", {}),
            "layers": layer_summary,
            "gate_count": len(gates),
            "release_required_gate_count": len(required),
            "declared_states": counts,
            "certification": {
                "state": "not_evaluated",
                "runtime_certified": False,
                "source": "static_acceptance_contract",
                "reason": (
                    "Static contract metadata does not prove live Windows/game behavior. "
                    "Runtime certification requires the proof harness and retained evidence."
                ),
            },
        }

    def latest_proof_status(self) -> dict[str, Any]:
        contract = self.contract_status()
        return latest_proof_status(self.root, str(contract.get("contract_id", "")))


class Handler(BaseHTTPRequestHandler):
    server_version = "BarrosPizzaAI/1.6.1"

    @property
    def app(self) -> App:
        return self.server.app  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:
        print("[%s] %s" % (self.log_date_time_string(), fmt % args), flush=True)

    def _json(self, status: int, payload: Any) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        origin = self._allowed_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(raw)

    def _allowed_origin(self) -> str:
        origin = self.headers.get("Origin", "").rstrip("/")
        if not origin:
            return ""
        if origin in self.app.allowed_origins:
            return origin
        return ""

    def _authorized(self) -> bool:
        if not self.app.api_token:
            return True
        supplied = self.headers.get("Authorization", "")
        if supplied.lower().startswith("bearer "):
            supplied = supplied[7:].strip()
        else:
            supplied = self.headers.get("X-Barros-Token", "").strip()
        return bool(supplied) and hmac.compare_digest(supplied, self.app.api_token)

    def _rate_allowed(self) -> bool:
        address = self.client_address[0] if self.client_address else "unknown"
        now = time.monotonic()
        with self.app.rate_lock:
            window = self.app.rate_windows[address]
            while window and now - window[0] >= 60:
                window.popleft()
            if len(window) >= self.app.rate_limit:
                return False
            window.append(now)
        return True

    def _guard(self, public: bool = False) -> bool:
        origin = self.headers.get("Origin", "").rstrip("/")
        if origin and not self._allowed_origin():
            self._json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "This web origin is not allowed."})
            return False
        if not self._rate_allowed():
            self._json(HTTPStatus.TOO_MANY_REQUESTS, {"ok": False, "error": "Too many requests. Try again shortly."})
            return False
        if not public and not self._authorized():
            self._json(HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "A valid Barro's access token is required."})
            return False
        return True

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0 or length > MAX_BODY:
            raise ValueError("Request body must be between 1 byte and 16 MB.")
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Request JSON must be an object.")
        return payload

    def _file(self, path: Path) -> None:
        content_type = {".ogg": "audio/ogg", ".mp3": "audio/mpeg", ".wav": "audio/wav", ".mp4": "video/mp4"}.get(path.suffix.casefold(), "application/octet-stream")
        size = path.stat().st_size
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                self.wfile.write(chunk)

    def do_OPTIONS(self) -> None:  # noqa: N802
        if self.headers.get("Origin") and not self._allowed_origin():
            self._json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "This web origin is not allowed."})
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        origin = self._allowed_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Barros-Token")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._guard(public=path == "/health"):
            return
        if path.startswith("/music/playback/"):
            track = self.app.music.resolve_track(unquote(path[len("/music/playback/"):]))
            if track is None:
                self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Music track not found."})
            else:
                try:
                    self._file(self.app.music.prepare_playback(track))
                except RuntimeError as exc:
                    self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"ok": False, "error": str(exc)})
            return
        if path == "/health":
            stt = self.app.provider.stt_status()
            stt_configured = bool(stt["configured"])
            inspiration = self.app.inspiration.status()
            self._json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "name": "Barro's AI Pizza Designer",
                    "version": "1.6.1",
                    "mobile_api": "1.0.0",
                    "provider": self.app.settings.provider,
                    "online": self.app.provider.online,
                    "image_parser": "png+jpeg+webp-v1",
                    "capabilities": {
                        "compose": True,
                        "chat": True,
                        "lab": True,
                        "crew": True,
                        "history": True,
                        "reload": True,
                        "attachment_inspection": True,
                        "contract": True,
                        "proof_results": True,
                        "ingredient_intelligence": True,
                        "inspiration_library": True,
                        "pizza_art": True,
                        "stt_configured": stt_configured,
                        "tts_configured": self.app.tts.configured,
                        "remote_pairing": True,
                        "windows_bridge": True,
                    },
                    "inspiration": inspiration,
                    "stt": stt,
                    "tts": self.app.tts.status(),
                    "music": self.app.music.status(),
                    "uptime_seconds": round(time.time() - self.app.started, 1),
                },
            )
            return
        if path == "/catalog":
            catalog_path = self.app.root / "catalog.bootstrap.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8-sig"))
            self._json(HTTPStatus.OK, {"ok": True, "catalog": catalog})
            return
        if path == "/remote/latest":
            self._json(HTTPStatus.OK, self.app.remote_inbox.pop())
            return
        if path == "/inspiration":
            self._json(HTTPStatus.OK, {"ok": True, **self.app.inspiration.status()})
            return
        if path == "/contract":
            try:
                self._json(HTTPStatus.OK, self.app.contract_status())
            except (ValueError, json.JSONDecodeError) as exc:
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})
            return
        if path == "/proof/latest":
            try:
                self._json(HTTPStatus.OK, self.app.latest_proof_status())
            except (ValueError, ProofStatusError, json.JSONDecodeError) as exc:
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})
            return
        if path == "/history":
            self._json(HTTPStatus.OK, {"ok": True, "entries": self.app.history.read()})
            return
        self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Unknown endpoint."})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not self._guard():
            return
        try:
            payload = self._body()
            if path == "/pairing/bridge/register":
                self._json(HTTPStatus.OK, self.app.remote_bridge.register_bridge(payload.get("name")))
                return
            if path == "/pairing/connect":
                self._json(
                    HTTPStatus.OK,
                    self.app.remote_bridge.connect(payload.get("pair_code"), payload.get("device_name")),
                )
                return
            if path == "/bridge/jobs":
                self._json(
                    HTTPStatus.OK,
                    self.app.remote_bridge.enqueue(
                        payload.get("pair_token"), payload.get("payload"), payload.get("action")
                    ),
                )
                return
            if path == "/bridge/jobs/next":
                self._json(
                    HTTPStatus.OK,
                    self.app.remote_bridge.next_job(payload.get("bridge_id"), payload.get("bridge_secret")),
                )
                return
            if path == "/bridge/jobs/ack":
                self._json(
                    HTTPStatus.OK,
                    self.app.remote_bridge.acknowledge(
                        payload.get("bridge_id"),
                        payload.get("bridge_secret"),
                        payload.get("job_id"),
                        payload.get("state"),
                        payload.get("detail"),
                    ),
                )
                return
            if path == "/remote/import":
                self._json(HTTPStatus.OK, self.app.remote_inbox.push(payload))
                return
            if path == "/inspect-attachment":
                attachment = normalize_attachment(payload)
                public = {
                    "name": attachment.get("name", "attachment"),
                    "mime_type": attachment.get("mime_type", ""),
                    "image_metadata": attachment.get("image_metadata"),
                    "text_chars": len(str(attachment.get("text", ""))),
                }
                self._json(HTTPStatus.OK, {"ok": True, "attachment": public})
                return
            if path in {"/compose", "/chat", "/lab"}:
                payload["attachments"] = normalize_attachments(payload.get("attachments") or [])
                if path == "/lab":
                    payload["count"] = 3
                result = self.app.orchestrator.compose(payload)
                self.app.history.append(path[1:], str(payload.get("prompt", "")), result)
                self._json(HTTPStatus.OK, result)
                return
            if path == "/crew":
                payload["attachments"] = normalize_attachments(payload.get("attachments") or [])
                result = self.app.orchestrator.crew(payload)
                self.app.history.append("crew", str(payload.get("prompt", "")), result)
                self._json(HTTPStatus.OK, result)
                return
            if path == "/transcribe":
                encoded = str(payload.get("audio_base64", ""))
                if not encoded:
                    raise ValueError("audio_base64 is required.")
                if not self.app.provider.stt_configured:
                    raise ProviderError("Voice transcription is not configured in settings.json.")
                text = self.app.provider.transcribe(base64.b64decode(encoded), str(payload.get("filename", "voice.wav")))
                self._json(HTTPStatus.OK, {"ok": True, "text": text})
                return
            if path == "/speak":
                audio, profile, clean = self.app.tts.synthesize(
                    str(payload.get("agent", "")),
                    str(payload.get("message", "")),
                    str(payload.get("voice", "")),
                    float(payload.get("rate", 1.0)),
                )
                self._json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "agent": profile.agent,
                        "voice": profile.voice,
                        "locale": profile.locale,
                        "label": profile.label,
                        "spoken_text": clean,
                        "mime_type": "audio/wav",
                        "audio_base64": base64.b64encode(audio).decode("ascii"),
                    },
                )
                return
            if path == "/reload":
                self.app.reload()
                self._json(HTTPStatus.OK, {"ok": True, "provider": self.app.settings.provider})
                return
            if path == "/music/refresh":
                self._json(HTTPStatus.OK, self.app.music.refresh())
                return
            if path == "/shutdown":
                self._json(HTTPStatus.OK, {"ok": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Unknown endpoint."})
        except (ValueError, AttachmentError, json.JSONDecodeError, ProviderError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
        except Exception as exc:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)})


def run(root: Path, settings_path: Path, host: str = "127.0.0.1", port: int = 48173) -> None:
    app = App(root, settings_path)
    if host not in {"127.0.0.1", "localhost", "::1"} and not app.api_token:
        raise RuntimeError("BARROS_API_TOKEN is required when listening beyond the local computer.")
    server = ThreadingHTTPServer((host, port), Handler)
    server.app = app  # type: ignore[attr-defined]
    app.server = server
    print("Barro's AI Pizza Designer listening on http://%s:%d (%s)" % (host, port, app.settings.provider), flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
