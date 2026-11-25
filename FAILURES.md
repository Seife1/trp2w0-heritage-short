# Chronological Failure Journal & Root Cause Analysis

Documenting blockers, root cause investigations, attempted fixes, and final verified solutions.

---

### Failure 01: Gemini 3.8 Flash TTS Rate Limit (HTTP 429 & 503)
- **Timestamp:** 2026-11-24 16:53 EAT
- **Stage / Subsystem:** `pipeline/narration.py` (Gemini 3.8 Flash TTS)
- **Error / Blocker Description:**
  ```text
  HTTP 429: Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 5 RPM.
  HTTP 503: The model is currently experiencing high demand.
  ```
- **Root Cause Analysis:** Google AI Studio's Free Tier enforces a strict 5 requests-per-minute (RPM) ceiling on `gemini-3.8-flash`. Iterating across 9 shots in an unpaced loop instantly exhausts the per-minute quota window.
- **Attempts Made:**
  1. *Attempt 1:* Direct burst loop without delays &rarr; failed with HTTP 429 on shot 5.
  2. *Attempt 2:* Blind retry without rate recognition &rarr; triggered secondary HTTP 503 unavailable responses.
- **Final Resolution / Workaround:**
  - Implemented 3-attempt exponential backoff with a 26-second delay on HTTP 429.
  - Added polite 12-second inter-call pacing between consecutive shot generations to maintain an average throughput of ~4 RPM (comfortably below the 5 RPM ceiling).
- **Preventative Measure:**
  - Enforced SHA-256 content hashing (`narration_{shot_id}.hash`). Completed audio files are permanently cached to disk, ensuring zero redundant quota burn on subsequent pipeline executions.

---

### Failure 02: Prompt Leakage into TTS Audio Output (Meta-Instruction Spoken Verbatim)
- **Timestamp:** 2026-11-24 18:28 EAT
- **Stage / Subsystem:** `pipeline/narration.py` (Gemini 3.8 Flash TTS)
- **Error / Blocker Description:**
  Generated narration audio stems included spoken English instructions (*"Read the following Amharic text aloud with calm, unhurried elder pacing..."*) preceding the Amharic story lines in both general narration and character dialogue.
- **Root Cause Analysis:**
  Unlike LLM chat endpoints that separate meta-instructions from content, the `gemini-3.8-flash-tts` model synthesizes the raw string contents of `contents.parts[0].text` verbatim into speech. Formatting prompt instructions in that field causes the voice synthesizer to read the instruction aloud as dialogue.
- **Attempts Made:**
  - *Identified:* Line 77 had string template `f"Read the following Amharic text aloud...:\n\n{text}"`.
- **Final Resolution / Workaround:**
  - Cleaned the payload to pass only the pure target Amharic string: `{"text": text}`.
  - Re-executed generation with `--force` to overwrite contaminated audio stems with clean native speech.
- **Preventative Measure:**
  - Codified rule: For dedicated TTS endpoints, never embed meta-instructions inside the text payload field; pass strictly the target spoken script.

---

### Failure 03: Raw PCM vs. WAV Container Mismatch Across Model Tiers
- **Timestamp:** 2026-11-25 10:15 EAT
- **Stage / Subsystem:** `pipeline/narration.py` (Multi-model TTS fallback)
- **Error / Blocker Description:**
  `gemini-2.5-flash-preview-tts` returned raw PCM audio bytes without a RIFF WAV container header. Writing raw bytes directly to `.wav` produced an unreadable file with `duration: 0.0s` in standard wave parsers.
- **Root Cause Analysis:**
  While `gemini-3.8-flash-tts` wraps speech in a standard `audio/wav` RIFF container, fallback preview models return raw 24kHz 16-bit mono PCM.
- **Attempts Made:**
  - *Identified:* Checked byte header: found raw audio samples starting immediately without `b'RIFF'`.
- **Final Resolution / Workaround:**
  - Added header inspection: if `not raw_audio.startswith(b"RIFF")`, automatically construct a valid 24,000 Hz, 16-bit, 1-channel WAV container via Python's `wave` module.
- **Preventative Measure:**
  - Standardized audio ingestion pipeline to guarantee container validity regardless of upstream model format differences.

---

### Failure 04: Cloudflare Workers AI FLUX Payload HTTP 400 (Unsupported Root Keys)
- **Timestamp:** 2026-11-25 10:47 EAT
- **Stage / Subsystem:** `pipeline/references.py` & `pipeline/keyframes.py` (`@cf/black-forest-labs/flux-1-schnell`)
- **Error / Blocker Description:**
  ```text
  HTTP 400: {"success":false,"errors":[{"code":10000,"message":"Invalid request body: Extra inputs are not permitted"}]}
  ```
- **Root Cause Analysis:**
  Cloudflare's implementation of FLUX-1-schnell strictly validates its incoming JSON schema and rejects custom root parameters such as `seed`, `num_steps`, or `aspect_ratio`.
- **Attempts Made:**
  - Sent standard Diffusers-style payload with `seed` and `num_steps: 4`.
- **Final Resolution / Workaround:**
  - Stripped all auxiliary parameters and passed strictly `{"prompt": prompt}`. Embedded framing and style constraints directly within the prompt text.
- **Preventative Measure:**
  - Updated API wrapper to keep payloads minimal and schema-compliant with Cloudflare Workers AI specs.

---

### Failure 05: FFmpeg Drawtext Nested Quote Collision & ASS Subtitles Migration
- **Timestamp:** 2026-11-25 12:36 EAT
- **Stage / Subsystem:** `pipeline/assemble.py` (Rough Cut Assembly)
- **Error / Blocker Description:**
  ```text
  [AVFilterGraph] No option name near ' \What one does not know brings much sweat.':fontcolor=white...
  ```
- **Root Cause Analysis:**
  Chaining 18 individual `drawtext` filters with single quotes inside English proverb translations caused quote escaping collisions in FFmpeg's filtergraph parser.
- **Attempts Made:**
  - Attempted multi-layer backslash escaping (`\'` and `\\'`).
- **Final Resolution / Workaround:**
  - Migrated subtitle rendering to an Advanced SubStation Alpha (`.ass`) file using the `subtitles=` filter with direct DirectWrite font rendering of Windows `Nyala`.
- **Preventative Measure:**
  - Standardized all multi-line bilingual subtitle rendering through dedicated ASS files rather than inline filtergraph text strings.
