# Changelog

All notable changes to Stock-Video-Collector will be documented in this file.

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
