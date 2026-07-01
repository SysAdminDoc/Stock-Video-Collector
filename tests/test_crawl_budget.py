import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import artlist_scraper as app  # noqa: E402


class _FakeRobotsResponse:
    def __init__(self, text):
        self._text = text

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, _size=-1):
        return self._text.encode("utf-8")


class CrawlBudgetTests(unittest.TestCase):
    def test_retry_after_parses_seconds_and_http_date(self):
        self.assertEqual(app._parse_retry_after_seconds("12"), 12.0)
        self.assertGreaterEqual(
            app._parse_retry_after_seconds("Wed, 01 Jul 2026 00:00:10 GMT", now_wall=1782864000),
            9.0,
        )

    def test_disabled_budget_skips_robots_fetch(self):
        controller = app.CrawlBudgetController({"respect_crawl_budget": False})

        with patch.object(app, "_safe_urlopen") as safe:
            allowed, reason = asyncio.run(controller.before_request("https://example.com/private"))

        self.assertTrue(allowed)
        self.assertEqual(reason, "")
        safe.assert_not_called()

    def test_robots_disallow_and_crawl_delay_are_cached(self):
        robots = "\n".join([
            "User-agent: *",
            "Disallow: /private",
            "Crawl-delay: 5",
        ])
        controller = app.CrawlBudgetController({"respect_crawl_budget": True})

        with patch.object(app, "_safe_urlopen", return_value=_FakeRobotsResponse(robots)) as safe:
            policy = controller._robots_for_url("https://example.com/public")
            allowed, reason = asyncio.run(controller.before_request("https://example.com/private/file"))

        self.assertEqual(policy["delay"], 5.0)
        self.assertFalse(allowed)
        self.assertIn("robots.txt disallows", reason)
        safe.assert_called_once()

    def test_rate_limit_headers_create_host_cooldown(self):
        controller = app.CrawlBudgetController({"respect_crawl_budget": True})

        retry_message = controller.observe_response(
            "https://example.com/search",
            status=429,
            headers={"Retry-After": "3"},
        )
        reset_message = controller.observe_response(
            "https://media.example/search",
            status=200,
            headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "2"},
        )

        self.assertIn("example.com", retry_message)
        self.assertIn("Retry-After", retry_message)
        self.assertIn("media.example", reset_message)
        self.assertIn("X-RateLimit reset", reset_message)


if __name__ == "__main__":
    unittest.main()
