import json
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


class _FakeKeyring:
    def __init__(self):
        self.store = {}

    def set_password(self, service, username, password):
        self.store[(service, username)] = password

    def get_password(self, service, username):
        return self.store.get((service, username))


class SecretVaultTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_appdata = os.environ.get("APPDATA")
        self.old_disable_keyring = os.environ.get(app.DISABLE_KEYRING_ENV)
        os.environ["APPDATA"] = self.tmp.name
        os.environ[app.DISABLE_KEYRING_ENV] = "1"
        app._SECRET_STORAGE_MESSAGE = ""
        app._CONFIG_MIGRATED_DIRS.clear()

    def tearDown(self):
        if self.old_appdata is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = self.old_appdata
        if self.old_disable_keyring is None:
            os.environ.pop(app.DISABLE_KEYRING_ENV, None)
        else:
            os.environ[app.DISABLE_KEYRING_ENV] = self.old_disable_keyring
        app._SECRET_STORAGE_MESSAGE = ""
        app._CONFIG_MIGRATED_DIRS.clear()
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

    def test_keyring_backend_stores_secret_payload_outside_vault_file(self):
        os.environ.pop(app.DISABLE_KEYRING_ENV, None)
        fake = _FakeKeyring()

        with patch.object(app, "_keyring_backend", return_value=fake):
            app.save_config({"pixabay_api_key": "keyring-secret", "safe": "value"})
            config_path = Path(app.get_config_dir()) / "config.json"
            vault_path = Path(app.get_config_dir()) / "secrets.json"
            raw = json.loads(config_path.read_text(encoding="utf-8"))
            vault = json.loads(vault_path.read_text(encoding="utf-8"))
            secret_id = raw["pixabay_api_key"][app._SECRET_REF_KEY]

            self.assertEqual(vault[secret_id]["backend"], "keyring")
            self.assertNotIn("keyring-secret", vault_path.read_text(encoding="utf-8"))
            self.assertIn((app.SECRET_KEYRING_SERVICE, secret_id), fake.store)
            self.assertEqual(app.load_config()["pixabay_api_key"], "keyring-secret")

    def test_existing_local_vault_blob_migrates_to_keyring_when_available(self):
        config_dir = Path(app.get_config_dir())
        secret_id = "cfg.legacy"
        (config_dir / "config.json").write_text(
            json.dumps({"pixabay_api_key": {app._SECRET_REF_KEY: secret_id}}),
            encoding="utf-8",
        )
        (config_dir / "secrets.json").write_text(
            json.dumps({secret_id: app._local_secret_blob("legacy-secret")}),
            encoding="utf-8",
        )
        os.environ.pop(app.DISABLE_KEYRING_ENV, None)
        fake = _FakeKeyring()

        with patch.object(app, "_keyring_backend", return_value=fake):
            loaded = app.load_config()

        vault = json.loads((config_dir / "secrets.json").read_text(encoding="utf-8"))
        self.assertEqual(loaded["pixabay_api_key"], "legacy-secret")
        self.assertEqual(vault[secret_id]["backend"], "keyring")
        self.assertNotIn("legacy-secret", json.dumps(vault))


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
