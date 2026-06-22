from rhimoz.notes.model import NoteSequence, TranscribedNote
from rhimoz.pipeline.export_pdf import (
    _ensure_smufl_font_registered,
    export_pdf,
    musicxml_to_svg,
    svg_to_pdf,
)

TINY_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
<rect x="10" y="10" width="50" height="50" fill="black"/>
</svg>"""


def test_svg_to_pdf_writes_nonempty_file(tmp_path):
    """Pure unit test, no verovio/audio involved - catches reportlab/svglib
    wiring breakage on its own."""
    out_path = tmp_path / "out.pdf"
    result_path = svg_to_pdf(TINY_SVG, out_path)

    assert result_path == out_path
    assert out_path.exists()
    assert out_path.stat().st_size > 0
    with open(out_path, "rb") as f:
        assert f.read(4) == b"%PDF"


def _synthetic_sequence() -> NoteSequence:
    notes = [
        TranscribedNote(start_s=0.0, end_s=0.5, midi_pitch=60, amplitude=0.8),
        TranscribedNote(start_s=0.5, end_s=1.0, midi_pitch=62, amplitude=0.7),
    ]
    return NoteSequence(notes=notes, instrument_name="chromatic_harmonica", tempo_bpm=120.0)


def test_musicxml_to_svg_renders_synthetic_sequence(tmp_path):
    from rhimoz.pipeline.export_musicxml import export_musicxml

    musicxml_path = export_musicxml(_synthetic_sequence(), tmp_path / "out.musicxml")
    svg = musicxml_to_svg(musicxml_path)

    assert svg.strip().startswith("<svg")
    assert "</svg>" in svg


def test_export_pdf_end_to_end_on_synthetic_sequence(tmp_path):
    out_path = tmp_path / "out.pdf"
    result_path = export_pdf(_synthetic_sequence(), out_path)

    assert result_path == out_path
    assert out_path.exists()
    assert out_path.stat().st_size > 0
    with open(out_path, "rb") as f:
        assert f.read(4) == b"%PDF"


def test_smufl_font_is_registered_and_resolves_exactly():
    """Regression test: without registering verovio's embedded Leipzig
    font with svglib, glyphs like the tempo mark's quarter-note symbol
    silently render as a filled placeholder box instead of the real
    glyph. find_font returning an exact match (not a fallback) confirms
    the font is actually usable, not just present in the font map."""
    from svglib.svglib import find_font

    _ensure_smufl_font_registered()

    _, is_exact = find_font("Leipzig", weight="normal", style="normal")
    assert is_exact is True

    _, is_exact_bold = find_font("Leipzig", weight="bold", style="normal")
    assert is_exact_bold is True


def test_export_pdf_cleans_up_temp_musicxml_file(tmp_path):
    import glob
    import tempfile

    tmp_dir = tempfile.gettempdir()
    before = set(glob.glob(tmp_dir + "/*.musicxml"))
    export_pdf(_synthetic_sequence(), tmp_path / "out.pdf")
    after = set(glob.glob(tmp_dir + "/*.musicxml"))

    assert after == before
