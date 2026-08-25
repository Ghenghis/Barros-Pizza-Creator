from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "pc3-only-scope.json"
MARKER = ROOT / "00_READ_FIRST_PC3_ONLY.md"

FORBIDDEN = (
    re.compile(r"\bPC2\b", re.IGNORECASE),
    re.compile(r"Pizza\s+Connection\s+2", re.IGNORECASE),
    re.compile(r"Fast\s+Food\s+Tycoon\s+2", re.IGNORECASE),
    re.compile(r"Pizza\s+Tycoon\s+2", re.IGNORECASE),
)

# Only scope/quarantine policy files may name the prohibited product family.
# Implementation, ordinary docs, config, tests, evidence and assets are not exempt.
POLICY_EXEMPT = {
    "00_READ_FIRST_PC3_ONLY.md",
    "PC3_ONLY_SCOPE.md",
    "WORKSTREAM_OWNERSHIP.md",
    "CLAUDE_HANDOFF.md",
    "CLAUDE_NEXT_TASKS_PC3_CREATOR.md",
    "docs/PC2_QUARANTINE_PC3_CLEAN_START_PLAN.md",
    "contracts/pc3-only-scope.json",
    "contracts/workstream-ownership.json",
    "contracts/claude-creator-task-queue.json",
    "scripts/check_pc3_scope.py",
}

TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".py", ".ps1", ".bat", ".cmd", ".sh", ".cs", ".csproj", ".props",
    ".xml", ".csv", ".sql", ".js", ".jsx", ".ts", ".tsx", ".html", ".css",
}


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def normalize_repo(remote: str) -> str:
    value = remote.strip().replace("\\", "/")
    match = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", value, re.IGNORECASE)
    return match.group(1) if match else ""


def tracked_files() -> list[str]:
    raw = git("ls-files", "-z")
    return [item for item in raw.split("\0") if item]


def should_scan(path: Path) -> bool:
    if path.name in {".gitignore", ".gitattributes", "Dockerfile"}:
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def main() -> int:
    failures: list[str] = []
    if not MARKER.is_file():
        failures.append("missing root scope marker: 00_READ_FIRST_PC3_ONLY.md")
    else:
        marker = MARKER.read_text(encoding="utf-8", errors="replace")
        if "SCOPE:" not in marker or "PC3" not in marker or "DO NOT MIX" not in marker:
            failures.append("root scope marker lacks required PC3-only warning language")

    if not CONTRACT.is_file():
        failures.append("missing contracts/pc3-only-scope.json")
        contract: dict[str, object] = {}
    else:
        try:
            contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append(f"scope contract is unreadable: {exc}")
            contract = {}

    assignment = contract.get("repository_assignment") if isinstance(contract, dict) else None
    if not isinstance(assignment, dict):
        failures.append("scope contract lacks repository_assignment")
        expected_repo = ""
    else:
        expected_repo = str(assignment.get("repository") or "")
        if not expected_repo:
            failures.append("scope contract repository_assignment.repository is empty")
        if not str(assignment.get("owner") or ""):
            failures.append("scope contract repository_assignment.owner is empty")
        if not str(assignment.get("workstream") or ""):
            failures.append("scope contract repository_assignment.workstream is empty")
        if not str(assignment.get("primary_runtime_profile") or "").startswith("creator-"):
            failures.append("Creator repository must declare a creator-* primary runtime profile")

    actual_repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not actual_repo:
        try:
            actual_repo = normalize_repo(git("remote", "get-url", "origin"))
        except Exception:
            actual_repo = ""
    if not actual_repo:
        failures.append("could not verify GitHub repository identity from GITHUB_REPOSITORY or origin")
    elif expected_repo and actual_repo.lower() != expected_repo.lower():
        failures.append(f"wrong repository identity: expected {expected_repo}, found {actual_repo}")

    for rel in tracked_files():
        normalized = rel.replace("\\", "/")
        if normalized in POLICY_EXEMPT:
            continue
        for pattern in FORBIDDEN:
            if pattern.search(normalized):
                failures.append(f"forbidden PC2 marker in tracked path: {normalized}")
                break
        path = ROOT / rel
        if not path.is_file() or not should_scan(path):
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            failures.append(f"could not inspect tracked text file {normalized}: {exc}")
            continue
        for pattern in FORBIDDEN:
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                failures.append(f"forbidden PC2 marker in {normalized}:{line}: {match.group(0)!r}")
                break

    if failures:
        print("PC3 SCOPE GUARD: FAIL")
        for item in failures:
            print(" - " + item)
        return 1

    print(f"PC3 SCOPE GUARD: PASS ({actual_repo})")
    print("Scope is locked to PC3 Pizza Creator; no non-policy PC2 markers detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
