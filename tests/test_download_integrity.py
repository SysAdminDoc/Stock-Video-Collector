import os
import subprocess
import sys
import tempfile
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "artlist_scraper.py"
sys.path.insert(0, str(ROOT))

import artlist_scraper as app  # noqa: E402


class _Cursor:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class _DownloadDB:
    def __init__(self, row):
        self.row = row
        self.statuses = []
        self.local_updates = []

    def execute(self, sql, params=()):
        if "WHERE dl_status='done'" in sql:
            return _Cursor(rows=[])
        if "SELECT dl_status, local_path, m3u8_url FROM clips" in sql:
            return _Cursor(row={
                "dl_status": "",
                "local_path": "",
                "m3u8_url": self.row["m3u8_url"],
            })
        if "SELECT * FROM clips WHERE clip_id" in sql:
            return _Cursor(row=self.row)
        return _Cursor()

    def set_dl_status(self, clip_id, status):
        self.statuses.append((clip_id, status))

    def update_local_path(self, clip_id, local_path, dl_status="done"):
        self.local_updates.append((clip_id, local_path, dl_status))


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


def _make_test_video(ffmpeg, path):
    result = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=16x16:d=0.2",
            "-frames:v",
            "1",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise unittest.SkipTest(f"ffmpeg test source unavailable: {result.stderr[:160]}")


class DownloadIntegrityHelperTests(unittest.TestCase):
    def test_part_path_is_final_path_with_part_suffix(self):
        self.assertEqual(
            app._download_part_path(r"C:\clips\sample.mp4"),
            r"C:\clips\sample.mp4.part",
        )

    def test_quarantine_file_moves_suspect_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            suspect = Path(tmp) / "clip.mp4"
            suspect.write_bytes(b"not a video")

            quarantined = Path(app._quarantine_file(str(suspect)))

            self.assertFalse(suspect.exists())
            self.assertTrue(quarantined.exists())
            self.assertIn(".invalid-", quarantined.name)
            self.assertEqual(quarantined.read_bytes(), b"not a video")

    def test_video_validation_rejects_non_video_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            invalid = Path(tmp) / "clip.mp4"
            invalid.write_bytes(b"not a video")

            ok, reason = app._validate_video_file(str(invalid), app._get_ffmpeg())

            self.assertFalse(ok)
            self.assertTrue(reason)

    def test_video_validation_accepts_ffmpeg_generated_video(self):
        ffmpeg = app._get_ffmpeg()
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "clip.mp4"
            _make_test_video(ffmpeg, video)

            ok, reason = app._validate_video_file(str(video), ffmpeg)

            self.assertTrue(ok, reason)


class DownloadWorkerIntegrationTests(unittest.TestCase):
    def test_download_one_classifies_404_preflight_as_permanent(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = {
                "clip_id": "missing404",
                "title": "Missing",
                "m3u8_url": "https://cdn.example.test/missing.mp4",
                "duration": "00:01",
                "creator": "",
                "collection": "",
                "resolution": "",
                "frame_rate": "",
                "camera": "",
                "formats": "",
                "source_url": "https://example.test/missing",
                "source_site": "test",
                "tags": "",
            }
            db = _DownloadDB(row)
            worker = app.DownloadWorker(str(Path(tmp) / "out"), db, max_concurrent=1, max_retries=0)
            worker._head_check_url = lambda url, timeout=8: (False, "HTTP 404")

            result = worker._download_one(row, "ffmpeg")

            self.assertEqual(result, "permanent")
            self.assertFalse(db.local_updates)

    def test_download_one_promotes_valid_part_file_atomically(self):
        ffmpeg = app._get_ffmpeg()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_video = tmp_path / "source.mp4"
            _make_test_video(ffmpeg, source_video)

            handler = partial(_QuietHandler, directory=str(tmp_path))
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                url = f"http://127.0.0.1:{server.server_address[1]}/{source_video.name}"
                row = {
                    "clip_id": "atomic1",
                    "title": "Atomic Test",
                    "m3u8_url": url,
                    "duration": "00:01",
                    "creator": "",
                    "collection": "",
                    "resolution": "",
                    "frame_rate": "",
                    "camera": "",
                    "formats": "",
                    "source_url": url,
                    "source_site": "test",
                    "tags": "",
                }
                db = _DownloadDB(row)
                out_dir = tmp_path / "out"
                worker = app.DownloadWorker(str(out_dir), db, max_concurrent=1, max_retries=0)
                worker._fn_template = "{title}"
                worker._extract_thumb = lambda clip_id, mp4_path: None
                worker._head_check_url = lambda url, timeout=8: (True, "ok")

                result = worker._download_one(row, ffmpeg)

                self.assertEqual(result, "ok")
                final_path = Path(db.local_updates[-1][1])
                self.assertTrue(final_path.exists())
                self.assertFalse(Path(f"{final_path}.part").exists())
                self.assertTrue(final_path.with_suffix(".json").exists())
                self.assertEqual(db.local_updates[-1][2], "done")
                ok, reason = app._validate_video_file(str(final_path), ffmpeg)
                self.assertTrue(ok, reason)
            finally:
                server.shutdown()
                server.server_close()


class DownloadWorkerSourceContractTests(unittest.TestCase):
    def test_download_finalizes_part_file_before_sidecar_and_database_done(self):
        source = APP.read_text(encoding="utf-8")
        self.assertIn("part_path  = _download_part_path(out_path)", source)
        self.assertIn("'-f', 'mp4',", source)
        self.assertIn("os.replace(part_path, out_path)", source)

        replace_idx = source.index("os.replace(part_path, out_path)")
        sidecar_idx = source.index("self._write_sidecar(clip_data, out_path)")
        db_idx = source.index("self.db.update_local_path(clip_id, out_path, 'done')", replace_idx)

        self.assertLess(replace_idx, sidecar_idx)
        self.assertLess(replace_idx, db_idx)

    def test_archive_verification_uses_video_validation(self):
        source = APP.read_text(encoding="utf-8")
        verify_idx = source.index("def _verify_archive(self):")
        reset_idx = source.index("def _reset_missing(self):")
        verify_body = source[verify_idx:reset_idx]

        self.assertIn("_validate_video_file(path, ffmpeg)", verify_body)
        self.assertIn("invalid.append", verify_body)


if __name__ == "__main__":
    unittest.main()
