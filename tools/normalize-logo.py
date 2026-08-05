#!/usr/bin/env python3
"""
normalize-logo.py  --  fit a supplied logo to the house canvas

WHY THIS EXISTS
    The logo rows set `img { height: 30px; width: auto }`, so a logo's rendered
    size is decided entirely by the file it arrives in, not by the mark itself.
    Two things go wrong when a file is dropped in as supplied:

    A logo on a tall canvas renders tiny. The Fenwick file was 500x375 with the
    wordmark filling 17% of it, which came out about 5px tall, a smudge.

    A logo on a wide canvas renders oversized. Visar Systems was 1024x333, a
    3.08 ratio against everyone else's 2.0, so it sat 92px wide in a row of
    60px logos and pulled the eye.

    Both are the same bug: the canvas is doing the sizing, and nobody looks at
    the canvas. This normalises it away.

HOW TO RUN IT
    pip3 install pillow
    python3 tools/normalize-logo.py SOURCE OUTPUT

    e.g. python3 tools/normalize-logo.py ~/Downloads/acme.png \\
                 assets/img/collaborators/acme.jpg

    Run it on every new logo before committing. Check the reported ink height
    against the table it prints; if the new logo is wildly outside the range of
    its neighbours, the source art is probably cropped oddly.

WHAT IT DOES
    Trims to the ink, then centres it on a 500x250 white canvas, scaled so the
    mark's bounding box covers the same AREA as every other logo in the repo.
    Aspect ratio is preserved, so a wide wordmark ends up long and short and a
    roundel ends up narrow and tall, but the two take up the same amount of the
    row. Equal area is what stops any one logo reading as dominant.

    Transparency is flattened onto white, because the rows sit on white and a
    transparent PNG would otherwise darken unpredictably under the greyscale
    filter.
"""

import os
import sys

from PIL import Image

CANVAS_W, CANVAS_H = 500, 250     # every logo in the repo uses this
WHITE_CUTOFF = 230                # anything lighter counts as background

# Each logo is scaled so its bounding box covers the same AREA of the canvas.
# Aspect ratio is preserved, so a wide wordmark comes out long and short while a
# roundel comes out narrow and tall, and the two occupy the same amount of the
# row. This is the number that decides whether a logo looks dominant.
TARGET_INK_AREA = 0.238           # fraction of the 500x250 canvas

# Guards only. At the target above nothing in this repo reaches either, so every
# logo lands on exactly equal area. They exist so a freak aspect ratio cannot
# push ink off the canvas.
MAX_INK_W = 0.90
MAX_INK_H = 0.82

# Why area and not "fit inside a box":
#   The first version of this script capped width at 88% and height at 78% and
#   let whichever bind first. That silently produced a 2.9x spread in rendered
#   area, because a 6:1 wordmark is limited by width and a 1:1 roundel by
#   height, and those two limits describe very different amounts of ink. Jina AI
#   came out at 1178 square pixels against Tidelift's 412. Equal area fixes it.
#
# Which area, precisely:
#   The BOUNDING BOX, not the count of dark pixels. Those are different metrics
#   and only one of them works. Counting dark pixels confuses size with stroke
#   weight, so a bold wordmark like Fenwick (13.7% of its canvas inked) would be
#   shrunk while a hairline one like Debricked (6.6%) would be inflated, even
#   though both already sat correctly in the row. The bounding box measures how
#   much room a mark takes up, which is what the eye is judging.
#
# Note the canvas scales uniformly into the row: 500x250 becomes 60x30, x0.12 on
# both axes. So equal area on the canvas is equal area on screen, and this can be
# reasoned about entirely in canvas pixels.


def ink_box(rgb):
    """Bounding box of everything that is not near-white."""
    mask = rgb.convert('L').point(lambda v: 255 if v < WHITE_CUTOFF else 0)
    return mask.getbbox()


def normalize(src_path, out_path):
    im = Image.open(src_path)
    # Flatten any alpha onto white first, so transparent corners do not read as
    # ink and blow the bounding box out to the full canvas.
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        im = Image.alpha_composite(Image.new('RGBA', im.size, (255, 255, 255, 255)), im)
    rgb = im.convert('RGB')

    box = ink_box(rgb)
    if not box:
        sys.exit(f'ERROR: {src_path} looks blank. Nothing darker than {WHITE_CUTOFF}.')
    ink = rgb.crop(box)

    # Scale to hit the target bounding-box area, preserving aspect ratio.
    # area = (w*s)*(h*s) = w*h*s^2, so s = sqrt(target / (w*h)).
    target = TARGET_INK_AREA * CANVAS_W * CANVAS_H
    scale = (target / (ink.width * ink.height)) ** 0.5

    # Then pull back if that would overflow either guard.
    scale = min(scale,
                CANVAS_W * MAX_INK_W / ink.width,
                CANVAS_H * MAX_INK_H / ink.height)

    tw, th = max(1, round(ink.width * scale)), max(1, round(ink.height * scale))
    ink = ink.resize((tw, th), Image.LANCZOS)

    canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), (255, 255, 255))
    canvas.paste(ink, ((CANVAS_W - tw) // 2, (CANVAS_H - th) // 2))

    ext = os.path.splitext(out_path)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        canvas.save(out_path, quality=92, optimize=True)
    else:
        canvas.save(out_path, optimize=True)

    area = 100 * tw * th / (CANVAS_W * CANVAS_H)
    capped = ('  CAPPED by width guard' if tw >= CANVAS_W * MAX_INK_W - 1 else
              '  CAPPED by height guard' if th >= CANVAS_H * MAX_INK_H - 1 else '')
    print(f'  {os.path.basename(out_path)}')
    print(f'    source {im.size}  ->  canvas {CANVAS_W}x{CANVAS_H}')
    print(f'    ink {tw}x{th}   aspect {tw/th:.2f}   area {area:.1f}% of canvas{capped}')
    print(f'    renders {60*tw/CANVAS_W:.1f}x{30*th/CANVAS_H:.1f}px in the 60x30 slot')


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__.strip().split('HOW TO RUN IT')[1].split('WHAT IT DOES')[0])
    normalize(sys.argv[1], sys.argv[2])
    print()


if __name__ == '__main__':
    main()
