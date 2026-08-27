# Barro's Pizza Creator 1.4 runtime proof — 2026-08-27

The final `1.4.0-rc1` build was compiled against and installed into the real Steam **Pizza Connection 3 - Pizza Creator 0.11.272** folder on Windows 11. The installed DLL is 129,536 bytes with SHA-256 `0A56A95F336EA1D671C32078B43EBD0B22EDE44C2895F3189A54C65A66282342`. The original game assemblies and unrelated PC2/PC3 projects were not modified.

| Gate | Result | Retained proof |
|---|---|---|
| Exact installed-game compile | PASS | Zero compiler errors against Creator 0.11.272, Unity 2017.3.1p4 and BepInEx 5.4.23.5; artifact/provenance hashes agree. |
| Automated suite | PASS | 102/102 tests passed. |
| Final five-tab UI | PASS | Chat, AI Lab and Media were opened in the real game; the panel remained inside the right column and all five native side tabs stayed visible. |
| Five-song library and queue | PASS | Media displayed 5 of 5 bundled songs, all queued in the saved order. Earlier guided clicks individually reached real playing/PAUSE state on every song. |
| Queue editing | PASS | Include/exclude did not delete the library file; Up/Down, Select All, Clear, Save Queue and Load Saved behaved correctly. The final saved queue contains all five songs. |
| Stock/Barro's exclusivity | PASS | Switching to Stock displayed `Stock ON · Barro's OFF`; switching back displayed `Barro's ON · Stock OFF` and restored custom playback. |
| Pause/resume and progression | PASS | Pause/resume retained the current song. During the final soak the real player advanced from song 1 to song 2 and had reached song 4 after ten minutes without a process restart. |
| Ten-minute stability soak | PASS | 21/21 game, sidecar-process and `/health` samples passed over 603.534 seconds; relevant runtime error lines remained zero. See `docs/evidence/media-soak-2026-08-27.json`. |
| Bundled audio quality | PASS | 5/5 OGG files contain one Vorbis audio stream only, decode completely, use 48 kHz stereo, and measure between -13.7 and -12.8 LUFS with -0.9 to -0.8 dBFS peaks. See `docs/evidence/audio-quality-audit.json`. |
| Runtime auto import | PASS | A live MP3 drop was detected without restarting, converted to audio-only OGG, decode-validated, measured, and added as library-only while the saved startup queue stayed at five. The temporary file was then removed from the live library. See `docs/evidence/runtime-auto-import-report.json`. |
| On-screen import quality result | PASS | The installed Media tab displayed `48 kHz stereo · Vorbis q8 · -14 LUFS · -1 dBTP` after Import + Refresh. |
| Music ducking before agent speech | STATIC PASS / RUNTIME NOT RUN | The one-second pause, prior-playing-state retention and conditional resume paths compile and pass contract tests. Azure Speech is not configured on this PC, so audible agent-speech interaction is not claimed. |
| Microphone transcription | BLOCKED BY DEVICE | Windows exposes no usable microphone to this build; the UI truthfully shows `No mic` and STT fails closed. |
| Subjective audible smoothness | USER LISTENING CHECK | The concrete stutter risks found here were removed: embedded cover-art video streams, live waveform sampling during playback, streaming download and unrepaired timestamps. Runtime stability and transitions pass, but the automation channel cannot judge speaker output by ear. |

## Media behavior delivered

- One native music source is used, so stock and Barro's music cannot overlap.
- The five owner songs are bundled as audio-only, high-quality OGG files.
- New MP3/WAV/OGG-compatible files can be auto-imported without rebuilding the mod; converted files are hashed, decoded and measured in `conversion-report.json`.
- The library is non-destructive. A separate saved queue controls inclusion, order, shuffle, repeat, volume, bass/mid/treble, auto-import and preferred startup soundtrack.
- Current song, next song, queue position, waveform, seek, previous/next, pause and stop are visible in the Media tab.
- Agent speech pauses active music one second before synthesis and resumes it only when speech ends and only when music had been playing.

The final live screenshots are `docs/evidence/live-v14-media-quality-2026-08-27.png` and `docs/evidence/live-v14-media-post-soak-2026-08-27.png`.
