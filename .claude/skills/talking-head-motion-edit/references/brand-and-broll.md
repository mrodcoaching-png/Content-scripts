# Optional: brand tokens and website B-roll

Skip this file entirely if the video isn't promoting a specific product/site, or if the user
already handed you local assets to use directly — it only applies when you're pulling brand
material live from the web.

## Pulling a palette and logo from a live site

Fifteen minutes of scraping beats guessing at colors. Mine the site before designing a single
card, and turn what you find into a small CSS token block that every card, caption highlight,
and chip inherits from — point the same edit at a different brand later and the whole visual
system re-skins by changing five lines.

```bash
curl -sL -A "Mozilla/5.0" https://brand.com -o site.html
grep -oE "#[0-9a-fA-F]{6}\b" site.html | sort | uniq -c | sort -rn | head -20
grep -oE '(src|href)="[^"]*(logo|icon)[^"]*"' site.html | sort -u
# also repeat the color histogram on any linked .css files — they're often richer than the HTML
```

```css
:root {
  --brand-accent: #___;   /* their primary color */
  --bg-dark: #___;        /* their background */
  --panel: #___;          /* card surface */
  --muted: #___;          /* secondary text */
  --green: #___;          /* wins / positive numbers */
  --red: #___;            /* costs / negative numbers */
  --gold: #___;           /* ratings */
}
```

Prefer real screenshots over recreated mockups wherever the storyboard calls for showing the
product — a genuine dashboard screenshot inside a white card reads as proof, a recreation
reads as an ad. If the user gave you an asset folder, check it for product shots and a logo
before falling back to scraping.

## Recording clean website B-roll

If the storyboard calls for showing the product/site in motion, capture 4-6 short clips
(3-6 seconds each) of it scrolling smoothly — clean, with no cookie banners, chat widgets,
stray windows, or dialogs baked in.

```js
await puppeteer.launch({
  headless: false,
  executablePath: /* the system Chrome path */,
  userDataDir: /* a fresh temp profile */,
  ignoreDefaultArgs: ["--enable-automation"], // kills the "Chrome is being controlled" infobar
  args: ["--kiosk", "--hide-scrollbars", "--use-mock-keychain"],
});
// hide junk before recording, and re-sweep on an interval in case it reappears:
// display:none on [id*="cookie"], [class*="chat"], [class*="intercom"]
```

Scroll with an eased loop (~1.4s per move, holding 3-4s per section) and log timestamps as
you go, so the master recording can be cut into named clips afterward:

```bash
ffmpeg -ss START -to END -i master.mp4 -crf 17 -g 30 broll/hero.mp4
```

A shot list that covers most scripts: hero section, features, pricing/calculator,
how-it-works, reviews, CTA. Record one smooth pass through all of them, then cut clips out of
that single master rather than recording each separately.

**Watch for the scrolling trap:** if you're scrolling to a text anchor, target the *smallest*
DOM node that contains the text you're looking for — an ancestor `div` can also "contain" it
while sitting at `top: 0`, which means the page silently never actually scrolls. Always
extract a frame from the capture afterward and look at it; this is the only reliable way to
catch a scroll that didn't move, a keychain dialog, or a personal window that leaked into the
recording.

In the composition, frame B-roll like a browser — inside a dark rounded card with
traffic-light dots and a URL pill — it reads as instantly more credible than a bare video
crop.
