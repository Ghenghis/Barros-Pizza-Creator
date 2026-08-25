# Upstream tooling and compatibility audit

Audited 2026-08-25. Primary vendor documentation and upstream repositories were preferred over forum recipes. Online research cannot replace a live test of this proprietary Unity scene; it can remove tool and API uncertainty around that test.

## Decisions retained

| Area | Upstream evidence | Project decision |
|---|---|---|
| Loader family | [BepInEx 5 plugin guide](https://docs.bepinex.dev/v5.4.11/articles/dev_guide/plugin_tutorial/2_plugin_start.html) documents `BaseUnityPlugin`, `BepInPlugin`, game-DLL references, and deployment under `BepInEx/plugins`. | Keep BepInEx 5 x64; compile against local PC3 Managed DLLs; deploy to a dedicated plugin directory. |
| Process isolation | The same BepInEx guide documents `BepInProcess` for restricting a plugin to named executables. | RC1 is restricted to `Pizza Connection 3 - Pizza Creator.exe`. |
| Loader artifact | [BepInEx v5.4.23.5 release](https://github.com/BepInEx/BepInEx/releases/tag/v5.4.23.5) is the pinned upstream release. | Installer downloads the x64 archive and requires SHA-256 `82f987…32c4`; the independently downloaded archive matched. |
| Loader diagnostics | [BepInEx troubleshooting](https://docs.bepinex.dev/articles/user_guide/troubleshooting.html) identifies bitness, loader logs, entry points, and older-Unity proxy issues as first checks. | Proof harness retains `BepInEx/LogOutput.log`; no Harmony patching is required by this plugin. |
| Screenshot capture | [Unity 2017.3 `ScreenCapture.CaptureScreenshot`](https://docs.unity3d.com/2017.3/Documentation/ScriptReference/ScreenCapture.CaptureScreenshot.html) is the engine-native screenshot path. | F8 and automatic action captures use the exact `UnityEngine.ScreenCaptureModule.dll` from the supplied build. |
| Microphone | [Unity 2017.3 `Microphone.devices`](https://docs.unity3d.com/2017.3/Documentation/ScriptReference/Microphone-devices.html), [`Microphone.Start`](https://docs.unity3d.com/2017.3/Documentation/ScriptReference/Microphone.Start.html), and [`Microphone.GetPosition`](https://docs.unity3d.com/2017.3/Documentation/ScriptReference/Microphone.GetPosition.html) define device enumeration and capture progress. | Enumerate before starting; capture mono/stereo data at 16 kHz; retain device count, sample count, and WAV byte count as proof events. |
| Speech request | [OpenAI speech-to-text guide](https://platform.openai.com/docs/guides/speech-to-text) uses multipart audio transcription requests. | Sidecar sends `model` plus WAV `file` to an OpenAI-compatible `/v1/audio/transcriptions`; a deterministic unit test now checks URL, authorization, content type, model, filename, and audio bytes. |
| Local SDK | [Microsoft's non-admin .NET install guidance](https://learn.microsoft.com/en-us/dotnet/core/install/linux-scripted-manual) supports local SDK extraction. | A local Roslyn compiler was used only for certification; no machine-wide toolchain was changed or shipped. |
| PowerShell validation | [Microsoft's binary-archive guidance](https://learn.microsoft.com/en-us/powershell/scripting/install/alternate-install-methods) supports portable PowerShell. | The proof scripts were parsed and executed under a verified portable PowerShell 7.6.5; user-facing scripts remain Windows PowerShell 5.1-compatible syntax. |
| Ogg conversion | [FFmpeg's libvorbis documentation](https://ffmpeg.org/ffmpeg-codecs.html#libvorbis) defines the VBR quality range and [Unity 2017.3](https://docs.unity3d.com/2017.3/Documentation/ScriptReference/Networking.UnityWebRequestMultimedia.GetAudioClip.html) exposes decoded audio clips with `AudioType.OGGVORBIS`. | Add a hash-manifested, decode-validated conversion tool; defer automatic scene playback until the live mixer group is observed. |
| GitLab publication | [GitLab's existing-project push documentation](https://docs.gitlab.com/topics/git/project/) and [repository mirroring docs](https://docs.gitlab.com/user/project/repository/mirror/) cover normal pushes and mirror topology. | Preserve the GitLab repository's initial commit, then publish the same reviewed source snapshot and CI contract rather than force-erasing its history. |

## Searches that did not change the architecture

- Harmony or native detours are unnecessary: the exact decompiled build exposes the needed public service and tab-registration paths.
- Replacing `Assembly-CSharp.dll`, rewriting saves directly, and mouse automation add risk without solving an uncovered requirement.
- A standalone companion window would make visual matching easier but would not satisfy the user's in-game fifth-tab requirement.
- A research-paper scoring model is not needed for the release gate because the exact game already exposes citizen taste/popularity and cost/profit calculations; Novelty and Originality remain explicitly labeled deterministic heuristics.

## Remaining knowledge that only the target run can supply

1. The live scene's realized `RectTransform` sizes at the user's display scaling and supported resolutions.
2. Whether BepInEx's proxy loads normally on this exact Windows installation.
3. Whether the stock `PizzaLoaded` flow and active tab ordering match the decompiled behavior at runtime.
4. Windows microphone availability/permission and the configured STT endpoint's actual response.
5. Pixel and interaction differences between the four live captures and the four reference images.

Those are isolated in L2-L6 of `contracts/rc1.acceptance.json`; no further internet search can truthfully promote them.
