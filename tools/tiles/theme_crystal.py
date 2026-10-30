"""Theme `crystal`: the crystal caverns. Dark rock studded with glowing violet and cyan crystal clusters; terrain B
are polished, faceted crystal blocks; the back wall is a deep cave wall with faint crystal glints."""
import math

import numpy as np
from scipy import ndimage

from tilelib import T, XX, YY, Tile, RAMPS, C, geom, displaced, periodic_noise, noise_1d, shade_form
from organic import StoneTex, Profiles, rock_shape, rock_fill, hang, column_rng, top_surface_y, bottom_surface_y
from parts import (box, spike_tile, door_tile, toggle_on, toggle_off, conveyor_tile, liquid_tiles, rectm, ellipse,
                   poly, finish, pad, line_m, breakable_block, crumble_block, gem_cluster)

VI = RAMPS["violet"]
PU = RAMPS["purple"]
SL = RAMPS["slate"]
CY = RAMPS["cyan"]
MG = RAMPS["magenta"]
BL = RAMPS["blue"]
ST = RAMPS["steel"]
YE = RAMPS["yellow"]
TE = RAMPS["teal"]
WH = C("white", 0)
OUT = C("outline", 0)

SEED = 6601
ROCK = [VI[0], SL[1], VI[1], SL[2], SL[3], SL[4], SL[5]]
TEX = StoneTex(SEED, n=3, aspect=1.2, keep=0.7)
PROF = Profiles(SEED + 1, top=(0.5, 2.0), bottom=(1.5, 4), side=(0, 2))
GEM_V = [VI[2], VI[3], VI[4], VI[5], PU[5], VI[6], VI[7], WH]
GEM_C = [BL[2], CY[2], CY[3], CY[4], CY[5], CY[6], CY[7], WH]
BORDER_OK = (XX >= 3) & (XX <= 28) & (YY >= 3) & (YY <= 28)


def _prism(t, cx, base_y, h, w, ramp, up=True, lean=0.0, region=None, glow=True):
    """One crystal prism: lit left facet, bright ridge, darker right facet, from base_y growing up (or down)."""
    sgn = -1 if up else 1
    tip_y = base_y + sgn * h
    tipx = cx + lean
    shoulder = base_y + sgn * (h - w * 0.7)
    pts = [(cx - w / 2, base_y), (cx - w / 2 + lean * 0.8, shoulder), (tipx, tip_y), (cx + w / 2 + lean * 0.8,
                                                                                     shoulder), (cx + w / 2, base_y)]
    m = poly(T, T, pts)
    if region is not None:
        m &= region
    rel = np.clip((YY - tip_y) / (base_y - tip_y + 1e-6), 0, 1) if up else np.clip((tip_y - YY) / (tip_y - base_y
                                                                                                 + 1e-6), 0, 1)
    mid = tipx + (cx - tipx) * rel
    n = len(ramp)
    t.fill(m, ramp[n - 5], glow)
    t.fill(m & (XX < mid + 0.5), ramp[n - 3], glow)
    t.fill(m & (XX < mid - w * 0.25), ramp[n - 2], glow)
    t.fill(m & (np.abs(XX - mid) < 0.6), ramp[n - 1], glow)
    t.fill(m & (XX > mid + w * 0.3), ramp[n - 6], glow)
    return m


PRISM_V = [VI[1], VI[2], PU[3], VI[4], PU[4], VI[5], VI[6]]
PRISM_C = [BL[1], CY[2], CY[3], TE[4], CY[4], CY[5], CY[6]]


def _cluster(t, s, v, up=True):
    rng = column_rng(SEED, v, 3 if up else 4)
    ramp = PRISM_V if v in (0, 3) else PRISM_C
    if up:
        ty = top_surface_y(s)
        x0 = int(rng.integers(8, 20))
        if ty[x0] >= 99:
            return
        by = int(ty[x0]) + 9
        for i, (dx, h, w, ln) in enumerate(((0, 11, 5, -1.5), (4, 14, 6, 0.5), (8, 8, 4, 2.0))):
            _prism(t, x0 + dx, by, h, w, ramp, True, ln)
    else:
        by_ = bottom_surface_y(s)
        x0 = int(rng.integers(8, 20))
        if by_[x0] < 0:
            return
        by = int(by_[x0]) - 6
        for (dx, h, w, ln) in ((0, 9, 5, -1.0), (5, 12, 5, 0.8), (9, 7, 4, 1.5)):
            m = _prism(t, x0 + dx, by, h, w, ramp, False, ln)


