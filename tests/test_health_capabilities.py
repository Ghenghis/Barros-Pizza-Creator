from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.server import App, Handler, ThreadingHTTPServer  # noqa: E402


class CreatorHealthCapabilityTests(unittest.TestCase):
    def _health(self, settings_payload: dict) -> dict:
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

    def test_health_advertises_chat_and_safe_offline_stt_status(self) -> None:
        health = self._health({"provider": "offline"})
        self.assertTrue(health["ok"])
        self.assertTrue(health["capabilities"]["chat"])
        self.assertTrue(health["capabilities"]["compose"])
        self.assertFalse(health["capabilities"]["stt"])
        self.assertFalse(health["stt"]["available"])
        self.assertFalse(health["stt"]["configured_endpoint"])
        self.assertEqual("whisper-1", health["stt"]["model"])

    def test_health_reports_explicit_stt_endpoint_without_exposing_url(self) -> None:
        health = self._health({
            "provider": "offline",
            "stt_endpoint": "https://private.example.test/v1/audio/transcriptions",
            "stt_model": "whisper-test",
        })
        self.assertTrue(health["capabilities"]["stt"])
        self.assertTrue(health["stt"]["available"])
        self.assertTrue(health["stt"]["configured_endpoint"])
        self.assertEqual("whisper-test", health["stt"]["model"])
        self.assertNotIn("endpoint", health["stt"])


if __name__ == "__main__":
    unittest.main()
