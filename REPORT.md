# The Heritage Short — AI-Content Generation Challenge
## Written Analytical Report: Technical & Creative Synthesis
**Project:** *The Weight of the Handle (የእጁ ሚስጥር)*  
**Core Narrative:** Traditional Ethiopian Amharic Proverb: *"የማያውቁት ነገር ላብ ያበረክታል"* (*"What one does not know brings much sweat and toil"*).  
**Deliverable Scope:** Assignment 1 (Codebase, Pipeline & Analytical Report) & Assignment 2 (Films, Walkthrough & Post).  
**Repository Location:** `the-heritage-short` (`main` branch)

---

## 1. Project Intent, Persona & Audience Definition

### The Premise
The Heritage Short set out to translate an ancestral Ethiopian proverb into an emotionally resonant, culturally authentic, and technically reproducible 68-second short film. In the rural highlands, an eager apprentice, **Kaleb**, exhausts himself striking rocky furrow soil with brute force. His grandfather, **Ato Berhanu**, steps forward not to scold, but to adjust his hands, demonstrating that the secret lies in balance, fulcrum leverage, and letting the tool's natural momentum do the work.

### Target Audience & Viewing Context
* **Primary Persona:** Ethiopian diaspora youth, second-generation African immigrants, and global folklore enthusiasts who primarily consume vertical short-form video.
* **Viewing Context:** High-velocity vertical mobile feeds (`9:16`, 1080x1920) across YouTube Shorts, Instagram Reels, TikTok, and WhatsApp Status.
* **Single Emotional Takeaway:** Humility before ancestral wisdom—the profound realization that knowledge elevates grueling struggle into effortless grace, ensuring that no honest labor is spent in vain.

---

## 2. Audience Learnings & Iterations (User Tests #1 and #2)

To ensure the production was grounded in real viewer reactions rather than unverified creator assumptions, we conducted two structured user tests with $\ge 3$ audience members:

### User Test #1: The Radio Cut (Narration + Temp Score)
* **Format:** Line-by-line Amharic narration over a placeholder audio drone on a vertical black canvas.
* **Audience Feedback:**
  1. *Prompt Preamble Leakage:* The TTS model inadvertently vocalized instruction preambles (e.g. *"Read the following text..."*).
  2. *Terminology Resonance:* Generic references to farming tools felt detached; listeners asked for the culturally specific Amharic term **"ዶማ" (Doma)**.
  3. *Pacing:* Shot durations needed contraction to allow the music score breathing room.
* **Codebase Changes Applied:**
  - Standardized `pipeline/narration.py` to send pure Ethiopic text without English preambles (Experiment 01).
  - Updated `storyboard.json` narrative text to feature the Doma and adjusted shot pacing to a total duration of 65.50s.

### User Test #2: Near-Final Master Cut
* **Format:** Full master cuts evaluated across mobile phone speakers (iPhone 14, Samsung Galaxy S23) and closed-back headphones.
* **Audience Feedback:**
  1. *Voice Identity Beat:* Listeners strongly commended the voice switch on Shot 6, noting that hearing an older, resonant voice (`Algenib`) for Ato Berhanu immediately signaled ancestral authority.
  2. *Subtitle Visibility:* Gold Amharic on top and white English below rendered with DirectWrite native `Nyala` remained crisp and fully legible inside the mobile safe area.
  3. *Audio Balance:* Dynamic sidechain ducking (-8 to -10 dB) ensured the Begena and Krar strings never competed with the spoken proverb.
* **Codebase Changes Applied:**
  - Upgraded `pipeline/assemble.py` to perform two-pass EBU R128 mastering (`-14.44 LUFS`, True Peak `-0.74 dBFS`) and appended a 2.5s Ethical AI Disclosure End Card.

---

## 3. The Hardest Technical & Creative Problem and Its Resolution

### The Blocker: Visual Identity Drift, Tool Collisions & Cloudflare Rate Caps
Visual consistency across generative image models is notorious for breaking down during tool interaction. In our initial test sets:
1. **Tool Shape Morphed Continuously:** The farming tool morphed from a pickaxe to an axe, to a hoe, and in Shot 3 generated crossed multi-head monstrosities.
2. **Model Trade-offs:** FLUX.1 schnell excelled at capturing raw human exhaustion and facial perspiration, but compressed the landscape and generated forked tool heads. Leonardo AI Phoenix generated breathtaking panoramic terraced hills and intricate cotton weaves on Ato Berhanu’s Gabi, but produced static poses during action shots.
3. **Hard Free-Tier Ceiling:** Cloudflare Workers AI free tier imposes a strict 10,000 daily Neurons ceiling (`AiError: code 4006`), which blocked regenerating all 18 frames repeatedly.