def terrain_a(m, v):
    s = rock_shape(m, v, PROF, 5)
    t = Tile()
    rock_fill(t, s, TEX, v, ROCK, 2.6, tex_amp=1.0, edge_amp=1.2, edge_w=6, deep=(10, 14, 0.5), crack=0.25,
              crack_col=VI[0], calm=(10, 22, 0.6), rim_hi=SL[5], rim_lo=VI[0])
    k = s.depth
    # crystal grit along the top
    if s.top:
        t.fill(s.solid & (s.wt > 0.5) & (k >= 1) & (k < 2), SL[3])
    # embedded glints deep in the rock
    rng = column_rng(SEED, v, 7)
    for _ in range(1 if v in (2, 3) else 0):
        x, y = int(rng.integers(5, 26)), int(rng.integers(5, 26))
        if s.solid[y, x] and k[y, x] > 4:
            ramp = GEM_C if (x + y) % 2 else GEM_V
            t.px(x, y, ramp[6], True)
            t.px(x + 1, y, ramp[4], True)
            t.px(x, y + 1, ramp[3], True)
    if v == 0 and s.top:
        _cluster(t, s, v, True)
    if v == 1 and s.bottom:
        _cluster(t, s, v, False)
    elif s.bottom:
        def dc(i, n, dx):
            return SL[2] if dx == 0 else VI[1]
        hang(t, s, v, SEED + 9, dc, count=(1, 2), length=(2, 4), width=2)
    return t


FACET = [OUT, PU[1], PU[2], VI[3], PU[3], VI[4], PU[4], VI[5], VI[6], VI[7], WH]


def terrain_b(m, v):
    """Polished crystal blocks: each cell a cut gem with bevelled facets and an inner light."""
    s = displaced(geom(m, 2, "chamfer"))
    t = Tile()
    sol, k = s.solid, s.depth
    d = np.minimum(np.minimum(XX, 31 - XX), np.minimum(YY, 31 - YY))
    top = (YY <= XX) & (YY <= 31 - XX)
    bot = (YY >= XX) & (YY >= 31 - XX)
    lft = (XX < YY) & (XX < 31 - YY)
    t.fill(sol, PU[3])
    bev = d < 6
    t.fill(sol & bev & top, VI[5])
    t.fill(sol & bev & lft, VI[4])
    t.fill(sol & bev & ~top & ~lft & ~bot, PU[2])
    t.fill(sol & bev & bot, PU[1])
    # table: inner light, a diagonal sheen
    tab = sol & ~bev
    t.fill(tab, VI[3], glow=True)
    t.fill(tab & ((XX + YY) < 28), VI[4], glow=True)
    t.fill(tab & (np.abs(XX - YY + (v - 1.5) * 4) <= 1) & (XX + YY < 44), VI[6], glow=True)
    t.fill(sol & (d == 6) & (top | lft), PU[2])
    t.fill(sol & (d == 0), PU[2])
    t.fill(sol & (d == 0) & (top | lft), VI[6])
    t.fill(sol & (np.abs(XX - YY) == 0) & bev & (XX < 6), VI[7])
    rng = column_rng(SEED, v, 12)
    for _ in range(2):
        x, y = int(rng.integers(8, 24)), int(rng.integers(8, 24))
        t.px(x, y, WH, True)
    # outer rim from the mask
    t.fill(sol & (k < 1) & (s.lit > 0.25), WH)
    t.fill(sol & (k < 1) & (s.lit < -0.3), OUT)
    return t


BACK = [OUT, VI[0], SL[1]]
BKTEX = StoneTex(SEED + 7, n=2, aspect=1.4, keep=0.5, tone=0)
BKPROF = Profiles(SEED + 8, top=(0, 3), bottom=(0, 4), side=(0, 3))


def back(m, v):
    s = rock_shape(m, v, BKPROF, 6)
    t = Tile()
    sol, k = s.solid, s.depth
    rock_fill(t, s, BKTEX, v, BACK, 1.4, tex_amp=0.5, edge_amp=0.0, deep=(99, 1, 0), crack=0.2,
              crack_col=OUT, calm=(99, 100, 0), rim=False, thr=0.45)
    rng = column_rng(SEED, v, 17)
    if v == 1:
        x, y = int(rng.integers(6, 26)), int(rng.integers(6, 26))
        if sol[y, x] and k[y, x] > 4:
            t.px(x, y, VI[4], True)
            t.px(x + 1, y + 1, VI[2], True)
    rim = sol & (k < 3.5)
    t.fill(rim, SL[1])
    t.fill(rim & (k < 2) & (s.lit > 0.3), SL[2])
    t.fill(rim & (k < 1) & (s.lit > 0.3), SL[3])
    t.fill(rim & (s.lit < -0.3) & (k < 2), VI[0])
    return t


TINTS = [
    (0, 255, 255, 255, 0, "neutral"),
    (1, 236, 214, 255, 14, "amethyst"),
    (2, 200, 236, 255, -30, "aquamarine"),
    (3, 176, 170, 210, 0, "deep"),
]


