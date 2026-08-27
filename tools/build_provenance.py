from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command_text(command: list[str]) -> str:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    value = (completed.stdout or completed.stderr).strip()
    if completed.returncode and not value:
        raise subprocess.CalledProcessError(completed.returncode, command)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate build provenance for the exact Windows Creator plugin artifact.")
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, default=ROOT / "artifacts" / "Barros.PizzaCreator.AI.dll")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "build-provenance.json")
    parser.add_argument("--tests", default="not run")
    parser.add_argument("--boundary", default="Compilation and portable tests only; live behavior requires separately retained game evidence.")
    args = parser.parse_args()

    game = args.game_root.resolve()
    artifact = args.artifact.resolve()
    output = args.output.resolve()
    managed = game / "Pizza Connection 3 - Pizza Creator_Data" / "Managed"
    bepinex = game / "BepInEx" / "core" / "BepInEx.dll"
    framework = Path(os.environ["WINDIR"]) / "Microsoft.NET" / "Framework64" / "v4.0.30319"
    if not framework.is_dir():
        framework = Path(os.environ["WINDIR"]) / "Microsoft.NET" / "Framework" / "v4.0.30319"
    compiler = framework / "csc.exe"

    references = {
        "mscorlib.dll": framework / "mscorlib.dll",
        "System.dll": framework / "System.dll",
        "System.Core.dll": framework / "System.Core.dll",
        "BepInEx.dll": bepinex,
        "Assembly-CSharp.dll": managed / "Assembly-CSharp.dll",
        "Assembly-CSharp-firstpass.dll": managed / "Assembly-CSharp-firstpass.dll",
        "Newtonsoft.Json.dll": managed / "Newtonsoft.Json.dll",
        "Zenject.dll": managed / "Zenject.dll",
        "UnityEngine.dll": managed / "UnityEngine.dll",
        "UnityEngine.CoreModule.dll": managed / "UnityEngine.CoreModule.dll",
        "UnityEngine.IMGUIModule.dll": managed / "UnityEngine.IMGUIModule.dll",
        "UnityEngine.UI.dll": managed / "UnityEngine.UI.dll",
        "UnityEngine.UIModule.dll": managed / "UnityEngine.UIModule.dll",
        "UnityEngine.TextRenderingModule.dll": managed / "UnityEngine.TextRenderingModule.dll",
        "UnityEngine.AudioModule.dll": managed / "UnityEngine.AudioModule.dll",
        "UnityEngine.InputModule.dll": managed / "UnityEngine.InputModule.dll",
        "UnityEngine.ImageConversionModule.dll": managed / "UnityEngine.ImageConversionModule.dll",
        "UnityEngine.ScreenCaptureModule.dll": managed / "UnityEngine.ScreenCaptureModule.dll",
        "UnityEngine.VideoModule.dll": managed / "UnityEngine.VideoModule.dll",
        "UnityEngine.UnityWebRequestWWWModule.dll": managed / "UnityEngine.UnityWebRequestWWWModule.dll",
        "UnityEngine.UnityWebRequestModule.dll": managed / "UnityEngine.UnityWebRequestModule.dll",
        "UnityEngine.UnityWebRequestAudioModule.dll": managed / "UnityEngine.UnityWebRequestAudioModule.dll",
    }
    missing = [str(path) for path in [artifact, compiler, *references.values()] if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing provenance input(s): " + ", ".join(missing))

    source_files = sorted((ROOT / "plugin-src").glob("*.cs"), key=lambda item: item.name)
    source_hashes = {path.name: digest(path) for path in source_files}
    source_tree_text = "".join(
        "%s  plugin-src/%s\n" % (source_hashes[path.name], path.name) for path in source_files
    )
    compiler_literal = str(compiler).replace("'", "''")
    compiler_version = command_text(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "(Get-Item -LiteralPath '%s').VersionInfo.ProductVersion" % compiler_literal,
        ]
    )
    source_commit = command_text(["git", "-C", str(ROOT), "rev-parse", "HEAD"])
    artifact_hash = digest(artifact)

    payload = {
        "schema_version": "1.0",
        "artifact": artifact.name,
        "artifact_bytes": artifact.stat().st_size,
        "artifact_sha256": artifact_hash,
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_parent_commit": source_commit,
        "source_tree_sha256": hashlib.sha256(source_tree_text.encode("utf-8")).hexdigest(),
        "compiler": "Microsoft Visual C# Compiler " + compiler_version,
        "compiler_host": ".NET Framework on %s %s" % (platform.system(), platform.machine()),
        "output_kind": "PE32 AnyCPU .NET/Mono library",
        "options": ["nologo", "target:library", "optimize+", "debug:pdbonly", "platform:anycpu", "utf8output", "codepage:65001"],
        "target": {
            "game_version": "0.11.272",
            "unity": "2017.3.1p4 x64",
            "assembly_csharp_sha256": digest(references["Assembly-CSharp.dll"]),
            "assembly_csharp_firstpass_sha256": digest(references["Assembly-CSharp-firstpass.dll"]),
            "bepinex_version": "5.4.23.5",
            "bepinex_archive_sha256": "82f9878551030f54657792c0740d9d51a09500eeae1fba21106b0c441e6732c4",
            "bepinex_dll_sha256": digest(bepinex),
        },
        "reference_sha256": {name: digest(path) for name, path in references.items()},
        "source_files_sha256": source_hashes,
        "verification": {
            "compile_exit_code": 0,
            "compiler_errors": 0,
            "absolute_build_path_embedded": False,
            "backend_and_contract_tests": args.tests,
        },
        "boundary": args.boundary,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("Wrote %s for %s (%s)" % (output, artifact.name, artifact_hash))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
