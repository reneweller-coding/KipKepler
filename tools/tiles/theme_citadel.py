"""Theme `citadel`: the Gloam's core. Cold black-violet alloy with sharp chamfers, cyan circuit traces that run on
across tiles (every variant has the same ports on its borders) and magenta neon along the floors; terrain B are
energy-field blocks; the back wall is a dark tech wall with a faint circuit glow."""
import math

import numpy as np

from tilelib import (T, XX, YY, Tile, RAMPS, C, geom, displaced, qidx, seamless_variants, periodic_noise, rivet,
                     hazard, inset_rect, edge_bands, shade_form)
from parts import (box, spike_tile, door_tile, toggle_on, toggle_off, conveyor_tile, liquid_tiles, rectm, ellipse,
                   poly, finish, pad, line_m, breakable_block, crumble_block, d_pipe, gem_cluster)

VI = RAMPS["violet"]
PU = RAMPS["purple"]
SL = RAMPS["slate"]
MG = RAMPS["magenta"]
CY = RAMPS["cyan"]
TE = RAMPS["teal"]
BL = RAMPS["blue"]
YE = RAMPS["yellow"]
RD = RAMPS["red"]
CR = RAMPS["crimson"]
WH = C("white", 0)
OUT = C("outline", 0)

SEED = 8801
ALLOY = [OUT, VI[0], VI[1], SL[2], VI[2], SL[3], SL[4], SL[5]]

# circuit routes per variant: polylines in tile pixels; ports are x=10 (top/bottom) and y=21 (left/right)
ROUTES = {
    0: [[(10, 0), (10, 13), (16, 19), (16, 31 + 0)], [(0, 21), (6, 21)], [(31, 21), (24, 21), (19, 26)],
        [(10, 31), (10, 27)]],
    1: [[(10, 0), (10, 31)], [(0, 21), (10, 21)], [(31, 21), (22, 21), (22, 9)]],
    2: [[(10, 0), (10, 6)], [(0, 21), (13, 21), (19, 15), (31, 15)], [(10, 31), (10, 26)], [(31, 21), (26, 21)]],
    3: [[(10, 0), (10, 9), (4, 15)], [(0, 21), (31, 21)], [(10, 31), (10, 21)]],
}
# note: route 0 enters the bottom at x=16 instead of the port: fix to the port
ROUTES[0][0] = [(10, 0), (10, 12), (15, 17), (15, 25), (10, 30), (10, 31)]
ROUTES[2][1] = [(0, 21), (13, 21), (18, 16), (25, 16), (30, 21), (31, 21)]


def _route_masks(routes, w=1):
    line = np.zeros((T, T), bool)
    pads = []
    for pl in routes:
        line |= line_m(T, T, pl, w)
        for (x, y) in (pl[0], pl[-1]):
            if 0 < x < 31 and 0 < y < 31:
                pads.append((x, y))
    return line, pads


def _circuit(t, v, region, cols, glow=True, routes=ROUTES):
    line, pads = _route_masks(routes[v])
    t.fill(line & region, cols[0], glow=glow)
    for (x, y) in pads:
        pm = (np.abs(XX - x) <= 1) & (np.abs(YY - y) <= 1) & region
        t.fill(pm, cols[1], glow=glow)
        if region[y, x]:
            t.px(x, y, cols[2], glow)


