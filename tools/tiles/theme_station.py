"""Theme `station`: the Academy ring's interior. Brushed steel-blue panels, rivets, seams, teal light strips, hazard
stripes at ledge ends; terrain B are darker machinery blocks; the back wall is panelled with recessed lights."""
import math

import numpy as np

from tilelib import (T, XX, YY, Tile, RAMPS, C, geom, displaced, qidx, seamless_variants, periodic_noise, rivet,
                     hazard, inset_rect, bevel_rect, edge_bands)

ST = RAMPS["steel"]
SL = RAMPS["slate"]
TE = RAMPS["teal"]
YE = RAMPS["yellow"]
OR = RAMPS["orange"]
OUT = C("outline", 0)

_rng = np.random.default_rng(7101)
STREAK = seamless_variants(_rng, 4, sx=16, sy=0.5, band=(1.0, 6.0))
BLOT = seamless_variants(_rng, 4, sx=9, sy=9, band=(2.0, 9.0))


def rim_shade(lit, hi=7, lo=1):
    """Shade index of the outermost edge pixel by its facing."""
    return np.where(lit > 0.62, hi, np.where(lit > 0.25, hi - 1, np.where(lit > -0.25, (hi + lo) // 2,
                    np.where(lit > -0.62, lo + 1, lo))))


SEAM_X = {0: 9, 1: 22, 2: None, 3: 15}


def plates(t, region, v, face=3, hi=4, lo=2, seam=1, deep=None):
    """Brick-bond wall plates: a horizontal joint at the bottom of every tile, one vertical joint per variant."""
    sx = SEAM_X[v]
    t.fill(region & (YY == 0), ST[hi])
    t.fill(region & (YY == 30), ST[lo])
    t.fill(region & (YY == 31), ST[seam])
    if sx is not None:
        t.fill(region & (XX == sx) & (YY < 31), ST[seam])
        t.fill(region & (XX == sx + 1) & (YY < 30) & (YY > 0), ST[hi])
        t.fill(region & (XX == sx - 1) & (YY < 30) & (YY > 0), ST[lo])


def terrain_a(m, v):
    g = displaced(geom(m, 3, "chamfer"))
    t = Tile()
    sol, k, lit = g.solid, g.depth, g.lit
    ke = k * (1 - 0.22 * g.wt)  # bands are a bit thicker on top

    # plate face: flat steel with sparse brush streaks
    t.fill(sol, ST[3])
    t.fill(sol & (STREAK[v] > 1.9) & (YY > 1) & (YY < 29), ST[4])
    plates(t, sol, v)
    inner = sol & (ke >= 4.5)
    rc = (ST[1], ST[4], ST[6])
    sx = SEAM_X[v]
    if sx is not None:
        for (x, y) in ((sx - 4, 3), (sx + 3, 3), (sx - 4, 25), (sx + 3, 25)):
            rivet(t, x, y, rc, clip=inner)
    elif v == 2 and k[16, 16] < 18:
        # service hatch with a teal status lamp
        inset_rect(t, 9, 8, 22, 21, ST[3], ST[1], ST[4], clip=inner)
        t.rect(11, 10, 20, 10, ST[2], clip=inner)
        lamp = inner & (XX == 19) & (YY == 18)
        t.fill(lamp, TE[6], glow=True)

    # caps along exposed edges (light from the top left)
    edge_bands(t, g, k, {
        "t": [ST[6], ST[5], ST[4], ST[4], ST[2], ST[1]],
        "l": [ST[5], ST[4], ST[4], ST[2], ST[1]],
        "r": [ST[1], ST[2], ST[2], ST[2], ST[1]],
        "b": [ST[0], ST[1], ST[2], ST[2], ST[1]],
    })
    # bolts in the side trims
    for side, xb in (("l", 1), ("r", 30)):
        if (side == "l" and g.left) or (side == "r" and g.right):
            for yb in range(7, 30, 8):
                if sol[yb, xb] and k[yb, xb] >= 0.5 and k[yb, xb] < 3 and (g.wl[yb, xb] > 0.6 or g.wr[yb, xb] > 0.6):
                    t.px(xb, yb, ST[6] if side == "l" else ST[4])
                    t.px(xb, yb + 1, ST[1])
    # hazard stripes under the floor cap towards ledge ends
    if g.top:
        endzone = np.zeros((T, T), bool)
        if g.left:
            endzone |= XX < 14
        if g.right:
            endzone |= XX > 17
        cap = sol & endzone & (YY >= 6) & (YY <= 10)
        if g.left:
            cap &= XX >= 5
        if g.right:
            cap &= XX <= 26
        hz = cap & (YY >= 7) & (YY <= 9)
        hazard(t, hz, YE[4], ST[0], period=6, slope=-1)
        t.fill(cap & ((YY == 6) | (YY == 10)), ST[1])
    # recessed ceiling lamps on exposed undersides
    if g.bottom:
        bot = sol & (g.wb > 0.6)
        t.fill(bot & (XX >= 7) & (XX <= 24) & (k >= 3) & (k < 7), ST[1])
        lm = bot & (XX >= 8) & (XX <= 23) & (k >= 4) & (k < 6)
        t.fill(lm, TE[5], glow=True)
        t.fill(lm & (k < 5) & (XX > 8) & (XX < 23), TE[7], glow=True)
    return t


