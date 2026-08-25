from __future__ import annotations

import json
import re
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.server import App, Handler, ThreadingHTTPServer  # noqa: E402


class LiveContractHttpTests(unittest.TestCase):
    def _get(self, path: str) -> dict:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            settings = root / "settings.json"
            settings.write_text('{"provider":"offline"}', encoding="utf-8")
            contract_dir = root / "contracts"
            contract_dir.mkdir(parents=True)
            (contract_dir / "rc1.acceptance.json").write_text(
                (ROOT / "contracts" / "rc1.acceptance.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            app = App(root, settings)
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            server.app = app
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                port = server.server_address[1]
                return json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}{path}"))
            finally:
                server.shutdown()
                server.server_close()

    def test_health_advertises_contract_surface(self) -> None:
        health = self._get("/health")
        self.assertTrue(health["capabilities"]["contract"])

    def test_contract_surface_is_truth_safe_and_target_specific(self) -> None:
        status = self._get("/contract")
        self.assertTrue(status["ok"])
        self.assertEqual("barros-pc3-rc1", status["contract_id"])
        self.assertEqual("0.11.272", status["target"]["game_version"])
        self.assertEqual(24, status["gate_count"])
        self.assertEqual(24, status["release_required_gate_count"])
        self.assertEqual(24, status["declared_states"]["not_run"])
        self.assertEqual("not_evaluated", status["certification"]["state"])
        self.assertFalse(status["certification"]["runtime_certified"])
        self.assertIn("retained evidence", status["certification"]["reason"])

    def test_rc1_contract_release_matches_product_version(self) -> None:
        contract = json.loads((ROOT / "contracts" / "rc1.acceptance.json").read_text(encoding="utf-8"))
        version_text = (ROOT / "VERSION.txt").read_text(encoding="utf-8")
        match = re.search(r"^Version:\s*(\S+)\s*$", version_text, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), contract["release"])


if __name__ == "__main__":
    unittest.main()
