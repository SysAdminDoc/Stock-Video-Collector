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

- [ ] P2 — Add local dependency audit and reproducible release gate
  Why: Broad dependency ranges make releases depend on the current venv state, and there is no local vulnerability audit in release verification.
  Evidence: `requirements.txt`, `tools/build_release.py`, pip-audit project.
  Touches: requirements/constraints, release verification script, README release steps, tests.
  Acceptance: release verification records/resolves deterministic dependency versions, runs a local vulnerability audit, fails on incompatible or vulnerable core dependencies, and remains local-only with no CI workflow.
  Complexity: M

- [ ] P2 — Remove hidden keyboard shortcuts and keep actions visible
  Why: Current project instructions prohibit keyboard shortcuts, but the app registers hidden `QShortcut` bindings.
  Evidence: `artlist_scraper.py:7169`, `README.md` keyboard shortcuts section, `AGENTS.md`.
  Touches: `MainWindow` action wiring, toolbar/context/menu controls, README usage docs, static tests.
  Acceptance: no `QShortcut`/`QKeySequence` action bindings remain; every removed shortcut action is reachable through visible UI controls; tests or static checks prevent reintroduction.
  Complexity: S

- [ ] P2 — Add database backup catalog with checksum, retention, and selected restore
  Why: Current recovery restores only the latest pre-clear backup, which is weak for long-running local libraries.
  Evidence: `artlist_scraper.py:863`, `artlist_scraper.py:881`, `artlist_scraper.py:10167`, `artlist_scraper.py:10215`.
  Touches: DB backup helpers, Crawl/Admin tab recovery UI, backup metadata, tests.
  Acceptance: users can view timestamp/size/checksum for available backups, restore a selected verified backup, and configure/delete backups by retention policy.
  Complexity: M

- [ ] P2 — Add thumbnail failure diagnostics and retry queue
  Why: Thumbnail HTTP/ffmpeg failures are currently hard to see or repair, leaving large libraries with silent blank cards.
  Evidence: `artlist_scraper.py:3621`, `artlist_scraper.py:6037`, Immich thumbnail/corrupt-media issue patterns.
  Touches: thumbnail fetch helpers, `ThumbnailWorker`, DB schema, Library filters/actions, tests.
  Acceptance: failed thumbnail jobs persist reason, source URL/local path, timestamp, and retry count; Library exposes a failed-thumbnail filter and retry/reset action; tests cover HTTP failure, ffmpeg failure, and successful retry cleanup.
  Complexity: M

- [ ] P2 — Add embedded provenance and metadata round-trip
  Why: Existing sidecars and planned provenance fields do not preserve embedded IPTC/XMP/C2PA-style rights metadata from imported or exported video assets.
  Evidence: `artlist_scraper.py:6138`, `artlist_scraper.py:6257`, `artlist_scraper.py:7017`, C2PA specifications, IPTC Video Metadata Hub.
  Touches: DB schema after provenance fields, `ImportWorker`, sidecar writer, export workers, optional metadata-tool detection, tests.
  Acceptance: imports read embedded title/creator/rights/license fields when available, exports include a standards-oriented provenance sidecar or validation report, and no in-place media metadata writes occur without explicit copy/backup behavior.
  Complexity: L

- [ ] P3 — Add explicit portable mode and config-location diagnostics
  Why: Config, thumbnails, and default output paths still assume user-profile folders, making USB/portable usage and support harder.
  Evidence: `artlist_scraper.py:1584`, `artlist_scraper.py:3571`, `artlist_scraper.py:7547`, `artlist_scraper.py:9514`, desktop downloader portable-use patterns.
  Touches: config path helpers, startup args/env handling, About/diagnostics panel, path migration tests.
  Acceptance: `--portable` or a documented sentinel stores config/db/thumbs/output under the app directory, diagnostics show the active config mode/path, and legacy/default mode remains backward-compatible.
  Complexity: M
