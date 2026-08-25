from __future__ import annotations

import json
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.server import App, Handler, ThreadingHTTPServer  # noqa: E402


class ProofResultsHttpTests(unittest.TestCase):
    def _get(self, results_payload: dict | None = None, create_evidence: bool = False) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as folder:
            package = Path(folder) / "BarrosAI"
            backend = package / "backend"
            backend.mkdir(parents=True)
            settings = backend / "settings.json"
            settings.write_text('{"provider":"offline"}', encoding="utf-8")
            contract_dir = package / "contracts"
            contract_dir.mkdir(parents=True)
            contract = json.loads((ROOT / "contracts" / "rc1.acceptance.json").read_text(encoding="utf-8"))
            (contract_dir / "rc1.acceptance.json").write_text(json.dumps(contract), encoding="utf-8")

            if results_payload is not None:
                run_root = package / "evidence" / "runs" / str(results_payload.get("run_id", "run"))
                run_root.mkdir(parents=True)
                if create_evidence:
                    evidence = run_root / "proof.log"
                    evidence.write_text("proof", encoding="utf-8")
                    for row in results_payload.get("results", []):
                        if row.get("state") == "pass":
                            row["evidence"] = [str(evidence)]
                (run_root / "results.json").write_text(json.dumps(results_payload), encoding="utf-8")

            app = App(backend, settings)
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            server.app = app
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                port = server.server_address[1]
                try:
                    response = urllib.request.urlopen(f"http://127.0.0.1:{port}/proof/latest")
                    return response.status, json.load(response)
                except urllib.error.HTTPError as exc:
                    return exc.code, json.loads(exc.read().decode("utf-8"))
            finally:
                server.shutdown()
                server.server_close()

    def test_no_retained_results_stays_not_run(self) -> None:
        code, body = self._get()
        self.assertEqual(200, code)
        self.assertTrue(body["ok"])
        self.assertFalse(body["available"])
        self.assertEqual("not_run", body["certification"]["state"])
        self.assertFalse(body["certification"]["runtime_certified"])

    def test_all_stage_complete_results_can_report_runtime_certified(self) -> None:
        results = [
            {"gate_id": "A", "state": "pass", "release_required": True, "evidence": []},
            {"gate_id": "B", "state": "pass", "release_required": True, "evidence": []},
        ]
        payload = {
            "contract_id": "barros-pc3-rc1",
            "release": "1.1.0-rc1",
            "run_id": "20260825T090000Z",
            "stage": "All",
            "game_root": r"S:\Unity_Games\PC3 - Pizza Creator",
            "package_root": r"S:\Barros-Pizza-Creator",
            "counts": {"pass": 2, "fail": 0, "blocked": 0, "not_run": 0},
            "results": results,
        }
        code, body = self._get(payload, create_evidence=True)
        self.assertEqual(200, code)
        self.assertTrue(body["available"])
        self.assertEqual("pass", body["certification"]["state"])
        self.assertTrue(body["certification"]["runtime_certified"])
        self.assertEqual(2, body["release_required_pass_count"])
        self.assertEqual([], body["missing_referenced_evidence"])

    def test_static_results_never_promote_runtime_certification(self) -> None:
        payload = {
            "contract_id": "barros-pc3-rc1",
            "release": "1.1.0-rc1",
            "run_id": "20260825T090001Z",
            "stage": "Static",
            "counts": {"pass": 1, "fail": 0, "blocked": 0, "not_run": 0},
            "results": [{"gate_id": "SRC-001", "state": "pass", "release_required": True, "evidence": []}],
        }
        code, body = self._get(payload, create_evidence=True)
        self.assertEqual(200, code)
        self.assertEqual("not_run", body["certification"]["state"])
        self.assertFalse(body["certification"]["runtime_certified"])

    def test_count_mismatch_fails_closed(self) -> None:
        payload = {
            "contract_id": "barros-pc3-rc1",
            "release": "1.1.0-rc1",
            "run_id": "20260825T090002Z",
            "stage": "All",
            "counts": {"pass": 99, "fail": 0, "blocked": 0, "not_run": 0},
            "results": [{"gate_id": "A", "state": "pass", "release_required": True, "evidence": []}],
        }
        code, body = self._get(payload, create_evidence=True)
        self.assertEqual(500, code)
        self.assertFalse(body["ok"])
        self.assertIn("count mismatch", body["error"])


if __name__ == "__main__":
    unittest.main()
