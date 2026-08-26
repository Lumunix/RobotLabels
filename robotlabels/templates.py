"""Layout geometry for 60x60 mm labels (620 px design coordinates)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


PREVIEW_PX = 620
DEFAULT_DPI = 203
DEFAULT_SIZE_MM = 60.0


class LabelKind(str, Enum):
    ANT = "ant"
    TOTE = "tote"


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    def center(self) -> tuple[int, int]:
        return (self.left + self.width // 2, self.top + self.height // 2)

    def scale(self, factor: float) -> "Rect":
        return Rect(
            round(self.left * factor),
            round(self.top * factor),
            round(self.right * factor),
            round(self.bottom * factor),
        )


@dataclass(frozen=True)
class LabelTemplate:
    kind: LabelKind
    preview_px: int
    outer: Rect
    inner: Rect | None
    datamatrix: Rect
    ticks: tuple[Rect, ...]  # filled registration marks, in preview coordinates
    text_height_px: int
    text_band_px: Rect | None  # region between outer and inner for edge text (ant)
    bottom_text_y: int | None  # baseline region center for tote bottom text
    corner_radius_px: int
    line_width_px: int = 2

    def dots(self, dpi: int = DEFAULT_DPI, size_mm: float = DEFAULT_SIZE_MM) -> int:
        return round(size_mm / 25.4 * dpi)

    def scale_factor(self, dpi: int = DEFAULT_DPI, size_mm: float = DEFAULT_SIZE_MM) -> float:
        return self.dots(dpi, size_mm) / self.preview_px


# Ticks are short dashes perpendicular to the outer border, crossing it at the
# midpoint of each edge (measured from the reference label photo).
_EDGE_TICKS = (
    Rect(307, 0, 313, 28),      # top
    Rect(307, 592, 313, 620),   # bottom
    Rect(0, 307, 28, 313),      # left
    Rect(592, 307, 620, 313),   # right
)

# Center-axis ticks drawn inward from the inner border toward the Data Matrix.
# They continue the outer edge ticks so a cross-line laser aligned with them
# passes through the Data Matrix center, without crossing the edge text that
# sits between the outer and inner borders.
_INNER_CENTER_TICKS = (
    Rect(307, 77, 313, 105),    # top
    Rect(307, 514, 313, 542),   # bottom
    Rect(77, 307, 105, 313),    # left
    Rect(514, 307, 542, 313),   # right
)

ANT_TEMPLATE = LabelTemplate(
    kind=LabelKind.ANT,
    preview_px=PREVIEW_PX,
    outer=Rect(20, 20, 599, 599),
    inner=Rect(77, 77, 542, 542),
    datamatrix=Rect(192, 192, 428, 428),
    ticks=_EDGE_TICKS + _INNER_CENTER_TICKS,
    text_height_px=44,
    text_band_px=Rect(20, 20, 599, 599),
    bottom_text_y=None,
    corner_radius_px=8,
    line_width_px=4,
)

TOTE_TEMPLATE = LabelTemplate(
    kind=LabelKind.TOTE,
    preview_px=PREVIEW_PX,
    outer=Rect(20, 20, 599, 599),
    inner=None,
    datamatrix=Rect(161, 161, 459, 459),
    ticks=_EDGE_TICKS,
    text_height_px=44,
    text_band_px=None,
    bottom_text_y=512,
    corner_radius_px=8,
    line_width_px=4,
)

TEMPLATES: dict[LabelKind, LabelTemplate] = {
    LabelKind.ANT: ANT_TEMPLATE,
    LabelKind.TOTE: TOTE_TEMPLATE,
}


def get_template(kind: LabelKind | str) -> LabelTemplate:
    if isinstance(kind, str):
        kind = LabelKind(kind.lower())
    return TEMPLATES[kind]


def format_tote_code(code: str) -> str:
    code = code.strip()
    if not code.upper().startswith("TOTE_"):
        return f"TOTE_{code}"
    return code
