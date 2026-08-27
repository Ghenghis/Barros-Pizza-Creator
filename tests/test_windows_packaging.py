from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging" / "windows"


def test_windows_manager_enforces_exact_game_and_offline_dependencies():
    source = (PACKAGING / "BarrosCreatorManager.cs").read_text(encoding="utf-8")
    assert "Pizza Connection 3 - Pizza Creator.exe" in source
    assert "ebf8698df7cb4af904c98c299994705ea529efbdf1e8ccb3e7ca8cb42a1cbc1c" in source
    assert "f9cbf0951fc4d4b0788c47bbe41a3820fa333d293175bbb7cb398eb4728fd284" in source
    assert "BepInEx_win_x64_5.4.23.5.zip" in source
    assert "python-3.12.10-embed-amd64.zip" in source
    assert "INSTALL / REPAIR" in source
    assert "REMOVE ADD-ON" in source
    assert 'HasOption(args, "--configure")' in source
    assert 'HasOption(args, "--diagnose")' in source


def test_inno_installer_has_repair_shortcuts_and_uninstall_hook():
    source = (PACKAGING / "BarrosCreator.iss").read_text(encoding="utf-8")
    assert "AppVersion={#AppVersion}" in source
    assert "PrivilegesRequired=admin" in source
    assert "GameRootPage" in source
    assert "--install --game-root" in source
    assert "[UninstallRun]" in source
    assert "--uninstall" in source
    assert "Pizza Connection 3 - Pizza Creator.exe" in source


def test_builder_refuses_commercial_game_files_and_verifies_dependencies():
    source = (ROOT / "tools" / "build_windows_release.ps1").read_text(encoding="utf-8")
    assert "commercial_game_included = $false" in source
    assert '$_ .Name -eq "Pizza Connection 3 - Pizza Creator.exe"'.replace("$_ ", "$_") in source
    assert "82F9878551030F54657792C0740D9D51A09500EEAE1FBA21106B0C441E6732C4" in source
    assert "4ACBED6DD1C744B0376E3B1CF57CE906F9DC9E95E68824584C8099A63025A3C3" in source
    assert "redundant same-song MP3" in source


def test_game_installer_uses_windows_crypto_without_get_file_hash_dependency():
    source = (ROOT / "INSTALL_Barros_AI_Designer.ps1").read_text(encoding="utf-8")
    assert "[Security.Cryptography.SHA256]::Create()" in source
    assert "Get-FileHash" not in source


def test_portable_readme_states_ownership_and_smartscreen_boundaries():
    text = (PACKAGING / "PORTABLE_README.txt").read_text(encoding="utf-8")
    assert "commercial Pizza Creator game is not included" in text
    assert "Unknown publisher" in text
    assert "SHA-256" in text
