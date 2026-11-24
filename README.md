# The Heritage Short — AI-Content Generation Pipeline

![Version](https://img.shields.io/badge/version-v0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-scaffolded-orange.svg)

An automated, schema-driven, multi-model pipeline that transforms a declarative contract (`storyboard.json`) into high-quality vertical (`9:16`) and horizontal (`16:9`) heritage short films with synchronized speech, original score, sidechain audio ducking, and burned-in subtitles.

---

## Repository Structure

```text
├── README.md            # Overview, quickstart, and changelog
├── TODO.md              # Complete self-contained challenge playbook
├── storyboard.json      # Declarative single source of truth for all shots
├── schema/              # JSON Schema validation
│   └── storyboard.schema.json
├── pipeline/            # Modular generation and assembly stages
│   ├── __init__.py
│   ├── script.py        # Gemini story / script generation
│   ├── keyframes.py     # Cloudflare FLUX image keyframes with SHA-256 caching
│   ├── shots.py         # Wan 2.2 / Ken Burns video generation
│   ├── music.py         # ACE-Step 1.5 score generator
│   ├── narration.py     # Gemini 3.8 Flash TTS line-by-line narrator
│   └── assemble.py      # FFmpeg ducking, subtitle burn-in, loudness normalization
├── runs.jsonl           # Append-only execution and cost telemetry
├── outputs/             # Generated media (gitignored)
├── DESIGN.md            # Audience definition, User Test #1 & #2 logs and diffs
├── ARCHITECTURE.md      # Stage contracts, caching mechanism, retry & fallback logic
├── EXPERIMENTS.md       # >= 10 structured hypothesis-driven experiments
├── FAILURES.md          # Chronological blocker and resolution journal
├── COSTS.md             # Measured latency, GPU minutes, and list-price equivalents
└── ETHICS.md            # Consent gate records, model licences, and AI disclosure plan
```

---

## Quickstart

### Prerequisites
- Python 3.10+
- FFmpeg installed and available on PATH
- Google AI Studio API Key (`GEMINI_API_KEY`)
- Cloudflare Workers AI Token (`CLOUDFLARE_API_TOKEN`)

### Setup
```bash
# 1. Clone repository
git clone <repo-url>
cd "Week 0"

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your valid credentials

# 3. Install Python dependencies
pip install -r requirements.txt
```

---

## Recent Updates

### [v0.1.0] - 2026-11-24
- Initialized repository architecture with strict contract-driven schema (`schema/storyboard.schema.json`).
- Established documentation framework: `DESIGN.md`, `ARCHITECTURE.md`, `EXPERIMENTS.md`, `FAILURES.md`, `COSTS.md`, and `ETHICS.md`.
- Configured `.gitignore` and `.env.example` ensuring zero credential leaks.
