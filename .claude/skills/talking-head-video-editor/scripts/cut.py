#!/usr/bin/env python3
"""Cut dead space and dropped segments (retakes/mistakes) out of raw footage.

Usage:
    cut.py <transcript.json> <out_dir> [--drop 3,4,9] [--drop-words 12:3-5]
           [--max-gap 0.35] [--pad 0.08] [--dry-run]

How it decides what to keep:
  * Speech is kept word by word (from Whisper word timestamps), so long pauses
    *inside* a segment get tightened too, not just pauses between segments.
  * Any silence longer than --max-gap is shortened to --max-gap (split evenly
    around the cut), so the edit stays punchy but not breathless.
  * --pad keeps a little air before/after each word so consonants aren't clipped.
  * Real pauses are also found from the audio loudness (Whisper often stretches
    a word over the pause after it), and shortened the same way. Disable with
    --no-audio-silence, or set the threshold with --silence-db.
  * --drop removes whole segments by id (use for retakes/flubs).
  * --drop-words removes a word range inside one segment: "<seg>:<first>-<last>"
    (0-based word indexes, inclusive). Repeatable, comma separated.

Writes:
  <out_dir>/cut.mp4              re-encoded, frame-accurate edit
  <out_dir>/keep_ranges.json     source ranges that were kept
  <out_dir>/cut_transcript.json  transcript re-timed to cut.mp4 (use these
                                 times for overlays/captions)
"""
import argparse
import array
import json
import math
import subprocess
import sys
from pathlib import Path


def parse_drop_words(spec: str):
    out = {}
    if not spec:
        return out
    for part in spec.split(","):
        seg, rng = part.split(":")
        a, b = rng.split("-")
        out.setdefault(int(seg), set()).update(range(int(a), int(b) + 1))
    return out


