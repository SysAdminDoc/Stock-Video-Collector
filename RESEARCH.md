# Research — Stock Video Collector

## Executive Summary
Verified: Stock Video Collector is a local-first Python/PyQt6 desktop app that crawls stock-video sites with Playwright or direct HTTP, catalogs clips in SQLite/FTS5, reviews them in a dark card library, downloads validated MP4s, and exports sidecar metadata. Its strongest current shape is the integrated private desktop workflow: marketplace profiles, backup-backed destructive recovery, atomic validated downloads, redacted secret vaulting, release verification, and passing local tests. Highest-value direction: harden trust and recovery boundaries before expanding breadth. Priorities, in order: shared URL safety for all fetches; Direct HTTP crawl availability without Chromium; legacy app-data path migration; OS-backed secret storage; release dependency audit/lock; visible controls instead of hidden shortcuts; database backup catalog; thumbnail failure retry diagnostics; embedded provenance/metadata round-trip; and portable config diagnostics.

## Product Map
- Core workflows: select stock-site profiles, crawl/search pages, extract clip metadata and video URLs, catalog in SQLite/FTS5, browse/search/filter/rate/tag, download MP4s with sidecar JSON, and export URL/metadata sets.
- User personas: solo video editor building a reusable footage library; marketer collecting B-roll; local archivist importing existing MP4 folders; power user bridging GUI curation with yt-dlp/gallery-dl-style tooling.
- Platforms and distribution: Python 3.9+, PyQt6 desktop on Windows/Linux/macOS, Playwright Chromium for browser modes, SQLite local database, PyInstaller EXE build script/spec.
- Key integrations and data flows: `SiteProfile` + `CrawlerWorker`/`DirectScrapeWorker` -> `DB.save_clip()` -> SQLite/FTS5; `DownloadWorker` + ffmpeg/ffprobe -> `.part` validation -> MP4 + JSON sidecar + thumbnail; import/export workers -> local folders, sidecars, TXT/JSON/M3U/CSV.

## Competitive Landscape
- yt-dlp: broad extractor coverage, cookies, output templates, network backend work, and active enhancement triage. Learn extractor-contract discipline, runtime warnings, and URL handoff; avoid becoming CLI-only because this repo's value is visual library curation.
- gallery-dl: strong per-site extractor/config/archive model. Learn modular adapters, archive idempotency, and fixture-friendly extraction; avoid copying image-first assumptions that under-serve video metadata.
- Streamlink / Media Downloader / Tartube / MeTube: mature stream/downloader frontends with presets, queues, cookies, retry, and user-visible status. Learn queue ergonomics and engine abstraction; avoid remote-server complexity and GPL/AGPL code reuse conflicts.
- Eagle / Adobe Bridge / Lightroom-style workflows: dense visual grids, labels/ratings, smart folders, batch metadata, and duplicate review are table stakes for media-library users. Learn curation ergonomics and metadata discipline; avoid creative-suite coupling.
- PhotoPrism / Immich / Hydrus: long-running indexing, duplicate relations, perceptual search, thumbnail/transcode failure handling, and recovery surfaces are recurring product needs. Learn background job state and retry design; avoid server-first or multi-user architecture until local reliability is complete.
- Pexels / Pixabay / Vimeo / Adobe Stock APIs: official APIs improve metadata, license provenance, and crawl stability where keys are available. Learn API-first adapters, quota/backoff, and attribution fields; avoid plaintext credential storage and invisible quota failures.

## Security, Privacy, and Reliability
- Verified: app-initiated fetch paths still need a shared private-network/unsafe-scheme policy. `DirectScrapeWorker._http_get()`, thumbnail fetches, and `DownloadWorker._head_check_url()` call `urllib.request.urlopen()` on harvested URLs (`artlist_scraper.py:3627`, `artlist_scraper.py:4247`, `artlist_scraper.py:6665`); OWASP SSRF guidance applies.
- Verified: Direct HTTP mode is blocked unnecessarily when Chromium is missing. `_check_browser_status()` disables Start globally, while `_start_crawl()` has a `direct_http` branch that does not need Playwright (`artlist_scraper.py:9073`, `artlist_scraper.py:9127`).
- Verified: persisted paths still use the old `ArtlistScraper` name for config, thumbnails, output defaults, and fallback export locations (`artlist_scraper.py:1584`, `artlist_scraper.py:3571`, `artlist_scraper.py:7547`, `artlist_scraper.py:9514`, `artlist_scraper.py:9621`).
- Verified: the v0.7.8 vault removes sensitive values from plaintext config, but it uses a local key file beside app config rather than OS credential storage (`artlist_scraper.py:1599`). Official API, proxy, and cookie work will increase secret value.
- Verified: hidden `QShortcut` bindings remain for search, refresh, tabs, zoom, select-all, and escape (`artlist_scraper.py:7169`), while current project instructions require visible controls instead of keyboard shortcuts.
- Verified: database clear now backs up and restores the latest backup, but recovery has no backup catalog, checksum validation, retention setting, or selected-restore UI (`artlist_scraper.py:863`, `artlist_scraper.py:881`, `artlist_scraper.py:10167`, `artlist_scraper.py:10215`).
- Verified: thumbnail failures are mostly invisible. `_download_thumb_url()` swallows failures, and thumbnail generation/fetch paths do not persist failure reason, retry count, or a repair filter (`artlist_scraper.py:3621`, `artlist_scraper.py:6037`).
- Likely: dependency reproducibility is fragile because `requirements.txt` permits broad major ranges, local Playwright is one minor behind latest, and `tools/build_release.py --verify-only` does not run an audit or lock/record resolved versions.

