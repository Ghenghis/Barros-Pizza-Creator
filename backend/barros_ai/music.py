from __future__ import annotations

import os
import hashlib
import json
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


IMPORT_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".wma", ".aiff", ".aif", ".opus", ".oga", ".ogg", ".mp4", ".lrc"}
PLAY_EXTENSIONS = {".ogg", ".mp3", ".wav", ".mp4"}
RESERVED_MUSIC_FOLDERS = {"imports", ".playback-cache", "tools"}
MAX_IMPORT_BYTES = 500 * 1024 * 1024
NO_WINDOW_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
GAME_SAMPLE_RATE = "48000"
OGG_QUALITY = "8"
LOUDNESS_TARGET_LUFS = "-14"
TRUE_PEAK_DBFS = "-1.0"
IMPORT_AUDIO_FILTER = (
    "aresample=48000:async=1:first_pts=0,"
    "loudnorm=I=%s:TP=%s:LRA=11" % (LOUDNESS_TARGET_LUFS, TRUE_PEAK_DBFS)
)


class MusicLibrary:
    """Safe, local music inbox and optional FFmpeg-to-OGG conversion."""

    def __init__(self, music_root: Path):
        self.root = music_root
        self.inbox = music_root / "imports"

    def _ffmpeg(self) -> str:
        explicit = os.environ.get("BARROS_FFMPEG_PATH", "").strip()
        candidates = [explicit, shutil.which("ffmpeg") or "", str(self.root / "tools" / "ffmpeg.exe")]
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return str(Path(candidate).resolve())
        return ""

    def _tracks(self) -> list[Path]:
        tracks: list[Path] = []
        for path in self.root.rglob("*"):
            if not path.is_file() or path.suffix.casefold() not in PLAY_EXTENSIONS:
                continue
            relative = path.relative_to(self.root)
            if relative.parts and relative.parts[0].casefold() in RESERVED_MUSIC_FOLDERS:
                continue
            if path.suffix.casefold() == ".mp3" and path.with_suffix(".ogg").is_file():
                continue
            tracks.append(path)
        return sorted(tracks, key=lambda path: path.relative_to(self.root).as_posix().casefold())

    def _imports(self) -> list[Path]:
        files = sorted(
            (
                path
                for path in self.inbox.rglob("*")
                if path.is_file() and path.suffix.casefold() in IMPORT_EXTENSIONS
            ),
            key=lambda path: path.relative_to(self.inbox).as_posix().casefold(),
        )
        video_stems = {
            (path.parent.relative_to(self.inbox).as_posix().casefold(), path.stem.casefold())
            for path in files
            if path.suffix.casefold() == ".mp4"
        }
        return [
            path
            for path in files
            if path.suffix.casefold() in {".mp4", ".lrc"}
            or (path.parent.relative_to(self.inbox).as_posix().casefold(), path.stem.casefold()) not in video_stems
        ]

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _validate_and_measure(ffmpeg: str, path: Path) -> dict[str, float]:
        measured = subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-nostdin",
                "-v",
                "info",
                "-xerror",
                "-i",
                str(path),
                "-map",
                "0:a:0",
                "-vn",
                "-sn",
                "-dn",
                "-filter_complex",
                "ebur128=peak=true",
                "-f",
                "null",
                os.devnull,
            ],
            capture_output=True,
            text=True,
            timeout=240,
            check=False,
            creationflags=NO_WINDOW_FLAGS,
        )
        if measured.returncode:
            raise RuntimeError((measured.stderr or "Converted OGG decode validation failed.").strip()[:500])
        report = measured.stderr or ""
        loudness = re.findall(r"^\s*I:\s*(-?\d+(?:\.\d+)?)\s+LUFS", report, flags=re.MULTILINE)
        peaks = re.findall(r"^\s*Peak:\s*(-?\d+(?:\.\d+)?)\s+dBFS", report, flags=re.MULTILINE)
        if not loudness or not peaks:
            raise RuntimeError("Converted OGG decoded, but FFmpeg did not return its loudness summary.")
        return {"measured_lufs": float(loudness[-1]), "measured_peak_dbfs": float(peaks[-1])}

    def status(self) -> dict[str, Any]:
        self.root.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        tracks = self._tracks()
        imports = self._imports()
        return {
            "converter_available": bool(self._ffmpeg()),
            "track_count": len(tracks),
            "video_count": sum(path.suffix.casefold() == ".mp4" for path in tracks),
            "import_count": len(imports),
            "inbox": str(self.inbox),
            "quality_profile": "Audio: 48 kHz stereo · Vorbis q8 · -14 LUFS · -1 dBTP · Video: MP4 passthrough",
            "sample_rate_hz": int(GAME_SAMPLE_RATE),
            "loudness_target_lufs": float(LOUDNESS_TARGET_LUFS),
            "true_peak_dbfs": float(TRUE_PEAK_DBFS),
        }

    def resolve_track(self, encoded_name: str) -> Path | None:
        normalized = str(encoded_name or "").replace("\\", "/").strip("/")
        relative = PurePosixPath(normalized)
        if (
            not normalized
            or relative.is_absolute()
            or any(part in {"", ".", ".."} for part in relative.parts)
            or relative.parts[0].casefold() in RESERVED_MUSIC_FOLDERS
            or relative.suffix.casefold() not in PLAY_EXTENSIONS
        ):
            return None
        candidate = (self.root.joinpath(*relative.parts)).resolve()
        try:
            candidate.relative_to(self.root.resolve())
        except ValueError:
            return None
        return candidate if candidate.is_file() else None

    def prepare_playback(self, track: Path) -> Path:
        if track.suffix.casefold() == ".wav":
            return track
        ffmpeg = self._ffmpeg()
        if not ffmpeg:
            raise RuntimeError("Compressed playback needs FFmpeg. Set BARROS_FFMPEG_PATH or install FFmpeg on PATH.")
        cache = self.root / ".playback-cache"
        cache.mkdir(parents=True, exist_ok=True)
        relative_key = track.relative_to(self.root).as_posix().casefold().encode("utf-8")
        cache_key = hashlib.sha256(relative_key).hexdigest()[:12]
        destination = cache / (cache_key + "-" + track.stem + ".wav")
        if destination.is_file() and destination.stat().st_size > 1024 and destination.stat().st_mtime_ns >= track.stat().st_mtime_ns:
            return destination
        temporary = cache / (track.stem + "." + uuid.uuid4().hex + ".partial.wav")
        try:
            completed = subprocess.run(
                [
                    ffmpeg,
                    "-hide_banner",
                    "-nostdin",
                    "-v",
                    "error",
                    "-y",
                    "-i",
                    str(track),
                    "-map",
                    "0:a:0",
                    "-vn",
                    "-sn",
                    "-dn",
                    "-map_metadata",
                    "-1",
                    "-map_chapters",
                    "-1",
                    "-af",
                    "aresample=48000:async=1:first_pts=0",
                    "-c:a",
                    "pcm_s16le",
                    "-ar",
                    GAME_SAMPLE_RATE,
                    "-ac",
                    "2",
                    str(temporary),
                ],
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
                creationflags=NO_WINDOW_FLAGS,
            )
            if completed.returncode:
                raise RuntimeError((completed.stderr or "FFmpeg playback-cache conversion failed.").strip()[:500])
            if not temporary.is_file() or temporary.stat().st_size < 1024:
                raise RuntimeError("The decoded playback cache was empty.")
            os.replace(temporary, destination)
            return destination
        finally:
            if temporary.exists():
                temporary.unlink()

    def refresh(self) -> dict[str, Any]:
        state = self.status()
        ffmpeg = self._ffmpeg()
        converted = 0
        copied = 0
        video_copied = 0
        lyrics_copied = 0
        skipped = 0
        failed: list[dict[str, str]] = []
        records: list[dict[str, Any]] = []
        for source in self._imports():
            extension = source.suffix.casefold()
            relative_source = source.relative_to(self.inbox)
            source_label = relative_source.as_posix()
            if source.stat().st_size > MAX_IMPORT_BYTES:
                failed.append({"file": source_label, "error": "File exceeds the 500 MB import limit."})
                records.append({"source": source_label, "state": "failed", "detail": "File exceeds the 500 MB import limit."})
                continue
            is_video = extension == ".mp4"
            is_lyrics = extension == ".lrc"
            destination = self.root / relative_source if is_video or is_lyrics else (self.root / relative_source).with_suffix(".ogg")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination_label = destination.relative_to(self.root).as_posix()
            if destination.is_file() and destination.stat().st_size > 0 and destination.stat().st_mtime_ns >= source.stat().st_mtime_ns:
                skipped += 1
                records.append(
                    {
                        "source": source_label,
                        "source_sha256": self._sha256(source),
                        "output": destination_label,
                        "output_sha256": self._sha256(destination),
                        "state": "skipped_current",
                    }
                )
                continue
            temporary = destination.with_name(
                destination.stem + "." + uuid.uuid4().hex + ".partial" + destination.suffix
            )
            try:
                if is_video or is_lyrics:
                    shutil.copy2(source, temporary)
                    copied += 1
                    if is_video:
                        video_copied += 1
                    else:
                        lyrics_copied += 1
                    measurements = {}
                elif ffmpeg:
                    completed = subprocess.run(
                        [
                            ffmpeg,
                            "-hide_banner",
                            "-nostdin",
                            "-v",
                            "error",
                            "-y",
                            "-i",
                            str(source),
                            "-map",
                            "0:a:0",
                            "-vn",
                            "-sn",
                            "-dn",
                            "-map_metadata",
                            "-1",
                            "-map_chapters",
                            "-1",
                            "-af",
                            IMPORT_AUDIO_FILTER,
                            "-c:a",
                            "libvorbis",
                            "-q:a",
                            OGG_QUALITY,
                            "-ar",
                            GAME_SAMPLE_RATE,
                            "-ac",
                            "2",
                            str(temporary),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=180,
                        check=False,
                        creationflags=NO_WINDOW_FLAGS,
                    )
                    if completed.returncode:
                        raise RuntimeError((completed.stderr or "FFmpeg conversion failed.").strip()[:500])
                    measurements = self._validate_and_measure(ffmpeg, temporary)
                    converted += 1
                elif extension == ".ogg":
                    shutil.copy2(source, temporary)
                    copied += 1
                else:
                    skipped += 1
                    detail = "No FFmpeg converter was found; the Media Deck can still try direct playback."
                    failed.append({"file": source_label, "error": detail})
                    records.append({"source": source_label, "state": "failed", "detail": detail})
                    continue
                minimum_bytes = 1 if is_lyrics else 1024
                if not temporary.is_file() or temporary.stat().st_size < minimum_bytes:
                    raise RuntimeError("The imported media file was empty.")
                os.replace(temporary, destination)
                records.append(
                    {
                        "source": source_label,
                        "source_sha256": self._sha256(source),
                        "output": destination_label,
                        "output_sha256": self._sha256(destination),
                        "output_bytes": destination.stat().st_size,
                        "state": "video_copied" if is_video else ("lyrics_copied" if is_lyrics else ("converted_and_decode_validated" if ffmpeg else "copied_without_converter")),
                        **(measurements if ffmpeg and not is_video and not is_lyrics else {}),
                    }
                )
            except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
                if temporary.exists():
                    temporary.unlink()
                failed.append({"file": source_label, "error": str(exc)[:500]})
                records.append({"source": source_label, "state": "failed", "detail": str(exc)[:500]})
        final = self.status()
        report_path = self.root / "conversion-report.json"
        report_temporary = self.root / ("conversion-report." + uuid.uuid4().hex + ".partial.json")
        report = {
            "schema_version": "1.0",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "quality_profile": final["quality_profile"],
            "audio_only": False,
            "video_passthrough": True,
            "decode_validation": True,
            "counts": {"converted": converted, "copied": copied, "video_copied": video_copied, "lyrics_copied": lyrics_copied, "skipped": skipped, "failed": len(failed)},
            "files": records,
        }
        try:
            report_temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            os.replace(report_temporary, report_path)
        finally:
            if report_temporary.exists():
                report_temporary.unlink()
        final.update(
            {
                "ok": not failed,
                "converted": converted,
                "copied": copied,
                "video_copied": video_copied,
                "lyrics_copied": lyrics_copied,
                "skipped": skipped,
                "failed": failed,
                "report": str(report_path),
            }
        )
        return final
