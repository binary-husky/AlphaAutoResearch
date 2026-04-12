#!/usr/bin/env python3
"""Vertically stitch all page_*.jpg/png in <indir> into a single long image.

Usage:
    python3 stitch_long.py <indir> <out_path> [quality]
"""
import glob
import os
import sys

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    indir = sys.argv[1]
    out_path = sys.argv[2]
    quality = int(sys.argv[3]) if len(sys.argv) > 3 else 95

    paths = sorted(
        glob.glob(os.path.join(indir, "page_*.jpg"))
        + glob.glob(os.path.join(indir, "page_*.jpeg"))
        + glob.glob(os.path.join(indir, "page_*.png"))
    )
    if not paths:
        print(f"No page_* images in {indir}", file=sys.stderr)
        sys.exit(1)

    arrs = [np.asarray(Image.open(p).convert("RGB")) for p in paths]
    W = arrs[0].shape[1]
    for p, a in zip(paths, arrs):
        if a.shape[1] != W:
            print(f"Width mismatch on {p}: {a.shape[1]} vs {W}", file=sys.stderr)
            sys.exit(1)

    total_h = sum(a.shape[0] for a in arrs)
    print(f"Stitching {len(arrs)} pages -> {W}x{total_h}")
    long_arr = np.concatenate(arrs, axis=0)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img = Image.fromarray(long_arr)
    if out_path.lower().endswith((".jpg", ".jpeg")):
        if total_h > 65500 or W > 65500:
            print(
                f"warning: {W}x{total_h} exceeds JPEG 65500 limit; saving PNG instead",
                file=sys.stderr,
            )
            out_path = os.path.splitext(out_path)[0] + ".png"
            img.save(out_path, optimize=False, compress_level=6)
        else:
            img.save(out_path, quality=quality)
    else:
        img.save(out_path, optimize=False, compress_level=6)
    print(f"Wrote {out_path} ({W}x{total_h})")


if __name__ == "__main__":
    main()
