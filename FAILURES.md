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
