from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.remote_bridge import LocalRemoteInbox, RemoteBridgeStore  # noqa: E402
from barros_ai.server import App  # noqa: E402


class MobileCompanionTests(unittest.TestCase):
    def test_web_manifest_and_required_offline_files_exist(self) -> None:
        manifest = json.loads((ROOT / "web" / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual("standalone", manifest["display"])
        self.assertEqual("/", manifest["start_url"])
        for name in ("index.html", "styles.css", "app.js", "sw.js"):
            self.assertTrue((ROOT / "web" / name).is_file(), name)

    def test_android_release_has_verified_link_contract(self) -> None:
        android_manifest = (ROOT / "android" / "app" / "src" / "main" / "AndroidManifest.xml").read_text(encoding="utf-8")
        self.assertIn("creator.daveai.tech", android_manifest)
        self.assertIn("android:autoVerify=\"true\"", android_manifest)
        asset_links = json.loads((ROOT / "web" / ".well-known" / "assetlinks.json").read_text(encoding="utf-8"))
        self.assertEqual("tech.daveai.barroscreator", asset_links[0]["target"]["package_name"])

    def test_remote_bridge_pair_send_poll_ack(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            store = RemoteBridgeStore(Path(folder) / "bridge.json")
            bridge = store.register_bridge("Test Windows")
            pair = store.connect(bridge["pair_code"], "Tab S9+")
            payload = {"ok": True, "recipes": [{"name": "Mobile Pizza", "ingredients": []}]}
            queued = store.enqueue(pair["pair_token"], payload)
            delivered = store.next_job(bridge["bridge_id"], bridge["bridge_secret"])
            self.assertEqual(queued["job_id"], delivered["job"]["job_id"])
            done = store.acknowledge(bridge["bridge_id"], bridge["bridge_secret"], queued["job_id"], "completed", "test")
            self.assertEqual("completed", done["state"])

    def test_local_inbox_is_one_time_handoff(self) -> None:
        inbox = LocalRemoteInbox()
        inbox.push({"recipes": [{"name": "Remote"}]})
        self.assertEqual("Remote", inbox.pop()["recipes"][0]["name"])
        self.assertEqual([], inbox.pop()["recipes"])

    def test_nonlocal_listener_requires_token(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            settings = root / "settings.json"
            settings.write_text('{"provider":"offline"}', encoding="utf-8")
            previous = os.environ.pop("BARROS_API_TOKEN", None)
            try:
                app = App(root, settings)
                self.assertEqual("", app.api_token)
            finally:
                if previous is not None:
                    os.environ["BARROS_API_TOKEN"] = previous

    def test_deployment_has_no_committed_secret(self) -> None:
        compose = (ROOT / "deploy" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("BARROS_API_TOKEN", compose)
        self.assertNotIn("sk-", compose)
        self.assertNotIn("Access-Control-Allow-Origin\", \"*", (ROOT / "backend" / "barros_ai" / "server.py").read_text(encoding="utf-8"))

    def test_mobile_release_builder_excludes_runtime_state(self) -> None:
        builder = (ROOT / "scripts" / "build_mobile_release.ps1").read_text(encoding="utf-8")
        self.assertIn('backend\\data', builder)
        self.assertIn('__pycache__', builder)
        self.assertIn('conversation_history.json', builder)
        self.assertIn('remote_bridge.json', builder)
        self.assertIn('Packaging stopped', builder)


if __name__ == "__main__":
    unittest.main()
