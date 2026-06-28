import os
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

    def test_restore_button_is_wired_in_crawl_toolbar(self):
        source = APP.read_text(encoding="utf-8")

        self.assertIn('self.btn_restore_db = QPushButton("Restore Last Backup")', source)
        self.assertIn("self.btn_restore_db.clicked.connect(self._restore_latest_db_backup)", source)
        self.assertIn("self._sync_restore_db_button()", source)


if __name__ == "__main__":
    unittest.main()