def terrain_b(m, v):
    """Machinery blocks / crates: darker slate housings, each cell a module with a frame."""
    g = displaced(geom(m, 2, "chamfer"))
    t = Tile()
    sol, k, lit = g.solid, g.depth, g.lit
    val = 2.4 + 0.18 * BLOT[(v + 2) % 4]
    near = np.clip(1 - (k - 3) / 8, 0, 1)
    val = val + near * lit * 0.7 - np.clip((k - 8) / 12, 0, 1) * 0.6
    t.fill_idx(sol, SL, qidx(val, 8, 0.4))
    inner = sol & (k >= 3.5)
    # module frame inside each cell (machinery blocks are bolted together cell by cell)
    fr = (XX <= 1) | (XX >= 30) | (YY <= 1) | (YY >= 30)
    t.fill(inner & fr, SL[2])
    t.fill(inner & ((XX == 0) | (YY == 0)), SL[3])
    t.fill(inner & ((XX == 31) | (YY == 31)), SL[1])
    rc = (SL[1], ST[3], ST[5])
    if v == 0:
        # cross-braced crate face
        for i in range(4, 28):
            for w in (0, 1):
                for (x, y) in ((i + w, i), (31 - i - w, i)):
                    if inner[y, x]:
                        t.px(x, y, SL[3] if w == 0 else SL[1])
        for (x, y) in ((3, 3), (27, 3), (3, 27), (27, 27)):
            rivet(t, x, y, rc, clip=inner)
    elif v == 1:
        # intake vent with slats
        inset_rect(t, 5, 6, 26, 25, SL[1], C("outline", 0), SL[3], clip=inner)
        for yy in range(8, 25, 3):
            t.rect(7, yy, 24, yy, SL[3], clip=inner)
            t.rect(7, yy + 1, 24, yy + 1, SL[2], clip=inner)
        for (x, y) in ((3, 3), (27, 3)):
            rivet(t, x, y, rc, clip=inner)
    elif v == 2:
        # power module: conduit + amber indicator
        inset_rect(t, 5, 5, 26, 26, SL[2], SL[1], SL[3], clip=inner)
        t.rect(8, 14, 23, 17, ST[2], clip=inner)
        t.rect(8, 14, 23, 14, ST[4], clip=inner)
        t.rect(8, 17, 23, 17, ST[1], clip=inner)
        for x in (11, 16, 21):
            t.rect(x, 13, x, 18, SL[1], clip=inner)
        t.rect(8, 8, 10, 9, OR[4], glow=True, clip=inner)
        t.px(8, 8, OR[6], glow=bool(inner[8, 8]))
        t.rect(13, 8, 15, 9, SL[1], clip=inner)
    else:
        # hazard-marked heavy block
        inset_rect(t, 4, 4, 27, 27, SL[2], SL[1], SL[3], clip=inner)
        hz = inner & (XX >= 6) & (XX <= 25) & (YY >= 21) & (YY <= 24)
        hazard(t, hz, YE[3], SL[0], period=6, slope=1)
        for (x, y) in ((7, 7), (23, 7)):
            rivet(t, x, y, rc, clip=inner)
        t.rect(9, 11, 22, 16, SL[3], clip=inner)
        t.rect(9, 16, 22, 16, SL[1], clip=inner)
        t.rect(9, 11, 22, 11, SL[4], clip=inner)
    band = sol & (k < 3.5)
    sh = np.clip(np.round(3 + 1.6 * lit), 1, 5).astype(int)
    t.fill_idx(band & (k >= 1), SL, sh)
    t.fill_idx(band & (k >= 2.5), SL, np.where(lit > 0.3, 1, 0))
    t.fill_idx(band & (k < 1), SL, rim_shade(lit, 6, 0))
    if g.top:
        hz = sol & (g.wt > 0.6) & (k >= 1) & (k < 2.5)
        t.fill(hz, ST[5])
    return t


