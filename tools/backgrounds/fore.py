"""Foreground layers of Kip Kepler's backgrounds: assets/bg/<name>/fore.png and the `fore` line in its bg.txt.

The foreground is drawn IN FRONT of the gameplay (behind the HUD), so it stays sparse: near-black silhouettes in the
theme's darkest shades along the top TOP rows and the bottom H - BOT rows of the 400 px high layer -- girders,
pipes, cables (station, hull, foundry, citadel), leaves, vines and fern fronds (jungle), resin drips and tendrils
(hive), icicles and frozen beams (ice), stalactites and crystal tips (crystal) -- plus at most two thin vertical
elements (a pillar edge, a hanging chain or vine) per 640 px. The middle band stays empty; check() enforces it.

    python tools/backgrounds/make_bg.py --fore                # all 16 fore layers (+ previews)
    python tools/backgrounds/make_bg.py --fore jungle_a ice_b

Previews: work/bg/<name>_fore_preview.png (the background, a mock gameplay frame made of the theme's real tiles and
sprites, the fore layer over it; 640 x 400 and 640 x 360 views, the layer alone, a 2x crop) and
work/bg/_fore_overview.png.
"""
import math
import zlib

import numpy as np
from PIL import Image

from bgkit import H, PAL, ROOT, Draw, Layer, Noise, col, edge, grow, truss, wdx

W = 1280                 # every fore layer is 1280 x 400
TOP = 62                 # the top band: rows 0 .. TOP-1 (tips may reach MID[0])
BOT = 348                # the bottom band: rows BOT .. H-1
MID = (70, 340)          # nothing here but the thin verticals
MAX_VERT = 2             # thin verticals per 640 px
MAX_VERT_W = 18          # widest column run of a vertical in the middle band (px)

# body: the silhouette (darkest), body2: a second dark tone (far parts, facets, panels), rim: the 1 px edge lit from
# the top left, acc: a dark accent (hazard stripes, eggs, gems)
PALS = {
    "station_a": dict(body="outline", body2="slate1", rim="slate2", acc="yellow1"),
    "station_b": dict(body="outline", body2="slate1", rim="steel2", acc="yellow1"),
    "hull_a": dict(body="outline", body2="steel1", rim="steel2", acc="red1"),
    "hull_b": dict(body="outline", body2="slate1", rim="cyan1", acc="red1"),
    "jungle_a": dict(body="outline", body2="green1", rim="green2", acc="teal1"),
    "jungle_b": dict(body="outline", body2="purple1", rim="purple2", acc="magenta1"),
    "hive_a": dict(body="outline", body2="brown1", rim="brown2", acc="orange1"),
    "hive_b": dict(body="outline", body2="purple1", rim="violet2", acc="magenta1"),
    "ice_a": dict(body="outline", body2="ice1", rim="ice2", acc="blue1"),
    "ice_b": dict(body="outline", body2="ice1", rim="ice2", acc="blue1"),
    "crystal_a": dict(body="outline", body2="teal1", rim="teal2", acc="violet1"),
    "crystal_b": dict(body="outline", body2="violet1", rim="magenta1", acc="violet2"),
    "foundry_a": dict(body="outline", body2="brown1", rim="red1", acc="red1"),
    "foundry_b": dict(body="outline", body2="brown1", rim="crimson1", acc="red1"),
    "citadel_a": dict(body="outline", body2="purple1", rim="magenta1", acc="magenta1"),
    "citadel_b": dict(body="outline", body2="slate1", rim="violet2", acc="purple1"),
}

# parallax x, parallax y, y offset per theme (heavier things move a little faster)
SPECS = {"station": (1.3, 1.15, 0), "hull": (1.3, 1.15, 0), "jungle": (1.25, 1.12, 0), "hive": (1.25, 1.12, 0),
         "ice": (1.3, 1.15, 0), "crystal": (1.3, 1.15, 0), "foundry": (1.35, 1.18, 0), "citadel": (1.35, 1.18, 0)}


# --------------------------------------------------------------------------------------------------------- painting

def sil(L, m, P, tone="body", rim="rim", keep=False, rim_dirs=((0, -1), (-1, 0))):
    """Paints a silhouette mask in P[tone] with a 1 px rim (P[rim]) on its sides facing rim_dirs (top, left)."""
    m = np.asarray(m, bool)
    L.put(m, col(P[tone]), keep=keep)
    if rim:
        lit = np.zeros_like(m)
        for dx, dy in rim_dirs:
            lit |= edge(m, dx, dy)
        lit[0] = False
        lit[-1] = False
        L.put(lit, col(P[rim]), keep=keep)
    return m


def arc(dr, box, start, end, width=1):
    """An arc in a wrapping Draw (PIL angles: clockwise from 3 o'clock)."""
    x0, y0, x1, y1 = box
    for o in (-dr.w, 0, dr.w):
        dr.d.arc([x0 + o, y0, x1 + o, y1], start, end, fill=255, width=width)


def catenary(xa, ya, xb, yb, sag, step=2.0):
    n = max(2, int(abs(xb - xa) / step))
    t = np.linspace(0, 1, n)
    return list(zip(xa + (xb - xa) * t, ya + (yb - ya) * t + sag * 4 * t * (1 - t)))


def path(x, y, ang, length, bend=0.0, step=1.0, wobble=None):
    """Points of a curve starting at (x, y) heading ang degrees (0 right, 90 down), turning by bend degrees over its
    length; wobble(t) adds a sideways offset."""
    n = max(2, int(length / step))
    pts, a = [], math.radians(ang)
    px, py = float(x), float(y)
    for i in range(n + 1):
        t = i / n
        pts.append((px, py))
        aa = a + math.radians(bend) * t
        px += math.cos(aa) * length / n
        py += math.sin(aa) * length / n
    if wobble is not None:
        out = []
        for i, (px, py) in enumerate(pts):
            t = i / n
            j = min(n, i + 1)
            k = max(0, i - 1)
            dx, dy = pts[j][0] - pts[k][0], pts[j][1] - pts[k][1]
            ln = math.hypot(dx, dy) or 1
            w = wobble(t)
            out.append((px - dy / ln * w, py + dx / ln * w))
        pts = out
    return pts


def ribbon(pts, w0, w1, prof=None):
    """A polygon around a centre line, w0 wide at the start, w1 at the end (prof(t) multiplies the width)."""
    n = len(pts) - 1
    left, right = [], []
    for i, (px, py) in enumerate(pts):
        t = i / max(1, n)
        j, k = min(n, i + 1), max(0, i - 1)
        dx, dy = pts[j][0] - pts[k][0], pts[j][1] - pts[k][1]
        ln = math.hypot(dx, dy) or 1
        w = (w0 + (w1 - w0) * t) * (prof(t) if prof else 1.0) / 2
        left.append((px - dy / ln * w, py + dx / ln * w))
        right.append((px + dy / ln * w, py - dx / ln * w))
    return left + right[::-1]


def leaf(dr, x, y, ang, length, width, bend=0.0, notch=False):
    """A pointed leaf from its stalk at (x, y): widest at 40 %, a short stalk, a sharp tip."""
    pts = path(x, y, ang, length, bend, step=1.5)

    def prof(t):
        if t < 0.08:
            return 0.25
        return max(0.0, math.sin(math.pi * min(1.0, (t - 0.04) / 0.96) ** 0.75)) ** 0.9
    dr.poly(ribbon(pts, width, width, prof))
    if notch:     # a torn notch on one side
        k = int(len(pts) * 0.55)
        px, py = pts[k]
        dr.ellipse(px - 1.5, py - 1.5, px + 1.5, py + 1.5, fill=0)
    return pts


def frond(dr, x, y, ang, length, bend, leaflet, pairs, stem_w=2, side_ang=58, droop=0.0, leaf_w=2.6):
    """A fern frond: a curved stem with pairs of leaflets that shorten towards the tip."""
    pts = path(x, y, ang, length, bend, step=1.0)
    dr.poly(ribbon(pts, stem_w + 0.6, 0.8))
    n = len(pts) - 1
    for k in range(pairs):
        t = 0.12 + 0.84 * k / max(1, pairs - 1)
        i = int(t * n)
        px, py = pts[i]
        j = min(n, i + 1)
        a = math.degrees(math.atan2(pts[j][1] - py, pts[j][0] - px))
        ln = leaflet * (1 - t) ** 0.55 * (0.6 + 0.4 * min(1.0, t * 4))
        if ln < 2.5:
            continue
        for s in (-1, 1):
            leaf(dr, px, py, a + s * side_ang + droop * s, ln, leaf_w, bend=s * 10)
    return pts


