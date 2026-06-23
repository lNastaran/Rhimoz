"""
Attaches harmonica tab annotations (hole number + blow/draw direction) to
each note, via the instrument profile's tab_for_note(). A thin pipeline
stage, not logic of its own - the actual hole/direction table lives in
ChromaticHarmonicaProfile.tab_for_note() (instruments/harmonica.py), kept
there so future instrument profiles (piano, guitar, ...) can each define
their own idiomatic annotation without this stage knowing instrument
identity, mirroring every other stage's "never branch on instrument
identity" rule.
"""
from dataclasses import replace

from rhimoz.instruments.profile import InstrumentProfile
from rhimoz.notes.model import NoteSequence


def annotate_tabs(seq: NoteSequence, profile: InstrumentProfile) -> NoteSequence:
    notes = [replace(note, tab=profile.tab_for_note(note.midi_pitch)) for note in seq.notes]
    return NoteSequence(
        notes=notes,
        instrument_name=seq.instrument_name,
        tempo_bpm=seq.tempo_bpm,
        beat_times_s=seq.beat_times_s,
    )
