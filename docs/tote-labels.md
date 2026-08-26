# Creating tote labels

Tote labels are **60 x 60 mm labels** affixed to warehouse totes. Each label shows a Data Matrix encoding the tote ID, with human-readable `TOTE_XXXXXX` text below the symbol.

## What you need

- Python 3.10+ and RobotLabels installed (see [README](../README.md#installation))
- A CSV file with one tote ID per row
- **60 x 60 mm** label stock
- A **Zebra ZD888** (203 dpi) or compatible Zebra printer for production output

## Code format

Tote IDs use the `TOTE_` prefix. Values in the CSV **without** the prefix are automatically prefixed:

| CSV value | Encoded / printed as |
|-----------|----------------------|
| `TOTE_009201` | `TOTE_009201` |
| `009202` | `TOTE_009202` |

The Data Matrix and bottom text both use the formatted value.

Example codes:

```text
TOTE_009201
TOTE_009202
009203
```

The last row above becomes `TOTE_009203` on the label.

## Step 1: Prepare the CSV

Create a CSV with a header row and a `code` column:

```csv
code
TOTE_009201
TOTE_009202
009203
```

If your export uses a different column name, pass `--code-column` when generating labels.

See [examples/tote_codes.csv](../examples/tote_codes.csv) for a working sample file.

## Step 2: Generate labels

From the project directory:

```bash
poetry run robotlabels tote examples/tote_codes.csv --png --pdf --zpl -o out/
```

Pick the output formats you need:

| Flag | Output | Use case |
|------|--------|----------|
| `--png` | One PNG per code in `out/png/` | Previewing layout, sharing proofs |
| `--pdf` | Multi-page `out/tote_labels.pdf` | Printing from a PDF viewer |
| `--zpl` | One ZPL file per code in `out/zpl/` | Direct printing on a Zebra printer |

At least one format flag is required.

### Preview first (PNG only)

```bash
poetry run robotlabels tote my_totes.csv --png -o preview/
```

Open the PNGs in `preview/png/` and confirm tote IDs and Data Matrix placement look correct before printing.

### Print-ready ZPL only

```bash
poetry run robotlabels tote my_totes.csv --zpl -o print/
```

ZPL filenames use the formatted tote ID (for example `TOTE_009201.zpl`).

## Step 3: Print on Linux (Zebra ZD888)

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

3. Send a ZPL file to the printer:

   ```bash
   lp -d zd888 -o raw out/zpl/TOTE_009201.zpl
   ```

4. Calibrate for 60 x 60 mm media if needed:

   - Load square label stock
   - Run the printer's media calibration (hold the feed button on power-up for ZD888)
   - Confirm `^PW480` and `^LL480` in the generated ZPL match your label size at 203 dpi

## Label layout

Each tote label includes:

- A **single rounded border**
- A **Data Matrix** symbol centered in the label
- **Tote ID text** below the symbol (for example `TOTE_009201`)
- **Registration tick marks** on each side for alignment

Geometry matches the original BarTender `ToteLabelTemplate 60-60 2025-3-6.btw` template, scaled to 480 x 480 dots at 203 dpi.

## Common options

| Flag | Default | Description |
|------|---------|-------------|
| `-o`, `--output` | `out` | Output directory |
| `--code-column` | `code` | CSV column containing tote IDs |
| `--dpi` | `203` | Print resolution (dots per inch) |
| `--size-mm` | `60` | Label width and height in millimeters |

Example with a custom column name:

```bash
poetry run robotlabels tote tote_export.csv --code-column tote_id --png --zpl -o out/
```

## Troubleshooting

**"Specify at least one output format"** — Add at least one of `--png`, `--pdf`, or `--zpl`.

**Tote ID missing the `TOTE_` prefix on the label** — Values are auto-prefixed unless they already start with `TOTE_` (case-insensitive). If your system expects a different prefix, include the full ID in the CSV.

**Scanned code does not match** — The Data Matrix encodes the formatted value (with `TOTE_` prefix). Confirm your scanner or WMS expects that format.

**Print is misaligned** — Recalibrate the printer for 60 x 60 mm stock and confirm label size settings (`--size-mm 60`, `--dpi 203`).
