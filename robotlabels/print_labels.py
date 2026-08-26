"""Batch printing of ZPL files through a CUPS raw queue."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def print_zpl_directory(directory: Path, printer: str, *, dry_run: bool = False) -> int:
    """Submit every .zpl file in a directory to a CUPS queue, one job per file.

    Returns 0 on success, 1 if any lp job failed, 2 if the directory is
    missing or contains no .zpl files.
    """
    if not directory.is_dir():
        print(f"Directory not found: {directory}", file=sys.stderr)
        return 2

    files = sorted(directory.glob("*.zpl"))
    if not files:
        print(f"No .zpl files found in {directory}", file=sys.stderr)
        return 2

    if dry_run:
        print(f"Would print {len(files)} file(s) to queue '{printer}':")
        for path in files:
            print(f"  {path}")
        return 0

    if shutil.which("lp") is None:
        print(
            "The 'lp' command was not found. Install CUPS (e.g. sudo apt install cups)"
            " and set up a raw queue for your Zebra printer first.",
            file=sys.stderr,
        )
        return 1

    failures = 0
    for index, path in enumerate(files, start=1):
        print(f"Printing {index}/{len(files)}: {path.name}")
        result = subprocess.run(
            ["lp", "-d", printer, "-o", "raw", str(path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failures += 1
            message = result.stderr.strip() or result.stdout.strip() or "unknown error"
            print(f"  Failed: {message}", file=sys.stderr)

    if failures:
        print(f"{failures} of {len(files)} job(s) failed.", file=sys.stderr)
        return 1

    print(f"Submitted {len(files)} job(s) to queue '{printer}'.")
    return 0
