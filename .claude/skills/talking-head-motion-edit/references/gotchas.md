# Gotchas

Every row here cost real time to discover once. Read this before your first render so you
don't rediscover them one by one.

| Symptom | Fix |
|---|---|
| Video renders as a frozen frame | Every video/audio element needs a unique `id`. No exceptions. |
| A frozen frame appears when the video moves or seeks | Sparse keyframes. Re-encode every media file with a keyframe every second (`-g 30 -keyint_min 30`). |
| An element is black/invisible the first time it should appear | A later animation stamped it hidden at page load. Set `immediateRender: false` on any `fromTo` tween whose element needs to be visible before that tween runs. |
| Two captions are mashed together on screen | A caption held past the next chunk's start time. Always end a caption at the *next* chunk's start minus ~0.04s, never at your own computed end. |
| Sound effects are inaudible in the final mix | About a third of generated SFX come back near-silent. Volume-audit every generated file, regenerate the duds, normalize the kit. |
| The music API returns a 400 error | An artist name is in the prompt. Describe the style/texture instead — the error body usually suggests a rewrite. |
| A keychain dialog or stray window is baked into B-roll | Use system Chrome with a fresh profile for capture, and frame-extract-and-look at every take before trusting it. |
| B-roll scrolling never actually moved | The scroll target grabbed an ancestor `div` whose `top` is already 0. Target the smallest DOM node that actually contains the text. |
| The rendered file has the wrong duration | A stale duration value survived an earlier edit to the composition. Verify with `ffprobe` on the actual output file — never trust a render log. |
| Emoji or icons render as empty boxes | Headless Chrome lacks Apple's private-use emoji glyphs. Use standard Unicode emoji or plain text labels instead of icon-font glyphs that depend on them. |

## The working style behind all of it

Verify visually at every stage rather than reasoning about whether code "should" work.
Generate the repetitive, mechanical 90% (captions, SFX markup) straight from the transcript
instead of hand-authoring it. Prefer real assets (screenshots, brand files) over recreations
wherever you have them. Ask your few preference questions once, up front, then run
autonomously to a reviewable draft — people are much better at reacting to a draft than
answering a long spec interview.
