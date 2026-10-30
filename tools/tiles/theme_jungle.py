"""Theme `jungle`: Thessa, a lush alien moon. Earthy rock with roots, glowing teal moss and blue-violet foliage on top
edges, hanging roots below; terrain B are ancient ruin stones with faintly glowing inlays; the back wall is a dark
cave / foliage wall."""
import math

import numpy as np

from tilelib import T, XX, YY, Tile, RAMPS, C, geom, displaced, qidx, periodic_noise, noise_1d, rivet, despeckle
from organic import StoneTex, Profiles, rock_shape, rock_fill, hang, tufts, column_rng, top_surface_y
from parts import (box, spike_tile, door_tile, toggle_on, toggle_off, conveyor_tile, liquid_tiles, rectm, ellipse,
                   poly, finish, pad, line_m, d_pipe)

BR = RAMPS["brown"]
TN = RAMPS["tan"]
GY = RAMPS["grey"]
GR = RAMPS["green"]
TE = RAMPS["teal"]
CY = RAMPS["cyan"]
VI = RAMPS["violet"]
PU = RAMPS["purple"]
LI = RAMPS["lime"]
RO = RAMPS["rose"]
YE = RAMPS["yellow"]
OL = RAMPS["olive"]
OUT = C("outline", 0)

ROCK = [BR[0], BR[1], RO[1], BR[2], BR[3], TN[4], TN[5]]
SEED = 3301
TEX = StoneTex(SEED, n=3, aspect=1.45, keep=0.6)
PROF = Profiles(SEED + 1, top=(1.5, 3.5), bottom=(2, 6), side=(0, 2.5))
_rng = np.random.default_rng(SEED + 2)
MOSSW = [5.0 + 3.0 * (noise_1d(_rng, T, 2.5) * 0.5 + 0.5) for _ in range(4)]
SPECK = [periodic_noise(_rng, T, 1.2, 1.2) for _ in range(4)]
BTEX = StoneTex(SEED + 5, n=7, aspect=1.2, r=4.0, rough=0.1, gain=2.0)
BPROF = Profiles(SEED + 6, top=(0, 1.5), bottom=(0, 2.5), side=(0, 1.5))


def _moss(t, s, v, depth_scale=1.0):
    """Moss band on exposed tops: glowing specks, tendrils hanging into the rock, wrapping round the corners."""
    if not s.top:
        return
    k = s.depth
    w = MOSSW[v][None, :] * depth_scale
    band = s.solid & (s.wt > 0.35) & (k < w)
    t.fill(band, TE[2])
    t.fill(band & (k < w - 1.5), TE[3])
    t.fill(band & (k < 2.5), TE[4])
    t.fill(band & (k < 1), TE[5])
    t.fill(band & (s.lit < -0.2) & (k < 2.5), TE[3])
    t.fill(band & (k >= w - 1) , VI[2])
    sp = band & (SPECK[v] > 1.45) & (k >= 1) & (k < w - 1.5)
    t.fill(sp, CY[6], glow=True)
    t.fill(band & (SPECK[v] < -1.3) & (k >= 1.5) & (k < w - 1), VI[4])
    # tendrils
    rng = column_rng(SEED, v, 11)
    for x in rng.choice(np.arange(3, 29), 4, replace=False):
        yb = np.nonzero(band[:, x])[0]
        if len(yb) == 0:
            continue
        y0 = yb.max()
        for i in range(int(rng.integers(1, 5))):
            y = y0 + 1 + i
            if y < T and s.solid[y, x]:
                t.px(int(x), y, VI[2] if i < 2 else VI[1])


def _foliage(t, s, v):
    """Blue-violet leaves and glowing teal blades above the moss."""
    def col(i, n):
        if i == n - 1:
            return CY[6] if (i + v) % 2 == 0 else VI[5]
        return VI[4] if i % 2 == 0 else TE[4]
    tufts(t, s, v, SEED, col, count=(7, 11), height=(1, 4), glow_fn=lambda i, n: i == n - 1 and (i + v) % 2 == 0)


