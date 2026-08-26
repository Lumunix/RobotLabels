"""Command-line interface for RobotLabels."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from robotlabels import __version__
from robotlabels.csv_io import read_codes
from robotlabels.print_labels import print_zpl_directory
from robotlabels.render import render_batch_png, render_label_png, save_pdf
from robotlabels.templates import DEFAULT_DPI, DEFAULT_SIZE_MM, LabelKind
from robotlabels.zpl import render_batch_zpl


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("csv", type=Path, help="CSV file with a code column")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("out"),
        help="Output directory (default: out)",
    )
    parser.add_argument(
        "--code-column",
        default="code",
        help="CSV column name containing label codes (default: code)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help=f"Print resolution in dots per inch (default: {DEFAULT_DPI})",
    )
    parser.add_argument(
        "--size-mm",
        type=float,
        default=DEFAULT_SIZE_MM,
        help=f"Label width/height in millimeters (default: {DEFAULT_SIZE_MM})",
    )
    parser.add_argument(
        "--png",
        action="store_true",
        help="Write one PNG file per code",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Write a multi-page PDF containing all labels",
    )
    parser.add_argument(
        "--zpl",
        action="store_true",
        help="Write one ZPL file per code for Zebra printers",
    )


def _run(kind: LabelKind, args: argparse.Namespace) -> int:
    if not (args.png or args.pdf or args.zpl):
        print("Specify at least one output format: --png, --pdf, and/or --zpl", file=sys.stderr)
        return 2

    codes = read_codes(args.csv, column=args.code_column)
    args.output.mkdir(parents=True, exist_ok=True)

    if args.png:
        png_paths = render_batch_png(
            codes,
            kind,
            args.output / "png",
            dpi=args.dpi,
            size_mm=args.size_mm,
        )
        print(f"Wrote {len(png_paths)} PNG file(s) to {args.output / 'png'}")

    if args.pdf:
        images = [
            render_label_png(code, kind, dpi=args.dpi, size_mm=args.size_mm)
            for code in codes
        ]
        pdf_path = args.output / f"{kind.value}_labels.pdf"
        save_pdf(images, pdf_path)
        print(f"Wrote PDF to {pdf_path}")

    if args.zpl:
        zpl_paths = render_batch_zpl(
            codes,
            kind,
            args.output / "zpl",
            dpi=args.dpi,
            size_mm=args.size_mm,
        )
        print(f"Wrote {len(zpl_paths)} ZPL file(s) to {args.output / 'zpl'}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="robotlabels",
        description="Generate ant and tote robot labels from CSV.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    ant = subparsers.add_parser(
        "ant",
        help="Generate 60x60 mm floor marker labels (Data Matrix + edge text)",
    )
    _add_common_args(ant)
    ant.set_defaults(handler=lambda args: _run(LabelKind.ANT, args))

    tote = subparsers.add_parser(
        "tote",
        help="Generate 60x60 mm tote labels (Data Matrix + bottom text)",
    )
    _add_common_args(tote)
    tote.set_defaults(handler=lambda args: _run(LabelKind.TOTE, args))

    printer = subparsers.add_parser(
        "print",
        help="Send every .zpl file in a directory to a CUPS raw queue",
    )
    printer.add_argument(
        "directory",
        type=Path,
        nargs="?",
        default=Path("out/zpl"),
        help="Directory containing .zpl files (default: out/zpl)",
    )
    printer.add_argument(
        "-d",
        "--printer",
        required=True,
        help="CUPS queue name (as created with lpadmin -p)",
    )
    printer.add_argument(
        "--dry-run",
        action="store_true",
        help="List the files that would be printed without submitting jobs",
    )
    printer.set_defaults(
        handler=lambda args: print_zpl_directory(
            args.directory, args.printer, dry_run=args.dry_run
        )
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(args.handler(args))
