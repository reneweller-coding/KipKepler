"""Theme `ice`: the comet mines of Ysk. Packed snow / ice rock with thick frost caps and icicles under the ledges;
terrain B are clear, slippery blue ice blocks; the back wall is a frozen mine wall (timber and steel supports come as
deco)."""
import math

import numpy as np
from scipy import ndimage

from tilelib import T, XX, YY, Tile, RAMPS, C, geom, displaced, periodic_noise, noise_1d, shade_form, rivet
from organic import StoneTex, Profiles, rock_shape, rock_fill, hang, tufts, column_rng
from parts import (box, spike_tile, door_tile, toggle_on, toggle_off, conveyor_tile, liquid_tiles, rectm, ellipse,
                   poly, finish, pad, line_m, breakable_block, crumble_block, gem_cluster, d_crate, d_pipe)

IC = RAMPS["ice"]
SL = RAMPS["slate"]
BL = RAMPS["blue"]
CY = RAMPS["cyan"]
ST = RAMPS["steel"]
BR = RAMPS["brown"]
TN = RAMPS["tan"]
OR = RAMPS["orange"]
YE = RAMPS["yellow"]
RD = RAMPS["red"]
WH = C("white", 0)
OUT = C("outline", 0)

SEED = 5501
ROCK = [SL[0], SL[1], IC[1], IC[2], IC[3], IC[4], IC[5]]
TEX = StoneTex(SEED, n=3, aspect=1.3, keep=0.7)
PROF = Profiles(SEED + 1, top=(0.5, 2.0), bottom=(3, 6), side=(0, 2))
_rng = np.random.default_rng(SEED + 2)
SNOWW = [3.6 + 2.4 * (noise_1d(_rng, T, 4.0) * 0.5 + 0.5) for _ in range(4)]
SPARK = [periodic_noise(_rng, T, 1.0, 1.0) for _ in range(4)]
BORDER_OK = (XX >= 3) & (XX <= 28) & (YY >= 3) & (YY <= 28)


def _snow(t, s, v, scale=1.0):
    """A thick frost cap: bright top, cold blue underside with a lumpy edge."""
    if not s.top:
        return
    k = s.depth
    w = SNOWW[v][None, :] * scale
    band = s.solid & (s.wt > 0.3) & (k < w)
    t.fill(band, IC[6])
    t.fill(band & (k >= w - 1.3), IC[5])
    t.fill(band & (k >= w - 0.6), IC[4])
    t.fill(band & (k < 1.6), IC[7])
    t.fill(band & (k < 0.8) & (s.lit > 0.2), WH)
    t.fill(band & (s.lit < -0.25) & (k < 2), IC[5])
    t.fill(band & (SPARK[v] > 1.7) & (k >= 1.6) & (k < w - 1.3), WH)


def _icicles(t, s, v, seed, count=(2, 4), length=(3, 9)):
    def ic(i, n, dx):
        if i == n - 1:
            return IC[7]
        return IC[6] if dx == 0 else IC[4]
    hang(t, s, v, seed, ic, count=count, length=length, width=2)


ICEA = [SL[0], SL[1], IC[2], IC[3], IC[4], IC[5], IC[6], IC[7]]
# strata of packed ice: the same wavy lines in every variant, so they run on across tiles
_X = np.arange(T)
STRATA = []
for (_y0, _ph, _amp) in ((4, 0.0, 1.4), (13, 2.2, 1.1), (22, 4.1, 1.6)):
    STRATA.append(np.round(_y0 + _amp * np.sin(2 * math.pi * _X / 32.0 + _ph)
                           + 0.7 * np.sin(4 * math.pi * _X / 32.0 + _ph * 1.7)).astype(int))


