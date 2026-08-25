#!/usr/bin/env python3
"""Build and verify the deterministic Barro's Pizza Creator RC1 release ZIP."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ZIP = ROOT / "releases" / "Barros_Pizza_Creator_AI_Designer_v1.0.0-rc1.zip"
ARCHIVE_ROOT = "Barros_Pizza_Creator_AI_Designer_v1.0.0-rc1"
FIXED_ZIP_TIME = (2026, 8, 24, 0, 0, 0)
EXCLUDED_ROOTS = {".git", "evidence", "releases"}
EXCLUDED_NAMES = {"MANIFEST.sha256", "RELEASE_CHECKSUMS.sha256"}
EXCLUDED_PARTS = {"__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".pdb"}
EXCLUDED_RELATIVE = {
    PurePosixPath("backend/settings.json"),
    PurePosixPath("backend/data/conversation_history.json"),
}
ALLOWED_ARTIFACTS = {
    PurePosixPath("artifacts/Barros.PizzaCreator.AI.dll"),
    PurePosixPath("artifacts/README.md"),
    PurePosixPath("artifacts/build-provenance.json"),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        relative = PurePosixPath(path.relative_to(root).as_posix())
        if relative.parts[0] in EXCLUDED_ROOTS:
            continue
        if relative.parts[0] == "artifacts" and relative not in ALLOWED_ARTIFACTS:
            continue
        if path.name in EXCLUDED_NAMES or any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES or relative in EXCLUDED_RELATIVE:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def manifest_text(root: Path, files: list[Path]) -> str:
    return "".join(
        f"{sha256_file(path)}  {path.relative_to(root).as_posix()}\n" for path in files
    )


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def build(output: Path) -> tuple[int, int, str]:
    files = package_files(ROOT)
    manifest = manifest_text(ROOT, files)
    (ROOT / "MANIFEST.sha256").write_text(manifest, encoding="utf-8", newline="\n")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".partial")
    if temporary.exists():
        temporary.unlink()

    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                relative = path.relative_to(ROOT).as_posix()
                archive.writestr(zip_info(f"{ARCHIVE_ROOT}/{relative}"), path.read_bytes(), compresslevel=9)
            archive.writestr(zip_info(f"{ARCHIVE_ROOT}/MANIFEST.sha256"), manifest.encode("utf-8"), compresslevel=9)
        os.replace(temporary, output)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    release_hash = sha256_file(output)
    release_relative = output.relative_to(ROOT).as_posix()
    (ROOT / "RELEASE_CHECKSUMS.sha256").write_text(
        f"{release_hash}  {release_relative}\n", encoding="utf-8", newline="\n"
    )
    verify(output)
    return len(files), output.stat().st_size, release_hash


def verify(output: Path) -> None:
    with zipfile.ZipFile(output, "r") as archive:
        manifest_name = f"{ARCHIVE_ROOT}/MANIFEST.sha256"
        manifest = archive.read(manifest_name).decode("utf-8")
        expected_names = {manifest_name}
        for line in manifest.splitlines():
            expected_hash, relative = line.split("  ", 1)
            member = f"{ARCHIVE_ROOT}/{relative}"
            expected_names.add(member)
            actual_hash = sha256_bytes(archive.read(member))
            if actual_hash != expected_hash:
                raise RuntimeError(f"ZIP member hash mismatch: {relative}")
        actual_names = {name for name in archive.namelist() if not name.endswith("/")}
        if actual_names != expected_names:
            extra = sorted(actual_names - expected_names)
            missing = sorted(expected_names - actual_names)
            raise RuntimeError(f"ZIP membership mismatch; extra={extra}, missing={missing}")
        bad_member = archive.testzip()
        if bad_member:
            raise RuntimeError(f"ZIP CRC failure: {bad_member}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.verify_only:
        verify(output)
        print(f"Verified release ZIP: {output}")
        return 0
    file_count, size, release_hash = build(output)
    print(f"Built and verified {output}")
    print(f"Manifest files: {file_count}; ZIP bytes: {size}; SHA-256: {release_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
