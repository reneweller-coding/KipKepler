"""Theme `hull`: the ring's outer hull in open space. Big painted armour plates with heavy bolts, scorch marks and a
red-orange Academy stripe along the tops; terrain B are orange construction girders with see-through truss holes;
the back wall is a dark bulkhead (mostly the sky shows here)."""
import math

import numpy as np

from tilelib import (T, XX, YY, Tile, RAMPS, C, geom, displaced, qidx, seamless_variants, periodic_noise, rivet,
                     hazard, inset_rect, edge_bands, shade_form)
from parts import (box, spike_tile, door_tile, toggle_on, toggle_off, conveyor_tile, liquid_tiles, rectm, ellipse,
                   poly, finish, pad, line_m, breakable_block, crumble_block, d_pipe, d_crate)

GY = RAMPS["grey"]
ST = RAMPS["steel"]
SL = RAMPS["slate"]
OR = RAMPS["orange"]
RD = RAMPS["red"]
YE = RAMPS["yellow"]
BR = RAMPS["brown"]
BL = RAMPS["blue"]
CY = RAMPS["cyan"]
VI = RAMPS["violet"]
WH = C("white", 0)
OUT = C("outline", 0)

SEED = 2201
_rng = np.random.default_rng(SEED)
SCORCH = seamless_variants(_rng, 4, sx=7, sy=5, band=(2.0, 10.0))
GRIME = seamless_variants(_rng, 4, sx=2, sy=2, band=(1.0, 5.0))
SEAM = {0: (True, True), 1: (False, True), 2: (True, False), 3: (False, False)}


def bolt(t, x, y, clip):
    """A heavy 3x3 hull bolt."""
    pts = [(x + 1, y, GY[6]), (x, y + 1, GY[6]), (x + 1, y + 1, GY[5]), (x + 2, y + 1, GY[3]), (x + 1, y + 2, GY[3]),
           (x + 2, y + 2, GY[2]), (x, y + 2, GY[4]), (x + 2, y, GY[4]), (x + 3, y + 2, GY[1]), (x + 2, y + 3, GY[1])]
    for (px, py, c) in pts:
        if 0 <= px < T and 0 <= py < T and clip[py, px]:
            t.px(px, py, c)


def terrain_a(m, v):
    g = displaced(geom(m, 4, "chamfer"))
    t = Tile()
    sol, k, lit = g.solid, g.depth, g.lit
    # painted armour: light grey plates, faint grime, scorch patches
    t.fill(sol, GY[4])
    # soft vertical shading per plate: lighter top, a darker band near the bottom joint
    t.fill(sol & (YY >= 22), GY[4])
    t.fill(sol & (YY >= 24) & (((XX + YY) % 2) == 0) & (YY < 26), GY[3])
    t.fill(sol & (YY >= 26), GY[3])
    t.fill(sol & (YY <= 3), GY[5])
    sc = (SCORCH[v] if v in (1, 3) else SCORCH[v] - 0.6) - np.clip((k - 10) / 10, 0, 1) * 1.5
    t.fill(sol & (sc > 1.1), GY[3])
    t.fill(sol & (sc > 1.45), BR[2])
    t.fill(sol & (sc > 1.85), GY[1])
    inner = sol & (k >= 5.5)
    sr, sb = SEAM[v]
    if sr:
        t.fill(inner & (XX == 31), GY[1])
        t.fill(inner & (XX == 30), GY[2])
        t.fill(inner & (XX == 29), GY[3])
    if sb:
        t.fill(inner & (YY == 31), GY[1])
        t.fill(inner & (YY == 30), GY[2])
        t.fill(inner & (YY == 29), GY[3])
    t.fill(inner & (YY == 0) & ~((XX >= 29) & sr), GY[5])
    t.fill(inner & (XX == 0) & ~((YY >= 29) & sb), GY[5])
    if sr or sb:
        for (x, y) in ((25, 25), (25, 4), (4, 25)):
            if (x == 25 and sr) or (y == 25 and sb):
                bolt(t, x, y, inner)
    near = k[16, 16] < 16
    if v == 2 and near:
        # access hatch
        inset_rect(t, 8, 8, 23, 21, GY[4], GY[2], GY[5], clip=inner)
        t.rect(10, 18, 21, 19, OR[3], clip=inner)
        t.rect(10, 18, 21, 18, OR[4], clip=inner)
        for (x, y) in ((9, 9), (20, 9)):
            bolt(t, x, y, inner)
    elif v == 3 and near:
        for yy in (9, 13, 17):
            t.rect(7, yy, 24, yy + 1, GY[2], clip=inner)
            t.rect(7, yy + 2, 24, yy + 2, GY[5], clip=inner)
    # armour edges
    edge_bands(t, g, k, {
        "t": [GY[6], GY[5], GY[5], GY[3], GY[2]],
        "l": [GY[5], GY[5], GY[4], GY[2]],
        "r": [GY[1], GY[2], GY[3], GY[2]],
        "b": [OUT, GY[1], GY[2], GY[2]],
    })
    # Academy stripe under the top edge
    if g.top:
        strip = sol & (g.wt > 0.55) & (k >= 5) & (k < 8)
        t.fill(strip, RD[3])
        t.fill(strip & (k < 6), RD[4])
        t.fill(strip & (k >= 7), RD[2])
        t.fill(sol & (g.wt > 0.55) & (k >= 8) & (k < 9), OR[3])
        t.fill(strip & (sc > 1.2), BR[2])
    return t


