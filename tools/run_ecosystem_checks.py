from __future__ import annotations

"""Run a durable, cross-project Pizza Connection 3 / Barro's Pizza audit.

The output is evidence, not a completion claim. Live GUI/game gates remain
NOT_RUN/BLOCKED until their real screenshots/runtime observations exist.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from verify_ecosystem_sync import verify as verify_sync  # noqa: E402


def _run(command: list[str], cwd: Path, timeout: int = 1800) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": proc.returncode,
            "pass": proc.returncode == 0,
            "stdout": proc.stdout[-40000:],
            "stderr": proc.stderr[-40000:],
        }
    except Exception as exc:
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": None,
            "pass": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _git(root: Path) -> dict[str, Any]:
    def one(*args: str) -> str:
        proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
        return proc.stdout.strip() if proc.returncode == 0 else ""

    status = one("status", "--porcelain")
    return {
        "root": str(root),
        "exists": root.is_dir(),
        "branch": one("branch", "--show-current"),
        "head": one("rev-parse", "HEAD"),
        "dirty": bool(status),
        "dirty_entry_count": len(status.splitlines()) if status else 0,
        "remote_names": one("remote").splitlines(),
    }


def _candidate_roots(kind: str, creator: Path) -> list[Path]:
    parent = creator.parent
    home = Path.home()
    values: list[Path] = []
    if kind == "workbench":
        env = os.environ.get("BARROS_WORKBENCH_ROOT")
        if env:
            values.append(Path(env))
        values += [
            parent / "barros-workbench",
            Path(r"S:\Barro's-Pizza\barros-workbench"),
            Path(r"S:\barros-workbench"),
            home / "Downloads" / "barros-workbench",
        ]
    else:
        env = os.environ.get("BARROS_STUDIO_ROOT")
        if env:
            values.append(Path(env))
        values += [
            parent / "PC3_Barros_Runtime_Proof_Studio",
            Path(r"S:\Barro's-Pizza\PC3_Barros_Runtime_Proof_Studio"),
            home / "Downloads" / "PC3_Barros_Runtime_Proof_Studio",
            home / "Downloads" / "PC3_Barros_Runtime_Proof_Studio_v0.7",
        ]
        # Workbench config is a useful durable pointer after a reboot.
        appdata = os.environ.get("APPDATA")
        if appdata:
            config = Path(appdata) / "BarrosWorkbench" / "config.json"
            if config.is_file():
                try:
                    payload = json.loads(config.read_text(encoding="utf-8"))
                    if payload.get("studio_root"):
                        values.insert(0, Path(str(payload["studio_root"])))
                except Exception:
                    pass
    # Preserve order, remove duplicates.
    out: list[Path] = []
    seen = set()
    for value in values:
        key = str(value).casefold()
        if key not in seen:
            seen.add(key)
            out.append(value)
    return out


def _resolve_root(explicit: str | None, kind: str, creator: Path) -> Path | None:
    if explicit:
        return Path(explicit).expanduser().resolve()
    for candidate in _candidate_roots(kind, creator):
        if candidate.is_dir() and (candidate / ".git").exists():
            return candidate.resolve()
    return None


def _python_for(root: Path) -> str:
    candidates = [
        root / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def _test_commands(creator: Path, workbench: Path, studio: Path) -> dict[str, tuple[Path, list[str]]]:
    return {
        "creator": (
            creator,
            [_python_for(creator), "-m", "unittest", "discover", "-s", "tests", "-v"],
        ),
        "workbench": (
            workbench,
            [_python_for(workbench), "-m", "pytest", "-q", "tests"],
        ),
        "studio": (
            studio,
            [_python_for(studio), "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Creator + Workbench + Studio as one evidence-first ecosystem")
    parser.add_argument("--creator", default=str(ROOT))
    parser.add_argument("--workbench")
    parser.add_argument("--studio")
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    creator = Path(args.creator).expanduser().resolve()
    workbench = _resolve_root(args.workbench, "workbench", creator)
    studio = _resolve_root(args.studio, "studio", creator)

    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    default_out = creator / "evidence" / "ecosystem_checks" / stamp / "ecosystem_check.json"
    out = Path(args.output).expanduser().resolve() if args.output else default_out

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "kind": "barros-pc3-ecosystem-local-check",
        "created_utc": now.isoformat(),
        "display_name": "Pizza Connection 3 / Barro's Pizza",
        "truth_rule": "Portable checks do not promote live GUI/game gates. PASS here means only the named local check passed.",
        "roots": {
            "creator": str(creator),
            "workbench": str(workbench) if workbench else None,
            "studio": str(studio) if studio else None,
        },
        "checks": {},
        "tests": {},
        "next_actions": [],
    }

    if not workbench:
        report["next_actions"].append("Set BARROS_WORKBENCH_ROOT or pass --workbench to the real Workbench checkout.")
    if not studio:
        report["next_actions"].append("Set BARROS_STUDIO_ROOT or pass --studio to the real Studio checkout.")

    roots_ok = creator.is_dir() and workbench is not None and studio is not None
    if roots_ok:
        assert workbench is not None and studio is not None
        report["git"] = {
            "creator": _git(creator),
            "workbench": _git(workbench),
            "studio": _git(studio),
        }
        report["checks"]["sync"] = verify_sync(creator, workbench, studio)
        report["checks"]["launchers"] = {
            "creator_installer": (creator / "INSTALL_Barros_AI_Designer.bat").is_file(),
            "workbench": (workbench / "run.bat").is_file(),
            "studio": (studio / "START_PC3_BARROS_STUDIO.bat").is_file(),
            "creator_gitlab_safe": (creator / "SYNC_GITLAB_SAFE.bat").is_file(),
            "workbench_gitlab_safe": (workbench / "SYNC_GITLAB_SAFE.bat").is_file(),
            "studio_gitlab_safe": (studio / "SYNC_GITLAB_SAFE.bat").is_file(),
        }
        if args.run_tests:
            for name, (cwd, command) in _test_commands(creator, workbench, studio).items():
                report["tests"][name] = _run(command, cwd)
    else:
        report["checks"]["sync"] = {"ok": False, "error": "One or more repository roots are unresolved."}

    sync_ok = bool((report["checks"].get("sync") or {}).get("ok"))
    launcher_ok = all((report["checks"].get("launchers") or {}).values()) if roots_ok else False
    tests_ok = all(row.get("pass") for row in report["tests"].values()) if report["tests"] else None
    clean = all(not row.get("dirty") for row in (report.get("git") or {}).values()) if roots_ok else False

    report["summary"] = {
        "roots_resolved": roots_ok,
        "cross_repo_sync_pass": sync_ok,
        "launchers_present": launcher_ok,
        "git_trees_clean": clean,
        "tests_requested": bool(args.run_tests),
        "tests_pass": tests_ok,
        "portable_check_pass": roots_ok and sync_ok and launcher_ok and (tests_ok is not False),
        "live_runtime_complete": False,
        "live_runtime_reason": "This runner does not substitute for required real Workbench/Studio/game screenshots and runtime observations.",
    }

    if not clean and roots_ok:
        report["next_actions"].append("Commit/review dirty working trees before publication or GitLab mirroring.")
    if roots_ok and not sync_ok:
        report["next_actions"].append("Repair shared schema/build-contract drift before build-specific runtime work.")
    if tests_ok is False:
        report["next_actions"].append("Fix the failing local suite before publication; inspect retained stdout/stderr in this report.")
    report["next_actions"].append("Run remaining live acceptance gates on the correct build profile and retain real screenshots/evidence.")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Evidence: {out}")
    return 0 if report["summary"]["portable_check_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