def _roots(t, s, v):
    """Roots winding through the rock under the moss, and hanging below undersides."""
    k = s.depth
    rng = column_rng(SEED, v, 21)
    if v in (0, 2):
        x = float(rng.integers(6, 24))
        y = 4.0
        pts = []
        for i in range(14):
            pts.append((x, y))
            x += rng.uniform(-1.6, 1.6)
            y += rng.uniform(1.0, 2.2)
        m = line_m(T, T, pts, 1) & s.solid & (k > 2.5) & (BORDER_OK)
        t.fill(m, BR[1])
        t.fill(np.roll(m, -1, 1) & ~m & s.solid & (k > 2.5) & BORDER_OK, BR[3])

    def rc(i, n, dx):
        return BR[3] if dx == 0 else BR[1]
    hang(t, s, v, SEED, rc, count=(2, 3), length=(4, 9), width=2, wiggle=True)
    # a glowing seed pod on some roots
    if v == 1 and s.bottom:
        def pc(i, n, dx):
            return CY[5] if i == n - 1 else BR[2]
        hang(t, s, (v + 2) % 4, SEED + 9, pc, count=(1, 1), length=(4, 6),
             glow_fn=lambda i, n: i == n - 1)


BORDER_OK = (XX >= 2) & (XX <= 29) & (YY >= 2) & (YY <= 29)


def terrain_a(m, v):
    s = rock_shape(m, v, PROF, 5)
    t = Tile()
    rock_fill(t, s, TEX, v, ROCK, 3.0, tex_amp=1.0, edge_amp=1.3, edge_w=6, deep=(10, 14, 0.6), crack=0.25,
              crack_col=BR[1], calm=(10, 22, 0.6), rim_hi=TN[5], rim_lo=BR[0])
    _roots(t, s, v)
    _moss(t, s, v)
    _foliage(t, s, v)
    return t


def terrain_b(m, v):
    """Ancient ruin masonry: grey stone blocks in running bond, carved inlays that glow faintly, moss in joints."""
    s = displaced(geom(m, 3, "chamfer"), BPROF[v])
    t = Tile()
    sol, k = s.solid, s.depth
    STN = [GY[0], GY[1], GY[2], GY[3], GY[4], GY[5], GY[6]]
    rock_fill(t, s, BTEX, v, STN, 3.0, tex_amp=0.6, edge_amp=1.1, edge_w=5, deep=(12, 16, 0.5), crack=None,
              calm=(8, 20, 0.3), rim=False)
    # running bond: blocks 32 x 16, joints at y 15 and 31, verticals at x 31 (top row) and x 15 (bottom row)
    jh = (YY == 15) | (YY == 31)
    jv = ((XX == 31) & (YY < 15)) | ((XX == 15) & (YY >= 16))
    joint = sol & (jh | jv) & (k > 1.5)
    t.fill(joint, GY[1])
    t.fill(sol & ((YY == 0) | (YY == 16)) & (k > 1.5) & ~jv, GY[4])
    t.fill(sol & (((XX == 0) & (YY < 15)) | ((XX == 16) & (YY >= 16))) & (k > 1.5), GY[4])
    t.fill(sol & ((YY == 14) | (YY == 30)) & (k > 1.5) & ~jv, GY[2])
    # moss in some joints
    mj = joint & (np.roll(SPECK[v], 3, 1) > 0.6)
    t.fill(mj, TE[2])
    # carved inlay (a glyph-free concentric motif) on one block in some variants
    if v == 1:
        for r, c in ((5, GY[1]), (3, GY[2])):
            m_ = (np.maximum(np.abs(XX - 8), np.abs(YY - 23)) == r - 1) & sol & (k > 3)
            t.fill(m_, c)
        t.fill(sol & (k > 3) & (np.abs(XX - 8) + np.abs(YY - 23) <= 1), TE[4], glow=True)
    elif v == 2:
        m_ = sol & (k > 3) & (YY == 7) & (XX >= 6) & (XX <= 25) & ((XX % 4) != 3)
        t.fill(m_, GY[1])
        t.fill(sol & (k > 3) & (YY == 8) & (XX >= 6) & (XX <= 25) & ((XX % 4) == 1), TE[3], glow=True)
    elif v == 3:
        # a crack through the lower block
        pts = [(19, 16), (21, 20), (19, 24), (22, 29)]
        cm = line_m(T, T, pts) & sol & (k > 2)
        t.fill(cm, GY[0])
        t.fill(np.roll(cm, 1, 1) & ~cm & sol & (k > 2), GY[4])
    # edges: chipped rim
    r0 = sol & (k < 1)
    t.fill(r0 & (s.lit > 0.25), GY[6])
    t.fill(r0 & (s.lit <= 0.25) & (s.lit > -0.3), GY[3])
    t.fill(r0 & (s.lit < -0.3), GY[1])
    t.fill(sol & (k >= 1) & (k < 2) & (s.lit > 0.3), GY[5])
    t.fill(sol & (k >= 1) & (k < 2) & (s.lit < -0.3), GY[2])
    if s.top:
        _moss(t, s, (v + 1) % 4, depth_scale=0.6)
        def col(i, n):
            return TE[4] if i < n - 1 else CY[6]
        tufts(t, s, v, SEED + 40, col, count=(2, 4), height=(1, 2), glow_fn=lambda i, n: i == n - 1)
    def vc(i, n, dx):
        return GR[2] if i < n - 1 else TE[3]
    hang(t, s, v, SEED + 41, vc, count=(1, 3), length=(3, 9))
    return t


