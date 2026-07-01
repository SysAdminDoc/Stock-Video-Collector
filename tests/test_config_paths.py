import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import artlist_scraper as app  # noqa: E402


class ConfigPathMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_appdata = os.environ.get("APPDATA")
        self.old_portable = os.environ.get(app.PORTABLE_ENV)
        self.old_argv = list(sys.argv)
        os.environ["APPDATA"] = self.tmp.name
        os.environ.pop(app.PORTABLE_ENV, None)
        sys.argv = [sys.argv[0]]
        app._CONFIG_MIGRATION_MESSAGE = ""
        app._CONFIG_MIGRATED_DIRS.clear()

    def tearDown(self):
        if self.old_appdata is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = self.old_appdata
        if self.old_portable is None:
            os.environ.pop(app.PORTABLE_ENV, None)
        else:
            os.environ[app.PORTABLE_ENV] = self.old_portable
        sys.argv = self.old_argv
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

    def test_portable_env_stores_config_and_output_under_app_directory(self):
        app_root = Path(self.tmp.name) / "app"
        app_root.mkdir()
        os.environ[app.PORTABLE_ENV] = "1"

        with mock.patch.object(app, "_app_root_dir", return_value=app_root):
            config_dir = Path(app.get_config_dir())
            output_dir = Path(app._default_output_dir())
            thumb_dir = Path(app.get_thumbnail_cache_dir())
            diag = app.get_config_diagnostics()

        self.assertEqual(config_dir, app_root / app.PORTABLE_DATA_DIR_NAME)
        self.assertEqual(output_dir, config_dir / "output")
        self.assertEqual(thumb_dir, config_dir / "thumbnails")
        self.assertEqual(diag["mode"], "portable")
        self.assertEqual(diag["trigger"], "env")
        self.assertIn(app.PORTABLE_SENTINEL_NAME, diag["sentinel"])

    def test_portable_cli_flag_enables_portable_mode(self):
        app_root = Path(self.tmp.name) / "cli-app"
        app_root.mkdir()
        sys.argv = [self.old_argv[0], "--portable"]

        with mock.patch.object(app, "_app_root_dir", return_value=app_root):
            self.assertTrue(app.is_portable_mode())
            self.assertEqual(Path(app.get_config_dir()), app_root / app.PORTABLE_DATA_DIR_NAME)
            self.assertEqual(app.get_config_diagnostics()["trigger"], "cli")

    def test_portable_sentinel_enables_portable_mode_without_legacy_migration(self):
        app_root = Path(self.tmp.name) / "sentinel-app"
        app_root.mkdir()
        (app_root / app.PORTABLE_SENTINEL_NAME).write_text("portable", encoding="utf-8")
        legacy = Path(self.tmp.name) / app.LEGACY_APP_CONFIG_DIR_NAME
        legacy.mkdir()
        (legacy / "config.json").write_text(json.dumps({"source": "legacy"}), encoding="utf-8")

        with mock.patch.object(app, "_app_root_dir", return_value=app_root):
            config_dir = Path(app.get_config_dir())
            diag = app.get_config_diagnostics()

        self.assertEqual(config_dir, app_root / app.PORTABLE_DATA_DIR_NAME)
        self.assertEqual(diag["trigger"], "sentinel")
        self.assertFalse((config_dir / "config.json").exists())
        self.assertEqual(app._consume_config_migration_message(), "")


if __name__ == "__main__":
    unittest.main()
