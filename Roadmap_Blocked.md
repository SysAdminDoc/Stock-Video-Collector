# Blocked Roadmap Items

Items that require external infrastructure, heavy ML dependencies, or external credentials.

## ML / Heavy Dependencies
- Embedding-based semantic search (CLIP video embeddings) for "find a clip of a sunset" without tags — needs torch + open_clip, ~2 GB model download
- Scene detection + thumbnail-mosaic preview per clip — needs scenedetect package + significant UI for mosaic grids
- Tag co-occurrence graph for tag refinement and discovery — needs graph visualization library (e.g. networkx + matplotlib or D3 webview)
- "Similar clips" from CLIP embedding nearest-neighbor search — depends on CLIP infrastructure above

## External Services / Credentials
- Discord-bot companion that takes a search query and drops newest matches into a channel — needs Discord bot token + hosting
- Automatic copyright check (frame-hash against a known-copyrighted db) with risk score — needs external frame-hash database

## Infrastructure
- Multi-machine library sync via SQLite replication or Litestream — needs server infrastructure or Litestream setup

## Dependency Decision Required
- Replace homebrew XOR stream cipher with standard AEAD (Fernet/AES-GCM) — requires adding `cryptography` package as a direct dependency. Current HMAC-SHA256 CTR + encrypt-then-MAC is functionally correct but not a named standard.

## Large Scope
- Built-in lightweight editor: trim + concatenate + export without leaving the app — massive scope, needs dedicated video editing UI with timeline, preview, and export pipeline
