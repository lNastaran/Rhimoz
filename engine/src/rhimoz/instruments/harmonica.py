import librosa

from rhimoz.instruments.profile import InstrumentProfile, PitchDetectionParams
from rhimoz.notes.model import TabAnnotation

# Solo-tuned chromatic harmonica layout, verified against Wikipedia's
# Chromatic harmonica article (per-hole table fetched directly, not
# recalled from memory): each octave repeats a 4-hole pattern with blow
# notes C E G C and draw notes D F A B. Pressing the slide button raises
# both reeds of a hole by one semitone, filling the chromatic gaps.
#
# semitone-in-octave -> (hole_offset 1-4, direction). Chosen canonically
# to prefer no-slide over needing slide whenever a semitone is reachable
# both ways (semitone 5/F: hole 2 draw, no slide, rather than hole 2
# blow+slide - both land on the same real reed pitch, a documented
# redundancy on the actual instrument, not a typo), and to always use the
# lowest hole number that produces a pitch (a new octave's C is hole 1 of
# that octave, never the previous octave's redundant hole 4 blow). The
# slide bit itself is tracked here for correctness of the mapping but
# deliberately not exposed in TabAnnotation - v1 shows hole+direction
# only, matching the product brief's stated default. Showing
# slide-pressed state (e.g. "6↑*") is an easy, explicitly-deferred
# follow-up: it would just mean adding a third field to TabAnnotation and
# surfacing the `uses_slide` value already computed here.
_SEMITONE_TO_HOLE_OFFSET_AND_DIRECTION: dict[int, tuple[int, str, bool]] = {
    0: (1, "blow", False),  # C
    1: (1, "blow", True),  # C#
    2: (1, "draw", False),  # D
    3: (1, "draw", True),  # D#
    4: (2, "blow", False),  # E
    5: (2, "draw", False),  # F (also reachable via hole 2 blow+slide)
    6: (2, "draw", True),  # F#
    7: (3, "blow", False),  # G
    8: (3, "blow", True),  # G#
    9: (3, "draw", False),  # A
    10: (3, "draw", True),  # A#
    11: (4, "draw", False),  # B
}
_HOLES_PER_OCTAVE = 4
_TOTAL_HOLES = 16  # 4 octaves (C3-C7) x 4 holes/octave


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

    def tab_for_note(self, midi_pitch: int) -> TabAnnotation | None:
        """Maps a MIDI pitch to this profile's hole number + blow/draw
        direction, per the verified layout in _SEMITONE_TO_HOLE_OFFSET_AND_DIRECTION
        above. MIDI 48 (C3) is hole 1's blow note - the bottom of
        pitch_range_hz(), chosen to match the range this profile already
        established rather than introduce a second, independently-chosen
        "real harmonica model" assumption.

        Returns None outside [48, 96] (this profile's playable range) -
        Basic Pitch isn't hard-guaranteed to respect the requested
        frequency range in every case even though Phase 0 confirmed it
        usually does, so this stays defensive rather than extrapolating a
        hole number for a pitch the instrument can't actually produce.
        """
        min_midi = int(round(librosa.hz_to_midi(self.pitch_range_hz()[0])))
        max_midi = int(round(librosa.hz_to_midi(self.pitch_range_hz()[1])))
        if not (min_midi <= midi_pitch <= max_midi):
            return None

        offset = midi_pitch - min_midi
        octave_index, semitone = divmod(offset, 12)
        hole_offset, direction, _uses_slide = _SEMITONE_TO_HOLE_OFFSET_AND_DIRECTION[
            semitone
        ]
        hole = octave_index * _HOLES_PER_OCTAVE + hole_offset

        # Top-of-range edge case: the topmost note (max_midi) is exactly
        # 4 octaves above min_midi, landing on the next (nonexistent)
        # octave's hole 1 blow. There is no hole 17 on a 16-hole
        # instrument - its actual last hole (16) is the doubled-C alias
        # for this pitch instead, matching how the real instrument's
        # octave-boundary redundancy works (every other octave's hole 4
        # blow aliases the next octave's hole 1 blow; at the very top
        # there is no next octave to alias to, so the last hole's blow
        # becomes the only way to play this note).
        if hole > _TOTAL_HOLES:
            hole = _TOTAL_HOLES

        return TabAnnotation(label=str(hole), direction=direction)
