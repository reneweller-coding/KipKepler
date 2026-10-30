"""Theme `hive`: organic caves of the brood. Glossy chitin plates, amber resin coating the tops and dripping from
undersides, pulsing amber nodules; terrain B are wax combs; the back wall is a dark ribbed tunnel of flesh."""
import math

import numpy as np
from scipy import ndimage

from tilelib import T, XX, YY, Tile, RAMPS, C, geom, displaced, periodic_noise, noise_1d, shade_form
from organic import StoneTex, Profiles, rock_shape, rock_fill, hang, tufts, column_rng, worley
from parts import (box, spike_tile, door_tile, toggle_on, toggle_off, conveyor_tile, liquid_tiles, rectm, ellipse,
                   poly, finish, pad, line_m, breakable_block, crumble_block)

RO = RAMPS["rose"]
CR = RAMPS["crimson"]
PU = RAMPS["purple"]
OR = RAMPS["orange"]
YE = RAMPS["yellow"]
TN = RAMPS["tan"]
BR = RAMPS["brown"]
LI = RAMPS["lime"]
OUT = C("outline", 0)

SEED = 4401
CHIT = [CR[0], CR[1], RO[1], RO[2], RO[3], RO[4], RO[5]]
TEX = StoneTex(SEED, n=2, aspect=1.0, keep=0.55)
PROF = Profiles(SEED + 1, top=(1, 2.5), bottom=(2, 5), side=(0, 2))
_rng = np.random.default_rng(SEED + 2)
RESW = [2.6 + 2.2 * (noise_1d(_rng, T, 2.5) * 0.5 + 0.5) for _ in range(4)]
NODULES = {1: [(11, 18, 3)], 3: [], 0: [], 2: []}
BORDER_OK = (XX >= 3) & (XX <= 28) & (YY >= 3) & (YY <= 28)


