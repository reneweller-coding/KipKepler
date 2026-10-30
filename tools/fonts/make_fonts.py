"""Builds the pixel fonts of Kip Kepler from the hand-drawn ASCII glyphs in glyphs_small.py and glyphs_big.py.

    python tools/fonts/make_fonts.py          # assets/fonts/small.png/.txt, big.png/.txt, big_outline.png
                                              # + specimens in work/fonts/
    python tools/fonts/make_fonts.py small    # only one font

Sheet format (docs/DESIGN.md "Fonts"): cells in a grid of 16 per row, in the order of the .txt; the .txt has
`cell w h`, `baseline n`, then one line per glyph `<codepoint hex> <advance>`. The glyphs are pure white on
transparent (alpha 0 or 255) so the engine can tint them; big_outline.png has the same layout with a 1-px
palette.OUTLINE border baked around every glyph. Baseline n = the first row below the letters: capitals end on row
n-1, descenders start on row n. The pen draws the cell at its x and moves on by the advance.
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ in tools/common or here

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from common.palette import OUTLINE  # noqa: E402

import importlib  # noqa: E402

OUT = ROOT / "assets" / "fonts"
WORK = ROOT / "work" / "fonts"
WHITE = (255, 255, 255)
PER_ROW = 16

# The character set and its order in the sheets: ASCII 32-126, the extra letters and signs, the button glyphs.
EXTRA = "ÄÖÜäöüßéèàçñ€©°•…«»„“”–—’"
CHARS = [chr(c) for c in range(32, 127)] + list(EXTRA) + [chr(0xE000 + i) for i in range(10)]

FONTS = {
    # name: (module, cell w, cell h, baseline, x offset of the glyphs in the cell, spacing, digit advance)
    "small": ("glyphs_small", 8, 12, 9, 0, 1, 6),
    "big": ("glyphs_big", 16, 24, 19, 1, 2, 13),
}


def parse(text):
    """`== <char> <top> [advance]` + bitmap rows -> {char: (top, bool array, advance or None)}."""
    out = {}
    cur = None
    rows = []

    def flush():
        if cur is not None:
            ch, top, adv = cur
            w = max(len(r) for r in rows)
            if any(len(r) != w for r in rows):
                raise ValueError(f"glyph {ch!r}: rows of different width")
            out[ch] = (top, np.array([[c == "#" for c in r] for r in rows], dtype=bool), adv)

    for line in text.splitlines():
        if line.startswith("== "):
            flush()
            parts = line.split()
            tok = parts[1]
            ch = chr(int(tok[2:], 16)) if tok.startswith("U+") and len(tok) > 2 else tok
            if ch in out:
                raise ValueError(f"glyph {ch!r} twice")
            cur = (ch, int(parts[2]), int(parts[3]) if len(parts) > 3 else None)
            rows = []
        elif line.strip() and cur is not None:
            rows.append(line.strip())
    flush()
    return out


def compose(glyphs, module):
    """Adds the accented letters: base glyph + accent mark, centred over the base's ink."""
    for ch, (base, acc) in module.COMPOSED.items():
        top, bm, adv = glyphs[base]
        marks, top_cap, top_low = module.ACCENTS[acc]
        mark = np.array([[c == "#" for c in r] for r in marks], dtype=bool)
        at = top_cap if base.isupper() else top_low
        if at is None:
            raise ValueError(f"accent {acc} has no position for {base!r}")
        y0 = min(top, at)
        h = max(top + bm.shape[0], at + mark.shape[0]) - y0
        w = max(bm.shape[1], mark.shape[1])
        img = np.zeros((h, w), dtype=bool)
        img[top - y0: top - y0 + bm.shape[0], : bm.shape[1]] |= bm
        mx = (bm.shape[1] - mark.shape[1] + 1) // 2 if module.__name__ == "glyphs_small" else \
            (bm.shape[1] - mark.shape[1]) // 2
        mx = max(0, mx)
        img[at - y0: at - y0 + mark.shape[0], mx: mx + mark.shape[1]] |= mark
        glyphs[ch] = (y0, img, adv)
    return glyphs


