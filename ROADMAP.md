# Stock Video Collector Roadmap

Roadmap for Stock Video Collector - a PyQt6 + Playwright desktop tool that crawls stock-video sites, indexes clips in SQLite+FTS5, and manages concurrent downloads.

## Planned Features

### Site coverage
- YouTube CC-BY collections (ingest via yt-dlp fallback, not Playwright)
- Coverr.co, Mazwai, Videvo, Mixkit, Videezy - royalty-free targets
- Generic RSS/Atom ingest for any site with a video feed

### Crawler hardening
- Playwright persistent context rotation + optional proxy pool (user-supplied proxies.txt)
- Residential-proxy toggle with per-session IP stickiness
- Human-in-the-loop CAPTCHA bypass with Discord/Telegram ping when a challenge appears
- Rate-limit respect: per-site `robots.txt` + `X-RateLimit` header observation; research note: implement with per-host token buckets, `Retry-After` handling, and visible crawl-budget state
- Scheduled crawls (APScheduler) with nightly incremental runs
- Per-site plugin interface so new sites can be added without touching core

### Metadata & search
- Embedding-based semantic search (CLIP video embeddings) for "find a clip of a sunset" without tags
- Scene detection + thumbnail-mosaic preview per clip
- Tag co-occurrence graph for tag refinement and discovery
- Duration-bucketed browsing (<5s, 5-15s, 15-30s, >30s)
- Locked-collection view for portfolio curation
- Saved-search feeds with new-match notifications

### Download manager
- yt-dlp fallback for any URL the Playwright extractor misses
- Accurate resume on partial HLS downloads (verify segment count + total bytes)
- Queue priorities + per-site concurrency caps
- Bandwidth schedule (full-speed nights, throttle daytime)
- Post-download transcode presets (H.264 1080p proxy, HEVC 4K archive, ProRes master)

