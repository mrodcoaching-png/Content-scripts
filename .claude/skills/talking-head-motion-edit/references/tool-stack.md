# Tool stack

| Tool | What it does here | Where to get it |
|---|---|---|
| HyperFrames | Renders video from an HTML file: one paused GSAP timeline, scrubbed to deterministic frames. Also does transcription, linting, snapshotting, and rendering. | `npx hyperframes` (no install/key needed) |
| ffmpeg / ffprobe | Probing source files, cutting crops, extracting audio, cutting B-roll clips, and verifying every rendered output. | `brew install ffmpeg` (or your platform's package manager) |
| ElevenLabs | Generates the SFX kit and the music bed via API. | `elevenlabs.io` — needs an API key |
| Puppeteer | Scripted, clean screen recording of a website for B-roll, only needed if a brand/site is part of the video. | `npm i puppeteer` |
| GSAP | The animation runtime inside the HTML composition. | Bundle it as a local file — never load it from a CDN, the renderer blocks network fetches |

## `.env`

The only credential this workflow needs:

```
ELEVENLABS_API_KEY='your-key-here'
```

Never commit this file.

## Why everything ships as local files

The renderer blocks network fetches during render, so fonts, the GSAP library, images,
B-roll, and audio all need to live inside the project folder as local files. Anything that
tries to pull from a CDN at render time will simply break the render — this isn't a
performance preference, it's a hard requirement.
