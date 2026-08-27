# Barro's music library

These five MP3 tracks were supplied by the project owner from the private Google Drive `Barros_Music` folder on 2026-08-27 for inclusion in Barro's Pizza Creator v1.4.

The source folder also contained WAV copies of the same songs. Each MP3 was converted to a Unity-friendly, audio-only 48 kHz stereo OGG/Vorbis quality-8 copy with timestamp repair, a -14 LUFS loudness target and -1 dBTP peak protection for dependable background playback in the Creator's Unity 2017 runtime. Each output has exactly one audio stream and was fully decoded during validation. The large duplicate WAV files are not packaged.

The Media Deck scans this folder at runtime for `.ogg`, `.mp3`, `.wav`, and `.mp4` files. Users can add more project-owned music or lyric videos without rebuilding the plugin. The editable saved queue controls inclusion, order, shuffle, repeat and startup playback without deleting library files. Release packaging prefers the OGG copies; the MP3 files remain source material in the development tree.

No cloud credentials, private Drive links, or access tokens are stored here.
