"""
Phase 0 validation: compare Basic Pitch vs pYIN/CREPE note detection on
solo harmonica-family audio, and simulate streaming chunks to estimate
latency/accuracy tradeoffs for the live-listening mode.

This is throwaway research code, not product code — it exists to produce
PHASE0_FINDINGS.md and inform the Phase 1 architecture decision.
"""
import json
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import librosa
import numpy as np

SAMPLES_DIR = Path(__file__).parent.parent / "samples"
RESULTS_DIR = Path(__file__).parent.parent / "results"
SAMPLE_FILES = [
    "marineband1.ogg",
    "meisterklasse1.ogg",
    "blues_harp1.ogg",
    "chromatik_mundharmonika.ogg",
]


@dataclass
class DetectedNote:
    start_s: float
    end_s: float
    pitch_hz: float
    midi: int


@dataclass
class RunResult:
    method: str
    file: str
    wall_time_s: float
    audio_duration_s: float
    notes: list


def hz_to_midi_safe(hz: float) -> int:
    return int(round(librosa.hz_to_midi(hz))) if hz > 0 else -1


def monophonic_filter(note_events: list) -> list:
    """
    Keep one note at a time: when two detected notes overlap, keep whichever
    has higher amplitude and drop the other entirely. Basic Pitch is built
    for polyphonic instruments and happily reports overtones/harmonics as
    separate simultaneous notes; chromatic harmonica is monophonic, so any
    overlap is a detection artifact, not a real chord.
    """
    events = sorted(note_events, key=lambda n: n[0])
    kept = []
    for ev in events:
        start, end, _pitch, amp, _bends = ev
        if kept and start < kept[-1][1]:
            if amp > kept[-1][3]:
                kept[-1] = ev
            # else: drop this overlapping, quieter note
        else:
            kept.append(ev)
    return kept


def run_basic_pitch(path: Path) -> RunResult:
    from basic_pitch.inference import predict

    y, sr = librosa.load(str(path), sr=None, mono=True)
    duration = len(y) / sr

    # Tuned for monophonic chromatic-harmonica audio: default thresholds and
    # full piano frequency range produce heavy over-segmentation and
    # harmonic bleed-through (see PHASE0_FINDINGS.md). Constraining to the
    # instrument's real range and raising onset/frame thresholds cuts note
    # count roughly in half and removes out-of-range artifacts.
    fmin = librosa.note_to_hz("C3")
    fmax = librosa.note_to_hz("C7")

    t0 = time.perf_counter()
    _, _, note_events = predict(
        str(path),
        onset_threshold=0.6,
        frame_threshold=0.4,
        minimum_note_length=100,
        minimum_frequency=fmin,
        maximum_frequency=fmax,
    )
    note_events = monophonic_filter(note_events)
    elapsed = time.perf_counter() - t0

    notes = [
        DetectedNote(
            start_s=float(start),
            end_s=float(end),
            pitch_hz=float(librosa.midi_to_hz(pitch)),
            midi=int(pitch),
        )
        for start, end, pitch, _amp, _bends in note_events
    ]
    return RunResult("basic_pitch", path.name, elapsed, duration, notes)


def run_pyin(path: Path) -> RunResult:
    y, sr = librosa.load(str(path), sr=None, mono=True)
    duration = len(y) / sr

    t0 = time.perf_counter()
    f0, voiced_flag, _voiced_prob = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
    )
    elapsed = time.perf_counter() - t0

    hop_length = 512  # librosa.pyin default
    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)

    notes = []
    cur_midi = None
    cur_start = None
    for i, (t, voiced, freq) in enumerate(zip(times, voiced_flag, f0)):
        midi = hz_to_midi_safe(freq) if voiced and not np.isnan(freq) else None
        if midi != cur_midi:
            if cur_midi is not None:
                notes.append(
                    DetectedNote(
                        start_s=float(cur_start),
                        end_s=float(t),
                        pitch_hz=float(librosa.midi_to_hz(cur_midi)),
                        midi=int(cur_midi),
                    )
                )
            cur_midi = midi
            cur_start = t
    if cur_midi is not None:
        # times[-1] is the start of the last frame, not the clip's end —
        # using it directly would truncate (or zero out) a trailing note
        # still sounding when the audio ends.
        notes.append(
            DetectedNote(
                start_s=float(cur_start),
                end_s=float(duration),
                pitch_hz=float(librosa.midi_to_hz(cur_midi)),
                midi=int(cur_midi),
            )
        )
    # Merge notes shorter than 60ms into neighbors' silence (pYIN frame noise)
    notes = [n for n in notes if (n.end_s - n.start_s) >= 0.06]
    return RunResult("pyin", path.name, elapsed, duration, notes)


