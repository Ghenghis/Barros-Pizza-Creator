#!/usr/bin/env python3
"""Generate controlled PC3 Creator native-JPEG research fixtures.

Input: a canonical exact-placement fixture JSON matching
`docs/NATIVE_JPEG_EXPERIMENT_HARNESS_SPEC.md`.

Supported experiment families:
- E01 rotation sweep
- E02 X sweep
- E03 Z sweep
- E04 Y sweep
- E05 two-piece order/Y factorial variants
- E09 A/B/C/D same-ingredients experiment

Every emitted variant includes a SHA-256 and a structural diff proof against the
canonical A/base fixture. If a generated variant changes an unexpected field family,
the script exits non-zero instead of silently producing a scientifically invalid pair.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple


RUNTIME_PROFILE = "creator-0.11.272"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_fixture(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_base(data)
    return data


def validate_base(data: Dict[str, Any]) -> None:
    if data.get("runtime_profile") != RUNTIME_PROFILE:
        raise ValueError(f"runtime_profile must be {RUNTIME_PROFILE}")
    if data.get("shape") not in {"Round", "Square", "Star", "Triangle"}:
        raise ValueError("shape must be Round, Square, Star, or Triangle")
    placements = data.get("placements")
    if not isinstance(placements, list) or not placements:
        raise ValueError("base fixture must contain at least one placement")
    for index, item in enumerate(placements):
        if item.get("sequence") != index:
            raise ValueError("placement sequence must be contiguous starting at zero")
        if item.get("size") not in {"Large", "Medium", "Small"}:
            raise ValueError(f"invalid size at placement {index}")
        if not isinstance(item.get("ingredient_id"), str) or not item["ingredient_id"]:
            raise ValueError(f"missing ingredient_id at placement {index}")
        for vector_name in ("position", "rotation"):
            vector = item.get(vector_name)
            if not isinstance(vector, dict) or set(vector) != {"x", "y", "z"}:
                raise ValueError(f"{vector_name} must contain exactly x/y/z at placement {index}")
            for axis in ("x", "y", "z"):
                value = vector[axis]
                if not isinstance(value, (int, float)):
                    raise ValueError(f"{vector_name}.{axis} must be numeric at placement {index}")


def structural_diff(a: Any, b: Any, path: str = "") -> List[str]:
    changes: List[str] = []
    if type(a) is not type(b):
        return [path or "$root"]
    if isinstance(a, dict):
        keys = set(a) | set(b)
        for key in sorted(keys):
            child = f"{path}.{key}" if path else key
            if key not in a or key not in b:
                changes.append(child)
            else:
                changes.extend(structural_diff(a[key], b[key], child))
    elif isinstance(a, list):
        if len(a) != len(b):
            changes.append(f"{path}.length")
        for index, (left, right) in enumerate(zip(a, b)):
            changes.extend(structural_diff(left, right, f"{path}[{index}]"))
    else:
        if a != b:
            changes.append(path or "$root")
    return changes


def normalize_allowed(path: str) -> str:
    # Replace explicit placement indexes with [*] so rules can be written by family.
    out = path
    start = 0
    while True:
        pos = out.find("placements[", start)
        if pos < 0:
            break
        end = out.find("]", pos)
        if end < 0:
            break
        out = out[:pos] + "placements[*]" + out[end + 1:]
        start = pos + len("placements[*]")
    return out


def diff_proof(base: Dict[str, Any], variant: Dict[str, Any], allowed: Set[str], experiment_id: str, variant_id: str) -> Dict[str, Any]:
    observed = structural_diff(base, variant)
    normalized = [normalize_allowed(path) for path in observed]
    unexpected = [path for path, norm in zip(observed, normalized) if norm not in allowed]
    return {
        "schema_version": "1.0",
        "kind": "pc3-creator-jpeg-fixture-diff-proof",
        "experiment_id": experiment_id,
        "variant": variant_id,
        "base_sha256": sha256_json(base),
        "variant_sha256": sha256_json(variant),
        "allowed_changed_fields": sorted(allowed),
        "observed_changed_fields": observed,
        "observed_changed_field_families": sorted(set(normalized)),
        "unexpected_changes": unexpected,
        "valid_one_variable_family": not unexpected,
    }


def set_metadata(fixture: Dict[str, Any], experiment: str, variant: str) -> None:
    fixture["experiment_id"] = experiment
    fixture["variant"] = variant
    fixture["name"] = f"JPEG_{experiment}_{variant}"


def rotation_variants(base: Dict[str, Any]) -> Iterable[Tuple[str, Dict[str, Any], Set[str]]]:
    for angle in [0, 30, 45, 60, 90, 120, 135, 180, 270]:
        variant = copy.deepcopy(base)
        label = f"R{angle:03d}"
        set_metadata(variant, "E01", label)
        for placement in variant["placements"]:
            placement["rotation"]["y"] = float(angle)
        yield label, variant, {
            "experiment_id", "variant", "name", "placements[*].rotation.y"
        }


def axis_variants(base: Dict[str, Any], experiment: str, axis: str, values: Sequence[float]) -> Iterable[Tuple[str, Dict[str, Any], Set[str]]]:
    for value in values:
        safe = str(value).replace("-", "m").replace(".", "p")
        label = f"{axis.upper()}_{safe}"
        variant = copy.deepcopy(base)
        set_metadata(variant, experiment, label)
        for placement in variant["placements"]:
            placement["position"][axis] = float(value)
        yield label, variant, {
            "experiment_id", "variant", "name", f"placements[*].position.{axis}"
        }


def e05_variants(base: Dict[str, Any]) -> Iterable[Tuple[str, Dict[str, Any], Set[str]]]:
    if len(base["placements"]) != 2:
        raise ValueError("E05 requires a base fixture with exactly two placements")
    a_y = float(base["placements"][0]["position"]["y"])
    b_y = float(base["placements"][1]["position"]["y"])
    center_y = (a_y + b_y) / 2.0
    low = center_y
    high = center_y + 0.02
    cases = [
        ("AB_sameY", False, center_y, center_y),
        ("BA_sameY", True, center_y, center_y),
        ("AB_A_low", False, low, high),
        ("AB_A_high", False, high, low),
        ("BA_B_low", True, high, low),
        ("BA_B_high", True, low, high),
    ]
    for label, reverse, y0, y1 in cases:
        variant = copy.deepcopy(base)
        set_metadata(variant, "E05", label)
        variant["placements"][0]["position"]["y"] = y0
        variant["placements"][1]["position"]["y"] = y1
        if reverse:
            variant["placements"] = list(reversed(variant["placements"]))
            for index, placement in enumerate(variant["placements"]):
                placement["sequence"] = index
        # Reordering a list causes many path-level field changes even when the same
        # objects are simply swapped. E05 intentionally permits complete ordered
        # placement-record changes plus Y and sequence.
        allowed = {
            "experiment_id", "variant", "name",
            "placements[*].sequence", "placements[*].ingredient_id", "placements[*].size",
            "placements[*].position.x", "placements[*].position.y", "placements[*].position.z",
            "placements[*].rotation.x", "placements[*].rotation.y", "placements[*].rotation.z",
        }
        yield label, variant, allowed


def e09_variants(base: Dict[str, Any], rotation_delta: float, x_delta: float, z_delta: float) -> Iterable[Tuple[str, Dict[str, Any], Set[str]]]:
    a = copy.deepcopy(base)
    set_metadata(a, "E09", "A")
    yield "A", a, {"experiment_id", "variant", "name"}

    b = copy.deepcopy(a)
    set_metadata(b, "E09", "B")
    for placement in b["placements"]:
        placement["rotation"]["y"] = float(placement["rotation"]["y"]) + rotation_delta
    yield "B", b, {"variant", "name", "placements[*].rotation.y"}

    c = copy.deepcopy(a)
    set_metadata(c, "E09", "C")
    for placement in c["placements"]:
        placement["position"]["x"] = float(placement["position"]["x"]) + x_delta
        placement["position"]["z"] = float(placement["position"]["z"]) + z_delta
    yield "C", c, {"variant", "name", "placements[*].position.x", "placements[*].position.z"}

    d = copy.deepcopy(a)
    set_metadata(d, "E09", "D")
    d["placements"] = list(reversed(d["placements"]))
    for index, placement in enumerate(d["placements"]):
        placement["sequence"] = index
    allowed = {
        "variant", "name",
        "placements[*].sequence", "placements[*].ingredient_id", "placements[*].size",
        "placements[*].position.x", "placements[*].position.y", "placements[*].position.z",
        "placements[*].rotation.x", "placements[*].rotation.y", "placements[*].rotation.z",
    }
    yield "D", d, allowed


def write_variant(out_dir: Path, base_for_diff: Dict[str, Any], experiment: str, label: str, fixture: Dict[str, Any], allowed: Set[str]) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = out_dir / f"{label}.json"
    fixture_path.write_text(json.dumps(fixture, indent=2, sort_keys=True), encoding="utf-8")
    proof = diff_proof(base_for_diff, fixture, allowed, experiment, label)
    proof_path = out_dir / f"{label}.diff-proof.json"
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True), encoding="utf-8")
    if not proof["valid_one_variable_family"]:
        raise RuntimeError(f"{experiment}/{label} changed unexpected fields: {proof['unexpected_changes']}")
    return {
        "variant": label,
        "fixture": str(fixture_path.resolve()),
        "fixture_sha256": proof["variant_sha256"],
        "diff_proof": str(proof_path.resolve()),
        "observed_changed_fields": proof["observed_changed_fields"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_fixture", type=Path)
    parser.add_argument("experiment", choices=["E01", "E02", "E03", "E04", "E05", "E09"])
    parser.add_argument("--out", type=Path, default=Path("research/jpeg-pipeline/fixtures-generated"))
    parser.add_argument("--rotation-delta", type=float, default=90.0, help="E09 B rotation delta")
    parser.add_argument("--x-delta", type=float, default=0.35, help="E09 C X delta")
    parser.add_argument("--z-delta", type=float, default=0.20, help="E09 C Z delta")
    args = parser.parse_args()

    original = load_fixture(args.base_fixture)
    experiment = args.experiment
    target_dir = args.out / experiment

    if experiment == "E01":
        variants = list(rotation_variants(original))
        diff_base = original
    elif experiment == "E02":
        variants = list(axis_variants(original, "E02", "x", [-5.0, -4.5, -4.0, -3.5, -3.0, -2.5, -2.0, -1.5, -1.0]))
        diff_base = original
    elif experiment == "E03":
        variants = list(axis_variants(original, "E03", "z", [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]))
        diff_base = original
    elif experiment == "E04":
        variants = list(axis_variants(original, "E04", "y", [0.99, 1.0, 1.01, 1.02, 1.05, 1.10]))
        diff_base = original
    elif experiment == "E05":
        variants = list(e05_variants(original))
        diff_base = original
    else:
        variants = list(e09_variants(original, args.rotation_delta, args.x_delta, args.z_delta))
        # E09 B/C/D are defined relative to canonical A, not the user's pre-metadata base.
        diff_base = next(fixture for label, fixture, _ in variants if label == "A")

    records = []
    for label, fixture, allowed in variants:
        base = diff_base
        if experiment == "E09" and label == "A":
            # A's only intended changes relative to the input base are experiment metadata.
            base = original
        records.append(write_variant(target_dir, base, experiment, label, fixture, allowed))

    manifest = {
        "schema_version": "1.0",
        "kind": "pc3-creator-generated-jpeg-research-fixtures",
        "experiment_id": experiment,
        "runtime_profile": RUNTIME_PROFILE,
        "source_base": str(args.base_fixture.resolve()),
        "source_base_sha256": sha256_json(original),
        "variants": records,
        "truth_note": "Fixture generation/diff proof only. Native runtime/save/JPEG evidence is still required."
    }
    manifest_path = target_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"manifest": str(manifest_path.resolve()), "variants": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
