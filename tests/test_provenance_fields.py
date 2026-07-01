import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import artlist_scraper as app


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "artlist_scraper.py"


class ProvenanceFieldTests(unittest.TestCase):
    def _db(self, tmpdir):
        return app.DB(str(Path(tmpdir) / "clips.db"))

    def test_schema_includes_license_and_attribution_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp)
            cols = {
                row["name"]
                for row in db.execute("PRAGMA table_info(clips)").fetchall()
            }
            db.conn.close()

        for field in app.ALL_PROVENANCE_FIELDS:
            self.assertIn(field, cols)

    def test_source_profile_defaults_fill_missing_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp)
            db.save_clip({
                "clip_id": "pexels-123",
                "source_url": "https://www.pexels.com/video/example-123/",
                "source_site": "Pexels",
                "title": "Example",
            })
            row = db.execute(
                "SELECT * FROM clips WHERE clip_id=?",
                ("pexels-123",),
            ).fetchone()
            values = dict(row)
            db.conn.close()

        self.assertEqual(values["license_name"], "Pexels License")
        self.assertEqual(values["license_url"], "https://www.pexels.com/license/")
        self.assertEqual(values["attribution_required"], "No")
        self.assertEqual(values["preview_status"], "Direct MP4")

    def test_explicit_provenance_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp)
            db.save_clip({
                "clip_id": "custom-1",
                "source_url": "https://www.pexels.com/video/example-456/",
                "source_site": "Pexels",
                "title": "Custom",
                "license_name": "Custom Client License",
                "terms_url": "https://example.test/terms",
                "preview_status": "Client approved",
            })
            row = db.execute(
                "SELECT license_name, terms_url, preview_status FROM clips WHERE clip_id=?",
                ("custom-1",),
            ).fetchone()
            values = dict(row)
            db.conn.close()

        self.assertEqual(values["license_name"], "Custom Client License")
        self.assertEqual(values["terms_url"], "https://example.test/terms")
        self.assertEqual(values["preview_status"], "Client approved")

    def test_update_metadata_can_backfill_missing_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = self._db(tmp)
            db.save_clip({
                "clip_id": "adobe-1",
                "source_url": "https://stock.adobe.com/video/sample/1234",
                "source_site": "Adobe Stock",
                "title": "Adobe",
                "license_name": " ",
            })
            db.execute(
                "UPDATE clips SET license_name='', license_url='', "
                "attribution_required='', terms_url='', preview_status='' "
                "WHERE clip_id='adobe-1'"
            )
            db.commit()
            db.update_metadata("adobe-1", {"source_site": "Adobe Stock", "title": "Adobe updated"})
            row = db.execute(
                "SELECT license_name, terms_url, preview_status FROM clips WHERE clip_id=?",
                ("adobe-1",),
            ).fetchone()
            values = dict(row)
            db.conn.close()

        self.assertEqual(values["license_name"], "Adobe Stock license terms")
        self.assertEqual(values["terms_url"], "https://stock.adobe.com/license-terms")
        self.assertEqual(values["preview_status"], "Watermarked preview")

    def test_exports_and_sidecars_include_provenance_fields(self):
        source = APP.read_text(encoding="utf-8")
        for field in app.ALL_PROVENANCE_FIELDS:
            self.assertIn(f"'{field}'", source)
        self.assertIn("'source_site','license_name','license_url'", source)

    def test_ffprobe_tags_normalize_to_embedded_provenance(self):
        info = {
            "format": {
                "tags": {
                    "title": "Embedded Clip Title",
                    "artist": "Embedded Creator",
                    "copyright": "Copyright 2026 Example Studio",
                    "XMPRights:WebStatement": "https://example.test/license",
                    "terms_of_use": "https://example.test/terms",
                    "credit": "Courtesy Example Studio",
                }
            },
            "streams": [],
        }
        fields = app._embedded_provenance_from_ffprobe(info)

        self.assertEqual(fields["embedded_title"], "Embedded Clip Title")
        self.assertEqual(fields["embedded_creator"], "Embedded Creator")
        self.assertEqual(fields["embedded_rights"], "Copyright 2026 Example Studio")
        self.assertEqual(fields["embedded_license_url"], "https://example.test/license")
        self.assertEqual(fields["embedded_terms_url"], "https://example.test/terms")
        self.assertEqual(fields["embedded_attribution_text"], "Courtesy Example Studio")
        self.assertIn("format.title", json.loads(fields["embedded_metadata_json"]))

    def test_import_probe_reads_embedded_provenance_tags(self):
        fake_ffprobe = {
            "format": {
                "duration": "7.25",
                "tags": {
                    "title": "Tagged Import",
                    "creator": "Camera Operator",
                    "rights": "Client rights statement",
                    "license_url": "https://example.test/import-license",
                },
            },
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30000/1001",
                    "tags": {"credit": "Credit Camera Operator"},
                }
            ],
        }
        worker = app.ImportWorker("unused", None, "unused", recursive=False)

        with patch.object(
            app.subprocess,
            "run",
            return_value=types.SimpleNamespace(returncode=0, stdout=json.dumps(fake_ffprobe)),
        ):
            meta = worker._probe("ffprobe", "tagged.mp4")

        self.assertEqual(meta["resolution"], "1920x1080")
        self.assertEqual(meta["duration"], "0:07")
        self.assertEqual(meta["fps"], "30")
        self.assertEqual(meta["embedded_title"], "Tagged Import")
        self.assertEqual(meta["embedded_creator"], "Camera Operator")
        self.assertEqual(meta["embedded_rights"], "Client rights statement")
        self.assertEqual(meta["embedded_license_url"], "https://example.test/import-license")
        self.assertEqual(meta["embedded_attribution_text"], "Credit Camera Operator")

    def test_sidecar_roundtrip_preserves_embedded_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mp4 = root / "clip.mp4"
            mp4.write_bytes(b"video")
            db = self._db(tmp)
            try:
                worker = app.DownloadWorker(str(root), db)
                worker._write_sidecar({
                    "clip_id": "embedded-1",
                    "title": "Embedded",
                    "source_site": "Local Import",
                    "license_name": "Copyright 2026 Example Studio",
                    "embedded_title": "Embedded",
                    "embedded_creator": "Example Studio",
                    "embedded_rights": "Copyright 2026 Example Studio",
                    "embedded_license_url": "https://example.test/license",
                    "embedded_metadata_source": "ffprobe:format/stream tags",
                    "embedded_metadata_json": json.dumps({"format.title": "Embedded"}),
                }, str(mp4))

                sidecar = json.loads((root / "clip.json").read_text(encoding="utf-8"))
                self.assertEqual(sidecar["embedded_rights"], "Copyright 2026 Example Studio")
                self.assertEqual(
                    sidecar["provenance"]["schema"],
                    "stock-video-collector.provenance.v1",
                )
                self.assertIn("never modified in place", sidecar["provenance"]["media_write_policy"])

                normalized = app._normalize_sidecar_payload(sidecar)
                db.save_clip(normalized)
                row = db.execute(
                    "SELECT embedded_rights, embedded_license_url FROM clips WHERE clip_id=?",
                    ("embedded-1",),
                ).fetchone()
                self.assertEqual(row["embedded_rights"], "Copyright 2026 Example Studio")
                self.assertEqual(row["embedded_license_url"], "https://example.test/license")
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
