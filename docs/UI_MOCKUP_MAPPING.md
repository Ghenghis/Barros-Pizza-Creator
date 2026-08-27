# UI mockup mapping

The original four reference images are under `docs/mockups/`. The implemented workspace has evolved into five top-level mode buttons—Chat, AI Lab, Crew, Voice and Media—inside one chef-chat side tab so the stock side rail does not become crowded.

| Mockup | Implemented mode | Directly represented controls |
|---|---|---|
| `01_chat.png` | Chat | Online pill, Build with me / Surprise me / Improve this, user/assistant history, exact recipe card, six scores, Preview, Apply, attachment, microphone and send |
| `02_lab.png` | AI Lab | Constraint chips, Surprise me, three candidate cards, score bars, Preview/Use, rationale and Generate 3 more |
| `03_crew.png` | Design Crew | Four named agent rows, ready states, consensus card, flavor/profit/popularity/originality bars, discussion log, Balanced/Max flavor/Max profit and Apply crew recipe |
| `04_voice.png` | Chef Voice | Listening state, live waveform, microphone control, transcript, heat choice, AI draft and recipe actions |
| Runtime extension | Media Deck | Exclusive Stock/Barro's switch, waveform/seek, synchronized audio lyrics, portrait lyric video, playlists, search, ordering and import |

The color system uses the Creator's parchment background, lighter recipe cards, dark-brown text, maroon controls, brighter-red primary actions, green readiness/profit and amber cost. The panel is scaled into the actual recipe-content `RectTransform`, preserving the pizza canvas and the existing Bakehouse header.

`authoring/BarrosCreatorUiLab2021` is the editable visual source for future UI polish. Its protected dark rail models the five original game tabs, its Barro's panel uses the same 640×1050 virtual size as the plug-in, and its exporter writes the rounded PNG skins consumed by the live runtime. The proof scene and its Game view must be checked at 1920×1080 before an export is accepted.

While the AI tab is active, `assets/barros-pizza-creator-header.png` is aspect-fitted into the long title strip highlighted in the supplied header markup. It reads **BARRO'S PIZZA CREATOR**, reserves space for the original close button, and is removed when another stock tab becomes active. The full-resolution generated source is retained under `docs/branding/`.

## Interaction details beyond the static images

- F10 activates the AI tab.
- Shape and heat cycle from the bottom composer.
- PNG/JPG/WEBP attachments reach vision-capable providers as data images; JSON/TXT/Markdown becomes bounded text context.
- History is written locally and the in-session transcript can be collapsed.
- Preview and Apply both use live 3D placement; Preview retains a restore point.
- The game's own recipe-book save remains available inside every result card.
