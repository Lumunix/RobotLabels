# Creating ant labels

Ant labels are **60 x 60 mm floor markers** used by mobile robots to navigate a warehouse. Each label encodes a location code as a Data Matrix symbol, with the same code printed along all four edges for human readability.

## What you need

- Python 3.10+ and RobotLabels installed (see [README](../README.md#installation))
- A CSV file with one location code per row
- **60 x 60 mm** label stock
- A **Zebra ZD888** (203 dpi) or compatible Zebra printer for production output

## Code format

Ant codes are opaque location identifiers. They are encoded into the Data Matrix exactly as written in the CSV — no prefix or transformation is applied.

Example codes:

```text
100000CC100000
100000CC100001
100000CC100002
```

Use whatever format your robot navigation system expects.

## Step 1: Prepare the CSV

Create a CSV with a header row and a `code` column:

```csv
code
100000CC100000
100000CC100001
100000CC100002
```

If your export uses a different column name (for example `location_id`), pass `--code-column location_id` when generating labels.

See [examples/ant_codes.csv](../examples/ant_codes.csv) for a working sample file.

## Step 2: Generate labels

From the project directory:

```bash
poetry run robotlabels ant examples/ant_codes.csv --png --pdf --zpl -o out/
```

Pick the output formats you need:

| Flag | Output | Use case |
|------|--------|----------|
| `--png` | One PNG per code in `out/png/` | Previewing layout, sharing proofs |
| `--pdf` | Multi-page `out/ant_labels.pdf` | Printing from a PDF viewer |
| `--zpl` | One ZPL file per code in `out/zpl/` | Direct printing on a Zebra printer |

At least one format flag is required.

### Preview first (PNG only)

```bash
poetry run robotlabels ant my_codes.csv --png -o preview/
```

Open the PNGs in `preview/png/` and confirm codes, borders, and Data Matrix placement look correct before printing.

### Print-ready ZPL only

```bash
poetry run robotlabels ant my_codes.csv --zpl -o print/
```

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
   lp -d zd888 -o raw out/zpl/100000CC100000.zpl
   ```

4. Calibrate for 60 x 60 mm media if needed:

   - Load square label stock
   - Run the printer's media calibration (hold the feed button on power-up for ZD888)
   - Confirm `^PW480` and `^LL480` in the generated ZPL match your label size at 203 dpi

## Label layout

Each ant label includes:

- A **double border** (outer and inner rounded rectangles)
- A **Data Matrix** symbol centered in the inner area
- The **location code** repeated on all four edges (top, bottom, left, right)
- **Registration tick marks** on each side for alignment

Geometry matches the original BarTender `AntLabelTemplate 60-60 label 2025-3-6.btw` template, scaled to 480 x 480 dots at 203 dpi.

## Common options

| Flag | Default | Description |
|------|---------|-------------|
| `-o`, `--output` | `out` | Output directory |
| `--code-column` | `code` | CSV column containing label codes |
| `--dpi` | `203` | Print resolution (dots per inch) |
| `--size-mm` | `60` | Label width and height in millimeters |

Example with a custom column name:

```bash
poetry run robotlabels ant warehouse_locations.csv --code-column location_id --png --zpl -o out/
```

## Troubleshooting

**"Specify at least one output format"** — Add at least one of `--png`, `--pdf`, or `--zpl`.

**Empty or missing codes** — Check that your CSV has a header row and that `--code-column` matches the column name.

**Scanned code does not match** — The Data Matrix encodes the CSV value verbatim. Verify the source data and re-export if needed.

**Print is misaligned** — Recalibrate the printer for 60 x 60 mm stock and confirm label size settings (`--size-mm 60`, `--dpi 203`).