BACK = [GR[0], TE[1], GR[1]]
BKTEX = StoneTex(SEED + 7, n=2, aspect=1.5, keep=0.5, tone=0)
BKPROF = Profiles(SEED + 8, top=(0, 3), bottom=(0, 4), side=(0, 3))
LEAF = [periodic_noise(np.random.default_rng(SEED + 12 + i), T, 5, 4) for i in range(4)]


def back(m, v):
    """Dark cave wall (a shadowed, flatter version of the rock) with a rocky rim and hanging vines toward the sky."""
    s = rock_shape(m, v, BKPROF, 6)
    t = Tile()
    sol, k = s.solid, s.depth
    rock_fill(t, s, BKTEX, v, BACK, 1.0, tex_amp=0.5, edge_amp=0.0, deep=(99, 1, 0), crack=0.2,
              crack_col=GR[0], calm=(99, 100, 0), rim=False, thr=0.45)
    # rim toward the sky: the rock of the cave mouth
    rim = sol & (k < 4)
    t.fill(rim, BR[1])
    t.fill(rim & (k < 2.5) & (s.lit > 0.3), RO[1])
    t.fill(rim & (k < 1) & (s.lit > 0.3), BR[2])
    t.fill(rim & (s.lit < -0.3) & (k < 2), BR[0])
    t.fill(sol & (k >= 4) & (k < 5), GR[0])
    def vc(i, n, dx):
        return GR[1] if i < n - 1 else TE[2]
    hang(t, s, v, SEED + 50, vc, count=(1, 3), length=(3, 10), wiggle=True)
    return t


TINTS = [
    (0, 255, 255, 255, 0, "neutral"),
    (1, 255, 238, 210, 10, "dusk"),
    (2, 210, 240, 255, -12, "night"),
    (3, 190, 220, 190, 0, "deep"),
]


# ------------------------------------------------------------------------------------------------ small sheets


def platform():
    """A root-bound log bridge with moss on top; columns single, left end, middle, right end."""
    rows = []
    for v in range(4):
        row = []
        for col in range(4):
            t = Tile()
            capl, capr = col in (0, 1), col in (0, 3)
            x0, x1 = (2 if capl else 0), (29 if capr else 31)
            # log body
            for y in range(2, 11):
                rel = (y - 2) / 8.0
                c = BR[4] if rel < 0.2 else BR[3] if rel < 0.55 else BR[2] if rel < 0.85 else BR[1]
                t.rect(x0, y, x1, y, c)
            # bark grain
            for i in range(6):
                gx = (i * 7 + v * 5) % 30
                t.rect(gx, 5 + (i % 3), gx + 3, 5 + (i % 3), BR[2])
            # moss top
            t.rect(x0, 0, x1, 2, TE[3])
            t.rect(x0, 0, x1, 0, TE[5])
            for x in range(x0, x1 + 1):
                if (x * 7 + v * 3) % 5 == 0:
                    t.px(x, 3, TE[2])
                if (x * 11 + v) % 9 == 0:
                    t.px(x, 1, CY[5], glow=True)
            t.rect(x0, 11, x1, 11, BR[0])
            # binding root rings
            for bx in (9, 24):
                if x0 <= bx <= x1:
                    t.rect(bx, 1, bx + 1, 11, BR[1])
                    t.rect(bx, 1, bx, 11, BR[3])
            if capl:
                t.fill(ellipse(T, T, (0, 1, 6, 11)), BR[3])
                t.fill(ellipse(T, T, (1, 3, 5, 9)), TN[4])
                t.fill(ellipse(T, T, (2, 4, 4, 8)), TN[3])
                t.px(3, 6, BR[2])
            if capr:
                t.fill(ellipse(T, T, (25, 1, 31, 11)), BR[2])
                t.fill(ellipse(T, T, (26, 3, 30, 9)), TN[3])
                t.fill(ellipse(T, T, (27, 4, 29, 8)), TN[2])
            if v == 2:
                for x in (6, 15, 22):
                    if x0 <= x <= x1:
                        t.rect(x, 12, x, 12 + (x % 5), GR[2])
            row.append(t)
        rows.append(row)
    return rows


