import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import artlist_scraper as app  # noqa: E402


class BrowserRotationProxyTests(unittest.TestCase):
    def test_proxy_entry_normalization_supports_auth_and_default_scheme(self):
        proxy = app._normalise_proxy_entry("user:pass@example.com:8080")

        self.assertEqual(proxy["server"], "http://example.com:8080")
        self.assertEqual(proxy["username"], "user")
        self.assertEqual(proxy["password"], "pass")

        socks = app._normalise_proxy_entry("socks5://proxy.example.com:1080")
        self.assertEqual(socks, {"server": "socks5://proxy.example.com:1080"})

    def test_proxy_pool_selection_is_deterministic_and_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "proxies.txt"
            path.write_text(
                "\n".join(
                    [
                        "# comment",
                        "http://alpha.example.com:8080",
                        "user:plain-secret@beta.example.com:8443",
                        "bad://ignored.example.com:1",
                    ]
                ),
                encoding="utf-8",
            )
            cfg = {"proxy_pool_enabled": True, "proxy_pool_path": str(path)}

            first, count = app._select_proxy_from_pool(cfg, "same-session")
            second, count2 = app._select_proxy_from_pool(cfg, "same-session")

            self.assertEqual(count, 2)
            self.assertEqual(count2, 2)
            self.assertEqual(first, second)
            self.assertNotIn("plain-secret", app._proxy_for_log(first))

    def test_browser_profile_context_defaults_to_legacy_profile(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(app, "get_config_dir", return_value=tmp):
            context = app._browser_profile_context({}, "session")

            self.assertFalse(context["rotating"])
            self.assertEqual(context["profile_dir"], str(Path(tmp) / "browser_profile"))
            self.assertEqual(context["slots"], 1)

    def test_browser_profile_rotation_uses_bounded_slot_directory(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(app, "get_config_dir", return_value=tmp):
            cfg = {"rotate_browser_profiles": True, "browser_profile_slots": 3}

            context = app._browser_profile_context(cfg, "session-a")
            again = app._browser_profile_context(cfg, "session-a")

            self.assertTrue(context["rotating"])
            self.assertEqual(context, again)
            self.assertIn("browser_profiles", context["profile_dir"])
            self.assertRegex(context["profile_dir"], r"slot-0[1-3]$")


if __name__ == "__main__":
    unittest.main()
