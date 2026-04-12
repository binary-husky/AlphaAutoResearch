#!/usr/bin/env python3
"""Adjust seams between adjacent page images.

For each consecutive pair of pages (A, B) in <indir>, consider a flex zone
of the bottom `shift_ratio` of A and the top `shift_ratio` of B. Pick a new
seam inside that zone:
  - If a contiguous background (whitespace) band exists in the zone, put
    the seam at its center — so the whitespace splits evenly into A and B.
  - Otherwise, pick the row with the least non-background content (least
    likely to cut through text/graphics).

The seam shift physically moves pixel rows from one image to its neighbor;
no global stitching is performed. All pages must share the same width.

Usage:
    python3 adjust_seams.py <indir> <outdir> [shift_ratio] [bg_tol]

    shift_ratio : fraction of page height allowed to shift (default 0.20)
    bg_tol      : per-channel tolerance for background detection (default 8)
"""
import glob
import os
import sys

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def detect_bg_color(arr):
    """Sample edge rows/cols; take the median as the background color."""
    h, w, _ = arr.shape
    samples = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]], axis=0)
    return np.median(samples, axis=0)


def bg_row_mask(arr, bg_color, tol):
    """Boolean (H,) — True where the entire row is within `tol` of bg_color."""
    diff = np.abs(arr - bg_color).max(axis=2)  # (H, W)
    return diff.max(axis=1) <= tol


def longest_true_run(mask):
    """Return (start, length) of the longest True run; (-1, 0) if none."""
    if not mask.any():
        return -1, 0
    d = np.diff(mask.astype(np.int8), prepend=0, append=0)
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0]
    lens = ends - starts
    i = int(np.argmax(lens))
    return int(starts[i]), int(lens[i])


def pick_seam(strip, bg_color, tol, orig_seam):
    """Return a row index in [0, strip.shape[0]] for the new seam."""
    mask = bg_row_mask(strip, bg_color, tol)
    start, length = longest_true_run(mask)
    if length > 0:
        return start + length // 2
    # No whitespace band: choose row with least non-bg content,
    # with a mild preference for staying near the original seam.
    diff = np.abs(strip - bg_color).max(axis=2)
    content = (diff > tol).sum(axis=1).astype(np.float32)
    H = strip.shape[0]
    offs = (np.arange(H) - orig_seam).astype(np.float32)
    penalty = (offs / max(H / 2, 1.0)) ** 2 * (content.mean() + 1.0) * 0.1
    return int(np.argmin(content + penalty))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    indir = sys.argv[1]
    outdir = sys.argv[2]
    shift_ratio = float(sys.argv[3]) if len(sys.argv) > 3 else 0.20
    bg_tol = float(sys.argv[4]) if len(sys.argv) > 4 else 8.0
    pad_y = int(sys.argv[5]) if len(sys.argv) > 5 else 60

    paths = sorted(
        glob.glob(os.path.join(indir, "page_*.jpg"))
        + glob.glob(os.path.join(indir, "page_*.jpeg"))
        + glob.glob(os.path.join(indir, "page_*.png"))
    )
    if len(paths) < 2:
        print(f"Need >=2 page_* images in {indir}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(outdir, exist_ok=True)
    pages = [np.asarray(Image.open(p).convert("RGB"), dtype=np.float32) for p in paths]
    W = pages[0].shape[1]
    for p, arr in zip(paths, pages):
        if arr.shape[1] != W:
            print(f"Width mismatch on {p}: {arr.shape[1]} vs {W}", file=sys.stderr)
            sys.exit(1)

    bg_color = detect_bg_color(pages[0])
    print(
        f"bg={bg_color.astype(int).tolist()} tol={bg_tol} "
        f"shift_ratio={shift_ratio} pages={len(pages)}"
    )


    for i in range(len(pages) - 1):
        A, B = pages[i], pages[i + 1]
        Ha, Hb = A.shape[0], B.shape[0]
        page_h = (Ha + Hb) / 2.0
        shift = int(shift_ratio * page_h)
        sa = min(shift, Ha)
        sb = min(shift, Hb)
        if sa == 0 or sb == 0:
            continue

        strip = np.concatenate([A[Ha - sa:], B[:sb]], axis=0)
        new_seam = pick_seam(strip, bg_color, bg_tol, orig_seam=sa)
        delta = new_seam - sa  # >0: push rows from B to A; <0: push A to B

        if delta > 0:
            moved = B[:delta]
            pages[i] = np.concatenate([A, moved], axis=0)
            pages[i + 1] = B[delta:]
        elif delta < 0:
            d = -delta
            moved = A[Ha - d:]
            pages[i] = A[:Ha - d]
            pages[i + 1] = np.concatenate([moved, B], axis=0)

        print(
            f"  seam {i + 1}|{i + 2}: flex=+-{shift}px  delta={delta:+d}px  "
            f"-> {pages[i].shape[0]} / {pages[i + 1].shape[0]}"
        )

    for p, arr in zip(paths, pages):
        out = os.path.join(outdir, os.path.basename(p))
        if pad_y > 0:
            W_ = arr.shape[1]
            bg = np.broadcast_to(bg_color, (pad_y, W_, 3)).astype(np.uint8)
            arr = np.concatenate([bg, arr.astype(np.uint8), bg], axis=0)
        img = Image.fromarray(arr.astype(np.uint8))
        if out.lower().endswith((".jpg", ".jpeg")):
            img.save(out, quality=95)
        else:
            img.save(out)
        print(f"  wrote {out}  {arr.shape[1]}x{arr.shape[0]}")


if __name__ == "__main__":
    main()
