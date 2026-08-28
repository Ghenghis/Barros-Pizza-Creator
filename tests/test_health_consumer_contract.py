from __future__ import annotations

import json
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.server import App, Handler, ThreadingHTTPServer  # noqa: E402


REQUIRED_CAPABILITIES = {
    "compose",
    "chat",
    "lab",
    "crew",
    "history",
    "reload",
    "attachment_inspection",
    "contract",
    "proof_results",
}


def _health(settings_payload: dict) -> dict:
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        settings = root / "settings.json"
        settings.write_text(json.dumps(settings_payload), encoding="utf-8")
        app = App(root, settings)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.app = app
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            return json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/health"))
        finally:
            server.shutdown()
            server.server_close()


def test_health_matches_workbench_and_studio_consumer_contract() -> None:
    health = _health({"provider": "offline"})

    assert health["ok"] is True
    assert health["version"] == "1.6.1"
    assert health["provider"] == "offline"
    assert health["online"] is False
    assert REQUIRED_CAPABILITIES.issubset(health["capabilities"])
    assert all(health["capabilities"][name] is True for name in REQUIRED_CAPABILITIES)
    assert isinstance(health["capabilities"]["stt_configured"], bool)

    stt = health["stt"]
    assert isinstance(stt["configured"], bool)
    assert isinstance(stt["dedicated_endpoint_configured"], bool)
    assert stt["configured"] is health["capabilities"]["stt_configured"]
    assert stt["reachability"] == "not_probed"
    assert isinstance(stt["model"], str) and stt["model"]
    assert "available" not in stt
    assert "endpoint" not in stt


def test_health_consumer_contract_preserves_configured_vs_reachable_boundary() -> None:
    health = _health({
        "provider": "offline",
        "stt_endpoint": "https://private.example.test/v1/audio/transcriptions",
        "stt_model": "whisper-test",
    })

    assert health["capabilities"]["stt_configured"] is True
    assert health["stt"]["configured"] is True
    assert health["stt"]["dedicated_endpoint_configured"] is True
    assert health["stt"]["reachability"] == "not_probed"