### Library & export
- Import existing MP4 libraries and reverse-index metadata via ffprobe
- Tag editor with bulk rename, merge, and split
- Export to Adobe Premiere / DaVinci Resolve bin (XML) with proxies pre-linked
- Export to OpenCut / Final Cut XML
- Batch ffmpeg watermark-stripper (for user's *own* uploaded clips that have preview watermarks)

## Competitive Research

- **yt-dlp / gallery-dl** - bulk extraction at CLI level, no library management. Stock Video Collector is the GUI + library layer on top; add a "yt-dlp URL list" import/export so power users can bridge.
- **Eagle / Billfish** - best-in-class visual library UX with pinch-zoom grids and smart folders; borrow their folder/tag hybrid model and batch tag ops.
- **Lightroom / Bridge** - rating + flag + color-label workflow; already partly mirrored with stars + favorites, add color labels and collection-as-query.
- **PornHub Downloader style tools** - aggressive anti-detection recipes (fingerprint randomization, canvas spoofing). The Playwright stealth implementation is close, but needs optional JS fingerprint rotation.

## Nice-to-Haves

- Built-in lightweight editor: trim + concatenate + export without leaving the app
- Automatic copyright check (frame-hash against a known-copyrighted db) with risk score
- Discord-bot companion that takes a search query and drops newest matches into a channel
- "Similar clips" from CLIP embedding nearest-neighbor search
- Project packaging - bundle selected clips into a zip with JSON metadata for handoff
- Watch-folder that auto-imports downloaded files from other tools
- Multi-machine library sync via SQLite replication or Litestream

## Open-Source Research (Round 2)

### Related OSS Projects
- https://github.com/Gabriellgpc/pexel-downloader — Pexels API + scrape hybrid, simple CLI MIT
- https://github.com/ToshY/pexels-scraper — Pexels image topic-search scraper, Python
- https://github.com/rpawk/image_downloader — Multi-source Pexels + Pixabay image downloader
- https://github.com/topics/pexels-downloader — Topic hub
- https://github.com/topics/pixabay — Pixabay topic hub
- https://github.com/nficano/pytube — Reference for progress-hook + resumable download pattern (applicable to any HTTP video dl)
- https://github.com/mikf/gallery-dl — Extensible site-extractor architecture, excellent plugin model for adding new stock sites

### Features to Borrow
- Official-API-first, browser-scrape-fallback — Pexels and Pixabay have generous free APIs; hit API when key present, fall back to Playwright only for logged-in Artlist/Envato (search results note this as cleaner than scraping)
- gallery-dl style extractor interface — each stock site = one extractor class with `pattern`, `extract_items`, `download_item`; drop-in extend
- Pytube-style progress hook (bytes_downloaded, total, speed) surfaced in PyQt6 progress delegate (already present; cross-reference for resumable HTTP range)
- Pixabay free-API key mode — 20k req/month free, avoid Playwright entirely for Pixabay
- "Similar clips" via CLIP embedding nearest-neighbor — already on roadmap; ref https://github.com/mlfoundations/open_clip

### Patterns & Architectures Worth Studying
- Extractor plugin pattern (gallery-dl) — `extractors/artlist.py`, `extractors/pexels.py`, each declaring URL patterns + cookie needs; core handles queuing, dedupe, rate-limit, retry
- Rate-limit decorator with per-host token bucket so concurrent downloads from same host respect ToS
- Resumable chunked download with SHA256 verify + `.part` file (pytube, gallery-dl, ffmpeg-dl all use this)
- Cookie-jar persistence per extractor so Artlist re-login doesn't happen every run — save to keyring, not plaintext
- FTS5 + embedding hybrid search — FTS for keywords, CLIP vector for visual similarity, union-rank with RRF

## Research-Driven Additions

- [ ] P0 - Normalize release/version state and reproducible artifact builds
  Why: The source header lists internal notes through v1.1.0 while README/window title say v0.7.4, and `dist/` is not tied to a repeatable release flow.
  Evidence: `artlist_scraper.py`, `README.md`, PyInstaller build notes, Eagle/JDownloader/4K Download public release patterns.
  Touches: `artlist_scraper.py`, `README.md`, changelog/release notes, build script/spec, release artifact cleanup.
  Acceptance: One version constant drives UI/docs/badges/changelog; clean build deletes stale artifacts and produces a fresh installable desktop artifact.
  Complexity: M

- [ ] P0 - Atomic download writes with post-download validation
  Why: `_download_one()` writes directly to the final MP4 path and only deletes zero-byte failures, which can leave corrupt files marked as usable.
  Evidence: `artlist_scraper.py`, yt-dlp/gallery-dl archive and partial-download behavior.
  Touches: `DownloadWorker._download_one`, `_write_sidecar`, `_extract_thumb`, archive verification UI, tests.
  Acceptance: Downloads write to `.part`, atomically rename only after nonzero size plus `ffprobe` validation, and failed partials remain clearly resumable or quarantined.
  Complexity: M

- [ ] P0 - Replace destructive confirmation dialogs with backup-plus-undo flow
  Why: Database clearing is destructive and currently modal; the UI rule is immediate action with toast/status feedback and recovery.
  Evidence: `artlist_scraper.py` `_clear_db`, repository GUI rules.
  Touches: `DB.clear_all`, `MainWindow._clear_db`, config/output backup helpers, toast/log/status paths.
  Acceptance: Clear database creates a timestamped SQLite backup, runs immediately, shows toast/status/log feedback, and offers an in-app restore action for the latest backup.
  Complexity: M

- [ ] P0 - Add credential vault and redacted diagnostics
  Why: API keys, proxy credentials, and session-related settings should not live in plaintext JSON or leak into logs as official API modes expand.
  Evidence: `load_config`/`save_config` in `artlist_scraper.py`, Pexels/Pixabay/Vimeo/Adobe Stock API docs.
  Touches: config storage, API connector settings, crawl/download logging, crash log writer, export diagnostics.
  Acceptance: Secrets are stored via OS keyring or encrypted fallback, logs/crash reports redact tokens/cookies/query credentials, and config export excludes secrets by default.
  Complexity: L

- [ ] P1 - Add optional official API connector layer
  Why: Pexels, Pixabay, Vimeo, and Adobe Stock expose official search APIs that can reduce browser fragility and improve metadata completeness.
  Evidence: Pexels API docs, Pixabay API docs, Vimeo API docs, Adobe Stock API docs, existing API-first roadmap notes.
  Touches: new `connectors/` or `profiles/` modules, settings UI, quota/backoff handling, `DB.save_clip`, tests/fixtures.
  Acceptance: When a key is configured, supported profiles can crawl via API with quota-aware pagination and fall back to Playwright when unavailable.
  Complexity: L

- [ ] P1 - Split site profiles into extractor modules with contract tests
  Why: The monolithic file mixes profile definitions, JS extractors, crawler behavior, storage, and GUI, making site breakage expensive to isolate.
  Evidence: `artlist_scraper.py`, gallery-dl and yt-dlp extractor architecture.
  Touches: `profiles/`, `crawler/`, `tests/fixtures/`, `tests/test_static_profiles.py`, import/bootstrap wiring.
  Acceptance: Each built-in site has an importable extractor/profile module with URL-match, ID extraction, catalog fixture, and video URL filter tests.
  Complexity: L

- [ ] P1 - Add per-site crawl trace and replay diagnostics
  Why: Broken selectors and network drift need reproducible evidence without rerunning broad live crawls.
  Evidence: Playwright trace/HAR features, current log-only crawler diagnostics in `CrawlerWorker`.
  Touches: `CrawlerWorker`, log panel, output directory layout, redaction helper, test fixture loader.
  Acceptance: A failed crawl can save a redacted trace/HAR/HTML snapshot bundle and replay extractor tests against saved fixtures.
  Complexity: M

- [ ] P1 - Add license and attribution provenance fields
  Why: Stock footage libraries need source license, attribution, preview/watermark status, and terms URL to prevent misuse during export/handoff.
  Evidence: Pexels/Pixabay/Vimeo/Adobe Stock docs, README export workflow, current `clips` schema.
  Touches: `DB._init`, `save_clip`, profile/API metadata extraction, detail panel, CSV/JSON/sidecar exports.
  Acceptance: New clips record license/provenance where available, UI exposes it, and exports include attribution/terms fields.
  Complexity: M

- [ ] P1 - Add accessibility pass for controls, status, and media cards
  Why: Dense PyQt controls and icon/text buttons need accessible names, focus order, non-color-only states, and screen-reader-friendly status updates.
  Evidence: `MainWindow._build_*` methods, Eagle/Bridge media-library UX expectations, PyQt6 accessibility APIs.
  Touches: UI builders, `ClipCard`, `ToastNotification`, status/log widgets, tests or manual checklist.
  Acceptance: Major controls/cards have accessible names/descriptions, keyboard focus order is deterministic, and errors/statuses are not color-only.
  Complexity: M

- [ ] P2 - Expand automated tests beyond static profile parsing
  Why: Current tests compile the entrypoint and inspect profile literals, but downloader, DB migrations, exports, and local import are unprotected.
  Evidence: `tests/test_static_profiles.py`, `DB`, `DownloadWorker`, `ImportWorker`, export methods.
  Touches: `tests/`, fake HTTP server fixtures, fake ffmpeg/ffprobe fixtures, temporary SQLite databases.
  Acceptance: Local test suite covers DB migrations/FTS recovery, export formats, download error paths, local import metadata, and profile extractor contracts.
  Complexity: L

- [ ] P2 - Add duplicate and near-duplicate detection
  Why: Visual libraries need duplicate management before large imports/downloads become hard to curate.
  Evidence: Eagle/Billfish duplicate features, Hydrus/PhotoPrism/Immich media library patterns, PySceneDetect/ThreatExchange references.
  Touches: import worker, thumbnail pipeline, DB schema, Library filters, bulk actions.
  Acceptance: Exact file hashes and optional perceptual signatures group duplicate/near-duplicate clips with merge/keep decisions in the Library.
  Complexity: L

- [ ] P3 - Add project handoff packages with provenance manifests
  Why: Editors often need to hand off selected clips plus metadata, licenses, thumbnails, and sidecars as a portable bundle.
  Evidence: Adobe Bridge batch/package workflows, DaVinci Resolve media pool workflows, current JSON/CSV/M3U export support.
  Touches: export tab, collection selection, zip/tar creation, manifest schema, sidecar writer.
  Acceptance: A selected collection/search can export a folder or archive containing clips, thumbnails, sidecars, license/provenance manifest, and checksum file.
  Complexity: M