def terrain_a(m, v):
    """Packed snow-ice: bright and dense, with wavy strata that run on across tiles, a few inclusions per variant,
    a lit rim, a thick frost cap on top and icicles under ledges."""
    s = rock_shape(m, v, PROF, 5)
    t = Tile()
    sol, k, lit = s.solid, s.depth, s.lit
    near = np.clip(1 - (k - 1) / 6.0, 0, 1)
    val = 4.0 + near * lit * 1.3
    t.fill_idx(sol, ICEA, np.clip(np.floor(val + 0.5), 0, 7).astype(int))
    inner = sol & (k > 2.5)
    for i, yy in enumerate(STRATA):
        y = yy[None, :]
        t.fill(inner & (YY == y), IC[5])
        t.fill(inner & (YY == y + 1), IC[3] if i != 1 else IC[4])
    # sparse snow grains between the strata
    t.fill(inner & (SPARK[v] > 2.1), IC[5])
    # inclusions only near the surfaces: deep inside big masses the ice stays calm
    deep = inner & (k > 4) & (k < 13) & BORDER_OK
    rng = column_rng(SEED, v, 4)
    if v == 1:
        # dark rock pebbles frozen in
        for _ in range(2):
            x, y = int(rng.integers(5, 23)), int(rng.integers(6, 22))
            peb = ellipse(T, T, (x, y, x + 5, y + 3)) & deep
            t.fill(peb, IC[2])
            t.fill(peb & (YY <= y + 1), IC[3])
            t.fill(peb & (YY == y + 3), SL[2])
    elif v == 2:
        for _ in range(4):
            x, y = int(rng.integers(5, 26)), int(rng.integers(5, 26))
            if deep[y, x]:
                t.px(x, y, IC[7])
                t.px(x + 1, y + 1, IC[3])
    elif v == 3:
        x0, y0 = int(rng.integers(6, 12)), int(rng.integers(8, 14))
        pts = [(x0, y0), (x0 + 6, y0 + 4), (x0 + 9, y0 + 3), (x0 + 15, y0 + 9)]
        vm = line_m(T, T, pts) & deep
        t.fill(vm, IC[3])
        t.fill(np.roll(vm, -1, 0) & ~vm & deep, IC[6])
    # rim: bright toward the light, cold blue-black on the shadow side
    r0 = sol & (k < 1)
    t.fill(r0 & (lit > 0.25), IC[7])
    t.fill(r0 & (lit < -0.3), SL[1])
    t.fill(sol & (k >= 1) & (k < 2) & (lit < -0.5), IC[2])
    _snow(t, s, v)
    _icicles(t, s, v, SEED + 3)
    return t


ICEB = [BL[2], BL[3], IC[3], IC[4], IC[5], IC[6], IC[7]]
STREAKS = {0: [(4, 20, 12)], 1: [(14, 28, 9)], 2: [], 3: [(6, 26, 14), (16, 30, 6)]}


def terrain_b(m, v):
    """Clear blue ice: one bevelled block per cell, glossy streaks, trapped bubbles and white cracks."""
    s = displaced(geom(m, 2, "chamfer"))
    t = Tile()
    sol, k = s.solid, s.depth
    t.fill(sol, IC[3])
    t.fill(sol & (YY + XX < 22), IC[4])
    t.fill(sol & (YY + XX > 40), BL[3])
    # block seams (each cell one block)
    t.fill(sol & ((XX == 0) | (YY == 0)), IC[6])
    t.fill(sol & ((XX == 31) | (YY == 31)), BL[2])
    t.fill(sol & ((XX == 30) | (YY == 30)) & (XX > 0) & (YY > 0), IC[3])
    # glossy diagonal streaks
    for (a, b, ln) in STREAKS[v]:
        sm = sol & (np.abs((XX + YY) - b) <= 1) & (XX >= a) & (XX <= a + ln) & (k > 2)
        t.fill(sm, IC[6])
        t.fill(sol & (np.abs((XX + YY) - b) == 0) & (XX >= a + 1) & (XX <= a + ln - 2) & (k > 2), IC[7])
    # bubbles
    rng = column_rng(SEED, v, 9)
    for _ in range(3):
        x, y = int(rng.integers(5, 26)), int(rng.integers(5, 26))
        if sol[y, x] and k[y, x] > 3:
            t.px(x, y, IC[7])
            t.px(x + 1, y + 1, IC[3])
    if v == 2:
        cm = line_m(T, T, [(9, 22), (14, 17), (13, 12), (19, 8)]) & sol & (k > 3)
        t.fill(cm, IC[7])
    # outer rim
    t.fill(sol & (k < 1) & (s.lit > 0.25), WH)
    t.fill(sol & (k < 1) & (s.lit <= 0.25) & (s.lit > -0.3), IC[6])
    t.fill(sol & (k < 1) & (s.lit < -0.3), BL[2])
    t.fill(sol & (k >= 1) & (k < 2) & (s.lit > 0.3), IC[6])
    t.fill(sol & (k >= 1) & (k < 2) & (s.lit < -0.3), BL[3])
    if s.top:
        _snow(t, s, (v + 2) % 4, scale=0.55)
    _icicles(t, s, v, SEED + 13, count=(1, 3), length=(2, 6))
    return t


