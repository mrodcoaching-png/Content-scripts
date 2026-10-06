---
name: talking-head-video-editor
description: Edits raw talking-head footage (Reels, TikTok, Shorts, YouTube clips) end to end with Claude + HyperFrames, the free open-source HTML-to-video framework from HeyGen. It transcribes with Whisper, cuts dead space, mistakes and retakes, adds animated overlays and captions from a plain-English brief, checks the frames and fixes problems, then renders an MP4. Use this whenever the user hands over a raw video/recording and wants it edited, trimmed, "cleaned up", captioned, made into a reel, or given motion graphics / animations / b-roll-style cards, or mentions HyperFrames or "have Claude edit my video" — even if they never say "talking head".
---

# Talking-Head Video Editor (Claude + HyperFrames)

Turn a raw selfie-style recording into a finished, edited video with no manual
editing. This follows Colton Dean's workflow ("Claude can fully edit videos now"):

1. **Setup**: install HyperFrames and Whisper
2. **Clean cut**: transcribe, then remove dead space and every mistake or retake
3. **Brief**: the user explains how they want it edited (more specific = better)
4. **Build**: compose the edit in HyperFrames (animations, captions, clips)
5. **QA**: screenshot the frames and fix anything that looks off *before* the final render
6. **Render** and hand over the MP4
7. **Reuse**: if the user keeps asking for the same style, turn it into a style preset or skill

The split of work: the scripts in `scripts/` do the mechanical parts (word-level
transcription, frame-accurate cutting, contact sheets). You do the parts that
need judgment: which takes are mistakes, what the overlays should say and show,
and whether a frame looks right.

## 1. Setup (once per machine)

Check first, then install only what's missing:

- **Node 22+**, **ffmpeg/ffprobe**, **uvx** (`node --version`, `which ffmpeg uvx`).
  Install ffmpeg with the OS package manager if missing. Then run
  `npx hyperframes doctor`; if it flags Chrome, run `npx hyperframes browser ensure`
  (local rendering needs Chrome Headless Shell). Docker, TTS, and music items
  in `doctor` are optional.
- **HyperFrames skills** teach you its composition syntax (data attributes,
  GSAP rules, catalog blocks). Prefer the plugin:
  `claude plugin marketplace add heygen-com/hyperframes && claude plugin install hyperframes@hyperframes`,
  or `npx skills add heygen-com/hyperframes` (pick "Core Skills"). After that,
  **follow the HyperFrames skills for composition details**. They track the
  current API better than anything written here.
- **Whisper** needs no install: `scripts/transcribe_words.py` runs it via `uvx`
  (first run downloads the model, about 1.5 GB for `turbo`).

Repo: https://github.com/heygen-com/hyperframes (Apache-2.0, free).

## 2. Transcribe and clean cut

Keep everything in a project folder next to the footage, e.g. `<name>-edit/`.

Phone footage is often 4K HEVC with a rotation flag. Normalize it to 1080p H.264
first: it transcodes faster, and HyperFrames' headless Chrome can't decode HEVC
reliably. (ffmpeg applies the rotation automatically.)

```bash
ffmpeg -i raw.MOV -map 0:v:0 -map 0:a:0 -vf "scale=1080:1920,format=yuv420p" \
  -c:v libx264 -crf 17 -c:a aac -b:a 192k raw1080.mp4   # 1920:1080 for landscape
```

```bash
python3 <skill>/scripts/transcribe_words.py raw.mp4 <name>-edit/
```

This prints a numbered line per segment with `[gap Ns]` flags. Read the whole
thing and decide what goes:

- **Retakes**: the same line said twice or more. Keep the *last* complete take
  (people usually re-record because the earlier one was worse), unless an
  earlier take is clearly cleaner.
- **Mistakes**: false starts, "wait, let me start over", "uh, cut that", trailing
  off, stumbles mid-sentence. Drop a whole segment with `--drop`, or just the
  bad words with `--drop-words seg:first-last` (0-based word indexes; the
  word list is in `transcript.json`).
- **Dead space**: handled automatically, from word gaps *and* from audio
  loudness. Whisper often stretches a word over the pause after it, so word
  gaps alone miss many pauses. `cut.py` prints the pauses it found; if it's
  clipping quiet speech, raise the bar with `--silence-db` (e.g. -38).
  Silences longer than `--max-gap`
  (default 0.35s) are shortened. Use ~0.25 for punchy Reels/TikTok and ~0.5 for
  calmer YouTube pacing.

Preview the plan before encoding, then cut:

```bash
python3 <skill>/scripts/cut.py <name>-edit/transcript.json <name>-edit/cut --drop 3,4 --drop-words 9:0-2 --dry-run
python3 <skill>/scripts/cut.py <name>-edit/transcript.json <name>-edit/cut --drop 3,4 --drop-words 9:0-2
```

