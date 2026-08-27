#!/usr/bin/env python3
"""Compare two canonical PC3 Creator controlled stimulus fixtures.

This consumes the shared `contracts/creator-controlled-stimulus.schema.json` shape used
by both Creator and Runtime Proof Studio. It does not generate stimuli; Studio owns the
canonical E00-E10 corpus generator.

The report separates evidence-label differences (`case_id`, `notes`) from actual model
and operation changes and normalizes placement indexes to `[*]` field families.
Optional `--allow` globs make the command fail closed when a supposedly one-variable
pair changes unexpected model/operation fields.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


PROFILE = "creator-0.11.272"
EVIDENCE_ONLY_FIELDS = {"case_id", "notes"}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_fixture(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    validate_fixture(value)
    return value


def validate_vector(value: Any, path: str) -> None:
    if not isinstance(value, dict) or set(value) != {"x", "y", "z"}:
        raise ValueError(f"{path} must contain exactly x/y/z")
    for axis in ("x", "y", "z"):
        if not isinstance(value[axis], (int, float)) or isinstance(value[axis], bool):
            raise ValueError(f"{path}.{axis} must be numeric")


def validate_fixture(value: Dict[str, Any]) -> None:
    required = {"schema_version", "experiment_id", "case_id", "runtime_profile", "model", "operation"}
    allowed = required | {"notes"}
    if not isinstance(value, dict):
        raise ValueError("fixture root must be an object")
    extra = set(value) - allowed
    missing = required - set(value)
    if missing or extra:
        raise ValueError(f"fixture root missing={sorted(missing)} extra={sorted(extra)}")
    if value["schema_version"] != "1.0":
        raise ValueError("schema_version must be 1.0")
    if value["runtime_profile"] != PROFILE:
        raise ValueError(f"runtime_profile must be {PROFILE}")
    if not isinstance(value["experiment_id"], str) or not value["experiment_id"]:
        raise ValueError("experiment_id must be non-empty")
    if not isinstance(value["case_id"], str) or not value["case_id"]:
        raise ValueError("case_id must be non-empty")

    model = value["model"]
    model_required = {"name", "shape", "profit_factor", "placements"}
    if not isinstance(model, dict) or set(model) != model_required:
        raise ValueError("model must contain exactly name/shape/profit_factor/placements")
    if not isinstance(model["name"], str) or not 1 <= len(model["name"]) <= 54:
        raise ValueError("model.name length must be 1..54")
    if model["shape"] not in {"Round", "Square", "Star", "Triangle"}:
        raise ValueError("invalid model.shape")
    if not isinstance(model["profit_factor"], (int, float)) or isinstance(model["profit_factor"], bool):
        raise ValueError("model.profit_factor must be numeric")
    if not 0.0 <= float(model["profit_factor"]) <= 2.0:
        raise ValueError("model.profit_factor must be 0..2")
    placements = model["placements"]
    if not isinstance(placements, list) or len(placements) > 180:
        raise ValueError("model.placements must be an array with <=180 items")
    for index, placement in enumerate(placements):
        expected = {"ingredient_id", "size", "position", "rotation"}
        if not isinstance(placement, dict) or set(placement) != expected:
            raise ValueError(f"model.placements[{index}] has wrong fields")
        if not isinstance(placement["ingredient_id"], str) or not placement["ingredient_id"]:
            raise ValueError(f"model.placements[{index}].ingredient_id must be non-empty")
        if placement["size"] not in {"Large", "Medium", "Small"}:
            raise ValueError(f"model.placements[{index}].size invalid")
        validate_vector(placement["position"], f"model.placements[{index}].position")
        validate_vector(placement["rotation"], f"model.placements[{index}].rotation")

    operation = value["operation"]
    operation_fields = {"preview_exact_model", "native_recipe_save", "reload_verify", "native_resave_after_reload"}
    if not isinstance(operation, dict) or set(operation) != operation_fields:
        raise ValueError("operation has wrong fields")
    if not all(isinstance(operation[key], bool) for key in operation_fields):
        raise ValueError("all operation fields must be boolean")


def structural_diff(a: Any, b: Any, path: str = "") -> List[str]:
    if type(a) is not type(b):
        return [path or "$root"]
    if isinstance(a, dict):
        changes: List[str] = []
        for key in sorted(set(a) | set(b)):
            child = f"{path}.{key}" if path else key
            if key not in a or key not in b:
                changes.append(child)
            else:
                changes.extend(structural_diff(a[key], b[key], child))
        return changes
    if isinstance(a, list):
        changes = []
        if len(a) != len(b):
            changes.append(f"{path}.length")
        for index, (left, right) in enumerate(zip(a, b)):
            changes.extend(structural_diff(left, right, f"{path}[{index}]"))
        return changes
    return [path or "$root"] if a != b else []


def normalized_path(path: str) -> str:
    output = path
    start = 0
    while True:
        pos = output.find("placements[", start)
        if pos < 0:
            break
        end = output.find("]", pos)
        if end < 0:
            break
        output = output[:pos] + "placements[*]" + output[end + 1:]
        start = pos + len("placements[*]")
    return output


def is_evidence_only(path: str) -> bool:
    return path in EVIDENCE_ONLY_FIELDS


def matches_allowed(path: str, allowed: Sequence[str]) -> bool:
    normalized = normalized_path(path)
    # ``placements[*]`` is our literal normalized family token. Python's
    # fnmatch otherwise interprets ``[*]`` as a character class and fails to
    # match the brackets present in the normalized path itself.
    return any(normalized == pattern or fnmatch.fnmatchcase(normalized, pattern) for pattern in allowed)


def compare(a: Dict[str, Any], b: Dict[str, Any], allowed: Sequence[str]) -> Dict[str, Any]:
    paths = structural_diff(a, b)
    evidence = [path for path in paths if is_evidence_only(path)]
    substantive = [path for path in paths if not is_evidence_only(path)]
    unexpected = [path for path in substantive if allowed and not matches_allowed(path, allowed)]
    return {
        "all_changed_fields": paths,
        "evidence_label_changed_fields": evidence,
        "substantive_changed_fields": substantive,
        "substantive_changed_field_families": sorted({normalized_path(path) for path in substantive}),
        "allowed_patterns": list(allowed),
        "unexpected_substantive_changes": unexpected,
        "allowed_check_applied": bool(allowed),
        "allowed_check_pass": bool(allowed) and not unexpected,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture_a", type=Path)
    parser.add_argument("fixture_b", type=Path)
    parser.add_argument("--allow", action="append", default=[], help="Allowed substantive field glob, e.g. model.placements[*].rotation.y")
    parser.add_argument("--out", type=Path, default=Path("stimulus-diff.json"))
    args = parser.parse_args()

    a = load_fixture(args.fixture_a)
    b = load_fixture(args.fixture_b)
    result = compare(a, b, args.allow)
    report = {
        "schema_version": "1.0",
        "kind": "pc3-creator-controlled-stimulus-diff",
        "runtime_profile": PROFILE,
        "a": {
            "path": str(args.fixture_a.resolve()),
            "experiment_id": a["experiment_id"],
            "case_id": a["case_id"],
            "sha256": sha256_json(a),
        },
        "b": {
            "path": str(args.fixture_b.resolve()),
            "experiment_id": b["experiment_id"],
            "case_id": b["case_id"],
            "sha256": sha256_json(b),
        },
        "comparison": result,
        "truth_note": "Stimulus-input comparison only. It does not prove native runtime application or JPEG behavior.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(args.out.resolve()), "comparison": result}, indent=2))
    if args.allow and not result["allowed_check_pass"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
