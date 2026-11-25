# Changelog

All notable changes to **The Heritage Short** AI-content generation pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Rough Cut Assembly (`pipeline/assemble.py --rough-cut`):**
  - Assembled Checkpoint 2 Rough Cut in both `9:16` vertical (`rough_cut.mp4`, 11.16 MB) and `16:9` horizontal (`rough_cut_h16_9.mp4`, 10.17 MB).
  - Synchronized all 9 moving video shots (65.50s total duration conforming to the 60-90s contract).
  - Layered winning original score (`score_final.wav`) with dynamic sidechain ducking (-8 to -10 dB under speech).
  - Integrated dual Amharic & English subtitles via Advanced SubStation Alpha (`.ass`) with DirectWrite font rendering of native Windows `Nyala`.
- **Original Score Engine (`pipeline/music.py`):**
  - Implemented culturally authentic acoustic synthesizer modeling traditional Ethiopian instruments: Krar (plucked lyre in Tizita minor), Begena (10-string box lyre with 'birke' buzz), Washint (bamboo flute), and Kebero (hand drum).
  - Built automated audition engine generating 3 distinct arrangements, measuring spectral speech masking (1kHz–3kHz) and dynamic headroom.
  - Exported winning score (`outputs/audio/music/score_final.wav`) with 1.5s seamless crossfade between struggle (74 BPM) and wisdom (80 BPM) cues.
- **Moving Shots Engine (`pipeline/shots.py`):**
  - Built programmatic FFmpeg Ken Burns dynamic camera engine translating storyboard motion prompts into fluid 24fps motion clips with zero aspect distortion.
  - Added dual aspect ratio rendering (`9:16` vertical 1080x1920 and `16:9` horizontal 1920x1080) for all 9 narrative shots.
  - Implemented SHA-256 caching and telemetry logging into `runs.jsonl`.
  - Added Kaggle/Colab remote execution script (`scripts/kaggle_wan_ti2v.py`) for Wan 2.2 TI2V-5B GPU generation.
- **Keyframe Generation Engine (`pipeline/keyframes.py`):**
  - Integrated Cloudflare Workers AI (`@cf/black-forest-labs/flux-1-schnell`) with automated SHA-256 caching and retry logic.
  - Ingested root character conditioning (`ref_kaleb` and `ref_ato_berhanu`) and centered cinematic framing for dual `9:16` and `16:9` safety.
  - Successfully generated and visually validated all 9 narrative keyframes in `outputs/keyframes/`.
- **Character & Setting Reference Generator (`pipeline/references.py`):**
  - Produced golden anchor reference sheets for Kaleb, Ato Berhanu, and the highland farm setting.
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