## Architecture Assessment
- Verified: `artlist_scraper.py` remains the dominant boundary, mixing config, vault, DB schema, site profiles, crawler workers, download workers, import/export workers, and GUI construction. The existing extractor-module roadmap item is still the root refactor.
- Verified: the local suite covers release hygiene, secret redaction, download integrity, database backup/restore, and static profiles; `python -m unittest discover -s tests` passed with 24 tests. Missing tests now map to network safety, mode availability, path migration, keyring migration, backup catalog behavior, thumbnail retry state, embedded metadata round-trip, and visible-control reachability.
- Verified: the PyInstaller spec and `tools/build_release.py` include a runtime freeze hook and artifact hash output, but the spec is ignored by pattern and release verification does not audit dependencies or emit a persisted release manifest.
- Verified: JSON sidecars exist (`DownloadWorker._write_sidecar()`), and local imports use ffprobe for basic technical metadata (`ImportWorker._probe()`), but there is no IPTC/XMP/C2PA-style embedded rights/provenance import or export round-trip.
- Verified: existing roadmap items already cover official API connectors, extractor modules, crawl trace/replay diagnostics, license/provenance DB fields, accessibility, expanded tests, duplicate detection, and handoff packages; new items should extend those, not duplicate them.
- Verified: security, accessibility, observability, testing, docs, distribution/packaging, plugin/API architecture, offline recovery, migration paths, and upgrade strategy are represented by existing or new roadmap items. Mobile, multi-user, and i18n/l10n are intentionally rejected for now.

## Rejected Ideas
- Mobile companion app — source: Immich/PhotoPrism. Reason: mobile sync/upload does not strengthen the current desktop crawl/download/library workflow.
- Multi-user/team DAM — source: PhotoPrism/Immich and commercial DAM patterns. Reason: accounts, ACLs, sharing, and server operations would distract from local reliability.
- Cloud sync first — source: commercial DAM and self-hosted media patterns. Reason: backup/export/portable recovery should land before sync.
- Residential proxy marketplace integration — source: downloader networking issue patterns. Reason: high abuse, support, and ToS risk; user-supplied proxy settings plus rate-limit/robots handling are safer.
- Built-in NLE/editor — source: Bridge/Lightroom/Resolve-adjacent workflows. Reason: export/handoff to editors fits better than editing media inside the crawler.
- Watermark-removal expansion — source: stock-media licensing workflows. Reason: keep any existing tooling limited to the user's own uploaded clips; do not make marketplace preview bypass a product direction.
- GitHub Actions, Dependabot, or Renovate — source: project instructions. Reason: this repo requires local builds/tests and manual dependency updates.
- i18n/l10n now — source: local repo inspection. Reason: no non-English demand signal; accessibility, visible controls, and stable settings are higher leverage first.

## Sources
Direct OSS and adjacent:
- https://github.com/yt-dlp/yt-dlp
- https://github.com/mikf/gallery-dl
- https://github.com/streamlink/streamlink
- https://github.com/alexta69/metube
- https://github.com/mhogomchungu/media-downloader
- https://github.com/axcore/tartube
- https://github.com/hydrusnetwork/hydrus
- https://github.com/photoprism/photoprism
- https://github.com/immich-app/immich
- https://github.com/Breakthrough/PySceneDetect
- https://github.com/mlfoundations/open_clip
- https://github.com/facebookresearch/faiss

Awesome lists and community:
- https://github.com/awesome-selfhosted/awesome-selfhosted
- https://github.com/antonio-orionus/awesome-video-downloaders

Commercial and product references:
- https://en.eagle.cool/
- https://www.adobe.com/products/bridge.html
- https://jdownloader.org/

APIs, standards, security, dependencies:
- https://www.pexels.com/api/documentation/
- https://pixabay.com/api/docs/
- https://developer.vimeo.com/api/reference/videos
- https://developer.adobe.com/stock/docs/api/
- https://c2pa.org/specifications/
- https://iptc.org/standards/video-metadata-hub/
- https://www.rfc-editor.org/rfc/rfc9309.html
- https://owasp.org/www-community/attacks/Server_Side_Request_Forgery
- https://pypi.org/project/keyring/
- https://pypi.org/project/pip-audit/
- https://playwright.dev/python/docs/release-notes
- https://pypi.org/project/PyQt6/
- https://pypi.org/project/imageio-ffmpeg/

## Open Questions
None.