def quiet_runs(src, min_len, silence_db=None, win=0.05):
    """Find stretches of real silence in the audio.

    Whisper often stretches a word's timestamp over the pause after it ("had......
    all"), so word gaps alone miss many pauses. This measures loudness in 50ms
    windows and returns (start, end, threshold) runs quieter than the threshold.
    Default threshold: the clip's noise floor (10th percentile) + 4 dB, which
    adapts to noisy outdoor recordings.
    """
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-map", "0:a:0", "-ac", "1",
                          "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    pcm = array.array("h")
    pcm.frombytes(raw[: len(raw) // 2 * 2])
    n = int(16000 * win)
    levels = []
    for i in range(0, len(pcm) - n, n):
        chunk = pcm[i:i + n]
        ms = sum(x * x for x in chunk) / n
        levels.append(10 * math.log10(ms + 1e-9) - 90.3)  # dBFS
    if not levels:
        return [], None
    thr = silence_db if silence_db is not None else sorted(levels)[len(levels) // 10] + 4
    runs, start = [], None
    for i, lv in enumerate(levels + [0.0]):
        if lv < thr and start is None:
            start = i
        elif lv >= thr and start is not None:
            if (i - start) * win >= min_len:
                runs.append((start * win, i * win))
            start = None
    return runs, thr


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("transcript")
    p.add_argument("out_dir")
    p.add_argument("--drop", default="")
    p.add_argument("--drop-words", default="")
    p.add_argument("--max-gap", type=float, default=0.35)
    p.add_argument("--pad", type=float, default=0.08)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-audio-silence", action="store_true",
                   help="only use word-timestamp gaps; skip loudness-based pause detection")
    p.add_argument("--silence-db", type=float, default=None,
                   help="loudness (dBFS) below which audio counts as silence (default: auto)")
    a = p.parse_args()

    doc = json.loads(Path(a.transcript).read_text())
    src, total = doc["source"], doc["duration"]
    drop = {int(x) for x in a.drop.split(",") if x.strip()}
    drop_words = parse_drop_words(a.drop_words)

    # Collect kept words in source time.
    kept, idx = [], 0
    for s in doc["segments"]:
        words = s["words"] or [{"w": s["text"], "start": s["start"], "end": s["end"]}]
        for i, w in enumerate(words):
            idx += 1  # global word index, so we know when something was dropped in between
            if s["id"] in drop or i in drop_words.get(s["id"], set()):
                continue
            kept.append({**w, "seg": s["id"], "idx": idx})
    if not kept:
        sys.exit("Nothing left to keep -- check --drop.")

    # Build ranges: pad each word, merge when the silence between is <= max_gap.
    # Never merge across dropped words, even if they were spoken with no pause.
    ranges, prev = [], None
    for w in kept:
        st, en = max(0.0, w["start"] - a.pad), min(total, w["end"] + a.pad)
        contiguous = prev is not None and w["idx"] == prev["idx"] + 1
        if ranges and contiguous and st - ranges[-1][1] <= a.max_gap:
            ranges[-1][1] = max(ranges[-1][1], en)
        else:
            if ranges and not contiguous:
                # Pull both edges back to the word boundaries so no dropped audio leaks in.
                ranges[-1][1] = min(ranges[-1][1], prev["end"] + 0.02)
                st = max(st, w["start"] - 0.02)
            ranges.append([st, en])
        prev = w
    # Shorten real pauses hidden inside word timestamps (see quiet_runs).
    if not a.no_audio_silence:
        runs, thr = quiet_runs(src, a.max_gap + 0.15, a.silence_db)
        if runs:
            print(f"audio pauses below {thr:.1f} dBFS: " +
                  ", ".join(f"{x:.2f}-{y:.2f}" for x, y in runs))
        for qs, qe in runs:
            keep_half = a.max_gap / 2
            cs, ce = qs + keep_half, qe - keep_half  # remove the middle, keep max_gap of air
            new = []
            for st, en in ranges:
                if ce <= st or cs >= en:
                    new.append([st, en])
                    continue
                if cs > st:
                    new.append([st, cs])
                if ce < en:
                    new.append([ce, en])
            ranges = new
    ranges = [[round(x, 3), round(y, 3)] for x, y in ranges if y - x > 0.05]

    # Re-time words onto the cut timeline.
    offsets, t = [], 0.0
    for st, en in ranges:
        offsets.append((st, en, t))
        t += en - st
    cut_total = t

    def remap(x):
        for st, en, off in offsets:
            if st - 1e-6 <= x <= en + 1e-6:
                return round(off + (x - st), 3)
        # x fell inside a removed pause: snap to the edge of the nearest kept piece.
        best = None
        for st, en, off in offsets:
            for edge, mapped in ((st, off), (en, off + en - st)):
                if best is None or abs(edge - x) < best[0]:
                    best = (abs(edge - x), mapped)
        return round(best[1], 3) if best and best[0] < 2.0 else None

    cut_segments = {}
    for w in kept:
        ns, ne = remap(w["start"]), remap(w["end"])
        if ns is None or ne is None:
            continue
        seg = cut_segments.setdefault(w["seg"], {"id": w["seg"], "words": []})
        seg["words"].append({"w": w["w"], "start": ns, "end": ne})
    segs_out = []
    for seg in cut_segments.values():
        seg["start"], seg["end"] = seg["words"][0]["start"], seg["words"][-1]["end"]
        seg["text"] = " ".join(x["w"] for x in seg["words"])
        segs_out.append(seg)

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "keep_ranges.json").write_text(json.dumps(ranges, indent=1))
    (out / "cut_transcript.json").write_text(json.dumps(
        {"source": str((out / "cut.mp4").resolve()), "duration": round(cut_total, 3),
         "segments": segs_out}, indent=1))

    print(f"source {total:.1f}s -> cut {cut_total:.1f}s ({len(ranges)} pieces, "
          f"{total - cut_total:.1f}s removed)")
    if a.dry_run:
        for s in segs_out:
            print(f"#{s['id']:>3} {s['start']:7.2f}-{s['end']:7.2f}  {s['text']}")
        return

    parts, labels = [], []
    for i, (st, en) in enumerate(ranges):
        parts.append(f"[0:v]trim=start={st}:end={en},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim=start={st}:end={en},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.01,afade=t=out:st={max(0, en - st - 0.01):.3f}:d=0.01[a{i}];")
        labels.append(f"[v{i}][a{i}]")
    graph = "".join(parts) + "".join(labels) + f"concat=n={len(ranges)}:v=1:a=1[v][a]"
    graph_file = out / "cut_filter.txt"
    graph_file.write_text(graph)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", src, "-filter_complex_script", str(graph_file),
           "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-r", "30", "-g", "30", "-keyint_min", "30",  # dense keyframes: HyperFrames seeks per frame "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
           str(out / "cut.mp4")]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed:\n{r.stderr[-3000:]}")
    print(f"wrote {out / 'cut.mp4'} and {out / 'cut_transcript.json'}")


if __name__ == "__main__":
    main()
