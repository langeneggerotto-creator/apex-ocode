from __future__ import annotations

import threading
import unittest
import urllib.error
import urllib.request

from dreammusicforge.operator_studio.builder import build_operator_report
from dreammusicforge.operator_studio.server import create_operator_server

from .sample_data import ACCEPTED_RESULT


class CreateOperatorServerTests(unittest.TestCase):
    def setUp(self):
        report = build_operator_report(verification_results=(ACCEPTED_RESULT,), generated_at="2026-08-06T00:00:00+00:00")
        self.server = create_operator_server(report, host="127.0.0.1", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def test_serves_the_rendered_report_over_real_http(self):
        with urllib.request.urlopen(f"{self.base_url}/", timeout=5) as response:
            self.assertEqual(response.status, 200)
            body = response.read().decode("utf-8")
        self.assertIn("CANDIDATE-accepted", body)
        self.assertIn("<!doctype html>", body.lower())

    def test_binds_to_loopback_only(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_unknown_path_returns_404(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(f"{self.base_url}/nonexistent", timeout=5)
        self.assertEqual(ctx.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
