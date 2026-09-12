#!/usr/bin/env python3
"""
Turn a word-timestamped transcript into karaoke-style caption chunks.

Input: a JSON transcript with word-level timestamps, in either shape:
  - Whisper-style: {"segments": [{"words": [{"word": "hi", "start": 0.12, "end": 0.34}, ...]}, ...]}
  - Flat: {"words": [{"word": "hi", "start": 0.12, "end": 0.34}, ...]}

Output: a JSON list of caption chunks: [{"text": "hi there", "start": 0.08, "end": 1.02}, ...]

Chunking rule: group words 1-3 at a time, starting a new chunk when the gap since the
previous word exceeds GAP_THRESHOLD seconds, or when the previous word ends in punctuation,
or when the current chunk already has MAX_WORDS words.

Display timing: each chunk is shown from (its first word's start - LEAD) until the *next*
chunk's (first word's start - LEAD). This means a chunk's displayed end is always defined by
where the next one begins, never by the chunk's own last word ending -- cutting at your own
end time instead is exactly what causes two captions to visibly overlap on screen. The final
chunk is shown until its own last word's end plus LEAD, since there's no next chunk to key off.

All timestamps are rounded to the nearest frame boundary (1/FPS) before being written out,
since the renderer scrubs to specific frames and sub-frame timestamps just get truncated
inconsistently downstream.
"""
import argparse
import json
import sys

GAP_THRESHOLD = 0.45
LEAD = 0.04
MAX_WORDS = 3
PUNCTUATION = (".", "!", "?", ";", ":", ",")


def normalize_word(w):
    text = w.get("word", w.get("text", "")).strip()
    return {"word": text, "start": w["start"], "end": w["end"]}


def extract_words(transcript):
    # hyperframes `transcribe --json` emits a flat top-level list of
    # {"text": ..., "start": ..., "end": ...} entries.
    if isinstance(transcript, list):
        raw = transcript
    elif "words" in transcript:
        raw = transcript["words"]
    else:
        raw = []
        for segment in transcript.get("segments", []):
            raw.extend(segment.get("words", []))
    words = [normalize_word(w) for w in raw]
    if not words:
        raise ValueError(
            "No word-level timestamps found. This script needs a transcript with "
            "per-word start/end times (e.g. `npx hyperframes transcribe ... --json`), "
            "not just segment-level timestamps."
        )
    return words


def round_to_frame(t, fps):
    return round(t * fps) / fps


def chunk_words(words):
    chunks = []
    current = []
    prev_end = None
    for w in words:
        text = w["word"].strip()
        if not text:
            continue
        start, end = w["start"], w["end"]
        starts_new_chunk = current and (
            len(current) >= MAX_WORDS
            or (prev_end is not None and start - prev_end > GAP_THRESHOLD)
            or current[-1]["word"].strip().endswith(PUNCTUATION)
        )
        if starts_new_chunk:
            chunks.append(current)
            current = []
        current.append({"word": text, "start": start, "end": end})
        prev_end = end
    if current:
        chunks.append(current)
    return chunks


def build_caption_chunks(words, fps):
    word_chunks = chunk_words(words)
    if not word_chunks:
        return []

    raw_starts = [wc[0]["start"] for wc in word_chunks]
    captions = []
    for i, wc in enumerate(word_chunks):
        text = " ".join(w["word"] for w in wc)
        display_start = raw_starts[i] - LEAD
        if i + 1 < len(word_chunks):
            display_end = raw_starts[i + 1] - LEAD
        else:
            display_end = wc[-1]["end"] + LEAD
        captions.append(
            {
                "text": text,
                "start": round_to_frame(max(display_start, 0), fps),
                "end": round_to_frame(display_end, fps),
            }
        )
    return captions


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("transcript", help="Path to the word-timestamped transcript JSON")
    parser.add_argument("--out", help="Output path for caption chunks JSON (default: stdout)")
    parser.add_argument("--fps", type=int, default=30, help="Frame rate to round timestamps to (default: 30)")
    args = parser.parse_args()

    with open(args.transcript) as f:
        transcript = json.load(f)

    words = extract_words(transcript)
    captions = build_caption_chunks(words, args.fps)

    output = json.dumps(captions, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(output)
        print(f"Wrote {len(captions)} caption chunks to {args.out}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
