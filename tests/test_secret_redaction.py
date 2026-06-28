import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import artlist_scraper as app  # noqa: E402


class SecretVaultTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_appdata = os.environ.get("APPDATA")
        os.environ["APPDATA"] = self.tmp.name

    def tearDown(self):
        if self.old_appdata is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = self.old_appdata
        self.tmp.cleanup()

    def test_save_config_moves_sensitive_values_to_vault(self):
        cfg = {
            "profiles": ["Pexels"],
            "pexels_api_key": "px-secret-123",
            "artlist_graphql": {
                "headers": {
                    "Authorization": "Bearer art-token-456",
                    "Cookie": "sessionid=cookie-secret",
                    "Accept": "application/json",
                }
            },
        }

        app.save_config(cfg)

        config_path = Path(app.get_config_dir()) / "config.json"
        vault_path = Path(app.get_config_dir()) / "secrets.json"
        raw_text = config_path.read_text(encoding="utf-8")
        vault_text = vault_path.read_text(encoding="utf-8")
        raw = json.loads(raw_text)

        self.assertNotIn("px-secret-123", raw_text)
        self.assertNotIn("art-token-456", raw_text)
        self.assertNotIn("cookie-secret", raw_text)
        self.assertNotIn("px-secret-123", vault_text)
        self.assertIn(app._SECRET_REF_KEY, raw["pexels_api_key"])
        self.assertIn(app._SECRET_REF_KEY, raw["artlist_graphql"]["headers"]["Authorization"])
        self.assertEqual(raw["artlist_graphql"]["headers"]["Accept"], "application/json")

        loaded = app.load_config()
        self.assertEqual(loaded["pexels_api_key"], "px-secret-123")
        self.assertEqual(loaded["artlist_graphql"]["headers"]["Authorization"], "Bearer art-token-456")
        self.assertEqual(loaded["artlist_graphql"]["headers"]["Cookie"], "sessionid=cookie-secret")

    def test_load_config_migrates_plaintext_sensitive_values(self):
        config_dir = Path(app.get_config_dir())
        config_path = config_dir / "config.json"
        config_path.write_text(
            json.dumps({"pixabay_api_key": "pixabay-secret", "safe": "value"}),
            encoding="utf-8",
        )

        loaded = app.load_config()
        raw_text = config_path.read_text(encoding="utf-8")

        self.assertEqual(loaded["pixabay_api_key"], "pixabay-secret")
        self.assertNotIn("pixabay-secret", raw_text)
        self.assertIn(app._SECRET_REF_KEY, json.loads(raw_text)["pixabay_api_key"])


class RedactionTests(unittest.TestCase):
    def test_redact_text_removes_tokens_headers_and_sensitive_query_values(self):
        text = (
            "Authorization: Bearer abc.def.ghi\n"
            "Cookie: sessionid=plain-cookie\n"
            "https://cdn.example.test/video.mp4?api_key=plain-key&ok=1&X-Amz-Signature=plain-sig"
        )

        redacted = app._redact_text(text)

        self.assertNotIn("abc.def.ghi", redacted)
        self.assertNotIn("plain-cookie", redacted)
        self.assertNotIn("plain-key", redacted)
        self.assertNotIn("plain-sig", redacted)
        self.assertIn("ok=1", redacted)
        self.assertIn(app._REDACTED, redacted)

    def test_redact_obj_removes_sensitive_keys_recursively(self):
        redacted = app._redact_obj({
            "safe": "visible",
            "nested": {
                "api_key": "hidden",
                "url": "https://example.test/?token=hidden-token&name=clip",
            },
        })

        self.assertEqual(redacted["safe"], "visible")
        self.assertEqual(redacted["nested"]["api_key"], app._REDACTED)
        self.assertNotIn("hidden-token", redacted["nested"]["url"])
        self.assertIn("name=clip", redacted["nested"]["url"])


if __name__ == "__main__":
    unittest.main()