def back(m, v):
    """Panelled back wall: tall dark panels with a joint every tile, recessed lights; a frame toward open sky."""
    g = displaced(geom(m, 4, "chamfer"))
    t = Tile()
    sol, k, lit = g.solid, g.depth, g.lit
    inner = sol & (k > 4)
    t.fill(sol, ST[1])
    t.fill(sol & (XX == 31), SL[0])
    t.fill(sol & (XX == 0), ST[2])
    t.fill(sol & (XX == 30), SL[1])
    if v == 1:
        # recessed light slit
        t.rect(8, 5, 23, 7, SL[0], clip=inner)
        t.rect(9, 6, 22, 6, TE[2], glow=True, clip=inner)
        t.rect(11, 6, 20, 6, TE[3], glow=True, clip=inner)
        t.rect(8, 8, 23, 8, ST[2], clip=inner)
    elif v == 2:
        t.rect(1, 21, 29, 21, SL[0], clip=inner)
        t.rect(1, 22, 29, 22, ST[2], clip=inner)
    elif v == 3:
        for y in (4, 27):
            t.px(3, y, ST[2])
            t.px(3, y + 1, SL[0])
            t.px(27, y, ST[2])
            t.px(27, y + 1, SL[0])
    # frame toward the sky
    edge_bands(t, g, k, {
        "t": [ST[4], ST[3], ST[2], ST[2], SL[0]],
        "l": [ST[3], ST[3], ST[2], ST[2], SL[0]],
        "r": [SL[0], ST[1], ST[2], ST[2], SL[0]],
        "b": [SL[0], ST[1], ST[2], ST[2], SL[0]],
    })
    return t


TINTS = [
    (0, 255, 255, 255, 0, "neutral"),
    (1, 255, 236, 214, 0, "warm"),
    (2, 214, 232, 255, -8, "cold"),
    (3, 176, 182, 205, 0, "dim"),
]


# ------------------------------------------------------------------------------------------------ small sheets
from parts import (box, spike_tile, door_tile, toggle_on, toggle_off, conveyor_tile, liquid_tiles, rectm, ellipse,  # noqa
                   poly, finish, d_lamp, d_pipe, d_crate, d_screen, d_porthole, line_m, grid)
from tilelib import shade_form  # noqa: E402

BL = RAMPS["blue"]
CY = RAMPS["cyan"]
RD = RAMPS["red"]
GR = RAMPS["green"]


