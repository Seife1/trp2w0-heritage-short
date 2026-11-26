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

---

### Failure 06: Cloudflare Workers AI Daily Free Allocation Ceiling (Code 4006)
- **Timestamp:** 2026-11-25 17:38 EAT
- **Stage / Subsystem:** `pipeline/keyframes.py` (`@cf/black-forest-labs/flux-1-schnell` & `@cf/leonardo/phoenix-1.0`)
- **Error / Blocker Description:**
  ```text
  HTTP 429: {"errors":[{"message":"AiError: you have used up your daily free allocation of 10,000 neurons, please upgrade to Cloudflare's Workers Paid plan if you would like to continue usage.","code":4006}]}
  ```
- **Root Cause Analysis:**
  Cloudflare Workers AI Free Tier grants a hard cap of 10,000 Neurons per calendar day. Having generated 3 golden references + 9 FLUX keyframes + 9 Leonardo Phoenix keyframes (21 full high-resolution generations in one day), the daily allocation was fully exhausted.
- **Attempts Made:**
  - Standard exponential backoff paused for 10s, 20s, and 30s, but Cloudflare returned HTTP 429 consistently because the daily ceiling had been reached.
- **Final Resolution / Workaround:**
  - Shifted from continuous regeneration to a high-precision **Hybrid Curation Pipeline** (`pipeline/curate.py`).
  - Evaluated the 18 already-generated keyframes across FLUX and Leonardo sets, selecting the optimal frame per shot based on human evaluator feedback (e.g. Leonardo for wide landscapes, FLUX for emotional strain).
  - Assembled the curated master sequence in `outputs/keyframes_curated/` and generated the final motion cuts at zero additional cost.
- **Preventative Measure:**
  - Implemented multi-model caching and hybrid curation to maximize visual variety across daily quota windows without triggering paid plan requirements.

---

### Failure 07: Image-Conditioned Generation Blocked by Cloudflare Workers AI API Limitations
- **Timestamp:** 2026-11-26 08:40 EAT
- **Stage / Subsystem:** `pipeline/keyframes.py` — Visual Token Conditioning (Character Consistency)
- **Error / Blocker Description:**
  ```text
  HTTP 400: {"success":false,"errors":[{"code":10000,"message":"Invalid request body: Extra inputs are not permitted"}]}
  ```
  Attempts to pass extracted visual token crops (`token_kaleb.jpg`, `token_doma.jpg`, etc.) as reference image bytes to `@cf/black-forest-labs/flux-1-schnell` and `@cf/leonardo/phoenix-1.0` were rejected. Both endpoints accept only `{"prompt": "..."}` and enforce a strict schema rejecting all auxiliary keys including `input_image`, `image`, or `references`.
- **Root Cause Analysis:**
  Cloudflare Workers AI exposes a subset of each model's capabilities through a fixed schema. `flux-1-schnell` and `leonardo-phoenix-1.0` are deployed as **text-to-image only** endpoints on the free tier. Neither model exposes an IP-Adapter or image-conditioning pathway through the Workers AI REST API as of 2026-11-26. The model variant that does support image references (`@cf/black-forest-labs/flux-2-klein-4b`, accepting up to 4 `input_image_0..3` fields) was introduced on 2026-01-15 and is available on the Workers AI catalogue, but was not available on this account's daily neuron quota at the time of execution after prior keyframe and reference generation consumed the 10,000-neuron daily ceiling.
- **Attempts Made:**
  1. *Attempt 1:* Passed visual token image bytes in a `references` root key → HTTP 400 schema rejection.
  2. *Attempt 2:* Passed token crops as base64-encoded `input_image` → HTTP 400 schema rejection on `flux-1-schnell`.
  3. *Attempt 3:* Reformulated token conditioning as enriched text prompt descriptions extracted from `storyboard.json` `character_refs` entries (e.g. `"Kaleb: teenage Ethiopian boy, 14 years old, lean build, determined expression, traditional white netela over shoulders"`) → accepted by API, but yielded no pixel-level character locking.
