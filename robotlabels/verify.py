"""Verification helpers for generated labels."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from robotlabels.datamatrix import encode_matrix
from robotlabels.render import render_label_png
from robotlabels.templates import LabelKind, format_tote_code, get_template


def decode_datamatrix(image: Image.Image) -> str | None:
    try:
        from pylibdmtx.pylibdmtx import decode as dmtx_decode
    except ImportError:
        return None

    results = dmtx_decode(image.convert("RGB"))
    if not results:
        return None
    return results[0].data.decode("utf-8")


def verify_code_roundtrip(code: str, kind: LabelKind | str) -> dict[str, object]:
    template = get_template(kind)
    payload = format_tote_code(code) if template.kind == LabelKind.TOTE else code
    matrix = encode_matrix(payload)
    image = render_label_png(code, kind)
    decoded = decode_datamatrix(image)
    return {
        "input": code,
        "payload": payload,
        "matrix_size": (len(matrix), len(matrix[0])),
        "decoded": decoded,
        "ok": decoded == payload if decoded is not None else None,
    }


def compare_preview(
    generated: Path,
    reference: Path,
    size: int = 620,
) -> float:
    gen = Image.open(generated).convert("L").resize((size, size))
    ref = Image.open(reference).convert("L")
    gp = gen.load()
    rp = ref.load()
    match = 0
    total = size * size
    for y in range(size):
        for x in range(size):
            if (gp[x, y] < 128) == (rp[x, y] < 128):
                match += 1
    return match / total
