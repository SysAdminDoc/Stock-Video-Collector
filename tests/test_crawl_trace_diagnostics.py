import asyncio
import json
import tempfile
import unittest
from pathlib import Path

import artlist_scraper as app


class _FakeTracing:
    def __init__(self):
        self.started = False
        self.stopped_paths = []

    async def start(self, **_kwargs):
        self.started = True

    async def stop(self, path=None):
        self.stopped_paths.append(path)
        if path:
            Path(path).write_bytes(b"trace")


class _FakeContext:
    def __init__(self):
        self.tracing = _FakeTracing()


class _FakePage:
    def __init__(self):
        self.context = _FakeContext()
        self.handlers = {}

    def on(self, event, handler):
        self.handlers[event] = handler

    def remove_listener(self, event, handler):
        if self.handlers.get(event) is handler:
            del self.handlers[event]

    async def content(self):
        return (
            '<html><body>'
            '<a href="https://example.test/video?token=secret-value">clip</a>'
            '<video src="https://videos.pexels.com/video-files/123/123-hd.mp4?api_key=secret">'
            '</video></body></html>'
        )

    async def screenshot(self, path, full_page=True):
        Path(path).write_bytes(b"png")


class CrawlTraceDiagnosticsTests(unittest.TestCase):
    def test_bundle_names_are_stable_and_filesystem_safe(self):
        name = app._crawl_trace_bundle_name(
            "Pexels",
            "clip",
            "https://www.pexels.com/video/sample clip/?token=secret",
        )

        self.assertIn("Pexels-clip-www.pexels.com", name)
        self.assertNotIn("?", name)
        self.assertNotIn("/", name)

    def test_trace_bundle_writer_redacts_html_network_and_metadata(self):
        worker = app.CrawlerWorker(
            {"crawl_trace_on_failure": True},
            db=None,
            profile=app.SiteProfile.get("Pexels"),
        )
        page = _FakePage()
        state = asyncio.run(worker._start_trace_bundle(
            page.context,
            page,
            "https://www.pexels.com/video/sample?token=secret-value",
            2,
            "clip",
        ))
        self.assertTrue(page.context.tracing.started)

        original_trace_dir = app.get_crawl_trace_dir
        with tempfile.TemporaryDirectory() as tmp:
            trace_root = Path(tmp) / "traces"
            app.get_crawl_trace_dir = lambda: str(trace_root)
            try:
                asyncio.run(worker._finish_trace_bundle(
                    state,
                    failed=True,
                    reason="failed with api_key=secret-value",
                    clip_meta={"clip_id": "123", "auth_token": "secret-value"},
                ))

                candidates = sorted(trace_root.glob("*Pexels-clip-www.pexels.com*"))
                self.assertTrue(candidates)
                bundle = candidates[-1]
                metadata = json.loads((bundle / "metadata.json").read_text(encoding="utf-8"))
                html = (bundle / "snapshot.html").read_text(encoding="utf-8")
                network = json.loads((bundle / "network.har").read_text(encoding="utf-8"))

                self.assertTrue((bundle / "trace.zip").is_file())
                self.assertTrue((bundle / "screenshot.png").is_file())
                self.assertNotIn("secret-value", json.dumps(metadata))
                self.assertNotIn("secret-value", html)
                self.assertIn(app._REDACTED, html)
                self.assertEqual(metadata["profile"], "Pexels")
                self.assertIn("entries", network["log"])
            finally:
                app.get_crawl_trace_dir = original_trace_dir

    def test_replay_crawl_trace_bundle_extracts_snapshot_video_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            (bundle / "metadata.json").write_text(
                json.dumps({"profile": "Pexels", "url": "https://www.pexels.com/video/sample"}),
                encoding="utf-8",
            )
            (bundle / "snapshot.html").write_text(
                '<a href="https://www.pexels.com/video/sample-123/">clip</a>'
                '<video src="https://videos.pexels.com/video-files/123/123-hd.mp4"></video>',
                encoding="utf-8",
            )
            (bundle / "network.har").write_text(
                json.dumps({"log": {"entries": []}}),
                encoding="utf-8",
            )

            replay = app.replay_crawl_trace_bundle(bundle)

        self.assertEqual(replay["metadata"]["profile"], "Pexels")
        self.assertIn(
            "https://videos.pexels.com/video-files/123/123-hd.mp4",
            replay["video_urls"],
        )
        self.assertIn("https://www.pexels.com/video/sample-123/", replay["links"])


if __name__ == "__main__":
    unittest.main()
