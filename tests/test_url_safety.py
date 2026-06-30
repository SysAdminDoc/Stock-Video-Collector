import os
import socket
import sys
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import artlist_scraper as app  # noqa: E402


class UrlSafetyPolicyTests(unittest.TestCase):
    def test_blocks_local_private_metadata_and_ambiguous_targets(self):
        blocked = [
            "ftp://example.com/file.mp4",
            "http://localhost/video.mp4",
            "http://127.0.0.1/video.mp4",
            "http://10.0.0.1/video.mp4",
            "http://172.16.0.1/video.mp4",
            "http://192.168.1.1/video.mp4",
            "http://169.254.169.254/latest/meta-data",
            "http://[::1]/video.mp4",
            "http://2130706433/video.mp4",
            "http://0177.0.0.1/video.mp4",
        ]
        for url in blocked:
            with self.subTest(url=url):
                with self.assertRaises(app.UnsafeUrlError):
                    app._validate_safe_url(url)

    def test_blocked_url_errors_redact_sensitive_query_values(self):
        with self.assertRaises(app.UnsafeUrlError) as ctx:
            app._validate_safe_url("http://127.0.0.1/video.mp4?token=plain-secret&ok=1")

        message = str(ctx.exception)
        self.assertNotIn("plain-secret", message)
        self.assertIn(app._REDACTED, message)

    def test_allows_public_https_when_dns_resolves_publicly(self):
        public_dns = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
        ]
        with patch.object(app.socket, "getaddrinfo", return_value=public_dns):
            self.assertTrue(app._validate_safe_url("https://example.com/video.mp4"))

    def test_blocks_hostnames_that_resolve_to_private_addresses(self):
        private_dns = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.10", 443)),
        ]
        with patch.object(app.socket, "getaddrinfo", return_value=private_dns):
            with self.assertRaises(app.UnsafeUrlError) as ctx:
                app._validate_safe_url("https://cdn.example.test/video.mp4")

        self.assertIn("private resolved address", str(ctx.exception))

    def test_redirect_handler_blocks_private_redirect_target(self):
        req = urllib.request.Request("https://example.com/video.mp4")
        handler = app._SafeHTTPRedirectHandler()

        with self.assertRaises(app.UnsafeUrlError):
            handler.redirect_request(req, None, 302, "Found", {}, "http://127.0.0.1/admin")

    def test_download_head_check_reports_blocked_private_url(self):
        ok, reason = app.DownloadWorker._head_check_url("http://127.0.0.1/video.mp4")

        self.assertFalse(ok)
        self.assertIn("blocked", reason.lower())


if __name__ == "__main__":
    unittest.main()
