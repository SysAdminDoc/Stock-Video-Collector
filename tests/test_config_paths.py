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


class ConfigPathMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_appdata = os.environ.get("APPDATA")
        os.environ["APPDATA"] = self.tmp.name
        app._CONFIG_MIGRATION_MESSAGE = ""
        app._CONFIG_MIGRATED_DIRS.clear()

    def tearDown(self):
        if self.old_appdata is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = self.old_appdata
        app._CONFIG_MIGRATION_MESSAGE = ""
        app._CONFIG_MIGRATED_DIRS.clear()
        self.tmp.cleanup()

    def test_get_config_dir_uses_stock_video_collector_name(self):
        config_dir = Path(app.get_config_dir())

        self.assertEqual(config_dir.name, app.APP_CONFIG_DIR_NAME)
        self.assertEqual(config_dir.parent, Path(self.tmp.name))
        self.assertNotIn(app.LEGACY_APP_CONFIG_DIR_NAME, config_dir.parts)

    def test_legacy_config_data_copies_missing_files_without_overwrite(self):
        base = Path(self.tmp.name)
        legacy = base / app.LEGACY_APP_CONFIG_DIR_NAME
        current = base / app.APP_CONFIG_DIR_NAME
        legacy_backups = legacy / "backups"
        legacy_browser_cache = legacy / "browser_profile"
        legacy_backups.mkdir(parents=True)
        legacy_browser_cache.mkdir(parents=True)
        current.mkdir()

        (legacy / "config.json").write_text(json.dumps({"source": "legacy"}), encoding="utf-8")
        (legacy / "secrets.key").write_text("legacy-key", encoding="utf-8")
        (legacy / "secrets.json").write_text(json.dumps({"vault": True}), encoding="utf-8")
        (legacy / "artlist_results.db").write_bytes(b"sqlite-db")
        (legacy_backups / "library.db").write_bytes(b"sqlite-backup")
        (legacy_browser_cache / "cache.bin").write_bytes(b"regenerable-cache")
        (current / "config.json").write_text(json.dumps({"source": "current"}), encoding="utf-8")

        config_dir = Path(app.get_config_dir())
        message = app._consume_config_migration_message()

        self.assertEqual(config_dir, current)
        self.assertEqual(json.loads((current / "config.json").read_text(encoding="utf-8"))["source"], "current")
        self.assertEqual((current / "secrets.key").read_text(encoding="utf-8"), "legacy-key")
        self.assertEqual(json.loads((current / "secrets.json").read_text(encoding="utf-8"))["vault"], True)
        self.assertEqual((current / "artlist_results.db").read_bytes(), b"sqlite-db")
        self.assertEqual((current / "backups" / "library.db").read_bytes(), b"sqlite-backup")
        self.assertFalse((current / "browser_profile").exists())
        self.assertIn("Migrated", message)
        self.assertIn(app.APP_CONFIG_DIR_NAME, message)

    def test_thumbnail_cache_uses_current_config_dir(self):
        thumb_dir = Path(app.get_thumbnail_cache_dir())

        self.assertEqual(thumb_dir.name, "thumbnails")
        self.assertEqual(thumb_dir.parent.name, app.APP_CONFIG_DIR_NAME)
        self.assertTrue(thumb_dir.exists())

    def test_default_output_dir_uses_current_product_name(self):
        output_dir = Path(app._default_output_dir())

        self.assertEqual(output_dir.name, "output")
        self.assertEqual(output_dir.parent.name, app.APP_CONFIG_DIR_NAME)


if __name__ == "__main__":
    unittest.main()
