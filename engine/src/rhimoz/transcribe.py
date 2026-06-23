"""
Top-level orchestration: audio file in, MusicXML/MIDI/PDF out.
"""
import tempfile
from dataclasses import dataclass
from pathlib import Path

import soundfile as sf

from rhimoz.instruments.profile import InstrumentProfile
from rhimoz.notes.model import NoteSequence
from rhimoz.pipeline.detect import detect_notes
from rhimoz.pipeline.export_musicxml import export_midi, export_musicxml
from rhimoz.pipeline.export_pdf import export_pdf
from rhimoz.pipeline.preprocess import load_audio, normalize_audio
from rhimoz.pipeline.quantize import estimate_tempo, quantize_to_grid
from rhimoz.pipeline.tab import annotate_tabs


@dataclass
class TranscriptionResult:
    note_sequence: NoteSequence
    musicxml_path: Path
    midi_path: Path
    pdf_path: Path


def transcribe_file(
    audio_path: str | Path, profile: InstrumentProfile, out_dir: str | Path
) -> TranscriptionResult:
    """Runs the full file-based pipeline: preprocess -> detect -> quantize
    -> annotate tabs -> export. Output files are named after the input
    audio's stem and written into out_dir (created if missing)."""
    audio_path = Path(audio_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    y, sr = load_audio(audio_path)
    y = normalize_audio(y)

    # Basic Pitch's predict() only accepts a file path, not an in-memory
    # array, so the normalized audio is written to a temp WAV before
    # detection - otherwise normalize_audio() would have no actual effect
    # on detection, since detect_notes would just reload the original,
    # unnormalized file.
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        sf.write(tmp_path, y, sr)
        raw_sequence = detect_notes(tmp_path, profile)
    finally:
        tmp_path.unlink(missing_ok=True)

    tempo = estimate_tempo(y, sr)
    quantized = quantize_to_grid(raw_sequence, tempo)
    tabbed = annotate_tabs(quantized, profile)

    stem = audio_path.stem
    musicxml_path = export_musicxml(tabbed, out_dir / f"{stem}.musicxml")
    midi_path = export_midi(tabbed, out_dir / f"{stem}.mid")
    pdf_path = export_pdf(tabbed, out_dir / f"{stem}.pdf")

    return TranscriptionResult(
        note_sequence=tabbed,
        musicxml_path=musicxml_path,
        midi_path=midi_path,
        pdf_path=pdf_path,
    )