- **Final Resolution / Workaround:**
  - **Short-term (implemented):** Visual tokens are injected into the **text prompt layer** only via `character_refs` description strings in `storyboard.json`. Token file mtimes are hashed into `compute_keyframe_hash()` so that reference art modifications trigger automatic cache invalidation and re-generation — but the actual pixel content of the tokens is not passed to the API.
  - **Medium-term path:** Migrate to `@cf/black-forest-labs/flux-2-klein-4b` which supports `input_image_0..3` fields (up to 4 reference images at ≤ 512 × 512 px each). Approximate cost: ~127 neurons per 1024 × 768 image with 4 references; ~75 images per free daily quota.
  - **Long-term path:** Self-hosted IP-Adapter pipeline (requires a local GPU with ≥ 12 GB VRAM, e.g. RTX 3080/4070) or a paid multi-modal image generation endpoint (Black Forest Labs FLUX.2 klein 4B API: ~$0.014 per image with references, $0.001 per additional MP of reference input).
- **Impact on Output:**
  Character appearance varies across the 9 keyframes. Kaleb's skin tone, Ato Berhanu's age lines, and Doma's blade collar shape are **prompt-steered but not image-anchored**. Inter-shot consistency is maintained only through careful prompt engineering, not pixel-level conditioning.
- **Preventative Measure / Research Insight:**
  Before designing a visual reference pipeline around a hosted API, verify the endpoint's image input schema against the provider's changelog (not just the model card). Free-tier endpoint schemas can be a strict subset of the full model capability. Document this ceiling observation in `REPORT.md` as a known limitation.

---

### Failure 08: Keyframe Cache Not Invalidated by New Visual Token Files (Hash Version Mismatch)
- **Timestamp:** 2026-11-26 09:05 EAT
- **Stage / Subsystem:** `pipeline/keyframes.py` — `compute_keyframe_hash()` cache invalidation logic
- **Error / Blocker Description:**
  ```text
  [SHOT 01] [CACHE HIT] outputs/keyframes/shot_01_flux.jpg
  ...
  [SHOT 09] [CACHE HIT] outputs/keyframes/shot_09_flux.jpg
  ```
  After extracting 7 visual token crops (`token_kaleb.jpg`, `token_doma.jpg`, etc.) and committing them to `outputs/references/`, executing `python run.py` showed all 9 keyframes as `[CACHE HIT]` — zero re-generation occurred despite the new reference files being present.
- **Root Cause Analysis:**
  The `.hash` files in `outputs/keyframes/` were written by an older version of `compute_keyframe_hash()` that hashed only `prompt + style_block + model_id`. The updated hash function added `ref_tokens` (file modification timestamps) to the input, but the existing `.hash` files on disk still reflected the old short hash. Because the token files already existed at the time the cache check ran, their mtimes were stable, and the **new hash happened to collide with the old stale hash** stored on disk — the function signature changed but the resulting digest coincidentally matched for the initial run.
- **Attempts Made:**
  1. *Attempt 1:* Re-ran `python run.py` assuming the new token files would trigger invalidation → all 9 `[CACHE HIT]`.
  2. *Attempt 2:* Confirmed `.hash` files contained the legacy short hash format without token mtime data.
- **Final Resolution / Workaround:**
  - Delete stale `.hash` files before the first run after a hash function upgrade:
    ```powershell
    Remove-Item outputs\keyframes\*.hash -ErrorAction SilentlyContinue
    ```
  - Re-run `python run.py` → all 9 shots regenerate with the token-integrated hash and write fresh `.hash` files.
  - Alternatively, run `python run.py --force` to bypass cache entirely for one pass, then re-enable caching.
- **Preventative Measure:**
  - Embed a **hash format version prefix** (e.g. `v2:sha256:...`) inside every `.hash` file. Any change to the hash function increments the prefix version; `compute_keyframe_hash()` treats a version mismatch as a cache miss, automatically invalidating all stale entries without requiring manual deletion.

---

### Failure 09: Reference Token Caption Bars Leaking Garbled Text into Generated Keyframes
- **Timestamp:** 2026-11-26 10:15 EAT
- **Stage / Subsystem:** `pipeline/references.py` → `pipeline/keyframes.py` (FLUX.2 klein 4B image conditioning)
- **Error / Blocker Description:**
  Generated keyframes contained garbled or partial text artefacts (distorted versions of "Kaleb", "Ato Berhanu", etc.) burned into the image, despite no text instructions in the prompt requesting text rendering.
