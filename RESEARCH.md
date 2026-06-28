# Research - Stock Video Collector

## Executive Summary
Stock Video Collector is a PyQt6 + Playwright desktop crawler that already combines stock-site discovery, SQLite/FTS cataloging, card-based review, and ffmpeg downloads in one local app. Verified highest-value direction: make the existing power-user workflow trustworthy and repeatable before adding more profiles. Priorities: release/version hygiene, atomic downloads with validation, official API connectors for sites that provide them, credential/privacy hardening, extractor modularity, crawl politeness/traceability, richer license provenance, accessibility, and downloader/database test coverage.

## Product Map
- Core workflows: crawl stock catalogs, capture preview/video URLs, enrich metadata, search/filter/rate/tag clips, download MP4 sidecars, export URL/metadata files.
- User personas: solo video editor building a stock-footage library; marketer collecting reusable clips; power user bridging GUI curation with CLI downloaders; local archivist importing existing MP4 folders.
- Platforms and distribution: Python 3.9+, PyQt6 desktop on Windows/Linux/macOS, Playwright Chromium, SQLite database under the app config directory, PyInstaller documented but no tracked spec or release artifact workflow.
- Key integrations and data flows: Playwright network/DOM capture -> `DB.save_clip()` -> SQLite + FTS5; ffmpeg/imageio-ffmpeg -> MP4 + thumbnail + sidecar JSON; `ffprobe` local import -> catalog rows; TXT/JSON/M3U/CSV exports.

## Competitive Landscape
- yt-dlp: strongest extractor breadth and breakage response. Learn from its extractor/test separation and URL handoff model; avoid becoming CLI-only or hiding library curation behind flags.
- gallery-dl: strong site-extractor architecture, archive database, per-site config, and skip/retry behavior. Learn the plugin contract and archive idempotency; avoid copying its image-first UX.
- Streamlink: good at stream URL resolution and player handoff. Learn protocol-specific stream abstraction; avoid optimizing only for live-stream workflows.
- JDownloader: mature link-grabber, CAPTCHA/manual intervention, package grouping, retry, and archive extraction. Learn queue ergonomics and recovery states; avoid bundled adware-style distribution patterns.
- Eagle/Billfish: best fit for visual library UX: smart folders, duplicate finding, batch tags, color labels, dense media grids. Learn curation workflow; avoid cloud/team assumptions that conflict with local-first use.
- Adobe Bridge/Lightroom Classic: metadata, ratings, labels, smart collections, batch rename, and non-destructive organization are table stakes for media pros. Learn provenance/metadata discipline; avoid heavyweight creative-suite coupling.
- PhotoPrism/Immich/Hydrus: show how local media libraries handle perceptual search, duplicates, bulk tags, and long-running indexing. Learn background job boundaries; avoid server-first or multi-user complexity until local reliability is stronger.
- Pexels/Pixabay/Vimeo/Adobe Stock APIs: official APIs can reduce scraping fragility. Learn API-first adapters and quota-aware pagination; avoid storing API keys or session tokens in plaintext config/logs.

## Security, Privacy, and Reliability
- Verified: `get_config_dir()` still stores under `ArtlistScraper`, while app/docs are Stock Video Collector (`artlist_scraper.py`). This creates migration/support confusion.
- Verified: `load_config()`/`save_config()` write plaintext JSON and future API keys/proxy credentials would land beside browser/session settings (`artlist_scraper.py`).
- Verified: `_http_get()` and thumbnail fetchers use unrestricted URLs from crawled pages without a host allowlist beyond profile logic, so diagnostics and future import paths need SSRF-style localhost/private-network rejection (`artlist_scraper.py`).
- Verified: `_download_one()` writes directly to the final output path and only removes zero-byte failed files; gallery-dl/yt-dlp style `.part` atomic writes plus post-download `ffprobe` validation would reduce corrupt-library risk.
- Verified: destructive database clearing still uses a modal confirmation (`artlist_scraper.py`), while the target UI rule is backup/undo with toast/status feedback instead of confirmation dialogs.
- Verified: release/version strings are inconsistent: README and window header say v0.7.4, but the source header lists internal notes through v1.1.0. This blocks reliable release planning.
- Likely: Playwright trace/HAR capture, per-site crawl summaries, and redacted diagnostic bundles would make broken selectors/profile drift actionable without rerunning broad crawls.