def _boulder(t, x0, y0, x1, y1, ramp, base, seed):
    m = ellipse(T, T, (x0, y0, x1, y1))
    from tilelib import shade_form
    shade_form(t, m, ramp, base, spread=1.8, round_=True)
    return m


def breakable(v):
    """A cracked clay-and-root block (lighter than the rock) with a glowing fissure."""
    t = Tile()
    box(t, 0, 0, 31, 31, TN, 3, outline=True)
    rng = np.random.default_rng(SEED + 70 + v)
    h = periodic_noise(rng, T, 3, 3)
    t.fill(rectm(T, T, 2, 2, 29, 29) & (h > 0.9), TN[4])
    t.fill(rectm(T, T, 2, 2, 29, 29) & (h < -0.9), TN[2])
    pts = [[(6, 4), (12, 12), (10, 19), (17, 26)], [(26, 5), (19, 13), (21, 20), (13, 27)],
           [(4, 16), (12, 14), (17, 18), (27, 15)], [(15, 3), (13, 12), (19, 18), (16, 28)]][v]
    cm = line_m(T, T, pts, 2) & rectm(T, T, 2, 2, 29, 29)
    t.fill(cm, BR[1])
    t.fill(line_m(T, T, pts, 1) & rectm(T, T, 2, 2, 29, 29), LI[4], glow=True)
    t.rect(1, 1, 30, 1, TN[5])
    return t


def crumble(stage):
    """A slab of mossy stone on its last legs."""
    t = Tile()
    pieces = [(0, 15), (16, 31)] if stage < 3 else [(0, 9), (11, 20), (22, 31)]
    for i, (a, b) in enumerate(pieces):
        dy = 0 if stage < 3 else [3, 6, 2][i]
        dx = 0 if stage < 3 else [-1, 0, 1][i]
        box(t, a + dx, dy, b + dx, 12 + dy, GY, 3, outline=True)
        t.rect(a + dx + 1, dy, b + dx - 1, dy + 1, TE[3])
        t.rect(a + dx + 1, dy, b + dx - 1, dy, TE[5])
    if stage >= 1:
        t.fill(line_m(T, T, [(9, 2), (12, 7), (10, 11)]), GY[0])
    if stage >= 2:
        t.fill(line_m(T, T, [(22, 2), (19, 7), (23, 11)]), GY[0])
        t.fill(line_m(T, T, [(15, 3), (16, 12)]), GY[0])
    if stage == 3:
        for (x, y) in ((12, 22), (20, 26), (5, 27), (27, 24)):
            t.rect(x, y, x + 1, y + 1, GY[3])
            t.px(x + 1, y + 1, GY[1])
    return t


def blocks():
    return [[breakable(v) for v in range(4)], [crumble(s) for s in range(4)],
            [door_tile(GY, RAMPS["blue"], RAMPS["blue"], o) for o in range(4)],
            [door_tile(GY, YE, YE, o) for o in range(4)],
            [toggle_on(TE, CY, f, GY) for f in range(4)], [toggle_off(CY, f) for f in range(4)],
            [conveyor_tile(f, GY, BR, CY, LI[4]) for f in range(4)],
            [spike_tile(d, [OUT, BR[1], BR[2], BR[3], TN[4], TN[5], TN[6], TN[7]], BR, outline=BR[0], jag=3,
                        seed=5, n=4, height=16) for d in ("up", "down", "left", "right")]]


def liquid():
    ramp = [GR[1], GR[2], LI[2], LI[3], LI[4], LI[5]]
    return liquid_tiles(ramp, (LI[4], LI[6]), glow=True, seed=7, line_col=GR[3], bubble_cols=(LI[3], LI[5]))


# ------------------------------------------------------------------------------------------------------- deco