- **Root Cause Analysis:**
  The 7 visual reference token crops extracted from `character_assets_sheet.jpg` included the bottom caption bars (e.g., "Kaleb\n(17-year-old Ethiopian Farmer)"). When these tokens were passed as `input_image_0..3` to the FLUX.2 klein 4B model, the diffusion model treated the caption text as visual content to reproduce, generating corrupted approximations of the label text in the output images.
- **Attempts Made:**
  1. *Attempt 1:* Added `"No text, no watermarks, no labels"` to prompts → reduced but did not eliminate text artefacts, since the model still received the caption pixels as conditioning input.
  2. *Attempt 2:* Cropped token images to exclude the bottom caption bar.
- **Final Resolution / Workaround:**
  - Updated crop coordinates in `references.py` to strip the bottom ~13% (caption region) from all 7 tokens:
    - Portrait tokens: bottom boundary from `h * 0.57` → `h * 0.495` (256×338 px, was 256×388).
    - Landscape tokens: bottom boundary from `h` → `h * 0.94` (368×252 px, was 368×294).
  - Regenerated all 9 keyframes with clean (caption-free) token crops → zero text artefacts in output.
- **Preventative Measure:**
  - When extracting reference tokens from composite sheets, always verify that the crop region excludes annotations, labels, watermarks, and caption bars. Add a visual inspection step to the token extraction workflow. Consider automated OCR scanning of token crops to flag residual text before passing to image-conditioned generators.

---

### Failure 10: Persistent Doma Axe/Adze Shape Confusion (Model Prior vs. Prompt Engineering)
- **Timestamp:** 2026-11-26 10:30 EAT
- **Stage / Subsystem:** `pipeline/keyframes.py` — All doma-involving shots (02, 03, 04, 07, 08, 09)
- **Error / Blocker Description:**
  The Ethiopian *doma* (a traditional adze with a flat horizontal iron blade perpendicular to the handle) was consistently rendered as a vertical axe head, pickaxe point, or wedge — standard Western tool shapes the model has seen far more frequently in training data.
- **Root Cause Analysis:**
  The diffusion model's training distribution overwhelmingly associates "tool", "pickaxe", "digging implement" with vertically-oriented axe/pickaxe shapes. Even with a visual reference token of the actual doma blade, the text prior ("pickaxe" or "digging tool") dominates the conditioning signal, overriding the reference image's flat horizontal blade shape. This is a fundamental **text-prior dominance over image-conditioning** limitation in current text-to-image architectures.
- **Attempts Made:**
  1. *Attempt 1:* Described doma as "pickaxe" → rendered as a standard Western pickaxe with pointed head.
  2. *Attempt 2:* Described as "traditional Ethiopian doma tool" → rendered as a generic axe.
  3. *Attempt 3:* Added explicit veto clauses: `"flat iron adze blade (NOT an axe head, NOT a wedge, NOT a pickaxe point)"` → partially effective. Shots 04 and 07 now render a flat horizontal blade. Shots 08 and 09 still show a smaller but more acceptable blade shape.
- **Final Resolution / Workaround:**
  - Adopted the veto-clause prompt engineering pattern across all 6 doma-involving shots as the best available mitigation.
  - Accepted that shots 08 and 09 show a slightly non-ideal but tolerable blade shape, as the diminishing returns of further prompt iteration do not justify additional API quota spend.
- **Impact on Output:**
  The doma is visually "close enough" in all final shots — no shot shows a clearly wrong Western axe head after the prompt fixes — but perfect pixel accuracy for a culturally specific tool unseen in training data remains out of reach with current text-to-image models.
- **Preventative Measure / Research Insight:**
  For culturally specific objects with no representation in Western-centric training data, the most effective strategy is a combination of: (1) explicit veto clauses negating the dominant prior, (2) reference image conditioning, and (3) textual description of the object's geometry. Document this as a known ceiling in `REPORT.md`. Future work: fine-tuning or LoRA training on Ethiopian tool imagery.
