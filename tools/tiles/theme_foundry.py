"""Theme `foundry`: the dreadnought's forge decks. Soot-black iron plates with rust, heavy rivets and seams glowing
orange with heat; terrain B are hot vent blocks; the back wall is a dark furnace brick wall (pipes come as deco)."""
import math

import numpy as np
from scipy import ndimage

from tilelib import (T, XX, YY, Tile, RAMPS, C, geom, displaced, qidx, seamless_variants, periodic_noise, rivet,
                     hazard, inset_rect, edge_bands, shade_form)
from parts import (box, spike_tile, door_tile, toggle_on, toggle_off, conveyor_tile, liquid_tiles, rectm, ellipse,
                   poly, finish, pad, line_m, breakable_block, crumble_block, d_pipe, d_crate)
from organic import hang

GY = RAMPS["grey"]
SL = RAMPS["slate"]
BR = RAMPS["brown"]
OR = RAMPS["orange"]
RD = RAMPS["red"]
YE = RAMPS["yellow"]
ST = RAMPS["steel"]
BL = RAMPS["blue"]
CY = RAMPS["cyan"]
WH = C("white", 0)
OUT = C("outline", 0)

SEED = 7701
IRON = [OUT, GY[0], GY[1], GY[2], GY[3], GY[4], GY[5]]
_rng = np.random.default_rng(SEED)
RUST = seamless_variants(_rng, 4, sx=5, sy=4, band=(2.0, 9.0))
SOOT = seamless_variants(_rng, 4, sx=8, sy=12, band=(2.0, 9.0))
SEAM = {0: (True, False), 1: (False, True), 2: (True, True), 3: (False, False)}
GLOWSEG = {0: (6, 22), 1: (4, 18), 2: (10, 27), 3: None}


def hrivet(t, x, y, clip):
    for (px, py, c) in ((x + 1, y, GY[4]), (x, y + 1, GY[4]), (x + 1, y + 1, GY[3]), (x + 2, y + 1, GY[1]),
                        (x + 1, y + 2, GY[1]), (x + 2, y + 2, OUT), (x, y, GY[3]), (x + 2, y, GY[2]),
                        (x, y + 2, GY[2])):
        if 0 <= px < T and 0 <= py < T and clip[py, px]:
            t.px(px, py, c)


def terrain_a(m, v):
    g = displaced(geom(m, 3, "chamfer"))
    t = Tile()
    sol, k, lit = g.solid, g.depth, g.lit
    t.fill(sol, GY[2])
    t.fill(sol & (YY <= 2), GY[3])
    t.fill(sol & (YY >= 27), GY[1])
    t.fill(sol & (SOOT[v] - np.clip((k - 8) / 10, 0, 1) > 1.4) & (YY > 2), GY[1])
    # rust blooms (only on some plates)
    r = RUST[v] - (0.0 if v in (1, 2) else 0.7) - np.clip((k - 8) / 10, 0, 1) * 1.2
    t.fill(sol & (r > 1.2), BR[2])
    t.fill(sol & (r > 1.55), BR[3])
    t.fill(sol & (r > 1.9), OR[2])
    inner = sol & (k >= 5)
    sr, sb = SEAM[v]
    seg = GLOWSEG[v]
    if sr:
        t.fill(inner & (XX == 31), OUT)
        t.fill(inner & (XX == 30), GY[1])
        if seg:
            gm = inner & (XX == 31) & (YY >= seg[0]) & (YY <= seg[1])
            t.fill(gm, OR[4], glow=True)
            t.fill(gm & (YY >= seg[0] + 2) & (YY <= seg[1] - 2), YE[5], glow=True)
            t.fill(inner & (XX == 30) & (YY >= seg[0] + 1) & (YY <= seg[1] - 1), OR[2], glow=True)
    if sb:
        t.fill(inner & (YY == 31), OUT)
        t.fill(inner & (YY == 30), GY[1])
        if seg:
            gm = inner & (YY == 31) & (XX >= seg[0]) & (XX <= seg[1])
            t.fill(gm, OR[4], glow=True)
            t.fill(gm & (XX >= seg[0] + 2) & (XX <= seg[1] - 2), YE[5], glow=True)
            t.fill(inner & (YY == 30) & (XX >= seg[0] + 1) & (XX <= seg[1] - 1), OR[2], glow=True)
    t.fill(inner & (YY == 0) & ~(XX == 31), GY[3])
    t.fill(inner & (XX == 0) & ~(YY == 31), GY[3])
    # heavy rivets along owned seams, or a riveted strap
    if sr:
        for y in (4, 13, 22):
            hrivet(t, 26, y, inner)
    if sb:
        for x in (4, 13, 22):
            hrivet(t, x, 26, inner)
    if v == 3:
        t.rect(0, 12, 31, 17, GY[3], clip=inner)
        t.rect(0, 12, 31, 12, GY[4], clip=inner)
        t.rect(0, 17, 31, 17, GY[1], clip=inner)
        for x in (5, 16, 27):
            hrivet(t, x, 13, inner)
    edge_bands(t, g, k, {
        "t": [GY[5], GY[4], GY[3], GY[3], GY[1]],
        "l": [GY[4], GY[3], GY[3], GY[1]],
        "r": [OUT, GY[1], GY[2], GY[1]],
        "b": [OUT, GY[0], GY[1], GY[1]],
    })
    # rust creeping over the top lip
    if g.top:
        t.fill(sol & (g.wt > 0.5) & (k >= 1) & (k < 3) & (r > 0.6), BR[3])
        t.fill(sol & (g.wt > 0.5) & (k < 1) & (r > 1.2), BR[4])
    # glowing slag drips on some undersides

    def dc(i, n, dx):
        return YE[5] if i == n - 1 else OR[3]
    if v in (0, 2):
        hang(t, g, v, SEED + 3, dc, count=(1, 2), length=(1, 3),
             glow_fn=lambda i, n: True)
    return t