BACK = [SL[0], SL[1], IC[1]]
BKTEX = StoneTex(SEED + 7, n=2, aspect=1.4, keep=1.0, tone=0)
BKPROF = Profiles(SEED + 8, top=(0, 3), bottom=(0, 4), side=(0, 3))


BOARD_JOINTS = {0: (9, 23, 4, 17), 1: (20, 6, 27, 12), 2: (14, 28, 10, 3), 3: (5, 18, None, 25)}


def back(m, v):
    """Frozen mine wall: dark, cold timber lagging (horizontal boards, a board missing here and there showing the
    black rock behind), frost along the board edges; a snowy rim toward the sky. Low contrast, so it reads as
    behind; the vertical supports come as deco."""
    s = rock_shape(m, v, BKPROF, 6)
    t = Tile()
    sol, k = s.solid, s.depth
    row = YY // 8
    by = YY % 8
    t.fill(sol, SL[1])
    t.fill(sol & (by == 0), SL[2])
    t.fill(sol & (by == 7), SL[0])
    # grain: a few dark streaks per board
    grain = ((XX * 7 + row * 13 + v * 5) % 23 < 5) & (by == 3 + (row % 2))
    t.fill(sol & grain, SL[0])
    # board joints (inside the tile) with a nail on each side
    for r, jx in enumerate(BOARD_JOINTS[v]):
        rows = sol & (row == r)
        if jx is None:
            # a missing board: black rock with a glint of ice
            t.fill(rows & (by < 7), SL[0])
            t.fill(rows & (by == 1) & (XX % 9 == 4), IC[1])
            continue
        t.fill(rows & (XX == jx) & (by < 7), SL[0])
        t.fill(rows & (XX == jx + 1) & (by > 0) & (by < 7), SL[2])
        for nx in (jx - 2, jx + 3):
            if 0 <= nx < T:
                t.fill(rows & (XX == nx) & (by == 3), SL[3])
    # frost on the top edges of the boards, sparse
    t.fill(sol & (by == 0) & (SPARK[v] > 0.9), IC[1])
    rim = sol & (k < 3.5)
    t.fill(rim, IC[1])
    t.fill(rim & (k < 2) & (s.lit > 0.3), IC[3])
    t.fill(rim & (k < 1) & (s.lit > 0.3), IC[4])
    t.fill(rim & (s.lit < -0.3) & (k < 2), SL[0])
    t.fill(sol & (k >= 3.5) & (k < 4.5), SL[0])

    def ic(i, n, dx):
        return IC[2] if i < n - 1 else IC[3]
    hang(t, s, v, SEED + 50, ic, count=(1, 3), length=(2, 6))
    return t


TINTS = [
    (0, 255, 255, 255, 0, "neutral"),
    (1, 255, 236, 220, 6, "lamplit"),
    (2, 205, 228, 255, -10, "glacial"),
    (3, 176, 186, 214, 0, "deep"),
]


# ------------------------------------------------------------------------------------------------ small sheets


def platform():
    """A mine scaffold plank, snow on top, iron brackets, little icicles underneath."""
    rows = []
    WOOD = [BR[0], BR[1], BR[2], BR[3], BR[4], TN[5], TN[6]]
    for v in range(4):
        row = []
        for col in range(4):
            t = Tile()
            capl, capr = col in (0, 1), col in (0, 3)
            x0, x1 = (1 if capl else 0), (30 if capr else 31)
            t.rect(x0, 3, x1, 9, WOOD[3])
            t.rect(x0, 3, x1, 3, WOOD[4])
            t.rect(x0, 9, x1, 9, WOOD[1])
            t.rect(x0, 10, x1, 10, OUT)
            for i in range(5):
                gx = (i * 7 + v * 3) % 28 + 1
                t.rect(gx, 5 + i % 3, gx + 4, 5 + i % 3, WOOD[2])
            # plank joints
            for jx in (15,) if v % 2 == 0 else (7, 23):
                t.rect(jx, 3, jx, 9, WOOD[1])
                t.rect(jx + 1, 4, jx + 1, 8, WOOD[4])
            # snow
            t.rect(x0, 0, x1, 2, IC[6])
            t.rect(x0, 0, x1, 0, IC[7])
            for x in range(x0, x1 + 1):
                if (x * 5 + v) % 7 == 0:
                    t.px(x, 3, IC[5])
            # iron brackets
            for bx in (4, 26):
                if (bx == 4 and capl) or (bx == 26 and capr) or col == 2:
                    t.rect(bx, 2, bx + 2, 12, ST[2])
                    t.rect(bx, 2, bx, 12, ST[4])
                    t.px(bx + 1, 5, ST[6])
            for (ix, ln) in ((9, 3), (19, 4), (28, 2)):
                if x0 <= ix <= x1:
                    t.rect(ix, 11, ix, 11 + ln, IC[5])
                    t.px(ix, 11 + ln, IC[7])
            if capl:
                t.rect(0, 0, 0, 9, IC[6])
            if capr:
                t.rect(31, 0, 31, 9, IC[5])
            row.append(t)
        rows.append(row)
    return rows


