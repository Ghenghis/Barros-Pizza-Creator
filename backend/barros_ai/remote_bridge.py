from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
import time
import uuid
from pathlib import Path
from typing import Any


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class RemoteBridgeStore:
    """Small durable queue used by the hosted API and the Windows bridge.

    Secrets are returned once and stored only as hashes. The file is intentionally
    simple so it remains portable in the Windows sidecar and a single VPS
    container. A multi-replica deployment should replace this with a shared
    database before scaling out.
    """

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        if not self.path.exists():
            self._write({"bridges": {}, "pairings": {}, "jobs": []})

    def _read(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        return {
            "bridges": data.get("bridges") if isinstance(data.get("bridges"), dict) else {},
            "pairings": data.get("pairings") if isinstance(data.get("pairings"), dict) else {},
            "jobs": data.get("jobs") if isinstance(data.get("jobs"), list) else [],
        }

    def _write(self, data: dict[str, Any]) -> None:
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    @staticmethod
    def _clean_name(value: Any, fallback: str) -> str:
        clean = " ".join(str(value or fallback).strip().split())
        return (clean or fallback)[:80]

    def register_bridge(self, name: Any) -> dict[str, Any]:
        with self.lock:
            data = self._read()
            bridge_id = uuid.uuid4().hex
            bridge_secret = secrets.token_urlsafe(32)
            pair_code = "%06d" % secrets.randbelow(1_000_000)
            now = int(time.time())
            data["bridges"][bridge_id] = {
                "name": self._clean_name(name, "Barro's Windows Creator"),
                "secret_hash": _hash(bridge_secret),
                "pair_code_hash": _hash(pair_code),
                "created": now,
                "last_seen": now,
            }
            self._write(data)
            return {
                "ok": True,
                "bridge_id": bridge_id,
                "bridge_secret": bridge_secret,
                "pair_code": pair_code,
                "expires_in_seconds": 900,
            }

    def connect(self, pair_code: Any, device_name: Any) -> dict[str, Any]:
        code = str(pair_code or "").strip()
        if len(code) != 6 or not code.isdigit():
            raise ValueError("Enter the six-digit code shown by the Windows bridge.")
        now = int(time.time())
        with self.lock:
            data = self._read()
            bridge_id = ""
            for candidate_id, bridge in data["bridges"].items():
                if now - int(bridge.get("created", 0)) > 900:
                    continue
                if hmac.compare_digest(str(bridge.get("pair_code_hash", "")), _hash(code)):
                    bridge_id = candidate_id
                    break
            if not bridge_id:
                raise ValueError("That pairing code is invalid or expired. Restart the Windows bridge for a new code.")
            pair_token = secrets.token_urlsafe(32)
            pairing_id = uuid.uuid4().hex
            data["pairings"][pairing_id] = {
                "bridge_id": bridge_id,
                "device_name": self._clean_name(device_name, "Android companion"),
                "token_hash": _hash(pair_token),
                "created": now,
                "last_seen": now,
            }
            self._write(data)
            return {
                "ok": True,
                "pairing_id": pairing_id,
                "pair_token": pair_token,
                "bridge_id": bridge_id,
                "bridge_name": data["bridges"][bridge_id]["name"],
            }

    def _pairing(self, data: dict[str, Any], token: str) -> tuple[str, dict[str, Any]]:
        token_hash = _hash(token)
        for pairing_id, pairing in data["pairings"].items():
            if hmac.compare_digest(str(pairing.get("token_hash", "")), token_hash):
                return pairing_id, pairing
        raise ValueError("This mobile device is not paired. Enter a fresh Windows pairing code.")

    def enqueue(self, pair_token: Any, payload: Any, action: Any = "preview") -> dict[str, Any]:
        token = str(pair_token or "")
        if not isinstance(payload, dict):
            raise ValueError("A recipe response object is required.")
        recipes = payload.get("recipes")
        if not isinstance(recipes, list) or not recipes:
            raise ValueError("The design has no recipe to send to Windows.")
        with self.lock:
            data = self._read()
            pairing_id, pairing = self._pairing(data, token)
            job_id = uuid.uuid4().hex
            now = int(time.time())
            data["jobs"].append(
                {
                    "job_id": job_id,
                    "bridge_id": pairing["bridge_id"],
                    "pairing_id": pairing_id,
                    "action": str(action or "preview")[:20],
                    "payload": payload,
                    "created": now,
                    "state": "queued",
                }
            )
            data["jobs"] = data["jobs"][-200:]
            pairing["last_seen"] = now
            self._write(data)
            return {"ok": True, "job_id": job_id, "state": "queued"}

    def next_job(self, bridge_id: Any, bridge_secret: Any) -> dict[str, Any]:
        candidate_id = str(bridge_id or "")
        candidate_secret = str(bridge_secret or "")
        with self.lock:
            data = self._read()
            bridge = data["bridges"].get(candidate_id)
            if not bridge or not hmac.compare_digest(
                str(bridge.get("secret_hash", "")), _hash(candidate_secret)
            ):
                raise ValueError("Windows bridge credentials were rejected.")
            bridge["last_seen"] = int(time.time())
            for job in data["jobs"]:
                if job.get("bridge_id") == candidate_id and job.get("state") == "queued":
                    job["state"] = "delivered"
                    job["delivered"] = int(time.time())
                    self._write(data)
                    return {"ok": True, "job": job}
            self._write(data)
            return {"ok": True, "job": None}

    def acknowledge(self, bridge_id: Any, bridge_secret: Any, job_id: Any, state: Any, detail: Any) -> dict[str, Any]:
        candidate_id = str(bridge_id or "")
        candidate_secret = str(bridge_secret or "")
        with self.lock:
            data = self._read()
            bridge = data["bridges"].get(candidate_id)
            if not bridge or not hmac.compare_digest(
                str(bridge.get("secret_hash", "")), _hash(candidate_secret)
            ):
                raise ValueError("Windows bridge credentials were rejected.")
            for job in data["jobs"]:
                if job.get("job_id") == str(job_id) and job.get("bridge_id") == candidate_id:
                    job["state"] = str(state or "completed")[:20]
                    job["detail"] = str(detail or "")[:500]
                    job["finished"] = int(time.time())
                    self._write(data)
                    return {"ok": True, "job_id": job["job_id"], "state": job["state"]}
            raise ValueError("The remote job was not found.")


class LocalRemoteInbox:
    """One-process handoff from the Windows polling bridge to the game plug-in."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.queue: list[dict[str, Any]] = []

    def push(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict) or not isinstance(payload.get("recipes"), list):
            raise ValueError("Remote import requires a normal Barro's recipe response.")
        with self.lock:
            self.queue.append(payload)
            self.queue = self.queue[-20:]
            return {"ok": True, "queued": len(self.queue)}

    def pop(self) -> dict[str, Any]:
        with self.lock:
            if not self.queue:
                return {"ok": True, "message": "No remote design waiting.", "recipes": []}
            payload = self.queue.pop(0)
            payload["ok"] = True
            payload.setdefault("message", "Remote design received from the Android companion.")
            return payload
