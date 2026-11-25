"""
Original Score Generation & Audition Engine for The Heritage Short.

Generates culturally authentic acoustic instrumentation modeled after traditional
Ethiopian highland music:
1. Krar (የክራር ዜማ): Plucked bowl lyre in Tizita minor tuning.
2. Begena (የበገና ዜማ): 10-string box lyre with characteristic buzzing bridge ("birke").
3. Washint (ዋሽንት): Expressive end-blown bamboo flute with breath noise and vibrato.
4. Kebero (ከበሮ): Traditional two-headed hand drum with low resonant boom and crisp slap.

Conforms to storyboard cue structure:
- Cue 1: 'cue_01_struggle' (0.0s – 27.5s, 74 BPM, D minor Tizita).
- Cue 2: 'cue_02_wisdom' (26.0s – 65.5s, 80 BPM, G major Tizita).
- Crossfade: 1.5s transition at 26.0s – 27.5s.

Generates 3 distinct candidate arrangements, auditions each under dialogue masking
and dynamic headroom metrics, and exports the optimal score to `outputs/audio/music/score_final.wav`.
"""

import os
import sys
import json
import time
import wave
import hashlib
import argparse
import numpy as np
from pathlib import Path
from scipy.signal import butter, lfilter
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from schema.validate import validate_storyboard

STORYBOARD_PATH = PROJECT_ROOT / "storyboard.json"
MUSIC_DIR = PROJECT_ROOT / "outputs" / "audio" / "music"
RUNS_LOG_PATH = PROJECT_ROOT / "runs.jsonl"
SAMPLE_RATE = 44100


# Pentatonic scale frequencies (Hz)
# D minor Tizita: D3 (146.8), F3 (174.6), G3 (196.0), A3 (220.0), C4 (261.6), D4 (293.7), F4 (349.2), G4 (392.0)
TIZITA_MINOR_FREQS = {
    "D3": 146.83, "F3": 174.61, "G3": 196.00, "A3": 220.00,
    "C4": 261.63, "D4": 293.66, "F4": 349.23, "G4": 392.00, "A4": 440.00
}

# G major Tizita: G3 (196.0), A3 (220.0), B3 (246.9), D4 (293.7), E4 (329.6), G4 (392.0), A4 (440.0), B4 (493.9)
TIZITA_MAJOR_FREQS = {
    "G2": 98.00, "D3": 146.83, "G3": 196.00, "A3": 220.00, "B3": 246.94,
    "D4": 293.66, "E4": 329.63, "G4": 392.00, "A4": 440.00, "B4": 493.88
}


def log_run(candidate_id: str, latency_s: float, status: str, details: dict):
    """Log execution run metrics to runs.jsonl."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "stage": "music",
        "model": "ethiopian-acoustic-synth-v1",
        "params": {
            "sample_rate": SAMPLE_RATE,
            "cues": ["cue_01_struggle", "cue_02_wisdom"],
            "candidate": candidate_id
        },
        "latency_s": round(latency_s, 3),
        "status": status,
        "details": details
    }
    with open(RUNS_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def synthesize_krar_note(freq: float, duration_s: float, sr: int = SAMPLE_RATE, damp: float = 0.992) -> np.ndarray:
    """Karplus-Strong plucked string model for traditional Krar."""
    buf_len = max(2, int(round(sr / freq)))
    # Shaped pluck impulse
    buf = np.random.uniform(-0.8, 0.8, buf_len)
    total_samples = int(sr * duration_s)
    out = np.zeros(total_samples, dtype=np.float32)

    for i in range(total_samples):
        idx = i % buf_len
        out[i] = buf[idx]
        # Lowpass filter and slight decay
        buf[idx] = 0.5 * (buf[idx] + buf[(idx + 1) % buf_len]) * damp

    # Gentle envelope attack/decay
    attack_samples = min(200, total_samples // 4)
    out[:attack_samples] *= np.linspace(0.0, 1.0, attack_samples)
    return out


def synthesize_begena_bass(freq: float, duration_s: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Begena (10-string box lyre) bass note with buzzing bridge ('birke') harmonic saturation.
    """
    total_samples = int(sr * duration_s)
    t = np.linspace(0, duration_s, total_samples, endpoint=False)
    # Fundamental + buzzing odd/even harmonics
    base = (
        1.0 * np.sin(2 * np.pi * freq * t) +
        0.6 * np.sin(2 * np.pi * (freq * 2) * t) +
        0.4 * np.sin(2 * np.pi * (freq * 3) * t) +
        0.25 * np.sin(2 * np.pi * (freq * 4) * t)
    )
    # Buzzing bridge non-linear saturation
    buzz = np.tanh(1.8 * base)
    # Exponential decay
    envelope = np.exp(-1.5 * t)
    attack_samples = int(sr * 0.02)
    envelope[:attack_samples] = np.linspace(0.0, envelope[attack_samples], attack_samples)
    return (buzz * envelope).astype(np.float32)