def blocks():
    return [[breakable_block(v, [SL[0], SL[1], IC[2], IC[3], IC[4], IC[5], IC[6], IC[7]], SL[1], IC[7], seed=SEED + 60,
                             face=4) for v in range(4)],
            [crumble_block(s, [SL[1], IC[2], IC[3], IC[4], IC[5], IC[6], IC[7]], top=(IC[6], WH), face=3, thick=9) for
             s in range(4)],
            [door_tile(ST, BL, BL, o) for o in range(4)],
            [door_tile(ST, YE, YE, o) for o in range(4)],
            [toggle_on(CY, CY, f, ST) for f in range(4)], [toggle_off(CY, f) for f in range(4)],
            [conveyor_tile(f, ST, SL, CY, YE[4]) for f in range(4)],
            [spike_tile(d, [OUT, BL[2], IC[3], IC[4], IC[5], IC[6], IC[7], WH], ST, outline=BL[1], jag=3, seed=4,
                        n=4, height=17) for d in ("up", "down", "left", "right")]]


def liquid():
    ramp = [SL[1], IC[2], IC[3], IC[4], IC[5], IC[6]]
    rows = liquid_tiles(ramp, (IC[6], WH), glow=False, seed=11, line_col=IC[3], bubble_cols=(IC[5], IC[7]))
    # floating ice floes on the surface frames
    for f, st in enumerate(rows[0]):
        for (x0, w) in ((3, 8), (19, 6)):
            xs = (x0 + f * 2) % T
            for dx in range(w):
                x = (xs + dx) % T
                ys = np.nonzero(st.a[:, x])[0]
                if len(ys):
                    y = ys.min()
                    st.px(x, max(0, y - 1), IC[7])
                    st.px(x, y, IC[6])
                    st.px(x, y + 1, IC[4])
    return rows


# ------------------------------------------------------------------------------------------------------- deco


