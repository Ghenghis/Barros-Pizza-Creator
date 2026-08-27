#!/usr/bin/env python3
"""Build the loopback-only Creator backend bundle for a VPS or Linux host."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.3.0-rc1"
OUTPUT = ROOT / "releases" / f"Barros_Pizza_Creator_Backend_v{VERSION}_VPS_Headless.zip"
FIXED_TIME = (2026, 8, 27, 0, 0, 0)


def files() -> list[Path]:
    chosen = [
        ROOT / "VERSION.txt",
        ROOT / "backend" / "main.py",
        ROOT / "backend" / "catalog.bootstrap.json",
        ROOT / "backend" / "default_settings.json",
        ROOT / "backend" / "settings.example.json",
        ROOT / "contracts" / "rc1.acceptance.json",
        ROOT / "packaging" / "distribution-contract.json",
        ROOT / "docs" / "CREATOR_1_3_BEGINNER_AND_DISTRIBUTION.md",
    ]
    chosen.extend(sorted((ROOT / "backend" / "barros_ai").glob("*.py")))
    return chosen


def build(output: Path = OUTPUT) -> dict:
    selected = files()
    missing = [str(path) for path in selected if not path.is_file()]
    if missing:
        raise RuntimeError("Missing VPS bundle inputs: " + ", ".join(missing))
    prefix = f"Barros_Pizza_Creator_Backend_v{VERSION}_VPS_Headless"
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in selected:
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(f"{prefix}/{relative}", FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
        launcher = "#!/usr/bin/env sh\nset -eu\nexec python3 backend/main.py --host 127.0.0.1 --port 48173 \"$@\"\n"
        info = zipfile.ZipInfo(f"{prefix}/barros-creator-backend", FIXED_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 3
        info.external_attr = 0o100755 << 16
        archive.writestr(info, launcher.encode("utf-8"))
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"CRC failure: {bad}")
        members = len([name for name in archive.namelist() if not name.endswith("/")])
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n", encoding="ascii")
    return {"ok": True, "output": str(output), "sha256": digest, "members": members, "network_scope": "loopback_only"}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
