from __future__ import annotations

import argparse
import sys
from pathlib import Path

from barros_ai.server import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Local sidecar for Barro's AI Pizza Designer")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Loopback only. Use an SSH local-forward for a VPS; direct remote binding is blocked.",
    )
    parser.add_argument("--port", type=int, default=48173)
    parser.add_argument("--settings", default="")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    settings = Path(args.settings).resolve() if args.settings else root / "settings.json"
    if not settings.exists():
        settings = root / "default_settings.json"
    run(root, settings, args.host, args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