def deco():
    items = []

    def add(name, t, place, weight, glow=False, outline=True):
        if outline:
            t = finish(pad(t))
        items.append((name, t, place, weight, glow))

    WOOD = [BR[0], BR[1], BR[2], BR[3], BR[4], TN[5], TN[6]]
    # mining lantern on the wall (warm light)
    t = Tile(10, 16)
    t.rect(4, 0, 5, 2, ST[3])
    box(t, 1, 2, 8, 4, ST, 3, outline=False)
    t.rect(2, 5, 7, 12, OR[4], glow=True)
    t.rect(3, 6, 5, 10, YE[5], glow=True)
    t.px(3, 6, YE[7], glow=True)
    t.rect(1, 5, 1, 12, ST[2])
    t.rect(8, 5, 8, 12, ST[2])
    box(t, 1, 13, 8, 15, ST, 3, outline=False)
    add("lantern", t, "wall", 3, True)
    # hanging lantern on a chain (ceiling)
    t = Tile(10, 22)
    for y in range(0, 8, 2):
        t.px(5, y, ST[4])
        t.px(5, y + 1, ST[2])
    t.blit(items[-1][1], -1, 6)
    add("lantern_hanging", t, "ceiling", 2, True, outline=False)
    # timber support frame (two posts and a beam)
    t = Tile(40, 56)
    for x in (2, 32):
        t.rect(x, 4, x + 5, 55, WOOD[3])
        t.rect(x, 4, x + 1, 55, WOOD[4])
        t.rect(x + 5, 4, x + 5, 55, WOOD[1])
        for y in range(10, 55, 9):
            t.rect(x + 2, y, x + 4, y, WOOD[2])
    t.rect(0, 0, 39, 6, WOOD[3])
    t.rect(0, 0, 39, 1, WOOD[5])
    t.rect(0, 6, 39, 6, WOOD[1])
    t.rect(0, 0, 39, 0, IC[7])
    for x in (4, 34):
        rivet(t, x, 2, (ST[1], ST[4], ST[6]))
    for (ix, ln) in ((10, 4), (20, 6), (27, 3)):
        t.rect(ix, 7, ix, 7 + ln, IC[5])
        t.px(ix, 7 + ln, IC[7])
    add("support_timber", t, "wall", 3)
    # steel support arch
    t = Tile(40, 56)
    for x in (2, 33):
        t.rect(x, 6, x + 4, 55, ST[3])
        t.rect(x, 6, x, 55, ST[5])
        t.rect(x + 4, 6, x + 4, 55, ST[1])
        t.rect(x + 2, 6, x + 2, 55, ST[2])
    t.rect(0, 0, 39, 6, ST[3])
    t.rect(0, 0, 39, 0, ST[5])
    t.rect(0, 6, 39, 6, ST[1])
    for x in range(4, 37, 6):
        rivet(t, x, 2, (ST[1], ST[4], ST[6]))
    t.rect(0, 0, 39, 0, IC[7])
    add("support_steel", t, "wall", 2)
    # mine cart
    t = Tile(28, 20)
    body = poly(28, 20, [(0, 3), (27, 3), (24, 15), (3, 15)])
    shade_form(t, body, [OUT, RD[1], RD[2], RD[3], RD[4], RD[5]], 3, spread=1.0, round_=False)
    t.rect(0, 3, 27, 4, ST[4])
    t.fill(ellipse(28, 20, (2, 0, 25, 8)) & (YY[:20, :28] < 4), SL[2])
    for (gx, c) in ((6, IC[4]), (12, CY[5]), (17, IC[3])):
        t.fill(ellipse(28, 20, (gx, 0, gx + 5, 5)) & (YY[:20, :28] < 4), c)
    for cx in (7, 20):
        w = ellipse(28, 20, (cx - 4, 12, cx + 4, 19))
        t.fill(w, ST[1])
        t.fill(ellipse(28, 20, (cx - 2, 14, cx + 2, 17)), ST[4])
    add("mine_cart", t, "floor", 2)
    # pickaxe and shovel leaning
    t = Tile(16, 26)
    t.fill(line_m(16, 26, [(3, 25), (8, 2)], 2), WOOD[3])
    t.fill(poly(16, 26, [(2, 4), (8, 1), (14, 4), (8, 3)]), ST[4])
    t.fill(line_m(16, 26, [(12, 25), (10, 6)], 1), WOOD[4])
    t.fill(poly(16, 26, [(8, 18), (13, 18), (13, 25), (8, 25)]), ST[3])
    add("tools", t, "floor", 2)
    # crates and barrels
    add("crate", d_crate(20, 16, WOOD, 3), "floor", 3)
    t = d_pipe(12, 16, WOOD, horizontal=False, base=3)
    t.rect(0, 3, 11, 3, ST[2])
    t.rect(0, 12, 11, 12, ST[2])
    t.rect(0, 0, 11, 0, IC[7])
    add("barrel", t, "floor", 2)
    # glowing ore vein on the wall
    t = Tile(24, 16)
    for (pts, c) in (([(1, 12), (8, 8), (14, 9), (22, 3)], CY[4]), ([(8, 8), (10, 14)], CY[3])):
        t.fill(line_m(24, 16, pts, 2), c, glow=True)
    for (x, y) in ((8, 7), (14, 8), (21, 3)):
        t.rect(x, y, x + 1, y + 1, CY[6], glow=True)
    add("ore_vein", t, "wall", 2, True, outline=False)
    # ice crystal cluster
    add("ice_crystals", gem_cluster(18, 18, [BL[2], IC[3], IC[4], IC[5], IC[6], IC[7], WH], glow=False, seed=3),
        "floor", 3)
    # icicle bunch (ceiling)
    t = Tile(18, 16)
    for (x, ln) in ((1, 9), (5, 15), (9, 7), (13, 12)):
        sp = poly(18, 16, [(x, 0), (x + 3, 0), (x + 1.5, ln)])
        t.fill(sp, IC[5])
        t.fill(sp & (XX[:16, :18] <= x + 1), IC[7])
    add("icicles", t, "ceiling", 4)
    # icicles over a ledge
    t = Tile(12, 14)
    t.rect(0, 0, 11, 1, IC[7])
    for (x, ln) in ((1, 8), (5, 13), (8, 6)):
        sp = poly(12, 14, [(x, 1), (x + 3, 1), (x + 1.5, ln)])
        t.fill(sp, IC[5])
        t.fill(sp & (XX[:14, :12] <= x + 1), IC[7])
    add("icicles_edge", t, "edge", 3)
    # frozen pipe
    t = d_pipe(32, 8, ST, True, flanges=(6, 22))
    t.rect(0, 0, 31, 0, IC[7])
    t.fill(rectm(32, 8, 0, 1, 31, 1) & ((XX[:8, :32] % 5) < 3), IC[6])
    for (ix, ln) in ((10, 4), (17, 6)):
        pass
    add("pipe_frozen", t, "wall", 2)
    # warning sign: a falling-rock triangle (no letters)
    t = Tile(18, 16)
    tri = poly(18, 16, [(9, 0), (17, 15), (0, 15)])
    t.fill(tri, YE[4])
    t.fill(poly(18, 16, [(9, 3), (14, 13), (4, 13)]), YE[5])
    t.fill(ellipse(18, 16, (6, 7, 10, 11)), OUT)
    t.fill(ellipse(18, 16, (10, 10, 13, 13)), OUT)
    t.rect(0, 15, 17, 15, YE[2])
    add("sign_rocks", t, "wall", 1)
    # snow drift
    t = Tile(26, 8)
    drift = ellipse(26, 16, (0, 0, 25, 15))[:8]
    t.fill(drift, IC[6])
    t.fill(drift & (YY[:8, :26] < 2), IC[7])
    t.fill(drift & (YY[:8, :26] > 5), IC[5])
    add("snow_drift", t, "floor", 3)
    # rail track piece
    t = Tile(32, 6)
    for x in range(1, 32, 6):
        t.rect(x, 3, x + 3, 5, WOOD[2])
        t.rect(x, 3, x + 3, 3, WOOD[3])
    t.rect(0, 1, 31, 2, ST[4])
    t.rect(0, 1, 31, 1, ST[6])
    add("rails", t, "floor", 1)
    # drill rig
    t = Tile(22, 28)
    box(t, 2, 12, 19, 27, [OUT, OR[1], OR[2], OR[3], OR[4], OR[5], OR[6], OR[7]], 3)
    t.rect(5, 15, 16, 18, ST[2])
    t.rect(6, 16, 9, 16, CY[5], glow=True)
    t.fill(poly(22, 28, [(8, 12), (14, 12), (11, 0)]), ST[4])
    t.fill(poly(22, 28, [(11, 12), (14, 12), (11, 0)]), ST[2])
    for y in (3, 6, 9):
        t.rect(9, y, 13, y, ST[1])
    add("drill", t, "floor", 1, True)
    # frost fern on the wall
    t = Tile(16, 16)
    for a in np.linspace(-1.2, 1.2, 5):
        pts = [(8 + math.sin(a) * r, 15 - math.cos(a) * r) for r in range(0, 14, 2)]
        t.fill(line_m(16, 16, pts), IC[5])
        for (x, y) in pts[2::2]:
            t.px(int(x) + 1, int(y), IC[6])
    add("frost_fern", t, "wall", 2, outline=False)
    # frozen bones
    t = Tile(24, 10)
    t.fill(ellipse(24, 10, (0, 2, 9, 9)), TN[6])
    t.fill(ellipse(24, 10, (3, 4, 5, 6)), SL[1])
    t.rect(8, 7, 23, 8, TN[5])
    t.rect(8, 7, 23, 7, TN[6])
    t.rect(0, 0, 23, 1, IC[7])
    t.clear(rectm(24, 10, 0, 0, 23, 1) & ~ellipse(24, 10, (0, 0, 23, 6)))
    add("bones", t, "floor", 1)
    return items