def simulate_streaming_chunks(path: Path, chunk_s: float = 0.5) -> dict:
    """
    Simulate a live mic stream by feeding Basic Pitch increasing windows of
    audio (rather than the whole file at once) and measuring how detection
    of early notes changes as more context arrives, plus per-chunk latency.
    This approximates what a streaming/incremental pipeline would face
    without requiring real microphone hardware.
    """
    from basic_pitch.inference import predict
    import soundfile as sf
    import tempfile

    y, sr = librosa.load(str(path), sr=None, mono=True)
    total_duration = len(y) / sr
    chunk_samples = int(chunk_s * sr)

    per_chunk_latency = []
    n_chunks = min(10, int(total_duration / chunk_s))  # cap for runtime
    for i in range(1, n_chunks + 1):
        end_sample = min(i * chunk_samples, len(y))
        window = y[:end_sample]
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            sf.write(tmp.name, window, sr)
            t0 = time.perf_counter()
            predict(tmp.name)
            elapsed = time.perf_counter() - t0
        per_chunk_latency.append(
            {"window_end_s": round(end_sample / sr, 2), "inference_s": round(elapsed, 3)}
        )

    return {
        "file": path.name,
        "chunk_s": chunk_s,
        "per_chunk_latency": per_chunk_latency,
        "mean_inference_s": round(
            float(np.mean([c["inference_s"] for c in per_chunk_latency])), 3
        ),
        "max_inference_s": round(
            float(np.max([c["inference_s"] for c in per_chunk_latency])), 3
        ),
    }


def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    all_results = {"basic_pitch": [], "pyin": [], "streaming_simulation": []}

    for fname in SAMPLE_FILES:
        path = SAMPLES_DIR / fname
        if not path.exists():
            print(f"WARNING: missing sample {path}", file=sys.stderr)
            continue

        print(f"--- {fname} ---")

        bp_result = run_basic_pitch(path)
        print(
            f"  basic_pitch: {len(bp_result.notes)} notes, "
            f"{bp_result.wall_time_s:.2f}s wall time for {bp_result.audio_duration_s:.1f}s audio "
            f"(RTF={bp_result.wall_time_s / bp_result.audio_duration_s:.2f}x)"
        )
        all_results["basic_pitch"].append(asdict(bp_result))

        pyin_result = run_pyin(path)
        print(
            f"  pyin:        {len(pyin_result.notes)} notes, "
            f"{pyin_result.wall_time_s:.2f}s wall time for {pyin_result.audio_duration_s:.1f}s audio "
            f"(RTF={pyin_result.wall_time_s / pyin_result.audio_duration_s:.2f}x)"
        )
        all_results["pyin"].append(asdict(pyin_result))

    # Streaming simulation only on the two longest melodic files
    for fname in ["marineband1.ogg", "blues_harp1.ogg"]:
        path = SAMPLES_DIR / fname
        if not path.exists():
            continue
        print(f"--- streaming simulation: {fname} ---")
        stream_result = simulate_streaming_chunks(path, chunk_s=0.5)
        print(
            f"  mean inference/chunk: {stream_result['mean_inference_s']}s, "
            f"max: {stream_result['max_inference_s']}s (chunk size: 0.5s audio)"
        )
        all_results["streaming_simulation"].append(stream_result)

    out_path = RESULTS_DIR / "phase0_raw_results.json"
    out_path.write_text(json.dumps(all_results, indent=2))
    print(f"\nWrote raw results to {out_path}")


if __name__ == "__main__":
    main()
