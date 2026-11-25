# Changelog

All notable changes to **The Heritage Short** AI-content generation pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Multi-Model TTS Fallback Cascade (`pipeline/narration.py`):**
  - Added seamless tier routing (`gemini-3.8-flash-tts` &rarr; `gemini-3.8-flash-lite-tts` &rarr; `gemini-2.5-flash-preview-tts`) to navigate free-tier daily quotas.
  - Added automated raw PCM to RIFF WAV container packaging for preview endpoints.
- **Root Character References:**
  - Added centralized visual reference definitions for Kaleb and Ato Berhanu directly in `storyboard.json`.

### Changed
- **Refined Amharic Narration & Cultural Grounding:**
  - Standardized terminology to use the authentic Ethiopian agricultural tool **"ዶማ" (Doma)**.
  - Re-voiced all 9 shots with clean native phrasing, eliminating prompt preamble leakage.
  - Total pure spoken dialogue duration optimized to 48.81s across a 64.5s contract structure.
- **Re-rendered Radio Cut:**
  - Updated `outputs/final/radio_cut.mp4` with new audio stems, sidechain ducking, and native Nyala typography.

---

## [0.1.0] - 2026-11-24

### Added
- **Repository Architecture:** Scaffolded modular pipeline directories (`pipeline/`, `schema/`, `outputs/`).
- **Schema Validation Contract (`schema/storyboard.schema.json` & `schema/validate.py`):**
  - JSON Schema enforcing shot IDs, shot reasons, duration bounds (60–90s), and required prompt fields before execution.
- **Documentation Framework:**
  - `README.md` with architecture diagram, SemVer badge, and quickstart guide.
  - `ARCHITECTURE.md` detailing stage contracts, SHA-256 caching logic, and Ken Burns fallback architecture.
  - `EXPERIMENTS.md` structured matrix for $\ge 10$ hypothesis-driven tests.
  - `FAILURES.md` chronological blocker and resolution journal.
  - `COSTS.md` latency, GPU minutes, and commercial cost equivalent ledger.
- **Environment & Git Hygiene:**
  - Added `.env.example` template with API keys specification.
  - Added `.gitignore` to prevent secret leaks and heavy media tracking.
  - Pinned runtime dependencies in `requirements.txt`.
