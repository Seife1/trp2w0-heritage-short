# Changelog

All notable changes to **The Heritage Short** AI-content generation pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Automated Validation Test Suite (`tests/test_pipeline.py` & `run.py --test`):**
  - Added comprehensive pytest test suite verifying schema validation, 60-90s contract compliance, voice rules, visual reference auto-extraction, deterministic caching, and aspect-aware framing.
  - Achieved 100% pass rate (7/7 tests passed in 1.08s).
- **Aspect-Aware Cinematic Safe Framing (Experiment 11):**
  - Integrated `FRAMING_PROFILES` with shot-specific normalized anchor offsets ($x, y$) preventing tool-head and character clipping across `9:16` vertical mobile feeds and `16:9` widescreen.
  - Balanced two-character mentorship interaction (Shots 05, 06, 07, 09) within safe visual margins.
- **Golden Visual Reference Integration & Token Invalidation (Experiment 12):**
  - Ingested golden character and landscape reference sheets into `outputs/references/`.
  - Extracted 7 isolated visual tokens and integrated their timestamps into `compute_keyframe_hash()`.
- **Title Harmonization & Enhanced Bilingual End Card:**
  - Standardized official film title to `"የማያውቁት ነገር ላብ ያበረክታል"` across `storyboard.json`, documentation, and metadata.
  - Rendered updated 2.5s Ethical AI Disclosure End Card with gold Amharic quotation title and English translation (*"What one does not know brings much sweat and toil."*).
- **Golden Visual Reference Integration:**
  - Ingested golden character and landscape reference sheets into `outputs/references/`.
- **Single-Command Pipeline Entrypoint (`run.py`):**
  - Built stranger-friendly unified CLI providing one-command end-to-end reproducibility (`python run.py`).
  - Added `--dry-run` flag to audit schema validity, asset health, and contract durations without triggering network calls or consuming API quotas.
  - Added stage filtering (`--stage {schema,narration,music,curate,shots,master}`) and aspect targeting (`--aspect {9:16,16:9,both}`).
- **Two-Pass -14 LUFS Loudness Mastering & AI Disclosure End Card (`pipeline/assemble.py --master`):**
  - Implemented EBU R128 / ITU-R BS.1770 compliant two-pass mastering with true-peak limiting (`-14.0 LUFS` integrated, `True Peak <= -1.0 dBFS`, `LRA = 5.6 LU`).
  - Synthesized a 2.5s Ethical AI Disclosure End Card rendered with DirectWrite `Nyala` typography highlighting generative AI models used (FLUX.1 schnell, Leonardo Phoenix, Gemini Flash TTS, and acoustic instrument synthesis).
  - Delivered final production master MP4s conforming strictly to the 60.0–90.0s challenge contract:
    - Vertical Master (`9:16`, 1080x1920): `outputs/final/final_master_9_16.mp4` (11.18 MB, 68.11s)
    - Horizontal Master (`16:9`, 1920x1080): `outputs/final/final_master_16_9.mp4` (10.27 MB, 68.11s)
- **Hybrid Keyframe Curation Pipeline (`pipeline/curate.py`):**
  - Synthesized evaluator A/B feedback into a curated master keyframe sequence in `outputs/keyframes_curated/` pairing Leonardo Phoenix (landscape depth, garment weaves, companions) and FLUX.1 schnell (fatigue, strained grip, mentor posture).
  - Generated automated curation manifest (`outputs/keyframes_curated/curation_manifest.json`) recording per-shot model selection rationale.
- **Curated Rough Cut Re-assembly:**
  - Updated `pipeline/shots.py` and `pipeline/assemble.py` to target the curated master keyframes.
  - Re-rendered both vertical (`rough_cut.mp4`, 10.47 MB) and horizontal (`rough_cut_h16_9.mp4`, 9.56 MB) cuts with improved tool consistency and landscape depth.
- **Per-Shot TTS Voice Selection (`pipeline/narration.py`):**
  - Set Charon as the default voice and Algenib for Shot 6 through the storyboard contract.
  - Include the selected voice in narration cache keys so voice changes regenerate affected stems.
- **Multi-Model Keyframe A/B Testing (`pipeline/keyframes.py`):**
  - Added support for `--model leonardo` integrating **Leonardo AI Phoenix 1.0** (`@cf/leonardo/phoenix-1.0`) alongside FLUX.1 schnell.
  - Successfully generated and visually validated all 9 alternate keyframes in `outputs/keyframes_leonardo/`.
  - Documented quantitative and qualitative A/B evaluation in `EXPERIMENTS.md` (Experiment 04).
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
