#!/usr/bin/env python3
"""Grab QA frames from a video and tile them into contact sheets you can look at.

Usage:
    frames.py <video> <out_dir> [--every 1.0] [--at 3.2,7.9] [--cols 4] [--per-sheet 12]

Samples a frame every --every seconds plus any explicit --at timestamps (e.g.
the start/end of each overlay, where layout bugs show up). Each tile is stamped
with its timestamp so you can map a problem back to the composition.
Prints the sheet paths -- open them with your image viewer / Read tool.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def duration(path: str) -> float:
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, check=True).stdout)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("out_dir")
    p.add_argument("--every", type=float, default=1.0)
    p.add_argument("--at", default="")
    p.add_argument("--cols", type=int, default=4)
    p.add_argument("--per-sheet", type=int, default=12)
    a = p.parse_args()

    out = Path(a.out_dir)
    tiles = out / "tiles"
    tiles.mkdir(parents=True, exist_ok=True)
    for old in tiles.glob("*.png"):
        old.unlink()

    total = duration(a.video)
    times = set()
    t = 0.0
    while t < total:
        times.add(round(t, 2))
        t += a.every
    times.update(round(float(x), 2) for x in a.at.split(",") if x.strip())
    times = sorted(x for x in times if 0 <= x < total)

    paths = []
    for i, ts in enumerate(times):
        dst = tiles / f"{i:04d}.png"
        label = f"{ts:.2f}s"
        r = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(ts), "-i", a.video, "-frames:v", "1",
             "-vf", f"scale=360:-2,drawtext=text='{label}':x=8:y=8:fontsize=22:"
                    "fontcolor=yellow:box=1:boxcolor=black@0.6", str(dst)],
            capture_output=True, text=True)
        if r.returncode != 0:  # drawtext may be missing; fall back to an unlabeled frame
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(ts), "-i", a.video,
                            "-frames:v", "1", "-vf", "scale=360:-2", str(dst)], check=True)
        paths.append(dst)

    sheets = []
    for n in range(0, len(paths), a.per_sheet):
        chunk = paths[n:n + a.per_sheet]
        rows = -(-len(chunk) // a.cols)
        sheet = out / f"sheet_{n // a.per_sheet + 1:02d}.png"
        inputs = []
        for c in chunk:
            inputs += ["-i", str(c)]
        # xstack layout: tile i sits at column i%cols, row i//cols (all tiles share w0/h0).
        layout = "|".join(
            f"{'+'.join(['w0'] * (i % a.cols)) or '0'}_{'+'.join(['h0'] * (i // a.cols)) or '0'}"
            for i in range(len(chunk)))
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex",
                            f"xstack=inputs={len(chunk)}:layout={layout}:fill=black", str(sheet)]
                           if len(chunk) > 1 else
                           ["cp", str(chunk[0]), str(sheet)], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"contact sheet failed:\n{r.stderr[-2000:]}")
        sheets.append(sheet)
        print(f"{sheet}  ({times[n]:.2f}s - {times[n + len(chunk) - 1]:.2f}s, {rows}x{a.cols})")


if __name__ == "__main__":
    main()
