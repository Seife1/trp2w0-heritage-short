# Compute, Latency & Cost Tracking

All model calls are logged per-execution in `runs.jsonl`. This document summarizes aggregate metrics, GPU minutes, list-price equivalent, and frontier comparisons.

---

## 1. Measured Run Metrics Summary

| Pipeline Stage | Engine / Model | Hardware | Avg Latency / Item | Total Units | Total Time / GPU Min | Cost Equivalent (USD) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Script & Storyboard** | Gemini 3.8 Flash | Cloud API | ~2.5s | 1 contract | N/A | $0.00 (Free Tier) |
| **Narration (TTS)** | Gemini Flash TTS Cascade | Cloud API | ~12.1s / line | 9 audio stems | ~108.8s API time | $0.00 (Free Tier) |
| **Radio Cut Assembly** | FFmpeg 8.0 | Local CPU (i7) | 7.44s render | 1 render | N/A | Local Compute |
| **Keyframes** | FLUX-1-schnell | Cloudflare AI | ~10.8s / image | 9 images | 96.9s API time | $0.00 (Daily Free Allowance) |
| **Moving Shots** | Ken Burns / FFmpeg 8.0 | Local CPU (i7) | ~4.6s / shot | 18 clips (9x 9:16, 9x 16:9) | 88.6s compute | Local Compute |
| **Music Score** | Ethiopian Acoustic Synth | Local CPU (i7) | ~3.8s / candidate | 3 candidates + eval | 11.4s compute | Local Compute |
| **Final Assembly** | FFmpeg | Local CPU | Pending | 2 renders | N/A | Local Compute |

---

## 2. List-Price Commercial Equivalent
*Calculated based on equivalent commercial API pricing (e.g., ElevenLabs for TTS, Midjourney / FLUX Pro for keyframes, Runway Gen-3 / Luma for video, Suno for music):*

- **TTS (ElevenLabs equivalent):** ~$0.30
- **Keyframes (FLUX Pro equivalent):** ~$0.40
- **Video Generation (Runway Gen-3 equivalent):** ~$5.00
- **Music (Suno equivalent):** ~$0.20
- **Total Commercial Equivalent:** **~$5.90 per full generation run**

---

## 3. Frontier Comparison (Optional Extension)
*(To be populated if benchmarking open models vs. frontier equivalents such as Omni Flash / Nano Banana / Lyria 3.5)*