def terrain_b(m, v):
    """Hot vent blocks: a riveted iron frame around a grille that glows from the furnace below."""
    g = displaced(geom(m, 2, "chamfer"))
    t = Tile()
    sol, k = g.solid, g.depth
    box(t, 0, 0, 31, 31, IRON, 3, outline=True, clip=sol)
    inner = rectm(T, T, 4, 4, 27, 27) & sol
    t.fill(inner, OUT)
    heat = [OR[2], OR[3], OR[4], YE[4], YE[5]]
    # glow gradient: hottest at the bottom of the grille
    rel = np.clip((YY - 4) / 23.0, 0, 1)
    hi = np.clip(np.floor(rel * 4.2 + (v % 2) * 0.4), 0, 4).astype(int)
    slats = inner & (((YY - 4) % 4) != 0)
    t.fill_idx(slats, heat, hi, glow=True)
    t.fill(inner & (((YY - 4) % 4) == 0), GY[1])
    t.fill(inner & (((YY - 4) % 4) == 1), GY[2])
    # vertical bars
    for x in (11, 20):
        t.rect(x, 4, x + 1, 27, GY[2], clip=sol)
        t.rect(x, 4, x, 27, GY[3], clip=sol)
    for (x, y) in ((1, 1), (28, 1), (1, 28), (28, 28)):
        hrivet(t, x, y, sol)
    # mask-aware outer rim
    t.fill(sol & (k < 1) & (g.lit > 0.25), GY[5])
    t.fill(sol & (k < 1) & (g.lit < -0.3), OUT)
    return t


BRICK = [OUT, RD[0], BR[1], RD[1], BR[2]]


