# Barro's Pizza Creator 1.6 Windows release

Release date: 2026-08-27

## Deliverables

| File | Bytes | SHA-256 |
|---|---:|---|
| `Barros_Pizza_Creator_v1.6.0_Setup.exe` | 90,517,927 | `fc1af74cc8a0fdd89bd5794b2b310cadf38ac34ce38e1b4a32dc78d1d5699d94` |
| `Barros_Pizza_Creator_v1.6.0_Portable.zip` | 88,254,229 | `211f5465a7973d16f86664a602eb9ae0dad752479975de3af4fa1d84aca74dbe` |

The Setup EXE is a normal Windows installer with a modern wizard, game-folder detection, exact-build verification, Start-menu shortcuts, optional desktop shortcut, repair support and an Add/Remove Programs uninstaller. The portable ZIP contains the same offline payload plus `Barros_Pizza_Creator_Manager.exe` and `INSTALL_OFFLINE.cmd`.

## Ownership and compatibility boundary

The commercial Pizza Creator executable and data are not packaged. The user must already have a licensed installation of Pizza Connection 3 - Pizza Creator 0.11.272. Setup verifies:

- Windows x64 and Unity `2017.3.1p4` game profile;
- `Assembly-CSharp.dll` SHA-256 `ebf8698df7cb4af904c98c299994705ea529efbdf1e8ccb3e7ca8cb42a1cbc1c`;
- `Assembly-CSharp-firstpass.dll` SHA-256 `f9cbf0951fc4d4b0788c47bbe41a3820fa333d293175bbb7cb398eb4728fd284`.

No hardware reverse engineering is required or performed. The release targets the already verified Windows/software binary profile and uses normal device APIs for microphone and audio features.

## Included offline runtime

- certified Barro's 1.6 plug-in for the exact game assemblies;
- BepInEx 5.4.23.5 x64, verified before packaging and installation;
- private Python 3.12.10 embedded x64 runtime with no system PATH change;
- backend, contracts, rounded UI skin, five normalized OGG songs and four lyric videos;
- graphical manager for Verify, Install/Repair, Launch, Configure AI + Voice, Diagnostics and Remove Add-on.

## Retained proof

The release was tested against an isolated skeleton containing only the real game executable and two exact managed assemblies:

```text
clean_install=PASS
exact_plugin_hash=PASS
private_python=PASS
repair_preserved_settings=PASS
uninstall_removed_barros_files=PASS
uninstall_preserved_shared_bepinex=PASS
uninstall_preserved_original_game=PASS
commercial_game_packaged=NO
```

The graphical manager was opened through the normal Windows UI, detected the Steam Creator directory and reported `PASS — Verified Pizza Creator 0.11.272 / Unity 2017.3.1p4`. The complete automated source suite passes 121/121. The final live header proof also retains both end caps, remains clear of all five tabs and is centered inside the native close-button-safe area.

## Build and verification

Build with Inno Setup 7 and the two hash-pinned dependency archives:

```text
.\tools\build_windows_release.ps1
```

Run the isolated install → repair → uninstall lifecycle:

```text
.\tools\test_windows_installer.ps1 -GameRoot "C:\path\to\Pizza Connection 3 - Pizza Creator"
```

The build refuses to continue if a commercial game executable or data directory enters the release payload.

## Signing boundary

The community Setup and manager binaries are not Authenticode-signed because no code-signing certificate is available. Windows SmartScreen may therefore display **Unknown publisher**. Verify `Barros_Pizza_Creator_v1.6.0_WINDOWS_SHA256.txt` before running the release. This is an honest publication boundary, not an installation or runtime failure.
