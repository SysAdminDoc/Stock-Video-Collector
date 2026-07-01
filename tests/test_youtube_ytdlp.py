import re
import unittest

import artlist_scraper as app


class YouTubeYtDlpTests(unittest.TestCase):
    def test_youtube_profile_registered_and_contracts(self):
        profile = app.SiteProfile.get("YouTube CC-BY")

        self.assertIsNotNone(profile)
        self.assertEqual(
            profile.start_url,
            "https://www.youtube.com/results?search_query=creative+commons+stock+footage",
        )
        self.assertFalse(profile.is_catalog("https://www.youtube.com/feed/history"))
        self.assertTrue(profile.is_item("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertEqual(
            profile.extract_clip_id("https://youtu.be/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )
        self.assertTrue(
            profile.accepts_video_url(
                "https://rr1---sn.example.googlevideo.com/videoplayback/sample.mp4"
            )
        )
        self.assertFalse(profile.accepts_video_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))

    def test_ytdlp_cc_entry_maps_to_clip(self):
        clip = app.YtDlpIngestWorker._entry_to_clip(
            {
                "id": "abc123XYZ",
                "title": "CC Stock Clip",
                "uploader": "Creator Name",
                "playlist_title": "Reusable B-Roll",
                "license": "Creative Commons Attribution license (reuse allowed)",
                "license_url": "https://support.google.com/youtube/answer/2797468",
                "duration": 125,
                "width": 1920,
                "height": 1080,
                "fps": 29.97,
                "ext": "mp4",
                "webpage_url": "https://www.youtube.com/watch?v=abc123XYZ",
                "thumbnails": [
                    {"url": "https://i.ytimg.com/small.jpg", "width": 120, "height": 90},
                    {"url": "https://i.ytimg.com/large.jpg", "width": 1280, "height": 720},
                ],
                "tags": ["stock", "b-roll", "city"],
            }
        )

        self.assertEqual(clip["clip_id"], "youtube_abc123XYZ")
        self.assertEqual(clip["source_site"], "YouTube CC-BY")
        self.assertEqual(clip["resolution"], "1920x1080")
        self.assertEqual(clip["duration"], "2:05")
        self.assertEqual(clip["formats"], "MP4")
        self.assertEqual(clip["thumbnail_url"], "https://i.ytimg.com/large.jpg")
        self.assertEqual(clip["license_name"], "Creative Commons Attribution license (reuse allowed)")
        self.assertEqual(clip["attribution_required"], "Yes")
        self.assertEqual(clip["preview_status"], "yt-dlp metadata ingest")

    def test_ytdlp_non_cc_entry_is_skipped(self):
        self.assertIsNone(
            app.YtDlpIngestWorker._entry_to_clip(
                {
                    "id": "standard123",
                    "title": "Standard License Clip",
                    "license": "Standard YouTube License",
                }
            )
        )

    def test_ytdlp_command_is_metadata_only(self):
        cmd = app.YtDlpIngestWorker({}, None)._command("https://youtu.be/dQw4w9WgXcQ", 5)
        joined = " ".join(cmd)

        self.assertRegex(cmd[0], re.compile(r"yt-dlp(?:\.exe)?$", re.IGNORECASE))
        self.assertIn("--dump-json", cmd)
        self.assertIn("--skip-download", cmd)
        self.assertIn("--playlist-end 5", joined)


if __name__ == "__main__":
    unittest.main()
