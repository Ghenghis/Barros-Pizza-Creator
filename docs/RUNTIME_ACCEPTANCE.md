# Windows runtime acceptance

Run this checklist against `S:\Unity_Games\PC3 - Pizza Creator` after installation.

## Automated

1. Double-click `DIAGNOSE_Barros_AI.bat`.
2. Confirm PASS for game executable, exact managed assembly, BepInEx core, AI plugin, private Python, backend source, provider settings and packaged backend tests.
3. After one game launch, confirm PASS for “Plugin observed by loader” and “Runtime tab installed.”

## Visual and functional smoke

1. Launch the standalone Creator and enter Bakehouse.
2. Confirm the new chef-chat icon appears under the existing side tabs.
3. Confirm the compact **BARRO'S PIZZA CREATOR** banner aspect-fits in the title strip, the close button remains visible/clickable, and **Bakehouse** returns after selecting a stock tab.
4. Confirm Chat, AI Lab, Design Crew and Chef Voice stay inside the right panel at the game's supported resolutions.
5. In Chat, request: `Use chicken, bacon and jalapeno; medium heat; keep it profitable.`
6. Confirm the card contains only exact catalog IDs, then choose Preview.
7. Confirm real 3D pieces appear and the UI returns to the AI tab.
8. Choose Start over and confirm the previous pizza returns.
9. Generate three Lab candidates and Preview/Use each one.
10. Ask the Crew and confirm four independent log rows plus consensus.
11. With an STT provider configured, record a short voice request and confirm transcription becomes the prompt.
12. Attach a small reference image and confirm a vision-capable provider uses it.
13. Apply a recipe, save it to the recipe book, reload it through the stock recipe list, and confirm name, shape, placements and profit factor survive.

## Evidence to retain

- `BepInEx\LogOutput.log`
- the timestamped diagnostics report
- one screenshot per mode
- one saved/reloaded AI recipe

If any native step fails, keep the game closed while changing files and send the diagnostic report with the BepInEx log. Do not replace `Assembly-CSharp.dll`.