### The Resolution: The Hybrid Curation Engine (`pipeline/curate.py`)
Rather than blindly settling for a single flawed model set or spending paid credits, we engineered a programmatic curation architecture:
* **Algorithmic Asset Mapping:** We built `pipeline/curate.py` to assemble the winning frames from both models based on a 5-pillar rubric:
  - *Leonardo Phoenix:* Selected for wide landscape depth (Shot 1), downward strike physics (Shot 2), traditional Netela/Gabi textile weave (Shot 5), mentorship framing (Shot 6), clean soil turnover (Shot 8), and sunset companionship (Shot 9).
  - *FLUX.1 schnell:* Selected for strained knuckle grip and emotional tension (Shot 3), exhaustion pose (Shot 4), and elder wisdom poise (Shot 7).
* **Automated Traceability:** Generated `outputs/keyframes_curated/curation_manifest.json` recording the exact selection rationale and SHA-256 checksums.
* **Pipeline Integration:** Downstream video rendering (`pipeline/shots.py`) automatically detects and ingests the curated sequence, allowing us to deliver clean master cuts with zero budget.

---

## 4. Suggested Practice Comparison: Instinct vs. Evidence

| Evaluation Angle | Suggested Practice | Outcome | Evidence & Engineering Rationale |
| :--- | :--- | :---: | :--- |
| **Practice that BEAT our instinct** | **Single Golden Reference Sheet Conditioning** | **SUCCESS** | Our initial instinct was to generate unique character reference sheets for every shot's lighting condition. The suggested practice—locking **1 Golden Reference Sheet** per character upfront and concatenating a rigid visual style block—significantly anchored facial geometry, garment palette, and elder-versus-youth contrast across all 9 narrative shots. |
| **Practice that DID NOT beat our instinct** | **Unconstrained Remote GPU Video Generation** | **FAILED (Fallback Won)** | The suggested practice recommended generating all moving shots via remote GPU text-to-video diffusion (Wan 2.2 / HunyuanVideo). In practice, generating fine-grained physical tool mechanics (swinging a doma into rocky soil) resulted in severe hallucinatory morphing, temporal flickering, and 3–5 min remote queue timeouts. Our instinct—deploying a programmatic FFmpeg Ken Burns engine with directional zoom vectors—rendered in **4.6s per shot on CPU**, guaranteed zero temporal distortion, and preserved 100% of the hand/tool anatomy. |

---

## 5. Raising the Ceiling: Frontier vs. Open Benchmark Insights

As part of our exploration beyond the floor, we benchmarked our open-tier, zero-cost production pipeline against frontier commercial alternatives (ElevenLabs, Midjourney v6.1, Runway Gen-3, Suno v4, and Dolby.io):

1. **Cost & Accessibility:** The commercial equivalent cost for this 68s production is **~$6.10 per run**. By leveraging Gemini Flash TTS, Cloudflare Workers AI (FLUX & Leonardo), procedural acoustic audio synthesis, and FFmpeg, our pipeline achieved **$0.00 marginal cost**, making it fully democratized for creators in developing ecosystems.
2. **Cultural Authenticity over Generative Hallucination:** Frontier music generators (Suno/Udio) frequently hallucinate Western harmonies or synthetic pop vocals over dialogue. Our procedural acoustic synthesizer (modeling Karplus-Strong Krar in D minor Tizita, buzzing Begena bass in G major Tizita, Washint flute, and Kebero percussion) maintained strict cultural authenticity and guaranteed **12.74 dB of dynamic crest factor** for vocal clarity.
3. **What We Would Build Next:**
   - Train a custom LoRA on traditional Ethiopian highland agricultural implements (Doma, Maresha, Gabi) to achieve 100% automated single-prompt keyframe generation.
   - Package the pipeline into an Antigravity MCP Server / CLI for non-technical community storytellers to archive oral folklore into broadcast-ready shorts.

---

## 6. Verification & Final Deliverables Checklist

- [x] **Contract Duration:** 68.11s total (65.50s narrative + 2.5s end card), strictly within the 60.0s – 90.0s requirement.
- [x] **Dual Aspect Export:**
  - Vertical Master (`9:16`): `outputs/final/final_master_9_16.mp4` (11.18 MB)
  - Horizontal Master (`16:9`): `outputs/final/final_master_16_9.mp4` (10.27 MB)
- [x] **Audio Standards:** Two-pass `-14.44 LUFS` integrated loudness, True Peak `-0.74 dBFS`, dynamic sidechain ducking (-8 to -10 dB).
- [x] **Subtitles:** Dual Amharic (Gold) & English (White) burned-in subtitles rendered with DirectWrite `Nyala` within safe viewing zones.
- [x] **Ethical AI Card:** 2.5s disclosure end card appended to both master files citing all models used.
- [x] **Reproducibility:** One-command unified runner `python run.py` (with `--dry-run` and `--stage` options).
- [x] **Documentation Complete:** `README.md`, `ARCHITECTURE.md`, `DESIGN.md`, `EXPERIMENTS.md` (10 entries), `FAILURES.md`, `COSTS.md`, `ETHICS.md`, and `CHANGELOG.md`.
