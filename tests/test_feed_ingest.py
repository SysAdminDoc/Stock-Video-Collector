import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import artlist_scraper as app  # noqa: E402


class FeedIngestParserTests(unittest.TestCase):
    def test_rss_video_enclosure_maps_to_clip(self):
        payload = b"""<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0"
             xmlns:media="http://search.yahoo.com/mrss/"
             xmlns:dc="http://purl.org/dc/elements/1.1/"
             xmlns:cc="http://creativecommons.org/ns#">
          <channel>
            <title>Drone B-Roll Feed</title>
            <item>
              <title>Mountain drone flyover</title>
              <link>https://example.com/posts/mountain-drone</link>
              <description>Alpine b-roll sample.</description>
              <dc:creator>Example Creator</dc:creator>
              <category>drone</category>
              <media:keywords>mountain, aerial</media:keywords>
              <media:thumbnail url="https://cdn.example.com/thumbs/mountain.jpg" />
              <media:content url="https://cdn.example.com/video/mountain-4k.mp4"
                             type="video/mp4" duration="125" width="3840" height="2160" />
              <cc:license>https://creativecommons.org/licenses/by/4.0/</cc:license>
            </item>
          </channel>
        </rss>"""

        clips = app.FeedIngestWorker._parse_feed_items(payload, "https://example.com/feed.xml")

        self.assertEqual(len(clips), 1)
        clip = clips[0]
        self.assertTrue(clip["clip_id"].startswith("feed_"))
        self.assertEqual(clip["source_site"], "RSS/Atom Feed")
        self.assertEqual(clip["source_url"], "https://example.com/posts/mountain-drone")
        self.assertEqual(clip["m3u8_url"], "https://cdn.example.com/video/mountain-4k.mp4")
        self.assertEqual(clip["collection"], "Drone B-Roll Feed")
        self.assertEqual(clip["creator"], "Example Creator")
        self.assertEqual(clip["duration"], "2:05")
        self.assertEqual(clip["resolution"], "3840x2160")
        self.assertEqual(clip["formats"], "MP4")
        self.assertEqual(clip["thumbnail_url"], "https://cdn.example.com/thumbs/mountain.jpg")
        self.assertIn("drone", clip["tags"])
        self.assertEqual(clip["license_url"], "https://creativecommons.org/licenses/by/4.0/")
        self.assertEqual(clip["preview_status"], "Feed enclosure")

    def test_atom_enclosure_link_maps_to_clip(self):
        payload = b"""<?xml version="1.0" encoding="utf-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
          <title>Studio Clip Feed</title>
          <entry>
            <title>Studio lights</title>
            <author><name>Studio Team</name></author>
            <link rel="alternate" href="https://example.com/clips/studio-lights" />
            <link rel="enclosure" type="application/vnd.apple.mpegurl"
                  href="https://cdn.example.com/video/studio/master.m3u8" />
            <media:thumbnail url="https://cdn.example.com/thumbs/studio.jpg" />
            <category term="studio" />
          </entry>
        </feed>"""

        clips = app.FeedIngestWorker._parse_feed_items(payload, "https://example.com/atom.xml")

        self.assertEqual(len(clips), 1)
        clip = clips[0]
        self.assertEqual(clip["title"], "Studio lights")
        self.assertEqual(clip["creator"], "Studio Team")
        self.assertEqual(clip["source_url"], "https://example.com/clips/studio-lights")
        self.assertEqual(clip["m3u8_url"], "https://cdn.example.com/video/studio/master.m3u8")
        self.assertEqual(clip["formats"], "M3U8")
        self.assertEqual(clip["collection"], "Studio Clip Feed")
        self.assertEqual(clip["thumbnail_url"], "https://cdn.example.com/thumbs/studio.jpg")
        self.assertEqual(clip["tags"], "studio")

    def test_non_video_feed_items_are_ignored(self):
        payload = b"""<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0">
          <channel>
            <title>Text Feed</title>
            <item>
              <title>Article only</title>
              <link>https://example.com/article</link>
              <enclosure url="https://cdn.example.com/article.pdf" type="application/pdf" />
            </item>
          </channel>
        </rss>"""

        self.assertEqual(
            app.FeedIngestWorker._parse_feed_items(payload, "https://example.com/feed.xml"),
            [],
        )

    def test_worker_run_fetches_and_saves_feed_clip(self):
        payload = b"""<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0">
          <channel>
            <title>Run Feed</title>
            <item>
              <title>Runnable clip</title>
              <link>https://example.com/runnable</link>
              <enclosure url="https://cdn.example.com/runnable.mp4" type="video/mp4" />
            </item>
          </channel>
        </rss>"""

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit):
                return payload

        class FakeDB:
            def __init__(self):
                self.saved = []

            def save_clip(self, clip):
                self.saved.append(clip)
                return True

            def update_metadata(self, *_args):
                raise AssertionError("new feed clip should not update")

            def stats(self):
                return {"clips": len(self.saved)}

        db = FakeDB()
        worker = app.FeedIngestWorker({"start_url": "https://example.com/feed.xml", "batch_size": 5}, db)

        with patch.object(app, "_safe_urlopen", return_value=FakeResponse()):
            worker.run()

        self.assertEqual(len(db.saved), 1)
        self.assertEqual(db.saved[0]["title"], "Runnable clip")
        self.assertEqual(db.saved[0]["m3u8_url"], "https://cdn.example.com/runnable.mp4")


if __name__ == "__main__":
    unittest.main()
