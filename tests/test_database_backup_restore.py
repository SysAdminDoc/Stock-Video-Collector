import os
import json
import sys
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "artlist_scraper.py"
sys.path.insert(0, str(ROOT))

import artlist_scraper as app  # noqa: E402


class DatabaseBackupRestoreTests(unittest.TestCase):
    def test_backup_clear_restore_round_trip_preserves_clips_and_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "library.db"
            backup_path = Path(tmp) / "backups" / "library-backup.db"
            db = app.DB(str(db_path))
            try:
                db.save_clip({
                    "clip_id": "clip-1",
                    "source_url": "https://example.test/video/clip-1",
                    "title": "Backup Test Clip",
                    "creator": "Unit Test",
                    "collection": "Backups",
                    "resolution": "1920x1080",
                    "duration": "00:01",
                    "frame_rate": "24",
                    "camera": "",
                    "formats": "mp4",
                    "tags": "backup restore",
                    "m3u8_url": "https://cdn.example.test/clip-1.m3u8",
                    "thumbnail_url": "",
                    "source_site": "test",
                })
                db.enqueue("https://example.test/page", depth=1, priority=5, profile="Generic")

                created = db.backup_to(str(backup_path))
                self.assertEqual(created, str(backup_path))
                self.assertTrue(backup_path.exists())
                self.assertGreater(backup_path.stat().st_size, 0)

                db.clear_all()
                self.assertEqual(db.clip_count(), 0)
                self.assertEqual(db.queue_size(), 0)

                db.restore_from(str(backup_path))

                self.assertEqual(db.clip_count(), 1)
                self.assertEqual(db.queue_size(), 1)
                row = db.execute("SELECT title, source_site FROM clips WHERE clip_id=?", ("clip-1",)).fetchone()
                self.assertEqual(row["title"], "Backup Test Clip")
                self.assertEqual(row["source_site"], "test")
            finally:
                db.close()

    def test_restore_rejects_corrupt_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "library.db"
            bad_backup = Path(tmp) / "backups" / "bad.db"
            bad_backup.parent.mkdir()
            bad_backup.write_bytes(b"not sqlite")
            db = app.DB(str(db_path))
            try:
                db.save_clip({"clip_id": "safe", "title": "Safe Clip", "source_url": "https://example.test"})
                with self.assertRaises(Exception):
                    db.restore_from(str(bad_backup))
                self.assertEqual(db.clip_count(), 1)
            finally:
                db.close()

    def test_backup_catalog_records_checksums_and_prunes_by_retention(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_appdata = os.environ.get("APPDATA")
            os.environ["APPDATA"] = str(Path(tmp) / "appdata")
            app._CONFIG_MIGRATION_MESSAGE = ""
            app._CONFIG_MIGRATED_DIRS.clear()
            db = None
            try:
                db_path = Path(tmp) / "library.db"
                db = app.DB(str(db_path))
                db.save_clip({"clip_id": "clip-a", "title": "A", "source_url": "https://example.test/a"})
                class BackupHarness:
                    _db_backup_dir = app.MainWindow._db_backup_dir
                    _db_backup_catalog_path = app.MainWindow._db_backup_catalog_path
                    _backup_retention_count = app.MainWindow._backup_retention_count
                    _catalog_db_backups = app.MainWindow._catalog_db_backups
                    _prune_db_backups = app.MainWindow._prune_db_backups
                    _find_latest_db_backup = app.MainWindow._find_latest_db_backup
                    _sync_restore_db_button = app.MainWindow._sync_restore_db_button

                harness = BackupHarness()
                harness.db = db
                harness._latest_db_backup_path = ""
                harness._on_log = lambda *args, **kwargs: None
                backup_dir = Path(harness._db_backup_dir())
                first = backup_dir / "stock-video-collector-20260101-000000.db"
                second = backup_dir / "stock-video-collector-20260102-000000.db"
                db.backup_to(str(first))
                db.save_clip({"clip_id": "clip-b", "title": "B", "source_url": "https://example.test/b"})
                db.backup_to(str(second))
                os.utime(first, (1_700_000_000, 1_700_000_000))
                os.utime(second, (1_700_100_000, 1_700_100_000))

                entries = harness._catalog_db_backups()
                self.assertEqual(len(entries), 2)
                self.assertTrue(all(e["valid"] for e in entries))
                self.assertTrue(all(len(e["sha256"]) == 64 for e in entries))
                catalog = json.loads(Path(harness._db_backup_catalog_path()).read_text(encoding="utf-8"))
                self.assertEqual(len(catalog["backups"]), 2)

                removed = harness._prune_db_backups(1)
                self.assertEqual(len(removed), 1)
                self.assertFalse(first.exists())
                self.assertTrue(second.exists())
            finally:
                if db is not None:
                    db.close()
                if old_appdata is None:
                    os.environ.pop("APPDATA", None)
                else:
                    os.environ["APPDATA"] = old_appdata
                app._CONFIG_MIGRATION_MESSAGE = ""
                app._CONFIG_MIGRATED_DIRS.clear()


class ClearDatabaseSourceContractTests(unittest.TestCase):
    def test_clear_db_uses_backup_and_restore_flow_without_confirmation_dialog(self):
        source = APP.read_text(encoding="utf-8")
        clear_start = source.index("def _clear_db(self):")
        rebuild_start = source.index("def _rebuild_fts(self):")
        clear_restore_block = source[clear_start:rebuild_start]

        self.assertNotIn("QMessageBox.question", clear_restore_block)
        self.assertIn("backup_to(backup_path)", clear_restore_block)
        self.assertIn("Restore Last Backup is available", clear_restore_block)
        self.assertIn("def _restore_latest_db_backup(self):", clear_restore_block)
        self.assertIn("restore_from(backup_path)", clear_restore_block)
        self.assertIn("_catalog_db_backups()", clear_restore_block)
        self.assertIn("_prune_db_backups", clear_restore_block)

    def test_restore_button_is_wired_in_crawl_toolbar(self):
        source = APP.read_text(encoding="utf-8")

        self.assertIn('self.btn_restore_db = QPushButton("Restore Last Backup")', source)
        self.assertIn("self.btn_restore_db.clicked.connect(self._restore_latest_db_backup)", source)
        self.assertIn('self.btn_backup_catalog = QPushButton("Backups")', source)
        self.assertIn("self._sync_restore_db_button()", source)

    def test_backup_catalog_ui_is_wired_in_archive_tab(self):
        source = APP.read_text(encoding="utf-8")

        self.assertIn('grp_backups = QGroupBox("Database Backups")', source)
        self.assertIn("self.backup_table = QTableWidget(0, 6)", source)
        self.assertIn("self.btn_backup_restore_selected.clicked.connect(self._restore_selected_db_backup)", source)
        self.assertIn("self.btn_backup_prune.clicked.connect(self._prune_db_backups_action)", source)


if __name__ == "__main__":
    unittest.main()
