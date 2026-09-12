---
name: talking-head-motion-edit
description: Turn a raw talking-head video into a polished, word-synced motion-graphics edit — a split-screen (or full-bleed) cut with a designed graphic for every spoken line, karaoke-style captions, sound effects, a music bed, and optional A/B hook variants, all driven off the video's own transcript. Use this whenever someone hands over a raw talking-head/UGC clip (a URL or local file) and wants it turned into something that looks like a produced ad, reel, or brand-partnership video — phrases like "edit this into a real ad," "add motion graphics for every line," "make this look produced," or "I recorded a talking head, can you polish it." Also trigger on mentions of HyperFrames, GSAP video compositions, karaoke/word-synced captions, ElevenLabs sound design for video, or "the Claude Edit playbook." This is a personal/creator workflow, not scoped to any one client — brand colors, B-roll, and reference-ad folders are optional extras, never a requirement to start.
---

# Talking-Head Motion Edit

Turn one raw talking-head take into a fully produced vertical (or split-screen) edit: a
designed motion-graphic card synced to every sentence, karaoke captions, sound design, and
a music bed — built by reading the video's own transcript rather than by hand-timing anything.

## Why this shape

The video's transcript is the spine of the whole edit. Once you have word-level timestamps,
almost everything else — caption timing, where a graphic card enters, where a sound effect
lands — can be *generated* from those timestamps instead of eyeballed. The only genuinely
manual, taste-driven step is deciding, for each sentence, what the card should look like.
Everything else is mechanical enough to script, and should be, because a real script (a
10-15 sentence video) means 80-300 individually-timed elements — nobody hand-times that
without drift.

So the working rhythm is: **generate the repetitive 90%, hand-design the 10% where taste
lives, and verify by looking at pixels and measuring audio — never by re-reading code.**

## Inputs

**Required:**
- The raw video (a URL or local file path). Ideally 4K 16:9 talking-head footage, but work
  with whatever you're given.

**Optional — ask about these only if the user hasn't already said, don't assume they're needed:**
- A brand/product URL to pull colors and a logo from (see `references/brand-and-broll.md`),
  when the video promotes something with a live site.
- A local folder of brand assets (logo files, product shots, screen recordings — e.g. from
  Screen Studio) to use directly instead of scraping a site.
- A local folder of reference/competitor ads to emulate stylistically — treat this as "study
  these for recurring visual patterns," not "copy pixels."
- If none of the above apply, that's completely fine: just do the talking-head + per-line
  motion graphics with no B-roll or external brand tokens. Most of this skill's value (the
  captions, the cards, the sound design) doesn't depend on having a brand to scrape at all.

## Operating style

Ask about only three things up front, once, then run to a reviewable draft without further
check-ins:
1. **Canvas ratio** — vertical 9:16, or does a wider/square format make sense here?
2. **Layout mix** — mostly split-screen (video in a band, graphic on top) with occasional
   full-screen takeovers, or a different balance? (See the four framing modes below.)
3. **Hook variants** — did they record multiple opening lines/hooks they want cut into
   separate A/B versions?

Everything else — which sentences get which card archetype, caption styling, sound design,
exact timing — is your call to make and then show, not to ask about piecemeal. People are
much better at reacting to a draft than answering a spec interview.

## The pipeline

### 1. Probe the source and cut display crops

```bash
ffprobe -v error -show_entries format=duration -show_entries \
  stream=codec_name,width,height,r_frame_rate source.mp4
```
Record duration, resolution, and fps — the duration becomes the composition length.

From one source file, cut two framings you'll switch between in the edit: a wide "band" crop
(lives at the bottom of split layouts) and a tight full-bleed vertical crop (for dramatic
full-screen beats). **Actually extract a frame and look at it to center the crop on the
speaker's face — never trust crop math alone**, framing varies take to take.

Both crops (and the source) need to be **re-encoded with a keyframe every second**
(`-g 30 -keyint_min 30`) — sparse keyframes freeze on seek inside the HTML/GSAP renderer used
later. This is the single most common source of "the video won't play right" bugs in this
workflow; do it up front on every media file, not just the final output.

```bash
ffmpeg -i source.mp4 -vf "crop=W:H:X:0,scale=1080:840" \
  -crf 18 -g 30 -keyint_min 30 -pix_fmt yuv420p input-video.mp4      # band crop
ffmpeg -i source.mp4 -vf "crop=W:H:X:0,scale=1080:1920" \
  -crf 19 -g 30 -keyint_min 30 -an input-video-vert.mp4              # full-bleed crop
```

### 2. Transcribe with word-level timestamps

```bash
ffmpeg -i source.mp4 -vn -ac 1 -ar 16000 audio.mp3
npx hyperframes transcribe audio.mp3 --json --model small.en
```

The transcript is the backbone — every card entrance, caption chunk, and sound-effect hit
will be derived from these timestamps, so get it right before moving on:
- Fix transcription errors **in place**, in the JSON, keeping the original timestamps (brand
  names and jargon get mangled most often).
- Clamp the last word's end time to the file's actual duration — the model's final timestamp
  commonly overruns.

### 3. Storyboard one card per sentence

