# Stock Video Collector Roadmap

Roadmap for Stock Video Collector - a PyQt6 + Playwright desktop tool that crawls stock-video sites, indexes clips in SQLite+FTS5, and manages concurrent downloads.

## Audit-Identified Items

- [ ] P1 — Bandwidth throttle value computed but never applied to ffmpeg
  Why: Users selecting "Throttle daytime" get full-speed downloads. The `_throttle` return value from `_check_bw_schedule` is discarded.
  Where: `artlist_scraper.py` DownloadWorker._download_one, BW_SCHEDULES

- [ ] P2 — Bandwidth schedule blocks download slots for 10 minutes doing nothing
  Why: `nights_only` schedule sleeps in the download thread for 600s. Slots are occupied but idle.
  Where: `artlist_scraper.py` DownloadWorker._download_one

- [ ] P2 — Secret vault key file has no NTFS ACL protection on Windows
  Why: `os.chmod(path, 0o600)` is a no-op on Windows. The master key is readable by any process as the same user.
  Where: `artlist_scraper.py` secret vault key file creation

- [ ] P2 — User plugin system executes arbitrary Python without consent
  Why: Any `.py` file in `user_profiles/` is unconditionally executed at import time. No sandboxing or user confirmation.
  Where: `artlist_scraper.py` `_load_user_plugins()`

- [ ] P2 — Custom XOR stream cipher for secret vault instead of standard AEAD
  Why: Homebrew crypto (HMAC-SHA256 CTR) instead of Fernet/AES-GCM. Works but not peer-reviewed.
  Where: `artlist_scraper.py` vault encrypt/decrypt

- [ ] P3 — yt-dlp subprocess stderr not drained before wait() in ingest worker
  Why: Large stderr output could fill pipe buffer, causing 10s hang on stop.
  Where: `artlist_scraper.py` YtDlpIngestWorker.run()

- [ ] P3 — Watch folder detects files still being written (no stability check)
  Why: QFileSystemWatcher fires before file write completes. ffprobe may extract wrong metadata.
  Where: `artlist_scraper.py` _on_watch_folder_changed

See Roadmap_Blocked.md for items requiring external dependencies (CLIP, scene detection, Discord bot, etc.).
