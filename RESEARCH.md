# Research — Stock Video Collector

## Executive Summary
Verified: Stock Video Collector is a local-first PyQt6 desktop app for crawling stock-video sources, cataloging clips in SQLite/FTS5, reviewing them in a card library, and downloading/exporting media with sidecar metadata. Its strongest current shape is the integrated local workflow: marketplace profiles, browser/direct crawling, backup-backed destructive recovery, atomic validated downloads, and a redacted secret vault are already present. Highest-value direction: make crawl/download behavior safer, more reproducible, and easier to support before adding more sites. Top opportunities: block unsafe app-initiated URL fetches; keep Direct HTTP usable when Chromium is missing; migrate the legacy `ArtlistScraper` config path; move secrets to OS-backed storage; add release dependency/audit gates; remove hidden keyboard shortcuts in favor of visible controls; add a backup browser with checksums/retention; and then continue the existing extractor/API/provenance/accessibility/testing roadmap.

## Product Map
- Core workflows: crawl marketplace/search pages, extract preview/video metadata, catalog clips, search/filter/rate/tag, download MP4s with sidecars, export selected URLs/metadata.
- User personas: solo editor building a stock-footage library; marketer collecting reusable B-roll; power user bridging GUI curation with CLI downloaders; local archivist importing existing clips.
- Platforms and distribution: Python 3.9+ desktop app, PyQt6, Playwright Chromium, SQLite under the app config directory, local PyInstaller release workflow.
- Key integrations and data flows: `SiteProfile`/crawler workers -> `DB.save_clip()` -> SQLite + FTS5; download workers -> validated final media + sidecar JSON; import/export workers -> local MP4 metadata, CSV/JSON/M3U/TXT outputs.

## Competitive Landscape
- yt-dlp: broad extractor coverage, plugin hooks, cookies, output templates, and active breakage response. Learn extractor contract discipline and URL handoff; avoid becoming CLI-only because this repo's value is GUI curation.
- gallery-dl: strong per-site extractor/config/archive model and idempotent skip behavior. Learn modular site adapters and replayable fixtures; avoid image-first assumptions that under-serve video metadata.
- Streamlink: clean plugin boundary for resolving streams from many services. Learn protocol abstraction and stream-quality selection; avoid optimizing mainly for live-player handoff.
- MeTube / Media Downloader: practical desktop/web frontends around yt-dlp, gallery-dl, aria2, and presets. Learn queue controls, cookies handling, and user-visible downloader state; avoid remote-server complexity for this local app.
- Eagle / Adobe Bridge / Lightroom Classic: mature visual-library patterns: dense grids, ratings, labels, smart folders, duplicate review, batch metadata. Learn curation ergonomics and provenance rigor; avoid creative-suite coupling.
- PhotoPrism / Immich / Hydrus: long-running indexing, duplicate handling, tagging, perceptual search, and recovery patterns. Learn background-job boundaries and duplicate workflows; avoid server-first multi-user architecture before local reliability is finished.
- Pexels / Pixabay / Vimeo / Adobe Stock APIs: official APIs reduce scraping fragility and improve metadata completeness. Learn API-first adapters, quota/backoff, and license fields; avoid storing API keys or session tokens in plaintext or logs.

## Security, Privacy, and Reliability
- Verified: app-initiated URL fetch paths use harvested URLs without a shared private-network/unsafe-scheme policy, including `DirectScrapeWorker._http_get()` and `DownloadWorker._head_check_url()` (`artlist_scraper.py:4239`, `artlist_scraper.py:6658`). OWASP SSRF guidance applies to any import/fetch feature that can reach localhost, RFC1918, link-local, or metadata endpoints.
- Verified: Direct HTTP mode is unnecessarily blocked when Playwright Chromium is missing: `_check_browser_status()` disables Start globally, but `_start_crawl()` has a `direct_http` branch that does not need a browser (`artlist_scraper.py:9073`, `artlist_scraper.py:9123`).
- Verified: product naming and persisted data paths diverge. `get_config_dir()` still writes under `ArtlistScraper`, and the default database is stored there while README/UX identify the app as Stock Video Collector (`artlist_scraper.py:1584`, `artlist_scraper.py:7116`, `README.md`).
- Verified: v0.7.8 no longer stores sensitive values directly in JSON, but the vault uses a local key file beside app config rather than OS credential storage (`artlist_scraper.py:1599`). Official API/proxy/session work will increase the value of those secrets.
- Verified: hidden `QShortcut` bindings exist for search, refresh, tabs, zoom, select-all, and escape (`artlist_scraper.py:7169`). This conflicts with the current project instruction to expose visible controls instead of keyboard shortcuts.
- Verified: current recovery restores only the latest pre-clear backup. `backup_to()`, `restore_from()`, `_find_latest_db_backup()`, and `_restore_latest_db_backup()` provide a good base, but there is no backup catalog, checksum validation, or retention UI (`artlist_scraper.py:863`, `artlist_scraper.py:881`, `artlist_scraper.py:10167`, `artlist_scraper.py:10215`).
- Likely: dependency reproducibility is fragile because `requirements.txt` keeps broad ranges while local release verification relies on the current venv. A local lock/audit gate using `pip-audit` would harden releases without adding GitHub Actions.

