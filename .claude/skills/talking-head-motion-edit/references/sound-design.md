# Sound design

Sound is roughly half of what makes this kind of edit feel produced rather than like slides
over a video, and it's cheap to get right: build a small kit once via the ElevenLabs API,
reuse it across every hit in the edit.

## The SFX kit (~12 sounds, generated once)

```bash
curl -X POST https://api.elevenlabs.io/v1/sound-generation \
  -H "xi-api-key: $ELEVENLABS_API_KEY" -H "Content-Type: application/json" \
  -d '{"text": "deep punchy bass impact", "duration_seconds": 0.7, "prompt_influence": 0.35}'
```
`duration_seconds` has a floor of 0.5s. A kit that covers most edits: whoosh, whip, UI pop,
stamp slam, cash-register ticks, bass impact, fire ignite, pen scratch, cha-ching, shimmer,
ding.

**Audit every generated file before using it.** Roughly a third of generations come back
near-silent even on a successful API call — measure peak volume on each file, regenerate the
duds with an explicitly "loud, punchy" prompt, and normalize the whole kit to a consistent
level (around -3dB) once it's clean.

Land each hit on the exact word it belongs to, not the start of the sentence — a "fire"
whoosh goes on the word "fire," a card-entrance whoosh goes on the word that triggers the
card, and so on.

## The music bed (generated once per video)

```bash
curl -X POST https://api.elevenlabs.io/v1/music \
  -H "xi-api-key: $ELEVENLABS_API_KEY" -H "Content-Type: application/json" \
  -d '{"music_length_ms": DURATION_MS_PLUS_2000,
       "prompt": "suspenseful cinematic instrumental, dark pulsing low strings, sub-bass hits, ticking percussion, designed to sit under a voiceover, no vocals"}'
```
Describe the *texture* you want, not an artist or track — the API rejects prompts that name
artists, and the error response usually suggests a rewrite if that happens. Size the request
a couple seconds past the video's actual duration so you're never short.

## Mix levels

Starting points that sat right against a voiceover peaking around -7dB — treat these as a
first pass, then trust your ears over the numbers:

| Element | Level |
|---|---|
| UI pops | 0.32 |
| Whooshes | 0.30 |
| Stamps / impacts | 0.50 |
| Count-up ticks | 0.40–0.45 |
| Cha-ching | 0.40 |
| Music bed | 0.10 |

Keep the bed 18-20dB under the voice throughout — audible in the gaps between words,
essentially invisible once someone's talking.

**Verify SFX actually made it into the final mix**, don't just trust that adding an audio
element to the composition means it's audible: render (or spot-check) a version without SFX
and compare loudness around each hit's timestamp against the version with SFX. A hit is real
only if the peak measurably rises — a silent generation, a muted track, or a hit placed
outside the visible timeline can all *look* correct in the composition and still not be
audible in the output.