def deco():
    from parts import d_lamp
    from tilelib import shade_form
    items = []

    def add(name, t, place, weight, glow=False, outline=True):
        if outline:
            t = finish(pad(t))
        items.append((name, t, place, weight, glow))

    rng = np.random.default_rng(SEED + 90)
    # glowing mushrooms
    for i, (w, h) in enumerate(((14, 14), (20, 18))):
        t = Tile(w, h)
        for j in range(2 + i):
            cx = 3 + j * (w - 6) // max(1, 1 + i)
            ch = h - 2 - j * 3
            t.rect(cx, h - ch // 2, cx + 1, h - 1, TN[5])
            t.rect(cx + 1, h - ch // 2, cx + 1, h - 1, TN[4])
            cap = ellipse(w, h, (cx - 3, h - ch // 2 - 4, cx + 4, h - ch // 2 + 1))
            t.fill(cap, CY[4], glow=True)
            t.fill(cap & (YY[:h, :w] < h - ch // 2 - 2), CY[6], glow=True)
            t.fill(cap & (YY[:h, :w] >= h - ch // 2), TE[2])
        add("mushrooms_%d" % i, t, "floor", 3, True)
    # violet fern
    t = Tile(22, 20)
    for j, ang in enumerate((-1.2, -0.7, -0.25, 0.25, 0.7, 1.2)):
        pts = [(11 + math.sin(ang) * r * 1.0, 19 - math.cos(ang) * r) for r in range(0, 18, 2)]
        t.fill(line_m(22, 20, pts, 2), VI[3] if j % 2 else VI[4])
        for (x, y) in pts[2::2]:
            t.px(int(x) + (1 if ang > 0 else -1), int(y), VI[5])
    t.px(11, 3, VI[6])
    add("fern", t, "floor", 3)
    # glow grass tuft
    t = Tile(16, 10)
    for x in range(1, 15, 2):
        hgt = 3 + (x * 5) % 6
        t.rect(x, 9 - hgt, x, 9, TE[3])
        t.px(x, 9 - hgt, CY[6], glow=True)
    add("grass", t, "floor", 4, True)
    # big alien flower
    t = Tile(18, 28)
    t.fill(line_m(18, 28, [(9, 27), (8, 18), (10, 10)], 2), GR[3])
    for a in range(5):
        ang = a * 2 * math.pi / 5 - math.pi / 2
        pet = ellipse(18, 28, (9 + math.cos(ang) * 5 - 3, 8 + math.sin(ang) * 5 - 3, 9 + math.cos(ang) * 5 + 3,
                               8 + math.sin(ang) * 5 + 3))
        t.fill(pet, PU[4] if a % 2 else PU[5])
    t.fill(ellipse(18, 28, (7, 6, 12, 11)), YE[5], glow=True)
    t.px(8, 7, YE[7], glow=True)
    t.fill(ellipse(18, 28, (2, 19, 8, 23)), GR[3])
    t.fill(ellipse(18, 28, (10, 15, 16, 19)), GR[4])
    add("flower", t, "floor", 1, True)
    # hanging vines (ceiling)
    for i, n in enumerate((3, 5)):
        w, h = 6 + n * 3, 18 + i * 12
        t = Tile(w, h)
        for j in range(n):
            x = 2 + j * 3
            ln = int(h * (0.5 + 0.5 * rng.random()))
            for y in range(ln):
                xx = x + int(round(math.sin(y * 0.4 + j) * 0.8))
                t.px(xx, y, GR[2] if y % 4 else GR[3])
                if y % 5 == 2:
                    t.px(xx + 1, y, VI[4])
                    t.px(xx - 1, y + 1, VI[3])
            t.px(x, ln, CY[6], glow=True)
        add("vines_%d" % i, t, "ceiling", 3, True, outline=False)
    # hanging glow pods (ceiling)
    t = Tile(12, 20)
    t.fill(line_m(12, 20, [(6, 0), (5, 9)], 1), BR[2])
    pod = ellipse(12, 20, (1, 8, 10, 19))
    shade_form(t, pod, [TE[1], TE[2], TE[3], CY[4], CY[5], CY[6]], 3, spread=2.0, glow=True)
    add("glowpod", t, "ceiling", 2, True)
    # vines over a ledge
    t = Tile(14, 30)
    for j, x in enumerate((2, 6, 10)):
        ln = 18 + (j * 7) % 12
        for y in range(ln):
            xx = x + int(round(math.sin(y * 0.35 + j * 2)))
            t.px(xx, y, GR[3] if y % 3 else TE[3])
            if y % 6 == 3:
                t.px(xx - 1, y, VI[4])
                t.px(xx + 1, y + 1, VI[3])
    add("vines_edge", t, "edge", 4, outline=False)
    # ancient carved stone stele (glyph-free spiral motif)
    t = Tile(16, 30)
    box(t, 0, 2, 15, 29, GY, 3)
    t.fill(poly(16, 30, [(0, 3), (8, 0), (15, 3)]), GY[4])
    for r in (5, 3, 1):
        ring = (np.maximum(np.abs(XX[:30, :16] - 7.5), np.abs(YY[:30, :16] - 13)) == r + 0.5)
        t.fill(ring, GY[1])
    t.fill((np.abs(XX[:30, :16] - 7.5) < 1) & (np.abs(YY[:30, :16] - 13) < 1), TE[5], glow=True)
    t.rect(3, 22, 12, 22, GY[1])
    t.rect(3, 25, 12, 25, GY[1])
    t.rect(1, 26, 14, 29, TE[2])
    add("stele", t, "floor", 1, True)
    # broken pillar stub
    t = Tile(14, 20)
    box(t, 0, 4, 13, 19, GY, 3)
    t.fill(poly(14, 20, [(0, 4), (4, 1), (7, 3), (10, 0), (13, 4)]), GY[3])
    t.rect(2, 7, 2, 18, GY[5])
    t.rect(6, 7, 6, 18, GY[2])
    t.rect(10, 7, 10, 18, GY[2])
    t.rect(0, 16, 13, 19, TE[2])
    t.rect(0, 16, 13, 16, TE[4])
    add("pillar_stub", t, "floor", 2)
    # bones of a beast
    t = Tile(26, 12)
    t.fill(ellipse(26, 12, (0, 4, 10, 11)), TN[6])
    t.fill(ellipse(26, 12, (3, 6, 6, 9)), BR[1])
    for x in (12, 16, 20):
        t.fill(line_m(26, 12, [(x, 11), (x + 2, 3)], 2), TN[5])
    t.rect(9, 9, 25, 10, TN[5])
    t.rect(9, 9, 25, 9, TN[6])
    add("bones", t, "floor", 1)
    # roots on the wall
    t = Tile(24, 28)
    for j in range(4):
        pts = [(4 + j * 5 + math.sin(y * 0.3 + j) * 2, y) for y in range(0, 28, 2)]
        t.fill(line_m(24, 28, pts, 2 if j % 2 else 1), BR[1] if j % 2 else BR[2])
    add("roots_wall", t, "wall", 2, outline=False)
    # glowing fungus shelf on the wall
    t = Tile(16, 10)
    for j, (x, y, w) in enumerate(((0, 0, 9), (5, 4, 10), (2, 7, 7))):
        sh = ellipse(16, 10, (x, y, x + w, y + 4)) & (YY[:10, :16] <= y + 2)
        t.fill(sh, CY[4], glow=True)
        t.fill(sh & (YY[:10, :16] == y + 2), TE[3])
        t.fill(sh & (YY[:10, :16] == y), CY[6], glow=True)
    add("fungus_shelf", t, "wall", 2, True)
    # firefly cluster (tiny lights on the wall)
    t = Tile(14, 12)
    for (x, y) in ((2, 3), (7, 1), (11, 6), (4, 9), (9, 10)):
        t.px(x, y, LI[5], glow=True)
        t.px(x + 1, y, LI[3], glow=True)
    add("fireflies", t, "wall", 2, True, outline=False)
    # moss-covered boulder
    t = Tile(22, 16)
    b = ellipse(22, 16, (0, 2, 21, 15))
    shade_form(t, b, ROCK, 3, spread=2.0)
    t.fill(b & (YY[:16, :22] < 6), TE[3])
    t.fill(b & (YY[:16, :22] < 4), TE[4])
    t.px(7, 3, CY[6], glow=True)
    add("boulder", t, "floor", 2)
    # crashed survey probe (a hint of the Corps)
    t = Tile(20, 14)
    box(t, 2, 4, 17, 13, GY, 4)
    t.rect(5, 6, 9, 9, RAMPS["blue"][3], glow=True)
    t.rect(5, 6, 9, 6, RAMPS["blue"][5], glow=True)
    t.fill(line_m(20, 14, [(14, 4), (18, 0)], 1), GY[5])
    t.px(18, 0, RAMPS["red"][4], glow=True)
    t.rect(0, 11, 19, 13, TE[3])
    add("probe", t, "floor", 1, True)
    # spider-silk curtain in a corner (ceiling)
    t = Tile(16, 14)
    for j in range(5):
        t.fill(line_m(16, 14, [(j * 3 + 1, 0), (j * 3 + 2, 6 + j % 3 * 3)]), GY[5])
    t.fill(line_m(16, 14, [(0, 4), (15, 6)]), GY[4])
    add("silk", t, "ceiling", 1, outline=False)
    return items
