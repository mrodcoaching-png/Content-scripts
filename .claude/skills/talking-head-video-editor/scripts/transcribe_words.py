#!/usr/bin/env python3
"""Transcribe raw footage with word-level timestamps (openai-whisper via uvx).

Usage:
    transcribe_words.py <video> <out_dir> [--model turbo] [--language en]

Writes <out_dir>/transcript.json:
    {"source": ..., "duration": ..., "segments": [
        {"id": 0, "start": 0.0, "end": 2.4, "text": "...",
         "words": [{"w": "Claude", "start": 0.0, "end": 0.3}, ...]}]}
and prints a compact numbered view (one line per segment) to stdout, which is
what you read to spot retakes and dead space.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("out_dir")
    p.add_argument("--model", default="turbo")
    p.add_argument("--language", default=None)
    a = p.parse_args()

    video = Path(a.video).resolve()
    out = Path(a.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "whisper_raw"
    raw_dir.mkdir(exist_ok=True)

    cmd = ["uvx", "--from", "openai-whisper", "whisper", str(video),
           "--model", a.model, "--word_timestamps", "True",
           "--output_format", "json", "--output_dir", str(raw_dir), "--fp16", "False"]
    if a.language:
        cmd += ["--language", a.language]
    env = {**os.environ, "UV_TORCH_BACKEND": "cpu"}  # avoid pulling CUDA wheels on CPU boxes
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        sys.stderr.write(f"Whisper failed:\n{r.stderr[-4000:]}\n")
        sys.exit(1)

    raw = json.loads((raw_dir / (video.stem + ".json")).read_text())
    segments = []
    for i, s in enumerate(raw.get("segments", [])):
        words = [{"w": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)}
                 for w in s.get("words", [])]
        segments.append({"id": i, "start": round(s["start"], 3), "end": round(s["end"], 3),
                         "text": s["text"].strip(), "words": words})

    doc = {"source": str(video), "duration": duration(video), "segments": segments}
    (out / "transcript.json").write_text(json.dumps(doc, indent=1))

    prev_end = 0.0
    for s in segments:
        gap = s["start"] - prev_end
        flag = f"  [gap {gap:.1f}s]" if gap >= 0.6 else ""
        print(f"#{s['id']:>3} {s['start']:7.2f}-{s['end']:7.2f}{flag}  {s['text']}")
        prev_end = s["end"]
    print(f"\nwrote {out / 'transcript.json'} ({len(segments)} segments, {doc['duration']:.1f}s source)")


if __name__ == "__main__":
    main()
