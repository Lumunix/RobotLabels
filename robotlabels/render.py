"""PNG and PDF rendering for robot labels."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from robotlabels.datamatrix import encode_matrix
from robotlabels.templates import (
    DEFAULT_DPI,
    DEFAULT_SIZE_MM,
    LabelKind,
    LabelTemplate,
    format_tote_code,
    get_template,
)


def _scale(value: int, factor: float) -> int:
    return round(value * factor)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    radius: int,
    width: int,
) -> None:
    draw.rounded_rectangle(rect, radius=radius, outline=0, width=width)


def _draw_datamatrix(
    image: Image.Image,
    box: tuple[int, int, int, int],
    payload: str,
) -> None:
    matrix = encode_matrix(payload)
    rows = len(matrix)
    cols = len(matrix[0])
    left, top, right, bottom = box
    target_w = right - left
    target_h = bottom - top
    module = min(target_w // cols, target_h // rows)
    used_w = module * cols
    used_h = module * rows
    offset_x = left + (target_w - used_w) // 2
    offset_y = top + (target_h - used_h) // 2
    draw = ImageDraw.Draw(image)
    for y, row in enumerate(matrix):
        for x, cell in enumerate(row):
            if cell:
                x0 = offset_x + x * module
                y0 = offset_y + y * module
                draw.rectangle((x0, y0, x0 + module - 1, y0 + module - 1), fill=0)


def _draw_tick(
    draw: ImageDraw.ImageDraw,
    tick,
    template: LabelTemplate,
    factor: float,
    line_w: int,
) -> None:
    thickness = max(1, _scale(tick.thickness, factor))
    length = _scale(tick.end - tick.start, factor)
    center = _scale(tick.center, factor)
    start = _scale(tick.start, factor)

    if tick.orientation in {"top", "bottom"}:
        y = _scale(48 if tick.orientation == "top" else 551, factor)
        draw.rectangle((start, y, start + length, y + thickness), fill=0)
    else:
        x = _scale(48 if tick.orientation == "left" else 551, factor)
        draw.rectangle((x, start, x + thickness, start + length), fill=0)


def _draw_rotated_text(
    image: Image.Image,
    text: str,
    xy: tuple[int, int],
    angle: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    bbox = ImageDraw.Draw(image).textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    text_img = Image.new("RGBA", (tw + 4, th + 4), (255, 255, 255, 0))
    text_draw = ImageDraw.Draw(text_img)
    text_draw.text((2, 2), text, fill=(0, 0, 0, 255), font=font)
    rotated = text_img.rotate(angle, expand=True, fillcolor=(255, 255, 255, 0))
    base = image.convert("RGBA")
    base.paste(rotated, xy, rotated)
    image.paste(base.convert("L"))


def _draw_edge_text(
    image: Image.Image,
    text: str,
    template: LabelTemplate,
    factor: float,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    assert template.inner is not None
    outer = template.outer.scale(factor)
    inner = template.inner.scale(factor)

    draw = ImageDraw.Draw(image)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    bottom_y = inner.bottom + (outer.bottom - inner.bottom - th) // 2
    top_y = outer.top + (inner.top - outer.top - th) // 2
    left_x = outer.left + (inner.left - outer.left - th) // 2
    right_x = inner.right + (outer.right - inner.right - th) // 2

    draw.text(
        (outer.left + (outer.width - tw) // 2, bottom_y),
        text,
        fill=0,
        font=font,
    )
    _draw_rotated_text(
        image,
        text,
        (outer.left + (outer.width - tw) // 2, top_y),
        180,
        font,
    )
    _draw_rotated_text(
        image,
        text,
        (left_x, outer.top + (outer.height - tw) // 2),
        90,
        font,
    )
    _draw_rotated_text(
        image,
        text,
        (right_x, outer.top + (outer.height - tw) // 2),
        270,
        font,
    )


def render_label_png(
    code: str,
    kind: LabelKind | str,
    dpi: int = DEFAULT_DPI,
    size_mm: float = DEFAULT_SIZE_MM,
) -> Image.Image:
    template = get_template(kind)
    factor = template.scale_factor(dpi, size_mm)
    size = template.dots(dpi, size_mm)
    image = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(image)

    line_w = max(1, _scale(template.line_width_px, factor))
    radius = max(1, _scale(template.corner_radius_px, factor))
    font_size = max(8, _scale(template.text_height_px, factor))

    outer = template.outer.scale(factor)
    _draw_rounded_rect(draw, (outer.left, outer.top, outer.right, outer.bottom), radius, line_w)

    if template.inner:
        inner = template.inner.scale(factor)
        _draw_rounded_rect(draw, (inner.left, inner.top, inner.right, inner.bottom), radius, line_w)

    for tick in template.ticks:
        _draw_tick(draw, tick, template, factor, line_w)

    payload = format_tote_code(code) if template.kind == LabelKind.TOTE else code
    dm = template.datamatrix.scale(factor)
    _draw_datamatrix(image, (dm.left, dm.top, dm.right, dm.bottom), payload)

    font = _load_font(font_size)
    if template.kind == LabelKind.ANT:
        _draw_edge_text(image, payload, template, factor, font)
    else:
        bbox = draw.textbbox((0, 0), payload, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        text_y = _scale(template.bottom_text_y or 512, factor) - th // 2
        draw.text(((size - tw) // 2, text_y), payload, fill=0, font=font)

    return image.convert("1")


def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def save_pdf(images: list[Image.Image], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rgb_images = [img.convert("RGB") for img in images]
    first, rest = rgb_images[0], rgb_images[1:]
    first.save(path, save_all=True, append_images=rest, format="PDF", resolution=203.0)


def render_batch_png(
    codes: list[str],
    kind: LabelKind | str,
    output_dir: Path,
    dpi: int = DEFAULT_DPI,
    size_mm: float = DEFAULT_SIZE_MM,
) -> list[Path]:
    paths: list[Path] = []
    for code in codes:
        payload = format_tote_code(code) if get_template(kind).kind == LabelKind.TOTE else code
        safe = payload.replace("/", "_")
        path = output_dir / f"{safe}.png"
        save_png(render_label_png(code, kind, dpi, size_mm), path)
        paths.append(path)
    return paths
