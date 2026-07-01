import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import artlist_scraper as app  # noqa: E402


class _FakeResponse:
    status = 204

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def getcode(self):
        return self.status


class ChallengeNotificationTests(unittest.TestCase):
    def test_notification_message_redacts_sensitive_source_url(self):
        message = app._challenge_notification_message(
            "Pexels",
            "https://example.com/videos?token=plain-secret&ok=1",
            headless=False,
        )

        self.assertIn("Pexels", message)
        self.assertIn("visible", message)
        self.assertIn("token=[REDACTED]", message)
        self.assertNotIn("plain-secret", message)

    def test_notifications_disabled_returns_no_work(self):
        self.assertEqual(app._send_challenge_notifications({}, "Artlist", "https://example.com"), [])

    def test_discord_and_telegram_payloads_use_safe_post(self):
        calls = []

        def fake_safe_urlopen(req, timeout=15):
            calls.append((req.full_url, json.loads(req.data.decode("utf-8")), timeout))
            return _FakeResponse()

        cfg = {
            "challenge_notify_enabled": True,
            "challenge_discord_webhook_url": "https://discord.com/api/webhooks/abc/secret",
            "challenge_telegram_bot_token": "123:abc/def",
            "challenge_telegram_chat_id": "987654",
        }

        with patch.object(app, "_safe_urlopen", side_effect=fake_safe_urlopen):
            results = app._send_challenge_notifications(
                cfg,
                "Generic",
                "https://stock.example/challenge",
                headless=True,
            )

        self.assertEqual([name for name, ok, _ in results if ok], ["Discord", "Telegram"])
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0], cfg["challenge_discord_webhook_url"])
        self.assertIn("Stock Video Collector challenge detected", calls[0][1]["content"])
        self.assertEqual(calls[0][1]["allowed_mentions"], {"parse": []})
        self.assertTrue(calls[1][0].startswith("https://api.telegram.org/bot123%3Aabc%2Fdef/sendMessage"))
        self.assertEqual(calls[1][1]["chat_id"], "987654")
        self.assertTrue(calls[1][1]["disable_web_page_preview"])


if __name__ == "__main__":
    unittest.main()
