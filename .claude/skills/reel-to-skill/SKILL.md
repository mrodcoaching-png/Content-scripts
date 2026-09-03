---
name: reel-to-skill
description: Turns an Instagram reel into a new, ready-to-use Claude Code skill. Use this whenever the user pastes an Instagram reel URL (instagram.com/reel/... or /p/... or a share link that resolves to one) and wants the technique, workflow, recipe, or process it demonstrates turned into a skill or agent -- phrases like "turn this reel into a skill", "make this a skill", "reel to skill", "learn this workflow from this video", or simply pasting a reel link with no other context. Downloads the reel anonymously, transcribes the audio, and hands the transcript + caption + author off to skill-creator to build the new skill. Make sure to use this whenever an Instagram reel/video URL appears in the conversation, even if the user doesn't explicitly say the word "skill".
---

# Reel to Skill

Turn an Instagram reel into a new Claude Code skill: fetch the reel, transcribe it, then
hand the content to `skill-creator` to author the actual skill. The whole thing should take
a couple of minutes end to end.

## Why this shape

Steps 1 and 2 are mechanical (download a file, run a fixed transcription model on it) --
there's nothing for you to reason about there, so they're scripted for speed and reliability.
Step 3 is the opposite: turning a raw transcript into a well-scoped, well-triggered skill
requires real judgment (what's the actual reusable technique here? what should the skill be
named? does it need bundled scripts?), so that step is *not* scripted -- you do it directly,
with `skill-creator`'s help.

## Steps

### 1. Fetch the reel

Run the fetch script with the reel URL. Give it an explicit working directory so you know
where the downloaded files live (use a scratch/temp directory, not a permanent one -- the
video gets deleted in step 4):

```bash
python3 .claude/skills/reel-to-skill/scripts/fetch_reel.py "<reel-url>" /tmp/reel-to-skill/<run-id>
```

This shells out to `uvx yt-dlp` (no install needed, no login/cookies -- fully anonymous). On
success it prints a JSON object to stdout with `caption`, `author` (`username` +
`display_name`), `like_count`, and `video_path`. Parse that JSON.

**If it fails:** the script exits non-zero and prints yt-dlp's actual error to stderr.
Instagram's anonymous access is rate-limited and can break without notice -- don't retry
blindly. Show the real error to the user and stop; only retry if the error clearly indicates
a transient network blip.

### 2. Transcribe the video

```bash
python3 .claude/skills/reel-to-skill/scripts/transcribe.py "<video_path>" /tmp/reel-to-skill/<run-id>
```

This runs `openai-whisper` (the `turbo` model, via `uvx` -- nothing to pre-install) on the
video. It also auto-installs `ffmpeg` via `apt-get` if it's missing, since Whisper needs it
to decode audio. Runs on CPU (no GPU assumed) -- fine for reel-length clips, typically well
under a minute of wall-clock time.

On success it prints JSON with `transcript_path` and `transcript` (the full text). If the
transcript comes back empty, the clip is probably music-only or silent -- tell the user and
ask whether to proceed with just the caption, since there may not be a spoken workflow to
capture.

### 3. Hand off to skill-creator

You now have `transcript`, `caption`, `author`, and `like_count`. Invoke the `skill-creator`
skill directly (do not try to replicate its process yourself) with a prompt along these
lines:

> Build a new Claude Code skill or agent that captures the workflow/technique this Instagram
> reel is teaching. Base it on the transcript below (the primary source -- it's what the
> creator actually said/demonstrated), using the caption and author for extra context.
>
> Author: `<author.display_name>` (`<author.username>`)
> Caption: `<caption>`
> Transcript: `<transcript>`

Let `skill-creator` drive from there -- it will ask clarifying questions if the transcript is
ambiguous about what the reusable technique actually is (a reel is a source to interview
against, not a spec to transcribe literally). Follow its normal process for drafting,
naming, and (if the user wants) testing the skill.

**Tell skill-creator explicitly to save the finished skill to the user's global skill
directory, `~/.claude/skills/`** (not this project repo) -- reels teach general techniques,
not something specific to the `Content-scripts` project.

### 4. Record and clean up

Once the new skill exists, save a lightweight record of this run so there's a durable trail
of what reel produced which skill -- but do **not** keep the video or any intermediate audio
files; those are large and disposable, and shouldn't end up in this repo.

Write a small record to `reels/<author-username-or-slug>-<yyyy-mm-dd>/reel.md` in this repo
(create the `reels/` directory if it doesn't exist), containing:

```markdown
# <caption's first line, or "Reel by <author>">

- Source: <reel URL>
- Author: <display_name> (<username>)
- Likes: <like_count, or "not available">
- Fetched: <date>
- Skill created: <name and path of the skill skill-creator produced>

## Caption

<full caption>

## Transcript

<full transcript>
```

Then delete the working directory from step 1 (`/tmp/reel-to-skill/<run-id>`, video + info
JSON + transcript included) -- everything worth keeping is now in the record above and in
the new skill itself.

## Notes

- This only handles Instagram reels. A non-Instagram URL, or an Instagram URL that isn't a
  reel/post, should be flagged to the user rather than passed through blindly.
- Anonymous scraping is inherently fragile. If fetches start failing consistently (not just
  a one-off), say so plainly -- the fix would be providing yt-dlp with a cookies file for
  authenticated access, which is a deliberate tradeoff the user would need to opt into, not
  something to silently fall back to.
