#!/usr/bin/env python3
"""Fetch an Instagram reel's video and metadata via yt-dlp (run through uvx).

Usage:
    fetch_reel.py <instagram-reel-url> [out_dir] [--cookies COOKIES_FILE]

By default this is fully anonymous -- no login, no cookies. Instagram sometimes blocks
anonymous requests outright (commonly from cloud/datacenter IPs, with an error like
"Instagram sent an empty media response"), in which case pass --cookies pointing at a
Netscape-format cookies.txt exported from a logged-in browser session. This is an explicit
opt-in fallback, never automatic: cookies tie the fetch to a real account, which is a
deliberate tradeoff the caller should make knowingly, not something this script decides on
its own. Never commit a cookies file to git -- it's a live, reusable session credential.

Prints a JSON summary to stdout on success:
    {
      "caption": ...,
      "author": {"username": ..., "display_name": ...},
      "like_count": ...,
      "video_path": ...,
      "info_json_path": ...,
      "source_url": ...
    }

On failure, exits non-zero with the real yt-dlp error on stderr. This does not retry --
Instagram's anonymous access is flaky/rate-limited by nature, and silently retrying just
hides that from the caller.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


def run_yt_dlp(url: str, out_dir: Path, cookies: Optional[str]) -> None:
    # --write-info-json + an actual download in one invocation: one Instagram fetch cycle
    # produces both the video file and a sidecar *.info.json with caption/author/likes.
    out_template = str(out_dir / "%(id)s.%(ext)s")
    cmd = [
        "uvx", "yt-dlp",
        "--no-warnings",
        "--no-playlist",
        "--write-info-json",
        "-f", "mp4/best",
        "-o", out_template,
    ]
    if cookies:
        cmd += ["--cookies", cookies]
    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if cookies:
            hint = (
                "yt-dlp failed even with cookies supplied -- check that the cookies file is "
                "fresh (Instagram sessions expire) and actually belongs to a logged-in "
                "session, then check the error below."
            )
        else:
            hint = (
                "yt-dlp failed to fetch the reel anonymously. This is often Instagram "
                "blocking anonymous requests outright (common from cloud/datacenter IPs), "
                "not a bug in this script. Do not blindly retry -- check the error below "
                "first. If it mentions needing to be logged in or an 'empty media response', "
                "the fallback is to re-run this script with --cookies pointing at a "
                "Netscape-format cookies.txt from a logged-in browser session."
            )
        sys.stderr.write(f"{hint}\n\nyt-dlp stderr:\n{result.stderr}\n")
        sys.exit(1)


def find_info_json(out_dir: Path) -> Path:
    candidates = sorted(out_dir.glob("*.info.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        sys.stderr.write(f"yt-dlp exited successfully but wrote no .info.json in {out_dir}.\n")
        sys.exit(1)
    return candidates[0]


def find_video_file(info: dict, out_dir: Path, info_json_path: Path) -> Path:
    for d in info.get("requested_downloads") or []:
        fp = d.get("filepath") or d.get("_filename")
        if fp and Path(fp).exists():
            return Path(fp)
    for key in ("filepath", "_filename"):
        fp = info.get(key)
        if fp and Path(fp).exists():
            return Path(fp)
    # Fall back to the newest non-JSON file that shares the info.json's basename.
    stem = info_json_path.name[: -len(".info.json")]
    for p in sorted(out_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if p.name.startswith(stem) and not p.name.endswith(".json"):
            return p
    sys.stderr.write("Downloaded metadata but could not locate the video file on disk.\n")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch an Instagram reel via yt-dlp (anonymous by default).")
    parser.add_argument("url", help="Instagram reel URL")
    parser.add_argument(
        "out_dir", nargs="?", default=None,
        help="Directory to save the video + metadata into (default: a new temp dir)",
    )
    parser.add_argument(
        "--cookies", default=None, metavar="COOKIES_FILE",
        help=(
            "Path to a Netscape-format cookies.txt file for authenticated access. Optional "
            "fallback for when anonymous access fails -- never used unless explicitly passed. "
            "Never commit this file to git; it contains a live, reusable session credential."
        ),
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else Path(tempfile.mkdtemp(prefix="reel_"))
    out_dir.mkdir(parents=True, exist_ok=True)

    run_yt_dlp(args.url, out_dir, args.cookies)
    info_json_path = find_info_json(out_dir)
    info = json.loads(info_json_path.read_text())
    video_path = find_video_file(info, out_dir, info_json_path)

    like_count = info.get("like_count")
    if like_count is None:
        sys.stderr.write(
            "Note: like_count was not available (Instagram often withholds it from anonymous "
            "requests). Continuing without it.\n"
        )

    summary = {
        "caption": info.get("description"),
        "author": {
            "username": info.get("uploader_id") or info.get("channel_id"),
            "display_name": info.get("uploader") or info.get("channel"),
        },
        "like_count": like_count,
        "video_path": str(video_path),
        "info_json_path": str(info_json_path),
        "source_url": args.url,
        "authenticated": bool(args.cookies),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
