"""
PDF export via verovio (MusicXML -> SVG) + svglib/reportlab (SVG -> PDF).
Deliberately avoids MuseScore/Lilypond/system Cairo: this machine's
Homebrew isn't user-writable, and both verovio and svglib/reportlab ship
prebuilt wheels with no system dependency, confirmed by installing them
cleanly in this engine's venv.

Two verovio output quirks needed workarounds here, both found by visually
inspecting rendered PDFs rather than just checking files were non-empty:

1. Verovio nests an inner <svg viewBox="0 0 21000 29700"> (the actual
   page content) inside an outer <svg width="2100px" height="2970px">
   that has no viewBox of its own. svg2rlg doesn't apply the inner
   viewBox's implied scale, so only content within roughly the first
   "system" lands on the visible page - everything after silently renders
   off-canvas for any score with more than ~6 notes. _flatten_nested_svg()
   hoists the inner viewBox onto the root and inlines its children into a
   single, correctly-scaled <svg> document.
2. Verovio renders some glyphs (e.g. the quarter-note symbol in a tempo
   marking) as <text font-family:'Leipzig'>, referencing its own SMuFL
   font embedded in the SVG as a base64 WOFF2 @font-face. svglib doesn't
   parse embedded web fonts, so without registering that font separately,
   any such glyph silently falls back to a filled placeholder box.
   _ensure_smufl_font_registered() extracts the font verovio already
   ships (woff2 -> ttf via fontTools, needs the brotli package for woff2
   decompression) and registers it with svglib once per process.
"""
import base64
import io
import re
import tempfile
from functools import lru_cache
from pathlib import Path

import verovio
from fontTools.ttLib import TTFont as FontToolsFont
from lxml import etree
from reportlab.graphics import renderPDF
from svglib.svglib import register_font, svg2rlg

from rhimoz.notes.model import NoteSequence
from rhimoz.pipeline.export_musicxml import export_musicxml

_SMUFL_FONT_NAME = "Leipzig"
_SVG_NS = "http://www.w3.org/2000/svg"


@lru_cache(maxsize=1)
def _ensure_smufl_font_registered() -> None:
    """Extracts verovio's bundled Leipzig SMuFL font and registers it with
    svglib so embedded music-glyph text renders correctly instead of
    falling back to a placeholder box. Cached so the woff2->ttf conversion
    only happens once per process - lru_cache only caches a successful
    return, so a failure here (e.g. if a future verovio version changes
    Leipzig.css's format) raises and is retried on the next call rather
    than being memoized as silently "done"."""
    resource_dir = Path(verovio.toolkit().getResourcePath())
    css = (resource_dir / f"{_SMUFL_FONT_NAME}.css").read_text()
    match = re.search(
        r"data:application/font-woff2;charset=utf-8;base64,([^)]+)\)", css
    )
    if not match:
        raise RuntimeError(
            f"Could not find embedded WOFF2 font data in {_SMUFL_FONT_NAME}.css - "
            "verovio's font packaging may have changed. Without this, SMuFL text "
            "glyphs (e.g. tempo marking symbols) render as placeholder boxes."
        )

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


def _flatten_nested_svg(svg_content: str) -> str:
    """Hoists a nested <svg viewBox=...> (verovio's actual page content)
    onto the root <svg>, inlining its children. See module docstring point
    1. A no-op if the SVG isn't nested this way."""
    root = etree.fromstring(svg_content.encode("utf-8"))
    inner = root.find(f"{{{_SVG_NS}}}svg")
    if inner is None:
        return svg_content

    view_box = inner.get("viewBox")
    if view_box:
        root.set("viewBox", view_box)

    index = list(root).index(inner)
    for offset, child in enumerate(list(inner)):
        root.insert(index + offset, child)
    root.remove(inner)

    return etree.tostring(root, encoding="unicode")


def musicxml_to_svg(musicxml_path: str | Path) -> str:
    """Renders the first page of a MusicXML file to an SVG string."""
    tk = verovio.toolkit()
    if not tk.loadFile(str(musicxml_path)):
        raise ValueError(f"verovio failed to load {musicxml_path}")
    return tk.renderToSVG(1)


def svg_to_pdf(svg_content: str, out_path: str | Path) -> Path:
    _ensure_smufl_font_registered()
    out_path = Path(out_path)
    drawing = svg2rlg(io.StringIO(_flatten_nested_svg(svg_content)))
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