## Architecture Assessment
- `artlist_scraper.py` is about 9,800 lines and mixes bootstrap, themes, database schema/migrations, site profiles, crawl workers, download workers, importers, and GUI construction. Split first around stable boundaries: `profiles/`, `crawler/`, `downloads/`, `storage/`, and `ui/`.
- Built-in `SiteProfile.register()` blocks are testable by AST only today. Convert them into importable extractor modules with contract tests for URL matching, catalog-card extraction fixtures, and video URL filtering.
- Tests currently cover compile plus static profile patterns only (`tests/test_static_profiles.py`). Missing: DB migration/FTS recovery tests, download worker tests with fake ffmpeg/HTTP, export tests, local import tests, and GUI smoke tests.
- Official API adapters should be implemented as optional connectors, not replacements for browser capture: Pexels/Pixabay API modes can fill metadata and quota-aware pagination; Playwright remains useful for logged-in or preview-only marketplaces.
- Data model should add provenance fields before more exports: license, attribution, source terms URL, preview/watermark flag, API/scrape source, capture method, and retrieved-at timestamp.
- Distribution needs a tracked build script/spec and stale artifact cleanup before release. `dist/` exists locally but is ignored and not tied to a repeatable release process.

## Rejected Ideas
- Mobile app: Immich/PhotoPrism show mobile value, but this project's current value is desktop crawling/downloading and local library curation.
- Multi-user/team DAM: Daminion-style permissions and server catalogs add high maintenance before the local workflow is trustworthy.
- Residential proxy marketplace integration: common in scraper tools, but high ToS, privacy, and support risk; user-supplied proxy settings already cover the safer path.
- Built-in NLE/editor: trimming/transcode presets are useful, but full editing competes with DaVinci Resolve/OpenCut rather than strengthening collection/download reliability.
- Watermark removal workflows: high legal/reputation risk even with "own uploads" wording; keep provenance and license clarity instead.
- Cloud sync as a first-class service: SQLite replication/Litestream is already on the roadmap, but local backup/export and corruption recovery should land first.

## Sources
Direct OSS:
- https://github.com/yt-dlp/yt-dlp
- https://github.com/mikf/gallery-dl
- https://github.com/streamlink/streamlink
- https://github.com/alexta69/metube
- https://github.com/axcore/tartube
- https://github.com/hydrusnetwork/hydrus
- https://github.com/photoprism/photoprism
- https://github.com/immich-app/immich
- https://github.com/Breakthrough/PySceneDetect
- https://github.com/facebookresearch/faiss
- https://github.com/mlfoundations/open_clip
- https://github.com/facebook/ThreatExchange

Commercial / Product:
- https://en.eagle.cool/
- https://www.billfishapp.com/
- https://www.adobe.com/products/bridge.html
- https://helpx.adobe.com/lightroom-classic/help/metadata-basics-actions.html
- https://www.blackmagicdesign.com/products/davinciresolve
- https://jdownloader.org/
- https://www.4kdownload.com/products/videodownloader-42

APIs / Standards / Dependencies:
- https://www.pexels.com/api/documentation/
- https://pixabay.com/api/docs/
- https://developer.vimeo.com/api/reference/videos
- https://developer.adobe.com/stock/docs/api/
- https://playwright.dev/python/docs/release-notes
- https://www.riverbankcomputing.com/static/Docs/PyQt6/
- https://www.sqlite.org/fts5.html
- https://pypi.org/project/pip-audit/
- https://osv.dev/

## Open Questions
- Which official API keys will be available for live validation: Pexels, Pixabay, Vimeo, Adobe Stock, or none?
- Should the app migrate config/database paths from `ArtlistScraper` to `StockVideoCollector` with automatic legacy import, or keep the old path for compatibility?
