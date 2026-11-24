# TODO: The Heritage Short — Complete Self-Contained Playbook & Checklist

**Deadline:** Thursday, 26 November, at 23:59 East Africa Time (EAT)  
**Target:** Build a 60–90 second narrated short film + a reproducible, schema-driven multi-model pipeline (`storyboard.json` -> keyframes -> moving shots -> music -> narration -> FFmpeg assembly).

---

## Quick Reference: Grading Breakdown & Automatic-Zero Gate

> **CRITICAL GATE (AUTOMATIC ZERO ON FILM):** If any real person's face, likeness, or voice appears in the film, their explicit, informed consent (including agreement to the words spoken) **must** be recorded in `ETHICS.md` *before* generating anything of them.

### Assignment 1: `B2W0: AI-Content Generation - Codebase and Report` (100 pts + Mandatory AI Interview)
*Note: Graders read code, text, logs, and Markdown files only—they do NOT open media files in the repo.*
- **Software engineering & reproducibility (20 pts):** Clear stage boundaries around validated `storyboard.json`; input-hash caching so re-runs only regenerate changed shots; retries; zero secrets committed; complete `runs.jsonl`; one documented command runs end-to-end from a clean clone.
- **Documentation (10 pts):** Stranger-friendly `README.md`; `ARCHITECTURE.md` explaining stage contracts, caching, and failure handling.
- **Design thinking & audience (10 pts):** Audience & intent written in `DESIGN.md` *before* generating; notes from **2 user tests** (Radio Cut + Near-Final Cut), each with **>= 3 people** from your target audience; visible storyboard updates from feedback; every shot has a stated reason in `storyboard.json`.
- **Experimentation & iteration (10 pts):** **>= 10 logged experiments** (`Hypothesis -> Change -> Result`) in `EXPERIMENTS.md` with fixed-seed evidence in text/logs.
- **Troubleshooting & persistence (10 pts):** `FAILURES.md` detailing real blockers (quotas, OOM, identity drift, language/TTS errors), what you tried, and fixes/workarounds.
- **Measurement (5 pts):** Measured latency and GPU minutes per stage in `COSTS.md`, list-price equivalent, and frontier comparison (if cohort Slack grants capped access to `Omni Flash`, `Nano Banana`, `Lyria 3.5`).
- **Consent, labelling & licences (5 pts):** Recorded consent, checked model/output licences, and clear labelling plan in `ETHICS.md`.
- **Report: Reflection & audience learning (10 pts):** Candid account tied to repo evidence (what audience said, what changed, hardest problem & solution).
- **Report: Suggested practices tested honestly (10 pts):** One suggested practice that beat your instinct + one that did not, each backed by evidence.
- **Report: Curiosity beyond the floor (10 pts):** Measured insight from optional "Raising the Ceiling" work.

### Assignment 2: `B2W0: AI-Content Generation - Film, Walkthrough and Post` (100 pts, Manual Grade)
- **The film (50 pts):** 60–90s in both `9:16` (primary link) and `16:9` (attachment); clear narration, ducked score, accurate English subtitles, consistent character/style, 2–3s AI end card, story lands for target audience.
- **Walkthrough video (30 pts):** `<= 5 minutes`; explains architecture + 1 hard decision; **live regeneration demo** (edit 1 keyframe prompt or narration line in `storyboard.json`, rerun pipeline, and prove on screen/in logs that *only* that shot regenerated).
- **Public post (20 pts):** Public post written by you (story, why it matters, 1 technical takeaway) with the platform's **AI-generated label enabled**.

---

## Phase 1: Setup, Story, Ethics & Radio Cut (Target: Finish Day 1 / Tuesday)

### 1.1 Environment, Free Stack & Smoke Test
- [ ] **Gemini API (Google AI Studio — free tier, Ethiopia supported):**
  - [ ] Generate API key for `Gemini 3.8 Flash` (script/storyboard), `Gemini 3.8 Flash-Lite` (bulk calls), and `Gemini 3.8 Flash TTS` (narration in 130+ languages incl. Amharic).
- [ ] **Cloudflare Workers AI (Daily free allowance: ~50–170 images):**
  - [ ] Create account and API token for `FLUX.2 klein` (4B is Apache 2.0; 9B is non-commercial—prefer 4B or `FLUX.1 schnell` to keep commercial/open rights clean).
- [ ] **Kaggle & Google Colab (Free GPUs):**
  - [ ] Create & phone-verify Kaggle account (~30 GPU hrs/week on `2x T4`) and configure Google Colab as backup for `Wan 2.2 TI2V-5B` / `HunyuanVideo 1.5` and `ACE-Step 1.5`.
  - [ ] *Note:* Kaggle/Colab sessions time out—design scripts to save outputs incrementally to disk/cloud as each shot finishes.
