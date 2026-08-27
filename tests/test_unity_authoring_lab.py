import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "authoring" / "BarrosCreatorUiLab2021"
EXPORT = ROOT / "assets" / "ui" / "generated"


def test_unity_authoring_lab_is_locked_to_installed_2021_lts():
    version = (LAB / "ProjectSettings" / "ProjectVersion.txt").read_text(encoding="utf-8")
    assert "2021.3.45f2" in version
    builder = (LAB / "Assets" / "BarrosLab" / "Editor" / "BarrosUiLabBuilder.cs").read_text(encoding="utf-8")
    assert "1920, 1080" in builder
    assert "protected original five tabs" in builder.lower()
    assert '"Chat", "AI Lab", "Crew", "Voice", "Media"' in builder


def test_compatibility_export_is_neutral_and_hash_verified():
    theme = json.loads((EXPORT / "barros-ui-theme.json").read_text(encoding="utf-8"))
    assert theme["authoring_editor"] == "2021.3.45f2"
    assert theme["target_runtime"] == "Unity 2017.3.1p4"
    assert theme["format"] == "neutral-png-json"
    assert theme["protected_tab_count"] == 5
    assert theme["virtual_size"] == {"width": 640, "height": 1050}
    assert all(item["name"].endswith(".png") for item in theme["files"])
    for item in theme["files"]:
        payload = (EXPORT / item["name"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == item["sha256"]


def test_runtime_loader_has_bounded_fallback_behavior():
    source = (ROOT / "plugin-src" / "PanelRenderer.cs").read_text(encoding="utf-8")
    assert 'LoadExportedSkin("panel.png") ?? Rounded' in source
    assert 'LoadExportedSkin("card.png") ?? Rounded' in source
    assert "5 * 1024 * 1024" in source
    assert "texture.width > 512" in source
    assert 'evidence.Record("ui.exported_theme_loaded"' in source


def test_release_builder_excludes_unity_editor_cache():
    module_path = ROOT / "tools" / "build_release.py"
    spec = importlib.util.spec_from_file_location("barros_build_release", module_path)
    build_release = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(build_release)

    packaged = {path.relative_to(ROOT).as_posix().casefold() for path in build_release.package_files(ROOT)}
    transient = ("/library/", "/temp/", "/obj/", "/logs/", "/builds/", "/usersettings/")
    assert not any(any(marker in path for marker in transient) for path in packaged)
    assert "authoring/barroscreatoruilab2021/projectsettings/projectversion.txt" in packaged
    assert "authoring/barroscreatoruilab2021/assets/barroslab/scenes/barroscreatoruilab.unity" in packaged
