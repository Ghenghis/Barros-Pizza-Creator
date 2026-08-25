# Barro's music conversion pipeline

The supplied music directory is expected at `S:\Unity_Games\PC3 - Pizza Creator\Barros_Music`. Audio files were not mounted in the portable analysis workspace, so no track is claimed as converted and no placeholder music is shipped.

## One-click conversion

1. Install an FFmpeg Windows build that includes `libvorbis` and place `ffmpeg.exe` on `PATH`, or pass its exact path to the PowerShell script.
2. Double-click `CONVERT_BARROS_MUSIC.bat`.
3. Find the converted tracks and `conversion-manifest.json` under `S:\Unity_Games\PC3 - Pizza Creator\Barros_Music\converted-ogg`.

Equivalent explicit command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Convert-BarrosMusic.ps1 `
  -SourceDirectory "S:\Unity_Games\PC3 - Pizza Creator\Barros_Music" `
  -Quality 5 -SampleRate 44100 -Channels 2
```

The converter recursively accepts WAV, MP3, FLAC, M4A, AAC, WMA, AIFF, Opus and OGA. Existing `.ogg` files are left alone unless `-IncludeExistingOgg` is supplied. It preserves the relative directory structure and metadata, encodes Ogg Vorbis through `libvorbis`, decodes each new file back to a null sink to detect corruption, and records source/output SHA-256 values. It writes through a temporary file so a failed encode cannot masquerade as a completed track.

FFmpeg documents `libvorbis` quality as VBR values from `-1` through `10`, with higher values producing higher quality. RC1 uses `5` as a balanced archival/game setting. Unity 2017.3 exposes Ogg Vorbis as `AudioType.OGGVORBIS` and can construct an `AudioClip` through `UnityWebRequestMultimedia.GetAudioClip`.

## Deliberate release boundary

Conversion is complete tooling; automatic in-game background-music replacement is not part of the RC1 runtime contract. Adding playback safely requires one live decision: which stock mixer group and volume setting the Creator scene should use. That must be observed in the target runtime rather than guessed. Until then, converted files remain user-owned staging assets and are not copied elsewhere automatically.

Only distribute tracks for which you have the necessary rights. The project does not bundle FFmpeg or any music.

Primary references:

- [FFmpeg libvorbis encoder documentation](https://ffmpeg.org/ffmpeg-codecs.html#libvorbis)
- [Unity 2017.3 Ogg Vorbis audio type](https://docs.unity3d.com/2017.3/Documentation/ScriptReference/AudioType.OGGVORBIS.html)
- [Unity 2017.3 audio-clip download API](https://docs.unity3d.com/2017.3/Documentation/ScriptReference/Networking.UnityWebRequestMultimedia.GetAudioClip.html)
