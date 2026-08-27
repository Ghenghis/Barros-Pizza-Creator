from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from barros_ai.server import validate_bind_host


class NetworkBoundaryTests(unittest.TestCase):
    def test_loopback_hosts_are_allowed(self) -> None:
        self.assertEqual("127.0.0.1", validate_bind_host("127.0.0.1"))
        self.assertEqual("::1", validate_bind_host("::1"))
        self.assertEqual("localhost", validate_bind_host("LOCALHOST"))

    def test_remote_bind_is_blocked(self) -> None:
        for host in ("0.0.0.0", "192.168.1.10", "example.com", ""):
            with self.subTest(host=host):
                with self.assertRaisesRegex(ValueError, "loopback-only"):
                    validate_bind_host(host)
