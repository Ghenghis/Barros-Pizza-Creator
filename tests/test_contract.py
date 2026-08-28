import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "rc1.acceptance.json"


class ProofContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_gate_ids_are_unique_and_release_requirements_have_evidence(self):
        gates = [gate for layer in self.contract["layers"] for gate in layer["gates"]]
        ids = [gate["id"] for gate in gates]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(gates), 20)
        for gate in gates:
            self.assertRegex(gate["id"], r"^[A-Z]{2,3}-\d{3}$")
            if gate["release_required"]:
                self.assertTrue(gate["evidence"].strip())

    def test_locked_reference_images_exist_and_match(self):
        self.assertEqual(4, len(self.contract["reference_images"]))
        for reference in self.contract["reference_images"]:
            path = ROOT / reference["path"]
            self.assertTrue(path.is_file(), path)
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(reference["sha256"], actual, reference["mode"])

    def test_certified_artifact_matches_provenance(self):
        provenance = json.loads((ROOT / "artifacts" / "build-provenance.json").read_text(encoding="utf-8"))
        artifact = ROOT / "artifacts" / provenance["artifact"]
        self.assertTrue(artifact.is_file())
        self.assertEqual(provenance["artifact_bytes"], artifact.stat().st_size)
        self.assertEqual(provenance["artifact_sha256"], hashlib.sha256(artifact.read_bytes()).hexdigest())
        self.assertEqual(
            self.contract["target"]["assembly_csharp_sha256"],
            provenance["target"]["assembly_csharp_sha256"],
        )
        source_lines = []
        for path in sorted((ROOT / "plugin-src").glob("*.cs"), key=lambda item: item.name):
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(provenance["source_files_sha256"][path.name], actual)
            source_lines.append(f"{actual}  plugin-src/{path.name}\n")
        source_tree = hashlib.sha256("".join(source_lines).encode("utf-8")).hexdigest()
        self.assertEqual(provenance["source_tree_sha256"], source_tree)

    def test_contract_names_all_requested_runtime_proofs(self):
        requirements = " ".join(
            gate["requirement"] for layer in self.contract["layers"] for gate in layer["gates"]
        ).lower()
        for term in ("fifth tab", "header", "preview", "restore", "apply", "save", "reload", "microphone", "speech provider", "chat", "lab", "crew", "voice", "media"):
            self.assertIn(term, requirements)

    def test_bepinex_plugin_version_is_numeric_and_installer_is_target_scoped(self):
        plugin = (ROOT / "plugin-src" / "BarrosAiPlugin.cs").read_text(encoding="utf-8")
        match = re.search(r'BepInPlugin\([^\n]+,\s*"([^"]+)"\)\]', plugin)
        self.assertIsNotNone(match)
        self.assertRegex(match.group(1), r"^\d+\.\d+\.\d+$")

        installer = (ROOT / "INSTALL_Barros_AI_Designer.ps1").read_text(encoding="utf-8")
        self.assertIn("$targetExePath", installer)
        self.assertIn("$_.ExecutablePath", installer)
        self.assertNotIn("Get-Process -Name $processName", installer)

    def test_recipe_placement_spreads_across_ingredient_families(self):
        bridge = (ROOT / "plugin-src" / "GameBridge.cs").read_text(encoding="utf-8")
        self.assertIn("global * 2.399963229728653", bridge)
        self.assertNotIn("index * 2.399963229728653", bridge)
        self.assertIn("new Vector3(-3f + localX", bridge)

    def test_designer_panel_stays_clear_of_native_tab_rail(self):
        renderer = (ROOT / "plugin-src" / "PanelRenderer.cs").read_text(encoding="utf-8")
        self.assertIn("FitBesideTabRail(screenRect)", renderer)
        self.assertIn("tabScreenRect.xMax + gap", renderer)
        self.assertIn('"ui.panel_fitted"', renderer)

    def test_designer_panel_blocks_clicks_from_reaching_hidden_stock_controls(self):
        installer = (ROOT / "plugin-src" / "RuntimeTabInstaller.cs").read_text(encoding="utf-8")
        self.assertIn("blocker.raycastTarget = true", installer)

    def test_complete_header_is_centered_inside_the_close_button_safe_area(self):
        installer = (ROOT / "plugin-src" / "RuntimeTabInstaller.cs").read_text(encoding="utf-8")
        self.assertIn("rect.anchorMin = new Vector2(0.5f, 0f)", installer)
        self.assertIn("rect.anchoredPosition = new Vector2(-39f, 0f)", installer)
        self.assertIn("rect.sizeDelta = new Vector2(width, 8f)", installer)
        self.assertIn("close_reserve=78", installer)

    def test_music_uses_native_service_and_releases_one_clip_before_loading_the_next(self):
        deck = (ROOT / "plugin-src" / "MediaDeck.cs").read_text(encoding="utf-8")
        bridge = (ROOT / "plugin-src" / "GameBridge.cs").read_text(encoding="utf-8")
        self.assertNotIn("OnAudioFilterRead", deck)
        self.assertNotIn("ThreeBandEq", deck)
        self.assertIn("ReleaseLoadedClip();", deck)
        self.assertIn("audioReachedPlayback = true", deck)
        self.assertIn("if (musicSource.isPlaying)", deck)
        self.assertIn("new WWW(audioUrl)", deck)
        self.assertIn("request.GetAudioClip(false, false, AudioType.WAV)", deck)
        self.assertIn("loadedClip.loadState == AudioDataLoadState.Unloaded", deck)
        self.assertNotIn("DownloadHandlerAudioClip.GetContent", deck)
        self.assertIn("CacheWaveform(52);", deck)
        self.assertNotIn("cachedWaveform = new float[0];\n                    status = \"Playing \"", deck)
        self.assertIn("audio.StartMusic(clip", bridge)

    def test_barros_playlist_replaces_stock_by_default_and_stock_is_reversible(self):
        deck = (ROOT / "plugin-src" / "MediaDeck.cs").read_text(encoding="utf-8")
        bridge = (ROOT / "plugin-src" / "GameBridge.cs").read_text(encoding="utf-8")
        panel = (ROOT / "plugin-src" / "PanelRenderer.cs").read_text(encoding="utf-8")
        self.assertIn("barrosReplacesStock = true", deck)
        self.assertIn('audio.StartPreloadedMusic("PizzaCreator\\\\PizzaCreator"', bridge)
        self.assertIn('"BARRO\'S"', panel)
        self.assertIn('"STOCK"', panel)
        self.assertIn("if (barrosReplacesStock && currentIndex < 0", deck)
        self.assertIn("StopPlayback();\n            ReleaseLoadedClip();\n            barrosReplacesStock = false", deck)
        self.assertIn("if (game != null) game.StopMusic();", deck)

    def test_saved_music_queue_and_agent_speech_focus_are_wired(self):
        deck = (ROOT / "plugin-src" / "MediaDeck.cs").read_text(encoding="utf-8")
        panel = (ROOT / "plugin-src" / "PanelRenderer.cs").read_text(encoding="utf-8")
        for term in (
            "music-playlist.json",
            "ToggleQueued",
            "MoveQueued",
            "SavePlaylist",
            "LoadPlaylist",
            "NextPlaylistIndex",
            "BeginSpeechFocus",
            "EndSpeechFocus",
            "InboxRevision",
            "ConversionReportFile",
            "BassDb = bassDb",
            "AutoImport = autoImport",
            "UseBarros = barrosReplacesStock",
        ):
            self.assertIn(term, deck)
        self.assertIn("SAVE PLAYLISTS", panel)
        self.assertIn("RELOAD SAVED", panel)
        self.assertIn("Auto import", panel)
        self.assertIn("REPORT", panel)
        self.assertIn("new WaitForSecondsRealtime(pause)", panel)
        self.assertIn("pausedBeforeSpeech = paused", deck)
        self.assertIn("paused = true", deck)
        self.assertIn("do you want to save it to the recipe book now?", panel)

    def test_v15_library_roundtable_and_microphone_controls_are_scalable(self):
        deck = (ROOT / "plugin-src" / "MediaDeck.cs").read_text(encoding="utf-8")
        panel = (ROOT / "plugin-src" / "PanelRenderer.cs").read_text(encoding="utf-8")
        client = (ROOT / "plugin-src" / "BackendClient.cs").read_text(encoding="utf-8")
        for term in (
            "SearchOption.AllDirectories",
            "MediaNamedPlaylistState",
            "ActivePlaylistName",
            "CreatePlaylist",
            "DuplicatePlaylist",
            "RenamePlaylist",
            "DeletePlaylist",
            "AddVisible",
            "RemoveVisible",
        ):
            self.assertIn(term, deck)
        for term in (
            "VisibleMediaTracks",
            "BeginScrollView",
            "MediaFilters",
            "MediaSorts",
            "QueueAgentRoundtable",
            "agentSpeechQueue",
            "agentSpeechGeneration",
            "CurrentMicrophoneLevel",
            "SelectedMicrophoneDevice",
            "microphoneGain",
        ):
            self.assertIn(term, panel)
        self.assertIn("request.Rate = rate", client)

    def test_interactive_provider_requests_are_bounded_and_have_local_fallback(self):
        orchestrator = (ROOT / "backend" / "barros_ai" / "orchestrator.py").read_text(encoding="utf-8")
        client = (ROOT / "plugin-src" / "BackendClient.cs").read_text(encoding="utf-8")
        self.assertIn("timeout_seconds=45", orchestrator)
        self.assertIn("retries=0", orchestrator)
        self.assertIn("Online provider failed; used the built-in designer", orchestrator)
        self.assertIn("request.Timeout = 45000", client)

    def test_educational_and_audio_pipeline_assets_are_real_and_present(self):
        for relative in (
            "docs/ENGINEERING_PLAYBOOK.md",
            "docs/PROJECT_STATUS.md",
            "docs/AUDIO_PIPELINE.md",
            "scripts/Convert-BarrosMusic.ps1",
            "CONVERT_BARROS_MUSIC.bat",
            "tools/build_release.py",
        ):
            path = ROOT / relative
            self.assertTrue(path.is_file(), path)
            self.assertGreater(path.stat().st_size, 100, path)

        converter = (ROOT / "scripts" / "Convert-BarrosMusic.ps1").read_text(encoding="utf-8")
        self.assertIn(r"S:\Unity_Games\PC3 - Pizza Creator\Barros_Music", converter)
        self.assertIn('"libvorbis"', converter)
        self.assertIn("conversion-manifest.json", converter)

        release_builder = (ROOT / "tools" / "build_release.py").read_text(encoding="utf-8")
        self.assertIn("ALLOWED_ARTIFACTS", release_builder)
        self.assertIn("artifacts/Barros.PizzaCreator.AI.dll", release_builder)
        self.assertIn('(\"backend\", \"data\", \"inspiration\")', release_builder)

        manifest_paths = {
            line.split("  ", 1)[1]
            for line in (ROOT / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
        }
        self.assertEqual(
            {
                "artifacts/Barros.PizzaCreator.AI.dll",
                "artifacts/README.md",
                "artifacts/build-provenance.json",
            },
            {path for path in manifest_paths if path.startswith("artifacts/")},
        )

        music_readme = (ROOT / "assets" / "music" / "README.md").read_text(encoding="utf-8")
        self.assertIn("supplied by the project owner", music_readme)
        self.assertIn("Unity-friendly, audio-only 48 kHz stereo OGG/Vorbis", music_readme)
        ogg_tracks = sorted((ROOT / "assets" / "music").glob("*.ogg"))
        source_mp3 = sorted((ROOT / "assets" / "music").glob("*.mp3"))
        self.assertEqual(5, len(ogg_tracks))
        self.assertEqual(5, len(source_mp3))
        self.assertTrue(all(path.stat().st_size > 500_000 for path in ogg_tracks))
        self.assertIn('path.suffix.lower() == ".mp3"', release_builder)


if __name__ == "__main__":
    unittest.main()
