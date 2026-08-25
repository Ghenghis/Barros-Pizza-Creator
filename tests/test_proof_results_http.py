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


class ProofResultsHttpTests(unittest.TestCase):
    def _contract(self) -> dict:
        return json.loads((ROOT / "contracts" / "rc1.acceptance.json").read_text(encoding="utf-8"))

    def _contract_results(self, state: str = "not_run") -> list[dict]:
        rows: list[dict] = []
        for layer in self._contract()["layers"]:
            for gate in layer["gates"]:
                rows.append({
                    "gate_id": gate["id"],
                    "state": state,
                    "release_required": gate["release_required"],
                    "evidence": [],
                })
        return rows

    @staticmethod
    def _counts(results: list[dict]) -> dict[str, int]:
        return {
            state: sum(1 for row in results if row["state"] == state)
            for state in ("pass", "fail", "blocked", "not_run")
        }

    def _get(self, results_payload: dict | None = None, create_evidence: bool = False) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as folder:
            package = Path(folder) / "BarrosAI"
            backend = package / "backend"
            backend.mkdir(parents=True)
            settings = backend / "settings.json"
            settings.write_text('{"provider":"offline"}', encoding="utf-8")
            contract_dir = package / "contracts"
            contract_dir.mkdir(parents=True)
            contract = self._contract()
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

    def test_no_retained_results_stays_not_run_and_contract_bound(self) -> None:
        code, body = self._get()
        self.assertEqual(200, code)
        self.assertTrue(body["ok"])
        self.assertFalse(body["available"])
        self.assertEqual("not_run", body["certification"]["state"])
        self.assertFalse(body["certification"]["runtime_certified"])
        self.assertTrue(body["proof_binding"]["contract_validated"])
        self.assertGreater(body["proof_binding"]["contract_gate_count"], 0)
        self.assertGreater(body["proof_binding"]["contract_release_required_gate_count"], 0)

    def test_all_stage_complete_results_can_report_runtime_certified(self) -> None:
        results = self._contract_results("pass")
        payload = {
            "contract_id": "barros-pc3-rc1",
            "release": "1.1.0-rc1",
            "run_id": "20260825T090000Z",
            "stage": "All",
            "game_root": r"S:\Unity_Games\PC3 - Pizza Creator",
            "package_root": r"S:\Barros-Pizza-Creator",
            "counts": self._counts(results),
            "results": results,
        }
        code, body = self._get(payload, create_evidence=True)
        self.assertEqual(200, code)
        self.assertTrue(body["available"])
        self.assertEqual("pass", body["certification"]["state"])
        self.assertTrue(body["certification"]["runtime_certified"])
        self.assertEqual(len(results), body["proof_binding"]["contract_gate_count"])
        expected_required = sum(1 for row in results if row["release_required"])
        self.assertEqual(expected_required, body["release_required_pass_count"])
        self.assertEqual(expected_required, body["proof_binding"]["contract_release_required_gate_count"])
        self.assertEqual([], body["missing_referenced_evidence"])

    def test_static_results_never_promote_runtime_certification(self) -> None:
        results = self._contract_results("not_run")
        results[0]["state"] = "pass"
        payload = {
            "contract_id": "barros-pc3-rc1",
            "release": "1.1.0-rc1",
            "run_id": "20260825T090001Z",
            "stage": "Static",
            "counts": self._counts(results),
            "results": results,
        }
        code, body = self._get(payload, create_evidence=True)
        self.assertEqual(200, code)
        self.assertEqual("not_run", body["certification"]["state"])
        self.assertFalse(body["certification"]["runtime_certified"])

    def test_count_mismatch_fails_closed(self) -> None:
        results = self._contract_results("pass")
        counts = self._counts(results)
        counts["pass"] += 1
        payload = {
            "contract_id": "barros-pc3-rc1",
            "release": "1.1.0-rc1",
            "run_id": "20260825T090002Z",
            "stage": "All",
            "counts": counts,
            "results": results,
        }
        code, body = self._get(payload, create_evidence=True)
        self.assertEqual(500, code)
        self.assertFalse(body["ok"])
        self.assertIn("count mismatch", body["error"])

    def test_missing_contract_gate_fails_closed(self) -> None:
        results = self._contract_results("pass")
        removed = results.pop()
        payload = {
            "contract_id": "barros-pc3-rc1",
            "release": "1.1.0-rc1",
            "run_id": "20260825T090003Z",
            "stage": "All",
            "counts": self._counts(results),
            "results": results,
        }
        code, body = self._get(payload, create_evidence=True)
        self.assertEqual(500, code)
        self.assertFalse(body["ok"])
        self.assertIn("missing contract gates", body["error"])
        self.assertIn(removed["gate_id"], body["error"])

    def test_release_required_tampering_fails_closed(self) -> None:
        results = self._contract_results("pass")
        target = next(row for row in results if row["release_required"] is True)
        target["release_required"] = False
        payload = {
            "contract_id": "barros-pc3-rc1",
            "release": "1.1.0-rc1",
            "run_id": "20260825T090004Z",
            "stage": "All",
            "counts": self._counts(results),
            "results": results,
        }
        code, body = self._get(payload, create_evidence=True)
        self.assertEqual(500, code)
        self.assertFalse(body["ok"])
        self.assertIn("release_required does not match", body["error"])

    def test_unknown_or_duplicate_gate_fails_closed(self) -> None:
        unknown_results = self._contract_results("pass")
        unknown_results[0]["gate_id"] = "FAKE-999"
        payload = {
            "contract_id": "barros-pc3-rc1",
            "release": "1.1.0-rc1",
            "run_id": "20260825T090005Z",
            "stage": "All",
            "counts": self._counts(unknown_results),
            "results": unknown_results,
        }
        code, body = self._get(payload, create_evidence=True)
        self.assertEqual(500, code)
        self.assertFalse(body["ok"])
        self.assertIn("unknown contract gate", body["error"])

        duplicate_results = self._contract_results("pass")
        duplicate_results[1]["gate_id"] = duplicate_results[0]["gate_id"]
        payload = {
            "contract_id": "barros-pc3-rc1",
            "release": "1.1.0-rc1",
            "run_id": "20260825T090006Z",
            "stage": "All",
            "counts": self._counts(duplicate_results),
            "results": duplicate_results,
        }
        code, body = self._get(payload, create_evidence=True)
        self.assertEqual(500, code)
        self.assertFalse(body["ok"])
        self.assertIn("duplicate gate_id", body["error"])


if __name__ == "__main__":
    unittest.main()
