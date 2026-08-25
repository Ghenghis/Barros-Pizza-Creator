from __future__ import annotations

import base64
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

from barros_ai.attachments import AttachmentError, inspect_image_bytes, normalize_attachment  # noqa: E402
from barros_ai.server import App, Handler, ThreadingHTTPServer  # noqa: E402


# Minimal structural JPEG sufficient to prove SOF dimension parsing. The parser
# is metadata-oriented and never decodes pixels; provider-side vision receives
# the original bytes after this contract check.
def fake_jpeg(width: int, height: int) -> bytes:
    sof_payload = (
        b"\x08"
        + height.to_bytes(2, "big")
        + width.to_bytes(2, "big")
        + b"\x01\x01\x11\x00"
    )
    sof = b"\xff\xc0" + (len(sof_payload) + 2).to_bytes(2, "big") + sof_payload
    return b"\xff\xd8" + sof + b"\xff\xd9"


def fake_png(width: int, height: int) -> bytes:
    # Parser needs the authoritative PNG signature + IHDR dimensions. Extra
    # bytes model later chunks without adding a third-party image dependency.
    return (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\x0dIHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x06\x00\x00\x00"
        + b"\x00\x00\x00\x00"
    )


class AttachmentParserTests(unittest.TestCase):
    def test_jpeg_sof_dimensions_and_sha_are_parsed(self) -> None:
        raw = fake_jpeg(640, 360)
        result = inspect_image_bytes(raw)
        self.assertEqual("image/jpeg", result["mime_type"])
        self.assertEqual("JPEG", result["format"])
        self.assertEqual((640, 360), (result["width"], result["height"]))
        self.assertEqual(64, len(result["sha256"]))

    def test_png_dimensions_are_parsed(self) -> None:
        result = inspect_image_bytes(fake_png(512, 256))
        self.assertEqual("image/png", result["mime_type"])
        self.assertEqual((512, 256), (result["width"], result["height"]))

    def test_declared_jpeg_cannot_hide_png_bytes(self) -> None:
        attachment = {
            "name": "reference.jpg",
            "mime_type": "image/jpeg",
            "data_base64": base64.b64encode(fake_png(32, 16)).decode("ascii"),
        }
        with self.assertRaisesRegex(AttachmentError, "does not match decoded"):
            normalize_attachment(attachment)

    def test_invalid_base64_is_rejected(self) -> None:
        with self.assertRaisesRegex(AttachmentError, "not valid base64"):
            normalize_attachment({
                "name": "bad.jpg",
                "mime_type": "image/jpeg",
                "data_base64": "%%%not-base64%%%",
            })

    def test_inspect_attachment_endpoint_returns_metadata_not_raw_image(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            settings = root / "settings.json"
            settings.write_text('{"provider":"offline"}', encoding="utf-8")
            app = App(root, settings)
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            server.app = app
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                port = server.server_address[1]
                payload = {
                    "name": "reference.jpeg",
                    "mime_type": "image/jpeg",
                    "data_base64": base64.b64encode(fake_jpeg(800, 450)).decode("ascii"),
                }
                request = urllib.request.Request(
                    f"http://127.0.0.1:{port}/inspect-attachment",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                response = json.load(urllib.request.urlopen(request))
                self.assertTrue(response["ok"])
                self.assertEqual(800, response["attachment"]["image_metadata"]["width"])
                self.assertEqual(450, response["attachment"]["image_metadata"]["height"])
                self.assertNotIn("data_base64", response["attachment"])
            finally:
                server.shutdown()
                server.server_close()

    def test_inspect_endpoint_returns_400_for_mime_spoof(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            settings = root / "settings.json"
            settings.write_text('{"provider":"offline"}', encoding="utf-8")
            app = App(root, settings)
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            server.app = app
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                port = server.server_address[1]
                payload = {
                    "name": "spoof.jpg",
                    "mime_type": "image/jpeg",
                    "data_base64": base64.b64encode(fake_png(20, 10)).decode("ascii"),
                }
                request = urllib.request.Request(
                    f"http://127.0.0.1:{port}/inspect-attachment",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(request)
                self.assertEqual(400, caught.exception.code)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
