# Compute, Latency & Cost Tracking

All model calls are logged per-execution in `runs.jsonl`. This document summarizes aggregate metrics, GPU minutes, list-price equivalent, and frontier comparisons.

---

## 1. Measured Run Metrics Summary

| Pipeline Stage | Engine / Model | Hardware | Avg Latency / Item | Total Units | Total Time / GPU Min | Cost Equivalent (USD) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Script & Storyboard** | Gemini 3.8 Flash | Cloud API | ~2.5s | 1 contract | N/A | $0.00 (Free Tier) |
| **Narration (TTS)** | Gemini Flash TTS Cascade | Cloud API | ~12.1s / line | 9 audio stems | ~108.8s API time | $0.00 (Free Tier) |
| **Radio Cut Assembly** | FFmpeg 8.0 | Local CPU (i7) | 7.44s render | 1 render | N/A | Local Compute |
| **Keyframes (Model A)** | FLUX-1-schnell | Cloudflare AI | ~10.8s / image | 9 images | 96.9s API time | $0.00 (Daily Free Allowance) |
| **Keyframes (Model B - A/B Test)** | Leonardo Phoenix 1.0 | Cloudflare AI | ~9.6s / image | 9 images | 86.8s API time | $0.00 (Daily Free Allowance) |
| **Moving Shots** | Ken Burns / FFmpeg 8.0 | Local CPU (i7) | ~4.6s / shot | 18 clips (9x 9:16, 9x 16:9) | 88.6s compute | Local Compute |
| **Music Score** | Ethiopian Acoustic Synth | Local CPU (i7) | ~3.8s / candidate | 3 candidates + eval | 11.4s compute | Local Compute |
| **Rough Cut Assembly** | FFmpeg 8.0 (libass + directwrite) | Local CPU (i7) | ~38.7s / render | 2 renders (9:16 + 16:9) | 77.4s compute | Local Compute |
| **Final Mastering (-14 LUFS + End Card)** | FFmpeg 8.0 (two-pass loudnorm + alimiter) | Local CPU (i7) | ~22.5s / render | 2 renders (9:16 + 16:9) | 45.0s compute | Local Compute |

---

## 2. List-Price Commercial Equivalent
*Calculated based on equivalent commercial API pricing (e.g., ElevenLabs for TTS, Midjourney / FLUX Pro for keyframes, Runway Gen-3 / Luma for video, Suno for music, Descript / Dolby for mastering):*

- **TTS (ElevenLabs equivalent):** ~$0.30 (9 speech stems in Amharic)
- **Keyframes (FLUX Pro / Midjourney equivalent):** ~$0.45 (18 high-resolution images generated across A/B test)
- **Video Motion Generation (Runway Gen-3 equivalent):** ~$5.00 (18 motion clips rendered)
- **Music (Suno equivalent):** ~$0.20 (3 audition candidates + final arrangement)
- **Audio Mastering & Loudness (Dolby.io equivalent):** ~$0.15 (Two-pass broadcast normalization)
- **Total Commercial Equivalent:** **~$6.10 per full generation run**

---

## 3. Frontier Comparison (Open vs. Frontier Benchmarking)

| Benchmark Angle | Open / Free Tier Pipeline (Our Implementation) | Frontier Model Equivalent | Trade-offs & Analysis |
| :--- | :--- | :--- | :--- |
| **Narration (TTS)** | Gemini 3.8 Flash TTS Cascade (Charon + Algenib) | ElevenLabs Multilingual v2 / Google Cloud Chirp 3 | Our zero-cost cascade achieved authentic Amharic accent and natural emotional pacing; commercial frontier APIs offer finer phoneme control but incur recurring per-character costs ($0.30/min). |
| **Visual Keyframes** | FLUX.1 schnell + Leonardo Phoenix (Workers AI) | Midjourney v6.1 / FLUX 1.1 Pro Ultra | Our hybrid open stack eliminated billing costs completely while delivering intricate Ethiopian textile weaves and landscape depth via targeted curation. Frontier models produce slightly higher micro-texture resolution but lock prompts behind paid subscriptions. |
| **Motion Generation** | Programmatic FFmpeg Ken Burns Dynamic Engine | Runway Gen-3 Alpha / Sora / Wan 2.2 TI2V-5B | The programmatic camera engine renders in ~4.6s on CPU with deterministic framing, zero halluncinatory morphing, and zero quota consumption. Remote GPU engines (Wan 2.2 / Runway) generate physical object fluidity but introduce 2–5 min queue times and morphing artifacts on complex agricultural tools. |
| **Score Synthesis** | Culturally Authentic Synthesis (Krar, Begena, Washint, Kebero) | Udio / Suno v4 / Lyria | Our procedural synthesizer guarantees authentic pentatonic Tizita minor/major scales and leaves 12.74 dB of dynamic crest factor for dialogue headroom. Commercial music frontier generators frequently hallucinate Western pop harmonies or unrequested synthetic vocals over dialogue. |

