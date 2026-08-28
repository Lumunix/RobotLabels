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


# Labels are drawn at SUPERSAMPLE x the final resolution, then downscaled with
# LANCZOS so text and border corners come out smooth instead of pixelated.
SUPERSAMPLE = 4


def _scale(value: int, factor: float) -> int:
    return round(value * factor)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
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


def _draw_ticks(
    draw: ImageDraw.ImageDraw,
    template: LabelTemplate,
    factor: float,
) -> None:
    for tick in template.ticks:
        r = tick.scale(factor)
        draw.rectangle((r.left, r.top, max(r.right, r.left + 1), max(r.bottom, r.top + 1)), fill=0)


def _make_text_image(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> Image.Image:
    """Render text tightly cropped to its ink bounding box (white background)."""
    measure = ImageDraw.Draw(Image.new("L", (1, 1)))
    bbox = measure.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    text_img = Image.new("L", (tw, th), 255)
    # Offset by the bbox origin so ascenders/descenders are not clipped.
    ImageDraw.Draw(text_img).text((-bbox[0], -bbox[1]), text, fill=0, font=font)
    return text_img


def _paste_centered(image: Image.Image, tile: Image.Image, center: tuple[int, int]) -> None:
    image.paste(tile, (center[0] - tile.width // 2, center[1] - tile.height // 2))


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

    text_img = _make_text_image(text, font)
    mid = (outer.left + outer.right) // 2
    top_band = (outer.top + inner.top) // 2
    bottom_band = (inner.bottom + outer.bottom) // 2
    left_band = (outer.left + inner.left) // 2
    right_band = (inner.right + outer.right) // 2

    # Orientations measured from the reference label photo: bottom reads
    # normally, top is upside down, left reads top-to-bottom, right reads
    # bottom-to-top (180-degree rotational symmetry).
    _paste_centered(image, text_img, (mid, bottom_band))
    _paste_centered(image, text_img.rotate(180, expand=True, fillcolor=255), (mid, top_band))
    _paste_centered(image, text_img.rotate(270, expand=True, fillcolor=255), (left_band, mid))
    _paste_centered(image, text_img.rotate(90, expand=True, fillcolor=255), (right_band, mid))


def render_label_png(
    code: str,
    kind: LabelKind | str,
    dpi: int = DEFAULT_DPI,
    size_mm: float = DEFAULT_SIZE_MM,
) -> Image.Image:
    template = get_template(kind)
    size = template.dots(dpi, size_mm)
    factor = template.scale_factor(dpi, size_mm) * SUPERSAMPLE
    canvas = size * SUPERSAMPLE
    image = Image.new("L", (canvas, canvas), 255)
    draw = ImageDraw.Draw(image)

    line_w = max(1, _scale(template.line_width_px, factor))
    radius = max(1, _scale(template.corner_radius_px, factor))
    font_size = max(8, _scale(template.text_height_px, factor))

    outer = template.outer.scale(factor)
    _draw_rounded_rect(draw, (outer.left, outer.top, outer.right, outer.bottom), radius, line_w)

    if template.inner:
        # The reference label's inner border has square corners.
        inner = template.inner.scale(factor)
        draw.rectangle((inner.left, inner.top, inner.right, inner.bottom), outline=0, width=line_w)

    _draw_ticks(draw, template, factor)

    payload = format_tote_code(code) if template.kind == LabelKind.TOTE else code
    dm = template.datamatrix.scale(factor)
    _draw_datamatrix(image, (dm.left, dm.top, dm.right, dm.bottom), payload)

    font = _load_font(font_size)
    if template.kind == LabelKind.FLOOR:
        _draw_edge_text(image, payload, template, factor, font)
    else:
        text_img = _make_text_image(payload, font)
        text_y = _scale(template.bottom_text_y or 512, factor)
        _paste_centered(image, text_img, (canvas // 2, text_y))

    return image.resize((size, size), Image.LANCZOS)


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
