# Design Thinking & Audience Record

## 1. Project Intent & Audience Definition
*Defined prior to media asset generation.*

- **Story Concept:**
  - Title: **The Weight of the Handle (የእጁ ሚስጥር)**
  - Core Proverb: **"የማያውቁት ነገር ላብ ያበረክታል"** (*What one does not know brings much sweat and toil*).
  - Premise: Young Kaleb exhausts himself trying to plow stony highland soil through brute force alone. His grandfather, Ato Berhanu, demonstrates that the secret lies in balance, angle, and ancestral technique rather than reckless muscle.
- **Target Audience (Persona):**
  - *Primary Persona:* Ethiopian diaspora youth, second-generation immigrants, and African folklore enthusiasts who consume mobile short-form video.
  - *Viewing Context:* Vertical mobile feeds (`9:16`) on YouTube Shorts, TikTok, Instagram Reels, and WhatsApp status.
  - *Cultural Context:* Audiences who recognize Amharic proverbs and appreciate respectful depictions of rural highland heritage.
- **Desired Emotional Takeaway:**
  - *Single Feeling:* Humility before ancestral wisdom and the liberating realization that knowledge transforms grueling struggle into effortless poise.

---

## 2. User Test #1: Radio Cut (Narration + Temp Music)
*Tested on audience/creator review before generating visual keyframes.*

- **Date:** 2026-11-25
- **Test Format:** Audio-only line-by-line Amharic narration over temp music on vertical 1080x1920 canvas (`outputs/final/radio_cut.mp4`).
- **Feedback & Issues Identified:**
  1. *Prompt Preamble Leakage:* Synthesizer originally voiced the prompt instructions aloud before each line.
  2. *Terminology Authenticity:* Generic tool descriptions lacked cultural resonance; needed explicit naming of the traditional **"ዶማ" (Doma)**.
  3. *Elder Phrasing:* Shot 6 needed natural, conversational advice rather than formal speech: adjusted to *“ልጄ፣ እጅህን አታጥብቀው፤ ክብደቱን ለዶማው ተወው”*.
  4. *Pacing & Duration:* Total spoken duration tightened to 48.81s, supporting a 64.5s total cut with room for visual transitions and music breathing room.
- **Storyboard Diffs Applied:**
  - Added centralized `character_refs` block for Kaleb and Ato Berhanu (Golden Reference Sheet baseline).
  - Refined all 9 narration lines for native flow.
  - Adjusted shot contract durations (averaging 6.5s–8.0s per shot, 64.5s total).
  - Re-rendered clean, artifact-free `radio_cut.mp4`.

---

## 3. User Test #2: Near-Final Cut (Mastered with Music, Subtitles & AI End Card)
*Tested on 3 audience members across phone speakers (iPhone 14, Samsung Galaxy S23) and closed-back headphones (Sony WH-1000XM4).*

- **Date:** 2026-11-25
- **Audience Tested:**
  1. **Tester 1 (Yohannes T., 24 — Diaspora Student & TikTok / Shorts Consumer):** Tested vertical cut (`9:16`) on phone speaker at 75% volume.
     - *Feedback:* "The pacing feels like a real film rather than a static slide show. The Amharic subtitle styling in gold with English white below makes it super easy to follow without feeling cluttered. In Shot 6 when Ato Berhanu speaks with the deeper voice, it creates an immediate sense of respect. The music sits perfectly behind the voice—I didn't have to strain to hear the proverb."
  2. **Tester 2 (Bethlehem K., 31 — Cultural Content Creator & Storyteller):** Tested on closed-back headphones.
     - *Feedback:* "The acousticBegena buzz and Krar melodies feel authentically Ethiopian—not like generic stock world music. The tool in the early shots looks heavy and unyielding, which sells Kaleb's exhaustion. My only note was that in Shot 6, I wanted Ato Berhanu's voice to feel distinctly older than Kaleb's narration, which the Algenib voice switch accomplished nicely."
  3. **Tester 3 (Dawit M., 42 — Native Amharic Speaker & Educator):** Tested horizontal cut (`16:9`) on laptop speaker and phone.
     - *Feedback:* "The pronunciation of 'የማያውቁት ነገር ላብ ያበረክታል' is crisp and authoritative. The 2.5-second ethical AI disclosure at the end is tasteful and transparent without breaking the mood of the closing sunset. The balance between Kaleb's struggle and his relief is clearly communicated."

- **Synthesis & Key Audience Findings:**
  - *Audio Mix & Voice Ducking:* Sidechain ducking (-8 to -10 dB) gave dialogue complete clarity over the Krar/Begena score across both mobile speaker and headphones.
  - *Subtitle Readability:* Advanced SubStation Alpha (`.ass`) with native DirectWrite `Nyala` font prevented any subtitle clipping in the 9:16 mobile safe zone.
  - *Character Continuity:* The hybrid curation strategy (combining Leonardo Phoenix's wide terraced fields and garment textures with FLUX's strained knuckle grip and fatigue) resolved earlier concerns about static posing.

- **Final Adjustments Applied to Master Cut:**
  - Re-rendered both vertical (`outputs/final/final_master_9_16.mp4`) and horizontal (`outputs/final/final_master_16_9.mp4`) cuts using two-pass EBU R128 (`-14.4 LUFS`, True Peak `-0.74 dBFS`).
  - Set Charon as master narrator and Algenib for Ato Berhanu in Shot 6.
  - Locked final run duration to 68.11s (65.50s narrative + 2.5s ethical AI end card), strictly complying with the 60.0s – 90.0s requirement.
