#!/usr/bin/env python3
"""Import up to 500 user-authorized pizza reference images into the local library."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.attachments import AttachmentError, inspect_image_bytes  # noqa: E402


SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
MIME_SUFFIX = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_ITEMS = 500


def tags_from_name(name: str) -> list[str]:
    ignored = {"img", "image", "photo", "facebook", "download", "received", "jpg", "jpeg", "png"}
    values = re.findall(r"[a-z][a-z0-9]+", Path(name).stem.casefold())
    return sorted({value for value in values if value not in ignored and len(value) > 2})[:12]


def load_existing(path: Path) -> dict:
    if not path.is_file():
        return {"schema_version": "1.0", "items": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Existing library index is invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("items", []), list):
        raise SystemExit(f"Existing library index has the wrong shape: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Folder containing JPG, PNG, or WebP designs")
    parser.add_argument(
        "--library-dir",
        type=Path,
        default=ROOT / "backend" / "data" / "inspiration",
        help="Local output library; excluded from release packages",
    )
    parser.add_argument("--limit", type=int, default=MAX_ITEMS)
    parser.add_argument("--source-label", default="local-folder")
    parser.add_argument("--source-url", default="")
    parser.add_argument(
        "--rights",
        choices=("user-owned", "permission-granted", "reference-only"),
        default="reference-only",
        help="Usage record; reference-only images are never included in a release ZIP",
    )
    args = parser.parse_args()

    source = args.source.resolve()
    if not source.is_dir():
        raise SystemExit(f"Source folder not found: {source}")
    limit = max(1, min(int(args.limit), MAX_ITEMS))
    library = args.library_dir.resolve()
    images_dir = library / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    index_path = library / "index.json"
    existing = load_existing(index_path)
    by_hash = {
        str(item.get("sha256", "")): item
        for item in existing.get("items", [])
        if isinstance(item, dict) and item.get("sha256")
    }

    scanned = imported = duplicates = rejected = 0
    for path in sorted(source.rglob("*"), key=lambda value: value.as_posix().casefold()):
        if len(by_hash) >= limit:
            break
        if not path.is_file() or path.is_symlink() or path.suffix.casefold() not in SUPPORTED_SUFFIXES:
            continue
        scanned += 1
        try:
            raw = path.read_bytes()
            metadata = inspect_image_bytes(raw)
        except (OSError, AttachmentError):
            rejected += 1
            continue
        digest = hashlib.sha256(raw).hexdigest()
        if digest in by_hash:
            duplicates += 1
            continue
        suffix = MIME_SUFFIX[metadata["mime_type"]]
        target = images_dir / f"{digest[:20]}{suffix}"
        if not target.exists():
            shutil.copyfile(path, target)
        record = {
            "id": digest[:16],
            "name": path.name[:240],
            "path": target.relative_to(library).as_posix(),
            "sha256": digest,
            "mime_type": metadata["mime_type"],
            "format": metadata["format"],
            "width": metadata["width"],
            "height": metadata["height"],
            "bytes": metadata["bytes"],
            "caption": Path(path.name).stem[:500],
            "tags": tags_from_name(path.name),
            "source_label": str(args.source_label)[:120],
            "source_url": str(args.source_url)[:2000],
            "rights": args.rights,
        }
        by_hash[digest] = record
        imported += 1

    items = sorted(by_hash.values(), key=lambda item: (str(item.get("name", "")).casefold(), str(item.get("sha256", ""))))[:MAX_ITEMS]
    payload = {
        "schema_version": "1.0",
        "updated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "local_only": True,
        "redistribution": "Images are excluded from release packages; keep source rights with each record.",
        "items": items,
    }
    temporary = index_path.with_suffix(".json.partial")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, index_path)
    print(
        f"Inspiration library ready: {len(items)} total; {imported} imported; "
        f"{duplicates} duplicates; {rejected} rejected; index={index_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
