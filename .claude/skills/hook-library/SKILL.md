---
name: hook-library
description: Writes and rewrites scroll-stopping opening lines for short-form video (Reels, TikTok, Shorts), LinkedIn posts, carousels and captions using a library of 193 proven hook patterns — each with a build recipe and fill-in templates (e.g. "Absurd Alternative Challenge", "Age Gate Warning", "Assumption Flip", "Easy Way Out"). Use this whenever the user wants hooks, openers, a first line, "the first 3 seconds", a better intro, or pastes a draft script/post/caption and wants it to grab attention — or says their videos get swiped past, retention drops early, or views are low — even if they don't say the word "hook". Also use when they want to browse hook styles or find a hook by feel (contrast, confession, urgency, story, curiosity, etc.).
---

# Hook Library

193 short-form hook patterns, each with a description, a step-by-step build
recipe, and example openers ending in a fill-in template. The hook is the first
line the viewer hears or reads — its only job is to make them stay for the
second line.

Source: the zerotomany hook library (https://viral.nglokchun.com/hooks).

## Files

- `references/index.md` — one line per hook: name, what it does, tags. **Read
  this first** to pick candidates; it's ~200 lines.
- `references/library.md` — full entry per hook under `## <Name>`: build steps
  and example openers. Don't read the whole file — grep for the chosen hooks'
  headings (e.g. `grep -n -A 20 "^## Easy Way Out$"`) and read just those.

## Modes

Figure out which one the user wants from their message; don't ask if it's clear.

### 1. Hooks for a topic
The user has a topic, idea, or video and needs openers.

1. Get the essentials: topic, audience, platform, and what the video actually
   delivers (the payoff). Use what's in the conversation or project files; ask
   in one short message only if the topic or payoff is missing.
2. Scan `index.md` and pick **5 hooks from different families** (e.g. one
   contrast/reframe, one confession/personal, one urgency/warning, one
   curiosity/reveal, one list/challenge) so the user sees real range rather
   than five variations of one idea.
3. Pull those entries from `library.md` and follow each build recipe.
4. Write one finished opener per hook in the creator's voice.

### 2. Rewrite a draft
The user pastes an opener, script, caption or post.

1. Find the payoff of the draft — what the viewer actually gets. A hook that
   promises something the content doesn't deliver kills retention, so the
   rewrite must stay true to the draft.
2. Diagnose the current opener in one line (e.g. "starts with context, the
   interesting part is in sentence 3", "no tension", "too generic — could be
   anyone's video").
3. Pick 3 hooks that fit the content and rewrite the opening with each. Often
   the best hook is already buried mid-draft — pull it to the front.
4. If they pasted a full script, show the rewritten opener plus the first 1–2
   lines after it so the transition works; leave the rest of the script alone
   unless asked.

### 3. Browse
The user wants to explore ("show me confession hooks", "what hooks are there
for storytelling?"). Search `index.md` by tag and description words, list the
matches as name + one-line description, and offer to write examples for any
they like.

## Writing rules

- **Spoken, not written.** It should sound natural said out loud in under ~3
  seconds (roughly 8–20 words). Read it in your head; if you'd stumble, cut.
- **Specific beats clever.** Concrete numbers, ages, objects, and situations
  ("I'm 34 and just quit my $140k job") beat abstractions ("Let's talk about
  career change").
- **Don't copy the examples.** The library's example openers show the shape —
  rewrite them for the user's niche. Use the `(insert …)` template as the
  skeleton.
- **Never fabricate facts about the creator.** If a hook needs a real number,
  age, result, or credential you don't have, use `[FILL IN: …]`.
- **Make sure the content delivers.** If a hook implies a payoff the video
  doesn't have, say so or pick a different hook.

## Output format

For each hook:

```
### <Hook name>
**Opener:** "<exact spoken line>"
**Why it fits:** <one sentence — the tension or curiosity it creates for this audience>
```

For rewrites, put the one-line diagnosis of the original first, then the 3
options in the format above.

End with your pick: which opener you'd film first and why. For written posts,
also offer an **on-screen text** version (≤8 words) of your pick, since many
viewers watch muted.

## Pairs well with

- `proven-post-frameworks` — the post idea; this skill sharpens its first line.
- `pattern-awareness-content` / `small-story-bigger-picture` — full scripts;
  use this skill to test alternate openers for them.
