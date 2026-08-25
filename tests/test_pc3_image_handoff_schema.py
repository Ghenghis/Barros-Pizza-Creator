from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts" / "pc3-image-handoff.schema.json"


class Pc3ImageHandoffSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_identity_and_version_are_locked(self) -> None:
        self.assertEqual(self.schema["$id"], "barros-pc3-image-handoff-v1")
        self.assertEqual(
            self.schema["properties"]["schema_version"]["const"],
            "1.0",
        )
        item = self.schema["properties"]["items"]["items"]
        self.assertEqual(item["properties"]["kind"]["const"], "barros-pc3-image-handoff")

    def test_truth_states_cannot_promote_unknown_values(self) -> None:
        item = self.schema["properties"]["items"]["items"]
        states = item["properties"]["proof"]["properties"]["state"]["enum"]
        self.assertEqual(states, ["not_run", "pass", "fail", "blocked"])

    def test_hash_and_image_contract_requirements_are_strict(self) -> None:
        item = self.schema["properties"]["items"]["items"]
        candidate = item["properties"]["candidate_input"]
        self.assertEqual(candidate["required"], ["path", "sha256"])
        self.assertEqual(candidate["properties"]["sha256"]["pattern"], "^[a-fA-F0-9]{64}$")

        image = self.schema["$defs"]["imageContract"]
        for field in (
            "source_path",
            "source_name",
            "width",
            "height",
            "source_format",
            "mode",
            "has_alpha",
            "sha256",
        ):
            self.assertIn(field, image["required"])
        self.assertEqual(image["properties"]["sha256"]["pattern"], "^[a-fA-F0-9]{64}$")

    def test_target_metadata_has_pc3_mapping_fields(self) -> None:
        item = self.schema["properties"]["items"]["items"]
        target = item["properties"]["target"]["properties"]
        self.assertEqual(set(target), {"asset_id", "relative_path", "path_id", "family", "usage"})


if __name__ == "__main__":
    unittest.main()
