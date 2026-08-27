# Barro's music library

Five MP3 tracks and four lyric videos were supplied by the project owner from the private Google Drive `Barros_Music` folder on 2026-08-27 for inclusion in Barro's Pizza Creator v1.6.

The source folder also contained WAV copies of the same songs. Each MP3 was converted to a Unity-friendly, audio-only 48 kHz stereo OGG/Vorbis quality-8 copy with timestamp repair, a -14 LUFS loudness target and -1 dBTP peak protection for dependable background playback in the Creator's Unity 2017 runtime. The four lyric videos were normalized to H.264 High/yuv420p video plus 48 kHz stereo AAC audio with fast-start metadata and then fully decoded during validation. The large duplicate WAV files and duplicate local `(1)` video are not packaged.

The Media Deck scans this folder at runtime for `.ogg`, `.mp3`, `.wav`, and `.mp4` files. A same-name `.lrc` file adds synchronized line highlighting to any audio track; pausing, resuming or seeking keeps the displayed line aligned. Users can hide visual/timed lyrics without stopping playback and can add more project-owned music or lyric videos without rebuilding the plugin. The editable saved queue controls inclusion, order, shuffle, repeat and startup playback without deleting library files. Release packaging prefers the OGG copies; the MP3 files remain source material in the development tree.

No cloud credentials, private Drive links, or access tokens are stored here.