- [ ] **Coding Agent & Local Tools:**
  - [ ] Install & authenticate `Antigravity CLI` (`agy`) or `OpenCode` (check free model data terms; keep private family details out of endpoints that train on prompts).
  - [ ] Install `FFmpeg` locally (and `Remotion` if rendering React-based animated titles/end card).
- [ ] **Smoke Test:**
  - [ ] Run a 1-call smoke test against each provider and log initial latency/status to `runs.jsonl`.

### 1.2 Repository Structure & Hygiene
- [ ] Initialize a **public** GitHub repository with this exact layout:
  ```text
  ├── README.md            # One-command setup & run, overview, cost summary
  ├── storyboard.json      # Single source of truth: shots, durations, prompts, refs, narration, music cues
  ├── schema/              # JSON Schema validating storyboard.json before every run
  ├── pipeline/            # Modular scripts: script.py, keyframes.py, shots.py, music.py, narration.py, assemble.py
  ├── runs.jsonl           # Append-only log: 1 JSON line per model call (stage, model, params, seed, latency_s, gpu_min, cost_est)
  ├── outputs/             # Generated images, audio, video clips, and final renders
  ├── DESIGN.md            # Audience, intent, User Test #1 & #2 notes, and resulting storyboard diffs
  ├── ARCHITECTURE.md      # Stage contracts, input-hash caching logic, retry & fallback architecture
  ├── EXPERIMENTS.md       # >= 10 structured entries (Hypothesis -> Change -> Result + evidence)
  ├── FAILURES.md          # Chronological failure journal (blocker -> attempts -> fix/workaround)
  ├── COSTS.md             # Measured latency, GPU minutes/stage, list-price equivalent, frontier comparison
  └── ETHICS.md            # Consent records, model/output licences, AI labelling & watermark preservation plan
  ```
- [ ] Add `.env.example` and `.gitignore` (ignore `.env`, API keys, temp caches; ensure **zero secrets** ever enter git history).

### 1.3 Story, Audience & Mandatory Consent Gate
- [ ] **Story & Consultation:** Pick a 60–90s story about a person, place, or proverb that matters to your family. Talk to the person whose story it is.
- [ ] **Consent Gate (`ETHICS.md`):** Record explicit, informed consent for any real person's likeness or voice, plus confirmation of the script lines attributed to them, *before* running image/voice generation.
- [ ] **Licences & Labelling (`ETHICS.md`):**
  - [ ] Document licences: `Wan 2.2` (Apache 2.0), `ACE-Step 1.5` (MIT, commercial output allowed), `FLUX.2 klein 4B` (Apache 2.0) vs `9B` (non-commercial), `Gemini API` terms.
  - [ ] Document AI disclosure plan: platform AI disclosure toggle + 2–3s end card + preserving SynthID/C2PA metadata/watermarks.
  - [ ] Avoid naming living artists in style prompts; describe visual qualities instead (e.g., *"warm golden-hour light, subtle film grain, hand-painted gouache texture"*).
- [ ] **Audience & Intent (`DESIGN.md`):** Write down *who* will watch (persona), *where* they will watch (e.g., vertical phone feed on WhatsApp/YouTube Shorts), and the *single feeling or takeaway* at the end—before generating media.

### 1.4 Storyboard Schema & Contract
- [ ] **Plan Before Prompting:** Draft the story in 3–5 sentences (1 visual beat per sentence). Aim for **8–12 shots** (~6–8s each) and **~130–220 spoken words** total (~2–2.5 words/sec).
- [ ] **Schema (`schema/storyboard.schema.json`):** Enforce required fields per shot: `shot_id`, `reason` (why this shot exists), `duration_s`, `shot_type` (wide/medium/close-up), `character_refs`, `keyframe_prompt`, `motion_prompt`, `seed`, `narration_text`, `music_cue_id`.
- [ ] **Validation:** Make every pipeline stage validate `storyboard.json` against the JSON Schema before executing.

### 1.5 Narration & Radio Cut (Checkpoint 1)
- [ ] **Build `pipeline/narration` (`Gemini 3.8 Flash TTS`):**
  - [ ] Generate narration **line-by-line (one audio file per shot)** in your chosen language so retakes are cheap and exact shot durations are driven by actual speech length.
  - [ ] Use concise style instructions (e.g., *"calm, warm, unhurried"*) rather than constantly switching voices.
  - [ ] Have a native speaker check names and places for pronunciation errors; log any TTS language struggles in `FAILURES.md`.
