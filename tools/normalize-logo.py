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
    Trims to the ink, then centres it on a 500x250 white canvas inside a box of
    88% width by 60% height, preserving aspect ratio. Wide wordmarks are bound
    by the width limit, squarer marks by the height limit, and everything lands
    in the same optical range.

    Transparency is flattened onto white, because the rows sit on white and a
    transparent PNG would otherwise darken unpredictably under the greyscale
    filter.
"""

import os
import sys

from PIL import Image

CANVAS_W, CANVAS_H = 500, 250     # every logo in the repo uses this
MAX_INK_W = 0.88                  # binds on wide wordmarks
MAX_INK_H = 0.78                  # binds on squarer marks with a symbol
WHITE_CUTOFF = 230                # anything lighter counts as background

# Why a bounding box and not equal ink area:
#   Normalising every logo to the same area of dark pixels sounds more correct
#   and looks worse. Ink area confuses size with stroke weight, so a bold
#   wordmark like Fenwick (13.7% ink) gets shrunk while a hairline one like
#   Debricked (6.6% ink) gets inflated, even though both currently sit
#   correctly in the row. Fitting the bounding box keeps apparent size tied to
#   apparent size.
#
# Why two caps rather than one:
#   A single width cap makes tall square marks enormous, and a single height cap
#   makes wide wordmarks vanish. Whichever binds first wins, so a 6:1 wordmark
#   is limited by width and a 1:1 roundel by height.


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

    # Fit inside the box, preserving aspect. Whichever limit binds first wins.
    scale = min(CANVAS_W * MAX_INK_W / ink.width,
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

    bound = 'width' if scale == CANVAS_W * MAX_INK_W / (box[2] - box[0]) else 'height'
    print(f'  {os.path.basename(out_path)}')
    print(f'    source {im.size}  ->  canvas {CANVAS_W}x{CANVAS_H}')
    print(f'    ink {tw}x{th}  =  {100*tw/CANVAS_W:.1f}% wide, '
          f'{100*th/CANVAS_H:.1f}% tall   ({bound} limit binds)')
    print(f'    renders {30*tw/CANVAS_W:.0f}x{30*th/CANVAS_H:.0f}px '
          f'inside the 60x30 slot')


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__.strip().split('HOW TO RUN IT')[1].split('WHAT IT DOES')[0])
    normalize(sys.argv[1], sys.argv[2])
    print()


if __name__ == '__main__':
    main()