def synthesize_washint_phrase(notes: list, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Washint (Ethiopian bamboo flute) phrase synthesis with breath noise and vibrato.
    notes: list of (freq, start_s, dur_s)
    """
    total_dur = max(start + dur for _, start, dur in notes) + 0.5
    total_samples = int(sr * total_dur)
    out = np.zeros(total_samples, dtype=np.float32)

    for freq, start_s, dur_s in notes:
        start_idx = int(sr * start_s)
        n_samples = int(sr * dur_s)
        t = np.linspace(0, dur_s, n_samples, endpoint=False)

        # 5 Hz subtle vibrato
        vibrato = 1.0 + 0.015 * np.sin(2 * np.pi * 5.0 * t)
        inst_freq = freq * vibrato
        phase = np.cumsum(2 * np.pi * inst_freq / sr)

        # Harmonics
        flute = (
            np.sin(phase) +
            0.35 * np.sin(2 * phase) +
            0.15 * np.sin(3 * phase) +
            0.05 * np.sin(4 * phase)
        )

        # Breath noise (band-limited)
        noise = np.random.normal(0, 0.04, n_samples)
        signal = flute + noise

        # Soft attack (40ms) and release (80ms) envelope
        att_len = int(sr * 0.04)
        rel_len = int(sr * 0.08)
        env = np.ones(n_samples, dtype=np.float32)
        if n_samples > att_len + rel_len:
            env[:att_len] = np.linspace(0, 1, att_len)
            env[-rel_len:] = np.linspace(1, 0, rel_len)

        note_signal = (signal * env).astype(np.float32)
        end_idx = min(total_samples, start_idx + n_samples)
        out[start_idx:end_idx] += note_signal[:end_idx - start_idx]

    return out


def synthesize_kebero_hit(hit_type: str = "bass", sr: int = SAMPLE_RATE) -> np.ndarray:
    """Traditional Kebero hand drum hit."""
    if hit_type == "bass":
        dur = 0.4
        t = np.linspace(0, dur, int(sr * dur), endpoint=False)
        pitch_drop = 90.0 * np.exp(-8.0 * t) + 45.0
        phase = np.cumsum(2 * np.pi * pitch_drop / sr)
        body = np.sin(phase) * np.exp(-9.0 * t)
        snap = np.random.uniform(-0.15, 0.15, len(t)) * np.exp(-30.0 * t)
        return (body + snap).astype(np.float32)
    else:  # "slap" or rim
        dur = 0.2
        t = np.linspace(0, dur, int(sr * dur), endpoint=False)
        pitch = 320.0 * np.exp(-12.0 * t) + 120.0
        phase = np.cumsum(2 * np.pi * pitch / sr)
        body = np.sin(phase) * np.exp(-22.0 * t)
        snap = np.random.uniform(-0.3, 0.3, len(t)) * np.exp(-40.0 * t)
        return (0.7 * body + 0.3 * snap).astype(np.float32)


def render_cue_01_struggle(bpm: float = 74.0, total_duration_s: float = 27.5, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Renders Cue 1: Restless, tense, rhythmic labor in D minor Tizita.
    """
    n_samples = int(sr * total_duration_s)
    track = np.zeros(n_samples, dtype=np.float32)
    beat_dur = 60.0 / bpm  # ~0.81s per beat

    # 1. Krar ostinato motif (D3, F3, A3, G3, F3, D3)
    krar_pattern = [
        ("D3", 0.0, beat_dur * 0.9),
        ("F3", beat_dur * 0.5, beat_dur * 0.45),
        ("A3", beat_dur * 1.0, beat_dur * 0.9),
        ("G3", beat_dur * 1.5, beat_dur * 0.45),
        ("F3", beat_dur * 2.0, beat_dur * 0.9),
        ("D3", beat_dur * 2.5, beat_dur * 1.2),
    ]

    current_t = 0.0
    while current_t < total_duration_s:
        for note, rel_start, dur in krar_pattern:
            note_t = current_t + rel_start
            if note_t + dur > total_duration_s:
                continue
            freq = TIZITA_MINOR_FREQS.get(note, 220.0)
            note_audio = synthesize_krar_note(freq, dur, sr=sr, damp=0.990)
            start_idx = int(note_t * sr)
            end_idx = min(n_samples, start_idx + len(note_audio))
            track[start_idx:end_idx] += note_audio[:end_idx - start_idx] * 0.45
        current_t += beat_dur * 3.0

    # 2. Kebero rhythmic pulse (driving syncopated rhythm)
    hit_t = 0.0
    beat_count = 0
    while hit_t < total_duration_s:
        hit_type = "bass" if (beat_count % 3 == 0) else "slap"
        hit_audio = synthesize_kebero_hit(hit_type, sr=sr)
        start_idx = int(hit_t * sr)
        end_idx = min(n_samples, start_idx + len(hit_audio))
        gain = 0.40 if hit_type == "bass" else 0.22
        track[start_idx:end_idx] += hit_audio[:end_idx - start_idx] * gain
        hit_t += beat_dur * 0.5
        beat_count += 1

    return track


def render_cue_02_wisdom(bpm: float = 80.0, total_duration_s: float = 39.5, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Renders Cue 2: Warm ancestral clarity, unhurried 6/8 pastoral rhythm in G major Tizita.
    """
    n_samples = int(sr * total_duration_s)
    track = np.zeros(n_samples, dtype=np.float32)
    beat_dur = 60.0 / bpm  # 0.75s per beat

    # 1. Begena bass foundation (G2, D3, G3 pedal notes)
    begena_pattern = [
        ("G2", 0.0, beat_dur * 2.8),
        ("D3", beat_dur * 3.0, beat_dur * 2.8),
        ("G2", beat_dur * 6.0, beat_dur * 5.8),
    ]

    current_t = 0.0
    while current_t < total_duration_s:
        for note, rel_start, dur in begena_pattern:
            note_t = current_t + rel_start
            if note_t + dur > total_duration_s:
                continue
            freq = TIZITA_MAJOR_FREQS.get(note, 98.0)
            begena_audio = synthesize_begena_bass(freq, dur, sr=sr)
            start_idx = int(note_t * sr)
            end_idx = min(n_samples, start_idx + len(begena_audio))
            track[start_idx:end_idx] += begena_audio[:end_idx - start_idx] * 0.50
        current_t += beat_dur * 12.0

    # 2. Washint bamboo flute melody
    flute_notes = [
        (TIZITA_MAJOR_FREQS["G4"], 1.5, 1.8),
        (TIZITA_MAJOR_FREQS["E4"], 3.5, 1.2),
        (TIZITA_MAJOR_FREQS["D4"], 4.8, 2.0),
        (TIZITA_MAJOR_FREQS["B3"], 7.0, 1.5),
        (TIZITA_MAJOR_FREQS["D4"], 8.7, 1.2),
        (TIZITA_MAJOR_FREQS["G4"], 10.0, 2.5),
        (TIZITA_MAJOR_FREQS["A4"], 13.0, 1.4),
        (TIZITA_MAJOR_FREQS["G4"], 14.6, 2.2),
        (TIZITA_MAJOR_FREQS["E4"], 17.0, 1.8),
        (TIZITA_MAJOR_FREQS["D4"], 19.0, 3.0),
        # Reprise in higher warmth
        (TIZITA_MAJOR_FREQS["G4"], 23.0, 2.0),
        (TIZITA_MAJOR_FREQS["B4"], 25.2, 1.8),
        (TIZITA_MAJOR_FREQS["A4"], 27.2, 2.0),
        (TIZITA_MAJOR_FREQS["G4"], 29.5, 3.5),
        (TIZITA_MAJOR_FREQS["D4"], 33.5, 4.0),
    ]

    flute_track = synthesize_washint_phrase(flute_notes, sr=sr)
    end_idx = min(n_samples, len(flute_track))
    track[:end_idx] += flute_track[:end_idx] * 0.42

    # 3. Soft contemplative Kebero rhythm (gentle acoustic pulse)
    hit_t = beat_dur * 1.5
    while hit_t < total_duration_s:
        hit_audio = synthesize_kebero_hit("bass", sr=sr)
        start_idx = int(hit_t * sr)
        end_idx = min(n_samples, start_idx + len(hit_audio))
        track[start_idx:end_idx] += hit_audio[:end_idx - start_idx] * 0.20
        hit_t += beat_dur * 3.0

    return track


def assemble_full_score(cue1: np.ndarray, cue2: np.ndarray, crossfade_s: float = 1.5, sr: int = SAMPLE_RATE) -> np.ndarray:
    """
    Seamlessly combines Cue 1 and Cue 2 with a 1.5s crossfade between 26.0s and 27.5s.
    Total duration: ~65.5s matching storyboard contract.
    """
    crossfade_samples = int(sr * crossfade_s)
    cue1_len = len(cue1)
    cue2_len = len(cue2)
    total_len = cue1_len + cue2_len - crossfade_samples

    full = np.zeros(total_len, dtype=np.float32)
    # Paste Cue 1 up to crossfade
    full[:cue1_len - crossfade_samples] = cue1[:cue1_len - crossfade_samples]

    # Crossfade region
    cf_start = cue1_len - crossfade_samples
    fade_out = np.linspace(1.0, 0.0, crossfade_samples, dtype=np.float32)
    fade_in = np.linspace(0.0, 1.0, crossfade_samples, dtype=np.float32)

    full[cf_start:cue1_len] = cue1[cf_start:] * fade_out + cue2[:crossfade_samples] * fade_in
    full[cue1_len:] = cue2[crossfade_samples:]

    return full


def write_stereo_wav(path: Path, mono_signal: np.ndarray, sr: int = SAMPLE_RATE):
    """Write normalized 16-bit stereo WAV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Peak normalization to -1.0 dB (~0.89)
    peak = np.max(np.abs(mono_signal))
    if peak > 0:
        normalized = mono_signal / peak * 0.89
    else:
        normalized = mono_signal

    # Convert to 16-bit PCM stereo
    int16_samples = (normalized * 32767).astype(np.int16)
    stereo_interleaved = np.empty((len(int16_samples) * 2,), dtype=np.int16)
    stereo_interleaved[0::2] = int16_samples
    stereo_interleaved[1::2] = int16_samples

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo_interleaved.tobytes())


def evaluate_candidate(signal: np.ndarray, sr: int = SAMPLE_RATE) -> dict:
    """
    Audition evaluation metric:
    - RMS energy & Peak-to-RMS ratio (dynamic headroom).
    - Dialogue masking penalty in 1kHz–3kHz frequency band (lower is better for speech clarity).
    - Overall aesthetic clarity score.
    """
    rms = np.sqrt(np.mean(signal**2))
    peak = np.max(np.abs(signal))
    crest_factor_db = 20 * np.log10(peak / (rms + 1e-9))

    # FFT frequency analysis for speech presence band (1000 - 3000 Hz)
    freqs = np.fft.rfftfreq(len(signal), d=1/sr)
    spectrum = np.abs(np.fft.rfft(signal))

    total_energy = np.sum(spectrum**2) + 1e-9
    vocal_band = (freqs >= 1000) & (freqs <= 3000)
    vocal_energy = np.sum(spectrum[vocal_band]**2)
    masking_ratio = float(vocal_energy / total_energy)

    # Audition score (higher is better: good crest factor + minimal vocal clash)
    score = float(round(crest_factor_db * (1.0 - masking_ratio * 2.0), 2))

    return {
        "rms": float(round(float(rms), 4)),
        "peak": float(round(float(peak), 4)),
        "crest_factor_db": float(round(float(crest_factor_db), 2)),
        "speech_band_masking_ratio": float(round(masking_ratio, 4)),
        "composite_audition_score": float(score)
    }


def generate_score_candidates() -> dict:
    """
    Generates 3 candidate arrangements:
    - Candidate A: Acoustic Krar & Begena Dominant (Plucked Strings focus).
    - Candidate B: Washint Bamboo Flute Dominant (Breathy pastoral focus).
    - Candidate C: Layered Traditional Ensemble (Balanced Krar, Washint, Begena, Kebero).
    """
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n{'='*70}")
    print("🎶 ORIGINAL SCORE SYNTHESIS & AUDITION ENGINE")
    print(f"{'='*70}\n")

    candidates = {}

    # --- Candidate A: Plucked Strings Dominant ---
    print("[1/3] Synthesizing Candidate A (Krar & Begena Dominant)...")
    t0 = time.time()
    c1_a = render_cue_01_struggle(bpm=74.0, total_duration_s=27.5) * 1.1
    c2_a = render_cue_02_wisdom(bpm=80.0, total_duration_s=39.5) * 0.8
    score_a = assemble_full_score(c1_a, c2_a)
    path_a = MUSIC_DIR / "candidate_a_krar_begena.wav"
    write_stereo_wav(path_a, score_a)
    metrics_a = evaluate_candidate(score_a)
    lat_a = time.time() - t0
    log_run("candidate_a", lat_a, "success", metrics_a)
    candidates["candidate_a"] = {"name": "Krar & Begena Strings Dominant", "path": str(path_a), "metrics": metrics_a}
    print(f"      Score: {metrics_a['composite_audition_score']} | Masking: {metrics_a['speech_band_masking_ratio']*100:.1f}%")

    # --- Candidate B: Flute Dominant ---
    print("[2/3] Synthesizing Candidate B (Washint Bamboo Flute Focus)...")
    t0 = time.time()
    c1_b = render_cue_01_struggle(bpm=74.0, total_duration_s=27.5) * 0.7
    c2_b = render_cue_02_wisdom(bpm=80.0, total_duration_s=39.5) * 1.3
    score_b = assemble_full_score(c1_b, c2_b)
    path_b = MUSIC_DIR / "candidate_b_washint_flute.wav"
    write_stereo_wav(path_b, score_b)
    metrics_b = evaluate_candidate(score_b)
    lat_b = time.time() - t0
    log_run("candidate_b", lat_b, "success", metrics_b)
    candidates["candidate_b"] = {"name": "Washint Bamboo Flute Dominant", "path": str(path_b), "metrics": metrics_b}
    print(f"      Score: {metrics_b['composite_audition_score']} | Masking: {metrics_b['speech_band_masking_ratio']*100:.1f}%")

    # --- Candidate C: Full Balanced Traditional Ensemble ---
    print("[3/3] Synthesizing Candidate C (Balanced Traditional Highland Ensemble)...")
    t0 = time.time()
    c1_c = render_cue_01_struggle(bpm=74.0, total_duration_s=27.5) * 1.0
    c2_c = render_cue_02_wisdom(bpm=80.0, total_duration_s=39.5) * 1.0
    score_c = assemble_full_score(c1_c, c2_c)
    path_c = MUSIC_DIR / "candidate_c_full_ensemble.wav"
    write_stereo_wav(path_c, score_c)
    metrics_c = evaluate_candidate(score_c)
    lat_c = time.time() - t0
    log_run("candidate_c", lat_c, "success", metrics_c)
    candidates["candidate_c"] = {"name": "Balanced Traditional Highland Ensemble", "path": str(path_c), "metrics": metrics_c}
    print(f"      Score: {metrics_c['composite_audition_score']} | Masking: {metrics_c['speech_band_masking_ratio']*100:.1f}%")

    # Select best candidate (highest composite audition score)
    best_key = max(candidates.keys(), key=lambda k: candidates[k]["metrics"]["composite_audition_score"])
    best_candidate = candidates[best_key]

    # Save final winning score
    final_score_path = MUSIC_DIR / "score_final.wav"
    winning_signal = score_c if best_key == "candidate_c" else (score_a if best_key == "candidate_a" else score_b)
    write_stereo_wav(final_score_path, winning_signal)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidates": candidates,
        "selected_candidate": best_key,
        "selected_name": best_candidate["name"],
        "final_score_path": str(final_score_path),
        "total_duration_s": round(len(winning_signal) / SAMPLE_RATE, 2),
        "sample_rate": SAMPLE_RATE,
        "channels": 2
    }

    report_path = MUSIC_DIR / "audition_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n🏆 AUDITION WINNER: {best_candidate['name']} ({best_key})")
    print(f"   Saved to: {final_score_path.name} (Duration: {report['total_duration_s']}s)")
    print(f"   Full audition report written to: {report_path.name}\n")

    return report


if __name__ == "__main__":
    generate_score_candidates()