# ------------------------------------------------------------------------------------------------ small sheets


def platform():
    """A faceted crystal shelf; columns single, left end, middle, right end."""
    rows = []
    for v in range(4):
        row = []
        ramp = GEM_V
        for col in range(4):
            t = Tile()
            capl, capr = col in (0, 1), col in (0, 3)
            x0, x1 = (3 if capl else 0), (28 if capr else 31)
            t.rect(x0, 0, x1, 9, ramp[3], glow=True)
            t.rect(x0, 0, x1, 2, ramp[5], glow=True)
            t.rect(x0, 0, x1, 0, ramp[7], glow=True)
            t.rect(x0, 7, x1, 9, ramp[1], glow=True)
            t.rect(x0, 10, x1, 10, OUT)
            for fx in (7, 19) if v < 2 else (12, 25):
                if x0 <= fx <= x1:
                    t.fill(line_m(T, T, [(fx, 3), (fx + 3, 6)]) , ramp[6], glow=True)
            if capl:
                t.fill(poly(T, T, [(3, 0), (0, 5), (3, 10)]), ramp[4], glow=True)
                t.fill(poly(T, T, [(3, 0), (0, 5), (3, 5)]), ramp[6], glow=True)
            if capr:
                t.fill(poly(T, T, [(28, 0), (31, 5), (28, 10)]), ramp[2], glow=True)
            # hanging shards under it
            for (hx, ln) in ((10, 4), (21, 6)):
                if x0 <= hx <= x1:
                    t.fill(poly(T, T, [(hx - 1, 10), (hx + 2, 10), (hx + 0.5, 10 + ln)]), ramp[2], glow=True)
            row.append(t)
        rows.append(row)
    return rows


def blocks():
    ore = [VI[0], SL[1], VI[1], SL[2], SL[3], SL[4], SL[5], SL[6]]
    return [[breakable_block(v, ore, OUT, CY[5] if v % 2 else VI[5], seed=SEED + 60) for v in range(4)],
            [crumble_block(s, [VI[0], PU[1], PU[2], VI[3], VI[4], VI[5], VI[6]], top=(VI[5], VI[7]), thick=9) for s in
             range(4)],
            [door_tile(ST, BL, BL, o) for o in range(4)],
            [door_tile(ST, YE, YE, o) for o in range(4)],
            [toggle_on(VI, VI, f, SL) for f in range(4)], [toggle_off(VI, f) for f in range(4)],
            [conveyor_tile(f, SL, VI, CY, CY[6]) for f in range(4)],
            [spike_tile(d, [OUT, PU[1], VI[3], VI[4], VI[5], VI[6], VI[7], WH], SL, outline=VI[0], jag=3, seed=6,
                        n=4, height=17, tip=(None, CY[5], CY[7]), glow_tip=True) for d in ("up", "down", "left",
                                                                                        "right")]]


def liquid():
    ramp = [PU[1], PU[2], VI[3], MG[4], MG[5], MG[6]]
    return liquid_tiles(ramp, (MG[5], WH), glow=True, seed=13, line_col=VI[4], bubble_cols=(MG[5], WH))


# ------------------------------------------------------------------------------------------------------- deco


