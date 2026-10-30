"""Draws the HUD and menu art of Kip Kepler into assets/ui/ (every colour from tools/common/palette.py, alpha 0/255).

    python tools/ui/make_ui.py        # all assets + enlarged previews in work/ui/

Files (see tools/ui/README.md for the engine side):
    hud.png + hud.txt + hud_glow.png  32x32 icons, `anim <name> 1 loop <index>` per icon (sprite-sheet format)
    bar_frame.png, bar_fill*.png, bar.txt   health/ammo bar: frame, banded fills, where the fill goes
    logo.png + logo_glow.png          "KIP KEPLER" title logo; subtitle.png a plate for a subtitle line
    panel.png + panel.txt             9-slice menu panel (48x48, 16-px corners)
    cursor.png                        menu arrow (tip at the right)
    weapon_slot.png, weapon_slot_selected.png (+ _glow)   weapon wheel slots, 40x40
    ep1.png .. ep4.png                episode cards, 200x120
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ in tools/common or here

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
from common.palette import OUTLINE, RAMPS, WHITE  # noqa: E402

OUT = ROOT / "assets" / "ui"
WORK = ROOT / "work" / "ui"
R = RAMPS


# ---------------------------------------------------------------------------------------------------------------
# Drawing toolkit: a layer is an RGB array + an opacity mask + a glow mask; shapes are boolean masks.
# ---------------------------------------------------------------------------------------------------------------

class Layer:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), dtype=np.uint8)
        self.a = np.zeros((h, w), dtype=bool)
        self.g = np.zeros((h, w), dtype=bool)

    def paint(self, mask, colour, glow=False):
        mask = mask & self.inside()
        self.rgb[mask] = colour
        self.a |= mask
        if glow:
            self.g |= mask
        else:
            self.g &= ~mask
        return self

    def erase(self, mask):
        self.a &= ~mask
        self.g &= ~mask
        self.rgb[mask] = 0
        return self

    def inside(self):
        return np.ones((self.h, self.w), dtype=bool)

    def px(self, x, y, colour, glow=False):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.rgb[y, x] = colour
            self.a[y, x] = True
            self.g[y, x] = glow
        return self

    def image(self):
        out = np.zeros((self.h, self.w, 4), dtype=np.uint8)
        out[..., :3] = self.rgb
        out[..., 3] = np.where(self.a, 255, 0)
        out[~self.a, :3] = 0
        return Image.fromarray(out, "RGBA")

    def glow_image(self):
        out = np.zeros((self.h, self.w, 4), dtype=np.uint8)
        m = self.g & self.a
        out[m, :3] = self.rgb[m]
        out[m, 3] = 255
        return Image.fromarray(out, "RGBA")

    def paste(self, other, x, y):
        """Copies another layer's opaque pixels (and glow) onto this one at (x, y)."""
        h, w = other.h, other.w
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return self
        sub = other.a[y0 - y:y1 - y, x0 - x:x1 - x]
        self.rgb[y0:y1, x0:x1][sub] = other.rgb[y0 - y:y1 - y, x0 - x:x1 - x][sub]
        self.a[y0:y1, x0:x1] |= sub
        gsub = other.g[y0 - y:y1 - y, x0 - x:x1 - x]
        self.g[y0:y1, x0:x1][sub] = gsub[sub]
        return self


def blank(w, h):
    return np.zeros((h, w), dtype=bool)


def m_poly(w, h, pts):
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=1)
    return np.array(im, dtype=bool)


def m_ellipse(w, h, box):
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).ellipse(box, fill=1)
    return np.array(im, dtype=bool)


def m_rect(w, h, x0, y0, x1, y1):
    """Inclusive rectangle."""
    m = blank(w, h)
    m[max(0, y0):max(0, y1 + 1), max(0, x0):max(0, x1 + 1)] = True
    return m


def m_line(w, h, pts, width=1):
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).line([tuple(p) for p in pts], fill=1, width=width)
    return np.array(im, dtype=bool)


