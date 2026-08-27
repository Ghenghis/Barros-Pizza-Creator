from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.music import MusicLibrary, NO_WINDOW_FLAGS  # noqa: E402


class MusicLibraryTests(unittest.TestCase):
    def test_status_creates_inbox_and_counts_playable_tracks(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            music = MusicLibrary(Path(folder) / "music")
            (music.root).mkdir(parents=True)
            (music.root / "song.ogg").write_bytes(b"OggS" + b"x" * 2048)
            status = music.status()
            self.assertTrue(music.inbox.is_dir())
            self.assertEqual(1, status["track_count"])
            self.assertEqual(0, status["import_count"])

    def test_refresh_copies_owner_supplied_ogg_without_converter(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            music = MusicLibrary(Path(folder) / "music")
            music.status()
            (music.inbox / "New Barros Song.ogg").write_bytes(b"OggS" + b"z" * 4096)
            with patch.dict(os.environ, {"BARROS_FFMPEG_PATH": ""}), patch("shutil.which", return_value=None):
                result = music.refresh()
            self.assertTrue(result["ok"])
            self.assertEqual(1, result["copied"])
            self.assertTrue((music.root / "New Barros Song.ogg").is_file())

    def test_refresh_preserves_mp4_lyric_video_without_audio_conversion(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            music = MusicLibrary(Path(folder) / "music")
            music.status()
            source = music.inbox / "Lyrics" / "Barros Calling.mp4"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"mp4-video" + b"v" * 4096)
            with patch.dict(os.environ, {"BARROS_FFMPEG_PATH": ""}), patch("shutil.which", return_value=None):
                result = music.refresh()
            self.assertTrue(result["ok"])
            self.assertEqual(1, result["video_copied"])
            self.assertEqual(1, result["video_count"])
            self.assertTrue((music.root / "Lyrics" / "Barros Calling.mp4").is_file())
            self.assertFalse((music.root / "Lyrics" / "Barros Calling.ogg").exists())

    def test_same_stem_mp4_is_preferred_over_audio_import(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            music = MusicLibrary(Path(folder) / "music")
            music.status()
            album = music.inbox / "Owner Uploads"
            album.mkdir(parents=True)
            (album / "Red White and Barros.mp4").write_bytes(b"mp4-video" + b"v" * 4096)
            (album / "Red White and Barros.wav").write_bytes(b"RIFF" + b"w" * 4096)
            self.assertEqual(1, music.status()["import_count"])
            with patch.dict(os.environ, {"BARROS_FFMPEG_PATH": ""}), patch("shutil.which", return_value=None):
                result = music.refresh()
            self.assertTrue(result["ok"])
            self.assertEqual(1, result["track_count"])
            self.assertTrue((music.root / "Owner Uploads" / "Red White and Barros.mp4").is_file())
            self.assertFalse((music.root / "Owner Uploads" / "Red White and Barros.ogg").exists())

    def test_same_name_lrc_is_preserved_for_synchronized_audio_lyrics(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            music = MusicLibrary(Path(folder) / "music")
            music.status()
            (music.inbox / "Theme.ogg").write_bytes(b"OggS" + b"o" * 4096)
            (music.inbox / "Theme.lrc").write_text("[00:01.00]Welcome to Barros\n[00:03.50]Design the pizza", encoding="utf-8")
            with patch.dict(os.environ, {"BARROS_FFMPEG_PATH": ""}), patch("shutil.which", return_value=None):
                result = music.refresh()
            self.assertTrue(result["ok"])
            self.assertEqual(1, result["lyrics_copied"])
            self.assertTrue((music.root / "Theme.lrc").is_file())
            self.assertEqual(1, result["track_count"])

    def test_ffmpeg_commands_strip_non_audio_streams_and_use_48khz(self) -> None:
        source = (ROOT / "backend" / "barros_ai" / "music.py").read_text(encoding="utf-8")
        for flag in ('"-vn"', '"-sn"', '"-dn"', '"-map_metadata"', '"-map_chapters"'):
            self.assertIn(flag, source)
        self.assertIn('GAME_SAMPLE_RATE = "48000"', source)
        self.assertIn('OGG_QUALITY = "8"', source)
        self.assertIn('LOUDNESS_TARGET_LUFS = "-14"', source)
        self.assertIn('TRUE_PEAK_DBFS = "-1.0"', source)
        self.assertIn('"loudnorm=I=%s:TP=%s:LRA=11"', source)
        self.assertIn('"-xerror"', source)
        self.assertIn('"ebur128=peak=true"', source)
        self.assertIn('"measured_lufs"', source)
        self.assertIn('"measured_peak_dbfs"', source)

    def test_refresh_preserves_mp3_when_converter_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            music = MusicLibrary(Path(folder) / "music")
            music.status()
            source = music.inbox / "Future Song.mp3"
            source.write_bytes(b"ID3" + b"m" * 4096)
            with patch.dict(os.environ, {"BARROS_FFMPEG_PATH": ""}), patch("shutil.which", return_value=None):
                result = music.refresh()
            self.assertFalse(result["ok"])
            self.assertTrue(source.is_file())
            self.assertFalse((music.root / "Future Song.ogg").exists())
            self.assertIn("direct playback", result["failed"][0]["error"])
            report = music.root / "conversion-report.json"
            self.assertTrue(report.is_file())
            self.assertIn('"state": "failed"', report.read_text(encoding="utf-8"))

    def test_track_resolution_blocks_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            music = MusicLibrary(Path(folder) / "music")
            music.status()
            track = music.root / "Safe Song.ogg"
            track.write_bytes(b"OggS" + b"x" * 2048)
            self.assertEqual(track.resolve(), music.resolve_track("Safe Song.ogg"))
            self.assertIsNone(music.resolve_track("../Safe Song.ogg"))
            self.assertIsNone(music.resolve_track("settings.json"))

    def test_nested_albums_are_counted_resolved_and_imported_in_place(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            music = MusicLibrary(Path(folder) / "music")
            music.status()
            album = music.root / "Barros Album One"
            album.mkdir()
            track = album / "Opening Theme.ogg"
            track.write_bytes(b"OggS" + b"x" * 2048)
            nested_import = music.inbox / "Live Sessions" / "Closing Theme.ogg"
            nested_import.parent.mkdir(parents=True)
            nested_import.write_bytes(b"OggS" + b"z" * 4096)

            self.assertEqual(1, music.status()["track_count"])
            self.assertEqual(track.resolve(), music.resolve_track("Barros Album One/Opening Theme.ogg"))
            with patch.dict(os.environ, {"BARROS_FFMPEG_PATH": ""}), patch("shutil.which", return_value=None):
                result = music.refresh()
            self.assertTrue(result["ok"])
            self.assertTrue((music.root / "Live Sessions" / "Closing Theme.ogg").is_file())
            self.assertEqual(2, result["track_count"])

    def test_reserved_folders_never_appear_as_library_tracks(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            music = MusicLibrary(Path(folder) / "music")
            music.status()
            for name in ("imports", ".playback-cache", "tools"):
                target = music.root / name / "Hidden.ogg"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"OggS" + b"x" * 2048)
            self.assertEqual(0, music.status()["track_count"])
            self.assertIsNone(music.resolve_track("imports/Hidden.ogg"))

    def test_wav_playback_needs_no_converter(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            music = MusicLibrary(Path(folder) / "music")
            music.status()
            wav = music.root / "Ready.wav"
            wav.write_bytes(b"RIFF" + b"x" * 2048)
            self.assertEqual(wav, music.prepare_playback(wav))

    def test_windows_ffmpeg_conversion_is_hidden(self) -> None:
        if os.name == "nt":
            self.assertNotEqual(0, NO_WINDOW_FLAGS)


if __name__ == "__main__":
    unittest.main()
