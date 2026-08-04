#!/usr/bin/env python3
"""
make-favicon.py  --  regenerates the IH monogram favicon in every size the site needs

WHEN TO RUN THIS
    Almost never. Only if the accent colour changes, or the heading typeface
    changes and you want the monogram to keep matching it.

HOW TO RUN IT
    pip3 install fonttools pillow
    python3 tools/make-favicon.py

WHAT IT MAKES
    favicon.ico                     root level, browsers ask for this by name
    assets/img/favicon.svg          modern browsers, scales to any size
    assets/img/apple-touch-icon.png 180px, iOS home screen
    assets/img/icon-192.png         Android home screen
    assets/img/icon-512.png         PWA install prompt and app switchers

WHY THE LETTERFORMS ARE PATHS, NOT TEXT
    An SVG that says <text font-family="Newsreader"> renders in whatever the
    viewer happens to have installed, which for a favicon is nothing. Converting
    the two glyphs to outlines makes the file self-contained, so it looks
    identical everywhere and needs no webfont to load first.

THE FONT FILE
    Downloaded from Google Fonts at build time into the scratch folder. It is
    not committed, because the outlines it produces are already baked into the
    SVG. Newsreader is licensed under the SIL Open Font License.
"""

import io
import os
import urllib.request

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Newsreader 600, the same weight the site uses for headings.
FONT_URL = ('https://fonts.gstatic.com/s/newsreader/v26/'
            'cY9qfjOCX1hbuyalUrK49dLac06G1ZGsZBtoBCzBDXXD9JVF438wpojADA.ttf')

ACCENT = '#14427E'      # --accent, the site's only strong colour
INK = '#FFFFFF'
LETTERS = 'IH'

SIZE = 512              # SVG viewBox, and the largest PNG
CORNER = 0.22           # corner radius as a fraction of the square
CAP_FRACTION = 0.40     # how tall the capitals sit relative to the square
TRACKING = 90           # extra space between I and H, in font units.
                        # Newsreader sets IH tightly. At 16px the two stems
                        # merge into a blur without this.


def font_bytes():
    """Fetch the TTF, caching it in the scratch folder between runs."""
    cache = os.path.join(ROOT, '.newsreader-cache.ttf')
    if os.path.exists(cache):
        with open(cache, 'rb') as f:
            return f.read()
    print('  downloading Newsreader 600 from Google Fonts')
    data = urllib.request.urlopen(FONT_URL, timeout=30).read()
    with open(cache, 'wb') as f:
        f.write(data)
    return data


def monogram_path(raw):
    """Return an SVG path for 'IH', scaled and centred in a SIZE square."""
    font = TTFont(io.BytesIO(raw))
    upem = font['head'].unitsPerEm
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()

    # Lay the two glyphs out on a baseline at x=0, adding tracking between them.
    parts, pen_x = [], 0
    for i, ch in enumerate(LETTERS):
        name = cmap[ord(ch)]
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        parts.append((pen.getCommands(), pen_x))
        pen_x += font['hmtx'][name][0] + (TRACKING if i < len(LETTERS) - 1 else 0)

    # Measure the ink, not the advance widths. Advances include side bearings,
    # which would push the monogram off centre.
    from fontTools.pens.boundsPen import BoundsPen
    x0 = y0 = 10 ** 9
    x1 = y1 = -10 ** 9
    offset = 0
    for i, ch in enumerate(LETTERS):
        name = cmap[ord(ch)]
        bp = BoundsPen(glyphs)
        glyphs[name].draw(bp)
        gx0, gy0, gx1, gy1 = bp.bounds
        x0, y0 = min(x0, gx0 + offset), min(y0, gy0)
        x1, y1 = max(x1, gx1 + offset), max(y1, gy1)
        offset += font['hmtx'][name][0] + (TRACKING if i < len(LETTERS) - 1 else 0)

    cap = y1 - y0
    scale = (SIZE * CAP_FRACTION) / cap
    tx = SIZE / 2 - ((x0 + x1) / 2) * scale
    ty = SIZE / 2 + ((y0 + y1) / 2) * scale   # +ve because SVG y grows downward

    # One transform wraps the lot: flip y, scale to fit, centre.
    inner = ''.join(
        f'<path transform="translate({dx} 0)" d="{cmds}"/>'
        for cmds, dx in parts
    )
    return (f'<g fill="{INK}" transform="translate({tx:.2f} {ty:.2f}) '
            f'scale({scale:.6f} {-scale:.6f})">{inner}</g>')


def write_svg(path_markup):
    r = round(SIZE * CORNER)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" '
        f'role="img" aria-label="Ibrahim Haddad">'
        f'<rect width="{SIZE}" height="{SIZE}" rx="{r}" ry="{r}" fill="{ACCENT}"/>'
        f'{path_markup}'
        f'</svg>\n'
    )
    out = os.path.join(ROOT, 'assets', 'img', 'favicon.svg')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f'  wrote assets/img/favicon.svg  ({len(svg)} bytes)')


def render_png(raw, px):
    """Raster fallback, drawn with the same font so it matches the SVG."""
    ss = 8  # supersample, then downscale. Cheaper than antialiasing by hand.
    big = px * ss
    img = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, big - 1, big - 1],
                        radius=round(big * CORNER), fill=ACCENT)

    # Binary-search a point size that lands the cap height where we want it.
    target = big * CAP_FRACTION
    lo, hi, best = 1, big * 2, None
    while lo <= hi:
        mid = (lo + hi) // 2
        f = ImageFont.truetype(io.BytesIO(raw), mid)
        h = d.textbbox((0, 0), 'H', font=f)[3] - d.textbbox((0, 0), 'H', font=f)[1]
        if h <= target:
            best, lo = (mid, f), mid + 1
        else:
            hi = mid - 1
    pt, font = best

    text = LETTERS[0] + ' ' * 0 + LETTERS[1]
    # Pillow has no tracking control, so draw the glyphs one at a time.
    gap = round(pt * (TRACKING / 2000) * 1.0)
    widths = [d.textlength(c, font=font) for c in LETTERS]
    total = sum(widths) + gap * (len(LETTERS) - 1)
    bb = d.textbbox((0, 0), LETTERS, font=font)
    x = (big - total) / 2
    y = big / 2 - (bb[1] + bb[3]) / 2
    for i, c in enumerate(LETTERS):
        d.text((x, y), c, font=font, fill=INK)
        x += widths[i] + gap

    return img.resize((px, px), Image.LANCZOS)


def main():
    raw = font_bytes()

    print('\nBuilding the IH monogram')
    write_svg(monogram_path(raw))

    targets = [
        ('assets/img/apple-touch-icon.png', 180),
        ('assets/img/icon-192.png', 192),
        ('assets/img/icon-512.png', 512),
    ]
    for rel, px in targets:
        img = render_png(raw, px)
        out = os.path.join(ROOT, rel)
        img.save(out)
        print(f'  wrote {rel}  ({px}x{px})')

    # One .ico carrying 16, 32 and 48, so old browsers and Windows both work.
    ico = render_png(raw, 256)
    ico.save(os.path.join(ROOT, 'favicon.ico'),
             sizes=[(16, 16), (32, 32), (48, 48)])
    print('  wrote favicon.ico  (16, 32, 48)')

    print('\nDone.\n')


if __name__ == '__main__':
    main()
