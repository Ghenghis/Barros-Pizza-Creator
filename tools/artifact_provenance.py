#!/usr/bin/env python3
"""Inspect whether the checked-in plug-in binary matches the current source tree."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def current_source_hashes(root: Path = ROOT) -> dict[str, str]:
    return {
        path.name: sha256_file(path)
        for path in sorted((root / "plugin-src").glob("*.cs"), key=lambda item: item.name)
    }


def source_tree_hash(source_hashes: dict[str, str]) -> str:
    lines = "".join(
        f"{digest}  plugin-src/{name}\n" for name, digest in sorted(source_hashes.items())
    )
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def inspect(root: Path = ROOT) -> dict[str, Any]:
    provenance_path = root / "artifacts" / "build-provenance.json"
    actual_sources = current_source_hashes(root)
    actual_tree = source_tree_hash(actual_sources)
    status: dict[str, Any] = {
        "certified_prebuilt_current": False,
        "artifact_exists": False,
        "artifact_hash_matches": False,
        "source_hashes_match": False,
        "source_tree_hash_matches": False,
        "current_source_tree_sha256": actual_tree,
        "mismatched_source_files": [],
        "missing_source_files": [],
        "unexpected_source_files": [],
        "reason": "build provenance is missing",
    }
    if not provenance_path.is_file():
        return status

    try:
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        status["reason"] = f"build provenance is unreadable: {error}"
        return status

    artifact_name = str(provenance.get("artifact", ""))
    artifact_path = root / "artifacts" / artifact_name
    status["artifact"] = artifact_name
    status["artifact_exists"] = artifact_path.is_file()
    if artifact_path.is_file():
        status["artifact_hash_matches"] = (
            sha256_file(artifact_path) == str(provenance.get("artifact_sha256", "")).lower()
        )

    expected_sources = {
        str(name): str(digest).lower()
        for name, digest in dict(provenance.get("source_files_sha256", {})).items()
    }
    status["mismatched_source_files"] = sorted(
        name
        for name in actual_sources.keys() & expected_sources.keys()
        if actual_sources[name] != expected_sources[name]
    )
    status["missing_source_files"] = sorted(expected_sources.keys() - actual_sources.keys())
    status["unexpected_source_files"] = sorted(actual_sources.keys() - expected_sources.keys())
    status["source_hashes_match"] = actual_sources == expected_sources
    status["source_tree_hash_matches"] = (
        actual_tree == str(provenance.get("source_tree_sha256", "")).lower()
    )
    status["certified_prebuilt_current"] = all(
        (
            status["artifact_exists"],
            status["artifact_hash_matches"],
            status["source_hashes_match"],
            status["source_tree_hash_matches"],
        )
    )
    status["reason"] = (
        "artifact, source files, and source-tree provenance agree"
        if status["certified_prebuilt_current"]
        else "checked-in artifact belongs to an earlier source tree; exact Windows rebuild required"
    )
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the complete machine-readable status.")
    parser.add_argument(
        "--require-current",
        action="store_true",
        help="Exit non-zero unless the certified binary matches every current plug-in source file.",
    )
    args = parser.parse_args()
    status = inspect()
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        state = "current" if status["certified_prebuilt_current"] else "rebuild-required"
        print(f"Certified prebuilt: {state}; {status['reason']}")
    return 1 if args.require_current and not status["certified_prebuilt_current"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
