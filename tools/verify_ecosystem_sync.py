from __future__ import annotations

"""Verify local Creator / Workbench / Studio checkouts share one ecosystem contract.

This intentionally understands that the Creator and Studio have DIFFERENT
certified PC3 binary profiles. It checks that every project agrees on that
matrix instead of falsely demanding one game version for all runtime tooling.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def canonical_sha(path: Path) -> str:
    data = load_json(path)
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "detail": detail}


def verify(creator: Path, workbench: Path, studio: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    projects = {"creator": creator, "workbench": workbench, "studio": studio}
    for key, root in projects.items():
        rows.append(check(f"{key}_root", root.is_dir(), str(root)))

    schema_paths = {
        key: root / "contracts" / "pc3-image-handoff.schema.json"
        for key, root in projects.items()
    }
    matrix_paths = {
        key: root / "contracts" / "pc3-build-compatibility.json"
        for key, root in projects.items()
    }

    schema_shas = {}
    matrix_shas = {}
    for key, path in schema_paths.items():
        if path.is_file():
            schema_shas[key] = canonical_sha(path)
        else:
            rows.append(check(f"{key}_image_schema", False, f"missing {path}"))
    for key, path in matrix_paths.items():
        if path.is_file():
            matrix_shas[key] = canonical_sha(path)
        else:
            rows.append(check(f"{key}_build_matrix", False, f"missing {path}"))

    rows.append(check(
        "image_schema_sync",
        len(schema_shas) == 3 and len(set(schema_shas.values())) == 1,
        json.dumps(schema_shas, sort_keys=True),
    ))
    rows.append(check(
        "build_matrix_sync",
        len(matrix_shas) == 3 and len(set(matrix_shas.values())) == 1,
        json.dumps(matrix_shas, sort_keys=True),
    ))

    matrix = load_json(matrix_paths["creator"]) if matrix_paths["creator"].is_file() else {}
    creator_profile = (matrix.get("profiles") or {}).get("creator-0.11.272") or {}
    studio_profile = (matrix.get("profiles") or {}).get("studio-1.11.403") or {}

    rc1_path = creator / "contracts" / "rc1.acceptance.json"
    if rc1_path.is_file():
        rc1 = load_json(rc1_path)
        target = rc1.get("target") or {}
        rows.append(check(
            "creator_profile_version",
            target.get("game_version") == creator_profile.get("product_version") == "0.11.272",
            f"rc1={target.get('game_version')} matrix={creator_profile.get('product_version')}",
        ))
        rows.append(check(
            "creator_profile_unity",
            str(target.get("unity", "")).startswith(str(creator_profile.get("unity_player", ""))),
            f"rc1={target.get('unity')} matrix={creator_profile.get('unity_player')}",
        ))
        rows.append(check(
            "creator_assembly_hash",
            target.get("assembly_csharp_sha256") == (creator_profile.get("assembly_csharp") or {}).get("sha256"),
            str(target.get("assembly_csharp_sha256")),
        ))
        rows.append(check(
            "creator_firstpass_hash",
            target.get("assembly_csharp_firstpass_sha256") == (creator_profile.get("assembly_csharp_firstpass") or {}).get("sha256"),
            str(target.get("assembly_csharp_firstpass_sha256")),
        ))
    else:
        rows.append(check("creator_rc1_contract", False, f"missing {rc1_path}"))

    studio_build_path = studio / "config" / "pc3_build_1.11.403.json"
    if studio_build_path.is_file():
        studio_build = load_json(studio_build_path).get("target") or {}
        rows.append(check(
            "studio_profile_version",
            studio_build.get("verified_game_build") == studio_profile.get("product_version") == "1.11.403",
            f"studio={studio_build.get('verified_game_build')} matrix={studio_profile.get('product_version')}",
        ))
        rows.append(check(
            "studio_profile_unity",
            studio_build.get("verified_unity_version") == studio_profile.get("unity_player") == "2017.4.40f1",
            f"studio={studio_build.get('verified_unity_version')} matrix={studio_profile.get('unity_player')}",
        ))
    else:
        rows.append(check("studio_build_contract", False, f"missing {studio_build_path}"))

    rows.append(check(
        "dual_profile_separation",
        creator_profile.get("product_version") != studio_profile.get("product_version")
        and creator_profile.get("unity_player") != studio_profile.get("unity_player"),
        f"Creator {creator_profile.get('product_version')}/{creator_profile.get('unity_player')} vs Studio {studio_profile.get('product_version')}/{studio_profile.get('unity_player')}",
    ))

    display_names = []
    for key, path in matrix_paths.items():
        if path.is_file():
            display_names.append(load_json(path).get("display_name"))
    rows.append(check(
        "display_name_sync",
        len(display_names) == 3 and set(display_names) == {"Pizza Connection 3 / Barro's Pizza"},
        repr(display_names),
    ))

    failed = [row for row in rows if not row["pass"]]
    return {
        "ok": not failed,
        "contract": "barros-pc3-ecosystem-sync-v1",
        "checks": rows,
        "pass_count": len(rows) - len(failed),
        "fail_count": len(failed),
        "important_fact": "Creator 0.11.272 and Studio 1.11.403 are intentionally separate runtime profiles.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--creator", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--workbench", required=True)
    parser.add_argument("--studio", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()
    result = verify(Path(args.creator).resolve(), Path(args.workbench).resolve(), Path(args.studio).resolve())
    text = json.dumps(result, indent=2, ensure_ascii=False)
    print(text)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
