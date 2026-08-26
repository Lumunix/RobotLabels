"""ZPL generation for Zebra ZD888 203 dpi printers."""

from __future__ import annotations

from pathlib import Path

from robotlabels.datamatrix import encode_matrix
from robotlabels.templates import (
    DEFAULT_DPI,
    DEFAULT_SIZE_MM,
    LabelKind,
    LabelTemplate,
    format_tote_code,
    get_template,
)


def _s(value: int, factor: float) -> int:
    return round(value * factor)


def _box_zpl(x: int, y: int, w: int, h: int, thickness: int) -> str:
    return f"^FO{x},{y}^GB{w},{h},{thickness},B^FS"


def _tick_zpl(template: LabelTemplate, factor: float) -> str:
    lines: list[str] = []
    for tick in template.ticks:
        r = tick.scale(factor)
        w = max(1, r.width)
        h = max(1, r.height)
        lines.append(_box_zpl(r.left, r.top, w, h, min(w, h)))
    return "".join(lines)


def _text_width(payload: str, font_h: int) -> int:
    """Approximate rendered width of ^A0 scalable font text."""
    return round(len(payload) * font_h * 0.55)


def render_label_zpl(
    code: str,
    kind: LabelKind | str,
    dpi: int = DEFAULT_DPI,
    size_mm: float = DEFAULT_SIZE_MM,
) -> str:
    template = get_template(kind)
    factor = template.scale_factor(dpi, size_mm)
    size = template.dots(dpi, size_mm)
    payload = format_tote_code(code) if template.kind == LabelKind.TOTE else code

    outer = template.outer.scale(factor)
    inner = template.inner.scale(factor) if template.inner else None
    dm = template.datamatrix.scale(factor)
    line_t = max(1, _s(template.line_width_px, factor))
    font_h = max(12, _s(template.text_height_px, factor))
    font_w = max(8, font_h // 2)

    parts = [
        "^XA",
        f"^PW{size}",
        f"^LL{size}",
        "^LH0,0",
        _box_zpl(
            outer.left,
            outer.top,
            outer.width,
            outer.height,
            line_t,
        ),
    ]

    if inner:
        parts.append(
            _box_zpl(
                inner.left,
                inner.top,
                inner.width,
                inner.height,
                line_t,
            )
        )

    parts.append(_tick_zpl(template, factor))

    # Size modules from the actual symbol so the printed Data Matrix fills the
    # template box like the PNG rendering does.
    cols = len(encode_matrix(payload)[0])
    dm_size = min(dm.width, dm.height)
    module = max(2, dm_size // cols)
    dm_x = dm.left + (dm.width - module * cols) // 2
    dm_y = dm.top + (dm.height - module * cols) // 2
    parts.append(f"^FO{dm_x},{dm_y}^BXN,{module},200,,,,_^FD{payload}^FS")

    text_w = _text_width(payload, font_h)
    if template.kind == LabelKind.ANT:
        assert inner is not None
        text_x = (size - text_w) // 2
        text_y = (size - text_w) // 2
        top_band = (outer.top + inner.top) // 2
        bottom_band = (inner.bottom + outer.bottom) // 2
        left_band = (outer.left + inner.left) // 2
        right_band = (inner.right + outer.right) // 2
        # Orientations match the reference label: bottom normal, top inverted,
        # left reads top-to-bottom (R), right reads bottom-to-top (B).
        parts.extend(
            [
                f"^FO{text_x},{bottom_band - font_h // 2}^A0N,{font_h},{font_w}^FD{payload}^FS",
                f"^FO{text_x},{top_band - font_h // 2}^A0I,{font_h},{font_w}^FD{payload}^FS",
                f"^FO{left_band - font_h // 2},{text_y}^A0R,{font_h},{font_w}^FD{payload}^FS",
                f"^FO{right_band - font_h // 2},{text_y}^A0B,{font_h},{font_w}^FD{payload}^FS",
            ]
        )
    else:
        text_y = _s(template.bottom_text_y or 512, factor) - font_h // 2
        parts.append(f"^FO{(size - text_w) // 2},{text_y}^A0N,{font_h},{font_w}^FD{payload}^FS")

    parts.append("^XZ")
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