## Architecture Assessment
- Verified: `artlist_scraper.py` is still the dominant boundary, mixing config, vault, database, profiles, crawler workers, download workers, imports, exports, and GUI. The existing roadmap item to split site profiles into extractor modules remains the right root refactor.
- Verified: tests now cover release hygiene, secret redaction, download integrity, database backup/restore, and static profiles, and `python -m unittest discover -s tests` passes locally. Remaining high-value gaps are network safety, mode availability, config migration, keyring migration, backup catalog behavior, and GUI control reachability.
- Verified: `tools/build_release.py --verify-only` passes and version strings are synchronized at v0.7.8, but release verification does not yet audit installed dependencies or record a deterministic dependency set.
- Verified: official API connector, provenance fields, crawl trace/replay, accessibility, expanded tests, duplicate detection, and handoff packages already exist in `ROADMAP.md`; new additions should support those rather than duplicate them.
- Likely: a shared URL policy helper should live below crawler/download/import code so Playwright, Direct HTTP, thumbnail fetches, and future API connectors cannot drift independently.
- Likely: config path migration should be reversible and compatibility-aware: copy or move legacy `ArtlistScraper` data to `StockVideoCollector`, keep fallback reads, and log what happened.
- Verified: security, observability, testing, distribution/upgrade, offline recovery, migration, accessibility, plugin/API architecture, and duplicate handling are represented by current or new roadmap items; mobile, multi-user, and i18n/l10n are intentionally rejected for now.

## Rejected Ideas
- Mobile companion app — source: Immich/PhotoPrism. Reason: mobile upload/viewer workflows do not help the current local desktop crawl/download core.
- Multi-user/team DAM — source: PhotoPrism/Immich and commercial DAM patterns. Reason: account, sync, ACL, and server operations would distract from local reliability.
- Cloud sync first — source: commercial DAM patterns. Reason: the repo's strongest fit is private local collection and offline operation.
- Residential proxy marketplace integration — source: downloader community/networking issue patterns. Reason: high abuse and maintenance risk; implement transparent rate limits, robots policy, and manual proxy config instead.
- Built-in NLE/editor — source: Bridge/Lightroom/Resolve-adjacent workflows. Reason: exports to editors fit better than editing media in the crawler.
- Watermark-removal expansion — source: stock-media licensing workflows. Reason: keep any existing tooling limited to the user's own uploaded clips; do not make bypassing marketplace previews a product direction.
- GitHub Actions, Dependabot, or Renovate — source: project instructions. Reason: this repo requires local builds/tests and manual dependency updates.
- i18n/l10n now — source: local repo inspection. Reason: no evidence of non-English demand; fix accessibility, visible controls, and stable settings first.

## Sources
Direct OSS and adjacent:
- https://github.com/yt-dlp/yt-dlp
- https://github.com/mikf/gallery-dl
- https://gdl-org.github.io/docs/configuration.html
- https://github.com/streamlink/streamlink
- https://github.com/alexta69/metube
- https://github.com/mhogomchungu/media-downloader
- https://github.com/hydrusnetwork/hydrus
- https://github.com/photoprism/photoprism
- https://github.com/immich-app/immich
- https://github.com/Breakthrough/PySceneDetect
- https://github.com/mlfoundations/open_clip
- https://github.com/facebookresearch/faiss

Commercial and product references:
- https://en.eagle.cool/
- https://www.adobe.com/products/bridge.html
- https://helpx.adobe.com/lightroom-classic/help/metadata-basics-actions.html
- https://jdownloader.org/
- https://www.4kdownload.com/products/videodownloader-42

APIs, standards, security, dependencies:
- https://www.pexels.com/api/documentation/
- https://pixabay.com/api/docs/
- https://developer.vimeo.com/api/reference/videos
- https://developer.adobe.com/stock/docs/api/
- https://www.rfc-editor.org/rfc/rfc9309.html
- https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-09.html
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Retry-After
- https://owasp.org/www-community/attacks/Server_Side_Request_Forgery
- https://pypi.org/project/keyring/
- https://pypi.org/project/pip-audit/
- https://playwright.dev/python/docs/release-notes
- https://pyinstaller.org/en/stable/CHANGES.html

## Open Questions
None.