def back(m, v):
    """Furnace brick wall: running bond of dark firebricks, soot, a few joints still glowing; an iron frame toward
    the sky."""
    g = displaced(geom(m, 4, "chamfer"))
    t = Tile()
    sol, k = g.solid, g.depth
    row = YY // 8
    off = np.where(row % 2 == 0, 0, 8)
    bx = (XX + off) % 16
    by = YY % 8
    t.fill(sol, BR[1])
    t.fill(sol & (by == 0), RD[1])
    t.fill(sol & ((by == 7) | (bx == 15)), OUT)
    t.fill(sol & (bx == 0) & (by != 7), RD[1])
    # per-brick tone (deterministic per brick, same in every variant for border bricks)
    bid = ((XX + off) // 16) * 7 + row * 3
    t.fill(sol & ((bid % 5) == 0) & (by > 0) & (by < 7) & (bx > 0) & (bx < 15), BR[1])
    t.fill(sol & ((bid % 7) == 3) & (by > 0) & (by < 7) & (bx > 0) & (bx < 15), RD[0])
    inner = sol & (k > 5)
    if v == 1:
        gm = inner & (by == 7) & (XX >= 6) & (XX <= 18) & (row == 2)
        t.fill(gm, OR[2], glow=True)
        t.fill(gm & (XX >= 9) & (XX <= 15), OR[3], glow=True)
    elif v == 3:
        gm = inner & (bx == 15) & (row == 1)
        t.fill(gm, OR[2], glow=True)
    edge_bands(t, g, k, {
        "t": [GY[3], GY[2], GY[2], GY[1], OUT],
        "l": [GY[3], GY[2], GY[2], GY[1], OUT],
        "r": [OUT, GY[1], GY[1], GY[1], OUT],
        "b": [OUT, GY[1], GY[1], GY[1], OUT],
    })
    return t


TINTS = [
    (0, 255, 255, 255, 0, "neutral"),
    (1, 255, 222, 190, 6, "white-hot"),
    (2, 214, 220, 255, -10, "cooled"),
    (3, 190, 170, 160, 0, "smoke"),
]


# ------------------------------------------------------------------------------------------------ small sheets


def platform():
    """An iron grating on chains; columns single, left end, middle, right end."""
    rows = []
    for v in range(4):
        row = []
        for col in range(4):
            t = Tile()
            capl, capr = col in (0, 1), col in (0, 3)
            x0, x1 = (1 if capl else 0), (30 if capr else 31)
            t.rect(x0, 0, x1, 7, GY[2])
            t.rect(x0, 0, x1, 0, GY[4])
            t.rect(x0, 1, x1, 1, GY[3])
            t.rect(x0, 7, x1, 7, OUT)
            holes = (YY >= 2) & (YY <= 5) & ((XX % 4) >= 1) & ((XX % 4) <= 2) & (XX >= x0 + 2) & (XX <= x1 - 2)
            t.fill(holes, OUT)
            t.fill(holes & (YY == 5) & ((XX + v) % 8 < 4), OR[2], glow=True)
            t.rect(x0, 8, x1, 9, GY[1])
            t.rect(x0, 8, x1, 8, GY[2])
            for bx in (2, 29):
                if (bx == 2 and capl) or (bx == 29 and capr):
                    for y in range(10, 18, 2):
                        t.px(bx, y, GY[3])
                        t.px(bx, y + 1, GY[1])
            if capl:
                t.rect(0, 0, 1, 9, GY[3])
            if capr:
                t.rect(30, 0, 31, 9, GY[1])
            row.append(t)
        rows.append(row)
    return rows


def blocks():
    rust = [OUT, BR[1], BR[2], BR[3], OR[3], BR[4], BR[5]]
    return [[breakable_block(v, rust, OUT, OR[4], seed=SEED + 60, face=3) for v in range(4)],
            [crumble_block(s, IRON, top=(BR[3], BR[4]), face=3, thick=8) for s in range(4)],
            [door_tile(GY, BL, BL, o) for o in range(4)],
            [door_tile(GY, YE, YE, o) for o in range(4)],
            [toggle_on(OR, OR, f, GY) for f in range(4)], [toggle_off(OR, f) for f in range(4)],
            [conveyor_tile(f, GY, SL, OR, YE[5]) for f in range(4)],
            [spike_tile(d, [OUT, GY[1], GY[2], GY[3], GY[4], GY[5], GY[6], GY[7]], GY, outline=OUT,
                        tip=(None, OR[4], YE[5]), glow_tip=True) for d in ("up", "down", "left", "right")]]


def liquid():
    ramp = [RD[2], RD[3], OR[3], OR[4], YE[4], YE[6]]
    rows = liquid_tiles(ramp, (YE[5], YE[7]), glow=True, seed=19, line_col=OR[4], bubble_cols=(YE[5], YE[7]))
    # dark crust floating on the lava body
    for f, bt in enumerate(rows[1]):
        for (x0, y0, w) in ((4, 6, 6), (19, 21, 5)):
            xs = (x0 + f * 2) % T
            for dx in range(w):
                x = (xs + dx) % T
                bt.px(x, y0, RD[1], False)
                if 0 < dx < w - 1:
                    bt.px(x, y0 + 1, RD[1], False)
    return rows


# ------------------------------------------------------------------------------------------------------- deco


def deco():
    items = []

    def add(name, t, place, weight, glow=False, outline=True):
        if outline:
            t = finish(pad(t))
        items.append((name, t, place, weight, glow))

    # furnace mouth
    t = Tile(30, 24)
    box(t, 0, 0, 29, 23, IRON, 3)
    mouth = poly(30, 24, [(5, 23), (5, 9), (15, 4), (24, 9), (24, 23)])
    t.fill(mouth, OR[3], glow=True)
    t.fill(mouth & (YY[:24, :30] > 14), YE[5], glow=True)
    t.fill(mouth & (YY[:24, :30] > 19), YE[7], glow=True)
    for x in (9, 14, 19):
        t.rect(x, 6, x + 1, 23, GY[1])
    t.rect(0, 22, 29, 23, GY[2])
    add("furnace", t, "wall", 2, True)
    # pipes
    add("pipe_h", d_pipe(32, 8, IRON + [GY[6]], True, flanges=(5, 24)), "wall", 3)
    add("pipe_v", d_pipe(8, 32, IRON + [GY[6]], False, flanges=(4, 23)), "wall", 3)
    # valve wheel + gauge
    t = Tile(18, 18)
    wheel = ellipse(18, 18, (0, 0, 17, 17)) & ~ellipse(18, 18, (2, 2, 15, 15))
    t.fill(wheel, RD[3])
    t.fill(wheel & (YY[:18, :18] < 8), RD[4])
    for a in (0, 60, 120):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        t.fill(line_m(18, 18, [(8.5 - 7 * ca, 8.5 - 7 * sa), (8.5 + 7 * ca, 8.5 + 7 * sa)]), RD[2])
    t.fill(ellipse(18, 18, (6, 6, 11, 11)), GY[3])
    add("valve", t, "wall", 2)
    t = Tile(14, 14)
    face = ellipse(14, 14, (0, 0, 13, 13))
    t.fill(face, GY[2])
    t.fill(ellipse(14, 14, (2, 2, 11, 11)), YE[6])
    t.fill(line_m(14, 14, [(6.5, 6.5), (10, 4)]), RD[3])
    t.fill(ellipse(14, 14, (2, 2, 11, 11)) & (XX[:14, :14] > 8) & (YY[:14, :14] > 8), OR[3])
    add("gauge", t, "wall", 2)
    # chains (ceiling)
    for i, ln in enumerate((20, 34)):
        t = Tile(6, ln)
        for y in range(0, ln - 3, 3):
            if (y // 3) % 2 == 0:
                t.rect(1, y, 4, y + 3, GY[3])
                t.rect(2, y + 1, 3, y + 2, OUT)
                t.px(1, y, GY[5])
            else:
                t.rect(2, y, 3, y + 3, GY[4])
        if i == 1:
            t.fill(poly(6, ln, [(0, ln - 6), (5, ln - 6), (3, ln - 1)]), GY[4])
        add("chain_%d" % i, t, "ceiling", 3)
    # crucible (floor, glowing)
    t = Tile(22, 16)
    bowl = poly(22, 16, [(0, 3), (21, 3), (18, 15), (3, 15)])
    shade_form(t, bowl, IRON + [GY[6]], 3, spread=1.0, round_=False)
    t.rect(2, 3, 19, 5, OR[4], glow=True)
    t.rect(4, 3, 12, 3, YE[6], glow=True)
    t.rect(0, 2, 21, 2, GY[4])
    add("crucible", t, "floor", 2, True)
    # ingot stack (glowing)
    t = Tile(20, 12)
    for (x, y, hot) in ((0, 7, True), (10, 7, False), (5, 2, True)):
        box(t, x, y, x + 9, y + 4, [RD[0], RD[1], OR[2], OR[3], OR[4], YE[5], YE[6]] if hot else IRON + [GY[6]], 3)
        if hot:
            t.rect(x + 1, y + 1, x + 8, y + 3, OR[4], glow=True)
            t.rect(x + 1, y + 1, x + 8, y + 1, YE[5], glow=True)
    add("ingots", t, "floor", 2, True)
    # coal / slag pile with embers
    t = Tile(24, 10)
    pile = ellipse(24, 20, (0, 0, 23, 19))[:10]
    t.fill(pile, GY[1])
    t.fill(pile & (YY[:10, :24] < 3), GY[2])
    for (x, y) in ((5, 5), (11, 3), (16, 6), (9, 8), (19, 4)):
        t.px(x, y, OR[4], True)
        t.px(x + 1, y, OR[2], True)
    add("slag_pile", t, "floor", 2, True)
    # caged lamp (ceiling)
    t = Tile(12, 16)
    t.rect(5, 0, 6, 3, GY[3])
    box(t, 2, 3, 9, 5, IRON, 3, outline=False)
    t.fill(ellipse(12, 16, (3, 5, 8, 14)), OR[4], glow=True)
    t.fill(ellipse(12, 16, (4, 6, 6, 10)), YE[6], glow=True)
    for x in (2, 5, 9):
        t.rect(x, 6, x, 14, GY[2])
    t.rect(2, 14, 9, 15, GY[3])
    add("cage_lamp", t, "ceiling", 3, True)
    # steam vent on the wall
    t = Tile(16, 12)
    box(t, 0, 0, 15, 11, IRON, 3)
    for x in range(3, 13, 3):
        t.rect(x, 3, x, 8, OUT)
    add("steam_vent", t, "wall", 2)
    # warning sign: a flame triangle (no letters)
    t = Tile(18, 16)
    tri = poly(18, 16, [(9, 0), (17, 15), (0, 15)])
    t.fill(tri, YE[4])
    t.fill(poly(18, 16, [(9, 3), (14, 13), (4, 13)]), YE[5])
    t.fill(poly(18, 16, [(9, 5), (11, 9), (10, 12), (8, 12), (7, 9)]), RD[3])
    t.fill(poly(18, 16, [(9, 8), (10, 11), (8, 11)]), OR[4])
    add("sign_heat", t, "wall", 1)
    # anvil-like press block
    t = Tile(22, 16)
    box(t, 4, 9, 17, 15, IRON, 3)
    t.fill(poly(22, 16, [(0, 2), (21, 2), (18, 9), (3, 9)]), GY[3])
    t.rect(0, 2, 21, 3, GY[4])
    t.rect(0, 2, 21, 2, GY[5])
    add("press", t, "floor", 1)
    # slag drips over an edge
    t = Tile(10, 14)
    for (x, ln) in ((1, 6), (4, 11), (7, 4)):
        t.rect(x, 0, x + 1, ln, OR[3], glow=True)
        t.px(x, ln, YE[6], True)
        t.px(x + 1, ln, YE[5], True)
    add("slag_drips", t, "edge", 2, True, outline=False)
    # barrel
    t = d_pipe(12, 16, [OUT, RD[1], RD[2], RD[3], RD[4], RD[5], RD[6]], horizontal=False, base=3)
    t.rect(0, 3, 11, 3, GY[1])
    t.rect(0, 12, 11, 12, GY[1])
    add("barrel", t, "floor", 2)
    # girder bracket on the wall
    t = Tile(24, 24)
    t.fill(poly(24, 24, [(0, 0), (6, 0), (23, 17), (23, 23)]), GY[3])
    t.fill(poly(24, 24, [(0, 0), (3, 0), (23, 20), (23, 23)]), GY[4])
    t.rect(0, 0, 4, 23, GY[2])
    t.rect(0, 0, 0, 23, GY[4])
    t.rect(0, 19, 23, 23, GY[2])
    t.rect(0, 19, 23, 19, GY[4])
    for (x, y) in ((1, 3), (1, 12), (8, 20), (18, 20)):
        hrivet(t, x, y, np.ones((T, T), bool))
    add("bracket", t, "wall", 1)
    # embers drifting (wall, no outline)
    t = Tile(14, 14)
    for (x, y) in ((2, 11), (6, 6), (11, 9), (8, 1), (3, 3)):
        t.px(x, y, OR[4], True)
    add("embers", t, "wall", 2, True, outline=False)
    return items
