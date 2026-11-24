# Changelog

All notable changes to **The Heritage Short** AI-content generation pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Gemini TTS Narration Pipeline (`pipeline/narration.py`):**
  - Line-by-line Amharic narration generation with SHA-256 input-hash caching.
  - Telemetry logging of latency, model parameters, and exact audio durations to `runs.jsonl`.
- **FFmpeg Radio Cut Assembler (`pipeline/assemble.py`):**
  - Concatenation of line-by-line audio stems.
  - Automated temp drone score generation with FFmpeg audio filters.
  - Sidechain dynamic ducking (`sidechaincompress`) layering score beneath speech.
  - Export of 1080x1920 vertical `radio_cut.mp4` for Checkpoint 1 user testing.
- **Validated Storyboard Contract (`storyboard.json`):**
  - 9 structured narrative beats (~64.5s total duration) based on the Ethiopian proverb *"የማያውቁት ነገር ላብ ያበረክታል"*.
  - Strict camera/motion prompts, character references (`kaleb`, `ato_berhanu`), and acoustic music cue points.
- **Ethics & Consent Documentation (`ETHICS.md`):**
  - Classified characters as authentic folkloric cultural archetypes with zero real-person likeness infringement risk.
  - Documented model licenses (`Wan 2.2`, `FLUX.2 klein`, `ACE-Step 1.5`, `Gemini API`) and AI disclosure end card plan.
- **Audience & Design Specifications (`DESIGN.md`):**
  - Defined target mobile persona, vertical viewing context (`9:16`), and templates for User Tests #1 and #2.

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
