import os
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import artlist_scraper as app  # noqa: E402
from connectors import ApiResponse, configured_connectors_for_profiles, connector_for_profile  # noqa: E402


class OfficialApiConnectorTests(unittest.TestCase):
    def test_registry_returns_only_configured_profile_connectors(self):
        cfg = {"pexels_api_key": "px", "pixabay_api_key": ""}

        connectors = configured_connectors_for_profiles(["Pexels", "Pixabay", "Artlist"], cfg)

        self.assertEqual([c.profile_name for c in connectors], ["Pexels"])
        self.assertIsNone(connector_for_profile("Artlist", cfg))

    def test_pexels_connector_maps_video_search_payload(self):
        requests = []

        def fake_client(request):
            requests.append(request)
            return ApiResponse(
                200,
                {"X-Ratelimit-Remaining": "199"},
                {
                    "total_results": 2,
                    "next_page": "https://api.pexels.com/v1/videos/search?page=2",
                    "videos": [{
                        "id": 123,
                        "url": "https://www.pexels.com/video/waves-123/",
                        "image": "https://images.pexels.com/videos/123/poster.jpeg",
                        "duration": 65,
                        "user": {"name": "A. Maker"},
                        "video_files": [
                            {"file_type": "video/mp4", "width": 640, "height": 360, "link": "https://videos.pexels.com/123-sd.mp4"},
                            {"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "https://videos.pexels.com/123-hd.mp4"},
                        ],
                    }],
                },
            )

        connector = connector_for_profile("Pexels", {"pexels_api_key": "px-secret"})
        page = connector.fetch_page(1, 10, "ocean", fake_client)

        self.assertIn("/v1/videos/search", requests[0].url)
        self.assertIn("query=ocean", requests[0].url)
        self.assertEqual(requests[0].headers["Authorization"], "px-secret")
        self.assertEqual(page.next_page, 2)
        self.assertEqual(page.quota_remaining, "199")
        self.assertEqual(page.clips[0]["clip_id"], "123")
        self.assertEqual(page.clips[0]["m3u8_url"], "https://videos.pexels.com/123-hd.mp4")
        self.assertEqual(page.clips[0]["resolution"], "1920x1080")

    def test_pixabay_connector_maps_video_payload(self):
        requests = []

        def fake_client(request):
            requests.append(request)
            return ApiResponse(
                200,
                {"X-RateLimit-Remaining": "99"},
                {
                    "totalHits": 50,
                    "hits": [{
                        "id": 456,
                        "pageURL": "https://pixabay.com/videos/forest-456/",
                        "tags": "forest, mist",
                        "duration": 12,
                        "user": "Pixabay User",
                        "videos": {
                            "small": {"width": 640, "height": 360, "url": "https://cdn.pixabay.com/456-small.mp4"},
                            "large": {"width": 3840, "height": 2160, "url": "https://cdn.pixabay.com/456-large.mp4", "thumbnail": "https://cdn.pixabay.com/456.jpg"},
                        },
                    }],
                },
            )

        connector = connector_for_profile("Pixabay", {"pixabay_api_key": "pb-secret"})
        page = connector.fetch_page(1, 25, "forest", fake_client)

        self.assertIn("key=pb-secret", requests[0].url)
        self.assertIn("q=forest", requests[0].url)
        self.assertEqual(page.next_page, 2)
        self.assertEqual(page.clips[0]["m3u8_url"], "https://cdn.pixabay.com/456-large.mp4")
        self.assertEqual(page.clips[0]["thumbnail_url"], "https://cdn.pixabay.com/456.jpg")

    def test_vimeo_connector_maps_video_payload(self):
        requests = []

        def fake_client(request):
            requests.append(request)
            return ApiResponse(
                200,
                {},
                {
                    "total": 1,
                    "paging": {"next": None},
                    "data": [{
                        "uri": "/videos/789",
                        "link": "https://vimeo.com/789",
                        "name": "Free city clip",
                        "duration": 31,
                        "user": {"name": "Vimeo Maker"},
                        "tags": [{"name": "city"}],
                        "files": [{"width": 1280, "height": 720, "type": "video/mp4", "link": "https://player.vimeo.com/progressive/789.mp4"}],
                        "pictures": {"sizes": [{"width": 640, "height": 360, "link": "https://i.vimeocdn.com/video/789.jpg"}]},
                    }],
                },
            )

        connector = connector_for_profile("Vimeo", {"vimeo_access_token": "vm-secret"})
        page = connector.fetch_page(1, 10, "city", fake_client)

        self.assertEqual(requests[0].headers["Authorization"], "Bearer vm-secret")
        self.assertIn("query=city", requests[0].url)
        self.assertEqual(page.clips[0]["clip_id"], "789")
        self.assertEqual(page.clips[0]["tags"], "city")

    def test_adobe_stock_connector_maps_video_search_payload(self):
        requests = []

        def fake_client(request):
            requests.append(request)
            return ApiResponse(
                200,
                {},
                {
                    "nb_results": 1,
                    "files": [{
                        "id": "987",
                        "title": "Office b roll",
                        "creator_name": "Adobe Creator",
                        "thumbnail_url": "https://as.ftcdn.net/thumb.jpg",
                        "content_url": "https://stock.adobe.com/content/987.mp4",
                        "details_url": "https://stock.adobe.com/video/office-b-roll/987",
                        "duration": 7,
                        "width": 1920,
                        "height": 1080,
                        "keywords": [{"name": "office"}],
                    }],
                },
            )

        connector = connector_for_profile(
            "Adobe Stock",
            {"adobe_stock_api_key": "adobe-key", "adobe_stock_access_token": "adobe-token"},
        )
        page = connector.fetch_page(1, 10, "office", fake_client)

        self.assertEqual(requests[0].headers["x-api-key"], "adobe-key")
        self.assertEqual(requests[0].headers["Authorization"], "Bearer adobe-token")
        self.assertIn("content_type:video", unquote(requests[0].url))
        self.assertEqual(page.clips[0]["preview_status"], "Watermarked preview")
        self.assertEqual(page.clips[0]["resolution"], "1920x1080")


class CrawlerOfficialApiTests(unittest.TestCase):
    def test_configured_api_connector_saves_clips_without_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = app.DB(str(Path(tmp) / "api.db"))
            try:
                profile = app.SiteProfile.get("Pexels")
                worker = app.CrawlerWorker(
                    {
                        "crawl_mode": "full",
                        "use_official_apis": True,
                        "pexels_api_key": "px-secret",
                        "api_search_query": "waves",
                        "api_page_limit": 1,
                        "api_per_page": 1,
                    },
                    db,
                    profiles=[profile],
                )

                def fake_client(_request):
                    return ApiResponse(
                        200,
                        {},
                        {
                            "videos": [{
                                "id": 321,
                                "url": "https://www.pexels.com/video/waves-321/",
                                "duration": 5,
                                "user": {"name": "Fixture Creator"},
                                "video_files": [{"file_type": "video/mp4", "width": 1280, "height": 720, "link": "https://videos.pexels.com/321.mp4"}],
                            }],
                        },
                    )

                with patch.object(app, "_safe_api_json_request", side_effect=fake_client):
                    handled = worker._run_configured_api_connectors()

                self.assertEqual(handled, {"Pexels"})
                row = db.execute("SELECT * FROM clips WHERE clip_id='321'").fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row["source_site"], "Pexels")
                self.assertEqual(row["m3u8_url"], "https://videos.pexels.com/321.mp4")
            finally:
                db.conn.close()


if __name__ == "__main__":
    unittest.main()