def platform():
    """Catwalk: a grated top plate on a truss; columns single, left end, middle, right end; rows are variants."""
    rows = []
    for v in range(4):
        row = []
        for col in range(4):
            t = Tile()
            capl = col in (0, 1)
            capr = col in (0, 3)
            x0 = 2 if capl else 0
            x1 = 29 if capr else 31
            # truss under the plate
            for x in range(x0, x1 + 1):
                ph = (x % 16)
                yy = 7 + (ph if ph < 8 else 15 - ph) * 5 // 7
                for d in (0, 1):
                    if 7 <= yy + d <= 12:
                        t.px(x, yy + d, ST[2] if d else ST[3])
            t.rect(x0, 12, x1, 13, ST[2])
            t.rect(x0, 12, x1, 12, ST[3])
            t.rect(x0, 14, x1, 14, ST[0])
            # top plate with grate slots
            t.rect(x0, 0, x1, 5, ST[4])
            t.rect(x0, 0, x1, 0, ST[6])
            t.rect(x0, 1, x1, 1, ST[5])
            t.rect(x0, 5, x1, 5, ST[1])
            t.rect(x0, 6, x1, 6, ST[0])
            slots = (YY >= 2) & (YY <= 3) & ((XX % 4) == 1) & (XX >= x0 + 2) & (XX <= x1 - 2)
            t.fill(slots, ST[1])
            t.fill(slots & (YY == 3), ST[2])
            if v == 1:
                t.rect(13, 4, 18, 4, TE[5], glow=True)
            elif v == 2:
                hz = (YY == 4) & (XX >= x0 + 1) & (XX <= x1 - 1)
                hazard(t, hz, YE[4], ST[1], period=4)
            elif v == 3:
                t.px(8, 4, OR[4], glow=True)
                t.px(23, 4, OR[4], glow=True)
            # end brackets
            if capl:
                box(t, 0, 0, 4, 9, ST, 4, outline=True)
                t.rect(1, 9, 3, 14, ST[2])
                t.rect(1, 9, 1, 14, ST[3])
                t.rect(0, 15, 4, 15, ST[0])
            if capr:
                box(t, 27, 0, 31, 9, ST, 4, outline=True)
                t.rect(28, 9, 30, 14, ST[2])
                t.rect(28, 9, 28, 14, ST[3])
                t.rect(27, 15, 31, 15, ST[0])
            row.append(t)
        rows.append(row)
    return rows


def _crack(t, pts, dark, light, clip=None):
    m = line_m(T, T, pts, 1)
    if clip is not None:
        m &= clip
    t.fill(m, dark)
    lm = np.roll(m, 1, axis=1) & ~m
    if clip is not None:
        lm &= clip
    t.fill(lm, light)


def breakable(v):
    """A dented service crate, marked with orange corner tags, cracked."""
    t = Tile()
    box(t, 0, 0, 31, 31, SL, 3, outline=True)
    box(t, 3, 3, 28, 28, SL, 2, outline=False)
    for (x, y) in ((1, 1), (25, 1), (1, 25), (25, 25)):
        t.rect(x, y, x + 5, y + 5, OR[3])
        t.rect(x, y, x + 5, y, OR[5])
        t.rect(x + 5, y + 1, x + 5, y + 5, OR[1])
        t.rect(x, y + 5, x + 4, y + 5, OR[2])
    cracks = [
        [(6, 9), (12, 13), (11, 18), (17, 22), (24, 21)],
        [(25, 7), (19, 12), (20, 17), (13, 21), (8, 26)],
        [(7, 15), (13, 15), (16, 10), (22, 14), (26, 12)],
        [(15, 5), (14, 11), (19, 16), (16, 23), (18, 27)],
    ][v]
    _crack(t, cracks, OUT, SL[4], clip=rectm(T, T, 3, 3, 28, 28))
    t.fill(line_m(T, T, cracks[1:3], 1) & rectm(T, T, 4, 4, 27, 27) & (XX % 3 == 0), SL[1])
    return t


def crumble(stage):
    """A thin floor plate on weak struts: intact, cracking, cracking more, falling apart."""
    t = Tile()
    pieces = [(0, 15), (16, 31)] if stage < 3 else [(0, 9), (11, 20), (22, 31)]
    for i, (a, b) in enumerate(pieces):
        dy = 0 if stage < 3 else [3, 6, 2][i]
        dx = 0 if stage < 3 else [-1, 0, 1][i]
        box(t, a + dx, dy, b + dx, 13 + dy, ST, 3, outline=True)
        t.rect(a + dx + 1, dy + 1, b + dx - 1, dy + 1, ST[5])
        for x in range(a + 3, b - 1, 4):
            t.px(x + dx, 7 + dy, ST[1])
            t.px(x + dx, 8 + dy, ST[2])
        if stage < 3:
            t.rect(a + 4, 14, a + 5, 26, ST[2])
            t.rect(a + 4, 14, a + 4, 26, ST[3])
            t.rect(a + 2, 27, a + 7, 29, ST[2])
            t.rect(a + 2, 27, a + 7, 27, ST[4])
    if stage >= 1:
        _crack(t, [(9, 1), (12, 6), (10, 12)], OUT, ST[5])
    if stage >= 2:
        _crack(t, [(22, 1), (19, 7), (23, 12)], OUT, ST[5])
        _crack(t, [(15, 2), (16, 13)], OUT, ST[5])
        for (x, y) in ((6, 16), (24, 18)):
            t.px(x, y, ST[3])
    if stage == 3:
        for (x, y) in ((12, 22), (20, 26), (5, 27), (27, 24)):
            t.rect(x, y, x + 1, y + 1, ST[3])
            t.px(x + 1, y + 1, ST[1])
    return t


