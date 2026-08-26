"""ZPL generation for Zebra ZD888 / ZD421 203 dpi printers.

The label is rendered with the same code path as the PNG proofs and embedded
as a ^GFA bitmap, so the printed label always matches the PNG pixel for pixel.
Composing the label from native ZPL text/barcode fields proved unreliable:
the printer's font metrics differ from our estimates and rotated ^A0 fields
anchor ^FO to a different corner per rotation, misplacing the edge text.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from robotlabels.render import render_label_png
from robotlabels.templates import (
    DEFAULT_DPI,
    DEFAULT_SIZE_MM,
    LabelKind,
    format_tote_code,
    get_template,
)

# Pixels darker than this are printed black. The PNG is anti-aliased, so a
# threshold above the midpoint keeps thin text strokes from dropping out.
_BLACK_THRESHOLD = 160


def _image_to_gfa(image: Image.Image) -> str:
    """Convert a grayscale label image to a ^GFA graphic field command."""
    mono = image.point(lambda p: 0 if p < _BLACK_THRESHOLD else 255).convert("1")
    bytes_per_row = (mono.width + 7) // 8
    # In ZPL graphics a 1 bit means "print black"; PIL mode "1" uses 0 for
    # black, so invert while packing.
    raw = bytes(b ^ 0xFF for b in mono.tobytes())
    total = bytes_per_row * mono.height
    assert len(raw) == total
    hex_rows = [
        raw[i : i + bytes_per_row].hex().upper()
        for i in range(0, total, bytes_per_row)
    ]
    data = "\n".join(hex_rows)
    return f"^FO0,0^GFA,{total},{total},{bytes_per_row},\n{data}^FS"


def render_label_zpl(
    code: str,
    kind: LabelKind | str,
    dpi: int = DEFAULT_DPI,
    size_mm: float = DEFAULT_SIZE_MM,
) -> str:
    template = get_template(kind)
    size = template.dots(dpi, size_mm)
    image = render_label_png(code, kind, dpi=dpi, size_mm=size_mm)

    parts = [
        "^XA",
        f"^PW{size}",
        f"^LL{size}",
        "^LH0,0",
        _image_to_gfa(image),
        "^XZ",
    ]
    return "\n".join(parts)


def render_batch_zpl(
    codes: list[str],
    kind: LabelKind | str,
    output_dir: Path,
    dpi: int = DEFAULT_DPI,
    size_mm: float = DEFAULT_SIZE_MM,
) -> list[Path]:
    paths: list[Path] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for code in codes:
        payload = format_tote_code(code) if get_template(kind).kind == LabelKind.TOTE else code
        safe = payload.replace("/", "_")
        path = output_dir / f"{safe}.zpl"
        path.write_text(render_label_zpl(code, kind, dpi, size_mm), encoding="ascii")
        paths.append(path)
    return paths
