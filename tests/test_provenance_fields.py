import tempfile
import unittest
from pathlib import Path

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

        for field in app.PROVENANCE_FIELDS:
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
        for field in app.PROVENANCE_FIELDS:
            self.assertIn(f"'{field}'", source)
        self.assertIn("'source_site','license_name','license_url'", source)


if __name__ == "__main__":
    unittest.main()
