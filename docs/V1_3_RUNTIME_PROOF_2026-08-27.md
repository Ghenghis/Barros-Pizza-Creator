# Barro's Pizza Creator v1.3 runtime proof

Proof date: 2026-08-27. Target: the standalone Steam `Pizza Connection 3 - Pizza Creator` 0.11.272 build on Windows 11, Unity 2017.3.1p4 x64. This is not a claim about the separate Pizza Connection 3 game or a Unity Hub project.

## Result

| Surface | Result | Retained evidence |
|---|---|---|
| Exact assembly build | PASS | `Barros.PizzaCreator.AI.dll` is 82,944 bytes, SHA-256 `0960AD3A1B820ACE9C2F83D56240006A64CD00C4390635396808677903954D9B`. `artifacts/build-provenance.json` binds it to the exact Creator assemblies and BepInEx 5.4.23.5. |
| Automated suite | PASS | 88/88 tests passed on Windows 11 after the final bounded-agent change. Coverage includes all 87 exact ingredients, seven artwork templates, exact placements, custom pixel maps, dietary palettes, deterministic remixes, HTTP contracts, Azure request formatting and safe fallback behavior. |
| Loader and fifth tab | PASS | The BepInEx log records plugin 1.3.0, sidecar start, live service/database injection and fifth-tab installation. |
| UI fit | PASS | Runtime event: `left=1346; right=1920; width=574; tab_right=1340; gap=6`. All five native tabs remained visible. |
| High-detail Santa compilation | PASS | The built-in compiler returned immediately without waiting for the slow text gateway and generated 176 exact, bounded pieces. |
| Native 3D preview | PASS | `action.preview.success` records `artwork=santa`, `detail=high`, `placements=176`, and the deterministic role-raster algorithm. The retained screenshot visibly shows a red hat, white beard/hair, eyes, nose, moustache and mouth rendered from real game ingredients. |
| Native apply | PASS | `action.apply.success` records the same 176-piece Santa plan applied to the live pizza. Native Save/reload was not exercised. |
| Design Crew menu | PASS | Four distinct agents, ASK controls, a combined review control, per-agent UK/Australian voice labels, mute/setup state and stop control fit in the panel. |
| Focused MiniMax agent interaction | PASS | In the real game, Creative Director returned a focused `Desert Fire` review with concrete Arizona ingredient and presentation suggestions. The configured gateway completed within the bounded request window. |
| Slow-gateway fallback | PASS | A provider stall is limited to one 25-second attempt with no retry chain. On the final installed DLL, the real gateway timed out and the Creative Director returned `Local fallback: The name and placement pattern give this pizza a recognizable signature.` The game remained responsive and displayed the focused review normally. |
| Azure design-agent speech | READY, NOT CONFIGURED | The current health response reports `tts_configured=false`, provider `disabled`, and `reachability=not_probed`. Voice mapping, SSML request, WAV validation/playback code, mute and stop controls passed compile/tests, but no Azure key was configured and no sound was claimed as heard. |
| Microphone/STT | BLOCKED | Windows exposed no usable input device during this run and no dedicated STT endpoint is configured. The UI truthfully displays `No mic`. |

## Retained screenshots

| File | Bytes | SHA-256 |
|---|---:|---|
| `docs/evidence/live-v13-santa-art-preview-2026-08-27.png` | 1,999,241 | `D4D2C61E61878F54E02F5691EE19B8A9C57FE78AEB45BD0F91430908B706BDA2` |
| `docs/evidence/live-v13-santa-art-panel-2026-08-27.png` | 2,035,760 | `CF9112191E395B0C8CAF9248B8AEB870D28A5101B49B7AB339B31D5101737F62` |
| `docs/evidence/live-v13-agent-voices-menu-2026-08-27.png` | 1,988,962 | `ACDB7BFA0E31B140B8AD23893A0FF3114772C1800A9CE992DA868AF56E9FA259` |
| `docs/evidence/live-v13-creative-director-response-2026-08-27.png` | 1,802,216 | `6757C3177CA475E410C8464F7EC5AB6D036B1431F8BA2E29179EEAA10ABF6CC6` |
| `docs/evidence/live-v13-creative-director-fallback-2026-08-27.png` | 1,778,865 | `FFBDC3CF69049E4ED00CB64E2CD68BF989EBA930029919FA38B1D0AE02C3A2F2` |

## Live health snapshot

The installed sidecar returned `ok=true`, version `1.3.0-rc1`, provider `openai-compatible`, `online=true`, and advertised `pizza_art`, `crew`, `chat`, `lab`, ingredient intelligence and inspiration-library capabilities. Its four speech profiles were Maisie/UK, Darren/Australia, Ryan/UK and Carly/Australia, while speech itself remained disabled until explicitly configured.

## Failure found and repaired during proof

The first high-detail Santa request timed out because the provider's configured retry window could outlive the Unity client's request window. Built-in art templates now compile locally, so Santa/face/heart/tree/smiley/snowman/star do not wait for a remote text provider. Crew review now builds its valid draft locally and gives each persona one bounded provider attempt, with a useful local fallback.

No unrelated PC2 or PC3 repository was modified by this v1.3 implementation or proof run.
