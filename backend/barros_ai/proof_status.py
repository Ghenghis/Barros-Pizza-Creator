from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

TRUTH_STATES = {"not_run", "pass", "fail", "blocked"}


class ProofStatusError(ValueError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _evidence_roots(app_root: Path) -> list[Path]:
    roots: list[Path] = []
    for candidate in (
        app_root / "evidence" / "runs",
        app_root.parent / "evidence" / "runs",
    ):
        resolved = candidate.resolve()
        if resolved not in roots:
            roots.append(resolved)
    return roots


def _contract_gate_requirements(app_root: Path, expected_contract_id: str) -> dict[str, bool]:
    """Load the installed acceptance contract and return its exact gate manifest.

    Retained results are only meaningful when they are bound to the currently
    installed contract. Matching the contract ID alone is insufficient because a
    hand-edited results file could otherwise omit required gates or change their
    ``release_required`` flags and still look complete.
    """
    candidates = (
        app_root / "contracts" / "rc1.acceptance.json",
        app_root.parent / "contracts" / "rc1.acceptance.json",
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        checked = ", ".join(str(candidate) for candidate in candidates)
        raise ProofStatusError(f"Acceptance contract not found; checked: {checked}")
    try:
        contract = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProofStatusError(f"Invalid acceptance contract: {path}: {exc}") from exc
    if not isinstance(contract, dict):
        raise ProofStatusError("Acceptance contract root must be a JSON object.")

    contract_id = str(contract.get("contract_id", "")).strip()
    if not contract_id:
        raise ProofStatusError("Acceptance contract lacks contract_id.")
    if expected_contract_id and contract_id != expected_contract_id:
        raise ProofStatusError(
            f"Acceptance contract mismatch: expected {expected_contract_id!r}, got {contract_id!r}."
        )

    layers = contract.get("layers")
    if not isinstance(layers, list):
        raise ProofStatusError("Acceptance contract layers must be a JSON array.")

    requirements: dict[str, bool] = {}
    for layer in layers:
        if not isinstance(layer, dict):
            raise ProofStatusError("Acceptance contract layers must contain JSON objects.")
        gates = layer.get("gates")
        if not isinstance(gates, list) or not all(isinstance(row, dict) for row in gates):
            raise ProofStatusError("Acceptance contract gates must be a JSON array of objects.")
        for gate in gates:
            gate_id = str(gate.get("id", "")).strip()
            if not gate_id:
                raise ProofStatusError("Acceptance contract contains a gate without id.")
            if gate_id in requirements:
                raise ProofStatusError(f"Acceptance contract contains duplicate gate id {gate_id!r}.")
            release_required = gate.get("release_required")
            if not isinstance(release_required, bool):
                raise ProofStatusError(
                    f"Acceptance contract gate {gate_id} lacks an explicit release_required boolean."
                )
            requirements[gate_id] = release_required
    if not requirements:
        raise ProofStatusError("Acceptance contract contains no proof gates.")
    return requirements


def _proof_binding(expected_gates: dict[str, bool]) -> dict[str, Any]:
    return {
        "contract_validated": True,
        "contract_gate_count": len(expected_gates),
        "contract_release_required_gate_count": sum(1 for required in expected_gates.values() if required),
    }


def _load_results(
    path: Path,
    expected_contract_id: str,
    expected_gates: dict[str, bool],
) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProofStatusError(f"Invalid Creator proof results: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ProofStatusError("Creator proof results root must be a JSON object.")

    contract_id = str(payload.get("contract_id", "")).strip()
    if not contract_id:
        raise ProofStatusError("Creator proof results lack contract_id.")
    if expected_contract_id and contract_id != expected_contract_id:
        raise ProofStatusError(
            f"Creator proof results contract mismatch: expected {expected_contract_id!r}, got {contract_id!r}."
        )

    stage = str(payload.get("stage", "")).strip()
    run_id = str(payload.get("run_id", "")).strip()
    results = payload.get("results")
    if not run_id:
        raise ProofStatusError("Creator proof results lack run_id.")
    if stage not in {"Static", "Build", "Runtime", "All"}:
        raise ProofStatusError(f"Creator proof results contain unsupported stage: {stage!r}.")
    if not isinstance(results, list) or not all(isinstance(row, dict) for row in results):
        raise ProofStatusError("Creator proof results must contain a results array of objects.")

    counts = {state: 0 for state in TRUTH_STATES}
    required: list[dict[str, Any]] = []
    missing_referenced_evidence: list[str] = []
    normalized: list[dict[str, Any]] = []
    observed_gate_ids: set[str] = set()
    for row in results:
        gate_id = str(row.get("gate_id", "")).strip()
        state = str(row.get("state", "")).strip().lower()
        if not gate_id:
            raise ProofStatusError("Creator proof results contain a gate without gate_id.")
        if gate_id in observed_gate_ids:
            raise ProofStatusError(f"Creator proof results contain duplicate gate_id {gate_id!r}.")
        observed_gate_ids.add(gate_id)
        if gate_id not in expected_gates:
            raise ProofStatusError(f"Creator proof results contain unknown contract gate {gate_id!r}.")
        if state not in TRUTH_STATES:
            raise ProofStatusError(f"Creator proof gate {gate_id} has invalid state: {state!r}.")
        counts[state] += 1

        release_required = row.get("release_required")
        if not isinstance(release_required, bool):
            raise ProofStatusError(
                f"Creator proof gate {gate_id} lacks an explicit release_required boolean."
            )
        if release_required is not expected_gates[gate_id]:
            raise ProofStatusError(
                f"Creator proof gate {gate_id} release_required does not match the installed contract."
            )

        evidence = row.get("evidence")
        if evidence is None:
            evidence = []
        if not isinstance(evidence, list):
            raise ProofStatusError(f"Creator proof gate {gate_id} evidence must be an array.")
        normalized_evidence: list[str] = []
        for evidence_path in evidence:
            if not isinstance(evidence_path, str) or not evidence_path.strip():
                raise ProofStatusError(
                    f"Creator proof gate {gate_id} evidence entries must be non-empty strings."
                )
            value = evidence_path.strip()
            normalized_evidence.append(value)
            if not Path(value).is_file():
                missing_referenced_evidence.append(value)

        item = dict(row)
        item["gate_id"] = gate_id
        item["state"] = state
        item["release_required"] = release_required
        item["evidence"] = normalized_evidence
        normalized.append(item)
        if release_required:
            required.append(item)

    missing_contract_gates = sorted(set(expected_gates) - observed_gate_ids)
    if missing_contract_gates:
        raise ProofStatusError(
            "Creator proof results are missing contract gates: " + ", ".join(missing_contract_gates)
        )

    reported_counts = payload.get("counts")
    if isinstance(reported_counts, dict):
        for state, actual in counts.items():
            try:
                reported = int(reported_counts.get(state, 0))
            except (TypeError, ValueError) as exc:
                raise ProofStatusError(f"Creator proof results count for {state} is not an integer.") from exc
            if reported != actual:
                raise ProofStatusError(
                    f"Creator proof results count mismatch for {state}: reported {reported}, observed {actual}."
                )

    required_complete = bool(required) and all(row["state"] == "pass" for row in required)
    runtime_certified = (
        stage == "All"
        and required_complete
        and not missing_referenced_evidence
    )
    if runtime_certified:
        state = "pass"
        reason = "All release-required gates in the retained All-stage proof results are PASS and referenced evidence is present."
    elif any(row["state"] == "fail" for row in required):
        state = "fail"
        reason = "At least one release-required retained proof gate is FAIL."
    elif any(row["state"] == "blocked" for row in required):
        state = "blocked"
        reason = "At least one release-required retained proof gate is BLOCKED."
    else:
        state = "not_run"
        reason = "The latest retained proof results do not complete every release-required gate in an All-stage run."
    if missing_referenced_evidence:
        reason = "Referenced proof evidence is missing; runtime certification is refused."

    return {
        "ok": True,
        "available": True,
        "contract_id": contract_id,
        "release": payload.get("release", ""),
        "run_id": run_id,
        "stage": stage,
        "game_root": payload.get("game_root", ""),
        "package_root": payload.get("package_root", ""),
        "results_path": str(path.resolve()),
        "results_sha256": _sha256(path),
        "proof_binding": _proof_binding(expected_gates),
        "counts": counts,
        "release_required_gate_count": len(required),
        "release_required_pass_count": sum(1 for row in required if row["state"] == "pass"),
        "missing_referenced_evidence": sorted(set(missing_referenced_evidence)),
        "results": normalized,
        "certification": {
            "state": state,
            "runtime_certified": runtime_certified,
            "source": "retained_proof_results",
            "reason": reason,
        },
    }


def latest_proof_status(app_root: str | Path, expected_contract_id: str) -> dict[str, Any]:
    """Read the newest retained Creator ``results.json`` without inventing proof.

    The newest file is selected first. If that file is malformed, contract-
    mismatched, or does not exactly match the installed contract gate manifest,
    the function fails closed instead of silently falling back to an older run
    that might look healthier.
    """
    root = Path(app_root)
    expected_gates = _contract_gate_requirements(root, expected_contract_id)
    binding = _proof_binding(expected_gates)
    candidates: list[Path] = []
    for evidence_root in _evidence_roots(root):
        if not evidence_root.is_dir():
            continue
        candidates.extend(path for path in evidence_root.glob("*/results.json") if path.is_file())
    if not candidates:
        return {
            "ok": True,
            "available": False,
            "contract_id": expected_contract_id,
            "proof_binding": binding,
            "certification": {
                "state": "not_run",
                "runtime_certified": False,
                "source": "retained_proof_results",
                "reason": "No retained Creator proof results.json was found.",
            },
        }

    newest = max(candidates, key=lambda path: (path.stat().st_mtime_ns, str(path)))
    return _load_results(newest, expected_contract_id, expected_gates)
