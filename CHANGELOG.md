# Changelog

## 0.1.0 — Initial repository publication

- Organized the supplied Contract Risk Analyzer source archive into a conventional repository layout.
- Added project README, architecture documentation, and a scoring-policy summary.
- Preserved the supplied enterprise scoring policy PDF and product demo video under `docs/assets/`.
- Removed bundled uploaded contract samples from version control and retained `uploads/.gitkeep` for runtime initialization.
- Added local database, runtime upload, cache, and generated-file ignore rules.
- Fixed the missing `logging` import in the FastAPI entry point so the module compiles cleanly.
