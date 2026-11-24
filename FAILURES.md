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
