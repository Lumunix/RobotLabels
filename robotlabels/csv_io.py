"""CSV input helpers."""

from __future__ import annotations

import csv
from pathlib import Path


def read_codes(path: Path, column: str = "code") -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no header row")
        if column not in reader.fieldnames:
            available = ", ".join(reader.fieldnames)
            raise ValueError(
                f"Column '{column}' not found in {path}. Available: {available}"
            )
        codes: list[str] = []
        for row_num, row in enumerate(reader, start=2):
            value = (row.get(column) or "").strip()
            if not value:
                raise ValueError(f"{path}:{row_num}: empty value in column '{column}'")
            codes.append(value)
    if not codes:
        raise ValueError(f"{path} contains no data rows")
    return codes
