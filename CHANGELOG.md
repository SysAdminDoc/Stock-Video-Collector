# Changelog

All notable changes to Stock-Video-Collector will be documented in this file.

## [v0.7.29] - 2026-07-01

- Added: Optional Playwright persistent-context rotation across `browser_profiles/slot-N` directories.
- Added: Optional `proxies.txt` pool for Playwright browser launches, with parsed HTTP(S)/SOCKS proxy entries and redacted logging.

## [v0.7.28] - 2026-07-01

- Added: Browser-free RSS/Atom feed ingest mode for video enclosures and `media:content` entries, using the shared unsafe-URL protection before fetching feeds.
- Added: Feed parser tests for RSS, Atom, media thumbnails, license URLs, categories, duration/resolution mapping, and non-video item filtering.

## [v0.7.27] - 2026-07-01

- Added: Royalty-free site profiles for Coverr, Mazwai, Videvo, Mixkit, and Videezy, including current Mazwai/Videvo redirects into the Magnific/Freepik video catalog.
- Added: Profile contract coverage for the new route shapes, clip IDs, excluded paths, and video URL filters.

## [v0.7.26] - 2026-06-30

- Added: YouTube CC-BY site profile and browser-free `yt-dlp` ingest mode for Creative Commons metadata collections.
- Added: Deterministic yt-dlp normalization tests for CC filtering, license/provenance fields, thumbnails, duration, command shape, and crawl-mode browser gating.

## [v0.7.25] - 2026-06-30

- Added: Project handoff package export that writes a portable folder and ZIP with copied media, thumbnails, generated sidecars, `manifest.json`, `licenses/ATTRIBUTION.txt`, and `checksums.sha256`.
- Added: Filtered handoff package export for current search/collection results.

## [v0.7.24] - 2026-06-30

- Added: Portable mode via `--portable`, `STOCK_VIDEO_COLLECTOR_PORTABLE=1`, or an app-adjacent `portable.flag` sentinel, storing config, database, thumbnails, and default output under `portable-data`.
- Added: Config diagnostics in the GUI showing active mode, trigger, config path, output path, and portable sentinel path.

## [v0.7.23] - 2026-06-30

- Added: Embedded provenance extraction from ffprobe format/stream tags for local imports, including title, creator, rights, license URL, terms URL, attribution text, source, and raw tag JSON.
- Changed: Download sidecars and JSON/CSV exports now include a sidecar-only provenance schema and media-write policy so embedded rights metadata round-trips without modifying media files in place.

## [v0.7.22] - 2026-06-30

- Added: Thumbnail failure diagnostics with persisted reason/source/timestamp/retry count and a Library failed-thumbnail filter.
- Added: Retry/reset thumbnail actions for failed thumbnail jobs without reprocessing every healthy clip.

## [v0.7.21] - 2026-06-30

- Added: Database backup catalog with SHA-256, SQLite integrity status, selected restore, and retention pruning controls.
- Changed: Backup restore now verifies SQLite integrity before copying data into the active database.

## [v0.7.20] - 2026-06-30

- Added: Pinned `requirements-lock.txt` release environment with `pip-audit` as a local release-time dependency.
- Changed: Release verification now fails on dependency lock drift or vulnerability audit findings and writes local dependency snapshot/audit JSON.

## [v0.7.19] - 2026-06-30

- Added: Exact SHA-256 and optional ffmpeg visual-hash duplicate grouping for imported/downloaded clips.
- Added: Library duplicate-only filter, duplicate sort, detail-panel duplicate status, and context-menu keep/ignore/review actions.
- Changed: Sidecar JSON and CSV exports include duplicate fingerprint and review metadata.

## [v0.7.18] - 2026-06-30

- Added: Expanded local workflow tests for legacy DB migration with FTS rebuild, export file outputs, download preflight failures, and local import metadata persistence.

## [v0.7.17] - 2026-06-30

- Added: Optional official API connector layer for Pexels, Pixabay, Vimeo, and Adobe Stock, using configured keys before falling back to browser crawling.
- Added: Config UI fields for API search query, API page limits, and provider keys/tokens, persisted through existing secret storage.
- Added: API connector contract tests and crawler-level DB insertion coverage using fake API responses.

## [v0.7.16] - 2026-06-30

- Changed: Built-in site profile definitions now live in importable `profiles/` modules instead of the main GUI/crawler file.
- Added: Profile module contract fixtures and tests covering URL matching, clip ID extraction, registration, and video URL filters for every built-in profile.
- Added: `SiteProfile.accepts_video_url()` and `SiteProfile.extract_clip_id()` helpers for shared extractor contract behavior.

## [v0.7.15] - 2026-06-30

- Added: Accessible names/descriptions for major controls, status surfaces, media cards, toasts, and library selection controls.
- Changed: Media card download state is shown as a compact text badge instead of a color-only status dot.
- Changed: Hidden keyboard shortcut bindings and README shortcut docs were removed; Select Visible and Clear Selection are available as visible Search tab actions.
- Fixed: Select-all now targets the Search tab correctly.