def _nodule(t, cx, cy, r, region):
    m = ellipse(T, T, (cx - r, cy - r, cx + r, cy + r)) & region
    if not m.any():
        return
    ring = ndimage.binary_dilation(m) & ~m & region
    t.fill(ring, CR[0])
    t.fill(m, OR[3], glow=True)
    t.fill(m & (YY < cy) , OR[4], glow=True)
    t.fill(m & (YY < cy) & (XX < cx), YE[5], glow=True)
    t.px(cx - max(1, r // 2), cy - max(1, r // 2), YE[7], glow=bool(region[cy - max(1, r // 2), cx - max(1, r // 2)]))


def _resin_top(t, s, v, scale=1.0):
    if not s.top:
        return
    k = s.depth
    w = RESW[v][None, :] * scale
    band = s.solid & (s.wt > 0.35) & (k < w)
    t.fill(band, OR[2])
    t.fill(band & (k < w - 1), OR[3])
    t.fill(band & (k < 1.6), YE[3])
    t.fill(band & (k < 0.8), YE[5])
    t.fill(band & (s.lit < -0.2) & (k < 1.6), OR[3])
    rng = column_rng(SEED, v, 5)
    for x in rng.choice(np.arange(3, 29), 3, replace=False):
        ys = np.nonzero(band[:, x])[0]
        if len(ys) == 0:
            continue
        y0 = ys.max()
        ln = int(rng.integers(2, 6))
        for i in range(ln):
            y = y0 + 1 + i
            if y < T and s.solid[y, x]:
                t.px(int(x), y, OR[2] if i < ln - 1 else OR[3])
                if i == ln - 1 and x + 1 < T and s.solid[y, x + 1]:
                    t.px(int(x) + 1, y, OR[2])
    # glossy specks
    for x in rng.choice(np.arange(3, 29), 3, replace=False):
        ys = np.nonzero(band[:, x])[0]
        if len(ys) > 2:
            t.px(int(x), int(ys.min()) + 1, YE[6])


def terrain_a(m, v):
    s = rock_shape(m, v, PROF, 5)
    t = Tile()
    rock_fill(t, s, TEX, v, CHIT, 2.7, tex_amp=1.0, edge_amp=1.2, edge_w=6, deep=(10, 14, 0.5), crack=0.25,
              crack_col=CR[0], calm=(10, 22, 0.8), rim_hi=RO[5], rim_lo=CR[0])
    # glossy specular spots on the plates
    spec = s.solid & (TEX.lit[v] > 0.8) & (TEX.h[v] > 0.6) & (s.depth > 2)
    t.fill(spec, RO[5])
    for (cx, cy, r) in NODULES[v]:
        if s.depth[cy, cx] < 14:
            _nodule(t, cx, cy, r, s.solid & (s.depth > r + 2) & BORDER_OK)
    _resin_top(t, s, v)

    def dc(i, n, dx):
        return YE[4] if i == n - 1 else (OR[3] if dx == 0 else OR[2])
    hang(t, s, v, SEED + 3, dc, count=(1, 3), length=(2, 6), width=2, glow_fn=lambda i, n: i == n - 1)
    return t


# wax combs: Voronoi of a periodic hex-ish lattice; border cells are always open cavities so neighbours agree
_PTS = np.array([(0, 0), (16, 0), (8, 16), (24, 16)], float)
_F1, _F2, _CID = worley(None, 0, pts=_PTS)
FILL = {0: {2: "cap"}, 1: {3: "honey"}, 2: {}, 3: {2: "cap", 3: "cap"}}
WAX = [BR[1], TN[2], TN[3], TN[4], YE[4], YE[5], YE[6]]


def terrain_b(m, v):
    g = geom(m, 3, "round")
    s = displaced(g)
    t = Tile()
    sol, k = s.solid, s.depth
    wall = (_F2 - _F1) < 3.0
    cell = ~wall
    t.fill(sol & wall, TN[4])
    t.fill(sol & wall & ((_F2 - _F1) < 1.2), TN[3])
    fill = FILL[v]
    for ci in range(len(_PTS)):
        cm = sol & cell & (_CID == ci)
        kind = fill.get(ci, "open")
        cx, cy = _PTS[ci]
        dx = XX - cx
        dx = np.where(dx > 16, dx - 32, np.where(dx < -16, dx + 32, dx))
        dy = YY - cy
        dy = np.where(dy > 16, dy - 32, np.where(dy < -16, dy + 32, dy))
        rim = cm & ~ndimage.binary_erosion(cell & (_CID == ci))
        if kind == "open":
            t.fill(cm, BR[1])
            t.fill(cm & (dy > 2), OR[1])
            t.fill(rim & (dx + dy < 0), CR[0])
            t.fill(rim & (dx + dy > 2), TN[5])
        elif kind == "honey":
            t.fill(cm, OR[3], glow=True)
            t.fill(cm & (dy > 0), OR[4], glow=True)
            t.fill(cm & (dx + dy < -5), YE[6], glow=True)
            t.fill(rim & (dx + dy < 0), OR[2], glow=True)
        else:
            t.fill(cm, TN[3])
            t.fill(cm & (dx + dy < -3), TN[5])
            t.fill(cm & (dx + dy > 4), TN[2])
            t.fill(rim & (dx + dy < 0), TN[2])
    # wax rim along exposed edges
    band = sol & (k < 3)
    t.fill(band, YE[5])
    t.fill(band & (k >= 1) & (s.lit < -0.2), TN[4])
    t.fill(band & (k < 1) & (s.lit > 0.3), YE[6])
    t.fill(band & (k < 1) & (s.lit < -0.3), TN[2])
    t.fill(sol & (k >= 3) & (k < 4) & (s.lit < -0.2), TN[3])

    def dc(i, n, dx):
        return YE[5] if i == n - 1 else OR[4]
    hang(t, s, v, SEED + 13, dc, count=(1, 2), length=(2, 5), width=2, glow_fn=lambda i, n: True)
    return t


BACK = [CR[0], RAMPS["violet"][1], PU[1]]
BKTEX = StoneTex(SEED + 7, n=2, aspect=1.6, keep=0.5, tone=0)
BKPROF = Profiles(SEED + 8, top=(0, 3), bottom=(0, 4), side=(0, 3))


def back(m, v):
    """Dark tunnel flesh with soft horizontal ribs (continuous across tiles) and faint veins; a glossy membrane rim
    toward the sky."""
    s = rock_shape(m, v, BKPROF, 6)
    t = Tile()
    sol, k = s.solid, s.depth
    t.fill(sol, PU[1])
    x = np.arange(T)
    for (y0, ph) in ((7, 0.0), (23, 2.1)):
        yr = np.round(y0 + 1.6 * np.sin(2 * math.pi * x / 32.0 + ph)).astype(int)
        top = YY == yr[None, :]
        t.fill(sol & top, CR[1])
        t.fill(sol & (YY == yr[None, :] + 1), PU[1])
        t.fill(sol & (YY == yr[None, :] + 2), CR[0])
        t.fill(sol & (YY == yr[None, :] - 1) & ((XX % 3) == 0), PU[2])
    if v in (1, 3):
        rng = column_rng(SEED, v, 31)
        xx, yy = float(rng.integers(8, 24)), 4.0
        pts = []
        for i in range(12):
            pts.append((xx, yy))
            xx += rng.uniform(-2, 2)
            yy += 2.0
        t.fill(line_m(T, T, pts) & sol & (k > 4) & BORDER_OK, CR[1])
    rim = sol & (k < 3.5)
    t.fill(rim, CR[1])
    t.fill(rim & (k < 2) & (s.lit > 0.3), RO[2])
    t.fill(rim & (k < 1) & (s.lit > 0.3), RO[3])
    t.fill(rim & (s.lit < -0.3) & (k < 2), CR[0])

    def dc(i, n, dx):
        return CR[1] if i < n - 1 else OR[2]
    hang(t, s, v, SEED + 50, dc, count=(1, 2), length=(2, 6))
    return t


TINTS = [
    (0, 255, 255, 255, 0, "neutral"),
    (1, 255, 226, 190, 8, "molten"),
    (2, 220, 210, 255, -16, "violet"),
    (3, 190, 170, 170, 0, "deep"),
]


# ------------------------------------------------------------------------------------------------ small sheets


def platform():
    """A bone rib bridge glued with resin; columns single, left end, middle, right end."""
    rows = []
    BONE = [BR[1], TN[3], TN[4], TN[5], TN[6], TN[7]]
    for v in range(4):
        row = []
        for col in range(4):
            t = Tile()
            capl, capr = col in (0, 1), col in (0, 3)
            x0, x1 = (3 if capl else 0), (28 if capr else 31)
            for y in range(1, 10):
                rel = (y - 1) / 8.0
                c = BONE[4] if rel < 0.15 else BONE[3] if rel < 0.5 else BONE[2] if rel < 0.8 else BONE[1]
                t.rect(x0, y, x1, y, c)
            t.rect(x0, 0, x1, 0, BONE[5])
            t.rect(x0, 10, x1, 10, BR[0])
            for i in range(3):
                gx = (i * 11 + v * 7) % 28 + 2
                t.rect(gx, 4, gx + 3, 4, BONE[2])
            # resin blobs
            for bx in ((8, 22) if v % 2 == 0 else (15,)):
                if x0 <= bx <= x1 - 3:
                    blob = ellipse(T, T, (bx - 3, 7, bx + 3, 13))
                    t.fill(blob, OR[3])
                    t.fill(blob & (YY < 10), OR[4])
                    t.px(bx - 1, 8, YE[6])
            if capl:
                t.fill(ellipse(T, T, (0, -1, 7, 6)), BONE[4])
                t.fill(ellipse(T, T, (0, 5, 7, 12)), BONE[3])
                t.fill(ellipse(T, T, (0, 5, 7, 12)) & (YY > 9), BONE[1])
            if capr:
                t.fill(ellipse(T, T, (24, -1, 31, 6)), BONE[3])
                t.fill(ellipse(T, T, (24, 5, 31, 12)), BONE[2])
                t.fill(ellipse(T, T, (24, 5, 31, 12)) & (YY > 9), BONE[1])
            row.append(t)
        rows.append(row)
    return rows


def blocks():
    return [[breakable_block(v, TN, OR[1], OR[4], seed=SEED + 60) for v in range(4)],
            [crumble_block(s, [OR[0], OR[1], OR[2], OR[3], OR[4], YE[5], YE[6]], top=(YE[4], YE[6])) for s in
             range(4)],
            [door_tile(RO, RAMPS["blue"], RAMPS["blue"], o) for o in range(4)],
            [door_tile(RO, YE, YE, o) for o in range(4)],
            [toggle_on(OR, YE, f, RO) for f in range(4)], [toggle_off(YE, f) for f in range(4)],
            [conveyor_tile(f, RO, CR, OR, YE[5]) for f in range(4)],
            [spike_tile(d, [OUT, CR[1], RO[2], RO[3], RO[4], TN[5], TN[6], TN[7]], RO, outline=CR[0], jag=3,
                        seed=8, n=4, height=17) for d in ("up", "down", "left", "right")]]


def liquid():
    ramp = [OR[1], OR[2], OR[3], OR[4], YE[4], YE[6]]
    return liquid_tiles(ramp, (YE[4], YE[6]), glow=True, seed=9, line_col=OR[3], bubble_cols=(YE[4], YE[6]))


# ------------------------------------------------------------------------------------------------------- deco


def deco():
    items = []

    def add(name, t, place, weight, glow=False, outline=True):
        if outline:
            t = finish(pad(t))
        items.append((name, t, place, weight, glow))

    EGG = [CR[0], OR[1], OR[2], OR[3], OR[4], YE[5], YE[6]]
    # egg clusters
    for i, n in enumerate((3, 5)):
        w, h = 10 + n * 4, 16
        t = Tile(w, h)
        rng = np.random.default_rng(SEED + 100 + i)
        for j in range(n):
            cx = 5 + j * 4 + rng.integers(-1, 2)
            hh = int(rng.integers(8, 14))
            m = ellipse(w, h, (cx - 4, h - hh, cx + 4, h - 1))
            shade_form(t, m, EGG, 3, spread=2.0, glow=True)
            t.px(cx - 1, h - hh + 2, YE[7], glow=True)
        add("eggs_%d" % i, t, "floor", 1, True)
    # wall nodule cluster
    t = Tile(20, 16)
    for (cx, cy, r) in ((6, 9, 4), (14, 6, 3), (15, 12, 2)):
        m = ellipse(20, 16, (cx - r, cy - r, cx + r, cy + r))
        t.fill(ndimage.binary_dilation(m) & ~m, CR[1])
        shade_form(t, m, EGG, 3, spread=2.0, glow=True)
    add("nodules", t, "wall", 3, True)
    # hanging larva pod
    t = Tile(12, 26)
    t.fill(line_m(12, 26, [(6, 0), (6, 9)], 1), RO[2])
    m = ellipse(12, 26, (1, 8, 10, 25))
    shade_form(t, m, [CR[0], CR[1], RO[2], RO[3], OR[3], OR[4], YE[5]], 3, spread=2.0)
    t.fill(m & (np.abs(YY[:26, :12] - 16) < 3) & (np.abs(XX[:26, :12] - 5) < 2), YE[4], glow=True)
    for y in (12, 16, 20):
        t.fill(m & (YY[:26, :12] == y), CR[1])
    add("larva_pod", t, "ceiling", 2, True)
    # membrane drape (ceiling)
    t = Tile(30, 14)
    mem = poly(30, 14, [(0, 0), (29, 0), (26, 6), (20, 11), (15, 13), (9, 11), (3, 6)])
    t.fill(mem, RO[2])
    t.fill(mem & (((XX[:14, :30] + YY[:14, :30]) % 5) == 0), RO[3])
    t.fill(mem & (YY[:14, :30] <= 1), RO[3])
    for x in (6, 15, 23):
        t.fill(line_m(30, 14, [(x, 0), (15, 12)]) & mem, CR[1])
    add("membrane", t, "ceiling", 2)
    # resin drips (ceiling)
    t = Tile(16, 16)
    for (x, ln) in ((2, 8), (6, 13), (10, 6), (13, 10)):
        t.rect(x, 0, x + 1, ln, OR[3])
        t.rect(x, 0, x, ln, OR[4])
        t.fill(ellipse(16, 16, (x - 1, ln - 1, x + 2, ln + 2)), YE[4], glow=True)
    t.rect(0, 0, 15, 1, OR[2])
    add("resin_drips", t, "ceiling", 3, True)
    # spines on the floor
    t = Tile(22, 14)
    for (x, hgt) in ((1, 8), (6, 13), (11, 10), (16, 12)):
        sp = poly(22, 14, [(x, 13), (x + 2.5, 13 - hgt), (x + 5, 13)])
        t.fill(sp, TN[5])
        t.fill(sp & (XX[:14, :22] >= x + 3), TN[3])
        t.fill(sp & (YY[:14, :22] < 13 - hgt + 3), TN[6])
    add("spines", t, "floor", 2)
    # a pile of gnawed bones
    t = Tile(28, 10)
    for (p0, p1) in (((2, 8), (20, 6)), ((8, 3), (25, 8)), ((5, 5), (14, 9))):
        t.fill(line_m(28, 10, [p0, p1], 2), TN[5])
        t.fill(line_m(28, 10, [p0, p1], 1), TN[6])
        for (x, y) in (p0, p1):
            t.fill(ellipse(28, 10, (x - 2, y - 2, x + 1, y + 1)), TN[6])
            t.px(x, y, TN[4])
    add("bones", t, "floor", 1)
    # skull of a beetle
    t = Tile(16, 12)
    sk = ellipse(16, 12, (0, 0, 15, 11))
    shade_form(t, sk, [BR[1], TN[3], TN[4], TN[5], TN[6], TN[7]], 3, spread=1.8)
    t.fill(ellipse(16, 12, (3, 3, 6, 6)), OUT)
    t.fill(ellipse(16, 12, (9, 3, 12, 6)), OUT)
    t.fill(line_m(16, 12, [(4, 9), (11, 9)]), BR[1])
    add("skull", t, "floor", 1)
    # veins on the wall
    t = Tile(26, 26)
    for j in range(3):
        pts = [(4 + j * 8 + math.sin(y * 0.3 + j * 2) * 3, y) for y in range(0, 26, 2)]
        t.fill(line_m(26, 26, pts, 1 + (j == 1)), CR[2])
        for (x, y) in pts[3::4]:
            t.fill(line_m(26, 26, [(x, y), (x + 4, y + 3)]), CR[2])
    add("veins", t, "wall", 2, outline=False)
    # cocoon stuck to the wall
    t = Tile(14, 22)
    m = ellipse(14, 22, (0, 0, 13, 21))
    shade_form(t, m, [TN[1], TN[2], TN[3], TN[4], TN[5], TN[6]], 3, spread=1.8)
    for y in range(3, 20, 3):
        t.fill(m & (YY[:22, :14] == y) & (XX[:22, :14] % 3 != 0), TN[3])
    add("cocoon", t, "wall", 1)
    # glow worms on the wall
    t = Tile(16, 12)
    for (x, y) in ((1, 2), (6, 6), (11, 3), (4, 10), (13, 9)):
        t.px(x, y, YE[6], glow=True)
        t.px(x + 1, y, OR[4], glow=True)
        t.px(x + 2, y, OR[3], glow=True)
    add("glow_worms", t, "wall", 2, True, outline=False)
    # wax comb chunk on the wall
    t = Tile(20, 18)
    for (cx, cy) in ((5, 5), (13, 5), (9, 11), (17, 11), (5, 16), (13, 16)):
        hexm = poly(20, 18, [(cx - 4, cy), (cx - 2, cy - 4), (cx + 2, cy - 4), (cx + 4, cy), (cx + 2, cy + 4),
                             (cx - 2, cy + 4)])
        t.fill(hexm, TN[5])
        inner = poly(20, 18, [(cx - 2, cy), (cx - 1, cy - 2), (cx + 1, cy - 2), (cx + 2, cy), (cx + 1, cy + 2),
                              (cx - 1, cy + 2)])
        t.fill(inner, OR[4] if (cx + cy) % 3 == 0 else OR[1], glow=(cx + cy) % 3 == 0)
    add("comb_chunk", t, "wall", 1, True)
    # tendrils over a ledge
    t = Tile(12, 26)
    for j, x in enumerate((2, 6, 9)):
        ln = 14 + j * 5
        for y in range(ln):
            xx = x + int(round(math.sin(y * 0.4 + j) * 1.2))
            t.px(xx, y, RO[2] if y % 4 else RO[3])
            t.px(xx + 1, y, CR[1])
        t.px(x, ln, YE[4], glow=True)
    add("tendrils_edge", t, "edge", 3, True, outline=False)
    # spore fungus
    t = Tile(16, 14)
    for (x, hgt, r) in ((3, 8, 3), (9, 12, 4)):
        t.rect(x, 13 - hgt, x + 1, 13, TN[4])
        cap = ellipse(16, 14, (x - r, 13 - hgt - r, x + r + 1, 13 - hgt + 2))
        t.fill(cap, LI[3])
        t.fill(cap & (YY[:14, :16] < 13 - hgt), LI[5], glow=True)
    add("fungus", t, "floor", 2, True)
    # hive pillar stump
    t = Tile(14, 22)
    m = poly(14, 22, [(1, 21), (3, 4), (6, 0), (9, 3), (12, 21)])
    shade_form(t, m, CHIT, 3, spread=2.0)
    for y in (8, 13, 18):
        t.fill(m & (YY[:22, :14] == y), CR[1])
    add("stump", t, "floor", 2)
    # egg sac on the wall, big and pulsing
    t = Tile(18, 20)
    m = ellipse(18, 20, (1, 0, 17, 19))
    shade_form(t, m, [CR[0], CR[1], RO[2], OR[3], OR[4], YE[5], YE[6]], 3, spread=2.0, glow=True)
    t.fill(ellipse(18, 20, (6, 6, 12, 13)), YE[4], glow=True)
    t.fill(ellipse(18, 20, (7, 7, 10, 10)), YE[6], glow=True)
    add("egg_sac", t, "wall", 1, True)
    return items