GIR = [OUT, OR[1], OR[2], OR[3], OR[4], OR[5], OR[6], OR[7]]


def terrain_b(m, v):
    """Construction girders: top/bottom chords, posts on exposed sides, diagonal braces; holes are transparent."""
    g = displaced(geom(m, 0, "square"))
    t = Tile()
    sol = g.solid
    beam = np.zeros((T, T), bool)
    beam |= YY <= 4
    beam |= YY >= 27
    if g.left:
        beam |= XX <= 4
    if g.right:
        beam |= XX >= 27
    if not g.top and not g.bottom and g.left and g.right:
        beam |= (YY >= 14) & (YY <= 17)
    # braces: a zig-zag continuous across tiles (period 32)
    d1 = np.abs((XX - YY)) <= 1.6
    d2 = np.abs((XX + YY) - 31) <= 1.6
    brace = (d1 if v % 2 == 0 else d2)
    beam |= brace & (YY > 3) & (YY < 28)
    t.fill(sol & beam, GIR[3])
    # shading: tops of chords lit, undersides dark, rivet lines
    t.fill(sol & beam & ((YY == 0) | (YY == 27)), GIR[5])
    t.fill(sol & beam & ((YY == 1) | (YY == 28)), GIR[4])
    t.fill(sol & beam & ((YY == 4) | (YY == 31)), GIR[1])
    t.fill(sol & beam & ((YY == 3) | (YY == 30)), GIR[2])
    if g.left:
        t.fill(sol & (XX == 0) & (YY > 0) & (YY < 31), GIR[5])
        t.fill(sol & (XX == 4) & (YY > 4) & (YY < 27), GIR[1])
    if g.right:
        t.fill(sol & (XX == 27) & (YY > 4) & (YY < 27), GIR[4])
        t.fill(sol & (XX == 31) & (YY > 0) & (YY < 31), GIR[1])
    br = sol & brace & (YY > 4) & (YY < 27) & ~((XX <= 4) & g.left) & ~((XX >= 27) & g.right)
    if v % 2 == 0:
        t.fill(br & ((XX - YY) < -0.5), GIR[4])
        t.fill(br & ((XX - YY) > 0.5), GIR[2])
    else:
        t.fill(br & ((XX + YY - 31) < -0.5), GIR[4])
        t.fill(br & ((XX + YY - 31) > 0.5), GIR[2])
    for x in range(3, 31, 6):
        for y in (2, 29):
            if sol[y, x]:
                t.px(x, y, GIR[6])
                t.px(x + 1, y, GIR[2])
    # outer rims from the mask (only where the girder is exposed)
    if g.top:
        t.fill(sol & (YY == 0), GIR[6])
    if g.bottom:
        t.fill(sol & (YY == 31), OUT)
    if v == 3:
        # a warning plate on the chord
        hz = sol & (YY >= 28) & (YY <= 29) & (XX >= 10) & (XX <= 21)
        hazard(t, hz, YE[4], OUT, period=4)
    return t


