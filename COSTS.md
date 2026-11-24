# Compute, Latency & Cost Tracking

All model calls are logged per-execution in `runs.jsonl`. This document summarizes aggregate metrics, GPU minutes, list-price equivalent, and frontier comparisons.

---

## 1. Measured Run Metrics Summary

| Pipeline Stage | Engine / Model | Hardware | Avg Latency / Item | Total Units | Total Time / GPU Min | Cost Equivalent (USD) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Script & Storyboard** | Gemini 3.8 Flash | Cloud API | ~2.5s | 1 call | N/A | $0.00 (Free Tier) |
| **Narration (TTS)** | Gemini 3.8 Flash TTS | Cloud API | ~1.8s / line | 8–12 lines | N/A | $0.00 (Free Tier) |
| **Keyframes** | FLUX.2 klein / schnell | Cloudflare AI | ~3.5s / img | 8–12 images | N/A | $0.00 (Daily Free Allowance) |
| **Moving Shots** | Wan 2.2 TI2V-5B | Kaggle 2x T4 | ~120s / shot | 8–12 shots | ~20 GPU min | $0.00 (Weekly Free Quota) |
| **Music Score** | ACE-Step 1.5 | Kaggle 2x T4 | ~45s / track | 3 candidates | ~2.5 GPU min | $0.00 (Weekly Free Quota) |
| **Assembly & Master** | FFmpeg | Local CPU | ~15s | 2 renders | N/A | Local Compute |
| **TOTAL** | | | | | **~25 GPU min** | **$0.00 Actual Cost** |

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