def deco():
    items = []

    def add(name, t, place, weight, glow=False, outline=True):
        if outline:
            t = finish(pad(t))
        items.append((name, t, place, weight, glow))

    for i, (w, h, ramp, n) in enumerate(((16, 18, GEM_V, 3), (24, 26, GEM_C, 4), (12, 12, GEM_V, 2),
                                         (20, 22, GEM_V, 4))):
        add("cluster_%d" % i, gem_cluster(w, h, ramp, True, seed=SEED + i, n=n), "floor", 3, True)
    for i, (w, h, ramp, n) in enumerate(((16, 16, GEM_C, 3), (22, 20, GEM_V, 4))):
        add("cluster_hang_%d" % i, gem_cluster(w, h, ramp, True, seed=SEED + 10 + i, n=n, direction="down"),
            "ceiling", 3, True)
    # geode on the wall
    t = Tile(22, 20)
    shell = ellipse(22, 20, (0, 0, 21, 19))
    shade_form(t, shell, ROCK, 3, spread=1.6)
    inner = ellipse(22, 20, (4, 4, 17, 15))
    t.fill(inner, VI[3], glow=True)
    for a in range(0, 360, 40):
        x = 10.5 + 5 * math.cos(math.radians(a))
        y = 9.5 + 4 * math.sin(math.radians(a))
        t.fill(line_m(22, 20, [(10.5, 9.5), (x, y)]) & inner, VI[5] if a < 180 else VI[4], glow=True)
    t.fill(ellipse(22, 20, (8, 7, 13, 12)), VI[6], glow=True)
    t.px(9, 8, WH, True)
    add("geode", t, "wall", 2, True)
    # glowing cave mushrooms
    t = Tile(16, 14)
    for (x, hgt, r) in ((3, 7, 3), (10, 11, 4)):
        t.rect(x, 13 - hgt, x + 1, 13, SL[4])
        cap = ellipse(16, 14, (x - r, 13 - hgt - r, x + r + 1, 13 - hgt + 2))
        t.fill(cap, TE[4], glow=True)
        t.fill(cap & (YY[:14, :16] < 13 - hgt), CY[6], glow=True)
    add("mushrooms", t, "floor", 2, True)
    # stalagmite and stalactite
    t = Tile(12, 24)
    m = poly(12, 24, [(0, 23), (5, 0), (7, 0), (11, 23)])
    shade_form(t, m, ROCK, 3, spread=2.0)
    add("stalagmite", t, "floor", 2)
    t = Tile(12, 24)
    m = poly(12, 24, [(0, 0), (11, 0), (6, 23), (5, 23)])
    shade_form(t, m, ROCK, 3, spread=2.0)
    t.px(5, 21, CY[5], True)
    add("stalactite", t, "ceiling", 3, True)
    # crystal vein on the wall
    t = Tile(26, 18)
    for (pts, c) in (([(1, 15), (9, 9), (16, 11), (25, 2)], VI[4]), ([(9, 9), (11, 16)], VI[3])):
        t.fill(line_m(26, 18, pts, 2), c, glow=True)
    for (x, y) in ((9, 8), (16, 10), (24, 2)):
        t.rect(x, y, x + 1, y + 1, VI[7], glow=True)
    add("vein", t, "wall", 2, True, outline=False)
    # floating prism shard (wall)
    t = Tile(10, 16)
    m = poly(10, 16, [(5, 0), (9, 6), (5, 15), (1, 6)])
    t.fill(m, CY[4], glow=True)
    t.fill(m & (XX[:16, :10] < 5), CY[6], glow=True)
    t.fill(m & (YY[:16, :10] > 9), CY[3], glow=True)
    t.px(4, 4, WH, True)
    add("float_shard", t, "wall", 1, True)
    # mining lamp post
    t = Tile(10, 30)
    t.rect(4, 6, 5, 29, ST[3])
    t.rect(4, 6, 4, 29, ST[5])
    t.rect(1, 27, 8, 29, ST[2])
    box(t, 1, 0, 8, 7, ST, 3, outline=False)
    t.rect(2, 2, 7, 5, YE[5], glow=True)
    t.rect(2, 2, 4, 3, YE[7], glow=True)
    add("lamp_post", t, "floor", 1, True)
    # scattered shards on the floor
    t = Tile(22, 7)
    for (x, h, c) in ((1, 4, GEM_V), (6, 6, GEM_C), (10, 3, GEM_V), (15, 5, GEM_V), (19, 3, GEM_C)):
        m = poly(22, 7, [(x, 6), (x + 1.5, 6 - h), (x + 3, 6)])
        t.fill(m, c[4], glow=True)
        t.fill(m & (XX[:7, :22] <= x + 1), c[6], glow=True)
    add("shards", t, "floor", 3, True)
    # crystal pillar (tall)
    t = Tile(14, 40)
    m = poly(14, 40, [(1, 39), (2, 6), (7, 0), (12, 6), (13, 39)])
    gx = np.mgrid[0:40, 0:14][1]
    t.fill(m, PU[3], glow=True)
    t.fill(m & (gx < 6), VI[4], glow=True)
    t.fill(m & (gx < 3), VI[5], glow=True)
    t.fill(m & (gx > 10), PU[2], glow=True)
    t.fill(m & (gx == 6), VI[7], glow=True)
    add("pillar", t, "floor", 1, True)
    # crystals over a ledge
    add("edge_crystals", gem_cluster(14, 14, GEM_C, True, seed=SEED + 30, n=3, direction="down"), "edge", 3, True)
    # survey scanner (Corps equipment)
    t = Tile(18, 16)
    box(t, 2, 6, 15, 15, ST, 3)
    t.rect(5, 8, 12, 11, BL[2], glow=True)
    t.fill(line_m(18, 16, [(5, 11), (7, 9), (9, 10), (12, 8)]), CY[6], glow=True)
    t.fill(line_m(18, 16, [(8, 6), (5, 0)]), ST[4])
    t.px(5, 0, VI[6], True)
    add("scanner", t, "floor", 1, True)
    # glints on the wall
    t = Tile(14, 12)
    for (x, y, c) in ((2, 2, CY[6]), (9, 4, VI[6]), (5, 9, VI[5]), (12, 10, CY[5])):
        t.px(x, y, c, True)
    add("glints", t, "wall", 3, True, outline=False)
    return items