def back(m, v):
    """Dark hull bulkheads: tall panels with subtle joints, a few vents; a thick bevelled frame toward space."""
    g = displaced(geom(m, 5, "chamfer"))
    t = Tile()
    sol, k = g.solid, g.depth
    inner = sol & (k > 6)
    t.fill(sol, GY[1])
    t.fill(sol & (XX == 31), GY[0])
    t.fill(sol & (XX == 0), GY[2])
    if v == 1:
        for y in (8, 11, 14):
            t.rect(9, y, 22, y, GY[0], clip=inner)
            t.rect(9, y + 1, 22, y + 1, GY[2], clip=inner)
    elif v == 2:
        t.rect(1, 20, 30, 20, GY[0], clip=inner)
        t.rect(1, 21, 30, 21, GY[2], clip=inner)
    elif v == 3:
        for (x, y) in ((4, 4), (26, 4), (4, 26), (26, 26)):
            t.px(x, y, GY[3])
            t.px(x + 1, y + 1, GY[0])
    edge_bands(t, g, k, {
        "t": [GY[4], GY[3], GY[3], GY[2], GY[2], OUT],
        "l": [GY[3], GY[3], GY[2], GY[2], GY[2], OUT],
        "r": [OUT, GY[1], GY[2], GY[2], GY[1], OUT],
        "b": [OUT, GY[1], GY[2], GY[2], GY[1], OUT],
    })
    return t


TINTS = [
    (0, 255, 255, 255, 0, "neutral"),
    (1, 255, 228, 200, 6, "sunlit"),
    (2, 200, 214, 255, -6, "shadowside"),
    (3, 255, 200, 190, -4, "redlight"),
]


# ------------------------------------------------------------------------------------------------ small sheets


def platform():
    """A short I-beam outrigger with grip strips and running lights."""
    rows = []
    for v in range(4):
        row = []
        for col in range(4):
            t = Tile()
            capl, capr = col in (0, 1), col in (0, 3)
            x0, x1 = (1 if capl else 0), (30 if capr else 31)
            t.rect(x0, 0, x1, 3, GIR[4])
            t.rect(x0, 0, x1, 0, GIR[6])
            t.rect(x0, 3, x1, 3, GIR[2])
            t.rect(x0, 4, x1, 8, GIR[2])
            t.rect(x0, 4, x1, 4, GIR[1])
            t.rect(x0, 9, x1, 11, GIR[3])
            t.rect(x0, 9, x1, 9, GIR[4])
            t.rect(x0, 11, x1, 11, GIR[1])
            t.rect(x0, 12, x1, 12, OUT)
            for x in range(x0 + 2, x1 - 1, 4):
                t.rect(x, 1, x + 1, 1, GIR[3])
            for x in range(x0 + 3, x1, 8):
                t.rect(x, 5, x + 1, 7, GIR[1])
            lights = [(8, 23), (15,), (5, 15, 25), (12, 20)][v]
            for lx in lights:
                if x0 <= lx <= x1:
                    t.px(lx, 6, RD[4] if v % 2 else CY[5], glow=True)
            if capl:
                t.rect(0, 0, 0, 11, GIR[5])
            if capr:
                t.rect(31, 0, 31, 11, GIR[1])
            row.append(t)
        rows.append(row)
    return rows


def blocks():
    return [[breakable_block(v, GY, GY[0], OR[4], seed=SEED + 60, face=3) for v in range(4)],
            [crumble_block(s, GIR, top=(GIR[5], GIR[6]), face=3, thick=8) for s in range(4)],
            [door_tile(GY, BL, BL, o) for o in range(4)],
            [door_tile(GY, YE, YE, o) for o in range(4)],
            [toggle_on(BL, CY, f, GY) for f in range(4)], [toggle_off(CY, f) for f in range(4)],
            [conveyor_tile(f, GY, SL, OR, YE[4]) for f in range(4)],
            [spike_tile(d, GY, GY, outline=GY[0]) for d in ("up", "down", "left", "right")]]