Read `references/card-archetypes.md` for the four framing modes (split / solo / fullhim /
full) and the table mapping common script beats (a number, "before vs. after," an emotional
one-liner, social proof, a guarantee, a CTA) to proven card designs. For every sentence in
the transcript, pick a framing mode and an archetype, and write it down as a storyboard —
sentence, timestamps, framing, archetype — before building anything. This is where your
design judgment actually matters; the storyboard keeps you honest about having made a
decision for every line instead of drifting into "whatever's easiest to build."

If a brand or reference-ad folder was provided, this is where it feeds in: real brand colors
inform the card palette, real product screenshots beat recreated ones, and patterns from
reference ads inform which archetypes to lean on — see
`references/brand-and-broll.md` for how to pull a palette/logo from a live site and how to
record clean B-roll of a website if that's part of the brief.

### 4. Build the composition

The composition is one HTML file: the video layers, the hand-designed cards, and a single
**paused** GSAP timeline that the renderer scrubs frame by frame. Hand-author the cards
where taste lives; generate the repetitive captions and SFX markup from the transcript with
`scripts/caption_chunks.py` (see below) rather than hand-timing them.

Six rules that avoid the large majority of rendering bugs — read `references/gotchas.md` for
the full table of symptom → fix, but the rules themselves:
1. **One paused timeline, fully deterministic.** No `setTimeout`, no randomness, no infinite
   repeats — the renderer scrubs to specific times and expects the same frame every time.
2. **Animate transforms only** — `y`, `scale`, `opacity`. Never `top`/`left`/`width`/`height`;
   those aren't reliably scrubbable.
3. **Every video and audio element needs a unique `id`.** Without one it renders as a frozen
   frame instead of playing.
4. **Initial hidden states belong in CSS**, not in a timeline `.set()` at time 0 — a `.set()`
   at time 0 doesn't necessarily paint before the first frame is captured.
5. Optional but effective: a thin progress bar across the top, zoom punches on key words, a
   vignette under full-bleed captions — small retention cues that cost little to add.
6. **All assets are local files** — fonts, the GSAP library itself, images, B-roll, audio.
   The renderer blocks network fetches; anything pulled from a CDN breaks the render.

**Generate the captions, don't hand-write them.** Run:

```bash
python3 scripts/caption_chunks.py transcript.json --out captions.json
```

This implements the karaoke-caption algorithm: group words into 1-3 word chunks (breaking on
a >0.45s gap or punctuation), show each chunk from `start - 0.04s` to the *next* chunk's
`start - 0.04s` (always cut at the next chunk's start, never at your own end time, or
captions overlap and mash together on screen), and round every timestamp to the frame grid
before use. Feed the resulting JSON into your build step to emit the caption markup and
GSAP tweens — for a normal script this is 60-300+ tweens, which is exactly the kind of volume
that drifts out of sync if written by hand.

### 5. Sound design

Read `references/sound-design.md` for the full recipe: generate a small (~12-sound) SFX kit
once via the ElevenLabs sound-generation API, reuse it across every hit in the edit (a whoosh
as a card enters, ticks under a count-up, a sharper hit on a money/emphasis line), then
generate one cinematic instrumental bed sized to the video's duration. It also has the
mix-level starting points (bed well under the voice, hits varying by type) and the two
sharpest gotchas: roughly a third of generated SFX come back near-silent (audit and
regenerate, don't assume a successful API call means an audible file), and the music API
rejects prompts that name artists (describe the texture instead).

Needs `ELEVENLABS_API_KEY` in a local `.env` — never commit it.

### 6. QA, render, verify

Every real bug in this workflow gets caught by looking at frames or measuring audio, not by
re-reading the composition code:

```bash
npx hyperframes check public                                   # lint + layout + contrast — fix every error
npx hyperframes snapshot public --at 2.7,12.2,27.8,45.9,68.5    # a handful of stills across the timeline
# actually look at the stills, fix what you SEE, repeat until they're clean, then:
npx hyperframes render public -o output.mp4 --fps 30
ffprobe output.mp4                                              # verify duration/resolution/audio on the FILE, never trust the render log
```

A 30-second contact sheet of snapshots catches far more than sitting through three full
renders would, and it's much cheaper — always snapshot before you render.

### 7. Optional: hook A/B variants

If the raw take stacks two (or more) opening hook lines back to back on purpose, you can cut
each version programmatically instead of re-editing from scratch: pick cut ranges at sentence
boundaries, remap every timestamp in the transcript/captions/SFX data by the same offset for
each version, pre-cut the underlying media, and hide the splice point inside a framing
change (a cut to full-bleed reads as a deliberate edit, not a stitch). One recorded master
becomes several test-ready variants this way.

## Reference files

- `references/card-archetypes.md` — the four framing modes and the beat → card-design table
- `references/brand-and-broll.md` — optional palette/logo scraping and clean website B-roll
  capture, for when a brand or product is actually part of the video
- `references/sound-design.md` — the SFX kit, the music bed prompt, and mix levels
- `references/gotchas.md` — symptom → fix table for every render bug this workflow tends to
  hit; skim it before your first render, it will save real time
- `references/tool-stack.md` — what each tool in the stack does and where to get it

## Bundled script

- `scripts/caption_chunks.py` — implements the karaoke caption-chunking algorithm described
  above. Input: a HyperFrames/Whisper `--json` transcript with word-level timestamps. Output:
  a JSON list of caption chunks (`text`, `start`, `end`) ready to drive your caption markup
  and GSAP tweens.
