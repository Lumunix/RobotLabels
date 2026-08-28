# RobotLabels

Open-source Python tool for generating robot floor and tote labels. Reads floor or tote codes from a CSV file and produces PNG, PDF, and ZPL output for a **Zebra ZD888-203 dpi** printer on **60 x 60 mm** stock.

Both label types use **Data Matrix** (not QR code) to stay compatible with existing scanners and robot navigation systems.

## Label types

| Command | Template | Layout |
|---------|----------|--------|
| `robotlabels floor` | Floor marker | Data Matrix centered inside a double border; code printed on all four edges |
| `robotlabels tote` | Tote label | Data Matrix centered; `TOTE_XXXXXX` text below |

## Documentation

- [Creating floor labels](docs/floor-labels.md) — full workflow from CSV to printed floor marker
- [Creating tote labels](docs/tote-labels.md) — full workflow, including `TOTE_` prefix rules
- [CLI reference](docs/cli.md) — all subcommands, flags, and exit codes
- [Printing debugging](docs/printing-debugging.md) — stuck jobs, wrong CUPS URIs, printer status lights

## Requirements

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation)
- Linux, macOS, or Windows

## Installation

From the project directory:

```bash
poetry install
```

Optional decode verification (requires the system `libdmtx` library):

```bash
poetry install --extras verify
```

## Quick start

Create a CSV with a header row and one floor or tote code per line (see `examples/`):

```csv
code
100000CC100000
100000CC100001
```

Generate labels:

```bash
poetry run robotlabels floor examples/floor_codes.csv --png --pdf --zpl -o out/
poetry run robotlabels tote examples/tote_codes.csv --png --pdf --zpl -o out/
```

Output layout:

```text
out/
  png/                 # one PNG per code
  zpl/                 # one ZPL file per code
  floor_labels.pdf      # multi-page PDF (floor command)
  tote_labels.pdf      # multi-page PDF (tote command)
```

At least one of `--png`, `--pdf`, or `--zpl` is required. See the [CLI reference](docs/cli.md) for all flags (`--code-column`, `--dpi`, `--size-mm`, ...).

## Printing on Linux (Zebra, 203 dpi)

One-time setup — create a raw CUPS queue using the device URI from `lpinfo -v | grep -i zebra`:

```bash
sudo lpadmin -p zebra -E -v "usb://Zebra%20Technologies/ZTC%20ZD421-203dpi%20ZPL?serial=XXXXXXXX" -m raw
sudo cupsaccept zebra
sudo cupsenable zebra
```

Print a single label or a whole directory (add `--dry-run` to preview the file list first):

```bash
lp -d zebra -o raw out/zpl/100000CC100000.zpl
poetry run robotlabels print out/zpl -d zebra
```

The label guides cover the full setup step by step, including media calibration. If a job is accepted but nothing prints, see [Printing debugging](docs/printing-debugging.md).

## How it works

1. Reads codes from CSV
2. Encodes each code as a Data Matrix symbol using pure-Python [`ppf-datamatrix`](https://pypi.org/project/ppf-datamatrix/)
3. Draws the label layout (borders, tick marks, text) with Pillow
4. Writes PNG/PDF for proofing, and ZPL that embeds the same rendering as a `^GFA` bitmap — so the printed label always matches the PNG proof pixel for pixel (native ZPL text fields placed rotated text inconsistently across printer models)

Layout geometry is defined in `robotlabels/templates.py` and scaled to 480 x 480 dots (60 mm at 203 dpi).

## Project layout

```text
pyproject.toml        # Poetry project metadata and dependencies
poetry.lock           # locked dependency versions
robotlabels/
  cli.py          # command-line interface
  csv_io.py       # CSV reader
  datamatrix.py   # Data Matrix encoder wrapper
  print_labels.py # batch printing of ZPL files via CUPS
  render.py       # PNG/PDF rendering
  templates.py    # label geometry
  verify.py       # optional verification helpers
  zpl.py          # ZPL generation
examples/
  floor_codes.csv
  tote_codes.csv
```

## License

MIT