Outputs `cut/cut.mp4` plus `cut/cut_transcript.json`, the transcript re-timed
to the cut. **Time every overlay and caption from `cut_transcript.json`**, not
the original, or everything drifts after the first cut.

Show the user a short list of what you removed (segment text + reason) so they
can veto a cut. A wrongly removed line is the most annoying mistake an editor
can make.

## 3. Get the brief

If the user already said how they want it edited, use that. Otherwise ask one
compact question covering: platform/aspect ratio, overlay style (e.g. "animations
above me showing what I'm talking about"), captions on/off and style, brand
colors/fonts, and anything to show on screen (URLs, steps, numbers, logos). If
they have no preference, use the default style in
`references/default-style.md`, which matches the reel this skill came from.

Specific briefs give better edits. If the brief is vague, propose a concrete
beat sheet (below) and let them react to it, not to the render.

## 4. Build the composition

Write a **beat sheet** first, one row per overlay, from `cut_transcript.json`:

| start–end (s) | spoken words | on-screen visual |
|---|---|---|
| 0.0–2.9 | "Claude can fully edit videos now" | Title card "HOW TO HAVE CLAUDE EDIT VIDEOS" |

Rules of thumb that make overlays feel edited, not pasted on:
- Trigger each visual on the **word** it illustrates (word timestamps), and
  let it land 0.1–0.2s *before* the word, not after.
- One idea on screen at a time; swap visuals at sentence boundaries.
- Visualize nouns and numbers literally: a tool name gets a logo/card, a step
  gets "01 Install it", a claim like "zero edits" gets a big "0".
- Keep overlays out of the face. **Look at a frame first** (`frames.py raw1080.mp4 qa --every 4`):
  if the speaker sits in the bottom half (desk setup), use the top ~45%; if the
  face fills the top two-thirds (handheld selfie), put captions in the bottom
  band over the torso and keep graphics to small tiles in the sky/background corners.
- Show the first caption from frame 0 with no fade-in. Frame 0 is often the
  thumbnail and a blank one looks broken.
- Never show the same word twice at once. If a word gets a big emphasis
  treatment, make it replace that caption instead of stacking on top.
- Keep captions to one line (`white-space:nowrap`, ~76px at 1080 wide, 3 words max).

Then scaffold the project with the cut as the base track:

```bash
cd <name>-edit && npx hyperframes init video --video cut/cut.mp4 \
  --resolution portrait --skip-transcribe --non-interactive
```

(`--resolution landscape` or `square` to match the footage, which you can check
with `ffprobe`. `--skip-transcribe` is used because you already have a better,
re-timed transcript.) This writes `video/index.html` with `cut.mp4` as a
full-frame `<video class="clip">` on track 0 and an empty GSAP timeline
registered as `window.__timelines["main"]`. Add each overlay as a
`class="clip"` element on track 1+ with `data-start`/`data-duration` from the
beat sheet, and animate it on that timeline at the same start time. Run
`npx hyperframes lint` after every round of edits. Defer to the HyperFrames
skills for anything beyond this (sub-compositions, catalog blocks via
`npx hyperframes add`, captions).

## 5. QA: look at the frames before the final render

This is the step that separates a usable edit from a broken one. Render a
fast draft, then pull frames:

```bash
cd <name>-edit/video && npx hyperframes render -q draft -o ../draft.mp4
python3 <skill>/scripts/frames.py ../draft.mp4 ../qa --every 1 --at <overlay start/end times>
```

(A 45s vertical draft takes about 2 minutes on a laptop-class CPU. `npx hyperframes inspect`
also reports layout problems without rendering.) Sample just after each
overlay's entrance (start + ~0.4s), not at its exact start, because at the exact start
it's still at opacity 0.

Open every contact sheet and check each tile for:
- text cut off, overflowing its card, or running off-screen
- overlays covering the face or mouth
- captions out of sync with the speech, or two captions overlapping
- empty/broken images, unstyled fallback fonts, flashes of black between cuts
- the visual not matching what's being said at that moment
- clashes with text or graphics already burned into the source footage

Fix, re-render the draft, and re-check the frames you touched. Iterate until a
pass turns up nothing. Then render the final.

## 6. Render and deliver

`npx hyperframes render -q delivery -o ../final.mp4` (`-f 60` for 60fps;
see `render --help` for more). Confirm the
output's duration and resolution with `ffprobe`, then give the user the MP4
path along with a short summary: original vs. final length, what was cut, and
what overlays were added.

## 7. Make the style reusable

If the user asks for the same kind of edit again ("same as last time", "my usual
style"), offer to save their brief + beat-sheet conventions as a new skill
(or a `references/<name>-style.md` here) so future edits need only the footage.
