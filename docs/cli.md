# CLI reference

RobotLabels ships a single `robotlabels` command with three subcommands:

| Subcommand | Purpose |
|------------|---------|
| `robotlabels ant` | Generate 60 x 60 mm floor marker labels (Data Matrix + edge text) |
| `robotlabels tote` | Generate 60 x 60 mm tote labels (Data Matrix + bottom text) |
| `robotlabels print` | Send every `.zpl` file in a directory to a CUPS raw queue |

Run commands inside the Poetry environment:

```bash
poetry run robotlabels --help
poetry run robotlabels --version
```

## robotlabels ant

Generate ant floor marker labels from a CSV file.

```bash
poetry run robotlabels ant CSV [-o OUTPUT] [--code-column NAME] [--dpi N] [--size-mm N] [--png] [--pdf] [--zpl]
```

| Argument / flag | Default | Description |
|-----------------|---------|-------------|
| `csv` | required | CSV file with a header row and a code column |
| `-o`, `--output` | `out` | Output directory |
| `--code-column` | `code` | CSV column name containing label codes |
| `--dpi` | `203` | Print resolution in dots per inch |
| `--size-mm` | `60` | Label width and height in millimeters |
| `--png` | off | Write one PNG file per code to `OUTPUT/png/` |
| `--pdf` | off | Write a multi-page `OUTPUT/ant_labels.pdf` |
| `--zpl` | off | Write one ZPL file per code to `OUTPUT/zpl/` |

At least one of `--png`, `--pdf`, or `--zpl` is required (exit code `2` otherwise).

Codes are encoded into the Data Matrix exactly as written in the CSV. See [Creating ant labels](ant-labels.md) for the full workflow.

```bash
poetry run robotlabels ant examples/ant_codes.csv --png --zpl -o out/
```

## robotlabels tote

Generate tote labels from a CSV file. Takes the same arguments as `robotlabels ant`; the PDF is written to `OUTPUT/tote_labels.pdf`.

Values without the `TOTE_` prefix are automatically prefixed (`009203` becomes `TOTE_009203`), and output filenames use the formatted ID. See [Creating tote labels](tote-labels.md) for the full workflow.

```bash
poetry run robotlabels tote examples/tote_codes.csv --png --zpl -o out/
```

## robotlabels print

Submit every `.zpl` file in a directory to a CUPS raw queue, one `lp` job per file, in alphabetical order.

```bash
poetry run robotlabels print [DIRECTORY] -d QUEUE [--dry-run]
```

| Argument / flag | Default | Description |
|-----------------|---------|-------------|
| `directory` | `out/zpl` | Directory containing `.zpl` files (non-recursive) |
| `-d`, `--printer` | required | CUPS queue name (as created with `lpadmin -p`) |
| `--dry-run` | off | List the files that would be printed without submitting jobs |

Requires the `lp` command (CUPS) and a raw queue pointing at your Zebra printer — see the [README printing section](../README.md#printing-on-linux-zebra-203-dpi) for one-time setup and [Printing debugging](printing-debugging.md) if jobs are accepted but nothing prints.

```bash
# Preview what would be printed
poetry run robotlabels print out/zpl -d zebra --dry-run

# Print the batch
poetry run robotlabels print out/zpl -d zebra
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | `print`: one or more `lp` jobs failed, or `lp` is not installed |
| `2` | `ant`/`tote`: no output format flag given; `print`: directory missing or contains no `.zpl` files |

## Typical workflow

```bash
# 1. Generate PNG proofs and print-ready ZPL
poetry run robotlabels ant my_codes.csv --png --zpl -o out/

# 2. Review the PNGs in out/png/ before printing

# 3. Print the whole batch
poetry run robotlabels print out/zpl -d zebra
```
