# Stock Video Collector Roadmap

Roadmap for Stock Video Collector - a PyQt6 + Playwright desktop tool that crawls stock-video sites, indexes clips in SQLite+FTS5, and manages concurrent downloads.

## Planned Features

### Crawler hardening
- Scheduled crawls (APScheduler) with nightly incremental runs
- Per-site plugin interface so new sites can be added without touching core

### Metadata & search
- Locked-collection view for portfolio curation
- Saved-search feeds with new-match notifications

### Download manager
- yt-dlp fallback for any URL the Playwright extractor misses
- Accurate resume on partial HLS downloads (verify segment count + total bytes)
- Queue priorities + per-site concurrency caps
- Bandwidth schedule (full-speed nights, throttle daytime)
- Post-download transcode presets (H.264 1080p proxy, HEVC 4K archive, ProRes master)

### Library & export
- Tag editor with bulk rename, merge, and split
- Export to Adobe Premiere / DaVinci Resolve bin (XML) with proxies pre-linked
- Export to OpenCut / Final Cut XML
- Batch ffmpeg watermark-stripper (for user's *own* uploaded clips that have preview watermarks)

### Automation
- Watch-folder that auto-imports downloaded files from other tools
