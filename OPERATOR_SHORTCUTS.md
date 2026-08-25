# Barro's Pizza Creator 1.1 — Operator Shortcuts

No-CLI Windows entry points for the **Pizza Connection 3 / Barro's Pizza** Creator ecosystem.

| Double-click | Purpose | Truth effect |
|---|---|---|
| `INSTALL_Barros_AI_Designer.bat` | Install Creator against exact `creator-0.11.272` assemblies | install gate only after hashes match |
| `CONFIGURE_AI_PROVIDER.bat` | Configure provider/voice settings | configuration only |
| `DIAGNOSE_Barros_AI.bat` | Fast Creator install/backend diagnostics | diagnostic evidence |
| `RUN_RC1_PROOF.bat` | Execute layered Creator proof contract | updates only actually executed gates |
| `RUN_ECOSYSTEM_CHECKS.bat` | Audit Creator + Workbench + Studio roots, Git SHAs, contracts and tests | portable ecosystem evidence, not live GUI/game proof |
| `CONVERT_BARROS_MUSIC.bat` | Convert approved music inputs through the documented pipeline | audio pipeline evidence only |
| `SYNC_GITLAB_SAFE.bat` | Non-force GitLab sync with ancestry and final SHA verification | publication proof after remote SHA matches |
| `UNINSTALL_Barros_AI_Designer.bat` | Remove Creator plugin/sidecar without rewriting stock assemblies | controlled rollback |

## Creator proof target

Creator proof is valid only for **0.11.272 / Unity 2017.3.1p4** with the exact locked `Assembly-CSharp.dll` and `Assembly-CSharp-firstpass.dll` hashes in `contracts/pc3-build-compatibility.json`.

Runtime Proof Studio's `1.11.403 / Unity 2017.4.40f1` game root is a different target and must not be substituted.