def terrain_a(m, v):
    g = displaced(geom(m, 6, "chamfer"))
    t = Tile()
    sol, k, lit = g.solid, g.depth, g.lit
    t.fill(sol, VI[2])
    inner = sol & (k >= 5.5)
    # faint brushed facets
    t.fill(inner & (YY == 0), SL[3])
    t.fill(inner & (YY == 31), VI[1])
    # angular inset plates in some variants
    if v == 1:
        pl = poly(T, T, [(5, 9), (9, 5), (26, 5), (26, 22), (22, 26), (5, 26)]) & inner
        t.fill(pl, VI[1])
        t.fill(pl & ~np.roll(pl, 1, 0), SL[2])
        t.fill(pl & ~np.roll(pl, -1, 1), SL[3])
    elif v == 3:
        cut = inner & (np.abs(XX - YY - 6) <= 0)
        t.fill(cut, OUT)
        t.fill(inner & (np.abs(XX - YY - 5) <= 0), SL[3])
    deep = k > 12
    _circuit(t, v, inner & ~deep, (CY[3], CY[4], CY[6]))
    _circuit(t, v, inner & deep, (SL[2], SL[3], CY[3]), glow=False)
    edge_bands(t, g, k, {
        "t": [SL[5], SL[4], VI[2], None, VI[1], OUT],
        "l": [SL[4], SL[3], VI[2], VI[1]],
        "r": [OUT, VI[1], VI[1], VI[0]],
        "b": [OUT, VI[0], VI[1], VI[1]],
    })
    # magenta neon along exposed tops, cyan pin lights on the sides
    if g.top:
        neon = sol & (g.wt > 0.5) & (k >= 3) & (k < 4)
        t.fill(neon, MG[5], glow=True)
        t.fill(neon & ((XX % 8) == 3), MG[7], glow=True)
        t.fill(sol & (g.wt > 0.5) & (k >= 4) & (k < 5), MG[2], glow=True)
    for side, ok in (("l", g.left), ("r", g.right)):
        if ok:
            x = 2 if side == "l" else 29
            for y in (8, 24):
                if sol[y, x] and k[y, x] < 3.5:
                    t.px(x, y, CY[5], True)
    if g.bottom:
        t.fill(sol & (g.wb > 0.5) & (k >= 2) & (k < 3) & (XX >= 8) & (XX <= 23), PU[3], glow=True)
    return t


def terrain_b(m, v):
    """Energy-field blocks: a chamfered alloy frame holding a humming cyan field."""
    g = displaced(geom(m, 3, "chamfer"))
    t = Tile()
    sol, k = g.solid, g.depth
    frame = poly(T, T, [(0, 3), (3, 0), (28, 0), (31, 3), (31, 28), (28, 31), (3, 31), (0, 28)])
    t.fill(sol, OUT)
    t.fill(sol & frame, VI[2])
    t.fill(sol & frame & ((YY <= 1) | (XX <= 1)), SL[4])
    t.fill(sol & frame & ((YY >= 30) | (XX >= 30)), VI[1])
    field = rectm(T, T, 4, 4, 27, 27) & sol
    t.fill(field, CY[2], glow=True)
    t.fill(field & (((YY + v) % 3) == 0), CY[3], glow=True)
    t.fill(field & (np.abs(XX - YY + (v * 7 % 16) - 8) <= 0), CY[5], glow=True)
    t.fill(field & ((YY == 4) | (XX == 4)), CY[5], glow=True)
    t.fill(field & ((YY == 27) | (XX == 27)), CY[1], glow=True)
    for (x, y) in ((2, 2), (29, 2), (2, 29), (29, 29)):
        t.px(x, y, MG[5], True)
    t.fill(sol & (k < 1) & (g.lit > 0.25), SL[5])
    return t


BACKROUTES = {
    0: [[(20, 0), (20, 5)], [(0, 12), (8, 12)], [(31, 12), (26, 12)], [(20, 31), (20, 26)]],
    1: [[(20, 0), (20, 7)], [(0, 12), (5, 12)], [(31, 12), (27, 12)], [(20, 31), (20, 24), (14, 18)]],
    2: [[(20, 0), (20, 12), (26, 18), (26, 26)], [(0, 12), (10, 12), (10, 20)], [(31, 12), (27, 12)],
        [(20, 31), (20, 28)]],
    3: [[(20, 0), (20, 4)], [(0, 12), (6, 12)], [(31, 12), (28, 12)], [(20, 31), (20, 27)]],
}


