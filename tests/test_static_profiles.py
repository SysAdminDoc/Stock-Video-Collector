import py_compile
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "artlist_scraper.py"


def _profile(profile_name):
    import artlist_scraper as app

    profile = app.SiteProfile.get(profile_name)
    if not profile:
        raise AssertionError(f"{profile_name} profile registration not found")
    return profile


def _kw(profile, name):
    if not hasattr(profile, name):
        raise AssertionError(f"{name} attribute not found")
    return getattr(profile, name)


class StaticSourceTests(unittest.TestCase):
    def test_entrypoint_compiles(self):
        py_compile.compile(str(APP), doraise=True)


class CrawlModeAvailabilityTests(unittest.TestCase):
    def test_direct_http_mode_does_not_require_browser(self):
        import artlist_scraper as app

        self.assertFalse(app.MainWindow._crawl_mode_requires_browser(object(), "direct_http"))
        self.assertTrue(app.MainWindow._crawl_mode_requires_browser(object(), "full"))
        self.assertTrue(app.MainWindow._crawl_mode_requires_browser(object(), "api_discover"))

    def test_direct_http_start_path_precedes_chromium_gate(self):
        source = APP.read_text(encoding="utf-8")
        start_idx = source.index("def _start_crawl(self):")
        pause_idx = source.index("def _toggle_pause", start_idx)
        body = source[start_idx:pause_idx]

        direct_idx = body.index("if mode == 'direct_http':")
        chromium_idx = body.index("if not _chromium_is_ready():")

        self.assertLess(direct_idx, chromium_idx)
        self.assertIn("Direct HTTP mode ready; Chromium not required.", source)
        self.assertIn("ready or not requires_browser", source)


class VimeoProfileTests(unittest.TestCase):
    def test_vimeo_profile_covers_public_video_pages(self):
        profile = _profile("Vimeo")

        self.assertEqual(
            _kw(profile, "start_url"),
            "https://vimeo.com/channels/freestockfootage",
        )
        self.assertEqual(
            _kw(profile, "video_types"),
            ["m3u8", "mp4", "webm", "mpd"],
        )
        self.assertIn("player.vimeo.com", _kw(profile, "domains"))

        item_re = re.compile(_kw(profile, "item_url_regex"))
        self.assertRegex("https://vimeo.com/123456789", item_re)
        self.assertRegex(
            "https://vimeo.com/channels/freestockfootage/123456789",
            item_re,
        )
        self.assertRegex(
            "https://vimeo.com/groups/freehd/videos/123456789",
            item_re,
        )
        self.assertRegex("https://player.vimeo.com/video/123456789", item_re)
        self.assertIsNone(item_re.search("https://vimeo.com/pricing"))

    def test_vimeo_catalog_extractor_keeps_hls_and_progressive_targets(self):
        profile = _profile("Vimeo")
        extractor_js = _kw(profile, "catalog_card_js")

        self.assertIn(r"vimeo\.com", extractor_js)
        self.assertIn(r"player\.vimeo\.com", extractor_js)
        self.assertIn("clip_id", extractor_js)
        self.assertIn("source_url", extractor_js)


class AdobeStockProfileTests(unittest.TestCase):
    def test_adobe_stock_profile_covers_asset_pages(self):
        profile = _profile("Adobe Stock")

        self.assertEqual(_kw(profile, "start_url"), "https://stock.adobe.com/video")
        self.assertEqual(
            _kw(profile, "video_types"),
            ["mp4", "webm", "m3u8", "mpd"],
        )
        self.assertIn("stock.adobe.com", _kw(profile, "domains"))

        item_re = re.compile(_kw(profile, "item_url_regex"))
        self.assertRegex(
            "https://stock.adobe.com/video/sample-stock-clip/123456789",
            item_re,
        )
        self.assertRegex(
            "https://stock.adobe.com/fr/video/sample-stock-clip/123456789",
            item_re,
        )
        self.assertRegex(
            "https://stock.adobe.com/search/video?k=office&asset_id=123456789",
            item_re,
        )
        self.assertIsNone(item_re.search("https://stock.adobe.com/photos/sample/123456789"))

    def test_adobe_catalog_extractor_records_watermarked_preview_metadata(self):
        profile = _profile("Adobe Stock")
        extractor_js = _kw(profile, "catalog_card_js")

        self.assertIn(r"stock\.adobe\.com", extractor_js)
        self.assertIn("asset_id", extractor_js)
        self.assertIn("Watermarked preview", extractor_js)
        self.assertIn("source_url", extractor_js)


class PreviewMarketplaceProfileTests(unittest.TestCase):
    def test_shutterstock_profile_covers_video_clip_pages(self):
        profile = _profile("Shutterstock")
        item_re = re.compile(_kw(profile, "item_url_regex"))
        id_re = re.compile(_kw(profile, "clip_id_regex"))

        url = "https://www.shutterstock.com/video/clip-1105380147-aerial-city"
        self.assertEqual(_kw(profile, "start_url"), "https://www.shutterstock.com/video")
        self.assertRegex(url, item_re)
        self.assertEqual(id_re.search(url).group(1), "1105380147")
        self.assertEqual(_kw(profile, "video_types"), ["mp4", "webm", "m3u8", "mpd"])
        self.assertIn("Preview", _kw(profile, "catalog_card_js"))

    def test_envato_elements_profile_covers_stock_video_items(self):
        profile = _profile("Envato Elements")
        item_re = re.compile(_kw(profile, "item_url_regex"), re.IGNORECASE)
        id_re = re.compile(_kw(profile, "clip_id_regex"), re.IGNORECASE)

        url = "https://elements.envato.com/clean-video-opener-AB12CD3"
        self.assertEqual(_kw(profile, "start_url"), "https://elements.envato.com/stock-video")
        self.assertRegex(url, item_re)
        self.assertEqual(id_re.search(url).group(1), "AB12CD3")
        self.assertIn("/stock-video", _kw(profile, "catalog_patterns"))
        self.assertIn("Preview", _kw(profile, "catalog_card_js"))

    def test_motion_array_profile_covers_stock_video_items(self):
        profile = _profile("Motion Array")
        item_re = re.compile(_kw(profile, "item_url_regex"))
        id_re = re.compile(_kw(profile, "clip_id_regex"))

        url = "https://motionarray.com/stock-video/drone-coastline-123456/"
        self.assertEqual(_kw(profile, "start_url"), "https://motionarray.com/stock-video/")
        self.assertRegex(url, item_re)
        self.assertEqual(id_re.search(url).group(1), "123456")
        self.assertIn("/stock-video", _kw(profile, "catalog_patterns"))
        self.assertIn("Preview", _kw(profile, "catalog_card_js"))


if __name__ == "__main__":
    unittest.main()
