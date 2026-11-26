# Pipeline Architecture & Stage Contracts

## System Overview
The Heritage Short generation pipeline is an automated, contract-driven, reproducible multi-model pipeline that transforms a validated declarative contract (`storyboard.json`) into high-quality vertical (`9:16`) and horizontal (`16:9`) short films.

```mermaid
flowchart TD
    Contract["storyboard.json"] --> Validate["schema/storyboard.schema.json Validator"]
    Validate --> Narration["pipeline/narration.py (Gemini 3.8 Flash TTS)"]
    Validate --> Keyframes["pipeline/keyframes.py (Cloudflare FLUX.2 klein 4B)"]
    Validate --> Music["pipeline/music.py (Procedural Acoustic Synth)"]
    Keyframes --> Shots["pipeline/shots.py (Wan 2.2 / Ken Burns)"]
    Narration --> Assembly["pipeline/assemble.py (FFmpeg)"]
    Music --> Assembly
    Shots --> Assembly
    Assembly --> MasterVertical["outputs/final/film_9_16.mp4"]
    Assembly --> MasterHorizontal["outputs/final/film_16_9.mp4"]
```

## Stage Contracts

### 1. Contract Validation
- **Input:** `storyboard.json`
- **Enforcement:** Validated against `schema/storyboard.schema.json` before any worker execution.
- **Fail-Fast:** Execution halts immediately with detailed schema errors if invalid.

### 2. Narration Stage (`pipeline/narration.py`)
- **Engine:** Google AI Studio `Gemini 3.8 Flash TTS`
- **Granularity:** Line-by-line (one `.wav` file per shot).
- **Output:** `outputs/audio/narration_{shot_id}.wav`
- **Voice selection:** `storyboard.json` sets Charon as the default preset; a shot may override it. Shot 6 uses Algenib for Ato Berhanu's dialogue.
- **Caching:** The selected voice is included in each narration cache key, so changing a shot's voice invalidates only that shot's cached narration.
- **Duration Locking:** The exact measured speech duration drives the visual clip duration during assembly.

### 3. Keyframe Generation (`pipeline/keyframes.py`)
- **Engine:** Cloudflare Workers AI (`FLUX.2 klein` 4B / `FLUX.1 schnell`)
- **Consistency Enforcement:**
  - Conditioning on a Golden Reference Sheet.
  - Verbatim appending of a centralized `style_block`.
- **SHA-256 Input-Hash Caching:**
  - `cache_key = sha256(prompt + style_block + seed + model_params + ref_hash)`
  - If output exists and hash matches, generation is skipped.

### 4. Moving Shots (`pipeline/shots.py`)
- **Engine:** `Wan 2.2 TI2V-5B` (or `HunyuanVideo 1.5`) via batch GPU inference on Kaggle / Colab.
- **Fallback:** Automatic fallback to FFmpeg Ken Burns dynamic `zoompan` after 3 failed attempts or GPU exhaustion.

### 5. Original Score (`pipeline/music.py`)
- **Engine:** Procedural Acoustic Physical Modeling (NumPy / SciPy). Rather than remote black-box text-to-music models (e.g. ACE-Step / Suno) which hallucinate Western chromatic harmonies or unwanted vocal babble, the score is synthesized locally in culturally authentic Ethiopian pentatonic Tizita modal scales:
  - **Krar (የክራር ዜማ):** Karplus-Strong physical modeling of plucked bowl lyre in D minor Tizita.
  - **Begena (የበገና ዜማ):** Harmonic saturation modeling the 10-string box lyre buzzing bridge ("birke").
  - **Washint (ዋሽንት):** End-blown bamboo flute model with breath turbulence and 5 Hz vibrato.
  - **Kebero (ከበሮ):** Resonant hand drum model with dual bass boom and rim slap.
- **Contract Integration:** Dynamically loads cue definitions, start/end timestamps, BPM, and keys from `storyboard.json` (`music_cues`) rather than hardcoded constants.
- **Deterministic Reproducibility:** Seeded NumPy PRNG (`--seed`, default `42`) guarantees bit-for-bit identical waveforms and audition scores across runs.
- **Audition Engine & Methodology:** Generates 3 candidate arrangements; computes an objective mathematical proxy for crest factor and 1kHz–3kHz speech-presence band masking. Structured human listening tests (User Test #2) across phone speakers and headphones validate final perceptual dialogue intelligibility.
- **Output:** Stems in `outputs/audio/music/` and master score `outputs/audio/music/score_final.wav`.

### 6. Assembly & Mastering (`pipeline/assemble.py`)
- **Tool:** `FFmpeg`
- **Audio Ducking:** `sidechaincompress` dynamic ducking (threshold=0.02, ratio=6, attack=300ms, release=1500ms).
- **Subtitles:** Centered inside the 9:16 safe area (max 2 lines, ~40 characters per line).
- **Loudness Normalization:** Two-pass EBU R128 (`loudnorm`) targeting **-14 LUFS** and **true peak <= -1 dB**.
- **End Card:** 2–3s AI attribution card appended at the conclusion.
