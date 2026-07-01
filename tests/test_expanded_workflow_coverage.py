import csv
import json
import os
import sqlite3
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import artlist_scraper as app  # noqa: E402


class DatabaseMigrationFtsTests(unittest.TestCase):
    def test_legacy_schema_migrates_columns_and_rebuilds_fts(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "legacy.db"
            conn = sqlite3.connect(db_path)
            conn.executescript(
                """
                CREATE TABLE clips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clip_id TEXT UNIQUE,
                    source_url TEXT,
                    title TEXT,
                    creator TEXT,
                    collection TEXT,
                    resolution TEXT,
                    duration TEXT,
                    frame_rate TEXT,
                    camera TEXT,
                    formats TEXT,
                    tags TEXT,
                    m3u8_url TEXT DEFAULT '',
                    thumbnail_url TEXT DEFAULT '',
                    found_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE crawled_pages (
                    url TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'pending',
                    depth INTEGER DEFAULT 0,
                    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE crawl_queue (
                    url TEXT PRIMARY KEY,
                    depth INTEGER DEFAULT 0,
                    priority INTEGER DEFAULT 0,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                INSERT INTO clips (
                    clip_id, source_url, title, creator, collection, resolution,
                    duration, frame_rate, camera, formats, tags, m3u8_url, thumbnail_url
                ) VALUES (
                    'legacy-1', 'https://example.test/legacy', 'Legacy Sunset',
                    'Archive', 'Old DB', '1920x1080', '0:05', '30', '',
                    'mp4', 'sunset migration', 'https://cdn.example.test/legacy.mp4', ''
                );
                INSERT INTO crawl_queue(url, depth, priority) VALUES ('https://example.test/page', 1, 5);
                """
            )
            conn.commit()
            conn.close()

            db = app.DB(str(db_path))
            try:
                clip_cols = {row["name"] for row in db.execute("PRAGMA table_info(clips)").fetchall()}
                queue_cols = {row["name"] for row in db.execute("PRAGMA table_info(crawl_queue)").fetchall()}

                self.assertIn("local_path", clip_cols)
                self.assertIn("user_tags", clip_cols)
                self.assertIn("license_name", clip_cols)
                self.assertIn("profile", queue_cols)

                self.assertEqual(db.rebuild_fts(), 1)
                rows = db.search("sunset")
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["clip_id"], "legacy-1")
            finally:
                db.close()


class _Signal:
    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self._callbacks):
            callback(*args)


class _SynchronousBackgroundWorker:
    def __init__(self, fn, *args, **kwargs):
        self._fn = fn
        self.result_signal = _Signal()
        self.error_signal = _Signal()
        self.finished = _Signal()

    def start(self):
        try:
            self.result_signal.emit(self._fn())
        except Exception as exc:  # pragma: no cover - failure path asserts via caller status text
            self.error_signal.emit(str(exc))
        finally:
            self.finished.emit()


class _TextField:
    def __init__(self, value):
        self._value = value

    def text(self):
        return self._value


class _StatusLabel:
    def __init__(self):
        self.values = []

    def setText(self, value):
        self.values.append(value)


def _bind_export_window(out_dir, rows):
    dummy = types.SimpleNamespace()
    dummy.inp_output = _TextField(str(out_dir))
    dummy.lbl_export_status = _StatusLabel()
    dummy._bg_workers = []
    dummy._get_export_rows = lambda filtered=False: rows
    dummy._ts = lambda: "20260101-000000"
    dummy._out_dir = types.MethodType(app.MainWindow._out_dir, dummy)
    dummy._export_txt = types.MethodType(app.MainWindow._export_txt, dummy)
    dummy._export_json = types.MethodType(app.MainWindow._export_json, dummy)
    dummy._export_m3u = types.MethodType(app.MainWindow._export_m3u, dummy)
    dummy._export_csv = types.MethodType(app.MainWindow._export_csv, dummy)
    dummy._export_handoff = types.MethodType(app.MainWindow._export_handoff, dummy)
    return dummy


