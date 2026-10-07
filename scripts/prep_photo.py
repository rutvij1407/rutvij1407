"""Prep a photo for ASCII conversion: cut out the subject, boost contrast, crop.

    python scripts/prep_photo.py path/to/photo.png [--crop TOP_FRACTION]

--crop keeps the top fraction of the subject's bounding box (default 0.42,
roughly head to chest for a full-body shot). Writes source-prepped.png.
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

OUT = Path(__file__).resolve().parent.parent / "source-prepped.png"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--crop", type=float, default=0.42)
    args = ap.parse_args()

    rgba = remove(Image.open(args.photo).convert("RGB"))  # background -> transparent
    alpha = np.array(rgba)[:, :, 3]

    # Crop to the subject, keeping only the top part of its bounding box.
    ys, xs = np.nonzero(alpha > 32)
    top, bottom = ys.min(), ys.min() + int((ys.max() - ys.min()) * args.crop)
    band = alpha[top:bottom] > 32
    cols = np.nonzero(band.any(axis=0))[0]
    pad = int((bottom - top) * 0.04)
    box = (max(cols.min() - pad, 0), max(top - pad, 0),
           min(cols.max() + pad, rgba.width), min(bottom, rgba.height))
    rgba = rgba.crop(box)

    # Local contrast (CLAHE) so a flat-lit face gets real highlights and shadows.
    gray = cv2.cvtColor(np.array(rgba.convert("RGB")), cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)

    # Composite onto white so the background maps to the blank end of the ramp.
    a = np.array(rgba)[:, :, 3].astype(np.float32) / 255
    # Subject is capped at 250 so pure white (255) always means "background".
    out = (np.minimum(gray, 250) * a + 255 * (1 - a)).astype(np.uint8)
    Image.fromarray(out, "L").save(OUT)
    print(f"wrote {OUT.name} ({out.shape[1]}x{out.shape[0]})")


if __name__ == "__main__":
    main()
