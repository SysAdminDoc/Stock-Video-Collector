import tempfile
import unittest
from pathlib import Path

import os
import sys


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
APP_SOURCE = ROOT / "artlist_scraper.py"

import artlist_scraper as app  # noqa: E402


class ThumbnailFailureTests(unittest.TestCase):
    def _row(self, db, clip_id):
        return db.execute("SELECT * FROM clips WHERE clip_id=?", (clip_id,)).fetchone()

    def test_thumbnail_worker_records_url_failure_and_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = app.DB(str(Path(tmp) / "library.db"))
            try:
                db.save_clip({
                    "clip_id": "thumb-url-fail",
                    "title": "URL Failure",
                    "source_url": "https://example.test/thumb-url-fail",
                    "thumbnail_url": "http://127.0.0.1/private-thumb.jpg",
                })
                row = dict(self._row(db, "thumb-url-fail"))
                worker = app.ThumbnailWorker([row], str(Path(tmp) / "thumbs"), db)

                worker.run()

                updated = self._row(db, "thumb-url-fail")
                self.assertEqual(updated["thumb_status"], "error")
                self.assertIn("thumbnail URL failed", updated["thumb_error"])
                self.assertEqual(len(db.search_assets(thumb_failed_only=True)), 1)
                self.assertEqual(len(db.get_clips_needing_thumbs()), 0)
                self.assertEqual(len(db.get_clips_needing_thumbs(include_failed=True)), 1)
            finally:
                db.close()

    def test_thumbnail_worker_records_ffmpeg_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = app.DB(str(Path(tmp) / "library.db"))
            bad_video = Path(tmp) / "bad.mp4"
            bad_video.write_text("not a video", encoding="utf-8")
            try:
                db.save_clip({
                    "clip_id": "thumb-ffmpeg-fail",
                    "title": "FFmpeg Failure",
                    "source_url": "https://example.test/thumb-ffmpeg-fail",
                })
                db.update_local_path("thumb-ffmpeg-fail", str(bad_video), "done")
                row = dict(self._row(db, "thumb-ffmpeg-fail"))
                worker = app.ThumbnailWorker([row], str(Path(tmp) / "thumbs"), db)

                worker.run()

                updated = self._row(db, "thumb-ffmpeg-fail")
                self.assertEqual(updated["thumb_status"], "error")
                self.assertIn("ffmpeg", updated["thumb_error"].lower())
                self.assertGreaterEqual(updated["thumb_retry_count"], 1)
            finally:
                db.close()

    def test_reset_thumb_failure_makes_clip_retryable(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = app.DB(str(Path(tmp) / "library.db"))
            try:
                db.save_clip({
                    "clip_id": "thumb-reset",
                    "title": "Reset",
                    "source_url": "https://example.test/thumb-reset",
                    "thumbnail_url": "https://example.test/thumb.jpg",
                })
                db.mark_thumb_failure("thumb-reset", "first failure", "https://example.test/thumb.jpg")
                self.assertEqual(len(db.get_clips_needing_thumbs()), 0)

                db.reset_thumb_failure("thumb-reset")

                row = self._row(db, "thumb-reset")
                self.assertEqual(row["thumb_status"], "")
                self.assertEqual(row["thumb_error"], "")
                self.assertEqual(len(db.get_clips_needing_thumbs()), 1)
            finally:
                db.close()

    def test_thumbnail_retry_controls_are_visible(self):
        source = APP_SOURCE.read_text(encoding="utf-8")
        self.assertIn('self.chk_thumb_failed = QCheckBox("Thumb Err")', source)
        self.assertIn('self.btn_retry_thumb_errors = QPushButton("Retry Thumb Errors")', source)
        self.assertIn('thumb_menu = menu.addMenu("Thumbnails")', source)
        self.assertNotIn("QShortcut", source)


if __name__ == "__main__":
    unittest.main()