## [v0.7.14] - 2026-06-30

- Added: Browser crawl failures now save redacted diagnostics bundles with Playwright trace, HTML snapshot, screenshot, metadata, and HAR-style network log.
- Added: Crawl trace replay helper for testing saved HTML snapshots without rerunning live crawls.
- Changed: Configure tab includes a visible "Save failed-crawl diagnostics" toggle, enabled by default and persisted in config.
- Fixed: Redaction now also scrubs standalone sensitive `key=value` fragments in exception strings while preserving safe query parameters.

## [v0.7.13] - 2026-06-30

- Added: Clip license/provenance columns for source license name, license URL, attribution requirement/text, terms URL, and preview/watermark status.
- Added: Built-in site profile defaults for known source license/terms pages, with explicit crawler/import metadata preserved when present.
- Changed: Detail panel, CSV exports, and download sidecar JSON now include license/provenance fields.
- Added: Provenance schema/default/export tests covering profile defaults and explicit-value preservation.

## [v0.7.12] - 2026-06-30

- Changed: Sensitive config values now store in the OS keyring when available, with the existing encrypted local vault as a logged fallback.
- Changed: Existing local vault entries migrate to keyring metadata when a usable keyring backend is available.
- Added: Keyring/fallback tests using a fake credential backend so local verification does not touch real OS credentials.

## [v0.7.11] - 2026-06-30

- Changed: App data now uses the `StockVideoCollector` config root, with startup migration that copies missing legacy `ArtlistScraper` config, vault, database, and backup files without overwriting current data.
- Changed: Default output and thumbnail-cache paths use the current product name.
- Added: Config path migration tests covering current directory selection, legacy copy-forward behavior, thumbnail cache, and default output paths.

## [v0.7.10] - 2026-06-30

- Fixed: Direct HTTP crawl mode stays startable when Playwright Chromium is missing, while browser-required crawl modes still show install guidance and remain blocked.
- Added: Static crawl-mode tests for the browser-free Direct HTTP path and mode-aware Chromium gate.

## [v0.7.9] - 2026-06-30

- Added: Shared URL safety policy for app-initiated crawler, thumbnail, GraphQL, direct HTTP, and download preflight fetches to block localhost, private/link-local networks, metadata services, non-HTTP(S) schemes, ambiguous IP literals, and redirect-to-private targets.
- Added: URL safety tests covering unsafe host rejection, sensitive-query redaction, DNS-to-private blocking, redirect blocking, and download HEAD preflight reporting.

## [v0.7.8] - 2026-06-28

- Added: Sensitive config values are migrated out of plaintext `config.json` into an encrypted local vault with `__secret_ref__` pointers.
- Added: Crash output, GUI logs, download logs, config import errors, and diagnostic strings redact tokens, cookies, auth headers, and sensitive query parameters.
- Added: Secret vault and redaction tests covering config migration, runtime hydration, and recursive diagnostic scrubbing.

## [v0.7.7] - 2026-06-28

- Added: Clear DB now creates a timestamped SQLite backup, clears immediately without a confirmation dialog, and exposes Restore Last Backup in-app.
- Added: Database backup/restore helpers using SQLite's online backup API, plus round-trip tests for clips and crawl queue restoration.

## [v0.7.6] - 2026-06-28

- Added: Downloader writes to `.part` files, validates completed videos, and atomically promotes only verified media to final MP4 paths.
- Added: Archive verification now flags invalid local video files, not just missing paths, and can reset missing/invalid records to pending.
- Added: Download integrity tests for partial paths, quarantine handling, video validation, and finalization ordering.

## [v0.7.5] - 2026-06-28

- Added: Reproducible release build script that cleans stale artifacts, verifies version sync, runs PyInstaller, and prints artifact hash metadata.
- Fixed: Centralized app version/title constants and restored PyInstaller freeze guard ordering before non-multiprocessing imports.
- Added: Release hygiene tests covering README, changelog, UI title wiring, and build-script metadata verification.

## [v0.7.4] - 2026-06-28

- Added: Shutterstock, Envato Elements, and Motion Array preview profiles with MP4/WebM/HLS/DASH capture.
- Added: Profile-specific clip ID extraction for marketplace URL patterns and static coverage tests.

## [v0.7.3] - 2026-06-28

- Added: Adobe Stock Video profile for public watermarked previews, asset-card extraction, and MP4/WebM/HLS/DASH capture.
- Added: Static tests for Adobe Stock asset URL detection and preview metadata extraction.

## [v0.7.2] - 2026-06-28

- Added: Vimeo public stock/CC profile with channel card extraction and HLS/MP4/WebM/DASH preview capture.
- Fixed: Restored Python parsing by repairing the PyQt6 GUI import block and removing a broken Windows console icon call.
- Added: Standard requirements file, source-level syntax/profile tests, and a PyInstaller runtime freeze guard.

## [v0.7.1] - %Y->- (HEAD -> main, origin/main, origin/HEAD)

- Changed: Update artlist_scraper.py
- Changed: Update artlist_scraper.py
- Changed: Update README.md
- Added: Add files via upload
