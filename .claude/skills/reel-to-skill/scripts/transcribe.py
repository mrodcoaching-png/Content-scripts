#!/usr/bin/env python3
"""Transcribe a downloaded video to plain text with openai-whisper's "turbo" model, run through uvx.

Usage:
    transcribe.py <video_path> [out_dir]

Uses openai-whisper (CPU-friendly, not mlx-whisper -- this targets a cloud Linux sandbox,
not Apple Silicon). Whisper needs the ffmpeg binary on PATH; this script installs it via
apt-get if it's missing.

Prints a JSON summary to stdout on success:
    {"transcript_path": ..., "transcript": ...}
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg"):
        return
    sys.stderr.write("ffmpeg not found on PATH; installing it via apt-get...\n")
    install = subprocess.run(
        "apt-get update -qq && apt-get install -y -qq ffmpeg",
        shell=True, capture_output=True, text=True,
    )
    if install.returncode != 0 or not shutil.which("ffmpeg"):
        sys.stderr.write(
            "Could not install ffmpeg automatically -- Whisper needs it to decode audio.\n"
            f"apt-get stdout:\n{install.stdout}\napt-get stderr:\n{install.stderr}\n"
            "Install ffmpeg manually (e.g. `apt-get install -y ffmpeg`) and re-run this script.\n"
        )
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe a video with Whisper (turbo model) via uvx.")
    parser.add_argument("video_path", help="Path to the downloaded video file")
    parser.add_argument(
        "out_dir", nargs="?", default=None,
        help="Directory to write the .txt transcript into (default: the video's own directory)",
    )
    args = parser.parse_args()

    video_path = Path(args.video_path)
    if not video_path.exists():
        sys.stderr.write(f"Video file not found: {video_path}\n")
        sys.exit(1)

    out_dir = Path(args.out_dir) if args.out_dir else video_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    ensure_ffmpeg()

    cmd = [
        "uvx", "--from", "openai-whisper", "whisper",
        str(video_path),
        "--model", "turbo",
        "--output_format", "txt",
        "--output_dir", str(out_dir),
        "--fp16", "False",  # no GPU in this sandbox; avoid the fp16-on-CPU warning
    ]
    # This sandbox has no GPU, so pin torch to the CPU-only wheel -- otherwise uv resolves
    # the default PyPI torch build, which drags in several GB of unused CUDA libraries.
    env = {**os.environ, "UV_TORCH_BACKEND": "cpu"}
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        sys.stderr.write(
            f"Whisper transcription failed.\n\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}\n"
        )
        sys.exit(1)

    transcript_path = out_dir / (video_path.stem + ".txt")
    if not transcript_path.exists():
        sys.stderr.write(
            f"Whisper ran but no transcript file was found at the expected path {transcript_path}.\n"
            f"whisper stdout:\n{result.stdout}\n"
        )
        sys.exit(1)

    transcript_text = transcript_path.read_text().strip()
    if not transcript_text:
        sys.stderr.write("Warning: transcript is empty (no speech detected, or a silent/music-only clip).\n")

    print(json.dumps({
        "transcript_path": str(transcript_path),
        "transcript": transcript_text,
    }, indent=2))


if __name__ == "__main__":
    main()
