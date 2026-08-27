# Creator 1.3 RC1 — beginner help and distribution contract

## What this repository is

This is the public, reversible runtime mod for the standalone Creator at
`S:\Unity_Games\PC3 - Pizza Creator`. It adds one fifth tab in memory and uses
the exact live catalog/service routes documented by the private source authority.
It does not contain or replace stock Unity containers.

## Beginner interaction

1. Open the Creator's Bakehouse.
2. Select the first new tab beneath the four stock tabs.
3. Hover any major mode/action button for plain-language help.
4. Describe a pizza or choose Chat, AI Lab, Design Crew or Chef Voice.
5. Preview first. Apply changes the live editor but does not save automatically.
6. Save to the recipe book only after review; export stock JPG is visual output,
   not editable recipe data.
7. Use the proof runner to retain apply/save/reload/export/restore evidence.

## Package types

- **Windows package manager EXE** installs the management files and shortcuts;
  its setup stage does not silently mutate a game tree.
- **Windows portable ZIP** contains the one-click guarded installer. The exact
  plug-in DLL is rebuilt locally against the installed Creator assemblies when
  the checked-in artifact provenance is not current.
- **VPS/headless ZIP** contains only the Python sidecar, contracts and help. It
  binds to `127.0.0.1`; from Windows use an SSH local-forward such as:

```powershell
ssh -L 48173:127.0.0.1:48173 USER@VPS_HOST
```

Direct `0.0.0.0`, LAN and Internet binding is blocked because the sidecar is not
a public multi-user service. Provider credentials remain external and are never
packaged.

## Proof boundary

Linux tests can prove backend, schema, contract and package behavior. Only the
real Windows Creator can prove DLL compatibility, tab placement, stock-tab
regression, font/sprite fidelity, microphone behavior, recipe mutation,
persistence, JPG export and exact restore.
