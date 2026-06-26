import unittest
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import app


class AppTests(unittest.TestCase):
    def test_security_headers_are_added(self):
        client = app.app.test_client()

        with patch.dict(app.os.environ, {"ENABLE_HSTS": "1"}, clear=False):
            response = client.get("/health")

        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["Referrer-Policy"], "same-origin")
        self.assertIn("default-src", response.headers["Content-Security-Policy"])
        self.assertIn("max-age=31536000", response.headers["Strict-Transport-Security"])
        self.assertEqual(response.headers["Cache-Control"], "no-store, max-age=0")
        self.assertEqual(response.headers["Pragma"], "no-cache")

    def test_method_not_allowed_returns_json_payload(self):
        client = app.app.test_client()
        response = client.put("/health")

        self.assertEqual(response.status_code, 405)
        payload = response.get_json()
        self.assertEqual(payload["error"], "Method not allowed")
        self.assertEqual(payload["path"], "/health")
        self.assertEqual(payload["method"], "PUT")
        self.assertIn("GET", payload["allowed_methods"])

    def test_logging_falls_back_when_config_is_not_writable(self):
        script = textwrap.dedent(
            """
            import os
            os.path.isdir = lambda path: True

            def deny(*args, **kwargs):
                raise PermissionError("read-only")

            os.makedirs = deny

            import logging_utils

            assert logging_utils.LOG_DIR is None
            assert [type(handler).__name__ for handler in logging_utils.logger.handlers] == ["StreamHandler"]
            """
        )

        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()
