# Barro's music conversion pipeline

Five project-owner-supplied songs are included as verified game-ready OGG files. The standalone converter can also process the owner's larger source library from `S:\Unity_Games\PC3 - Pizza Creator\Barros_Music`, while the in-game import inbox accepts new files without rebuilding the plugin.

## One-click conversion

1. Install an FFmpeg Windows build that includes `libvorbis` and place `ffmpeg.exe` on `PATH`, or pass its exact path to the PowerShell script.
2. Double-click `CONVERT_BARROS_MUSIC.bat`.
3. Find the converted tracks and `conversion-manifest.json` under `S:\Unity_Games\PC3 - Pizza Creator\Barros_Music\converted-ogg`.

Equivalent explicit command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Convert-BarrosMusic.ps1 `
  -SourceDirectory "S:\Unity_Games\PC3 - Pizza Creator\Barros_Music" `
  -Quality 8 -SampleRate 48000 -Channels 2 `
  -LoudnessTarget -14 -TruePeak -1
```

The converter recursively accepts WAV, MP3, FLAC, M4A, AAC, WMA, AIFF, Opus and OGA. Existing `.ogg` files are left alone unless `-IncludeExistingOgg` is supplied. It preserves the relative directory structure, selects only the first audio stream, repairs timestamp continuity, removes cover-art/video/subtitle/data streams and source metadata, applies a consistent -14 LUFS / -1 dBTP safety profile, and encodes 48 kHz stereo Ogg Vorbis through `libvorbis` quality 8. It then decodes each new file back to a null sink to detect corruption and records source/output SHA-256 values. It writes through a temporary file so a failed encode cannot masquerade as a completed track.

FFmpeg documents `libvorbis` quality as VBR values from `-1` through `10`, with higher values producing higher quality. This release uses `8` to reduce additional loss when an owner-supplied MP3 is transcoded. Loudness leveling cannot restore detail absent from a source file; it keeps songs consistently strong while true-peak protection prevents digital clipping. The original owner-supplied file remains in the import inbox.

## Runtime behavior

The Media Deck downloads a decoded 48 kHz stereo WAV from the local helper, creates a non-streaming in-memory Unity clip, prepares the waveform while playback is stopped, and then hands it to Pizza Creator's one native music source. That makes Barro's and Stock mutually exclusive: choosing a Barro's track replaces stock music; choosing Stock stops and releases the custom clip before restoring the preloaded Creator soundtrack. New files placed in the import inbox are converted to audio-only OGG on Refresh when FFmpeg is available. The saved play queue controls startup inclusion and order without deleting library files. Agent speech pauses the active soundtrack one second before voice playback and resumes it only after speech ends.

Only distribute tracks for which you have the necessary rights. The release bundles the five explicitly owner-supplied songs, but it does not redistribute FFmpeg or any unrelated music.

Primary references:

- [FFmpeg libvorbis encoder documentation](https://ffmpeg.org/ffmpeg-codecs.html#libvorbis)
- [Unity 2017.3 Ogg Vorbis audio type](https://docs.unity3d.com/2017.3/Documentation/ScriptReference/AudioType.OGGVORBIS.html)
- [Unity 2017.3 audio-clip download API](https://docs.unity3d.com/2017.3/Documentation/ScriptReference/Networking.UnityWebRequestMultimedia.GetAudioClip.html)