def shift(m, dx, dy):
    out = np.zeros_like(m)
    h, w = m.shape
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    out[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = m[ys0:ys1, xs0:xs1]
    return out


def edge(m, dx, dy):
    """Pixels of m whose neighbour in direction (dx, dy) is outside m."""
    return m & ~shift(m, -dx, -dy)


def dilate(m, diag=False):
    out = m | shift(m, 1, 0) | shift(m, -1, 0) | shift(m, 0, 1) | shift(m, 0, -1)
    if diag:
        out |= shift(m, 1, 1) | shift(m, -1, 1) | shift(m, 1, -1) | shift(m, -1, -1)
    return out


def erode(m):
    return m & shift(m, 1, 0) & shift(m, -1, 0) & shift(m, 0, 1) & shift(m, 0, -1)


def bevel(layer, m, ramp, base, light=2, dark=-2, rim2=True, glow=False):
    """Fills mask m with ramp[base]; top/left rim lighter, bottom/right rim darker (light from the top left)."""
    rp = R[ramp] if isinstance(ramp, str) else ramp
    cl = lambda i: rp[int(np.clip(i, 0, len(rp) - 1))]
    layer.paint(m, cl(base), glow)
    lo = edge(m, 0, 1) | edge(m, 1, 0)
    hi = edge(m, 0, -1) | edge(m, -1, 0)
    if rim2:
        inner = erode(m)
        lo2 = edge(inner, 0, 1) | edge(inner, 1, 0)
        hi2 = edge(inner, 0, -1) | edge(inner, -1, 0)
        layer.paint(lo2 & ~hi2, cl(base + (dark + 1 if dark < -1 else dark)), glow)
        layer.paint(hi2 & ~lo2, cl(base + (light - 1 if light > 1 else light)), glow)
    layer.paint(lo & ~hi, cl(base + dark), glow)
    layer.paint(hi, cl(base + light), glow)
    return layer


def outline(layer, colour=OUTLINE, diag=False):
    ring = dilate(layer.a, diag) & ~layer.a
    layer.paint(ring, colour)
    return layer


def bayer4():
    return np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 + 1 / 32.0


def vgrad(layer, mask, y0, y1, colours, dither=True):
    """Vertical gradient through palette colours over rows y0..y1, ordered-dithered between neighbours."""
    h, w = layer.h, layer.w
    ys = np.arange(h)[:, None] * np.ones((1, w))
    t = np.clip((ys - y0) / max(1, (y1 - y0)), 0, 1) * (len(colours) - 1)
    i = np.floor(t).astype(int)
    f = t - i
    b = np.tile(bayer4(), (h // 4 + 1, w // 4 + 1))[:h, :w]
    if dither:
        i = np.where(f > b, i + 1, i)
    i = np.clip(i, 0, len(colours) - 1)
    for k, c in enumerate(colours):
        layer.paint(mask & (i == k), c)
    return layer


def stars(layer, mask, count, seed, colours=None, crosses=0):
    rng = np.random.default_rng(seed)
    colours = colours or [R["slate"][5], R["ice"][6], R["ice"][7], WHITE]
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return layer
    for k in range(count):
        j = rng.integers(len(xs))
        layer.px(int(xs[j]), int(ys[j]), colours[rng.integers(len(colours))])
    for k in range(crosses):
        j = rng.integers(len(xs))
        x, y = int(xs[j]), int(ys[j])
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if mask[min(layer.h - 1, max(0, y + dy)), min(layer.w - 1, max(0, x + dx))]:
                layer.px(x + dx, y + dy, WHITE if (dx, dy) == (0, 0) else R["ice"][6], glow=(dx, dy) == (0, 0))
    return layer


def sparkle(layer, x, y, size=2, core=WHITE, arm=None, glow=True):
    arm = arm or R["ice"][6]
    layer.px(x, y, core, glow)
    for k in range(1, size + 1):
        c = arm if k < size else R["ice"][5]
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            layer.px(x + dx, y + dy, c, glow)
    return layer


def save(layer, name, glow=False, preview_scale=4, bg=(70, 74, 96)):
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    img = layer.image()
    img.save(OUT / f"{name}.png")
    if glow:
        layer.glow_image().save(OUT / f"{name}_glow.png")
    prev = Image.new("RGBA", img.size, bg + (255,))
    prev.alpha_composite(img)
    prev.convert("RGB").resize((img.width * preview_scale, img.height * preview_scale), Image.NEAREST).save(
        WORK / f"{name}_{preview_scale}x.png")
    return img


def check_palette(img, name):
    """Every opaque pixel must be a palette colour, alpha only 0 or 255."""
    from common.palette import palette
    a = np.asarray(img)
    pal = {tuple(c) for c in palette()}
    pal.add((255, 255, 255))
    alpha = set(np.unique(a[..., 3]).tolist())
    bad = {tuple(c) for c in a[a[..., 3] > 0][:, :3]} - pal
    if bad or not alpha <= {0, 255}:
        raise SystemExit(f"{name}: off-palette colours {list(bad)[:5]} / alpha {alpha}")


# ---------------------------------------------------------------------------------------------------------------
# HUD icons (32 x 32)
# ---------------------------------------------------------------------------------------------------------------

S = 32


def icon_crystal():
    L = Layer(S, S)
    top = m_poly(S, S, [(10, 10), (16, 3), (22, 10), (16, 13)])
    left = m_poly(S, S, [(10, 10), (16, 13), (16, 28), (11, 23)])
    right = m_poly(S, S, [(22, 10), (16, 13), (16, 28), (21, 23)])
    L.paint(left, R["cyan"][5], True)
    L.paint(right, R["violet"][4], True)
    L.paint(top, R["ice"][7], True)
    L.paint(edge(left, -1, 0) & ~top, R["cyan"][7], True)
    L.paint(edge(right, 1, 0), R["violet"][3], True)
    L.paint(m_line(S, S, [(16, 14), (16, 27)]), R["cyan"][6], True)       # the ridge
    L.paint(m_line(S, S, [(20, 14), (19, 22)]), R["magenta"][5], True)    # a prism sliver
    L.paint(m_line(S, S, [(12, 13), (13, 20)]), R["ice"][7], True)
    outline(L)
    sparkle(L, 24, 6, 2)
    return L


def icon_health():
    L = Layer(S, S)
    m = m_ellipse(S, S, (5, 6, 16, 17)) | m_ellipse(S, S, (15, 6, 26, 17)) | m_poly(S, S, [(5, 12), (26, 12), (16, 26),
                                                                                             (15, 26)])
    bevel(L, m, "red", 4, light=2, dark=-2)
    L.paint(m_rect(S, S, 8, 9, 10, 10) | m_rect(S, S, 8, 11, 8, 12), R["rose"][7])
    L.paint(m_rect(S, S, 9, 9, 9, 9), WHITE)
    outline(L)
    return L


def icon_key(ramp, chip):
    L = Layer(S, S)
    card = m_poly(S, S, [(8, 8), (24, 8), (25, 9), (25, 23), (24, 24), (7, 24), (6, 23), (6, 10)])
    bevel(L, card, ramp, 4, light=2, dark=-2)
    L.paint(m_rect(S, S, 8, 20, 23, 21), R[ramp][2])                     # magnetic stripe
    L.paint(m_rect(S, S, 9, 11, 14, 16), R[chip][5])                     # chip
    L.paint(m_rect(S, S, 9, 11, 14, 11) | m_rect(S, S, 9, 11, 9, 16), R[chip][7])
    L.paint(m_rect(S, S, 10, 13, 13, 13) | m_rect(S, S, 11, 12, 11, 15), R[chip][3])
    L.paint(m_rect(S, S, 17, 11, 22, 11) | m_rect(S, S, 17, 14, 21, 14), R[ramp][6])  # print lines
    L.erase(m_rect(S, S, 21, 16, 22, 17))                                # lanyard hole
    L.paint(m_rect(S, S, 21, 18, 22, 18) | m_rect(S, S, 23, 16, 23, 17), R[ramp][2])
    outline(L)
    return L


def icon_star():
    L = Layer(S, S)
    cx, cy = 16, 17
    pts = []
    for k in range(10):
        ang = -np.pi / 2 + k * np.pi / 5
        r = 12.5 if k % 2 == 0 else 5.2
        pts.append((cx + r * np.cos(ang), cy + r * np.sin(ang)))
    m = m_poly(S, S, pts)
    bevel(L, m, "yellow", 4, light=2, dark=-2)
    L.paint(m_rect(S, S, 15, 9, 15, 13) | m_rect(S, S, 13, 14, 15, 14), R["yellow"][7], True)
    outline(L)
    sparkle(L, 24, 7, 1)
    return L


def icon_clock():
    L = Layer(S, S)
    L.paint(m_rect(S, S, 14, 3, 18, 5), R["steel"][5])
    L.paint(m_rect(S, S, 15, 6, 17, 7), R["steel"][3])
    L.paint(m_rect(S, S, 23, 7, 25, 9), R["steel"][4])
    rim = m_ellipse(S, S, (5, 7, 27, 29))
    bevel(L, rim, "steel", 4, light=2, dark=-2)
    face = m_ellipse(S, S, (8, 10, 24, 26))
    L.paint(face, R["ice"][7])
    L.paint(edge(face, 0, -1) | edge(face, -1, 0), R["ice"][5])
    for x, y in ((16, 11), (16, 25), (9, 18), (23, 18)):
        L.px(x, y, R["slate"][2])
    L.paint(m_rect(S, S, 16, 12, 16, 18), R["slate"][1])                 # minute hand
    L.paint(m_rect(S, S, 16, 18, 21, 18), R["orange"][3])                # second hand
    L.px(16, 18, R["orange"][4])
    outline(L)
    return L


def icon_overdrive():
    L = Layer(S, S)
    hexa = m_poly(S, S, [(16, 3), (27, 9), (27, 23), (16, 29), (5, 23), (5, 9)])
    bevel(L, hexa, "orange", 3, light=2, dark=-2)
    bolt = m_poly(S, S, [(18, 6), (10, 18), (15, 18), (13, 27), (22, 14), (17, 14), (20, 6)])
    L.paint(bolt, R["yellow"][6], True)
    L.paint(edge(bolt, -1, 0) | edge(bolt, 0, -1), R["yellow"][7], True)
    L.paint(edge(bolt, 1, 0) & ~edge(bolt, -1, 0), R["yellow"][4], True)
    outline(L)
    return L


def icon_boots():
    L = Layer(S, S)
    shaft = m_poly(S, S, [(10, 5), (18, 5), (18, 17), (10, 17)])
    foot = m_poly(S, S, [(10, 16), (21, 16), (25, 19), (25, 23), (10, 23)])
    m = shaft | foot
    bevel(L, m, "teal", 4, light=2, dark=-2)
    L.paint(m_rect(S, S, 10, 9, 18, 10), R["cyan"][5], True)             # glow band
    L.paint(m_rect(S, S, 10, 21, 25, 23), R["steel"][2])                 # sole
    L.paint(m_rect(S, S, 10, 21, 25, 21), R["steel"][4])
    wing = m_poly(S, S, [(18, 7), (25, 4), (26, 6), (21, 9), (24, 9), (19, 12)])
    L.paint(wing, R["ice"][7])
    L.paint(edge(wing, 0, 1), R["ice"][5])
    flame = m_poly(S, S, [(11, 24), (19, 24), (15, 30)])
    L.paint(flame, R["orange"][4], True)
    L.paint(m_poly(S, S, [(13, 24), (17, 24), (15, 27)]), R["yellow"][6], True)
    outline(L)
    return L


def icon_shield():
    L = Layer(S, S)
    m = m_poly(S, S, [(6, 6), (16, 3), (26, 6), (26, 15), (16, 29), (6, 15)])
    bevel(L, m, "cyan", 3, light=2, dark=-2, glow=False)
    inner = m_poly(S, S, [(11, 9), (16, 7), (21, 9), (21, 15), (16, 23), (11, 15)])
    L.paint(inner, R["cyan"][5], True)
    L.paint(edge(inner, 0, -1) | edge(inner, -1, 0), R["ice"][7], True)
    L.paint(m_rect(S, S, 15, 8, 16, 21), R["ice"][7], True)
    outline(L)
    return L


def icon_ammo():
    L = Layer(S, S)
    L.paint(m_rect(S, S, 13, 4, 19, 6), R["steel"][5])
    L.paint(m_rect(S, S, 13, 4, 19, 4), R["steel"][7])
    body = m_poly(S, S, [(12, 7), (20, 7), (21, 8), (21, 27), (20, 28), (12, 28), (11, 27), (11, 8)])
    bevel(L, body, "steel", 3, light=2, dark=-2)
    win = m_rect(S, S, 13, 10, 19, 25)
    L.paint(win, R["lime"][4], True)
    L.paint(m_rect(S, S, 13, 10, 13, 25), R["lime"][6], True)
    for y in (14, 18, 22):
        L.paint(m_rect(S, S, 13, y, 19, y), R["lime"][2])
    L.paint(m_rect(S, S, 15, 11, 15, 12), R["lime"][7], True)
    outline(L)
    return L


def icon_skull():
    L = Layer(S, S)
    head = m_ellipse(S, S, (6, 4, 25, 22))
    jaw = m_poly(S, S, [(10, 19), (21, 19), (21, 26), (10, 26)])
    bevel(L, head | jaw, "grey", 6, light=1, dark=-2)
    L.paint(m_rect(S, S, 6, 13, 25, 13) & head, R["steel"][4])          # visor seam
    eye_l = m_rect(S, S, 10, 14, 14, 17)
    eye_r = m_rect(S, S, 17, 14, 21, 17)
    L.paint(eye_l | eye_r, R["slate"][1])
    L.paint(m_rect(S, S, 12, 15, 13, 16) | m_rect(S, S, 19, 15, 20, 16), R["red"][5], True)
    L.paint(m_rect(S, S, 15, 18, 16, 19), R["slate"][2])                 # nose
    for x in (12, 15, 18):
        L.paint(m_rect(S, S, x, 22, x, 26), R["grey"][3])                # teeth gaps
    L.paint(m_rect(S, S, 10, 21, 21, 21), R["grey"][4])
    L.paint(m_rect(S, S, 15, 5, 16, 7), R["orange"][4])                  # antenna stub
    outline(L)
    return L


def icon_secret():
    L = Layer(S, S)
    m = m_poly(S, S, [(16, 2), (29, 16), (16, 29), (3, 16)])
    bevel(L, m, "purple", 3, light=2, dark=-2)
    q = [
        ".#####.",
        "##...##",
        ".....##",
        "....##.",
        "...##..",
        "...##..",
        ".......",
        "...##..",
        "...##..",
    ]
    qm = blank(S, S)
    for j, row in enumerate(q):
        for i, ch in enumerate(row):
            if ch == "#":
                qm[11 + j, 13 + i] = True
    L.paint(shift(qm, 1, 1) & ~qm, R["purple"][1])  # a drop shadow under the mark
    L.paint(qm, R["magenta"][7], True)
    outline(L)
    return L


def icon_credits():
    L = Layer(S, S)
    coin = m_poly(S, S, [(11, 4), (21, 4), (27, 10), (27, 22), (21, 28), (11, 28), (5, 22), (5, 10)])
    bevel(L, coin, "yellow", 4, light=2, dark=-2)
    ring = m_poly(S, S, [(12, 8), (20, 8), (24, 12), (24, 20), (20, 24), (12, 24), (8, 20), (8, 12)])
    L.paint(edge(ring, 0, -1) | edge(ring, -1, 0), R["yellow"][2])
    L.paint(edge(ring, 0, 1) | edge(ring, 1, 0), R["yellow"][6])
    # the credit sign: a C with a bar
    c = (m_rect(S, S, 12, 11, 19, 12) | m_rect(S, S, 11, 12, 12, 20) | m_rect(S, S, 12, 20, 19, 21))
    bar = m_rect(S, S, 15, 9, 16, 23)
    L.paint(shift(c | bar, 1, 1) & ~(c | bar), R["yellow"][2])
    L.paint(c | bar, R["yellow"][7])
    outline(L)
    return L


# --- weapons: side views pointing right; steel bodies, colour-coded energy parts (glow) ------------------------

def gun_base(L, body, ramp="steel", base=4):
    bevel(L, body, ramp, base, light=2, dark=-2)


def icon_blaster():
    L = Layer(S, S)
    gun_base(L, m_poly(S, S, [(6, 12), (20, 12), (21, 13), (21, 20), (6, 20), (5, 19), (5, 13)]))
    gun_base(L, m_rect(S, S, 21, 14, 26, 18), base=3)
    L.paint(m_rect(S, S, 26, 13, 27, 19), R["steel"][6])
    L.paint(m_rect(S, S, 9, 21, 13, 26), R["slate"][3])
    L.paint(m_rect(S, S, 9, 21, 9, 26), R["slate"][4])
    L.paint(m_rect(S, S, 8, 14, 16, 17), R["cyan"][5], True)
    L.paint(m_rect(S, S, 8, 14, 16, 14), R["cyan"][7], True)
    L.paint(m_rect(S, S, 23, 15, 24, 16), R["cyan"][6], True)
    outline(L)
    return L


def icon_repeater():
    L = Layer(S, S)
    gun_base(L, m_poly(S, S, [(4, 11), (17, 11), (18, 12), (18, 21), (4, 21), (3, 20), (3, 12)]))
    for y in (12, 15, 18):
        gun_base(L, m_rect(S, S, 18, y, 28, y + 2), base=3, ramp="steel")
    L.paint(m_rect(S, S, 26, 11, 27, 21), R["steel"][6])
    L.paint(m_ellipse(S, S, (6, 18, 15, 27)), R["orange"][3], True)
    L.paint(m_ellipse(S, S, (8, 20, 13, 25)), R["orange"][5], True)
    L.paint(m_rect(S, S, 6, 13, 15, 14), R["orange"][4], True)
    L.paint(m_rect(S, S, 6, 13, 15, 13), R["orange"][6], True)
    outline(L)
    return L


def icon_scatter():
    L = Layer(S, S)
    gun_base(L, m_poly(S, S, [(5, 12), (17, 12), (17, 21), (5, 21), (4, 20), (4, 13)]))
    flare = m_poly(S, S, [(16, 12), (27, 7), (28, 8), (28, 25), (27, 26), (16, 21)])
    gun_base(L, flare, base=3)
    L.paint(m_poly(S, S, [(20, 13), (26, 11), (26, 22), (20, 20)]), R["yellow"][4], True)
    for y in (13, 16, 19):
        L.paint(m_rect(S, S, 21, y, 25, y), R["yellow"][6], True)
    L.paint(m_rect(S, S, 8, 22, 12, 27), R["slate"][3])
    L.paint(m_rect(S, S, 7, 14, 13, 15), R["yellow"][5], True)
    outline(L)
    return L


def icon_ricochet():
    L = Layer(S, S)
    gun_base(L, m_poly(S, S, [(4, 16), (24, 16), (26, 18), (26, 22), (4, 22), (3, 21), (3, 17)]))
    L.paint(m_rect(S, S, 8, 23, 12, 27), R["slate"][3])
    disc = m_ellipse(S, S, (8, 6, 24, 15))
    bevel(L, disc, "green", 4, light=2, dark=-2, glow=True)
    L.paint(m_ellipse(S, S, (13, 9, 19, 12)), R["green"][2], True)
    L.paint(m_rect(S, S, 15, 10, 17, 11), R["green"][6], True)
    L.paint(m_rect(S, S, 6, 18, 20, 19), R["green"][5], True)
    outline(L)
    return L


def icon_cryo():
    L = Layer(S, S)
    tank = m_poly(S, S, [(5, 10), (11, 10), (12, 11), (12, 22), (11, 23), (5, 23), (4, 22), (4, 11)])
    bevel(L, tank, "ice", 5, light=2, dark=-2)
    L.paint(m_rect(S, S, 6, 12, 7, 21), R["ice"][7], True)
    gun_base(L, m_rect(S, S, 12, 13, 22, 19))
    nozzle = m_poly(S, S, [(22, 12), (27, 10), (28, 11), (28, 21), (27, 22), (22, 20)])
    bevel(L, nozzle, "ice", 4, light=2, dark=-2, glow=True)
    L.paint(m_rect(S, S, 14, 15, 20, 16), R["cyan"][6], True)
    L.paint(m_rect(S, S, 14, 20, 17, 25), R["slate"][3])
    outline(L)
    for x, y in ((25, 4), (29, 6)):
        sparkle(L, x, y, 1, core=WHITE, arm=R["ice"][6])
    return L


def icon_lancer():
    L = Layer(S, S)
    gun_base(L, m_poly(S, S, [(3, 13), (16, 13), (17, 14), (17, 20), (3, 20), (2, 19), (2, 14)]))
    gun_base(L, m_rect(S, S, 17, 15, 29, 17), base=3)
    L.paint(m_rect(S, S, 28, 14, 29, 18), R["steel"][6])
    em = m_poly(S, S, [(9, 12), (14, 8), (16, 9), (16, 12)])
    L.paint(em, R["red"][4], True)
    L.paint(edge(em, 0, -1), R["red"][6], True)
    L.paint(m_rect(S, S, 18, 16, 27, 16), R["red"][5], True)
    L.paint(m_rect(S, S, 5, 15, 13, 16), R["red"][4], True)
    L.paint(m_rect(S, S, 6, 21, 10, 26), R["slate"][3])
    outline(L)
    return L


def icon_mortar():
    L = Layer(S, S)
    base = m_poly(S, S, [(4, 22), (19, 22), (20, 23), (20, 26), (4, 26), (3, 25), (3, 23)])
    gun_base(L, base, base=3)
    tube = m_poly(S, S, [(7, 21), (20, 8), (26, 14), (13, 27)])
    gun_base(L, tube, base=4)
    L.paint(m_poly(S, S, [(11, 21), (19, 13), (21, 15), (13, 23)]), R["violet"][4], True)
    mouth = m_poly(S, S, [(19, 7), (21, 5), (29, 13), (27, 15)])
    L.paint(mouth, R["steel"][6])
    shell = m_ellipse(S, S, (21, 3, 27, 9))
    L.paint(shell, R["violet"][5], True)
    L.paint(m_rect(S, S, 23, 4, 24, 5), R["violet"][7], True)
    outline(L)
    return L


def icon_arc():
    L = Layer(S, S)
    gun_base(L, m_poly(S, S, [(4, 12), (16, 12), (17, 13), (17, 21), (4, 21), (3, 20), (3, 13)]))
    for y in (10, 21):
        prong = m_rect(S, S, 16, y, 27, y + 2)
        gun_base(L, prong, base=3)
        for x in (19, 22, 25):
            L.paint(m_rect(S, S, x, y, x, y + 2), R["blue"][5], True)
    zig = m_line(S, S, [(27, 13), (24, 15), (27, 17), (24, 19), (27, 20)], width=1)
    L.paint(zig, R["blue"][7], True)
    L.paint(m_rect(S, S, 6, 14, 14, 18), R["blue"][4], True)
    L.paint(m_rect(S, S, 6, 14, 14, 14), R["blue"][6], True)
    L.paint(m_rect(S, S, 7, 22, 11, 27), R["slate"][3])
    outline(L)
    sparkle(L, 29, 16, 1, core=WHITE, arm=R["blue"][6])
    return L


def icon_seeker():
    L = Layer(S, S)
    box = m_poly(S, S, [(5, 9), (21, 9), (22, 10), (22, 24), (5, 24), (4, 23), (4, 10)])
    gun_base(L, box, base=3)
    for y in (10, 15, 20):
        tip = m_poly(S, S, [(22, y), (25, y), (28, y + 1.5), (25, y + 3), (22, y + 3)])
        L.paint(tip, R["magenta"][4], True)
        L.paint(edge(tip, 0, -1), R["magenta"][6], True)
        L.paint(m_rect(S, S, 19, y, 21, y + 3), R["slate"][1])
    L.paint(m_rect(S, S, 7, 12, 15, 13), R["magenta"][5], True)
    L.paint(m_rect(S, S, 8, 25, 12, 28), R["slate"][3])
    outline(L)
    return L


HUD = [
    ("crystal", icon_crystal),
    ("health", icon_health),
    ("key_blue", lambda: icon_key("blue", "yellow")),
    ("key_gold", lambda: icon_key("yellow", "steel")),
    ("score", icon_star),
    ("clock", icon_clock),
    ("power_overdrive", icon_overdrive),
    ("power_boots", icon_boots),
    ("power_shield", icon_shield),
    ("ammo", icon_ammo),
    ("skull", icon_skull),
    ("secret", icon_secret),
    ("credits", icon_credits),
    ("weapon_blaster", icon_blaster),
    ("weapon_repeater", icon_repeater),
    ("weapon_scatter", icon_scatter),
    ("weapon_ricochet", icon_ricochet),
    ("weapon_cryo", icon_cryo),
    ("weapon_lancer", icon_lancer),
    ("weapon_mortar", icon_mortar),
    ("weapon_arc", icon_arc),
    ("weapon_seeker", icon_seeker),
]
ALIASES = {"heart": "health", "star": "score"}


def make_hud():
    cols = 8
    rows = (len(HUD) + cols - 1) // cols
    sheet = Layer(cols * S, rows * S)
    for i, (name, fn) in enumerate(HUD):
        sheet.paste(fn(), (i % cols) * S, (i // cols) * S)
    img = save(sheet, "hud", glow=True, preview_scale=4)
    check_palette(img, "hud")
    index = {name: i for i, (name, _) in enumerate(HUD)}
    with open(OUT / "hud.txt", "w", encoding="utf-8", newline="\n") as f:
        f.write("# HUD icons (tools/ui/make_ui.py). One frame per icon; hud_glow.png = emissive mask.\n")
        f.write(f"frame {S} {S}\n")
        f.write(f"anchor {S // 2} {S // 2}\n")
        for name, _ in HUD:
            f.write(f"anim {name} 1 loop {index[name]}\n")
        for alias, name in ALIASES.items():
            f.write(f"anim {alias} 1 loop {index[name]}\n")


# ---------------------------------------------------------------------------------------------------------------
# Health / ammo bar
# ---------------------------------------------------------------------------------------------------------------

BAR_W, BAR_H = 100, 14
FILL_X, FILL_Y, FILL_W, FILL_H = 4, 3, 92, 8


def make_bar():
    L = Layer(BAR_W, BAR_H)
    body = m_poly(BAR_W, BAR_H, [(4, 1), (98, 1), (98, 9), (95, 12), (1, 12), (1, 4)])
    bevel(L, body, "steel", 4, light=2, dark=-2, rim2=False)
    win = m_rect(BAR_W, BAR_H, FILL_X, FILL_Y, FILL_X + FILL_W - 1, FILL_Y + FILL_H - 1)
    L.paint(dilate(win, True) & ~win, OUTLINE)
    L.paint(win, R["slate"][1])
    L.paint(m_rect(BAR_W, BAR_H, FILL_X, FILL_Y, FILL_X + FILL_W - 1, FILL_Y), R["slate"][0])
    for x in range(FILL_X + 9, FILL_X + FILL_W - 1, 10):          # faint cell marks in the empty part
        L.paint(m_rect(BAR_W, BAR_H, x, FILL_Y + 2, x, FILL_Y + FILL_H - 2), R["slate"][2])
    L.paint(m_rect(BAR_W, BAR_H, 2, 5, 2, 9), R["cyan"][5], True)  # status light on the left cap
    outline(L)
    img = save(L, "bar_frame", glow=False, preview_scale=6)
    check_palette(img, "bar_frame")

    def fill(name, ramp, shades):
        F = Layer(FILL_W, FILL_H)
        for y, k in enumerate(shades):
            F.paint(m_rect(FILL_W, FILL_H, 0, y, FILL_W - 1, y), R[ramp][k])
        for x in range(9, FILL_W, 10):                            # cell gaps, one shade darker
            for y, k in enumerate(shades):
                F.px(x, y, R[ramp][max(0, k - 2)])
        img = save(F, name, preview_scale=6)
        check_palette(img, name)

    fill("bar_fill", "lime", [7, 6, 5, 4, 4, 3, 3, 2])
    fill("bar_fill_low", "red", [7, 6, 5, 4, 4, 3, 3, 2])
    fill("bar_fill_white", "grey", [7, 7, 6, 6, 6, 5, 5, 4])
    with open(OUT / "bar.txt", "w", encoding="utf-8", newline="\n") as f:
        f.write("# health/ammo bar (tools/ui/make_ui.py)\n")
        f.write("# draw bar_frame.png, then a fill at (fill x, fill y), cropped to width round(fill w * fraction)\n")
        f.write(f"frame {BAR_W} {BAR_H}\n")
        f.write(f"fill {FILL_X} {FILL_Y} {FILL_W} {FILL_H}\n")


# ---------------------------------------------------------------------------------------------------------------
# Title logo
# ---------------------------------------------------------------------------------------------------------------

LOGO_W, LOGO_H = 420, 110
LH, LS, LB, LC = 64, 14, 11, 10          # letter height, stem, bar, chamfer


def _band(x0, y0, x1, y1, hw):
    return [(x0 - hw, y0), (x0 + hw, y0), (x1 + hw, y1), (x1 - hw, y1)]


def letter(ch):
    """Polygons (filled) and holes of a logo letter in its own box; returns (width, polys, holes)."""
    H, S, B, C = LH, LS, LB, LC
    if ch == "K":
        W = 40
        return W, [[(0, 0), (S - 1, 0), (S - 1, H - 1), (0, H - 1)],
                   _band(S + 3, 35, W - 8, 0, 7.5), _band(S + 5, 27, W - 8, H - 1, 7.5)], []
    if ch == "I":
        return S, [[(0, 0), (S - 1, 0), (S - 1, H - 1), (0, H - 1)]], []
    if ch == "P":
        W = 38
        return W, [[(0, 0), (W - 1 - C, 0), (W - 1, C), (W - 1, 40 - C), (W - 1 - C, 40), (S - 1, 40),
                    (S - 1, H - 1), (0, H - 1)]], [[(S, B), (W - 1 - S, B), (W - 1 - S, 40 - B), (S, 40 - B)]]
    if ch == "E":
        W = 34
        m = 26
        return W, [[(0, 0), (W - 1, 0), (W - 1, B - 1), (S - 1, B - 1), (S - 1, m), (W - 6, m), (W - 6, m + B - 1),
                    (S - 1, m + B - 1), (S - 1, H - B), (W - 1, H - B), (W - 1, H - 1), (0, H - 1)]], []
    if ch == "L":
        W = 32
        return W, [[(0, 0), (S - 1, 0), (S - 1, H - B), (W - 1, H - B), (W - 1, H - 1), (0, H - 1)]], []
    if ch == "R":
        W = 40
        bot = 38
        return W, [[(0, 0), (W - 1 - C, 0), (W - 1, C), (W - 1, bot - C), (W - 1 - C, bot), (S - 1, bot),
                    (S - 1, H - 1), (0, H - 1)],
                   [(W - S - 9, bot - 2), (W - 9, bot - 2), (W - 1, bot + 6), (W - 1, H - 1), (W - S, H - 1),
                    (W - S, bot + 12)]], [[(S, B), (W - 1 - S, B), (W - 1 - S, bot - B), (S, bot - B)]]
    raise KeyError(ch)


def make_logo():
    W, H = LOGO_W, LOGO_H
    text, gap, space = "KIP KEPLER", 7, 18
    widths = [space if c == " " else letter(c)[0] for c in text]
    total = sum(widths) + gap * (len(text) - 1 - 2)
    x = (W - total - 7) // 2
    y0 = 22
    front = blank(W, H)
    places = {}
    for c, w in zip(text, widths):
        if c == " ":
            x += space - gap
            continue
        lw, polys, holes = letter(c)
        m = blank(W, H)
        for p in polys:
            m |= m_poly(W, H, [(px + x, py + y0) for px, py in p])
        box = m_rect(W, H, x, y0, x + lw - 1, y0 + LH - 1)
        m &= box
        for p in holes:
            m &= ~m_poly(W, H, [(px + x, py + y0) for px, py in p])
        front |= m
        places.setdefault(c, []).append(x)
        x += lw + gap
    L = Layer(W, H)
    # extrusion towards the bottom right (in the shadow)
    depth = 6
    ext = blank(W, H)
    for k in range(1, depth + 1):
        ext |= shift(front, k, k)
    ext &= ~front
    L.paint(ext, R["violet"][1])
    L.paint(ext & ~shift(front, 3, 3) & ~shift(front, 2, 2) & ~shift(front, 1, 1), R["violet"][0])
    L.paint(edge(ext, -1, 1) & ext, R["violet"][2])               # the lit lower-left edge of the extrusion
    # prism bands on the face
    ys = np.arange(H)[:, None] - y0
    bands = [(0, 20, R["cyan"][5], True), (20, 30, R["cyan"][4], True), (30, 32, R["ice"][7], True),
             (32, 44, R["violet"][5], False), (44, 56, R["violet"][4], False), (56, 64, R["violet"][3], False)]
    for a, b, col, gl in bands:
        L.paint(front & (ys >= a) & (ys < b), col, gl)
    # bevel: bright top/left rims, dark bottom/right rims
    hi1 = edge(front, 0, -1) | edge(front, -1, 0)
    lo1 = (edge(front, 0, 1) | edge(front, 1, 0)) & ~hi1
    inner = front & ~hi1 & ~lo1
    hi2 = (edge(inner, 0, -1) | edge(inner, -1, 0))
    L.paint(hi2 & (ys < 30), R["cyan"][6], True)
    L.paint(hi2 & (ys >= 32), R["violet"][6])
    L.paint(lo1, R["violet"][2])
    L.paint(hi1 & (ys < 32), R["ice"][7], True)
    L.paint(hi1 & (ys >= 32), R["violet"][7])
    # diagonal glints
    xs = np.arange(W)[None, :]
    d = xs - ys
    for g0 in (22, 150, 290):
        glint = front & (((d >= g0) & (d < g0 + 3)) | ((d >= g0 + 6) & (d < g0 + 7))) & ~lo1
        L.paint(glint & (ys < 32), WHITE, True)
        L.paint(glint & (ys >= 32), R["violet"][7], True)
    outline(L, diag=True)
    # orange accents: the beacon above the I, and a thruster stripe under KEPLER
    ix = places["I"][0] + LS // 2
    by = y0 - 11
    star = blank(W, H)
    for k in range(0, 8):
        wdt = max(0, 2 - k // 3)
        star |= m_rect(W, H, ix - wdt, by - k, ix + wdt, by + k) if k < 2 else False
    core = m_ellipse(W, H, (ix - 3, by - 3, ix + 3, by + 3))
    rays = (m_rect(W, H, ix - 9, by, ix + 9, by) | m_rect(W, H, ix, by - 9, ix, by + 7) |
            m_rect(W, H, ix - 5, by - 1, ix + 5, by + 1) | m_rect(W, H, ix - 1, by - 5, ix + 1, by + 5))
    L.paint(dilate(core | rays) & ~(core | rays) & ~L.a, OUTLINE)
    L.paint(rays, R["orange"][4], True)
    L.paint(core, R["orange"][5], True)
    L.paint(m_rect(W, H, ix - 1, by - 1, ix + 1, by + 1), R["yellow"][7], True)
    L.px(ix, by, WHITE, True)
    kx = places["K"][1]
    rx = places["R"][0] + letter("R")[0] + 6
    sy = y0 + LH + 9
    stripe = m_poly(W, H, [(kx + 4, sy), (rx, sy), (rx - 4, sy + 4), (kx, sy + 4)])
    L.paint(dilate(stripe, True) & ~stripe & ~L.a, OUTLINE)
    L.paint(stripe, R["orange"][4], True)
    L.paint(edge(stripe, 0, -1), R["orange"][6], True)
    L.paint(edge(stripe, 0, 1) & ~edge(stripe, 0, -1), R["orange"][3], True)
    for cx in range(kx + 12, rx - 8, 9):                           # chevrons
        L.paint(m_poly(W, H, [(cx, sy + 1), (cx + 2, sy + 1), (cx + 4, sy + 2), (cx + 2, sy + 3), (cx, sy + 3),
                              (cx + 2, sy + 2)]), R["orange"][2], False)
    img = save(L, "logo", glow=True, preview_scale=2, bg=(28, 24, 48))
    check_palette(img, "logo")
    check_palette(Image.open(OUT / "logo_glow.png"), "logo_glow")
    # the plate for a subtitle line (the engine writes the text: small font centred, or big font)
    SW, SH = 240, 22
    P = Layer(SW, SH)
    plate = m_poly(SW, SH, [(7, 1), (232, 1), (238, 7), (238, 14), (232, 20), (7, 20), (1, 14), (1, 7)])
    bevel(P, plate, "slate", 3, light=2, dark=-2, rim2=False)
    inner = m_poly(SW, SH, [(8, 3), (231, 3), (235, 7), (235, 14), (231, 18), (8, 18), (4, 14), (4, 7)])
    P.paint(dilate(inner) & ~inner & plate & ~edge(plate, 0, -1) & ~edge(plate, -1, 0), OUTLINE)
    P.paint(inner, R["slate"][1])
    P.paint(m_rect(SW, SH, 12, 4, 227, 4), R["cyan"][3], True)
    for x0 in (5, 231):
        P.paint(m_rect(SW, SH, x0, 8, x0 + 3, 13) & inner, R["orange"][4], True)
    outline(P)
    img = save(P, "subtitle", glow=True, preview_scale=3)
    check_palette(img, "subtitle")


# ---------------------------------------------------------------------------------------------------------------
# Menu panel (9-slice), cursor, weapon slots
# ---------------------------------------------------------------------------------------------------------------

def frame_shape(n, cut):
    return m_poly(n, n, [(cut, 0), (n - 1 - cut, 0), (n - 1, cut), (n - 1, n - 1 - cut), (n - 1 - cut, n - 1),
                         (cut, n - 1), (0, n - 1 - cut), (0, cut)])


def make_panel():
    n = 48
    L = Layer(n, n)
    outer = frame_shape(n, 5)
    L.paint(outer, OUTLINE)
    ring = frame_shape(n - 2, 4)
    ring = shift(np.pad(ring, ((0, 2), (0, 2))), 1, 1)[:n, :n]
    bevel(L, ring, "steel", 4, light=2, dark=-2, rim2=False)
    inner = m_rect(n, n, 4, 4, n - 5, n - 5)
    L.paint(dilate(inner, True) & ~inner, OUTLINE)
    L.paint(inner, R["slate"][1])
    L.paint(m_rect(n, n, 4, 4, n - 5, 4), R["slate"][2])           # a lit top inner edge
    for (x, y, dx, dy) in ((5, 5, 1, 1), (n - 6, 5, -1, 1), (5, n - 6, 1, -1), (n - 6, n - 6, -1, -1)):
        for k in range(4):                                         # cyan corner brackets
            L.px(x + dx * k, y, R["cyan"][5], True)
            L.px(x, y + dy * k, R["cyan"][5], True)
    img = save(L, "panel", glow=True, preview_scale=6)
    check_palette(img, "panel")
    with open(OUT / "panel.txt", "w", encoding="utf-8", newline="\n") as f:
        f.write("# menu panel, 9-slice (tools/ui/make_ui.py): corners 16 px stay, edges and centre stretch or tile\n")
        f.write("slice 16\n")


def make_cursor():
    n = 16
    L = Layer(n, n)
    arrow = m_poly(n, n, [(2, 2), (7, 2), (13, 8), (7, 14), (2, 14), (7, 8)])
    bevel(L, arrow, "orange", 4, light=2, dark=-2, rim2=False, glow=True)
    L.paint(m_poly(n, n, [(4, 3), (7, 3), (11, 7), (8, 7)]), R["yellow"][6], True)
    outline(L, diag=True)
    img = save(L, "cursor", glow=True, preview_scale=8)
    check_palette(img, "cursor")


def make_slots():
    n = 40
    for name, ramp, inside, brackets in (("weapon_slot", "steel", R["slate"][1], False),
                                         ("weapon_slot_selected", "cyan", R["slate"][2], True)):
        L = Layer(n, n)
        L.paint(frame_shape(n, 6), OUTLINE)
        ring = shift(np.pad(frame_shape(n - 2, 5), ((0, 2), (0, 2))), 1, 1)[:n, :n]
        bevel(L, ring, ramp, 4, light=2, dark=-2, rim2=False, glow=brackets)
        inner = m_rect(n, n, 4, 4, 35, 35)
        L.paint(dilate(inner, True) & ~inner & ~(m_rect(n, n, 3, 3, 36, 3) & False), OUTLINE)
        L.paint(inner, inside)
        if brackets:
            for (x, y, dx, dy) in ((1, 1, 1, 1), (n - 2, 1, -1, 1), (1, n - 2, 1, -1), (n - 2, n - 2, -1, -1)):
                pass
            L.paint(m_rect(n, n, 4, 4, 35, 4), R["cyan"][2])
            for (x, y, dx, dy) in ((5, 5, 1, 1), (n - 6, 5, -1, 1), (5, n - 6, 1, -1), (n - 6, n - 6, -1, -1)):
                for k in range(5):
                    L.px(x + dx * k, y, R["ice"][7], True)
                    L.px(x, y + dy * k, R["ice"][7], True)
        else:
            L.paint(m_rect(n, n, 4, 4, 35, 4), R["slate"][2])
        outline(L)
        img = save(L, name, glow=brackets, preview_scale=6)
        check_palette(img, name)


# ---------------------------------------------------------------------------------------------------------------
# Episode cards (200 x 120)
# ---------------------------------------------------------------------------------------------------------------

CW, CH = 200, 120


def card_frame(L):
    m = m_rect(CW, CH, 0, 0, CW - 1, CH - 1) & ~m_rect(CW, CH, 1, 1, CW - 2, CH - 2)
    L.paint(m, OUTLINE)
    m2 = m_rect(CW, CH, 1, 1, CW - 2, CH - 2) & ~m_rect(CW, CH, 2, 2, CW - 3, CH - 3)
    L.paint(m2 & (np.arange(CH)[:, None] < 3), R["steel"][5])
    L.paint(m2 & (np.arange(CH)[:, None] >= 3), R["steel"][3])
    return L


def planet(L, cx, cy, r, ramp, base=3, rim=None, bands=None, seed=0, mask=None):
    """A lit sphere: light from the top left; optional horizontal bands (gas giant)."""
    yy, xx = np.mgrid[0:L.h, 0:L.w]
    d = np.hypot(xx - cx, yy - cy)
    disc = d <= r
    if mask is not None:
        disc &= mask
    # light: dot product with a direction from the top left
    nx, ny = (xx - cx) / max(r, 1), (yy - cy) / max(r, 1)
    lit = -(nx * 0.6 + ny * 0.8)
    rp = R[ramp]
    levels = np.clip(np.round(base + lit * 2.4), 1, len(rp) - 2).astype(int)
    if bands is not None:
        rng = np.random.default_rng(seed)
        ph = rng.random() * 6.28
        wob = np.sin((yy - cy) / r * bands + np.sin((xx - cx) / r * 2 + ph) * 0.8)
        levels = np.clip(levels + np.where(wob > 0.35, 1, np.where(wob < -0.45, -1, 0)), 1, len(rp) - 1)
    b = np.tile(bayer4(), (L.h // 4 + 1, L.w // 4 + 1))[:L.h, :L.w]
    frac = (base + lit * 2.4) - np.floor(base + lit * 2.4)
    levels = np.where((frac > b) & (bands is None), np.clip(levels, 1, len(rp) - 2), levels)
    for k in range(len(rp)):
        L.paint(disc & (levels == k), rp[k])
    if rim:
        ring = disc & ~(np.hypot(xx - cx + 1, yy - cy + 1) <= r - 1)
        L.paint(ring & (lit > -0.1), rim, True)
    return disc


def card_ep1():
    """The Academy ring station above a blue world."""
    L = Layer(CW, CH)
    full = m_rect(CW, CH, 0, 0, CW - 1, CH - 1)
    vgrad(L, full, 0, CH, [R["violet"][0], R["violet"][1], R["slate"][1], R["blue"][1], R["blue"][2]])
    stars(L, full & (np.arange(CH)[:, None] < 95), 90, 11, crosses=5)
    planet(L, 38, 168, 92, "blue", base=3, rim=R["cyan"][5])
    yy, xx = np.mgrid[0:CH, 0:CW]
    clouds = (np.sin(xx / 7.0 + np.sin(yy / 5.0) * 2) > 0.75) & (np.hypot(xx - 38, yy - 168) < 90)
    L.paint(clouds & (yy < 110), R["blue"][5])
    cx, cy = 122, 50
    outer_rx, outer_ry, inner_rx, inner_ry = 64, 24, 52, 16

    def ring_mask(dy):
        o = ((xx - cx) / outer_rx) ** 2 + ((yy - cy - dy) / outer_ry) ** 2 <= 1
        i = ((xx - cx) / inner_rx) ** 2 + ((yy - cy - dy) / inner_ry) ** 2 <= 1
        return o & ~i

    top = ring_mask(0)
    side = ring_mask(4) & ~top
    back = yy < cy
    # back half
    L.paint(side & back, R["steel"][2])
    L.paint(top & back, R["steel"][4])
    L.paint(edge(top, 0, -1) & back, R["steel"][6])
    # spokes and hub
    for ang in (0.35, 2.8, 3.5, 5.95):
        x1 = cx + np.cos(ang) * (inner_rx + 2)
        y1 = cy + np.sin(ang) * (inner_ry + 2)
        L.paint(m_line(CW, CH, [(cx, cy), (x1, y1)], width=2), R["steel"][3])
    hub = m_rect(CW, CH, cx - 7, cy - 22, cx + 7, cy + 18)
    hub_top = m_ellipse(CW, CH, (cx - 7, cy - 25, cx + 7, cy - 19))
    bevel(L, hub, "steel", 4, light=2, dark=-2, rim2=False)
    L.paint(hub_top, R["steel"][6])
    for y in range(cy - 16, cy + 16, 5):
        L.paint(m_rect(CW, CH, cx - 4, y, cx + 4, y), R["yellow"][6], True)
    L.paint(m_rect(CW, CH, cx - 1, cy - 31, cx + 1, cy - 25), R["steel"][5])
    sparkle(L, cx, cy - 33, 3, core=R["yellow"][7], arm=R["orange"][4])
    # front half
    front = ~back
    L.paint(side & front, R["steel"][2])
    L.paint(top & front, R["steel"][4])
    L.paint(edge(top, 0, -1) & front, R["steel"][6])
    L.paint(edge(top, 0, 1) & front, R["steel"][3])
    for k in range(0, 360, 9):
        a = np.radians(k)
        x = int(round(cx + np.cos(a) * (outer_rx - 0.5)))
        y = int(round(cy + 4 + np.sin(a) * (outer_ry + 1.5)))
        if np.sin(a) > -0.2:
            L.px(x, y, R["cyan"][6] if k % 27 else R["orange"][5], True)
    # a shuttle on approach
    sx, sy = 40, 34
    L.paint(m_poly(CW, CH, [(sx, sy), (sx + 9, sy + 2), (sx, sy + 4)]), R["steel"][6])
    L.paint(m_rect(CW, CH, sx - 3, sy + 1, sx - 1, sy + 3), R["orange"][5], True)
    L.px(sx - 4, sy + 2, R["yellow"][7], True)
    return card_frame(L)


def card_ep2():
    """The verdant moon Thessa: jungle under a ringed gas giant."""
    L = Layer(CW, CH)
    full = m_rect(CW, CH, 0, 0, CW - 1, CH - 1)
    yy, xx = np.mgrid[0:CH, 0:CW]
    vgrad(L, full, 0, 78, [R["teal"][1], R["teal"][2], R["teal"][3], R["green"][4], R["lime"][5], R["lime"][6]])
    stars(L, full & (yy < 30), 25, 21, colours=[R["teal"][5], R["teal"][6]])
    planet(L, 142, 34, 30, "tan", base=4, bands=9, seed=3, rim=R["yellow"][6])
    ring = (((xx - 142) / 52.0) ** 2 + ((yy - 38) / 7.0) ** 2 <= 1) & ~(((xx - 142) / 46.0) ** 2 +
                                                                          ((yy - 38) / 4.5) ** 2 <= 1)
    L.paint(ring & ((yy > 38) | (np.hypot(xx - 142, yy - 34) > 30)), R["tan"][6])
    rng = np.random.default_rng(22)

    def canopy(base_y, amp, step, col, seed):
        r2 = np.random.default_rng(seed)
        m = blank(CW, CH)
        x = -10
        while x < CW + 10:
            rr = r2.integers(step // 2, step)
            yc = base_y + r2.integers(-amp, amp + 1)
            m |= m_ellipse(CW, CH, (x - rr, yc - rr, x + rr, yc + rr))
            x += rr
        m |= yy >= base_y
        return m

    far = canopy(70, 4, 14, None, 23)
    L.paint(far, R["teal"][3])
    L.paint(edge(far, 0, -1), R["teal"][5])
    mist = (yy >= 74) & (yy < 82)
    b = np.tile(bayer4(), (CH // 4 + 1, CW // 4 + 1))[:CH, :CW]
    L.paint(mist & (b < 0.5), R["teal"][5])
    mid = canopy(84, 5, 18, None, 24)
    L.paint(mid, R["green"][2])
    L.paint(edge(mid, 0, -1), R["green"][4])
    L.paint(edge(mid, -1, 0) & ~edge(mid, 0, -1), R["green"][3])
    near = canopy(103, 4, 22, None, 25)
    L.paint(near, R["green"][1])
    L.paint(edge(near, 0, -1), R["green"][3])
    # a broad leaf and fronds in the foreground
    leaf = m_poly(CW, CH, [(0, 60), (14, 54), (34, 62), (46, 80), (30, 78), (12, 72), (0, 74)])
    L.paint(leaf, R["lime"][3])
    L.paint(edge(leaf, 0, -1), R["lime"][5])
    L.paint(m_line(CW, CH, [(0, 66), (40, 76)]), R["lime"][2])
    leaf2 = m_poly(CW, CH, [(199, 70), (182, 66), (164, 76), (158, 92), (176, 86), (199, 84)])
    L.paint(leaf2, R["green"][3])
    L.paint(edge(leaf2, 0, -1), R["green"][5])
    L.paint(m_line(CW, CH, [(199, 76), (162, 88)]), R["green"][2])
    for x0, length in ((7, 30), (15, 18), (24, 40), (33, 22), (178, 26), (188, 44), (195, 16)):  # hanging vines
        vine = m_line(CW, CH, [(x0, 1), (x0 + 2, length // 2), (x0, length)])
        L.paint(vine, R["green"][1])
        for y in range(6, length, 7):
            L.paint(m_rect(CW, CH, x0 + 1, y, x0 + 3, y + 1), R["green"][3])
        L.px(x0, length + 1, R["magenta"][5], True)
    ferns = blank(CW, CH)                                            # dark ferns along the bottom
    x = -4
    while x < CW + 4:
        h = int(rng.integers(8, 18))
        lean = int(rng.integers(-5, 6))
        ferns |= m_poly(CW, CH, [(x - 4, CH), (x + lean, CH - h), (x + 4, CH)])
        x += int(rng.integers(5, 10))
    L.paint(ferns, R["green"][0])
    L.paint(edge(ferns, 0, -1) & (yy < CH - 3), R["green"][2])
    for k in range(10):                                              # glowing flowers
        x = int(rng.integers(8, CW - 8))
        y = int(rng.integers(88, 114))
        col = R["magenta"][5] if k % 2 else R["lime"][6]
        L.paint(m_rect(CW, CH, x - 1, y, x + 1, y) | m_rect(CW, CH, x, y - 1, x, y + 1), col, True)
        L.px(x, y, R["yellow"][7], True)
    return card_frame(L)


def card_ep3():
    """The comet mines of Ysk: a crystal-studded comet with drill rigs and a long tail."""
    L = Layer(CW, CH)
    full = m_rect(CW, CH, 0, 0, CW - 1, CH - 1)
    yy, xx = np.mgrid[0:CH, 0:CW]
    vgrad(L, full, 0, CH, [R["slate"][0], R["violet"][1], R["slate"][1], R["violet"][1]])
    stars(L, full, 110, 31, crosses=6)
    # the tail: a widening wedge to the upper right, dithered from bright to dark
    b = np.tile(bayer4(), (CH // 4 + 1, CW // 4 + 1))[:CH, :CW]
    def tail(ax, ay, spread, length, curve, cols, strength, glow_levels):
        u = (xx - 70) * ax - (yy - 78) * ay
        v = (xx - 70) * ay + (yy - 78) * ax + curve * (u / 100.0) ** 2
        width = 5 + u * spread
        across = np.clip(1 - np.abs(v) / width, 0, 1)
        along = np.clip(1 - u / length, 0, 1)
        dens = np.where(u > 0, across ** 0.8 * along ** 0.9 * strength, 0)
        on = dens > b
        lev = np.clip(np.floor((1 - dens) * len(cols)), 0, len(cols) - 1)
        for k, c in enumerate(cols):
            L.paint(on & (lev == k), c, k < glow_levels)

    tail(0.85, 0.53, 0.36, 175, 10, [R["ice"][7], R["ice"][6], R["ice"][5], R["ice"][4], R["ice"][3]], 1.25, 2)
    tail(0.72, 0.69, 0.06, 150, 0, [R["cyan"][6], R["cyan"][5], R["blue"][4], R["blue"][3]], 0.9, 1)
    coma = np.hypot((xx - 62) / 1.25, (yy - 80) / 0.8)
    cd = np.clip(1 - (coma - 26) / 12, 0, 1) * (coma > 24)
    L.paint((cd > b) & (cd > 0.5), R["ice"][6], True)
    L.paint((cd > b) & (cd <= 0.5), R["ice"][4])
    # the nucleus
    rng = np.random.default_rng(33)
    pts = []
    for k in range(18):
        a = k / 18 * 2 * np.pi
        r = 28 + rng.uniform(-5, 5)
        pts.append((62 + np.cos(a) * r * 1.25, 80 + np.sin(a) * r * 0.8))
    rock = m_poly(CW, CH, pts)
    planet(L, 58, 74, 38, "ice", base=3, mask=rock)
    L.paint(edge(rock, 0, -1) | edge(rock, -1, 0), R["ice"][6])
    for k in range(9):                                               # craters
        x, y = int(rng.integers(36, 90)), int(rng.integers(66, 98))
        cr = m_ellipse(CW, CH, (x - 3, y - 2, x + 3, y + 2)) & rock
        L.paint(cr, R["ice"][2])
        L.paint(edge(cr, 0, 1) & cr, R["ice"][5])
    for (x, y, h) in ((40, 62, 12), (78, 60, 15), (96, 74, 10), (30, 86, 9), (66, 98, 8)):  # crystal clusters
        for dx, hh, ramp in ((-3, h - 4, "violet"), (0, h, "cyan"), (3, h - 2, "cyan")):
            shard = m_poly(CW, CH, [(x + dx - 2, y), (x + dx, y - hh), (x + dx + 2, y)])
            L.paint(shard, R[ramp][5], True)
            L.paint(edge(shard, -1, 0), R[ramp][7], True)
    # a drill rig with lamps
    L.paint(m_line(CW, CH, [(52, 52), (52, 36)], width=2), R["steel"][4])
    L.paint(m_line(CW, CH, [(48, 52), (52, 38), (56, 52)]), R["steel"][3])
    L.paint(m_rect(CW, CH, 49, 34, 55, 36), R["steel"][5])
    sparkle(L, 52, 32, 2, core=R["yellow"][7], arm=R["orange"][4])
    L.px(86, 58, R["orange"][5], True)
    L.px(24, 78, R["orange"][5], True)
    # a mining tug
    tx, ty = 150, 96
    tug = m_poly(CW, CH, [(tx, ty), (tx + 14, ty), (tx + 16, ty + 3), (tx + 14, ty + 6), (tx, ty + 6)])
    bevel(L, tug, "yellow", 4, light=2, dark=-2, rim2=False)
    L.paint(m_rect(CW, CH, tx + 10, ty + 2, tx + 12, ty + 3), R["cyan"][6], True)
    L.paint(m_rect(CW, CH, tx - 3, ty + 2, tx - 1, ty + 4), R["orange"][5], True)
    return card_frame(L)


def card_ep4():
    """The Gloam dreadnought in a red nebula."""
    L = Layer(CW, CH)
    full = m_rect(CW, CH, 0, 0, CW - 1, CH - 1)
    yy, xx = np.mgrid[0:CH, 0:CW]
    vgrad(L, full, 0, CH, [R["crimson"][0], R["crimson"][1], R["violet"][1], R["crimson"][1], R["crimson"][0]])
    b = np.tile(bayer4(), (CH // 4 + 1, CW // 4 + 1))[:CH, :CW]
    neb = np.sin(xx / 17.0 + np.sin(yy / 11.0) * 1.7) + np.sin(yy / 9.0 - xx / 31.0) * 0.8
    L.paint((neb > 1.0) & (b < 0.55), R["crimson"][2])
    L.paint((neb > 1.45) & (b < 0.4), R["magenta"][2])
    stars(L, full, 60, 41, colours=[R["rose"][5], R["rose"][6], R["ice"][7]], crosses=3)
    # the dreadnought: a long dark spearhead with stepped superstructure
    hull = m_poly(CW, CH, [(6, 62), (40, 48), (120, 40), (196, 52), (198, 58), (120, 78), (40, 80), (6, 70)])
    deck = m_poly(CW, CH, [(48, 48), (70, 34), (110, 30), (126, 40)])
    tower = m_poly(CW, CH, [(82, 32), (88, 20), (102, 18), (108, 30)])
    keel = m_poly(CW, CH, [(40, 80), (120, 78), (100, 92), (56, 92)])
    ship = hull | deck | tower | keel
    L.paint(ship, R["slate"][1])
    L.paint(hull & (yy > 60), R["slate"][0])
    L.paint(keel, R["slate"][0])
    L.paint(edge(ship, 0, -1), R["slate"][3])
    L.paint(edge(ship, -1, 0) & ~edge(ship, 0, -1), R["slate"][2])
    L.paint(m_line(CW, CH, [(40, 56), (196, 55)]), R["slate"][2])
    L.paint(m_line(CW, CH, [(30, 66), (150, 66)]), R["slate"][2])
    rng = np.random.default_rng(42)
    for k in range(40):                                              # rows of red lights
        x = int(rng.integers(20, 180))
        y = int(rng.choice([52, 58, 63, 70, 74]))
        if ship[y, x]:
            L.px(x, y, R["red"][5], True)
    for x in range(52, 120, 6):
        L.px(x, 44, R["red"][4], True)
    # the core: a glowing eye in the bridge
    eye = m_ellipse(CW, CH, (89, 22, 101, 28))
    L.paint(eye, R["red"][4], True)
    L.paint(m_ellipse(CW, CH, (93, 23, 97, 27)), R["orange"][5], True)
    L.px(95, 25, R["yellow"][7], True)
    # engines at the stern
    for y in (60, 66, 72):
        L.paint(m_rect(CW, CH, 2, y, 5, y + 2), R["magenta"][5], True)
        L.px(1, y + 1, R["magenta"][7], True)
    # escorts
    for (fx, fy) in ((150, 24), (166, 30), (30, 100), (172, 96)):
        f = m_poly(CW, CH, [(fx, fy), (fx + 7, fy + 2), (fx, fy + 4), (fx + 2, fy + 2)])
        L.paint(f, R["slate"][3])
        L.px(fx - 1, fy + 2, R["red"][5], True)
    return card_frame(L)


def make_cards():
    for i, fn in enumerate((card_ep1, card_ep2, card_ep3, card_ep4), 1):
        L = fn()
        img = save(L, f"ep{i}", glow=False, preview_scale=4)
        check_palette(img, f"ep{i}")


# ---------------------------------------------------------------------------------------------------------------

def contact():
    """All UI pictures on one sheet (2x) for a quick look."""
    files = ["hud", "bar_frame", "bar_fill", "bar_fill_low", "bar_fill_white", "logo", "subtitle", "panel", "cursor",
             "weapon_slot", "weapon_slot_selected", "ep1", "ep2", "ep3", "ep4"]
    imgs = [(f, Image.open(OUT / f"{f}.png")) for f in files]
    W = 900
    x = y = 0
    rowh = 0
    placed = []
    for f, im in imgs:
        w, h = im.width * 2, im.height * 2
        if x + w > W:
            x, y, rowh = 0, y + rowh + 8, 0
        placed.append((im, x, y))
        x += w + 8
        rowh = max(rowh, h)
    sheet = Image.new("RGBA", (W, y + rowh), (60, 64, 86, 255))
    for im, x, y in placed:
        sheet.alpha_composite(im.resize((im.width * 2, im.height * 2), Image.NEAREST), (x, y))
    sheet.convert("RGB").save(WORK / "contact.png")


def main():
    make_hud()
    make_bar()
    make_logo()
    make_panel()
    make_cursor()
    make_slots()
    make_cards()
    contact()
    print(f"ui -> {OUT}")


if __name__ == "__main__":
    main()