def back(m, v):
    """Dark tech wall: near-black alloy panels, faint violet circuit glow; an angular frame toward the sky."""
    g = displaced(geom(m, 6, "chamfer"))
    t = Tile()
    sol, k = g.solid, g.depth
    t.fill(sol, VI[0])
    if v in (0, 2):
        t.fill(sol & (XX == 31), OUT)
        t.fill(sol & (XX == 0), VI[1])
    _circuit(t, v, sol & (k > 5), (VI[1], PU[2], MG[3]), glow=False, routes=BACKROUTES)
    for (x, y) in _route_masks(BACKROUTES[v])[1]:
        if sol[y, x] and k[y, x] > 5:
            t.px(x, y, MG[3], True)
    edge_bands(t, g, k, {
        "t": [SL[3], VI[2], VI[2], VI[1], MG[2], OUT],
        "l": [SL[3], VI[2], VI[2], VI[1], OUT],
        "r": [OUT, VI[1], VI[1], VI[1], OUT],
        "b": [OUT, VI[1], VI[1], VI[1], OUT],
    }, glow={"t": [4]})
    return t


TINTS = [
    (0, 255, 255, 255, 0, "neutral"),
    (1, 255, 210, 240, 10, "alert"),
    (2, 200, 230, 255, -20, "frost"),
    (3, 170, 160, 200, 0, "blackout"),
]


# ------------------------------------------------------------------------------------------------ small sheets


def platform():
    """A hard-light bridge between two emitters; columns single, left end, middle, right end."""
    rows = []
    for v in range(4):
        row = []
        for col in range(4):
            t = Tile()
            capl, capr = col in (0, 1), col in (0, 3)
            x0, x1 = (5 if capl else 0), (26 if capr else 31)
            t.rect(x0, 1, x1, 5, MG[3], glow=True)
            t.rect(x0, 1, x1, 1, MG[6], glow=True)
            t.rect(x0, 2, x1, 2, MG[5], glow=True)
            t.rect(x0, 5, x1, 5, MG[2], glow=True)
            sh = (XX >= x0) & (XX <= x1) & (YY == 3) & (((XX + v * 4) % 12) < 2)
            t.fill(sh, MG[7], glow=True)
            t.fill((XX >= x0) & (XX <= x1) & (YY == 6) & ((XX % 2) == 0), PU[2], glow=True)
            if capl:
                box(t, 0, 0, 5, 8, ALLOY, 4, outline=True)
                t.rect(4, 2, 5, 4, MG[6], glow=True)
            if capr:
                box(t, 26, 0, 31, 8, ALLOY, 4, outline=True)
                t.rect(26, 2, 27, 4, MG[6], glow=True)
            row.append(t)
        rows.append(row)
    return rows


def blocks():
    return [[breakable_block(v, ALLOY, OUT, MG[5], seed=SEED + 60, face=4) for v in range(4)],
            [crumble_block(s, [OUT, VI[1], VI[2], PU[3], VI[4], VI[5], VI[6]], top=(MG[4], MG[6]), thick=8) for s in
             range(4)],
            [door_tile(ALLOY, BL, BL, o) for o in range(4)],
            [door_tile(ALLOY, YE, YE, o) for o in range(4)],
            [toggle_on(MG, MG, f, ALLOY) for f in range(4)], [toggle_off(MG, f) for f in range(4)],
            [conveyor_tile(f, ALLOY, VI, CY, CY[6]) for f in range(4)],
            [spike_tile(d, [OUT, VI[1], VI[2], SL[3], SL[4], SL[5], SL[6], WH], ALLOY, outline=OUT,
                        tip=(None, MG[5], MG[7]), glow_tip=True) for d in ("up", "down", "left", "right")]]


def liquid():
    ramp = [OUT, VI[0], VI[1], PU[3], MG[4], MG[6]]
    rows = liquid_tiles(ramp, (MG[5], WH), glow=True, seed=23, line_col=PU[2], bubble_cols=(MG[5], WH))
    return rows


# ------------------------------------------------------------------------------------------------------- deco


