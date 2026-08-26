"""ZPL generation for Zebra ZD888 203 dpi printers."""

from __future__ import annotations

from pathlib import Path

from robotlabels.templates import (
    DEFAULT_DPI,
    DEFAULT_SIZE_MM,
    LabelKind,
    format_tote_code,
    get_template,
)


def _s(value: int, factor: float) -> int:
    return round(value * factor)


def _box_zpl(x: int, y: int, w: int, h: int, thickness: int) -> str:
    return f"^FO{x},{y}^GB{w},{h},{thickness},B^FS"


def _tick_zpl(size: int, factor: float, thickness: int) -> str:
    lines: list[str] = []
    length = _s(35, factor)
    tick_t = max(1, thickness)
    center = size // 2
    margin = _s(37, factor)

    lines.append(_box_zpl(center - length // 2, margin, length, tick_t, tick_t))
    lines.append(
        _box_zpl(
            center - length // 2,
            size - margin - tick_t,
            length,
            tick_t,
            tick_t,
        )
    )
    lines.append(_box_zpl(margin, center - length // 2, tick_t, length, tick_t))
    lines.append(
        _box_zpl(size - margin - tick_t, center - length // 2, tick_t, length, tick_t)
    )
    return "".join(lines)


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

    parts.append(_tick_zpl(size, factor, line_t))

    dm_size = min(dm.width, dm.height)
    module = max(2, dm_size // 24)
    parts.append(f"^FO{dm.left},{dm.top}^BXN,{module},200,,,,_^FD{payload}^FS")

    if template.kind == LabelKind.ANT:
        bottom_y = _s(562, factor)
        top_y = _s(40, factor)
        left_x = _s(28, factor)
        right_x = size - _s(170, factor)
        parts.extend(
            [
                f"^FO{outer.left + 20},{bottom_y}^A0N,{font_h},{font_w}^FD{payload}^FS",
                f"^FO{outer.left + 20},{top_y}^A0I,{font_h},{font_w}^FD{payload}^FS",
                f"^FO{left_x},{outer.top + outer.height // 3}^A0R,{font_h},{font_w}^FD{payload}^FS",
                f"^FO{right_x},{outer.top + outer.height // 3}^A0B,{font_h},{font_w}^FD{payload}^FS",
            ]
        )
    else:
        text_y = _s(template.bottom_text_y or 512, factor)
        text_x = outer.left + 20
        parts.append(f"^FO{text_x},{text_y}^A0N,{font_h},{font_w}^FD{payload}^FS")

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
