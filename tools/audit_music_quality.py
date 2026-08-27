from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.music import MusicLibrary  # noqa: E402


def resolve_ffmpeg(requested: str) -> str:
    candidates = [requested, os.environ.get("BARROS_FFMPEG_PATH", ""), shutil.which("ffmpeg") or ""]
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    candidates.append(str(local / "Cypress" / "Cache" / "13.17.0" / "Cypress" / "resources" / "app" / "node_modules" / "@ffmpeg-installer" / "win32-x64" / "ffmpeg.exe"))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise FileNotFoundError("FFmpeg was not found. Pass --ffmpeg or set BARROS_FFMPEG_PATH.")


def inspect_stream(ffmpeg: str, track: Path) -> dict[str, object]:
    completed = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(track)],
        capture_output=True,
        text=True,
        check=False,
    )
    report = completed.stderr or ""
    streams = re.findall(r"^\s*Stream #.*$", report, flags=re.MULTILINE)
    audio = [line for line in streams if "Audio:" in line]
    sample_rate = 0
    channels = ""
    if audio:
        match = re.search(r"Audio:\s*vorbis,\s*(\d+)\s*Hz,\s*([^,]+)", audio[0])
        if match:
            sample_rate = int(match.group(1))
            channels = match.group(2).strip()
    return {
        "stream_count": len(streams),
        "audio_stream_count": len(audio),
        "codec": "vorbis" if audio and "Audio: vorbis" in audio[0] else "unknown",
        "sample_rate_hz": sample_rate,
        "channels": channels,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Barro's bundled OGG quality and decode integrity.")
    parser.add_argument("--ffmpeg", default="")
    parser.add_argument("--music-root", type=Path, default=ROOT / "assets" / "music")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "evidence" / "audio-quality-audit.json")
    args = parser.parse_args()

    ffmpeg = resolve_ffmpeg(args.ffmpeg)
    tracks = sorted(args.music_root.resolve().glob("*.ogg"), key=lambda path: path.name.casefold())
    if not tracks:
        raise FileNotFoundError("No OGG tracks were found under %s" % args.music_root)
    files: list[dict[str, object]] = []
    for track in tracks:
        stream = inspect_stream(ffmpeg, track)
        measured = MusicLibrary._validate_and_measure(ffmpeg, track)
        passed = (
            stream["stream_count"] == 1
            and stream["audio_stream_count"] == 1
            and stream["codec"] == "vorbis"
            and stream["sample_rate_hz"] == 48000
            and stream["channels"] == "stereo"
            and -15.5 <= measured["measured_lufs"] <= -12.5
            and measured["measured_peak_dbfs"] <= 0.0
        )
        files.append(
            {
                "file": track.name,
                "bytes": track.stat().st_size,
                "sha256": MusicLibrary._sha256(track),
                **stream,
                **measured,
                "decode_valid": True,
                "pass": passed,
            }
        )
    payload = {
        "schema_version": "1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "profile": "48 kHz stereo · Ogg Vorbis q8 · target -14 LUFS · peak protected",
        "track_count": len(files),
        "passed": all(bool(record["pass"]) for record in files),
        "files": files,
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".partial")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, output)
    print("Wrote %s: %d tracks, passed=%s" % (output, len(files), payload["passed"]))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