def buttons(glyphs, module):
    """Adds the controller button glyphs that a font composes from a plate minus a symbol (glyphs_big)."""
    for ch, (plate, sym, sx, sy, top) in getattr(module, "BUTTONS", {}).items():
        pm = np.array([[c == "#" for c in r] for r in module.PLATES[plate]], dtype=bool)
        sm = np.array([[c == "#" for c in r] for r in module.SYMBOLS[sym]], dtype=bool)
        cut = np.zeros_like(pm)
        cut[sy: sy + sm.shape[0], sx: sx + sm.shape[1]] = sm
        glyphs[ch] = (top, pm & ~cut, None)
    return glyphs


def build(name):
    modname, cw, chh, base, xo, spacing, digit_adv = FONTS[name]
    module = importlib.import_module(modname)
    glyphs = buttons(compose(parse(module.GLYPHS), module), module)
    missing = [c for c in CHARS if c not in glyphs]
    if missing:
        raise SystemExit(f"{name}: glyphs missing: {' '.join(f'U+{ord(c):04X}' for c in missing)}")
    rows = (len(CHARS) + PER_ROW - 1) // PER_ROW
    sheet = np.zeros((rows * chh, PER_ROW * cw), dtype=bool)
    advances = []
    margin = 1 if name == "big" else 0  # big keeps a free pixel at every cell edge for the outline
    for i, ch in enumerate(CHARS):
        top, bm, adv = glyphs[ch]
        h, w = bm.shape
        if top < margin or top + h > chh - margin or xo + w > cw - margin:
            raise SystemExit(f"{name}: glyph {ch!r} (U+{ord(ch):04X}) leaves the cell: top {top} h {h} w {w}")
        if adv is None:
            adv = w + spacing
            if ch.isdigit():
                adv = digit_adv
        advances.append(adv)
        x0 = (i % PER_ROW) * cw + xo
        y0 = (i // PER_ROW) * chh + top
        sheet[y0: y0 + h, x0: x0 + w] |= bm
    return sheet, advances, (cw, chh, base)


def to_rgba(mask, colour=WHITE):
    a = np.zeros(mask.shape + (4,), dtype=np.uint8)
    a[mask] = colour + (255,)
    return Image.fromarray(a, "RGBA")


def outlined(mask, cw, chh):
    """White glyphs with a 1-px OUTLINE border (8-neighbourhood), cell by cell so nothing bleeds across cells."""
    rgba = np.zeros(mask.shape + (4,), dtype=np.uint8)
    for cy in range(0, mask.shape[0], chh):
        for cx in range(0, mask.shape[1], cw):
            m = mask[cy:cy + chh, cx:cx + cw]
            p = np.pad(m, 1)
            dil = np.zeros_like(m)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    dil |= p[1 + dy: 1 + dy + m.shape[0], 1 + dx: 1 + dx + m.shape[1]]
            sub = rgba[cy:cy + chh, cx:cx + cw]
            sub[dil & ~m] = OUTLINE + (255,)
            sub[m] = WHITE + (255,)
    return Image.fromarray(rgba, "RGBA")


def write_txt(path, advances, cw, chh, base):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"cell {cw} {chh}\n")
        f.write(f"baseline {base}\n")
        for ch, adv in zip(CHARS, advances):
            f.write(f"{ord(ch):04X} {adv}\n")


# ---------------------------------------------------------------------------------------------------------------
# Specimens
# ---------------------------------------------------------------------------------------------------------------