class ExportFormatTests(unittest.TestCase):
    def test_export_formats_write_expected_files_and_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "exports"
            local_clip = Path(tmp) / "downloaded.mp4"
            local_clip.write_bytes(b"local")
            row = {
                "clip_id": "clip-1",
                "title": "Export Clip",
                "creator": "Unit Test",
                "collection": "Exports",
                "tags": "export,metadata",
                "resolution": "1920x1080",
                "duration": "0:05",
                "frame_rate": "30",
                "camera": "",
                "formats": "mp4",
                "m3u8_url": "https://cdn.example.test/export.mp4",
                "source_url": "https://example.test/export",
                "source_site": "Pexels",
                "license_name": "Pexels License",
                "license_url": "https://www.pexels.com/license/",
                "attribution_required": "No",
                "attribution_text": "",
                "terms_url": "https://www.pexels.com/terms-of-service/",
                "preview_status": "Direct MP4",
                "found_at": "2026-06-30T00:00:00",
                "local_path": str(local_clip),
            }
            dummy = _bind_export_window(out_dir, [row])

            with patch.object(app, "BackgroundWorker", _SynchronousBackgroundWorker):
                dummy._export_txt()
                dummy._export_json()
                dummy._export_m3u()
                dummy._export_csv()

            txt = (out_dir / "video-urls-20260101-000000.txt").read_text(encoding="utf-8")
            self.assertEqual(txt.strip(), "https://cdn.example.test/export.mp4")

            metadata = json.loads((out_dir / "video-metadata-20260101-000000.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["total"], 1)
            self.assertEqual(metadata["clips"][0]["license_name"], "Pexels License")

            playlist = (out_dir / "video-playlist-20260101-000000.m3u").read_text(encoding="utf-8")
            self.assertIn("#EXTM3U", playlist)
            self.assertIn(str(local_clip), playlist)

            with (out_dir / "video-metadata-20260101-000000.csv").open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(rows[0]["clip_id"], "clip-1")
            self.assertEqual(rows[0]["preview_status"], "Direct MP4")

    def test_handoff_package_contains_media_sidecars_manifest_and_checksums(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "exports"
            local_clip = root / "downloaded.mp4"
            thumb = root / "thumb.jpg"
            local_clip.write_bytes(b"media-bytes")
            thumb.write_bytes(b"thumb-bytes")
            row = {
                "clip_id": "clip-1",
                "title": "Handoff Clip",
                "creator": "Unit Test",
                "collection": "Handoffs",
                "tags": "handoff,metadata",
                "resolution": "1920x1080",
                "duration": "0:05",
                "frame_rate": "30",
                "formats": "mp4",
                "m3u8_url": "https://cdn.example.test/handoff.mp4",
                "source_url": "https://example.test/handoff",
                "source_site": "Pexels",
                "license_name": "Pexels License",
                "license_url": "https://www.pexels.com/license/",
                "attribution_required": "No",
                "terms_url": "https://www.pexels.com/terms-of-service/",
                "preview_status": "Direct MP4",
                "local_path": str(local_clip),
                "thumb_path": str(thumb),
                "file_sha256": app._sha256_file(str(local_clip)),
            }
            dummy = _bind_export_window(out_dir, [row])

            with patch.object(app, "BackgroundWorker", _SynchronousBackgroundWorker):
                dummy._export_handoff(filtered=True)

            archives = list(out_dir.glob("video-handoff-filtered-20260101-000000.zip"))
            self.assertEqual(len(archives), 1)
            with zipfile.ZipFile(archives[0]) as zf:
                names = set(zf.namelist())
                self.assertIn("manifest.json", names)
                self.assertIn("checksums.sha256", names)
                self.assertIn("licenses/ATTRIBUTION.txt", names)
                self.assertTrue(any(name.startswith("clips/") and name.endswith(".mp4") for name in names))
                self.assertTrue(any(name.startswith("thumbnails/") and name.endswith(".jpg") for name in names))
                self.assertIn("sidecars/clip-1.json", names)

                manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
                self.assertEqual(manifest["schema"], "stock-video-collector.handoff.v1")
                self.assertEqual(manifest["total_clips"], 1)
                self.assertEqual(manifest["clips"][0]["provenance"]["license"]["name"], "Pexels License")
                self.assertIn("copy-only", manifest["media_write_policy"])
                checksums = zf.read("checksums.sha256").decode("utf-8")
                self.assertIn("manifest.json", checksums)
                self.assertIn("sidecars/clip-1.json", checksums)


class ImportWorkerMetadataTests(unittest.TestCase):
    def test_import_worker_saves_ffprobe_metadata_and_local_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Source Folder"
            folder.mkdir()
            video = folder / "Sample_Clip-1080p.mp4"
            video.write_bytes(b"placeholder")
            db = app.DB(str(root / "import.db"))
            worker = app.ImportWorker(str(folder), db, str(root / "thumbs"), recursive=False)
            try:
                with (
                    patch.object(app, "_get_ffmpeg", return_value="ffmpeg"),
                    patch.object(app.ImportWorker, "_find_ffprobe", return_value="ffprobe"),
                    patch.object(app.ImportWorker, "_probe", return_value={
                        "resolution": "1920x1080",
                        "duration": "0:05",
                        "fps": "30",
                    }),
                    patch.object(app.ImportWorker, "_extract_thumb", return_value=None),
                ):
                    worker.run()

                row = db.execute("SELECT * FROM clips WHERE source_site='Local Import'").fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row["title"], "Sample Clip 1080p")
                self.assertEqual(row["collection"], "Source Folder")
                self.assertEqual(row["resolution"], "1920x1080")
                self.assertEqual(row["duration"], "0:05")
                self.assertEqual(row["frame_rate"], "30")
                self.assertEqual(row["local_path"], str(video))
                self.assertEqual(row["dl_status"], "done")
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
