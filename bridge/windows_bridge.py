from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(base_url: str, token: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    raw = json.dumps(payload).encode("utf-8")
    request = Request(base_url.rstrip("/") + path, data=raw, method="POST")
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", "Bearer " + token)
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError("HTTP %d: %s" % (exc.code, detail)) from exc
    except URLError as exc:
        raise RuntimeError("Connection failed: %s" % exc.reason) from exc
    if not isinstance(result, dict) or not result.get("ok"):
        raise RuntimeError(str(result.get("error", "Unexpected bridge response.")))
    return result


def load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def save_config(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pair Android/web Barro's Creator with the Windows game.")
    parser.add_argument("--server", default=os.getenv("BARROS_REMOTE_URL", "https://creator.daveai.tech/api"))
    parser.add_argument("--token", default=os.getenv("BARROS_API_TOKEN", ""))
    parser.add_argument("--local", default="http://127.0.0.1:48173")
    parser.add_argument("--config", default=str(Path(os.getenv("LOCALAPPDATA", ".")) / "BarrosPizzaCreator" / "windows-bridge.json"))
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    config_path = Path(args.config).expanduser().resolve()
    config = load_config(config_path)
    if not config.get("bridge_id") or not config.get("bridge_secret") or config.get("server") != args.server:
        config = request_json(args.server, args.token, "/pairing/bridge/register", {"name": os.environ.get("COMPUTERNAME", "Barro's Windows Creator")})
        config["server"] = args.server
        save_config(config_path, config)
    print("\nBarro's Windows Bridge is ready.")
    print("Pairing code: %s" % config.get("pair_code", "------"))
    print("Open Connect on the phone or tablet and enter this code.\n")
    while True:
        try:
            result = request_json(
                args.server,
                args.token,
                "/bridge/jobs/next",
                {"bridge_id": config["bridge_id"], "bridge_secret": config["bridge_secret"]},
            )
            job = result.get("job")
            if isinstance(job, dict):
                state = "completed"
                detail = "Delivered to the local Pizza Creator sidecar."
                try:
                    request_json(args.local, "", "/remote/import", job.get("payload") or {})
                    print("Received %s. Open the Barro's tab to preview or apply it." % job.get("job_id"))
                except RuntimeError as exc:
                    state = "failed"
                    detail = str(exc)
                    print("Could not reach the local game helper: %s" % exc, file=sys.stderr)
                request_json(
                    args.server,
                    args.token,
                    "/bridge/jobs/ack",
                    {
                        "bridge_id": config["bridge_id"],
                        "bridge_secret": config["bridge_secret"],
                        "job_id": job.get("job_id"),
                        "state": state,
                        "detail": detail,
                    },
                )
        except RuntimeError as exc:
            print("Bridge warning: %s" % exc, file=sys.stderr)
        if args.once:
            return 0
        time.sleep(3)


if __name__ == "__main__":
    raise SystemExit(main())
