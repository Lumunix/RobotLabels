# RobotLabels

Open-source Python replacement for BarTender when generating robot floor and tote labels. Reads codes from a CSV file and produces PNG, PDF, and ZPL output for a **Zebra ZD888-203 dpi** printer on **60 x 60 mm** stock.

Both label types use **Data Matrix** (not QR code) to stay compatible with existing scanners and robot navigation systems.

## Label types

| Command | Template | Layout |
|---------|----------|--------|
| `robotlabels ant` | Ant floor marker | Data Matrix centered inside a double border; code printed on all four edges |
| `robotlabels tote` | Tote label | Data Matrix centered; `TOTE_XXXXXX` text below |

Step-by-step guides:

- [Creating ant labels](docs/ant-labels.md)
- [Creating tote labels](docs/tote-labels.md)

Reference `.btw` files are included in the repo for comparison only. This tool does **not** require BarTender.

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

Run commands inside the Poetry environment:

```bash
poetry run robotlabels ant examples/ant_codes.csv --png -o out/
```

## CSV format

Create a CSV with a header row and one code per line:

**examples/ant_codes.csv**

```csv
code
100000CC100000
100000CC100001
100000CC100002
```

**examples/tote_codes.csv**

```csv
code
TOTE_009201
TOTE_009202
009203
```

For tote labels, values without the `TOTE_` prefix are automatically prefixed (`009203` becomes `TOTE_009203`).

Use `--code-column` if your CSV uses a different column name.

## Usage

Generate all output formats:

```bash
poetry run robotlabels ant examples/ant_codes.csv --png --pdf --zpl -o out/
poetry run robotlabels tote examples/tote_codes.csv --png --pdf --zpl -o out/
```

Output layout:

```text
out/
  png/                 # one PNG per code
  zpl/                 # one ZPL file per code
  ant_labels.pdf       # multi-page PDF (ant command)
  tote_labels.pdf      # multi-page PDF (tote command)
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-o`, `--output` | `out` | Output directory |
| `--code-column` | `code` | CSV column containing label codes |
| `--dpi` | `203` | Print resolution (dots per inch) |
| `--size-mm` | `60` | Label width and height in millimeters |
| `--png` | off | Write PNG files |
| `--pdf` | off | Write a multi-page PDF |
| `--zpl` | off | Write ZPL files for Zebra printers |

At least one of `--png`, `--pdf`, or `--zpl` is required.

### Examples

PNG only:

```bash
poetry run robotlabels ant examples/ant_codes.csv --png -o labels/
```

PDF only:

```bash
poetry run robotlabels tote examples/tote_codes.csv --pdf -o labels/
```

Custom column name:

```bash
poetry run robotlabels ant my_data.csv --code-column location_id --png --zpl -o out/
```

Alternatively, activate the Poetry shell once with `poetry shell`, then run `robotlabels` directly.

## Printing on Linux (Zebra, 203 dpi)

1. Connect the printer via USB and confirm it is detected:

   ```bash
   lsusb | grep -i zebra
   ```

2. Find the CUPS device URI (do not guess the model name):

   ```bash
   lpinfo -v | grep -i zebra
   ```

3. Create a raw CUPS queue (one-time setup). Use the URI from step 2:

   ```bash
   sudo lpadmin -p zebra -E -v "usb://Zebra%20Technologies/ZTC%20ZD421-203dpi%20ZPL?serial=XXXXXXXX" -m raw
   sudo cupsaccept zebra
   sudo cupsenable zebra
   ```

4. Send a ZPL file directly to the printer:

   ```bash
   lp -d zebra -o raw out/zpl/100000CC100000.zpl
   ```

5. Calibrate for 60 x 60 mm media if needed:

   - Load square label stock
   - Run the printer's media calibration (power off, hold **Feed** while powering on)
   - Confirm `^PW480` and `^LL480` in the generated ZPL match your label size at 203 dpi

**Printing problems?** See [Printing debugging](docs/printing-debugging.md) for stuck jobs, wrong CUPS URIs, and printer status lights.

## How it works

1. Reads codes from CSV
2. Encodes each code as a Data Matrix symbol using pure-Python [`ppf-datamatrix`](https://pypi.org/project/ppf-datamatrix/)
3. Draws the label layout (borders, tick marks, text) with Pillow
4. Writes PNG/PDF for proofing, and ZPL that embeds the same rendering as a `^GFA` bitmap — so the printed label always matches the PNG proof pixel for pixel (native ZPL text fields placed rotated text inconsistently across printer models)

Geometry is measured from the embedded preview images in the original BarTender `.btw` templates and scaled to 480 x 480 dots (60 mm at 203 dpi).

## Project layout

```text
pyproject.toml        # Poetry project metadata and dependencies
poetry.lock           # locked dependency versions
robotlabels/
  cli.py          # command-line interface
  csv_io.py       # CSV reader
  datamatrix.py   # Data Matrix encoder wrapper
  render.py       # PNG/PDF rendering
  templates.py    # label geometry
  verify.py       # optional verification helpers
  zpl.py          # ZPL generation
examples/
  ant_codes.csv
  tote_codes.csv
```

## License

MIT
