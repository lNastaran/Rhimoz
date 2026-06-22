# Phase 0 findings: pitch-detection feasibility for chromatic harmonica

## Question being answered

Can an existing, off-the-shelf pitch-detection model reach acceptable
accuracy and latency on real harmonica-family audio, both file-based and
simulated-streaming, without training anything custom?

## Setup

- Python 3.11 venv (`research/phase0/.venv`), managed via `uv` since Homebrew
  on this machine isn't user-writable and TensorFlow/Basic Pitch don't yet
  support Python 3.14.
- Backbones compared: **Basic Pitch** (Spotify, CoreML backend on this Apple
  Silicon Mac) vs **pYIN** (librosa).
- Test audio: 4 CC BY-SA/GFDL clips from Wikimedia Commons (see
  `samples/ATTRIBUTION.md`) — 3 diatonic harmonica melodic phrases used as a
  timbre proxy, 1 short genuine chromatic-harmonica chord clip. True
  permissively-licensed *chromatic* melodic recordings weren't findable
  without creating a Freesound account, which was out of scope here.
- Methodology was reviewed by one subagent (static code review) and executed
  independently by a second subagent (ran the script, sanity-checked output)
  before any tuning — see "What the review caught" below.

## Result 1: raw/default output is not usable as-is

With Basic Pitch's default thresholds and full piano frequency range:

| File | Duration | Notes detected | Plausible rate? |
|---|---|---|---|
| marineband1.ogg | 53.9s | 484 | No — ~9/s on a melodic phrase |
| meisterklasse1.ogg | 40.4s | 406 | No |
| blues_harp1.ogg | 43.9s | 436 | No |
| chromatik_mundharmonika.ogg | 8.9s | 64 | Expected (it's a chord clip) |

The independent test subagent flagged the real problem: this wasn't
random noise, it was **systematic harmonic bleed-through** — Basic Pitch
(built for polyphonic instruments) was reporting a harmonica note's own
overtones as separate simultaneous notes, plus a long tail of notes outside
the chromatic harmonica's real range (MIDI 48-96 / C3-C7): 86-217 out of
404-484 notes per file were out-of-range.

## Result 2: harmonica-aware constraints fix it

Two changes, both informed by the fact that chromatic harmonica is
**monophonic with a known, narrow pitch range** — not generic tuning, but
encoding what we already know about the instrument:

1. Constrain `minimum_frequency`/`maximum_frequency` to C3-C7, raise
   `onset_threshold` (0.5→0.6) and `frame_threshold` (0.3→0.4).
2. Add a monophonic post-filter: when two detected notes overlap in time,
   keep the higher-amplitude one and drop the other (harmonica can't play
   two pitches independently, so any overlap is a detection artifact).

After both:

| File | Notes detected | Notes/sec | Out-of-range | Overlapping pairs |
|---|---|---|---|---|
| marineband1.ogg | 160 | 3.0 | 0 | 0 |
| meisterklasse1.ogg | 107 | 2.6 | 0 | 0 |
| blues_harp1.ogg | 88 | 2.0 | 0 | 0 |
| chromatik_mundharmonika.ogg | 15 | — | 0 | 0 |

Note rate and pitch range are now consistent with a plausible solo melodic
line. This is exactly the shape of work the original plan anticipated: *"the
actual differentiation should go into harmonica-specific post-processing,
not reinventing pitch detection."* Phase 0 confirms that's a real and
necessary step, not optional polish — the raw backbone output requires it.

## Result 3: speed is not a concern

| Metric | Basic Pitch | pYIN |
|---|---|---|
| Real-time factor (file mode) | ~0.01-0.02x (50-100x faster than real-time) | ~0.19-0.22x (~5x faster than real-time) |
| Simulated streaming, 0.5s chunks, growing windows up to 5s | mean 0.107s/chunk, max 0.122s | not tested for streaming |

Basic Pitch's per-chunk latency stayed roughly flat (~0.09s→0.12s) as the
window grew from 0.5s to 5s rather than scaling linearly — its cost is
dominated by fixed per-call overhead at these short window sizes, not by
audio length. Max observed latency (~120ms) is within a workable budget for
"live feedback while playing," though only windows up to 5s were tested;
longer in-progress phrases during a real performance weren't measured and
should be re-checked once Phase 4 builds the actual streaming pipeline.

## What the review subagent caught (and what didn't need fixing)

- **Real bug, fixed**: in the pYIN note-segmentation loop, a note still
  sounding at the last audio frame got `end_s` set equal to its own
  `start_s` timestamp (using `times[-1]`, the start of the last frame, not
  the clip's actual end) — silently truncating or dropping trailing notes.
  Fixed by using the known clip `duration` instead.
- **Checked and correct**: `basic_pitch.inference.predict()`'s return shape
  and the streaming-window slicing logic (confirmed against the installed
  package's source rather than assumed) — no bug found.
- **Noted, not a bug**: simulated streaming windows get resampled to Basic
  Pitch's internal 22050 Hz on every chunk, so the streaming latency numbers
  include resample cost each call — realistic for an actual streaming
  scenario, but worth remembering when interpreting "pure model" latency.

## Conclusion: proceed to Phase 1

Pitch-detection accuracy and latency are viable for chromatic harmonica,
**conditional on harmonica-aware post-processing** (range constraint +
monophonic overlap resolution) rather than using either backbone out of the
box. This should land in Phase 1 as the first stage after raw pitch
detection, before note quantization.

Basic Pitch is the stronger choice over pYIN for this product: ~5-10x faster
at file-mode inference, and its existing onset/offset/amplitude output
(needed for note duration anyway) means less code to write than building
onset detection on top of pYIN's raw f0 contour.

## Open follow-ups for Phase 1

- Validate against **real chromatic harmonica** audio (not the diatonic
  proxy used here) before finalizing hole/direction mapping — timbre proxy
  was reasonable for a pitch-detection go/no-go, but won't surface
  chromatic-specific quirks (e.g. slide-button transients).
- Re-measure streaming latency with realistic in-progress phrase lengths
  (10-30s), not just up to 5s, once the live pipeline exists.
- The monophonic filter here is a blunt "drop the quieter overlapping note";
  Phase 1's real version should likely also consider pitch continuity
  (prefer the note closer to the previous note's pitch) to reduce octave
  jumps.