- [ ] **Assemble Radio Cut:** Lay the line-by-line narration over placeholder temp music on a black screen using `FFmpeg` to test story pacing and lock shot durations.
- [ ] **User Test #1:** Play the Radio Cut to **at least 3 people** from your intended audience (in person or on cohort Slack).
- [ ] **Log & Iterate (`DESIGN.md`):** Record exact feedback and update `storyboard.json` (pacing, word cuts, shot reasons) before generating visuals.

---

## Phase 2: Visuals, Motion & Original Score (Target: Day 2 / Wednesday)

### 2.1 Character & Style Reference Sheet + Keyframes
- [ ] **Lock the Look First:**
  - [ ] Define a fixed **Style Block** (palette, lighting, medium, era) appended verbatim to every keyframe prompt to prevent style drift.
  - [ ] Generate 4+ options for your main character/place and select **1 Golden Reference Sheet** (front/profile/expression) before generating shot keyframes.
- [ ] **Build `pipeline/keyframes` (`Cloudflare Workers AI: FLUX.2 klein / FLUX.1 schnell`):**
  - [ ] Condition every shot keyframe on the Golden Reference Sheet + fixed Style Block.
  - [ ] Compose subjects near the **center of the frame** so both `9:16` (vertical) and `16:9` (horizontal) crops work cleanly from the same source.
  - [ ] Never put text/signs inside generated images (add titles/subtitles in `FFmpeg`/`Remotion`).
  - [ ] Implement **SHA-256 input-hash caching** (hash of prompt + style block + ref image + seed + model params) so re-runs skip unchanged shots, plus exponential-backoff retries.
  - [ ] Inspect every keyframe for face identity, hands, and artifacts *before* spending GPU minutes animating.

### 2.2 Moving Shots (`Image-to-Video` + Smart Quota Management)
- [ ] **Build `pipeline/shots` (`Wan 2.2 TI2V-5B` or `HunyuanVideo 1.5` on Kaggle/Colab):**
  - [ ] **Prompting Rule:** Because the keyframe already defines subject, setting, and lighting, write **motion- and camera-only prompts** (e.g., *"The grandmother slowly turns toward the window, gentle push-in, soft morning breeze in the curtains"*). Avoid contradictory camera cues; use *"fixed camera"* for static shots.
  - [ ] **Quota Strategy:** Draft all shots at **`480p`** in batched runs first; inspect results, then re-render only the approved final shots at **`720p` (24 fps)**.
  - [ ] **Editing & Fallbacks:**
    - [ ] Trim weak first/last `0.5s` of generated clips in assembly if warping/morphing appears at clip boundaries.
    - [ ] Cap retries at **3 attempts per shot**; fall back automatically to **FFmpeg Ken Burns (`zoompan`)** with varied slow pan/zoom directions for any shot that fails or if GPU quota runs dry.
  - [ ] Log every run (including GPU minutes and queue/inference latency) to `runs.jsonl`.

### 2.3 Original Score (`ACE-Step 1.5`)
- [ ] **Spotting Notes (`storyboard.json`):** Define cue start/end times and emotional arc before generating.
- [ ] **Build `pipeline/music` (`ACE-Step 1.5` on Kaggle/Colab):**
  - [ ] Put **tempo (BPM) and key in metadata fields**, NOT in the text caption (avoids contradictions like *"slow ballad"* + fast BPM).
  - [ ] Put style, mood, instruments, texture, and `instrumental` tag in the caption; choose gentle textures without competing lead melodies so narration stays clear.
  - [ ] Generate **30–60s segments** (join sections if needed) and produce **at least 3 score candidates** across varied seeds.
  - [ ] Audition candidates at low volume under narration and document why you chose the winner in `EXPERIMENTS.md`.

### 2.4 Experimentation & Failure Journaling (Checkpoint 2)
- [ ] **Log `>= 10` Structured Experiments (`EXPERIMENTS.md`):** Format every entry as `Hypothesis -> Single Variable Changed (Fixed Seed) -> Measured Result & Decision`.
- [ ] **Maintain `FAILURES.md`:** Document real issues encountered (Kaggle queue/timeout, CUDA OOM, Tigrinya/Amharic TTS mispronunciations, face drift, Cloudflare rate limits) and exact resolutions.
- [ ] **Checkpoint 2 Check:** Verify Rough Cut plays end-to-end with visuals, narration, and chosen score.

---

## Phase 3: Assembly, Testing, Walkthrough & Submission (Target: Day 3 / Thursday)

