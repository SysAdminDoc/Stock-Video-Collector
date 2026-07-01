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


class DuplicateDetectionTests(unittest.TestCase):
    def _db(self, tmp):
        return app.DB(str(Path(tmp) / "duplicates.db"))

    def _save_clip(self, db, clip_id, title):
        db.save_clip({
            "clip_id": clip_id,
            "title": title,
            "source_url": f"https://example.test/{clip_id}",
            "m3u8_url": f"https://cdn.example.test/{clip_id}.mp4",
            "source_site": "test",
        })

    def test_exact_hashes_group_and_duplicate_filter_finds_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp)
            try:
                self._save_clip(db, "a", "Exact A")
                self._save_clip(db, "b", "Exact B")
                self._save_clip(db, "c", "Unique C")

                db.update_duplicate_fingerprints("a", "abc123", "0000000000000000")
                db.update_duplicate_fingerprints("b", "abc123", "ffffffffffffffff")
                db.update_duplicate_fingerprints("c", "unique", "1234567890abcdef")

                rows = db.execute(
                    "SELECT clip_id, duplicate_group, duplicate_status FROM clips ORDER BY clip_id"
                ).fetchall()
                values = {row["clip_id"]: dict(row) for row in rows}

                self.assertTrue(values["a"]["duplicate_group"])
                self.assertEqual(values["a"]["duplicate_group"], values["b"]["duplicate_group"])
                self.assertEqual(values["a"]["duplicate_status"], "review")
                self.assertEqual(values["c"]["duplicate_group"], "")

                filtered = db.search_assets(duplicates_only=True)
                self.assertEqual({row["clip_id"] for row in filtered}, {"a", "b"})

                db.set_duplicate_status("a", "keep")
                status = db.execute("SELECT duplicate_status FROM clips WHERE clip_id='a'").fetchone()[0]
                self.assertEqual(status, "keep")
            finally:
                db.close()

    def test_near_visual_hashes_group_without_matching_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp)
            try:
                self._save_clip(db, "near-a", "Near A")
                self._save_clip(db, "near-b", "Near B")

                db.update_duplicate_fingerprints("near-a", "sha-a", "0000000000000000")
                db.update_duplicate_fingerprints("near-b", "sha-b", "0000000000000003")

                rows = db.execute(
                    "SELECT clip_id, duplicate_group FROM clips WHERE duplicate_group!='' ORDER BY clip_id"
                ).fetchall()
                self.assertEqual([row["clip_id"] for row in rows], ["near-a", "near-b"])
                self.assertEqual(rows[0]["duplicate_group"], rows[1]["duplicate_group"])
            finally:
                db.close()

    def test_hash_helpers_return_empty_for_missing_files(self):
        self.assertEqual(app._sha256_file("missing.mp4"), "")
        self.assertEqual(app._video_perceptual_hash("missing.mp4", "ffmpeg"), "")

    def test_import_worker_persists_duplicate_fingerprints(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "imports"
            folder.mkdir()
            video = folder / "Duplicate_Source.mp4"
            video.write_bytes(b"placeholder")
            db = self._db(tmp)
            worker = app.ImportWorker(str(folder), db, str(root / "thumbs"), recursive=False)
            try:
                with (
                    patch.object(app, "_get_ffmpeg", return_value="ffmpeg"),
                    patch.object(app.ImportWorker, "_find_ffprobe", return_value="ffprobe"),
                    patch.object(app.ImportWorker, "_probe", return_value={
                        "resolution": "1280x720",
                        "duration": "0:03",
                        "fps": "24",
                    }),
                    patch.object(app.ImportWorker, "_extract_thumb", return_value=None),
                    patch.object(app, "_sha256_file", return_value="import-sha"),
                    patch.object(app, "_video_perceptual_hash", return_value="0101010101010101"),
                ):
                    worker.run()

                row = db.execute("SELECT file_sha256, perceptual_hash FROM clips").fetchone()
                self.assertEqual(row["file_sha256"], "import-sha")
                self.assertEqual(row["perceptual_hash"], "0101010101010101")
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