def liquid():
    ramp = [BL[1], BL[3], BL[4], CY[5], CY[6], CY[7]]
    return liquid_tiles(ramp, (CY[6], WH), glow=True, seed=17, line_col=BL[5], bubble_cols=(CY[6], WH))


# ------------------------------------------------------------------------------------------------------- deco


def deco():
    items = []

    def add(name, t, place, weight, glow=False, outline=True):
        if outline:
            t = finish(pad(t))
        items.append((name, t, place, weight, glow))

    # antenna mast with a blinking tip
    t = Tile(12, 40)
    gy = np.mgrid[0:40, 0:12][0]
    box(t, 1, 33, 10, 39, GY, 4)
    t.rect(5, 6, 6, 32, GY[4])
    t.rect(5, 6, 5, 32, GY[6])
    for y in range(10, 32, 6):
        t.rect(3, y, 8, y, GY[3])
    t.fill(ellipse(12, 40, (3, 0, 8, 5)), RD[4], glow=True)
    t.px(4, 1, RD[6], glow=True)
    add("antenna", t, "floor", 3, True)
    # satellite dish
    t = Tile(28, 26)
    dish = ellipse(28, 26, (0, 0, 27, 17)) & ~ellipse(28, 26, (2, -4, 25, 12))
    shade_form(t, dish, GY, 4, spread=2.0)
    t.fill(line_m(28, 26, [(14, 12), (14, 2)]), GY[5])
    t.px(14, 2, CY[6], glow=True)
    t.rect(12, 16, 15, 23, GY[3])
    t.rect(12, 16, 12, 23, GY[5])
    box(t, 6, 22, 21, 25, GY, 3)
    add("dish", t, "floor", 2, True)
    # beacon lamp (floor)
    t = Tile(12, 14)
    box(t, 1, 8, 10, 13, GY, 3)
    dome = ellipse(12, 14, (2, 1, 9, 10)) & (YY[:14, :12] < 8)
    t.fill(dome, OR[4], glow=True)
    t.fill(dome & (XX[:14, :12] < 5), OR[6], glow=True)
    t.px(4, 3, YE[7], glow=True)
    add("beacon_lamp", t, "floor", 2, True)
    # floodlight on the wall
    t = Tile(16, 12)
    box(t, 0, 0, 9, 11, GY, 3)
    t.fill(poly(16, 12, [(9, 2), (15, 0), (15, 11), (9, 9)]), GY[2])
    t.rect(11, 2, 14, 9, YE[5], glow=True)
    t.rect(11, 2, 12, 5, YE[7], glow=True)
    add("floodlight", t, "wall", 2, True)
    # hull window with warm interior light
    t = Tile(26, 18)
    box(t, 0, 0, 25, 17, GY, 4)
    t.rect(3, 3, 22, 14, OR[2], glow=True)
    t.rect(3, 3, 22, 8, OR[3], glow=True)
    t.rect(4, 4, 8, 4, YE[6], glow=True)
    t.rect(12, 3, 13, 14, GY[3])
    t.rect(12, 3, 12, 14, GY[5])
    add("window", t, "wall", 2, True)
    # solar panel
    t = Tile(30, 16)
    box(t, 0, 0, 29, 15, GY, 3)
    for x in range(2, 28, 6):
        t.rect(x, 2, x + 4, 13, BL[2])
        t.rect(x, 2, x + 4, 2, BL[4])
        t.rect(x, 7, x + 4, 7, BL[1])
        t.px(x, 3, BL[5])
    add("solar_panel", t, "wall", 2)
    # exhaust vent
    t = Tile(20, 16)
    box(t, 0, 0, 19, 15, GY, 2)
    for y in range(3, 13, 3):
        t.rect(3, y, 16, y + 1, OUT)
        t.rect(3, y + 2, 16, y + 2, GY[3])
    t.rect(3, 12, 16, 12, BR[2])
    add("exhaust", t, "wall", 2)
    # scorch mark (wall, no outline)
    t = Tile(24, 18)
    rng = np.random.default_rng(SEED + 4)
    n = periodic_noise(rng, 24, 3, 3, h=18) if False else rng.standard_normal((18, 24))
    from scipy import ndimage
    n = ndimage.gaussian_filter(n, 2.0)
    e = ellipse(24, 18, (0, 0, 23, 17))
    t.fill(e & (n > -0.05), BR[1])
    t.fill(e & (n > 0.12), GY[0])
    add("scorch", t, "wall", 2, outline=False)
    # fuel tank
    t = d_pipe(14, 22, GY, horizontal=False, base=4)
    t.rect(0, 0, 13, 1, GY[2])
    t.rect(0, 9, 13, 11, RD[3])
    t.rect(0, 9, 13, 9, RD[4])
    add("fuel_tank", t, "floor", 2)
    # docking clamp
    t = Tile(20, 14)
    box(t, 0, 0, 19, 6, GY, 3)
    t.fill(poly(20, 14, [(2, 6), (6, 6), (6, 13), (2, 10)]), GY[3])
    t.fill(poly(20, 14, [(13, 6), (17, 6), (17, 10), (13, 13)]), GY[2])
    hz = rectm(20, 14, 2, 2, 17, 4)
    hazard(t, hz, YE[4], OUT, period=4)
    add("clamp", t, "ceiling", 2)
    # sensor pod (ceiling)
    t = Tile(12, 12)
    t.rect(5, 0, 6, 3, GY[3])
    pod = ellipse(12, 12, (1, 3, 10, 11))
    shade_form(t, pod, GY, 4, spread=2.0)
    t.fill(ellipse(12, 12, (4, 6, 7, 9)), RD[4], glow=True)
    add("sensor", t, "ceiling", 2, True)
    # cables over an edge
    t = Tile(10, 26)
    for (x, ln, c) in ((2, 23, GY[3]), (5, 15, OR[3]), (7, 20, GY[2])):
        t.rect(x, 0, x + 1, ln, c)
        t.rect(x - 1, ln, x + 2, ln + 1, GY[4])
    add("edge_cables", t, "edge", 2)
    # comm array (wall)
    t = Tile(22, 22)
    box(t, 0, 8, 21, 21, GY, 3)
    for i in range(4):
        t.rect(3 + i * 5, 11, 5 + i * 5, 18, GY[2])
        t.rect(3 + i * 5, 11, 5 + i * 5, 11, GY[5])
    t.fill(line_m(22, 22, [(4, 8), (2, 0)]), GY[5])
    t.fill(line_m(22, 22, [(17, 8), (20, 1)]), GY[5])
    t.px(2, 0, CY[6], glow=True)
    t.px(20, 1, CY[6], glow=True)
    add("comm_array", t, "wall", 1, True)
    # supply crate
    add("crate", d_crate(20, 16, GY, 3, brace=False, band=OR[3]), "floor", 2)
    # handrail post
    t = Tile(30, 14)
    for x in (1, 14, 27):
        t.rect(x, 2, x + 1, 13, GY[4])
        t.rect(x, 2, x, 13, GY[6])
    t.rect(0, 2, 29, 3, GY[4])
    t.rect(0, 2, 29, 2, GY[6])
    t.rect(0, 8, 29, 8, GY[3])
    add("railing", t, "floor", 3)
    # numbered-without-numbers bay marker: chevrons
    t = Tile(18, 10)
    box(t, 0, 0, 17, 9, GY, 1)
    for x in (3, 8, 13):
        t.fill(poly(18, 10, [(x, 2), (x + 3, 5), (x, 8), (x - 1, 8), (x + 2, 5), (x - 1, 2)]), OR[4], glow=True)
    add("bay_marker", t, "wall", 1, True)
    return items
