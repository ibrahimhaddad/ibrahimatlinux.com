#!/usr/bin/env python3
"""
make-og-card.py  --  builds the social share image

WHY THIS EXISTS
    Every link to this site posted on LinkedIn renders a preview card, and
    LinkedIn is where Ibrahim publishes. The card was the square portrait, which
    LinkedIn crops into a landscape slot, so the result was a face with the top
    and bottom sliced off and no words at all.

    This makes a purpose-built 1200x630 card: the claim, the name, the portrait.
    Someone scrolling past now reads the positioning even if they never click.

HOW TO RUN IT
    pip3 install pillow
    python3 tools/make-og-card.py

    Then hard-refresh the card in LinkedIn's Post Inspector, because LinkedIn
    caches previews aggressively and will keep serving the old one otherwise:
    https://www.linkedin.com/post-inspector/

WHAT IT MAKES
    assets/img/og-card.png     1200x630, referenced by og:image on every page

WHY 1200x630
    LinkedIn, X, Facebook and Slack all converge on roughly 1.91:1. At this size
    nothing gets cropped on any of them.
"""

import io
import os
import urllib.request

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

W, H = 1200, 630
BG = '#0F2544'          # --surface-deep
INK = '#FFFFFF'
MUTED = '#8FA6C4'       # the footer's muted blue
RULE = '#26456F'

CLAIM = 'I have run both sides of open source.'
NAME = 'IBRAHIM HADDAD, PhD'
DOMAIN = 'ibrahimatlinux.com'

FONTS = {
    # Newsreader 500, the display face
    'display': ('https://fonts.gstatic.com/s/newsreader/v26/'
                'cY9qfjOCX1hbuyalUrK49dLac06G1ZGsZBtoBCzBDXXD9JVF438wpojADA.ttf'),
    # Inter 600, the UI face
    'ui': ('https://fonts.gstatic.com/s/inter/v20/'
           'UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuGKYMZg.ttf'),
}


def font_bytes(key):
    cache = os.path.join(ROOT, f'.font-cache-{key}.ttf')
    if os.path.exists(cache):
        with open(cache, 'rb') as f:
            return f.read()
    print(f'  downloading {key} font')
    data = urllib.request.urlopen(FONTS[key], timeout=30).read()
    with open(cache, 'wb') as f:
        f.write(data)
    return data


def wrap(draw, text, font, max_width):
    """Greedy wrap. The claim is short and fixed, so nothing cleverer is needed."""
    words, lines, line = text.split(), [], []
    for word in words:
        trial = ' '.join(line + [word])
        if draw.textlength(trial, font=font) <= max_width or not line:
            line.append(word)
        else:
            lines.append(' '.join(line))
            line = [word]
    if line:
        lines.append(' '.join(line))
    return lines


def portrait_panel(width, height):
    """Right-hand portrait, cropped to the panel and faded into the background.

    The source is square and the panel is tall, so a straight resize would
    squash him. Crop to the panel's aspect ratio first, biased upward to keep
    the face off the bottom edge.
    """
    src = Image.open(os.path.join(ROOT, 'assets', 'img', 'ibrahim-haddad.jpg')).convert('RGB')
    target = width / height
    sw, sh = src.size
    if sw / sh > target:
        new_w = int(sh * target)
        left = (sw - new_w) // 2
        src = src.crop((left, 0, left + new_w, sh))
    else:
        new_h = int(sw / target)
        top = int((sh - new_h) * 0.18)   # bias up, faces sit high
        src = src.crop((0, top, sw, top + new_h))
    panel = src.resize((width, height), Image.LANCZOS)

    # Fade the left edge into the background so the photo does not sit on the
    # card as a hard rectangle.
    fade = Image.new('L', (width, height), 255)
    fd = ImageDraw.Draw(fade)
    ramp = int(width * 0.38)
    for x in range(ramp):
        fd.line([(x, 0), (x, height)], fill=int(255 * (x / ramp) ** 1.4))
    panel.putalpha(fade)
    return panel


def main():
    disp_raw, ui_raw = font_bytes('display'), font_bytes('ui')

    card = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(card)

    pw = int(W * 0.42)
    card.paste(portrait_panel(pw, H), (W - pw, 0), portrait_panel(pw, H))

    pad = 68
    text_w = W - pw - pad - 40

    # Eyebrow
    ui = ImageFont.truetype(io.BytesIO(ui_raw), 21)
    x = pad
    for ch in NAME:                      # manual tracking, Pillow has none
        d.text((x, 84), ch, font=ui, fill=MUTED)
        x += d.textlength(ch, font=ui) + 2.4

    # The claim, set as large as it can go while still fitting four lines
    size, lines, disp = 74, [], None
    while size > 30:
        disp = ImageFont.truetype(io.BytesIO(disp_raw), size)
        lines = wrap(d, CLAIM, disp, text_w)
        if len(lines) <= 4 and max(d.textlength(l, font=disp) for l in lines) <= text_w:
            break
        size -= 2

    y = 152
    for line in lines:
        d.text((pad, y), line, font=disp, fill=INK)
        y += int(size * 1.16)

    # Rule and domain
    y += 26
    d.line([(pad, y), (pad + 96, y)], fill=RULE, width=3)
    small = ImageFont.truetype(io.BytesIO(ui_raw), 22)
    d.text((pad, y + 26), DOMAIN, font=small, fill=MUTED)

    out = os.path.join(ROOT, 'assets', 'img', 'og-card.png')
    card.save(out, optimize=True)
    print(f'  wrote assets/img/og-card.png  ({W}x{H}, {os.path.getsize(out)//1024} KB)')
    print('\nDone. Re-scrape it at https://www.linkedin.com/post-inspector/\n')


if __name__ == '__main__':
    main()