def render(text, sheet_img, advances, cw, chh, colour=None, line_gap=2):
    """Draws text with a font sheet like the engine would (pen + advance, cells drawn whole)."""
    index = {ch: i for i, ch in enumerate(CHARS)}
    lines = text.split("\n")
    width = max(sum(advances[index.get(c, index["?"])] for c in ln) for ln in lines) + cw
    img = Image.new("RGBA", (width, len(lines) * (chh + line_gap)), (0, 0, 0, 0))
    for li, ln in enumerate(lines):
        x = 0
        for c in ln:
            i = index.get(c, index["?"])
            cell = sheet_img.crop(((i % PER_ROW) * cw, (i // PER_ROW) * chh, (i % PER_ROW + 1) * cw,
                                   (i // PER_ROW + 1) * chh))
            if colour is not None:
                a = np.asarray(cell).copy()
                m = (a[..., 3] > 0) & (a[..., 0] > 200)
                a[m, :3] = colour
                cell = Image.fromarray(a, "RGBA")
            img.alpha_composite(cell, (x, li * (chh + line_gap)))
            x += advances[i]
    return img


SAMPLES = [
    "KIP KEPLER  Kristalle: 12/24  Schlüssel  Größe  Prüfung bestanden!",
    "The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs?",
    "Äußerst günstige Öl-Überprüfung: 49,90 € — „Toll“, sagt er. Café crème à la française, señor…",
    "«Bonjour» © 2026 – 100 °C • Kip’s “Beacon Corps” #1 (Ep. 3) [x] {y} <z> 50% & 7*8=56 @home",
    "Press  to jump,  to shoot,   weapons,  move,  aim,  pause,  map, "
    " back,  info",
    "SCORE 0012340   CREDITS 1985   TIME 03:27   AMMO 48/120",
    "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~",
    "Hamburgefonstiv minimum illumination jjj ggg yyy qpq Wellenwolf Quarzquelle Xylophon Zylinder",
]


def specimen(name, sheet_img, advances, cw, chh, bg=(24, 20, 40, 255)):
    parts = [render(s, sheet_img, advances, cw, chh) for s in SAMPLES]
    tinted = render("Tinted: Kristalle 12/24  SCORE 004200", sheet_img, advances, cw, chh, colour=(120, 230, 255))
    parts.append(tinted)
    w = max(p.width for p in parts) + 8
    h = sum(p.height + 4 for p in parts) + 8
    img = Image.new("RGBA", (w, h), bg)
    y = 4
    for p in parts:
        img.alpha_composite(p, (4, y))
        y += p.height + 4
    img = img.convert("RGB")
    img.save(WORK / f"specimen_{name}_1x.png")
    img.resize((img.width * 4, img.height * 4), Image.NEAREST).save(WORK / f"specimen_{name}_4x.png")
    # the 4x specimen in tiles of at most 1000 px width, so each can be looked at without being scaled down
    big = img.resize((img.width * 4, img.height * 4), Image.NEAREST)
    for old in WORK.glob(f"specimen_{name}_4x_*.png"):
        old.unlink()
    for k, x in enumerate(range(0, big.width, 1000)):
        big.crop((x, 0, min(big.width, x + 1000), big.height)).save(WORK / f"specimen_{name}_4x_{k + 1}.png")


def grid_view(name, sheet_img, cw, chh, scale):
    """The sheet enlarged, on a checker of cell backgrounds with the baseline marked."""
    base = FONTS[name][3]
    w, h = sheet_img.size
    bg = np.zeros((h, w, 4), dtype=np.uint8)
    for cy in range(0, h, chh):
        for cx in range(0, w, cw):
            odd = ((cx // cw) + (cy // chh)) % 2
            bg[cy:cy + chh, cx:cx + cw] = (40, 34, 64, 255) if odd else (30, 26, 50, 255)
            bg[cy + base, cx:cx + cw] = (70, 50, 90, 255)
    img = Image.fromarray(bg, "RGBA")
    img.alpha_composite(sheet_img)
    img.convert("RGB").resize((w * scale, h * scale), Image.NEAREST).save(WORK / f"sheet_{name}_{scale}x.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[1:] or list(FONTS):
        mask, advances, (cw, chh, base) = build(name)
        img = to_rgba(mask)
        img.save(OUT / f"{name}.png")
        write_txt(OUT / f"{name}.txt", advances, cw, chh, base)
        if name == "big":
            out = outlined(mask, cw, chh)
            out.save(OUT / "big_outline.png")
            specimen("big_outline", out, advances, cw, chh, bg=(96, 168, 214, 255))
        specimen(name, img, advances, cw, chh)
        grid_view(name, img, cw, chh, 4 if name == "small" else 3)
        print(f"{name}: {len(CHARS)} glyphs, sheet {img.width}x{img.height}")


if __name__ == "__main__":
    main()