### 3.1 Programmatic Assembly & Mastering (`pipeline/assemble`)
- [ ] **Pre-level Stems:** Normalize narration and score stems to consistent working levels before mixing.
- [ ] **Cut Picture to Voice:** Trim/time each video clip (or Ken Burns still) to match its shot's narration audio duration.
- [ ] **Sidechain Audio Ducking (`FFmpeg`):**
  - [ ] Duck score automatically beneath narration using `sidechaincompress` (starting baseline: `threshold=0.02:ratio=6:attack=300:release=1500`, tuned by ear).
- [ ] **Subtitles (Burned-In English):**
  - [ ] Format subtitles to **max 2 lines**, **~40 characters per line**, placed safely inside the **`9:16` vertical safe area** (clear of TikTok/Shorts/Reels UI buttons).
- [ ] **Loudness Mastering (`FFmpeg` two-pass `loudnorm`):**
  - [ ] Normalize final mix to **`-14 LUFS`** integrated loudness with **true peak `<= -1 dB`**.
- [ ] **End Card & Dual-Aspect Export:**
  - [ ] Append a **2–3 second end card** explicitly stating the film was made with AI.
  - [ ] Export H.264 video + AAC audio MP4s in both **Vertical (`9:16`)** and **Horizontal (`16:9`)**.

### 3.2 Second Audience Test & One-Command Reproducibility
- [ ] **User Test #2:** Show the near-final cut to **at least 3 people** from your target audience. Test playback on **both a phone speaker and headphones**.
- [ ] **Record Changes (`DESIGN.md`):** Log audience reactions and any final timing, subtitle, or mix adjustments.
- [ ] **Reproducibility Verification:**
  - [ ] Wire a single entry point (`make film` or `python run.py`) that validates `storyboard.json` and runs all stages end-to-end.
  - [ ] Test in a fresh directory/clean clone to verify caching, retries, and clean execution without manual intervention.
- [ ] **Finalize Repo Docs:** Complete `README.md`, `ARCHITECTURE.md`, and `COSTS.md` (include measured latency, GPU minutes, list-price equivalent, and any frontier model benchmark).

### 3.3 Optional "Raising the Ceiling" Extension (10 pts in Report)
- [ ] Pick **one** focused, well-measured extension that produces real insight (quality > quantity):
  - [ ] *Language stress-test:* Adapt narration to Afaan Oromo, Tigrinya, or Somali and document exact model failure points.
  - [ ] *Vocal song:* Generate a lyric song in your language with `ACE-Step 1.5` and timed captions, evaluating pronunciation.
  - [ ] *Open vs. Frontier blind benchmark:* Generate the same shot on open vs. frontier models (`Omni Flash` / `Nano Banana` / `Lyria 3.5` if unlocked on Slack), log cost/latency, and run a **>= 5-person blind preference test**.
  - [ ] *Tooling / Family App / LoRA:* Package pipeline as a CLI/MCP server, build a non-coder family web app, or train a character LoRA and measure identity consistency gains.

### 3.4 Walkthrough Video, Public Post & Final Submission (Due Thu, 26 Nov, 23:59 EAT)
- [ ] **Written Report (PDF / DOCX / public link):** Cover all required prompts:
  1. What you set out to make and for whom.
  2. What you learned from both audience tests (with repo evidence).
  3. The hardest technical/creative problem and how you solved it.
  4. **One suggested practice that beat your instinct** vs. **one that did not** (backed by evidence).
  5. Ceiling work insights and what you would build next.
- [ ] **Public Post:** Publish the film on YouTube/TikTok/Instagram/LinkedIn with the **platform's AI-generated label switched ON**. Write the caption yourself (the story, personal meaning, and 1 engineering takeaway).
- [ ] **Walkthrough Video (`<= 5 minutes`):**
  - [ ] Explain pipeline architecture and stage contracts (`storyboard.json`).
  - [ ] Explain one hard decision you made.
  - [ ] **Live Regeneration Demo:** Edit 1 keyframe prompt or 1 narration line in `storyboard.json`, run your pipeline command, and prove on screen (and via `runs.jsonl` showing a single new call) that **only that shot regenerated** *(you may pause the recording while GPU inference runs)*.
- [ ] **Verify Permissions:** Open every submitted URL in an Incognito/private window to confirm zero login walls.
- [ ] **Submit Assignment 1 (`B2W0: AI-Content Generation - Codebase and Report`):** Public GitHub URL + Report, then review `runs.jsonl`, `EXPERIMENTS.md`, `FAILURES.md`, and `DESIGN.md` ahead of your **AI Interview**.
- [ ] **Submit Assignment 2 (`B2W0: AI-Content Generation - Film, Walkthrough and Post`):** Vertical `9:16` MP4 link (primary) + Horizontal `16:9` MP4 link + Walkthrough video link + Public Post link/screenshot.
