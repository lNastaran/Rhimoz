"""
PDF export via verovio (MusicXML -> SVG) + svglib/reportlab (SVG -> PDF).
Deliberately avoids MuseScore/Lilypond/system Cairo: this machine's
Homebrew isn't user-writable, and both verovio and svglib/reportlab ship
prebuilt wheels with no system dependency, confirmed by installing them
cleanly in this engine's venv.

Verovio embeds its music glyphs (clefs, noteheads, etc.) as inline SVG
<defs>/<use> paths, which svglib renders fine with no extra work. The one
exception is text-based glyphs (e.g. the quarter-note symbol in a tempo
marking like "♩ = 120"), which verovio renders as <text font-family:
'Leipzig'> referencing its SMuFL font, embedded in the SVG as a base64
WOFF2 @font-face. svglib doesn't parse embedded web fonts, so without
registering that font separately, any such glyph silently falls back to a
filled placeholder box. _ensure_smufl_font_registered() extracts the font
verovio already ships (woff2 -> ttf via fontTools, needs the brotli
package for woff2 decompression) and registers it with svglib once per
process.
"""
import base64
import io
import re
import tempfile
from functools import lru_cache
from pathlib import Path

import verovio
from fontTools.ttLib import TTFont as FontToolsFont
from reportlab.graphics import renderPDF
from svglib.svglib import register_font, svg2rlg

from rhimoz.notes.model import NoteSequence
from rhimoz.pipeline.export_musicxml import export_musicxml

_SMUFL_FONT_NAME = "Leipzig"


@lru_cache(maxsize=1)
def _ensure_smufl_font_registered() -> None:
    """Extracts verovio's bundled Leipzig SMuFL font and registers it with
    svglib so embedded music-glyph text renders correctly instead of
    falling back to a placeholder box. Cached so the woff2->ttf conversion
    only happens once per process."""
    resource_dir = Path(verovio.toolkit().getResourcePath())
    css = (resource_dir / f"{_SMUFL_FONT_NAME}.css").read_text()
    match = re.search(
        r"data:application/font-woff2;charset=utf-8;base64,([^)]+)\)", css
    )
    if not match:
        return  # font not embedded as expected; glyph fallback is cosmetic only

    woff2_bytes = base64.b64decode(match.group(1))
    font = FontToolsFont(io.BytesIO(woff2_bytes))
    font.flavor = None
    ttf_buf = io.BytesIO()
    font.save(ttf_buf)

    with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as tmp:
        tmp.write(ttf_buf.getvalue())
        ttf_path = tmp.name

    register_font(_SMUFL_FONT_NAME, ttf_path, weight="normal", style="normal")
    register_font(_SMUFL_FONT_NAME, ttf_path, weight="bold", style="normal")


def musicxml_to_svg(musicxml_path: str | Path) -> str:
    """Renders the first page of a MusicXML file to an SVG string."""
    tk = verovio.toolkit()
    if not tk.loadFile(str(musicxml_path)):
        raise ValueError(f"verovio failed to load {musicxml_path}")
    return tk.renderToSVG(1)


def svg_to_pdf(svg_content: str, out_path: str | Path) -> Path:
    _ensure_smufl_font_registered()
    out_path = Path(out_path)
    drawing = svg2rlg(io.StringIO(svg_content))
    renderPDF.drawToFile(drawing, str(out_path))
    return out_path


def export_pdf(seq: NoteSequence, out_path: str | Path) -> Path:
    """Orchestrates: NoteSequence -> temp MusicXML -> SVG -> PDF."""
    with tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        export_musicxml(seq, tmp_path)
        svg_content = musicxml_to_svg(tmp_path)
        return svg_to_pdf(svg_content, out_path)
    finally:
        tmp_path.unlink(missing_ok=True)
