"""
Build lang/fonts.json for the Thai pack.

Each Pebble font slot gets a Thai weight chosen to match the stroke width of
the stock Latin bitmap font in that same slot (measured from the Renaissance
.pbff files: 1px stems at Gothic 14/18/24 regular, 2px at their bold and at
Gothic 28 regular, 3px at Gothic 28 bold).

Heights are then set so the Thai cap height matches the sizes already
approved on-device, stepping down if the mark stack would otherwise reach
into the descenders of the line above.
"""

import json
import sys

import freetype

sys.path.insert(0, '.')
from utils.fontgen import FT_MONO_FLAGS, Font, FontType, THAI_LEVEL1, THAI_LEVEL2

# slot: (line box, target Thai cap height, weight file)
SLOTS = {
    # Gothic system fonts -- weight matched to the Latin stem width.
    "001": (14, 6, "NotoSansThaiCond-Light.ttf"),
    "002": (14, 6, "NotoSansThaiCond-Regular.ttf"),
    "003": (18, 8, "NotoSansThaiCond-Light.ttf"),
    "004": (18, 8, "NotoSansThaiCond-Regular.ttf"),
    "005": (24, 11, "NotoSansThaiCond-Light.ttf"),
    "006": (24, 11, "NotoSansThaiCond-Regular.ttf"),
    "007": (28, 12, "NotoSansThaiCond-Medium.ttf"),
    "008": (28, 12, "NotoSansThaiCond-SemiBold.ttf"),
    "009": (36, 15, "NotoSansThaiCond-Medium.ttf"),
    "010": (36, 15, "NotoSansThaiCond-SemiBold.ttf"),
    # Display fonts -- weight follows the name of the Latin face they replace.
    "011": (18, 8, "NotoSansThaiCond-Light.ttf"),
    "012": (30, 13, "NotoSansThaiCond-Bold.ttf"),
    "013": (34, 14, "NotoSansThaiCond-Light.ttf"),
    "014": (34, 14, "NotoSansThaiCond-Medium.ttf"),
    "015": (42, 18, "NotoSansThaiCond-Bold.ttf"),
    "016": (42, 18, "NotoSansThaiCond-Light.ttf"),
    "017": (42, 18, "NotoSansThaiCond-Medium.ttf"),
    "018": (21, 8, "NotoSansThaiCond-Regular.ttf"),
    "019": (49, 22, "NotoSansThaiCond-Bold.ttf"),
    "020": (28, 12, "NotoSansThaiCond-Bold.ttf"),
}


def cap_height(path, size):
    face = freetype.Face('ttf/' + path)
    face.set_pixel_sizes(0, size)
    face.load_glyph(face.get_char_index(ord('ก')), FT_MONO_FLAGS)
    return face.glyph.bitmap.rows


def size_for_cap(path, target, lo=7, hi=48):
    best = lo
    for size in range(lo, hi + 1):
        if cap_height(path, size) <= target:
            best = size
    return best


def headroom(path, box, height):
    """Blank rows left above the tallest tone mark once it has been raised."""
    font = Font(FontType.TTF, 'ttf/' + path, '', height, 32640, False)
    font.set_heightoffset(box - height)
    font.compute_thai_mark_raise(0)
    best = 99
    for codepoint in THAI_LEVEL2:
        gindex = font.face.get_char_index(codepoint)
        if gindex == 0:
            continue
        font.face.load_glyph(gindex, FT_MONO_FLAGS)
        top = (height - font.face.glyph.bitmap_top + (box - height)
               - font.thai_mark_raise.get(codepoint, 0))
        best = min(best, top)
    return best


variants = {}
print(f"{'slot':>5s} {'box':>4s} {'weight':>10s} {'px':>3s} {'cap':>4s} "
      f"{'head':>5s} {'need':>5s}")
for slot, (box, target_cap, ttf) in sorted(SLOTS.items()):
    # The line above descends about box/6 into this line.
    need = round(box / 6)
    height = size_for_cap(ttf, target_cap)
    while height > 7 and headroom(ttf, box, height) < need:
        height -= 1
    variants[slot] = {
        "ttf": ttf,
        "height": height,
        "offset": box - height,
        "bold": False,
    }
    weight = ttf.replace('NotoSansThaiCond-', '').replace('.ttf', '')
    print(f"{slot:>5s} {box:4d} {weight:>10s} {height:3d} "
          f"{cap_height(ttf, height):4d} {headroom(ttf, box, height):5d} {need:5d}")

spec = json.load(open('lang/fonts.json'))
spec[0]['variants'] = variants
json.dump(spec, open('lang/fonts.json', 'w'), indent=4)
print("\nlang/fonts.json written")