def blob_band(rng, x0, x1, base, amp, cells=None, top=True, taper=0.25):
    """A per-column edge (y) of a band hanging from the top (or rising from the bottom) between x0 and x1: base +
    amp * noise, tapering to nothing at both ends. Returns (xs wrapped, y edge)."""
    n = int(x1 - x0)
    xs = np.arange(n, dtype=np.float32)
    cells = cells or max(2, n // 30)
    nz = Noise(max(8, n), cells, rng, 3, 0.5)(xs, np.full_like(xs, 17.0))
    t = xs / max(1, n - 1)
    env = np.clip(np.minimum(t, 1 - t) / taper, 0, 1) ** 0.6
    d = (base + amp * nz) * env
    return (np.arange(x0, x0 + n) % W).astype(np.int64), d


def band_mask(xs, d, top=True):
    m = np.zeros((H, W), bool)
    Y = np.arange(H)[:, None]
    if top:
        m[:, xs] = Y < d[None, :]
    else:
        m[:, xs] = Y >= (H - d)[None, :]
    return m


def chain_mask(x, y0, y1, big=True):
    """A hanging chain: rings seen face on (5 x 8 px, a 3 x 4 hole) and links seen edge on (2 px wide)
    alternating, x at its centre. Returns (mask, lit left side of the rings). big=False: 3 px wide rings."""
    m = np.zeros((H, W), bool)
    lit = np.zeros((H, W), bool)
    ring = ([".###.", "##.##", "#...#", "#...#", "#...#", "#...#", "##.##", ".###."] if big
            else [".#.", "#.#", "#.#", "#.#", ".#."])
    rw = len(ring[0])
    y = int(y0)
    k = 0
    while y < y1:
        if k % 2 == 0:
            for j, row in enumerate(ring):
                for i, ch in enumerate(row):
                    if ch == "#" and y + j < H:
                        xx = (x - rw // 2 + i) % W
                        m[y + j, xx] = True
                        if i <= 1 and ch == "#":
                            lit[y + j, xx] = True
            y += len(ring) - 1
        else:
            ln = 6 if big else 3
            for yy in range(y, min(H, y + ln)):
                m[yy, x % W] = True
                if big:
                    m[yy, (x - 1) % W] = True
                    lit[yy, (x - 1) % W] = True
            y += ln - 1
        k += 1
    return m, lit & m


def hook(dr, x, y, size=1.0):
    """A crane hook hanging at (x, y): a collar, a shank and a bowl opening to the right."""
    s = size
    dr.rect(x - 2 * s, y, x + 2 * s, y + 3 * s)
    dr.rect(x - 1, y + 3 * s, x, y + 9 * s)
    arc(dr, (x - 1 - 0 * s, y + 6 * s, x + 7 * s, y + 14 * s), -40, 185, width=max(2, int(2 * s)))
    dr.poly([(x + 6.5 * s, y + 7.5 * s), (x + 8 * s, y + 5.5 * s), (x + 8 * s, y + 9 * s)])


def chain_line(dr, pts, holes, w=2, gap=5):
    """A chain along a path (sagging chains): a 2 px line whose links show as holes every `gap` px."""
    dr.line(pts, width=w)
    acc = 0.0
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        acc += math.hypot(bx - ax, by - ay)
        if acc >= gap:
            acc = 0.0
            holes.append((int(round(bx)), int(round(by))))


def punch(L, pts):
    for x, y in pts:
        if 0 <= y < H:
            L.a[y, x % W] = False


def slots(rng, glen=(110, 300), gap=(50, 170)):
    """Alternating groups and gaps around the wrapped width: [(x0, x1), ...]."""
    x0 = int(rng.integers(0, 60))
    x = x0
    out = []
    while True:
        g = int(rng.integers(*glen))
        if x + g > x0 + W - gap[0]:
            break
        out.append((x, x + g))
        x += g + int(rng.integers(*gap))
    return out


# --------------------------------------------------------------------------------------------------------- hardware

def girder(L, P, x0, x1, y, h, tone="body", hangers=3, step=None, cw=3, bw=2):
    """A lattice girder hanging from the top edge on rods: two chords cw px, braces bw px, end plates, rim lit."""
    d = Draw(W)
    truss(d, x0, y + h / 2, x1, y + h / 2, h - cw, step=step or h, cw=cw, bw=bw)
    d.rect(x0 - 3, y - 3, x0 + 2, y + h + 2)
    d.rect(x1 - 2, y - 3, x1 + 3, y + h + 2)
    for k in range(hangers):
        xh = x0 + 10 + (x1 - x0 - 20) * k / max(1, hangers - 1)
        d.rect(xh - 1, 0, xh + 1, y)
        d.rect(xh - 5, y - 4, xh + 5, y)
    sil(L, d.mask(), P, tone, keep=True)
    # bolts on the end plates
    for xb in (x0 - 1, x1):
        for yb in (y, y + h - 1):
            L.put(_pt(xb, yb), col(P["body2"]))


def ibeam(L, P, x0, x1, y, h, holes=True, tone="body"):
    """A horizontal I-beam: dark, flange lines and rivets in the second tone, see-through lightening holes whose
    lower right insides catch the light."""
    d = Draw(W)
    d.rect(x0, y, x1, y + h)
    m = d.mask()
    sil(L, m, P, tone)
    f = Draw(W)
    f.rect(x0 + 1, y + 3, x1 - 1, y + 3)
    f.rect(x0 + 1, y + h - 3, x1 - 1, y + h - 3)
    L.put(f.mask() & m, col(P["body2"]))
    for xc in range(int(x0) + 5, int(x1) - 3, 9):
        for yy in (y + 1, y + h - 1):
            if 0 <= yy < H:
                L.put(_pt(xc, yy), col(P["body2"]))
    if holes and h >= 14:
        r = (h - 9) / 2
        hm = np.zeros((H, W), bool)
        for xc in range(int(x0) + 18, int(x1) - 14, 26):
            hd = Draw(W)
            hd.ellipse(xc - r * 1.4, y + h / 2 - r, xc + r * 1.4, y + h / 2 + r)
            hm |= hd.mask()
        hm &= m
        L.erase(hm)
        inner = (edge(~hm, -1, 0) | edge(~hm, 0, -1)) & grow(hm, 1) & m
        L.put(inner, col(P["rim"]))


def _pt(x, y):
    m = np.zeros((H, W), bool)
    m[int(y), int(x) % W] = True
    return m


def pipe_run(L, P, x0, x1, y, r, up=(True, True), flange=48, tone="body", supports=None):
    """A horizontal pipe from x0 to x1 at y (radius r), bending up into the top edge at its ends (or down into
    the bottom edge when supports='floor'), with flanges; shaded as a cylinder (lit top half)."""
    d = Draw(W)
    d.rect(x0, y - r, x1, y + r)
    for side, x in ((0, x0), (1, x1)):
        if not up[side]:
            continue
        xa = x - 2 * r if side == 0 else x
        if supports == "floor":
            d.rect(xa, y - r, xa + 2 * r, H)
        else:
            d.rect(xa, 0, xa + 2 * r, y + r)
    fl = Draw(W)
    for xf in range(int(x0) + flange // 2, int(x1) - 4, flange):
        fl.rect(xf, y - r - 1, xf + 2, y + r + 1)
    m = d.mask() | fl.mask()
    sil(L, m, P, tone)
    # the upper half of the horizontal run one tone up: a cylinder
    hd = Draw(W)
    hd.rect(x0 + 1, y - r + 2, x1 - 1, y - r + 2)
    L.put(hd.mask() & ~fl.mask() & m, col(P["body2"]))
    L.put(edge(fl.mask(), -1, 0) & m, col(P["rim"]))


def bracket_cables(L, P, rng, x0, x1, y, n=2, sag_to=None):
    """Loose cables sagging between hanger points along x0..x1 (lowest point at most sag_to)."""
    d = Draw(W)
    pts_x = sorted(rng.uniform(x0, x1, n + 1))
    lim = (sag_to or TOP) - y
    for k in range(n):
        xa, xb = pts_x[k], pts_x[k + 1]
        if xb - xa < 24:
            continue
        sag = min((xb - xa) * rng.uniform(0.14, 0.24), lim)
        d.line(catenary(xa, y, xb, y + rng.uniform(-3, 3), sag), width=int(rng.integers(2, 4)))
    sil(L, d.mask(), P, "body", rim=None, keep=True)


def hanging_lamp(L, P, x, y):
    """A dark work lamp on a rod: a shade wider at the bottom, the lens rim one tone up (it does not glow)."""
    d = Draw(W)
    d.rect(x - 1, 0, x, y)
    d.rect(x - 3, y - 3, x + 2, y)
    d.poly([(x - 6, y), (x + 5, y), (x + 13, y + 11), (x - 14, y + 11)])
    sil(L, d.mask(), P, "body", keep=True)
    d2 = Draw(W)
    d2.rect(x - 11, y + 11, x + 10, y + 12)
    L.put(d2.mask(), col(P["body2"]))


def duct(L, P, x0, x1, h):
    """A square air duct along the ceiling with a louvred grille and seams."""
    d = Draw(W)
    d.rect(x0, 0, x1, h)
    d.rect(x0 - 3, h - 4, x1 + 3, h)
    for xx in range(int(x0) + 40, int(x1) - 10, 46):
        d.rect(xx - 2, 0, xx + 2, h + 2)
    m = d.mask()
    sil(L, m, P, "body")
    g = Draw(W)
    gx0 = int(x0 + (x1 - x0) * rng_frac(x0))
    for xx in range(gx0, min(int(x1) - 8, gx0 + 40), 4):
        g.rect(xx, 6, xx + 1, h - 8)
    L.put(g.mask(), col(P["body2"]))
    b = Draw(W)
    b.rect(x0 + 2, h - 7, x1 - 2, h - 6)
    L.put(b.mask() & m, col(P["body2"]))


def rng_frac(x):
    return 0.2 + 0.5 * ((int(x) * 2654435761) % 1000) / 1000.0


def pillar(L, P, x, w=8, top_gusset=True, bot_gusset=True):
    """A thin vertical I-beam over the whole height: flanges, a web in the second tone, rivets, gusset plates in the
    bands only."""
    d = Draw(W)
    d.rect(x, 0, x + w - 1, H)
    if top_gusset:
        d.poly([(x + w - 1, 0), (x + w + 16, 0), (x + w - 1, 18)])
        d.poly([(x, 0), (x - 10, 0), (x, 10)])
        d.rect(x - 2, 30, x + w + 1, 34)
    if bot_gusset:
        d.poly([(x + w - 1, H), (x + w + 18, H), (x + w - 1, H - 20)])
        d.poly([(x, H), (x - 12, H), (x, H - 12)])
        d.rect(x - 2, H - 38, x + w + 1, H - 34)
    sil(L, d.mask(), P, "body")
    web = Draw(W)
    web.rect(x + 2, 0, x + 2, H)
    web.rect(x + w - 3, 0, x + w - 3, H)
    L.put(web.mask() & d.mask(), col(P["body2"]))
    for yy in range(12, H - 8, 26):
        L.put(_pt(x + w // 2 - 1, yy), col(P["rim"]))
    lm = Draw(W)
    lm.rect(x, 0, x, H)
    L.put(lm.mask(), col(P["rim"]))


def railing(L, P, x0, x1, ytop=354, post=34):
    """A walkway railing in front: posts, a top and a middle rail, a kick plate with hazard stripes."""
    d = Draw(W)
    d.rect(x0, ytop, x1, ytop + 2)
    d.rect(x0, ytop + 20, x1, ytop + 21)
    for xp in range(int(x0), int(x1) + 1, post):
        d.rect(xp, ytop, xp + 2, H)
    d.rect(x0 - 3, H - 13, x1 + 3, H)
    m = d.mask()
    sil(L, m, P, "body", keep=True)
    kp = Draw(W)
    kp.rect(x0, H - 10, x1, H - 3)
    k = kp.mask() & ((((L.X + L.Y) // 6).astype(np.int64) % 2) == 0)
    L.put(k, col(P["acc"]))


def crate(L, P, x, w, h, y_bot=H, brace=True):
    """A cargo crate: a frame in the second tone, a diagonal brace."""
    d = Draw(W)
    d.rect(x, y_bot - h, x + w, y_bot)
    sil(L, d.mask(), P, "body")
    p = Draw(W)
    p.rect(x + 3, y_bot - h + 3, x + w - 3, y_bot - h + 3)
    p.rect(x + 3, y_bot - h + 3, x + 3, y_bot)
    p.rect(x + w - 3, y_bot - h + 3, x + w - 3, y_bot)
    if brace:
        p.line([(x + 4, y_bot - 1), (x + w - 4, y_bot - h + 4)], width=2)
    L.put(p.mask(), col(P["body2"]), keep=True)


def console(L, P, x, w, h):
    """A slanted control console with a dark screen line."""
    d = Draw(W)
    d.poly([(x, H), (x, H - h * 0.55), (x + w * 0.35, H - h), (x + w, H - h), (x + w, H)])
    sil(L, d.mask(), P, "body")
    s = Draw(W)
    s.poly([(x + 4, H - h * 0.55 + 2), (x + w * 0.35 + 2, H - h + 4), (x + w * 0.35 + 6, H - h + 4),
            (x + 8, H - h * 0.55 + 6)])
    s.rect(x + w * 0.45, H - h + 5, x + w - 4, H - h + 6)
    L.put(s.mask(), col(P["body2"]), keep=True)


def gear(L, P, cx, cy, r, teeth=None, tone="body"):
    teeth = teeth or max(8, int(r / 2.6))
    pts = []
    for k in range(teeth * 4):
        a = 2 * math.pi * k / (teeth * 4)
        rr = r if (k % 4) in (1, 2) else r - 4
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d = Draw(W)
    d.poly(pts)
    m = d.mask()
    sil(L, m, P, tone)
    inner = Draw(W)
    arc(inner, (cx - r + 7, cy - r + 7, cx + r - 7, cy + r - 7), 0, 360, 1)
    arc(inner, (cx - r * 0.3, cy - r * 0.3, cx + r * 0.3, cy + r * 0.3), 0, 360, 1)
    L.put(inner.mask() & m, col(P["body2"]))
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        hx, hy = cx + r * 0.55 * math.cos(a), cy + r * 0.55 * math.sin(a)
        h = Draw(W)
        h.ellipse(hx - r * 0.13, hy - r * 0.13, hx + r * 0.13, hy + r * 0.13)
        L.erase(h.mask() & m)


# --------------------------------------------------------------------------------------------------------- themes

def fore_station(L, rng, P, v):
    """Station interior: lattice girders, pipe bundles and ducts under the ceiling, sagging cables, a work lamp; a
    railing, crates and consoles along the floor; one I-beam pillar and one hanging chain with a hook."""
    groups = slots(rng, (160, 340), (90, 200))
    for k, (x0, x1) in enumerate(groups):
        kind = (k + (0 if v == "a" else 1)) % 3
        if kind == 0:
            y = int(rng.integers(6, 12))
            h = int(rng.integers(18, 24))
            bracket_cables(L, P, rng, x0 + 10, x1 - 10, y + h - 2, 2, sag_to=TOP - 2)
            girder(L, P, x0, x1, y, h)
        elif kind == 1:
            y = int(rng.integers(12, 16))
            pipe_run(L, P, x0 + 16, x1 - 30, y + 20, 4, up=(True, True), flange=40)
            pipe_run(L, P, x0, x1, y, 7, up=(True, rng.random() < 0.6), flange=56)
            hanging_lamp(L, P, int(x0 + (x1 - x0) * rng.uniform(0.35, 0.65)), int(y + 26))
        else:
            bracket_cables(L, P, rng, x0, x1, 20, 2, sag_to=TOP - 4)
            duct(L, P, x0, x1, int(rng.integers(22, 30)))
    bgroups = slots(rng, (110, 280), (100, 220))
    for k, (x0, x1) in enumerate(bgroups):
        kind = (k + (1 if v == "a" else 0)) % 3
        if kind == 0:
            railing(L, P, x0, x1)
        elif kind == 1:
            x = x0
            while x < x1 - 36:
                w = int(rng.integers(36, 56))
                h = int(rng.integers(30, 46))
                crate(L, P, x, w, h)
                if rng.random() < 0.45 and h < 38:
                    crate(L, P, x + 6, w - 14, int(rng.integers(12, 18)), y_bot=H - h)
                x += w + int(rng.integers(2, 24))
        else:
            console(L, P, x0, min(78, x1 - x0), int(rng.integers(40, 50)))
            if x1 - x0 > 130:
                pipe_run(L, P, x0 + 90, x1, 380, 5, up=(True, True), supports="floor", flange=44)
    # verticals: an I-beam pillar and a hanging chain with a hook
    px = int(rng.integers(100, 500))
    pillar(L, P, px, 10)
    cx = (px + 640 + int(rng.integers(-80, 80))) % W
    m, lit = chain_mask(cx, 0, int(rng.integers(150, 210)))
    sil(L, m, P, "body", rim=None, keep=True)
    L.put(lit, col(P["rim"]), keep=True)
    d = Draw(W)
    ye = int(np.nonzero(m.any(1))[0].max())
    hook(d, cx, ye + 1, 1.2)
    sil(L, d.mask(), P, "body", keep=True)


def fore_hull(L, rng, P, v):
    """Outside on the hull: overhead plating with antenna arrays, comm dishes and tether cables; hull plates, EVA
    rails, a sensor dome and short masts along the bottom; a thin lattice mast and a dangling tether."""
    groups = slots(rng, (170, 340), (90, 210))
    for k, (x0, x1) in enumerate(groups):
        d = Draw(W)
        x = x0
        while x < x1:
            w = int(rng.integers(34, 80))
            hh = int(rng.integers(10, 26))
            d.poly([(x, 0), (x, hh - 4), (x + 4, hh), (min(x1, x + w), hh), (min(x1, x + w) + 2, 0)])
            x += w
        m = d.mask()
        bracket_cables(L, P, rng, x0 + 4, x1 - 4, int(rng.integers(16, 24)), 2, sag_to=TOP - 2)
        sil(L, m, P, "body")
        seam = Draw(W)
        x = x0
        while x < x1:
            x += int(rng.integers(20, 40))
            seam.rect(x, 0, x, 8)
        L.put(seam.mask() & m, col(P["body2"]))
        for xr in range(int(x0) + 3, int(x1) - 2, 7):
            L.put(_pt(xr, 3), col(P["body2"]))
        if (k + (v == "b")) % 2 == 0:   # an antenna array
            ax = int(x0 + (x1 - x0) * rng.uniform(0.3, 0.7))
            a = Draw(W)
            ln = int(rng.integers(40, 52))
            a.rect(ax - 1, 8, ax + 1, 8 + ln)
            for j, yy in enumerate(range(20, 6 + ln, 8)):
                half = 14 - j * 2.2
                a.rect(ax - half, yy, ax + 1 + half, yy + 1)
                a.rect(ax - half, yy - 2, ax - half + 1, yy + 3)
            a.ellipse(ax - 3, 8 + ln - 2, ax + 3, 8 + ln + 4)
            sil(L, a.mask(), P, "body", keep=True)
        else:                            # a comm dish hanging under the plates
            dx = int(x0 + (x1 - x0) * rng.uniform(0.3, 0.7))
            a = Draw(W)
            a.rect(dx - 2, 10, dx + 2, 26)
            for o in (-W, 0, W):
                a.d.chord([dx - 26 + o, 16, dx + 26 + o, 60], 0, 180, fill=255)
            a.rect(dx - 1, 38, dx + 1, 58)
            a.ellipse(dx - 3, 56, dx + 3, 62)
            dm = a.mask()
            sil(L, dm, P, "body", keep=True)
            rib = Draw(W)
            arc(rib, (dx - 20, 22, dx + 20, 52), 20, 160, 1)
            L.put(rib.mask() & dm, col(P["body2"]))
    bgroups = slots(rng, (130, 320), (90, 210))
    for k, (x0, x1) in enumerate(bgroups):
        d = Draw(W)
        x = x0
        while x < x1:
            w = int(rng.integers(40, 90))
            t1 = H - int(rng.integers(20, 34))
            d.poly([(x, H), (x, t1 + 6), (x + 6, t1), (min(x1, x + w), t1 + int(rng.integers(-4, 6))),
                    (min(x1, x + w), H)])
            x += w
        m = d.mask()
        sil(L, m, P, "body")
        for xr in range(int(x0) + 4, int(x1) - 2, 8):
            c_ = np.nonzero(m[:, xr % W])[0]
            if len(c_):
                L.put(_pt(xr, c_.min() + 4), col(P["body2"]))
        kind = (k + (v == "a")) % 3
        if kind == 0:     # EVA hand rail
            r = Draw(W)
            top = H - 52
            r.rect(x0 + 10, top, x1 - 10, top + 2)
            for xp in range(int(x0) + 10, int(x1) - 9, 30):
                r.rect(xp, top, xp + 2, H - 20)
            sil(L, r.mask(), P, "body", keep=True)
        elif kind == 1:   # sensor dome
            cx = int(x0 + (x1 - x0) * rng.uniform(0.3, 0.7))
            r = Draw(W)
            for o in (-W, 0, W):
                r.d.chord([cx - 26 + o, H - 56, cx + 26 + o, H - 8], 180, 360, fill=255)
            r.rect(cx - 30, H - 34, cx + 30, H - 26)
            dm = r.mask()
            sil(L, dm, P, "body", keep=True)
            ln = Draw(W)
            arc(ln, (cx - 18, H - 50, cx + 18, H - 14), 200, 340, 1)
            L.put(ln.mask() & dm, col(P["body2"]))
        else:             # short antenna masts
            for xm in rng.uniform(x0 + 12, x1 - 12, 2):
                r = Draw(W)
                hh = int(rng.integers(28, 38))
                yb = H - 14
                r.rect(xm - 1, yb - hh, xm + 1, yb)
                r.rect(xm - 7, yb - hh + 6, xm + 8, yb - hh + 7)
                r.rect(xm - 4, yb - hh + 15, xm + 5, yb - hh + 16)
                sil(L, r.mask(), P, "body", keep=True)
    # verticals: a thin lattice mast rising from the bottom, a dangling tether
    mx = int(rng.integers(80, 560))
    d = Draw(W)
    truss(d, mx, H, mx, 110, 7, step=9, cw=2, bw=1)
    d.rect(mx - 8, 106, mx + 8, 110)
    d.rect(mx - 1, 92, mx, 106)
    sil(L, d.mask(), P, "body", keep=True)
    tx = (mx + 640 + int(rng.integers(-60, 60))) % W
    d = Draw(W)
    pts = path(tx, 0, 92, int(rng.integers(150, 210)), bend=-8, step=2,
               wobble=lambda t: 3 * math.sin(t * 7.0) * t)
    d.line(pts, width=2)
    ex, ey = pts[-1]
    d.rect(ex - 3, ey, ex + 3, ey + 5)
    d.rect(ex - 1, ey + 6, ex + 1, ey + 9)
    sil(L, d.mask(), P, "body", rim=None, keep=True)


def fore_jungle(L, rng, P, v):
    """Overhanging canopy: clusters of broad drooping leaves and fronds from the top edge, short vines; fern fronds,
    broad leaves and grass rising from the bottom; one or two long vines with leaves."""
    groups = slots(rng, (130, 290), (70, 170))
    for (x0, x1) in groups:
        xs, d = blob_band(rng, x0, x1, 14, 14, taper=0.3)
        m = band_mask(xs, d)
        for _ in range(int(rng.integers(1, 3))):    # drooping fronds behind the mass
            fx = rng.uniform(x0 + 20, x1 - 20)
            dr = Draw(W)
            s_ = 1 if rng.random() < 0.5 else -1
            frond(dr, fx, 4, 90 - s_ * 66, rng.uniform(44, 56), s_ * 70, 13, 10, droop=12, leaf_w=3.2)
            sil(L, dr.mask(), P, "body2", keep=True)
        sil(L, m, P, "body", rim=None)
        n = int((x1 - x0) / 12)
        for k in range(n):
            lx = x0 + (x1 - x0) * (k + rng.uniform(0, 1)) / n
            base = d[int(np.clip(lx - x0, 0, len(d) - 1))] - 3
            ang = 90 + rng.uniform(-55, 55)
            env = 0.55 + 0.45 * math.sin(math.pi * (lx - x0) / (x1 - x0))
            ln = min(rng.uniform(26, 54) * env, TOP + 4 - base)
            tone = "body2" if k % 4 == 0 else "body"
            dr = Draw(W)
            leaf(dr, lx, base, ang, ln, rng.uniform(9, 15), bend=rng.uniform(-35, 35), notch=rng.random() < 0.3)
            lm = sil(L, dr.mask(), P, tone, keep=True)
            if tone == "body" and ln > 26:   # a midrib in the second tone
                rib = Draw(W)
                rib.line(path(lx, base, ang, ln * 0.7, rng.uniform(-10, 10)), width=1)
                L.put(rib.mask() & lm & ~edge(lm, 0, -1), col(P["body2"]), keep=True)
        for _ in range(int(rng.integers(1, 4))):
            vx = rng.uniform(x0 + 10, x1 - 10)
            _vine(L, P, rng, vx, 8, rng.uniform(24, 44))
    bgroups = slots(rng, (110, 260), (80, 190))
    for (x0, x1) in bgroups:
        xs, d = blob_band(rng, x0, x1, 10, 8, taper=0.3)
        nf = int((x1 - x0) / 36) + 1
        for k in range(nf):
            fx = x0 + (x1 - x0) * (k + rng.uniform(0.2, 0.8)) / nf
            for s_ in (-1, 1):
                dr = Draw(W)
                ang = -90 + s_ * rng.uniform(18, 50)
                frond(dr, fx, H + 2, ang, rng.uniform(44, 56), s_ * rng.uniform(55, 85), 14, 10, droop=-8,
                      leaf_w=3.2)
                sil(L, dr.mask(), P, "body2" if s_ < 0 else "body", keep=True)
        sil(L, band_mask(xs, d, top=False), P, "body", rim=None)
        for _ in range(int((x1 - x0) / 26)):
            gx = rng.uniform(x0, x1)
            dr = Draw(W)
            for _b in range(int(rng.integers(3, 7))):
                a = -90 + rng.uniform(-38, 38)
                pts = path(gx + rng.uniform(-5, 5), H, a, rng.uniform(16, 36), bend=rng.uniform(-45, 45))
                dr.poly(ribbon(pts, 3.6, 0.5))
            sil(L, dr.mask(), P, "body", rim=None, keep=True)
        for _ in range(int(rng.integers(1, 3))):
            lx = rng.uniform(x0 + 20, x1 - 20)
            dr = Draw(W)
            leaf(dr, lx, H, -90 + rng.uniform(-35, 35), rng.uniform(36, 48), rng.uniform(14, 20),
                 bend=rng.uniform(-45, 45))
            sil(L, dr.mask(), P, "body", keep=True)
    vx = rng.uniform(60, 560)
    _vine(L, P, rng, vx, 0, rng.uniform(170, 240), long_=True)
    if rng.random() < 0.6:
        _vine(L, P, rng, (vx + 640 + rng.uniform(-100, 100)) % W, 0, rng.uniform(120, 180), long_=True)


def _vine(L, P, rng, x, y, length, long_=False):
    dr = Draw(W)
    ph = rng.uniform(0, 6.28)
    amp = 2.5 if long_ else 2.0
    pts = path(x, y, 90, length, 0, step=1.5, wobble=lambda t: amp * math.sin(t * length / 18 + ph))
    dr.line(pts, width=2)
    lv = Draw(W)
    n = len(pts) - 1
    k = 0
    yy = 10.0
    while yy < length - 4:
        i = int(yy / length * n)
        px, py = pts[i]
        s_ = 1 if k % 2 == 0 else -1
        leaf(lv, px, py, 90 - s_ * 55, rng.uniform(5, 7) if long_ else rng.uniform(6, 9), rng.uniform(4, 5.5),
             bend=s_ * 20)
        k += 1
        yy += rng.uniform(9, 14)
    ex, ey = pts[-1]
    leaf(lv, ex, ey - 1, 90 + rng.uniform(-20, 20), 9, 5)
    sil(L, dr.mask(), P, "body", rim=None, keep=True)
    sil(L, lv.mask(), P, "body", keep=True)


def fore_hive(L, rng, P, v):
    """Resin hanging from the top edge in sagging masses with fat drips, strands and tendrils; resin mounds with
    egg clusters and spines along the bottom; one long dripping strand."""
    groups = slots(rng, (130, 300), (70, 180))
    for (x0, x1) in groups:
        xs, d = blob_band(rng, x0, x1, 18, 18, taper=0.35)
        m = band_mask(xs, d)
        drips = []
        for _ in range(int((x1 - x0) / 13)):
            dx = rng.uniform(x0 + 8, x1 - 8)
            base = d[int(np.clip(dx - x0, 0, len(d) - 1))] - 3
            if base < 6:
                continue
            ln = (TOP + 2 - base) * rng.uniform(0.3, 1.0) ** 0.7
            w0 = rng.uniform(6, 12)
            dr = Draw(W)
            pts = path(dx, base, 90, ln, rng.uniform(-8, 8), step=1.0)
            dr.poly(ribbon(pts, w0, 1.6, lambda t: 1 - 0.6 * t ** 0.7))
            ex, ey = pts[-1]
            rb = rng.uniform(2.2, 3.8)
            dr.ellipse(ex - rb, ey - rb * 0.6, ex + rb, ey + rb * 1.4)
            dm = sil(L, dr.mask(), P, "body", keep=True)
            g = Draw(W)     # a wet glint down the lit side
            g.line([(dx - w0 * 0.2, base + 3), (dx - 0.5, base + ln * 0.45)], width=1)
            L.put(g.mask() & dm & ~edge(dm, -1, 0), col(P["body2"]), keep=True)
            drips.append((dx, base + ln * 0.4))
        drips.sort()
        sd = Draw(W)
        for (xa, ya), (xb, yb) in zip(drips[:-1], drips[1:]):
            if 14 < xb - xa < 70 and rng.random() < 0.55:
                sd.line(catenary(xa, ya, xb, yb, rng.uniform(5, 12)), width=1)
        sil(L, sd.mask(), P, "body", rim=None, keep=True)
        sil(L, m, P, "body", rim=None)
        vn = Noise(W, 40, rng, 2)(L.X, L.Y * 2.0)
        L.put(m & (np.abs(vn - 0.5) < 0.025) & (L.Y > 2) & ~edge(m, 0, 1), col(P["body2"]), keep=True)
        for _ in range(int(rng.integers(1, 3))):
            tx = rng.uniform(x0 + 10, x1 - 10)
            base = d[int(np.clip(tx - x0, 0, len(d) - 1))] - 3
            _tendril(L, P, rng, tx, base, rng.uniform(30, max(31, TOP + 4 - base)))
    bgroups = slots(rng, (110, 270), (80, 190))
    for (x0, x1) in bgroups:
        xs, d = blob_band(rng, x0, x1, 26, 18, taper=0.35)
        m = band_mask(xs, d, top=False)
        for _ in range(int((x1 - x0) / 22)):
            sx = rng.uniform(x0 + 6, x1 - 6)
            top = H - d[int(np.clip(sx - x0, 0, len(d) - 1))]
            dr = Draw(W)
            pts = path(sx, top + 5, -90 + rng.uniform(-35, 35), rng.uniform(14, 30), rng.uniform(-40, 40))
            dr.poly(ribbon(pts, 5, 0.6))
            sil(L, dr.mask(), P, "body", keep=True)
        sil(L, m, P, "body")
        for _ in range(int((x1 - x0) / 40) + 1):
            ex = rng.uniform(x0 + 16, x1 - 16)
            top = H - d[int(np.clip(ex - x0, 0, len(d) - 1))]
            for j in range(int(rng.integers(2, 4))):
                rx, ry = rng.uniform(6, 9), rng.uniform(8, 12)
                cx, cy = ex + (j - 1) * rx * 1.6, top + ry * 0.2 + abs(j - 1) * 4
                dr = Draw(W)
                dr.ellipse(cx - rx, cy - ry, cx + rx, cy + ry)
                em = dr.mask()
                sil(L, em, P, "body")
                hl = Draw(W)
                hl.ellipse(cx - rx * 0.7, cy - ry * 0.8, cx - rx * 0.05, cy - ry * 0.05)
                L.put(hl.mask() & em & ~edge(em, 0, -1) & ~edge(em, -1, 0), col(P["body2"]))
                sp = Draw(W)
                sp.rect(cx - rx * 0.45, cy - ry * 0.55, cx - rx * 0.45 + 1, cy - ry * 0.55 + 2)
                L.put(sp.mask() & em, col(P["acc"]))
    sx = rng.uniform(60, 560)
    _tendril(L, P, rng, sx, 0, rng.uniform(170, 230), long_=True)


def _tendril(L, P, rng, x, y, length, long_=False):
    dr = Draw(W)
    ph = rng.uniform(0, 6.28)
    amp = rng.uniform(1.5, 2.5) if long_ else rng.uniform(3, 6)
    pts = path(x, y, 90, length, rng.uniform(-10, 10) if long_ else rng.uniform(-20, 20), step=1.0,
               wobble=lambda t: amp * math.sin(t * (length / 16) + ph) * (0.4 + 0.6 * t))
    dr.poly(ribbon(pts, 6.0 if long_ else 4.0, 1.6))
    ex, ey = pts[-1]
    rb = 3.6 if long_ else rng.uniform(2.2, 3.2)
    dr.ellipse(ex - rb, ey - rb * 0.7, ex + rb, ey + rb * 1.5)
    if long_:
        for t in (0.42, 0.68):
            px, py = pts[int(t * (len(pts) - 1))]
            dr.ellipse(px - 3, py - 4.5, px + 3, py + 4.5)
    sil(L, dr.mask(), P, "body", keep=True)


def _icicle(dr, x, y, length, w, lean=0.0):
    kink = length * 0.55
    dr.poly([(x - w / 2, y - 1), (x + w / 2, y - 1), (x + w * 0.22 + lean * 0.5, y + kink),
             (x + lean, y + length), (x - w * 0.18 + lean * 0.4, y + kink)])


def _facet(L, P, m, xs_centre):
    """The lit half of a crystal / icicle in the second tone: a facet."""
    L.put(m & (L.X < xs_centre) & ~edge(m, -1, 0) & ~edge(m, 0, -1), col(P["body2"]))


def fore_ice(L, rng, P, v):
    """A ragged ice ledge with icicle clusters, frozen beams with icicles; snow drifts and ice shards at the bottom;
    a frozen chain (ice_a) or a long icicle (ice_b)."""
    groups = slots(rng, (130, 300), (70, 180))
    for k, (x0, x1) in enumerate(groups):
        beam = (k + (v == "b")) % 3 == 1
        if beam:
            y = int(rng.integers(12, 20))
            hb = 14
            for xh in (x0 + 12, x1 - 12):
                dr = Draw(W)
                dr.rect(xh - 1, 0, xh + 1, y)
                sil(L, dr.mask(), P, "body", keep=True)
            ibeam(L, P, x0, x1, y, hb, holes=True)
            crust = Draw(W)
            for cx in np.arange(x0 - 2, x1 + 2, 4):
                r = rng.uniform(2.5, 5)
                crust.ellipse(cx - r, y - r * 0.9, cx + r, y + 2)
            sil(L, crust.mask() & (L.Y < y + 2), P, "body2")
            base, ends = y + hb, (x0 + 3, x1 - 3)
            n = int((x1 - x0) / 7)
            for j in range(n):
                ix = rng.uniform(*ends)
                dr = Draw(W)
                ln = rng.uniform(6, min(44, TOP + 6 - base))
                w = 3 + ln * rng.uniform(0.1, 0.16)
                _icicle(dr, ix, base, ln, w, rng.uniform(-1.5, 1.5))
                m = sil(L, dr.mask(), P, "body", keep=True)
                _facet(L, P, m, ix)
        else:
            xs, d = blob_band(rng, x0, x1, 10, 10, taper=0.25)
            m = band_mask(xs, d)
            sil(L, m, P, "body", rim=None)
            n = int((x1 - x0) / 6)
            for j in rng.permutation(n):
                ix = x0 + (x1 - x0) * (j + rng.uniform(0.1, 0.9)) / n
                base = d[int(np.clip(ix - x0, 0, len(d) - 1))] - 1
                env = math.sin(math.pi * (ix - x0) / (x1 - x0)) ** 0.6
                ln = min(rng.uniform(8, 56) * env + 4, TOP + 6 - base)
                w = 3 + ln * rng.uniform(0.12, 0.2)
                dr = Draw(W)
                _icicle(dr, ix, base, ln, w, rng.uniform(-2, 2))
                m2 = sil(L, dr.mask(), P, "body", keep=True)
                _facet(L, P, m2, ix)
    bgroups = slots(rng, (110, 270), (80, 190))
    for k, (x0, x1) in enumerate(bgroups):
        xs, d = blob_band(rng, x0, x1, 18, 12, taper=0.4, cells=max(2, int((x1 - x0) / 60)))
        m = band_mask(xs, d, top=False)
        n = int((x1 - x0) / 20) + 1
        for j in range(n):
            sx = x0 + (x1 - x0) * (j + rng.uniform(0.2, 0.8)) / n
            top = H - d[int(np.clip(sx - x0, 0, len(d) - 1))]
            for s_ in range(int(rng.integers(1, 4))):
                ang = rng.uniform(-30, 30)
                ln = rng.uniform(16, 46) * (1 - 0.25 * s_)
                w = rng.uniform(6, 11)
                a = math.radians(ang)
                bx, by = sx + s_ * 6 - 6, top + 8
                tip = (bx + math.sin(a) * ln, by - math.cos(a) * ln)
                px, py = math.cos(a) * w / 2, math.sin(a) * w / 2
                dr = Draw(W)
                dr.poly([(bx - px, by - py), (bx + px, by + py),
                         (bx + px * 0.9 + math.sin(a) * ln * 0.7, by + py * 0.9 - math.cos(a) * ln * 0.7), tip,
                         (bx - px * 0.9 + math.sin(a) * ln * 0.75, by - py * 0.9 - math.cos(a) * ln * 0.75)])
                m2 = sil(L, dr.mask(), P, "body", keep=True)
                _facet(L, P, m2, bx + math.sin(a) * ln * 0.4)
        sil(L, m, P, "body")
        sn = Draw(W)
        for xx in range(int(x0) + 6, int(x1) - 6, 3):
            c_ = np.nonzero(m[:, xx % W])[0]
            if len(c_) and rng.random() < 0.5:
                sn.rect(xx, c_.min() + 2, xx + 1, c_.min() + 2)
        L.put(sn.mask() & m, col(P["body2"]))
    vx = int(rng.integers(80, 560))
    if v == "a":
        cm, lit = chain_mask(vx, 0, int(rng.integers(150, 200)))
        sil(L, cm, P, "body", rim=None, keep=True)
        L.put(lit, col(P["rim"]), keep=True)
        ys = np.nonzero(cm.any(1))[0]
        lumps = Draw(W)
        for yy in rng.choice(ys[10:], 3, replace=False):
            lumps.ellipse(vx - 4, yy - 3, vx + 4, yy + 3)
        _icicle(lumps, vx, ys.max(), 18, 6)
        lm = sil(L, lumps.mask(), P, "body", keep=True)
        _facet(L, P, lm, vx)
    else:
        dr = Draw(W)
        _icicle(dr, vx, 0, int(rng.integers(150, 190)), 10, 2)
        m2 = sil(L, dr.mask(), P, "body", keep=True)
        _facet(L, P, m2, vx)


def _prism(dr, x, y, ang, length, w, tip=None):
    """A crystal prism from its base (x, y) pointing along ang degrees (90 = down): a body and a pointed tip."""
    tip = tip if tip is not None else w * 0.9
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    hw = w / 2
    pts = [(x + px * hw, y + py * hw), (x + px * hw + ux * (length - tip), y + py * hw + uy * (length - tip)),
           (x + ux * length, y + uy * length),
           (x - px * hw + ux * (length - tip), y - py * hw + uy * (length - tip)), (x - px * hw, y - py * hw)]
    dr.poly(pts)
    return pts


def _cluster(L, P, rng, x, y, size, down, n=None, spread=70):
    """A fan of crystal prisms from (x, y), pointing down (from the ceiling) or up; each with a lit facet and an
    edge line down its middle."""
    n = n or int(rng.integers(3, 6))
    order = sorted(range(n), key=lambda k: -abs(k - (n - 1) / 2))
    for k in order:
        t = (k - (n - 1) / 2) / max(1, (n - 1) / 2)
        ang = (90 if down else -90) + t * spread / 2 * (1 if down else -1) + rng.uniform(-8, 8)
        ln = size * (1 - 0.45 * abs(t)) * rng.uniform(0.85, 1.1)
        w = max(6.0, ln * rng.uniform(0.36, 0.48))
        bx = x + t * size * 0.22
        dr = Draw(W)
        _prism(dr, bx, y, ang, ln, w)
        m = sil(L, dr.mask(), P, "body", keep=True)
        a = math.radians(ang)
        across = (L.X - bx) * (-math.sin(a)) + (L.Y - y) * math.cos(a)
        lit_side = across * (1 if down else -1) > 0
        L.put(m & lit_side & ~edge(m, -1, 0) & ~edge(m, 0, -1) & ~edge(m, 1, 0), col(P["body2"]))
        seam = m & (np.abs(across) < 0.6) & ~edge(m, 0, 1) & ~edge(m, 0, -1)
        L.put(seam, col(P["rim"]))


def fore_crystal(L, rng, P, v):
    """A ragged rock ceiling with stalactites and fans of crystal tips pointing down; rock, stalagmites and upward
    crystal clusters along the bottom; one thin dripstone column (plus a hanging crystal string on b)."""
    groups = slots(rng, (130, 290), (70, 180))
    for k, (x0, x1) in enumerate(groups):
        xs, d = blob_band(rng, x0, x1, 14, 14, taper=0.3)
        m = band_mask(xs, d)
        sil(L, m, P, "body", rim=None)
        n = int((x1 - x0) / 34) + 1
        for j in range(n):
            sx = x0 + (x1 - x0) * (j + rng.uniform(0.2, 0.8)) / n
            base = d[int(np.clip(sx - x0, 0, len(d) - 1))] - 3
            if (j + k) % 2 == 0:
                ln = min(rng.uniform(26, 56), TOP + 6 - base)
                w = rng.uniform(10, 18)
                dr = Draw(W)
                pts = path(sx, base, 90 + rng.uniform(-6, 6), ln, rng.uniform(-10, 10), step=2.0)
                poly = ribbon(pts, w, 1.0, lambda t: (1 - t) ** 0.85 + 0.05)
                jag = rng.uniform(-1.2, 1.2, len(poly))
                poly = [(px + jag[i], py) for i, (px, py) in enumerate(poly)]
                dr.poly(poly)
                sm = sil(L, dr.mask(), P, "body", keep=True)
                L.put(sm & (L.X < sx - 1) & ~edge(sm, -1, 0) & (L.Y > base + 3), col(P["body2"]))
            else:
                _cluster(L, P, rng, sx, base, min(rng.uniform(32, 54), TOP + 6 - base), True)
    bgroups = slots(rng, (110, 270), (80, 190))
    for k, (x0, x1) in enumerate(bgroups):
        xs, d = blob_band(rng, x0, x1, 16, 12, taper=0.35)
        m = band_mask(xs, d, top=False)
        n = int((x1 - x0) / 44) + 1
        for j in range(n):
            sx = x0 + (x1 - x0) * (j + rng.uniform(0.2, 0.8)) / n
            top = H - d[int(np.clip(sx - x0, 0, len(d) - 1))] + 4
            if (j + k) % 3 == 1:
                dr = Draw(W)
                ln = min(rng.uniform(18, 34), top - BOT + 2)
                pts = path(sx, top + 2, -90 + rng.uniform(-6, 6), ln, rng.uniform(-10, 10), step=2.0)
                dr.poly(ribbon(pts, rng.uniform(10, 16), 1.0, lambda t: (1 - t) ** 0.8 + 0.05))
                sil(L, dr.mask(), P, "body", keep=True)
            else:
                _cluster(L, P, rng, sx, top, min(rng.uniform(30, 50), top - BOT + 2), False)
        sil(L, m, P, "body")
    cx = rng.uniform(80, 560)
    nz = Noise(H, 6, rng, 2)
    y = np.arange(H, dtype=np.float32)
    half = 3.0 + 1.6 * nz(np.zeros_like(y) + 5, y) + 16 * np.clip((34 - y) / 34, 0, 1) ** 2 \
        + 18 * np.clip((y - (H - 40)) / 40, 0, 1) ** 2
    sway = 3.0 * np.sin(y / 47.0 + rng.uniform(0, 6))
    m = np.abs(wdx(L.X, cx, W) - sway[:, None]) <= half[:, None]
    sil(L, m, P, "body")
    L.put(m & (wdx(L.X, cx, W) - sway[:, None] < -1.0) & ~edge(m, -1, 0), col(P["body2"]))
    if v == "b":
        sx = (cx + 640 + rng.uniform(-80, 80)) % W
        dr = Draw(W)
        ln = rng.uniform(120, 170)
        dr.line([(sx, 0), (sx, ln)], width=1)
        sil(L, dr.mask(), P, "body", rim=None, keep=True)
        for yy in (ln * 0.55, ln):
            dr = Draw(W)
            _prism(dr, sx, yy - 5, 90, 16, 7, 5)
            _prism(dr, sx, yy - 3, -90, 8, 7, 4)
            m2 = sil(L, dr.mask(), P, "body", keep=True)
            L.put(m2 & (L.X < sx) & ~edge(m2, -1, 0), col(P["body2"]))


def fore_foundry(L, rng, P, v):
    """Heavy I-beams on diagonal braces, a crane trolley with a hook on a chain, sagging chains and pipes under the
    roof; gears, rails and slag heaps with a crucible along the bottom; the hook's chain and an I-beam pillar."""
    groups = slots(rng, (170, 340), (80, 180))
    hook_x = None
    for k, (x0, x1) in enumerate(groups):
        kind = (k + (v == "b")) % 3
        if kind in (0, 2):
            y = int(rng.integers(6, 14))
            h = int(rng.integers(18, 24))
            br = Draw(W)
            for xb, s_ in ((x0 + 16, 1), (x1 - 16, -1)):
                br.poly([(xb - 3, 0), (xb + 3, 0), (xb + 3 + s_ * y * 1.2, y + 1), (xb - 3 + s_ * y * 1.2, y + 1)])
            sil(L, br.mask(), P, "body", keep=True)
            if kind == 0 and hook_x is None:
                ibeam(L, P, x0, x1, y, h)
                tx = int(x0 + (x1 - x0) * rng.uniform(0.35, 0.65))
                tr = Draw(W)
                tr.rect(tx - 13, y + h, tx + 13, y + h + 10)
                tr.ellipse(tx - 12, y + h - 3, tx - 4, y + h + 5)
                tr.ellipse(tx + 4, y + h - 3, tx + 12, y + h + 5)
                trm = sil(L, tr.mask(), P, "body")
                b = Draw(W)
                b.rect(tx - 10, y + h + 6, tx + 10, y + h + 6)
                L.put(b.mask() & trm, col(P["body2"]))
                hook_x = (tx, y + h + 10)
            else:
                holes = []
                dr = Draw(W)
                xa, xb = x0 + 24, x1 - 24
                chain_line(dr, catenary(xa, y + h, xb, y + h, min(TOP - y - h, (xb - xa) * 0.2)), holes, w=3,
                           gap=6)
                sil(L, dr.mask(), P, "body", rim=None, keep=True)
                punch(L, holes)
                ibeam(L, P, x0, x1, y, h)
        else:
            pipe_run(L, P, x0 + 18, x1 - 36, 40, 5, up=(True, False), flange=36)
            pipe_run(L, P, x0, x1, int(rng.integers(14, 20)), 9, up=(True, True), flange=44)
    bgroups = slots(rng, (120, 290), (90, 200))
    for k, (x0, x1) in enumerate(bgroups):
        kind = (k + (v == "a")) % 3
        if kind == 0:
            r = min(52, (x1 - x0) / 2 - 2)
            gear(L, P, (x0 + x1) / 2, H + 8, r)
            if x1 - x0 > 150:
                gear(L, P, x0 + 26, H - 4, 24)
        elif kind == 1:
            xs, d = blob_band(rng, x0, x1, 10, 6, taper=0.2)
            sil(L, band_mask(xs, d, top=False), P, "body", rim=None)
            dr = Draw(W)
            dr.rect(x0, H - 30, x1, H - 26)
            dr.rect(x0, H - 25, x1, H - 23)
            dr.rect(x0, H - 22, x1, H - 19)
            for xs_ in range(int(x0), int(x1), 18):
                dr.rect(xs_, H - 18, xs_ + 9, H)
            sil(L, dr.mask(), P, "body")
            bx = x1 - 14              # a buffer stop
            bs = Draw(W)
            bs.poly([(bx - 10, H - 30), (bx + 4, H - 52), (bx + 10, H - 52), (bx + 10, H - 30)])
            bs.rect(bx - 12, H - 48, bx - 6, H - 40)
            sil(L, bs.mask(), P, "body")
        else:
            xs, d = blob_band(rng, x0, x1, 30, 16, taper=0.45)
            sil(L, band_mask(xs, d, top=False), P, "body")
            cx = (x0 + x1) / 2
            dr = Draw(W)
            for o in (-W, 0, W):
                dr.d.chord([cx - 40 + o, H - 84, cx + 40 + o, H - 6], 0, 180, fill=255)
            dr.rect(cx - 45, H - 48, cx + 45, H - 43)
            dr.rect(cx + 40, H - 54, cx + 52, H - 48)
            cm = sil(L, dr.mask(), P, "body")
            ln = Draw(W)
            arc(ln, (cx - 34, H - 76, cx + 34, H - 12), 100, 170, 1)
            L.put(ln.mask() & cm, col(P["body2"]))
    if hook_x is None:
        hook_x = (int(rng.integers(100, 500)), 0)
    tx, ty = hook_x
    cm, lit = chain_mask(tx, ty, ty + int(rng.integers(120, 170)))
    sil(L, cm, P, "body", rim=None, keep=True)
    L.put(lit, col(P["rim"]), keep=True)
    ye = int(np.nonzero(cm.any(1))[0].max())
    dr = Draw(W)
    hook(dr, tx, ye + 1, 1.3)
    sil(L, dr.mask(), P, "body", keep=True)
    pillar(L, P, int((tx + 640 + rng.integers(-60, 60)) % W), 12)


def fore_citadel(L, rng, P, v):
    """Gloam architecture: angular blades and stepped teeth hanging from the top, conduits with 45-degree bends,
    diamond pendants; angular plates and spikes along the bottom; a notched pylon and a pendant on a cable."""
    groups = slots(rng, (140, 300), (70, 180))
    for k, (x0, x1) in enumerate(groups):
        for _ in range(int((x1 - x0) / 34)):     # a farther row of thin blades in the second tone, behind
            bx = rng.uniform(x0, x1)
            d2 = Draw(W)
            d2.poly([(bx - 4, 0), (bx + 4, 0), (bx + rng.uniform(-5, 5), rng.uniform(28, TOP + 2))])
            L.put(d2.mask(), col(P["body2"]), keep=True)
        cy = rng.uniform(18, 30)
        cpts, x = [(x0 + 6, cy)], x0 + 6
        while x < x1 - 30:
            x += rng.uniform(20, 50)
            x = min(x, x1 - 10)
            cpts.append((x, cy))
            dy = rng.choice([-7, 7, 0])
            cy = float(np.clip(cy + dy, 16, 34))
            x += abs(dy)
            cpts.append((x, cy))
        dr = Draw(W)
        dr.line(cpts, width=3)
        for bx, by in (cpts[0], cpts[-1]):
            dr.rect(bx - 2, by - 4, bx + 2, by + 4)
        for bx, by in cpts[1:-1:3]:
            dr.rect(bx - 1, by - 3, bx + 1, by + 3)
        sil(L, dr.mask(), P, "body", keep=True)
        pts = [(x0, 0)]
        x = x0
        y = int(rng.integers(7, 13))
        pts.append((x0, y))
        while x < x1 - 12:
            w = rng.uniform(10, 26)
            if rng.random() < 0.45:
                ln = rng.uniform(22, TOP + 4 - y)
                pts += [(x + w * 0.15, y + 3), (x + w * 0.55, y + ln), (x + w * 0.75, y + 4)]
            else:
                y = int(np.clip(y + rng.integers(-5, 6), 6, 20))
                pts += [(x + 3, y), (x + w, y)]
            x += w
        pts += [(x1, y), (x1 + 8, 0)]
        dr = Draw(W)
        dr.poly(pts)
        m = sil(L, dr.mask(), P, "body", keep=True)
        ln = Draw(W)
        ln.rect(x0 + 2, 3, x1 - 2, 3)
        L.put(ln.mask() & m, col(P["body2"]))
        if (k + (v == "a")) % 2 == 0:
            px = rng.uniform(x0 + 24, x1 - 24)
            py = rng.uniform(40, 52)
            dr = Draw(W)
            dr.rect(px, 8, px, py - 8)
            dr.poly([(px, py - 9), (px + 7, py), (px, py + 12), (px - 7, py)])
            m2 = sil(L, dr.mask(), P, "body", keep=True)
            L.put(m2 & (L.X > px) & (L.Y > py - 6) & ~edge(m2, 1, 0) & ~edge(m2, 0, 1), col(P["acc"]))
    bgroups = slots(rng, (110, 270), (80, 190))
    for k, (x0, x1) in enumerate(bgroups):
        dr = Draw(W)
        x = x0
        while x < x1:
            w = rng.uniform(26, 64)
            h = rng.uniform(16, 40)
            c = rng.uniform(5, min(12, w / 3))
            dr.poly([(x, H), (x, H - h + c), (x + c, H - h), (x + w - c, H - h), (x + w, H - h + c), (x + w, H)])
            x += w + rng.uniform(-6, 4)
        m = dr.mask()
        for _ in range(int((x1 - x0) / 24)):
            sx = rng.uniform(x0 + 5, x1 - 5)
            top = np.nonzero(m[:, int(sx) % W])[0]
            top = top.min() if len(top) else H
            dr2 = Draw(W)
            ln = min(rng.uniform(12, 38), top - BOT + 2)
            lean = rng.uniform(-6, 6)
            dr2.poly([(sx - 4, top + 2), (sx + 4, top + 2), (sx + lean, top - ln)])
            sil(L, dr2.mask(), P, "body", keep=True)
        sil(L, m, P, "body")
        seams = Draw(W)
        for xx in np.arange(x0 + 10, x1, 18):
            seams.rect(xx, H - 10, xx + 8, H - 9)
        L.put(seams.mask() & m, col(P["body2"]))
    px = int(rng.integers(80, 560))
    dr = Draw(W)
    dr.rect(px, 0, px + 7, H)
    dr.poly([(px + 7, 0), (px + 26, 0), (px + 7, 28)])
    dr.poly([(px + 7, H), (px + 28, H), (px + 7, H - 32)])
    dr.poly([(px, 0), (px - 12, 0), (px, 14)])
    m = sil(L, dr.mask(), P, "body")
    for yy in range(44, H - 44, 36):
        cut = Draw(W)
        cut.poly([(px + 8, yy), (px + 3, yy + 5), (px + 8, yy + 10)])
        L.erase(cut.mask())
    web = Draw(W)
    web.rect(px + 2, 0, px + 4, H)
    L.put(web.mask() & L.a & ~edge(m, 0, -1) & ~edge(m, 0, 1), col(P["body2"]))
    cx = (px + 640 + int(rng.integers(-80, 80))) % W
    ln = int(rng.integers(130, 190))
    dr = Draw(W)
    dr.rect(cx, 0, cx, ln)
    dr.poly([(cx, ln - 2), (cx + 7, ln + 9), (cx, ln + 24), (cx - 7, ln + 9)])
    m2 = sil(L, dr.mask(), P, "body", keep=True)
    L.put(m2 & (L.X > cx) & (L.Y > ln + 2) & ~edge(m2, 1, 0) & ~edge(m2, 0, 1), col(P["acc"]))


THEMES = {"station": fore_station, "hull": fore_hull, "jungle": fore_jungle, "hive": fore_hive, "ice": fore_ice,
          "crystal": fore_crystal, "foundry": fore_foundry, "citadel": fore_citadel}


# ---------------------------------------------------------------------------------------------------------- build

def build(name):
    """The fore layer of one background (a Layer)."""
    theme, v = name.rsplit("_", 1)
    rng = np.random.default_rng(zlib.crc32(("fore:" + name).encode()))
    L = Layer(W)
    THEMES[theme](L, rng, PALS[name], v)
    despeckle(L)
    return L


def despeckle(L):
    """Removes opaque pixels without any opaque 8-neighbour (true specks)."""
    a = L.a
    pad = np.pad(a, ((1, 1), (0, 0)))
    n = np.zeros(a.shape, np.int32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy:
                n += np.roll(pad[1 + dy:1 + dy + a.shape[0]], -dx, axis=1)
    L.erase(a & (n == 0))


def check(L, name):
    """The rules of a fore layer: palette colours, binary alpha, the middle band empty except at most MAX_VERT thin
    verticals per 640 px (each at most MAX_VERT_W px wide). Returns a list of problems."""
    probs = []
    pal = set(map(tuple, PAL.tolist()))
    used = set(map(tuple, np.unique(L.rgb[L.a].reshape(-1, 3), axis=0).tolist()))
    if used - pal:
        probs.append(f"colours outside the palette: {sorted(used - pal)[:4]}")
    cols_ = L.a[MID[0]:MID[1]].any(0)
    runs = []
    if cols_.any():
        start = int(np.argmin(cols_)) if not cols_.all() else 0
        x = start
        n = 0
        run = None
        while n < W:
            if cols_[x % W]:
                run = [x, x] if run is None else [run[0], x]
            elif run is not None:
                runs.append(run)
                run = None
            x += 1
            n += 1
        if run is not None:
            runs.append(run)
    for r0, r1 in runs:
        if r1 - r0 + 1 > MAX_VERT_W:
            probs.append(f"middle band: element at x {r0 % W}..{r1 % W} is {r1 - r0 + 1} px wide")
    for w0 in range(0, W, 64):
        n = sum(1 for r0, r1 in runs if w0 <= r0 % W < w0 + 640 or w0 <= r0 % W + W < w0 + 640)
        if n > MAX_VERT:
            probs.append(f"middle band: {n} verticals in x {w0}..{w0 + 640}")
            break
    cover = L.a[MID[0]:MID[1]].mean()
    if cover > 0.02:
        probs.append(f"middle band {cover:.1%} covered")
    top = L.a[:TOP].mean()
    bot = L.a[BOT:].mean()
    return probs, dict(verticals=len(runs), top=top, bottom=bot, middle=cover)


def save(name, L):
    out = ROOT / "assets" / "bg" / name
    Image.fromarray(L.rgba(), "RGBA").save(out / "fore.png", optimize=True)
    px, py, yoff = SPECS[name.rsplit("_", 1)[0]]
    p = out / "bg.txt"
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines()
             if not ln.startswith("fore ") and not ln.startswith("# fore")]
    lines += [
        "# fore <parallax x> <parallax y> <y offset>: fore.png (made by tools/backgrounds/fore.py), drawn IN FRONT of",
        "# fore   the world, behind the HUD: dark silhouettes in its top 62 and bottom 52 rows, the middle empty but",
        "# fore   for a thin pillar / chain / vine. x like a layer (-camera_x * parallax x, wrapped). y: keep it on the",
        "# fore   screen -- its top row at the y offset on the 400 px view and 20 px higher on the 360 px view; use",
        "# fore   parallax y only for a small bounded sway (the rise formula of the layers would carry the top band",
        "# fore   into the middle of the screen); no clamp-to-edge rows above or below it.",
        f"fore {px:g} {py:g} {yoff:d}",
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out / "fore.png"


def make(name, previews=True):
    L = build(name)
    probs, stats = check(L, name)
    out = save(name, L)
    if previews:
        preview(name, L)
    return out, probs, stats


# --------------------------------------------------------------------------------------------------------- preview

def _bg_layers(name):
    d = ROOT / "assets" / "bg" / name
    specs, fill = {}, ((0, 0, 0), (0, 0, 0))
    for ln in (d / "bg.txt").read_text(encoding="utf-8").splitlines():
        w = ln.split()
        if not w or w[0].startswith("#"):
            continue
        if w[0] == "fill":
            v = [int(x) for x in w[1:7]]
            fill = (tuple(v[:3]), tuple(v[3:]))
        elif w[0].startswith("layer"):
            specs[int(w[0][5:])] = (float(w[1]), float(w[2]), float(w[3]),
                                    float(w[4]) if len(w) > 4 and not w[4].startswith("#") else 0.0)
    layers = []
    for n in range(6):
        p = d / f"layer{n}.png"
        if p.exists():
            layers.append((np.asarray(Image.open(p).convert("RGBA")), specs.get(n, (0.1, 0.05, 0, 0))))
    return layers, fill


def _compose_bg(layers, fill, camx, rise, vw, vh):
    out = np.zeros((vh, vw, 3), np.uint8)
    t = np.linspace(0, 1, vh)[:, None, None]
    out[:] = (np.array(fill[0]) * (1 - t) + np.array(fill[1]) * t).astype(np.uint8)
    for img, (px, py, yoff, sc) in layers:
        h, w = img.shape[:2]
        top = int(math.floor(yoff + rise * py))
        sy = np.clip(np.arange(vh) - top, 0, h - 1)
        sx = (np.arange(vw) + int(round(camx * px))) % w
        src = img[sy][:, sx]
        a = src[..., 3:] > 0
        out = np.where(a, src[..., :3], out)
    return out


def _mock_map():
    rows, cols = 13, 40
    g = [[" "] * cols for _ in range(rows)]

    def fill(r0, r1, c0, c1, ch):
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                g[r][c] = ch
    fill(0, 1, 0, 6, "#")
    fill(2, 7, 0, 1, "#")
    fill(2, 7, 2, 5, ".")
    fill(2, 3, 6, 6, "#")
    fill(8, 12, 0, 9, "#")
    fill(8, 12, 14, 39, "#")
    fill(5, 5, 15, 18, "#")
    fill(3, 3, 21, 24, "-")
    fill(6, 6, 26, 28, "-")
    fill(0, 0, 33, 38, "#")
    fill(1, 7, 33, 33, "#")
    fill(1, 7, 34, 37, ".")
    fill(1, 2, 38, 38, "#")
    fill(7, 7, 38, 38, "#")
    return g


def _mock_world(theme, camx, vw, vh, dy=0):
    """The mock gameplay frame (RGBA) at camera x: the theme's real tiles, the hero, a crystal and an enemy."""
    tdir = ROOT / "assets" / "tiles" / theme
    g = _mock_map()
    rows, cols = len(g), len(g[0])
    world = np.zeros((rows * 32, cols * 32, 4), np.uint8)
    terr = np.asarray(Image.open(tdir / "terrain_a.png").convert("RGBA"))
    back = np.asarray(Image.open(tdir / "back.png").convert("RGBA"))
    plat = np.asarray(Image.open(tdir / "platform.png").convert("RGBA"))

    def at(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return "#"
        return g[r][c]
    nbs = ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1))
    for r in range(rows):
        for c in range(cols):
            ch = g[r][c]
            var = (r * 7 + c * 13) % 4
            if ch == "#":
                sheet, same = terr, lambda x: x == "#"
            elif ch == ".":
                sheet, same = back, lambda x: x != " "
            elif ch == "-":
                left, right = at(r, c - 1) == "-", at(r, c + 1) == "-"
                k = 0 if not left and not right else (1 if not left else (3 if not right else 2))
                tile = plat[var * 32:(var + 1) * 32, k * 32:(k + 1) * 32]
                dst = world[r * 32:(r + 1) * 32, c * 32:(c + 1) * 32]
                dst[tile[..., 3] > 0] = tile[tile[..., 3] > 0]
                continue
            else:
                continue
            mask = sum(1 << b for b, (dr_, dc) in enumerate(nbs) if same(at(r + dr_, c + dc)))
            idx = var * 256 + mask
            ty, tx = (idx // 16) * 32, (idx % 16) * 32
            tile = sheet[ty:ty + 32, tx:tx + 32]
            dst = world[r * 32:(r + 1) * 32, c * 32:(c + 1) * 32]
            dst[tile[..., 3] > 0] = tile[tile[..., 3] > 0]

    def sprite(sheet, frame, fw, fh, ax, ay, wx, wy):
        im = np.asarray(Image.open(ROOT / "assets" / "sprites" / f"{sheet}.png").convert("RGBA"))
        ncol = im.shape[1] // fw
        fy, fx = (frame // ncol) * fh, (frame % ncol) * fw
        spr = im[fy:fy + fh, fx:fx + fw]
        x0, y0 = wx - ax, wy - ay
        dst = world[y0:y0 + fh, x0:x0 + fw]
        m = spr[..., 3] > 0
        dst[m] = spr[m]
    sprite("hero", 0, 64, 64, 32, 60, 620, 256)
    sprite("items", 0, 32, 32, 16, 16, 760, 196)
    sprite("items", 0, 32, 32, 16, 16, 520, 140)
    sprite("sweeper", 0, 64, 64, 32, 60, 900, 256)
    out = np.zeros((vh, vw, 4), np.uint8)
    xs = (np.arange(vw) + camx) % world.shape[1]
    ys = np.arange(vh) + dy
    ok = (ys >= 0) & (ys < world.shape[0])
    out[ok] = world[ys[ok]][:, xs]
    return out


def _over(base, top):
    m = top[..., 3:] > 0
    return np.where(m, top[..., :3], base)


def _fore_view(F, camx, px, vw, vh, top):
    out = np.zeros((vh, vw, 4), np.uint8)
    sx = (np.arange(vw) + int(round(camx * px))) % F.shape[1]
    sy = np.arange(vh) - top
    ok = (sy >= 0) & (sy < F.shape[0])
    out[ok] = F[sy[ok]][:, sx]
    return out


def view(name, F, camx, vh=400):
    theme = name.rsplit("_", 1)[0]
    layers, fill = _bg_layers(name)
    px = SPECS[theme][0]
    bg = _compose_bg(layers, fill, camx, 0, 640, vh)
    world = _mock_world(theme, camx, 640, vh, dy=0 if vh == 400 else 20)
    v = _over(bg, world)
    return _over(v, _fore_view(F, camx, px, 640, vh, 0 if vh == 400 else -20))


def preview(name, L):
    F = L.rgba()
    a = view(name, F, 0)
    b = view(name, F, 560)
    c = view(name, F, 900, 360)
    yy, xx = np.mgrid[0:H, 0:W]
    chk = np.where(((yy // 8 + xx // 8) % 2 == 0)[..., None], 120, 90).astype(np.uint8).repeat(3, -1)
    alone = _over(chk, F)
    crop = F[0:180, 200:520]
    cb = _over(chk[0:180, 0:320], crop)
    crop2 = np.repeat(np.repeat(cb, 2, 0), 2, 1)
    gap = 6
    out = np.full((400 + gap + 400 + gap + 360, 1280 + gap, 3), 30, np.uint8)
    out[0:400, 0:640] = a
    out[0:400, 640 + gap:1280 + gap] = b
    out[406:806, 0:1280] = alone
    out[812:1172, 0:640] = c
    out[812:1172, 640 + gap:1280 + gap] = crop2
    p = ROOT / "work" / "bg" / f"{name}_fore_preview.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out).save(p)
    return p


def overview(names):
    tiles = []
    for n in names:
        p = ROOT / "work" / "bg" / f"{n}_fore_preview.png"
        if p.exists():
            im = Image.open(p).convert("RGB").crop((0, 0, 640, 400)).resize((320, 200), Image.NEAREST)
            tiles.append(np.asarray(im))
    if not tiles:
        return None
    while len(tiles) % 4:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.concatenate(tiles[i:i + 4], 1) for i in range(0, len(tiles), 4)]
    out = ROOT / "work" / "bg" / "_fore_overview.png"
    Image.fromarray(np.concatenate(rows, 0)).save(out)
    return out
