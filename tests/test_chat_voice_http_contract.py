from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.server import App, Handler, ThreadingHTTPServer  # noqa: E402


class CreatorChatVoiceHTTPTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = json.loads(
            (ROOT / "backend" / "catalog.bootstrap.json").read_text(encoding="utf-8")
        )["ingredients"]

    def _server(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        settings = root / "settings.json"
        settings.write_text('{"provider":"offline"}', encoding="utf-8")
        app = App(root, settings)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.app = app
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return temp, server

    def _post(self, base: str, path: str, payload: dict) -> dict:
        request = urllib.request.Request(
            base + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return json.load(urllib.request.urlopen(request))

    def test_chat_endpoint_uses_catalog_and_retains_chat_history(self) -> None:
        temp, server = self._server()
        try:
            base = f"http://127.0.0.1:{server.server_address[1]}"
            response = self._post(base, "/chat", {
                "prompt": "Arizona chicken pizza for Casa Grande",
                "catalog": self.catalog,
                "constraints": {"max_ingredients": 8},
            })
            self.assertTrue(response["ok"])

            history = json.load(urllib.request.urlopen(base + "/history"))["entries"]
            self.assertEqual("chat", history[-1]["mode"])
            self.assertEqual("Arizona chicken pizza for Casa Grande", history[-1]["prompt"])
        finally:
            server.shutdown()
            server.server_close()
            temp.cleanup()

    def test_transcribe_fails_closed_when_stt_is_not_configured(self) -> None:
        temp, server = self._server()
        try:
            base = f"http://127.0.0.1:{server.server_address[1]}"
            request = urllib.request.Request(
                base + "/transcribe",
                data=json.dumps({"filename": "voice.wav", "audio_base64": "UklGRg=="}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request)
            self.assertEqual(400, caught.exception.code)
            payload = json.loads(caught.exception.read().decode("utf-8"))
            self.assertFalse(payload["ok"])
            self.assertIn("transcription", payload["error"].lower())
        finally:
            server.shutdown()
            server.server_close()
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
