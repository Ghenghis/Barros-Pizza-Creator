# RC1 execution and proof contract

`RUN_RC1_PROOF.bat` and `contracts/rc1.acceptance.json` retain their historical filenames for existing Workbench/Studio integrations. Their active release value is now `1.2.0-rc2`; the filename is not a claim that the v1.2 source has passed Windows runtime certification.

This project is a real BepInEx/Unity integration. The four supplied images are visual reference baselines only. They never count as runtime evidence.

## Operating rule

Every claim is one of `not_run`, `pass`, `fail`, or `blocked`. A gate becomes `pass` only when its command ran against the stated target and its evidence was retained. Code presence, a plausible decompilation path, or another gate's success cannot promote it.

The canonical machine-readable contract is `contracts/rc1.acceptance.json`. `scripts/Invoke-ProofContract.ps1` creates an immutable timestamped run folder containing `results.json`, `summary.md`, command output, relevant hashes, and copied runtime logs.

## Dependency order

| Layer | Question answered | Blocks |
|---|---|---|
| L0 Source/package | Is the checked-in implementation internally complete and deterministic? | Every later layer |
| L1 Exact build | Does it compile against this supplied PC3/Unity/BepInEx ABI? | Loader and runtime |
| L2 Loader | Does BepInEx actually discover and initialize it? | UI and actions |
| L3 UI geometry | Is the fifth tab live, fitted, and branded without obstructing stock controls? | Visual certification |
| L4 Native actions | Do Preview, Restore, Apply, Save, and reload manipulate the real game state? | Release certification |
| L5 Voice | Does a real microphone and configured STT endpoint complete a transcript round-trip? | Voice certification |
| L6 Visual comparison | How closely do four live modes reproduce the reference targets? | Final UI sign-off |

No layer is skipped to make a percentage look better. Work proceeds with the cheapest upstream failure first.

## Commands

Static package proof (safe anywhere with Python 3):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Invoke-ProofContract.ps1 -Stage Static
```

The harness deliberately captures Python's stdout and stderr before checking
its process exit code. Python's verbose `unittest` runner writes normal test
progress to stderr; Windows PowerShell otherwise converts those lines into
`NativeCommandError` records, which can incorrectly terminate a script using
`$ErrorActionPreference = "Stop"`. A zero Python exit code remains the only
condition that passes `SRC-002`, and the complete merged output is retained as
`backend-tests.txt`.

Exact Windows build proof:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Invoke-ProofContract.ps1 `
  -Stage Build -GameRoot "S:\Unity_Games\PC3 - Pizza Creator"
```

Runtime evidence after launching the game and exercising the acceptance flow:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Invoke-ProofContract.ps1 `
  -Stage Runtime -GameRoot "S:\Unity_Games\PC3 - Pizza Creator"
```

Full certification requires all release-required gates:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Invoke-ProofContract.ps1 `
  -Stage All -RequireComplete -GameRoot "S:\Unity_Games\PC3 - Pizza Creator"
```

## Evidence retention

Local runs go under `evidence/runs/<UTC timestamp>/` and are intentionally excluded from source control because logs and prompts may contain machine paths or private provider details. A reviewed, redacted proof bundle can be attached to the public release.

The required final bundle is:

- exact game and plugin SHA-256 values;
- compiler output;
- BepInEx loader log;
- structured runtime event log;
- screenshots for fifth tab, header, Chat, Lab, Crew, Voice, Preview, Restore, Apply, and reload;
- visual comparison report for all four reference modes;
- a saved/reloaded recipe comparison.

Inside the live AI tab, **F8** captures the current Chat/Lab/Crew/Voice mode using the exact filenames expected by the comparison harness. After saving a recipe, press **F9**; the plugin reads the persisted JSON through PC3's `ISerializerService`, resolves ingredient references from the native database, requests `LoadPizzaFromModel`, waits for the event-driven load, and compares the live model with the disk-deserialized model down to dough positions, ingredient IDs/sizes/transforms, name, and profit factor. **Export stock JPG** separately proves the stock screenshot-only UI and `ScreenCapture` pipeline.

Run the objective panel comparison after all four F8 captures:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Compare-ReferenceImages.ps1 `
  -LiveRoot "S:\Unity_Games\PC3 - Pizza Creator\BarrosAI\evidence\screenshots"
```

It normalizes both images, measures right-panel mean absolute pixel error and edge intersection-over-union, writes one JSON report plus one difference image per mode, and still requires a human check for legibility and control access.

## Stop/go rules

- Hash mismatch: stop before compiling or copying a plugin.
- Compile failure: stop before loader testing.
- Loader exception: stop before judging layout or recipe actions.
- UI geometry failure: actions may be tested with F10, but visual sign-off stays blocked.
- Native action failure: do not test Save/reload on that candidate.
- Missing microphone/provider: offline/chat features remain testable; voice remains `blocked`, never `pass`.
- Missing screenshot: visual gate remains `not_run` even if the UI looked correct interactively.
