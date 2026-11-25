# The Heritage Short — AI-Content Generation Pipeline

[![Version](https://img.shields.io/badge/version-v0.1.0-blue.svg)](./CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Contract](https://img.shields.io/badge/contract-JSON%20Schema%20Draft--07-purple.svg)](./schema/storyboard.schema.json)
[![Status](https://img.shields.io/badge/status-active%20development-brightgreen.svg)]()

An automated, schema-driven, multi-model pipeline that transforms a single declarative contract (`storyboard.json`) into high-quality vertical (`9:16`) and horizontal (`16:9`) short films with synchronized speech, an original score, sidechain audio ducking, and burned-in subtitles.

---

## 📖 Story: *The Weight of the Handle (የእጁ ሚስጥር)*

> **"የማያውቁት ነገር ላብ ያበረክታል"**  
> *"What one does not know brings much sweat and toil."* — Traditional Ethiopian Proverb

Under the scorching sun of the Ethiopian highlands, a young apprentice named **Kaleb** exhausts himself trying to break stony soil through brute physical strength. Sinking to his knees in frustration, his grandfather, **Ato Berhanu**, steps forward. With weathered hands and calm poise, the elder adjusts Kaleb's grip, demonstrating that the secret lies in balance, leverage, and momentum—not reckless force.

* **Length:** ~64.5 seconds (9 structured narrative shots)
* **Language:** Native Amharic narration with English burned-in subtitles
* **Characters:** Fictional cultural archetypes (zero real-person likeness infringement; see [ETHICS.md](./ETHICS.md))

---

## 🏗️ Architecture & Pipeline Flow

The entire production is driven by **`storyboard.json`** as the single source of truth. Every stage is modular, testable, and equipped with **SHA-256 input-hash caching** so re-runs only regenerate changed shots.

```mermaid
flowchart TD
    Contract["storyboard.json (Declarative Contract)"] --> Validator["schema/validate.py (Draft-07 Validator)"]
    Validator --> Narration["pipeline/narration.py (Gemini 3.8 Flash TTS)"]
    Validator --> Keyframes["pipeline/keyframes.py (Cloudflare FLUX.2 klein)"]
    Validator --> Music["pipeline/music.py (ACE-Step 1.5)"]
    Keyframes --> Shots["pipeline/shots.py (Wan 2.2 / FFmpeg Ken Burns)"]
    Narration --> Assembly["pipeline/assemble.py (FFmpeg Mastering)"]
    Music --> Assembly
    Shots --> Assembly
    Assembly --> MasterVertical["outputs/final/film_9_16.mp4 (Vertical Primary)"]
    Assembly --> MasterHorizontal["outputs/final/film_16_9.mp4 (Horizontal Export)"]
```

---

## 🚀 Quickstart & One-Command Run

### Prerequisites
* **Python 3.10+** (or [`uv`](https://docs.astral.sh/uv/))
* **FFmpeg** installed and accessible on your system `PATH`
* **Google AI Studio API Key** (Free tier for Gemini 3.8 Flash TTS)
* **Cloudflare Workers AI Account** (Free tier for FLUX keyframes)

### 1. Clone & Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd the-heritage-short

# Create your local environment file
cp .env.example .env
# Edit .env and paste your GEMINI_API_KEY and CLOUDFLARE_API_TOKEN
```

### 2. Single-Command Reproducibility (`run.py`)
Run the entire production pipeline end-to-end with one command:
```bash
# Verify schema contract & asset health without network calls
python run.py --dry-run

# Run full end-to-end production master (Validates -> Narrates -> Scores -> Curates -> Renders -> Masters)
python run.py

# Or run individual stages on demand:
python run.py --stage curate
python run.py --stage shots
python run.py --stage master --aspect 9:16
```
```
Open `.env` in your editor and add your API credentials:
```env
GEMINI_API_KEY=your_gemini_api_key_here
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
CLOUDFLARE_API_TOKEN=your_token_here
```

### 2. Install Dependencies
```bash
# Using standard pip
pip install -r requirements.txt

# Or using uv (recommended)
uv pip install -r requirements.txt
```

### 3. Validate the Storyboard Contract
Ensure `storyboard.json` strictly adheres to the schema constraints:
```bash
python schema/validate.py storyboard.json schema/storyboard.schema.json
```

---

## 🎬 Running the Pipeline

### Checkpoint 2: Visuals, Music & Rough Cut
```bash
# Step 1: Curate winning multi-model keyframes
python pipeline/curate.py

# Step 2: Render 24fps Ken Burns motion clips (9:16 and 16:9)
python pipeline/shots.py

# Step 3: Audition & synthesize Ethiopian acoustic score
python pipeline/music.py

# Step 4: Assemble Rough Cut with sidechain ducking & bilingual subtitles
python pipeline/assemble.py --rough-cut --aspect 9:16
python pipeline/assemble.py --rough-cut --aspect 16:9
```
*Outputs generated at:* `outputs/final/rough_cut.mp4` and `outputs/final/rough_cut_h16_9.mp4`

### Phase 3: Final Master Delivery (-14 LUFS & AI Disclosure End Card)
```bash
# Two-pass broadcast mastering with true-peak limiter and 2.5s ethical AI end card
python pipeline/assemble.py --master --aspect 9:16
python pipeline/assemble.py --master --aspect 16:9
```
*Final Master cuts generated at:*  
* Vertical Master (`9:16`): `outputs/final/final_master_9_16.mp4` (68.11s, -14.4 LUFS, TP -0.7 dBFS)  
* Horizontal Master (`16:9`): `outputs/final/final_master_16_9.mp4` (68.11s, -14.4 LUFS, TP -0.7 dBFS)  

---

## 🛠️ Key Engineering Features

1. **Deterministic Input-Hash Caching:**  
   Every keyframe and voice stem calculates `sha256(content + parameters)`. Modifying a single line in `storyboard.json` triggers regeneration **only** for that specific shot, leaving the rest cached.
2. **Automated Audio Mastering:**  
   Programmatic FFmpeg sidechain compression (`sidechaincompress`) automatically ducks background music beneath the dialogue stem, followed by two-pass EBU R128 (`loudnorm`) targeting **`-14 LUFS`** and true peak $\le -1\text{ dB}$.
3. **Safe-Area Subtitling:**  
   English subtitles are generated directly from the storyboard contract and burned inside the vertical `9:16` safe zone (clear of platform buttons on TikTok, Reels, and YouTube Shorts).
4. **Ken Burns Dynamic Fallback:**  
   If remote GPU video generation hits queue limits or exceeds 3 retries, the pipeline automatically falls back to smooth FFmpeg `zoompan` motion to guarantee deadline delivery.
5. **Per-Shot TTS Voice Selection:**
   Charon is the default narration voice, with Algenib assigned to Ato Berhanu's spoken line in Shot 6. Voice changes invalidate only the affected narration cache.

---

## 📁 Repository Guide & Documentation Index

| File / Directory | Purpose |
| :--- | :--- |
| **[`storyboard.json`](./storyboard.json)** | Single source of truth: shot reasons, durations, prompts, narration, and seeds. |
| **[`schema/`](./schema/)** | JSON Schema validation engine enforcing contract rules before runs. |
| **[`pipeline/`](./pipeline/)** | Modular, decoupled generators for speech, images, video, score, and assembly. |
| **[`runs.jsonl`](./runs.jsonl)** | Append-only execution telemetry (latencies, parameters, timestamps, status). |
| **[`DESIGN.md`](./DESIGN.md)** | Target audience persona, viewing context, and User Tests #1 & #2 logs. |
| **[`ARCHITECTURE.md`](./ARCHITECTURE.md)** | Stage contracts, caching design, and error recovery workflows. |
| **[`ETHICS.md`](./ETHICS.md)** | Mandatory consent verification, model licenses, and AI attribution plan. |
| **[`EXPERIMENTS.md`](./EXPERIMENTS.md)** | 10+ hypothesis-driven tests (`Hypothesis -> Change -> Result`). |
| **[`FAILURES.md`](./FAILURES.md)** | Blocker journal, root cause analysis, and preventative fixes. |
| **[`COSTS.md`](./COSTS.md)** | Measured latencies, GPU minutes, and commercial cost comparisons. |
| **[`CHANGELOG.md`](./CHANGELOG.md)** | SemVer release history and unreleased updates. |

---

## 📜 Recent Updates

See the full [CHANGELOG.md](./CHANGELOG.md) for detailed release notes.

* **2026-11-25:** Implemented single-entrypoint runner `run.py` supporting one-command end-to-end execution, `--dry-run` health checks, and granular `--stage` invocation.
* **2026-11-25:** Implemented two-pass -14 LUFS loudness mastering with true-peak limiting (`-14.4 LUFS`, `TP <= -1.0 dBFS`) and synthesized a 2.5s Ethical AI Disclosure End Card into `outputs/final/final_master_9_16.mp4` and `final_master_16_9.mp4`.
* **2026-11-25:** Integrated multi-model keyframe curation (`pipeline/curate.py`) and per-shot dual-voice narration (Charon + Algenib).
* **v0.1.0 (2026-11-24):** Initialized repository architecture, schema contract, documentation framework, and v0.1.0 release tag.
