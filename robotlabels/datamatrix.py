"""Data Matrix encoding via ppf.datamatrix."""

from __future__ import annotations

from ppf.datamatrix import DataMatrix


def encode_matrix(payload: str) -> list[list[int]]:
    """Return a 2D matrix of 0/1 module values for the payload."""
    dm = DataMatrix(payload)
    matrix = dm.matrix
    return [[1 if cell else 0 for cell in row] for row in matrix]


def matrix_size(payload: str) -> tuple[int, int]:
    mat = encode_matrix(payload)
    return len(mat[0]), len(mat)
