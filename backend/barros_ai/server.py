from __future__ import annotations

import base64
import json
import os
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .attachments import AttachmentError, normalize_attachment, normalize_attachments
from .history import HistoryStore
from .orchestrator import PizzaOrchestrator
from .proof_status import ProofStatusError, latest_proof_status
from .providers import ProviderClient, ProviderError, ProviderSettings


MAX_BODY = 16 * 1024 * 1024
TRUTH_STATES = ("not_run", "pass", "fail", "blocked")


class App:
    def __init__(self, root: Path, settings_path: Path):
        self.root = root
        self.settings_path = settings_path
        self.settings = ProviderSettings.load(settings_path)
        self.provider = ProviderClient(self.settings)
        self.orchestrator = PizzaOrchestrator(self.provider)
        self.history = HistoryStore(root / "data" / "conversation_history.json")
        self.started = time.time()
        self.server: ThreadingHTTPServer | None = None

    def reload(self) -> None:
        self.settings = ProviderSettings.load(self.settings_path)
        self.provider = ProviderClient(self.settings)
        self.orchestrator = PizzaOrchestrator(self.provider)

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
    server_version = "BarrosPizzaAI/1.1"

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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0 or length > MAX_BODY:
            raise ValueError("Request body must be between 1 byte and 16 MB.")
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Request JSON must be an object.")
        return payload

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            stt_configured = bool(self.app.provider.online or self.app.settings.stt_endpoint)
            self._json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "name": "Barro's AI Pizza Designer",
                    "version": "1.2.0-rc2",
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
                        "stt_configured": stt_configured,
                    },
                    "stt": {
                        "configured": stt_configured,
                        "dedicated_endpoint_configured": bool(self.app.settings.stt_endpoint),
                        "model": self.app.settings.stt_model,
                        "reachability": "not_probed",
                    },
                    "uptime_seconds": round(time.time() - self.app.started, 1),
                },
            )
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
        try:
            payload = self._body()
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
                if not self.app.provider.online and not self.app.settings.stt_endpoint:
                    raise ProviderError("Voice transcription needs an OpenAI-compatible or configured STT endpoint.")
                text = self.app.provider.transcribe(base64.b64decode(encoded), str(payload.get("filename", "voice.wav")))
                self._json(HTTPStatus.OK, {"ok": True, "text": text})
                return
            if path == "/reload":
                self.app.reload()
                self._json(HTTPStatus.OK, {"ok": True, "provider": self.app.settings.provider})
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
    server = ThreadingHTTPServer((host, port), Handler)
    server.app = app  # type: ignore[attr-defined]
    app.server = server
    print("Barro's AI Pizza Designer listening on http://%s:%d (%s)" % (host, port, app.settings.provider), flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