def deco():
    items = []

    def add(name, t, place, weight, glow=False, outline=True):
        if outline:
            t = finish(pad(t))
        items.append((name, t, place, weight, glow))

    # the Gloam's eye sensor
    t = Tile(18, 14)
    shell = poly(18, 14, [(0, 7), (5, 0), (12, 0), (17, 7), (12, 13), (5, 13)])
    t.fill(shell, VI[2])
    t.fill(shell & (YY[:14, :18] < 5), SL[3])
    eye = ellipse(18, 14, (4, 3, 13, 10))
    t.fill(eye, OUT)
    t.fill(ellipse(18, 14, (6, 4, 11, 9)), MG[4], glow=True)
    t.fill(ellipse(18, 14, (7, 5, 10, 8)), MG[6], glow=True)
    t.px(8, 5, WH, True)
    add("eye_sensor", t, "wall", 2, True)
    # holo screen
    t = Tile(26, 18)
    box(t, 0, 0, 25, 17, ALLOY, 3)
    t.rect(3, 3, 22, 14, CY[1], glow=True)
    for y in range(4, 14, 2):
        ln = (y * 7) % 13 + 4
        t.rect(5, y, 5 + ln, y, CY[4], glow=True)
    t.fill(ellipse(26, 18, (15, 5, 21, 11)) & ~ellipse(26, 18, (16, 6, 20, 10)), CY[5], glow=True)
    add("holo_screen", t, "wall", 2, True)
    # data pylon
    t = Tile(12, 34)
    gx = np.mgrid[0:34, 0:12][1]
    gyy = np.mgrid[0:34, 0:12][0]
    body = poly(12, 34, [(1, 33), (2, 4), (6, 0), (10, 4), (11, 33)])
    t.fill(body, VI[2])
    t.fill(body & (gx < 5), SL[3])
    t.fill(body & (gx > 8), VI[1])
    for y in range(7, 31, 4):
        t.fill(body & (gyy == y) & (gx >= 3) & (gx <= 8), CY[4] if y % 8 == 3 else MG[4], glow=True)
    add("pylon", t, "floor", 2, True)
    # energy conduit (wall)
    t = Tile(10, 32)
    t.rect(0, 0, 9, 31, VI[1])
    t.rect(0, 0, 0, 31, SL[3])
    t.rect(3, 0, 6, 31, CY[3], glow=True)
    t.rect(4, 0, 4, 31, CY[6], glow=True)
    for y in (2, 15, 28):
        t.rect(0, y, 9, y + 1, VI[2])
        t.rect(0, y, 9, y, SL[4])
    add("conduit", t, "wall", 2, True)
    # neon sign: a triangle with an eye (no letters)
    t = Tile(22, 20)
    box(t, 0, 0, 21, 19, ALLOY, 1)
    tri = poly(22, 20, [(11, 3), (18, 16), (4, 16)]) & ~poly(22, 20, [(11, 6), (15.5, 14.5), (6.5, 14.5)])
    t.fill(tri, MG[5], glow=True)
    t.fill(ellipse(22, 20, (9, 9, 13, 13)), MG[6], glow=True)
    add("neon_sign", t, "wall", 1, True)
    # Gloam banner
    t = Tile(20, 32)
    t.rect(0, 0, 19, 1, SL[4])
    cloth = poly(20, 32, [(1, 2), (18, 2), (18, 28), (10, 31), (1, 28)])
    t.fill(cloth, CR[1])
    t.fill(cloth & (XX[:32, :20] <= 3), CR[2])
    t.fill(cloth & (XX[:32, :20] >= 16), CR[0])
    t.fill(poly(20, 32, [(10, 8), (15, 18), (5, 18)]) & ~poly(20, 32, [(10, 11), (12.5, 16.5), (7.5, 16.5)]), MG[4])
    t.fill(ellipse(20, 32, (8, 13, 11, 16)), MG[6], glow=True)
    add("banner", t, "wall", 1, True)
    # drone dock (ceiling)
    t = Tile(20, 14)
    box(t, 0, 0, 19, 4, ALLOY, 3)
    drone = ellipse(20, 14, (4, 4, 15, 12))
    shade_form(t, drone, ALLOY, 4, spread=2.0)
    t.fill(ellipse(20, 14, (8, 7, 11, 10)), RD[4], glow=True)
    add("drone_dock", t, "ceiling", 2, True)
    # cables (ceiling)
    t = Tile(44, 10)
    for (a, b, dip, c) in ((2, 41, 7, VI[2]), (6, 37, 4, PU[2]), (10, 42, 8, VI[3])):
        pts = [(a + (b - a) * i / 16.0, 1 + dip * (1 - ((i - 8) / 8.0) ** 2)) for i in range(17)]
        t.fill(line_m(44, 10, pts, 2), c)
    t.rect(0, 0, 5, 1, SL[3])
    t.rect(38, 0, 43, 1, SL[3])
    add("cables", t, "ceiling", 2)
    # power core (floor)
    t = Tile(18, 24)
    box(t, 0, 18, 17, 23, ALLOY, 3)
    box(t, 2, 0, 15, 4, ALLOY, 3)
    t.blit(gem_cluster(12, 14, [VI[1], PU[3], MG[3], MG[4], MG[5], MG[6], MG[7], WH], True, seed=4, n=3), 3, 4)
    add("power_core", t, "floor", 1, True)
    # server tower
    t = Tile(16, 32)
    box(t, 0, 0, 15, 31, ALLOY, 2)
    for i, y in enumerate(range(3, 29, 3)):
        t.rect(2, y, 13, y + 1, OUT)
        t.px(3 + (i * 5) % 9, y, CY[5] if i % 3 else MG[5], True)
    add("server", t, "floor", 2, True)
    # holo projector with a floating cube
    t = Tile(16, 28)
    box(t, 2, 22, 13, 27, ALLOY, 3)
    beam = poly(16, 28, [(6, 22), (10, 22), (14, 6), (2, 6)])
    t.fill(beam & ((YY[:28, :16] % 2) == 0), CY[2], glow=True)
    cube = poly(16, 28, [(8, 0), (13, 3), (13, 9), (8, 12), (3, 9), (3, 3)])
    t.fill(cube, CY[4], glow=True)
    t.fill(poly(16, 28, [(8, 0), (13, 3), (8, 6), (3, 3)]), CY[6], glow=True)
    t.fill(poly(16, 28, [(8, 6), (13, 3), (13, 9), (8, 12)]), CY[3], glow=True)
    add("projector", t, "floor", 1, True)
    # wall vent (angular)
    t = Tile(20, 12)
    t.fill(poly(20, 12, [(0, 3), (3, 0), (19, 0), (19, 8), (16, 11), (0, 11)]), VI[2])
    for x in range(3, 18, 3):
        t.fill(line_m(20, 12, [(x, 9), (x + 2, 2)]), OUT)
    add("vent", t, "wall", 2)
    # emitter over an edge
    t = Tile(8, 18)
    box(t, 0, 0, 7, 5, ALLOY, 3)
    t.rect(3, 6, 4, 17, MG[4], glow=True)
    t.rect(3, 6, 3, 17, MG[6], glow=True)
    add("edge_emitter", t, "edge", 2, True)
    # floating cube (wall)
    t = Tile(12, 12)
    t.fill(poly(12, 12, [(6, 0), (11, 3), (11, 8), (6, 11), (1, 8), (1, 3)]), MG[3], glow=True)
    t.fill(poly(12, 12, [(6, 0), (11, 3), (6, 6), (1, 3)]), MG[5], glow=True)
    t.px(6, 2, WH, True)
    add("float_cube", t, "wall", 1, True)
    # warning chevrons (wall)
    t = Tile(20, 8)
    t.rect(0, 0, 19, 7, OUT)
    for x in (2, 8, 14):
        t.fill(poly(20, 8, [(x, 1), (x + 3, 4), (x, 7), (x - 2, 7), (x + 1, 4), (x - 2, 1)]), MG[4], glow=True)
    add("chevrons", t, "wall", 1, True)
    return items
