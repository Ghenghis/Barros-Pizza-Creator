from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "ecosystem.release.acceptance.json"
ALLOWED_STATES = {"not_run", "pass", "fail", "blocked"}
EXPECTED_GATES = {f"REL-{index:03d}" for index in range(1, 9)}
PORTABLE_CI_PASS_GATES = {"REL-004", "REL-005"}
EXPECTED_REFERENCED_CONTRACTS = {
    "creator_rc1": "contracts/rc1.acceptance.json",
    "ecosystem_base": "contracts/ecosystem.acceptance.json",
    "image_handoff": "contracts/ecosystem.image.acceptance.json",
}


class EcosystemReleaseContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))

    def test_overlay_identifies_exact_release_line_and_runtime_profiles(self) -> None:
        payload = self.payload
        self.assertEqual("barros-pc3-ecosystem-release-v2", payload["contract_id"])
        self.assertEqual(
            {
                "creator": "1.2.0-rc1",
                "workbench": "2.3.0-rc1",
                "studio": "1.2.0-rc1",
            },
            payload["release_versions"],
        )
        self.assertEqual("creator-0.11.272", payload["runtime_profiles"]["creator"])
        self.assertEqual("studio-1.11.403", payload["runtime_profiles"]["studio"])

    def test_referenced_contracts_resolve_inside_repository(self) -> None:
        referenced = self.payload["referenced_contracts"]
        self.assertEqual(EXPECTED_REFERENCED_CONTRACTS, referenced)
        repository_root = ROOT.resolve()
        for name, relative in referenced.items():
            with self.subTest(name=name):
                path = (repository_root / relative).resolve()
                self.assertTrue(
                    path.is_relative_to(repository_root),
                    f"Referenced contract escapes repository root: {path}",
                )
                self.assertTrue(path.is_file(), f"Referenced contract does not exist: {path}")

    def test_release_gates_are_unique_required_and_truth_safe(self) -> None:
        gates = self.payload["gates"]
        self.assertEqual(8, len(gates))
        self.assertEqual(EXPECTED_GATES, {row["id"] for row in gates})
        self.assertEqual(len(gates), len({row["id"] for row in gates}))
        for row in gates:
            with self.subTest(gate=row["id"]):
                self.assertTrue(row["release_required"])
                self.assertIn(row["state"], ALLOWED_STATES)
                evidence = str(row.get("evidence", "")).strip()
                self.assertTrue(evidence)

                if row["state"] == "pass":
                    self.assertIn(
                        row["id"],
                        PORTABLE_CI_PASS_GATES,
                        "Live/runtime-dependent gates must never be pre-promoted by the canonical source contract.",
                    )
                    self.assertRegex(
                        evidence,
                        re.compile(r"\b[0-9a-f]{40}\b"),
                        "A persisted portable PASS must name the exact reviewed commit SHA.",
                    )
                    self.assertIn(
                        "PASS",
                        evidence,
                        "A persisted portable PASS must name retained successful workflow evidence.",
                    )

    def test_truth_policy_requires_retained_and_live_visual_evidence(self) -> None:
        truth = self.payload["truth_policy"]
        self.assertEqual(sorted(ALLOWED_STATES), sorted(truth["states"]))
        self.assertIn("retained evidence", truth["rule"].lower())
        self.assertIn("100% complete", truth["promotion"].lower())
        self.assertIn("live", truth["snapshot_rule"].lower())
        self.assertIn("screenshots", truth["snapshot_rule"].lower())


if __name__ == "__main__":
    unittest.main()
