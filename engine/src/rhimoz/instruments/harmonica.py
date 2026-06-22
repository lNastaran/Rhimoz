import librosa

from rhimoz.instruments.profile import InstrumentProfile, PitchDetectionParams


class ChromaticHarmonicaProfile(InstrumentProfile):
    """Chromatic harmonica: monophonic, roughly a C3-C7 range. Tuning
    values and overlap-resolution logic are ported from Phase 0's
    validated research - see research/phase0/PHASE0_FINDINGS.md and
    research/phase0/scripts/validate_pitch_detection.py for why Basic
    Pitch's polyphonic-instrument defaults produce harmonic bleed-through
    and out-of-range artifacts on solo harmonica audio without these."""

    name = "chromatic_harmonica"
    is_monophonic = True

    def pitch_range_hz(self) -> tuple[float, float]:
        return librosa.note_to_hz("C3"), librosa.note_to_hz("C7")

    def detection_params(self) -> PitchDetectionParams:
        fmin, fmax = self.pitch_range_hz()
        return PitchDetectionParams(
            onset_threshold=0.6,
            frame_threshold=0.4,
            minimum_note_length_ms=100,
            min_midi=int(round(librosa.hz_to_midi(fmin))),
            max_midi=int(round(librosa.hz_to_midi(fmax))),
        )

    def resolve_overlaps(self, note_events: list) -> list:
        """Sort by start time; whenever two notes overlap, keep whichever
        has higher amplitude and drop the other. A monophonic instrument
        can't produce two independent simultaneous pitches, so any overlap
        reported by the detection backbone is a harmonic-bleed-through
        artifact, not a real chord. Known limitation (documented in
        PHASE0_FINDINGS.md): this is "blunt" - it doesn't consider pitch
        continuity with the previous note, which a future version could
        use to reduce octave-jump artifacts."""
        events = sorted(note_events, key=lambda n: n[0])
        kept: list = []
        for ev in events:
            start, end, _pitch, amp, _bends = ev
            if kept and start < kept[-1][1]:
                if amp > kept[-1][3]:
                    kept[-1] = ev
            else:
                kept.append(ev)
        return kept
