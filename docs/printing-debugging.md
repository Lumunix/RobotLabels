# Printing debugging

This guide covers common issues when sending ZPL from Linux to a Zebra desktop printer (for example ZD421 or ZD888 at 203 dpi). The generated ZPL is usually fine — most problems are CUPS setup or physical printer/media state.

## Quick checks

```bash
# Is the printer connected?
lsusb | grep -i zebra

# What URI should CUPS use?
lpinfo -v | grep -i zebra

# Is a job stuck in the queue?
lpstat -o
lpstat -p YOUR_QUEUE_NAME -l
```

If `lp` returns a request id but nothing prints, check the queue device URI and printer status lights before changing ZPL.

## Job accepted but nothing prints

CUPS may accept the job while the queue points at the wrong USB device.

**Symptom:** `lp` reports success (for example `request id is zd888-3`) but no label comes out. `lpstat -p YOUR_QUEUE -l` shows:

```text
Waiting for printer to become available.
```

**Cause:** The queue URI does not match your actual printer. Example: the queue was created with `usb://Zebra/ZD888` but the connected printer is a **ZD421**.

**Fix:**

```bash
# Find the correct URI for your printer
lpinfo -v | grep -i zebra
# Example output:
# direct usb://Zebra%20Technologies/ZTC%20ZD421-203dpi%20ZPL?serial=XXXXXXXX

# Point the queue at the correct device
sudo lpadmin -p YOUR_QUEUE -v "usb://Zebra%20Technologies/ZTC%20ZD421-203dpi%20ZPL?serial=XXXXXXXX"
sudo cupsenable YOUR_QUEUE
sudo cupsaccept YOUR_QUEUE

# Cancel stuck jobs and resubmit
cancel YOUR_QUEUE-3
lp -d YOUR_QUEUE -o raw out/zpl/YOUR_CODE.zpl
```

Use whatever queue name you chose when running `lpadmin -p` (for example `zd888`, `zd421`).

**Note:** ZD421 and ZD888 are both supported at 203 dpi. RobotLabels ZPL uses 480 x 480 dots for 60 x 60 mm stock (`^PW480`, `^LL480`) and works on either model once the queue URI is correct.

## CUPS raw queue warning

You may see:

```text
lpadmin: Raw queues are deprecated and will stop working in a future version of CUPS.
```

Raw queues still work for sending ZPL today. The important part is that the `-v` URI matches your printer.

## Printer status lights (ZD421 / ZD621)

Read the **STATUS**, **SUPPLIES**, and **PAUSE** indicators together.

| Light pattern | Likely meaning | What to do |
|---------------|----------------|------------|
| **SUPPLIES solid red** | Media out, ribbon out, or media not detected | Load 60 x 60 mm labels, close the printhead firmly, press **Feed** once. Run media calibration (below). |
| **STATUS solid red** | Cover/printhead open, media detection error | Close the lid until it clicks. Open and re-close if needed, then press **Pause** to clear pause state. |
| **PAUSE solid amber** | Printer paused | Press **Pause** to resume. |
| **STATUS + PAUSE flashing red** | Printhead over-temperature | Power off (hold **Power** ~5 seconds), let the printer cool, power on again. |
| **STATUS solid green** | Ready | Resubmit the print job. |

A red **SUPPLIES** light means the printer will not print until it detects valid label stock — this is not a ZPL or RobotLabels error.

## Media calibration (60 x 60 mm)

1. Load square 60 x 60 mm direct-thermal labels (no ribbon needed for direct thermal).
2. Thread labels through the guides to the front.
3. Close the printhead.
4. **Calibration:** power off, hold **Feed** while powering on, release when feeding starts, wait until calibration finishes.
5. Confirm the printer feeds one label and the **SUPPLIES** light turns green.
6. Reprint:

   ```bash
   lp -d YOUR_QUEUE -o raw out/zpl/YOUR_CODE.zpl
   ```

## Print misalignment

Generated ZPL embeds the label as a `^GFA` bitmap of the same rendering used for the PNG proofs, so the print always matches the PNG pixel for pixel. Older versions of RobotLabels composed labels from native ZPL text fields (`^A0` with rotation), which printers place inconsistently — if the printed text is misplaced while the PNG looks correct, regenerate the ZPL files with the current version.

If labels print but content is offset or scaled wrong:

- Recalibrate for 60 x 60 mm media (steps above).
- Confirm generated ZPL contains `^PW480` and `^LL480` at 203 dpi.
- Regenerate with explicit size if needed:

  ```bash
  poetry run robotlabels ant examples/ant_codes.csv --zpl --dpi 203 --size-mm 60 -o out/
  ```

## Useful commands

```bash
# Queue status and device URI
lpstat -p YOUR_QUEUE -l
lpstat -v YOUR_QUEUE

# List or cancel jobs
lpstat -o
cancel YOUR_QUEUE-JOBID
cancel -a YOUR_QUEUE

# Test print after fixing URI or media
lp -d YOUR_QUEUE -o raw out/zpl/100000CC100000.zpl
```

## Still stuck?

1. Verify PNG proof looks correct (`out/png/`) — layout issues are separate from printing issues.
2. Confirm the queue URI with `lpinfo -v` matches `lpstat -v YOUR_QUEUE`.
3. Clear the queue, fix media/calibration until lights show ready (green), then resubmit one ZPL file.
