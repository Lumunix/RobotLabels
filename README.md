# RobotLabels

Open-source Python replacement for BarTender when generating robot floor and tote labels. Reads codes from a CSV file and produces PNG, PDF, and ZPL output for a **Zebra ZD888-203 dpi** printer on **60 x 60 mm** stock.

Both label types use **Data Matrix** (not QR code) to stay compatible with existing scanners and robot navigation systems.

## Label types

| Command | Template | Layout |
|---------|----------|--------|
| `robotlabels ant` | Ant floor marker | Data Matrix centered inside a double border; code printed on all four edges |
| `robotlabels tote` | Tote label | Data Matrix centered; `TOTE_XXXXXX` text below |

Reference `.btw` files are included in the repo for comparison only. This tool does **not** require BarTender.

## Requirements

- Python 3.10+
- Linux, macOS, or Windows

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional decode verification (requires the system `libdmtx` library):

```bash
pip install -e ".[verify]"
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
robotlabels ant examples/ant_codes.csv --png --pdf --zpl -o out/
robotlabels tote examples/tote_codes.csv --png --pdf --zpl -o out/
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
robotlabels ant examples/ant_codes.csv --png -o labels/
```

PDF only:

```bash
robotlabels tote examples/tote_codes.csv --pdf -o labels/
```

Custom column name:

```bash
robotlabels ant my_data.csv --code-column location_id --png --zpl -o out/
```

Run without installing (from repo root):

```bash
PYTHONPATH=. python3 -m robotlabels ant examples/ant_codes.csv --png -o out/
```

## Printing on Linux (Zebra ZD888)

1. Connect the printer via USB and confirm it is detected:

   ```bash
   lsusb | grep -i zebra
   ```

2. Create a raw CUPS queue (one-time setup):

   ```bash
   sudo lpadmin -p zd888 -E -v usb://Zebra/ZD888 -m raw
   sudo cupsaccept zd888
   sudo cupsenable zd888
   ```

   Adjust the `-v` URI to match your system (`lpinfo -v` lists available devices).

3. Send a ZPL file directly to the printer:

   ```bash
   lp -d zd888 -o raw out/zpl/100000CC100000.zpl
   ```

4. Calibrate for 60 x 60 mm media if needed:

   - Load square label stock
   - Run the printer's media calibration (hold the feed button on power-up for ZD888)
   - Confirm `^PW480` and `^LL480` in the generated ZPL match your label size at 203 dpi

## How it works

1. Reads codes from CSV
2. Encodes each code as a Data Matrix symbol using pure-Python [`ppf-datamatrix`](https://pypi.org/project/ppf-datamatrix/)
3. Draws the label layout (borders, tick marks, text) with Pillow
4. Writes PNG/PDF for proofing and ZPL with native `^BX` Data Matrix commands for production printing

Geometry is measured from the embedded preview images in the original BarTender `.btw` templates and scaled to 480 x 480 dots (60 mm at 203 dpi).

## Project layout

```text
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

## Rename this repository to RobotLabels

The GitHub repo is currently named `BTWLabels`. To rename it:

1. On GitHub: **Settings → General → Repository name → `RobotLabels`**
2. Update your local remote:

   ```bash
   git remote set-url origin https://github.com/Lumunix/RobotLabels.git
   ```

3. Optionally rename the local folder from `BTWLabels` to `RobotLabels` and reopen the workspace in Cursor.

If you use the GitHub CLI:

```bash
gh repo rename RobotLabels
```

## License

MIT