def blocks():
    rows = [[breakable(v) for v in range(4)], [crumble(s) for s in range(4)],
            [door_tile(ST, BL, BL, o) for o in range(4)], [door_tile(ST, YE, YE, o) for o in range(4)],
            [toggle_on(TE, TE, f, ST) for f in range(4)], [toggle_off(TE, f) for f in range(4)],
            [conveyor_tile(f, SL, ST, TE, YE[4]) for f in range(4)],
            [spike_tile(d, ST, SL, outline=ST[0]) for d in ("up", "down", "left", "right")]]
    return rows


def liquid():
    ramp = [TE[1], TE[2], TE[3], CY[4], CY[5], CY[6]]
    return liquid_tiles(ramp, (CY[5], CY[7]), glow=True, seed=3, line_col=TE[3], bubble_cols=(CY[4], CY[6]))


# ------------------------------------------------------------------------------------------------------- deco
from parts import pad  # noqa: E402

TN = RAMPS["tan"]


def _cyl(w, h, ramp, base=3):
    return d_pipe(w, h, ramp, horizontal=False, base=base)


def deco():
    items = []

    def add(name, t, place, weight, glow=False, outline=True):
        if outline:
            t = finish(pad(t))
        items.append((name, t, place, weight, glow))

    # wall lamp
    t = Tile(12, 9)
    box(t, 0, 0, 11, 8, ST, 3)
    t.rect(2, 5, 9, 6, TE[5], glow=True)
    t.rect(3, 5, 8, 5, TE[7], glow=True)
    t.rect(2, 2, 9, 2, ST[5])
    add("lamp_wall", t, "wall", 3, True)
    # ceiling strip lamp
    t = Tile(26, 7)
    box(t, 0, 0, 25, 4, ST, 3)
    t.rect(2, 4, 23, 5, TE[5], glow=True)
    t.rect(3, 5, 22, 5, TE[7], glow=True)
    t.rect(4, 6, 21, 6, TE[3], glow=True)
    add("lamp_ceiling", t, "ceiling", 4, True)
    # vent grille
    t = Tile(22, 14)
    box(t, 0, 0, 21, 13, ST, 2)
    for y in range(3, 11, 2):
        t.rect(3, y, 18, y, ST[0])
        t.rect(3, y + 1, 18, y + 1, ST[3])
    add("vent", t, "wall", 4)
    # pipes
    add("pipe_h", d_pipe(32, 8, ST, True, flanges=(4, 25)), "wall", 2)
    add("pipe_v", d_pipe(8, 32, ST, False, flanges=(3, 24)), "wall", 2)
    t = Tile(24, 10)
    t.blit(d_pipe(24, 8, SL, True, flanges=(9,), base=3), 0, 1)
    wheel = ellipse(24, 10, (13, 0, 21, 8)) & ~ellipse(24, 10, (15, 2, 19, 6))
    t.fill(wheel, RD[3])
    t.fill(wheel & (YY[:10, :24] < 3), RD[5])
    t.px(17, 4, RD[2])
    add("pipe_valve", t, "wall", 1)
    # screens
    add("screen_graph", d_screen(28, 18, ST, TE, "graph", 2), "wall", 2, True)
    add("screen_bars", d_screen(22, 16, ST, CY, "bars", 5), "wall", 2, True)
    add("screen_radar", d_screen(20, 18, ST, GR, "radar", 1), "wall", 1, True)
    # porthole onto space
    add("porthole", d_porthole(26, ST), "wall", 2)
    # arrow sign (glyph-free icon)
    t = Tile(18, 12)
    box(t, 0, 0, 17, 11, SL, 1)
    arrow = poly(18, 12, [(3, 5), (10, 5), (10, 2), (15, 6), (10, 10), (10, 7), (3, 7)])
    t.fill(arrow, TE[5], glow=True)
    t.fill(arrow & (YY[:12, :18] <= 5), TE[7], glow=True)
    add("sign_arrow", t, "wall", 2, True)
    # Beacon Corps banner: a lighthouse with a beam (no letters)
    t = Tile(22, 30)
    t.rect(0, 0, 21, 1, ST[4])
    t.rect(0, 0, 21, 0, ST[6])
    cloth = poly(22, 30, [(2, 2), (19, 2), (19, 26), (11, 22), (2, 26)])
    t.fill(cloth, BL[2])
    t.fill(cloth & (XX[:30, :22] <= 3), BL[3])
    t.fill(cloth & (XX[:30, :22] >= 18), BL[1])
    # beams to both sides, lamp room, tapering striped tower, base
    t.fill(poly(22, 30, [(11, 8), (3, 5), (3, 10)]), BL[4])
    t.fill(poly(22, 30, [(11, 8), (19, 5), (19, 10)]), BL[4])
    t.fill(poly(22, 30, [(10, 7), (12, 7), (12, 9), (10, 9)]), YE[6])
    t.rect(9, 6, 13, 6, YE[3])
    t.rect(9, 10, 13, 10, YE[3])
    tower = poly(22, 30, [(9.5, 11), (12.5, 11), (14, 20), (8, 20)])
    t.fill(tower, C("white", 0))
    t.fill(tower & ((YY[:30, :22] // 3) % 2 == 0), RD[3])
    t.fill(tower & (XX[:30, :22] >= 12), BL[1])
    t.rect(6, 20, 16, 21, YE[3])
    add("banner_corps", t, "wall", 1)
    # recruitment poster: a beacon beam over the ring (abstract)
    t = Tile(18, 24)
    box(t, 0, 0, 17, 23, TN, 6)
    t.rect(2, 2, 15, 21, BL[1])
    t.fill(ellipse(18, 24, (-6, 14, 23, 30)) & rectm(18, 24, 2, 2, 15, 21), BL[3])
    t.fill(poly(18, 24, [(8, 12), (15, 5), (15, 9)]), YE[5])
    t.rect(7, 11, 9, 14, YE[4])
    t.px(4, 4, C("white", 0))
    t.px(12, 16, C("white", 0))
    add("poster", t, "wall", 1)
    # crates
    add("crate", d_crate(22, 18, SL, 3), "floor", 3)
    add("crate_small", d_crate(14, 12, ST, 3, brace=False, band=OR[3]), "floor", 3)
    # canister
    t = _cyl(10, 18, RD, 3)
    t.rect(0, 0, 9, 1, ST[4])
    t.rect(3, 0, 6, 0, ST[6])
    t.rect(0, 6, 9, 7, YE[4])
    t.rect(0, 7, 9, 7, YE[2])
    add("canister", t, "floor", 2)
    # console with sloped screen
    t = Tile(28, 20)
    box(t, 0, 8, 27, 19, ST, 3)
    t.fill(poly(28, 20, [(3, 8), (24, 8), (21, 0), (6, 0)]), ST[2])
    scr = poly(28, 20, [(6, 6), (21, 6), (19, 1), (8, 1)])
    t.fill(scr, CY[2], glow=True)
    t.fill(scr & ((YY[:20, :28] % 2) == 0), CY[3], glow=True)
    t.rect(9, 3, 14, 3, CY[6], glow=True)
    for i, c in enumerate((RD[4], YE[4], GR[4], TE[5])):
        t.rect(4 + i * 5, 11, 6 + i * 5, 12, c, glow=True)
    t.rect(4, 15, 23, 15, ST[1])
    add("console", t, "floor", 2, True)
    # potted alien plant
    t = Tile(16, 24)
    pot = poly(16, 24, [(3, 16), (12, 16), (11, 23), (4, 23)])
    t.fill(pot, TN[3])
    t.fill(pot & (XX[:24, :16] <= 5), TN[4])
    t.fill(pot & (XX[:24, :16] >= 10), TN[2])
    t.rect(3, 16, 12, 16, TN[5])
    for (pts, c) in (([(7, 16), (3, 6), (1, 2)], GR[3]), ([(8, 16), (9, 4), (12, 0)], GR[4]),
                     ([(8, 16), (13, 9), (15, 7)], GR[3]), ([(7, 16), (5, 9), (6, 3)], GR[5])):
        t.fill(line_m(16, 24, pts, 2) & ~pot, c)
    for (x, y) in ((1, 2), (12, 0), (15, 7)):
        t.px(x, y, TE[6], glow=True)
    add("plant", t, "floor", 2)
    # locker
    t = Tile(14, 30)
    box(t, 0, 0, 13, 29, ST, 3)
    t.rect(6, 2, 6, 27, ST[1])
    for x in (2, 8):
        for y in (3, 5, 7):
            t.rect(x, y, x + 3, y, ST[1])
    t.rect(4, 14, 4, 17, ST[6])
    t.rect(8, 14, 8, 17, ST[6])
    add("locker", t, "floor", 2)
    # server rack with LEDs
    t = Tile(18, 30)
    box(t, 0, 0, 17, 29, SL, 2)
    for i, y in enumerate(range(3, 27, 4)):
        t.rect(2, y, 15, y + 2, SL[1])
        t.rect(2, y, 15, y, SL[3])
        for j, x in enumerate((4, 7, 10)):
            c = (GR[5], TE[5], OR[4], GR[5])[(i + j) % 4]
            t.px(x, y + 1, c, glow=True)
    add("server", t, "floor", 2, True)
    # drooping cables from the ceiling
    t = Tile(44, 10)
    for (a, b, dip, c) in ((2, 41, 7, SL[2]), (6, 37, 4, BL[2]), (2, 30, 8, RD[2])):
        pts = [(a + (b - a) * i / 16.0, 1 + dip * (1 - ((i - 8) / 8.0) ** 2)) for i in range(17)]
        t.fill(line_m(44, 10, pts, 2), c)
    t.rect(0, 0, 5, 1, ST[3])
    t.rect(38, 0, 43, 1, ST[3])
    add("cables", t, "ceiling", 2)
    # rotating warning light
    t = Tile(10, 9)
    box(t, 0, 0, 9, 2, ST, 3)
    dome = ellipse(10, 9, (1, 1, 8, 9)) & (YY[:9, :10] >= 3)
    t.fill(dome, OR[4], glow=True)
    t.fill(dome & (XX[:9, :10] <= 4), OR[6], glow=True)
    t.px(3, 4, OR[7], glow=True)
    add("warnlight", t, "ceiling", 1, True)
    # wall fan
    t = Tile(22, 22)
    box(t, 0, 0, 21, 21, ST, 2)
    ring = ellipse(22, 22, (2, 2, 19, 19))
    t.fill(ring, ST[0])
    for a in range(3):
        ang = a * 2 * math.pi / 3
        bl = poly(22, 22, [(10.5, 10.5), (10.5 + 8 * math.cos(ang), 10.5 + 8 * math.sin(ang)),
                           (10.5 + 7 * math.cos(ang + 0.8), 10.5 + 7 * math.sin(ang + 0.8))])
        t.fill(bl & ring, ST[3])
    t.fill(ellipse(22, 22, (8, 8, 13, 13)), ST[4])
    t.px(9, 9, ST[6])
    add("fan", t, "wall", 2)
    # cables hanging over a ledge
    t = Tile(10, 26)
    for (x, ln, c) in ((2, 23, SL[2]), (5, 17, BL[2]), (7, 21, SL[3])):
        t.rect(x, 0, x + 1, ln, c)
        t.rect(x - 1, ln, x + 2, ln + 1, ST[3])
    add("edge_cables", t, "edge", 2)
    # bench
    t = Tile(30, 10)
    box(t, 0, 0, 29, 3, ST, 4)
    t.rect(3, 4, 5, 9, ST[2])
    t.rect(24, 4, 26, 9, ST[2])
    t.rect(3, 4, 3, 9, ST[3])
    t.rect(24, 4, 24, 9, ST[3])
    add("bench", t, "floor", 1)
    # coolant bottle on a bracket
    t = Tile(9, 16)
    t.blit(_cyl(7, 13, RD, 3), 1, 3)
    t.rect(3, 0, 5, 2, ST[3])
    t.rect(0, 8, 8, 9, ST[2])
    add("bottle", t, "wall", 1)
    return items
