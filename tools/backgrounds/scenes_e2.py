"""Backgrounds of episode 2, the verdant moon Thessa: jungle (the surface) and hive (underground)."""
import numpy as np

from bgkit import (Draw, Layer, Noise, Spec, band, bands_at, col, dither_mask, edge, fogged, gas_field, grow, ladder,
                   levels, lift, mix, planet, shift, shrink, stars, stretch, swoosh, vbands, wdx)
from shapes import (_px, blob, column_profile, crowns, light, local, mesa_profile, paint_mesas, plate, rock, stamp)


# ------------------------------------------------------------------------------------------------------ helpers

def giant_tree(L, rng, x, base, height, cap_w, lad_trunk, lad_cap, tiers=2, tendrils=None, spots=None, lean=0.0,
               glow_tips=None):
    """An alien giant tree: a tapered, slightly bent trunk and tiers of umbrella caps (domes with a dark underside),
    lit from the upper left. lad_trunk: [shadow, body, lit]; lad_cap: [underside, shadow, body, lit, rim]."""
    lad_trunk = np.asarray(lad_trunk, np.uint8)
    lad_cap = np.asarray(lad_cap, np.uint8)
    top = base - height
    tw = max(4, cap_w * 0.09)
    y = L.Y
    t = np.clip((base - y) / height, 0, 1)
    cxs = x + lean * height * t ** 2
    half = tw / 2 * (1 - 0.45 * t) + tw * 0.9 * np.clip(1 - (base - y) / 26, 0, 1) ** 2
    dx = wdx(L.X, cxs, L.w)
    trunk = (np.abs(dx) <= half) & (y <= base + 2) & (y >= top)
    tidx = np.where(dx < -half * 0.35, 2, np.where(dx > half * 0.45, 0, 1))
    L.paint(trunk, tidx, lad_trunk)
    caps = []
    for k in range(tiers):
        f = 1.0 - k * 0.42
        cw = cap_w * f * rng.uniform(0.9, 1.1)
        ch = cw * rng.uniform(0.18, 0.26)
        cy = top + k * height * 0.3 + ch * 0.2
        ccx = x + lean * height * (1 - k * 0.3) ** 2 + rng.uniform(-0.1, 0.1) * cw
        caps.append((ccx, cy, cw, ch))
    for ccx, cy, cw, ch in reversed(caps):
        ddx = wdx(L.X, ccx, L.w) / (cw / 2)
        dome = (ddx * ddx + ((y - cy) / ch) ** 2 <= 1) & (y <= cy)
        under = (ddx * ddx + ((y - cy) / (ch * 0.28)) ** 2 <= 1) & (y > cy)
        v = np.clip(0.55 - 0.45 * ddx - 0.5 * (y - cy) / ch, 0, 0.999)
        idx, dith = band(v, 3, 0.35, None, L.by)
        L.paint(dome, idx + 1, lad_cap, dith)
        L.put(under, lad_cap[0])
        L.put(edge(dome, 0, -1) & (ddx < 0.3), lad_cap[4])
        if spots is not None:
            sp = dome & (Noise(L.w, int(L.w / 7), rng, 1)(L.X, y * 1.6) > 0.78) & ~edge(dome, 0, -1)
            L.put(sp & (y < cy - 2), spots)
        if tendrils is not None:
            for k in range(int(cw / 6)):
                tx = ccx + rng.uniform(-0.45, 0.45) * cw
                dd = ((tx - ccx) / (cw / 2)) ** 2
                ty = cy + ch * 0.28 * np.sqrt(max(0, 1 - dd))
                ln = rng.uniform(4, 10 + ch * 0.8)
                m = (np.abs(wdx(L.X, tx, L.w)) < 0.5) & (y >= ty - 1) & (y < ty + ln)
                L.put(m, tendrils)
                if glow_tips is not None and rng.random() < 0.5:
                    light(L, tx, ty + ln, glow_tips)


def mist(L, y0, y1, colour, dpx=6.0, wobble=None, mask=None):
    """An opaque mist bank from y0 down to y1 with a dithered upper edge (and wavy top if wobble is given)."""
    yy = L.Y if wobble is None else L.Y + wobble
    cover = np.clip((yy - y0) / (2 * dpx) + 0.5, 0, 1)
    m = (cover > L.by) & (L.Y <= y1)
    if mask is not None:
        m &= mask
    L.put(m, colour, keep=True)
    return m


def fern(L, rng, x, base, size, c, c_lit=None, n=6):
    """A fan of curved fronds rising from (x, base)."""
    m = np.zeros(L.a.shape, bool)
    for k in range(n):
        a = np.radians(rng.uniform(-80, 80) - 90)
        ln = size * rng.uniform(0.6, 1.0)
        curl = rng.uniform(-0.6, 0.6)
        for i in range(int(ln)):
            t = i / ln
            ang = a + curl * t * t
            px = x + np.cos(ang) * i
            py = base + np.sin(ang) * i + 0.35 * ln * t * t
            wd = max(0.5, (1 - t) * size * 0.06)
            ys0, ys1 = int(py - wd), int(py + wd) + 1
            for yy in range(max(0, ys0), min(L.h, ys1)):
                m[yy, int(px) % L.w] = True
            for s in (-1, 1):
                lx = px + s * (1 - t) * size * 0.08
                ly = py + (1 - t) * size * 0.04
                if 0 <= int(ly) < L.h and i % 2 == 0:
                    m[int(ly), int(lx) % L.w] = True
    L.put(m, c)
    if c_lit is not None:
        L.put(edge(m, 0, -1) & (L.X < x + size * 0.1), c_lit)
    return m


# ----------------------------------------------------------------------------------------------------- jungle_a

def jungle_a(seed):
    """Thessa by day: a teal sky with two moons, mesas in two depths, giant umbrella trees, mist bands."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280
    sky_h = col("teal2")

    # layer 0: the sky, two moons, far mesas
    L0 = Layer(W0)
    wob = (Noise(W0, 4, rng, 3)(L0.X, L0.Y * 0.3) - 0.5) * 24
    vbands(L0, "teal1", [(110, "teal2"), (268, "teal3")], dpx=8, wobble=wob)
    # high thin clouds
    cl = gas_field(L0, rng, cells=3, warp=200, streak=0.7, sy=3.0) * swoosh(L0, rng, 130, 30, 40)
    levels(L0, stretch(cl, 0, 99.8), ["teal2", "ice3"], [0.35, 0.62], dpx=0.04)
    planet(L0, rng, 250, 92, 36, [ladder("teal1 teal2 ice3 ice4 ice5 ice6")], light=(-0.8, -0.4, 0.45), band_freq=4,
           turb=0.8, levels=[0, 0.06, 0.22, 0.42, 0.62, 0.85, 1.0], dw=0.3)
    planet(L0, rng, 360, 56, 11, [ladder("teal1 rose2 rose3 rose4 rose5 rose6")], light=(-0.8, -0.4, 0.45),
           band_freq=3, turb=0.6, levels=[0, 0.08, 0.25, 0.45, 0.65, 0.85, 1.0], dw=0.3)
    mesas0 = [(120, 50, 70, 10, 40), (300, 26, 50, 8, 26), (560, 80, 84, 12, 60), (650, 18, 110, 6, 20),
              (820, 44, 58, 10, 40)]
    top0, own0, rel0 = mesa_profile(W0, rng, 318, mesas0)
    paint_mesas(L0, top0, own0, rel0, mesas0, ladder("teal1 teal2 teal2 teal3 ice4"), base=318)
    mist(L0, 300, 400, "teal3", dpx=8, wobble=(Noise(W0, 8, rng, 2)(L0.X, L0.Y) - 0.5) * 10)
    mist(L0, 340, 400, "steel4", dpx=6, wobble=(Noise(W0, 8, rng, 2)(L0.X, L0.Y) - 0.5) * 8)

    # layer 1: nearer mesas, a mist bank at their feet
    L1 = Layer(W)
    mesas1 = [(150, 64, 130, 14, 70), (250, 16, 170, 6, 30), (520, 40, 96, 12, 50), (760, 100, 156, 16, 90),
              (1100, 56, 110, 12, 60)]
    top1, own1, rel1 = mesa_profile(W, rng, 372, mesas1, noise_amp=4)
    paint_mesas(L1, top1, own1, rel1, mesas1, ladder("brown1 brown2 skin2 tan3 tan4"), base=372)
    # hanging vegetation on the mesa tops
    veg = (L1.Y >= top1[None, :]) & (L1.Y < top1[None, :] + 3 + 4 * Noise(W, 60, rng, 2)(L1.X, L1.Y * 0)) & L1.a
    L1.put(veg, "green2")
    mist(L1, 322, 400, "teal3", dpx=8, wobble=(Noise(W, 10, rng, 2)(L1.X, L1.Y) - 0.5) * 14)
    mist(L1, 356, 400, "steel4", dpx=6, wobble=(Noise(W, 10, rng, 2)(L1.X, L1.Y) - 0.5) * 10)

    # layer 2: giant umbrella trees in the haze
    L2 = Layer(W)
    trunk2 = fogged("olive1 brown2 tan3", sky_h, 0.32)
    cap2 = fogged("teal1 green1 green2 green3 lime3", sky_h, 0.32)
    for x, h, cw, tiers, lean in ((90, 250, 150, 3, 0.05), (420, 190, 110, 2, -0.08), (690, 280, 180, 3, 0.04),
                                  (980, 210, 120, 2, 0.1), (1180, 160, 80, 1, -0.05)):
        giant_tree(L2, rng, x, 404, h, cw, trunk2, cap2, tiers, tendrils=mix("teal1", sky_h, 0.3), lean=lean,
                   spots=mix("lime3", sky_h, 0.45))
    mist(L2, 366, 400, "teal3", dpx=6, wobble=(Noise(W, 12, rng, 2)(L2.X, L2.Y) - 0.5) * 10)

    # layer 3: near dark trees and fern fronds
    L3 = Layer(W)
    trunk3 = ladder("outline green1 olive1")
    cap3 = ladder("outline teal0 green1 teal1 green2")
    giant_tree(L3, rng, 260, 410, 330, 260, trunk3, cap3, 2, tendrils=col("green1"), lean=0.03,
               spots=col("teal1"))
    giant_tree(L3, rng, 980, 410, 240, 170, trunk3, cap3, 1, tendrils=col("green1"), lean=-0.06, spots=col("teal1"))
    for x in (60, 190, 330, 560, 640, 900, 1060, 1200):
        fern(L3, rng, x, 404, rng.uniform(40, 80), col("green1"), col("teal1"), n=7)
    L3.put(L3.Y >= 396, "outline")

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.05, 0.02), Spec(0.15, 0.05), Spec(0.32, 0.1), Spec(0.6, 0.2)]
    notes = """jungle_a: Thessa by day: teal sky with high clouds, two moons (pale and rose), far and near mesas
    standing in mist, giant umbrella trees in the haze, near dark trees and ferns."""
    return layers, specs, notes


# ----------------------------------------------------------------------------------------------------- jungle_b

def canopy(L, rng, base, n, rmin, rmax, fill, rim=None, dots=None, dot_density=0.004, jitter=8, emergent=()):
    """A backlit canopy band: round crowns along base, filled down to the bottom, an optional rim on the top edge,
    bioluminescent dots inside, and emergent umbrella trees [(x, height, cap width)] rising above it."""
    top = crowns(L.w, rng, base, n, rmin, rmax, jitter)
    m = L.Y >= top[None, :]
    for x, h, cw in emergent:
        ch = cw * 0.22
        cy = base - h
        trunk = (np.abs(wdx(L.X, x, L.w)) < max(1.5, cw * 0.04)) & (L.Y > cy) & (L.Y < base + 10)
        cap = blob(L, x, cy, cw / 2, ch) & (L.Y <= cy + ch * 0.25)
        m |= trunk | cap
    L.put(m, fill)
    if rim is not None:
        L.put(edge(m, 0, -1), rim)
    if dots is not None:
        inner = m & ~grow(edge(m, 0, -1), 2)
        pick = (rng.random(L.a.shape) < dot_density) & inner
        ys, xs = np.nonzero(pick)
        for y, x in zip(ys, xs):
            light(L, x, y, dots[int(rng.integers(0, len(dots)))])
    return m, top


def pods(L, rng, x, y, n, cols, spread=14, stalk="outline"):
    """A cluster of hanging glowing pods under (x, y): stalks with oval bulbs (dark rim, glowing core)."""
    for _ in range(n):
        px = x + rng.uniform(-spread, spread)
        ln = rng.uniform(4, 22)
        py = y + ln
        L.put((np.abs(wdx(L.X, px, L.w)) < 0.5) & (L.Y >= y) & (L.Y < py), stalk)
        rx, ry = rng.uniform(1.6, 3.2), rng.uniform(2.4, 4.4)
        b = blob(L, px, py + ry, rx, ry)
        core = blob(L, px - 0.4, py + ry - 0.6, max(0.8, rx - 1), max(1.0, ry - 1.4))
        L.put(b, cols[0], keep=True, glow=True)
        L.put(core, cols[1], keep=True, glow=True)
        L.put(_px(L, px - 1, py + ry - 1) & b, cols[2], keep=True, glow=True)


def jungle_b(seed):
    """Thessa at dusk: a magenta and orange sky with a setting sun, backlit canopies with bioluminescence."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280

    # layer 0: the dusk sky, the sun on the horizon, lit cloud streaks, the far canopy line
    L0 = Layer(W0)
    wob = (Noise(W0, 4, rng, 3)(L0.X, L0.Y * 0.3) - 0.5) * 20
    vbands(L0, "violet1", [(60, "purple1"), (120, "purple2"), (178, "magenta2"), (228, "crimson2"),
                           (262, "red2"), (288, "orange2"), (308, "orange3")], dpx=7, wobble=wob)
    sx, sy = 560, 316
    d = np.sqrt(wdx(L0.X, sx, W0) ** 2 + ((L0.Y - sy) * 1.0) ** 2)
    for r, c in ((70, "orange3"), (48, "orange4"), (30, "yellow5"), (22, "yellow6")):
        cover = np.clip((r + 3 - d) / 6, 0, 1)
        L0.put(dither_mask(cover, L0.by) if r > 25 else d <= r, c, keep=True, glow=r < 40)
    # cloud streaks: dark violet bodies, their undersides lit by the sun
    cl = gas_field(L0, rng, cells=3, warp=180, streak=0.45, sy=2.6, octaves=5)
    env = swoosh(L0, rng, 150, 40, 70)
    v = stretch(cl * env, 0, 99.7)
    body = shrink(grow(v > 0.45, 1), 1)
    L0.put(body & (L0.Y < 150), "purple2")
    L0.put(body & (L0.Y >= 150), "magenta2")
    under = body & ~shift(body, 0, 2)
    near_sun = np.clip(1 - np.abs(wdx(L0.X, sx, W0)) / 420, 0, 1)
    L0.put(under & (near_sun > 0.3), "orange3")
    L0.put(under & (near_sun <= 0.3), "crimson3")
    L0.put(body & ~shift(body, 0, 1) & (near_sun > 0.5), "orange4")
    core = shrink(v > 0.66, 1)
    L0.put(core, "violet2")
    L0.put(core & ~shift(core, 0, 1), "magenta3")
    canopy(L0, rng, 330, 26, 12, 30, "purple1", rim="crimson2", dots=["cyan3", "lime3"], dot_density=0.0015)
    L0.put(L0.Y >= 380, "purple1")

    # layer 1: a nearer canopy with emergent umbrella trees, cyan and lime sparks
    L1 = Layer(W)
    canopy(L1, rng, 340, 20, 24, 48, "purple0", rim="red2", dots=["cyan4", "lime4", "cyan3"], dot_density=0.003,
           emergent=((180, 120, 90), (470, 80, 60), (820, 150, 120), (1100, 96, 70)))

    # layer 2: big trees, dark, hung with glowing pods
    L2 = Layer(W)
    dark = ladder("outline purple0 purple1")
    for x, h, cw in ((120, 260, 200), (560, 300, 240), (980, 230, 170)):
        top = 400 - h
        ch = cw * 0.2
        trunk = (np.abs(wdx(L2.X, x, W) + (L2.Y - 400) * 0.04) < cw * 0.05 + np.clip((L2.Y - 360) / 4, 0, 10)) \
            & (L2.Y > top)
        cap = blob(L2, x, top, cw / 2, ch) & (L2.Y <= top + ch * 0.3)
        cap2 = blob(L2, x - cw * 0.3, top + 6, cw * 0.28, ch * 0.7) | blob(L2, x + cw * 0.32, top + 10, cw * 0.25,
                                                                               ch * 0.6)
        m = trunk | cap | (cap2 & (L2.Y <= top + ch * 0.5))
        L2.put(m, dark[1])
        L2.put(edge(m, 0, -1), "crimson2")
        L2.put(edge(m, -1, 0) & ~edge(m, 0, -1), "purple1")
        L2.put(edge(m, 1, 0) & trunk, dark[0])
        for k in range(7):
            px = x + rng.uniform(-0.45, 0.45) * cw
            pods(L2, rng, px, top + ch * 0.25, int(rng.integers(2, 5)),
                 ["teal2", "teal4", "teal6"] if k % 2 else ["green2", "lime4", "lime6"], spread=8,
                 stalk=col("purple0"))
    L2.put(L2.Y >= 392, "purple0")

    # layer 3: near ferns and vines with glowing flowers, almost black
    L3 = Layer(W)
    for x in range(30, W, 90):
        x2 = x + rng.uniform(-20, 20)
        fern(L3, rng, x2, 404, rng.uniform(50, 100), col("outline"), col("purple1"), n=8)
        if rng.random() < 0.6:
            light(L3, x2 + rng.uniform(-30, 30), rng.uniform(340, 380), "cyan5", size=2)
    for x in (300, 340, 880, 1180):
        ln = rng.uniform(70, 160)
        xs = x + 4 * np.sin(np.arange(int(ln)) / 9)
        for y, xx in enumerate(xs):
            L3.put(_px(L3, xx, y), "outline")
            if y % 13 == 7:
                L3.put(_px(L3, xx + 1, y) | _px(L3, xx - 1, y), "outline")
        light(L3, xs[-1], int(ln), "magenta5", size=2)
    L3.put(L3.Y >= 396, "outline")

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.05, 0.02), Spec(0.16, 0.05), Spec(0.34, 0.1), Spec(0.62, 0.2)]
    notes = """jungle_b: Thessa at dusk: a violet-magenta-orange sky with a setting sun and lit cloud streaks, backlit
    canopies with bioluminescent sparks, big trees hung with glowing pods, near ferns and vines (the vines run
    off the top of layer 3 and repeat upwards)."""
    return layers, specs, notes


# -------------------------------------------------------------------------------------------------------- hives

def organic_column(L, rng, cx, width, lad, rim, glow_x, ribs=9, honey=False, bulge=0.45, flare=1.6, cells=5):
    """A ribbed organic column from ceiling to floor, flared at both ends, shaded as a cylinder lit from the side
    of glow_x (that edge gets the rim colour). lad: dark to light (3+)."""
    m, u = column_profile(L, cx, width, rng, bulge=bulge, flare=flare, cells=cells, ret_u=True)
    lad = np.asarray(lad, np.uint8)
    side = 1 if wdx(glow_x, cx, L.w) > 0 else -1
    v = np.clip(0.5 + 0.55 * u * side, 0, 0.999) ** 1.3
    wob = (Noise(L.w, 30, rng, 2)(L.X, L.Y * 0.2) - 0.5) * 8 + np.abs(u) * 4
    rib = (((L.Y + wob) % ribs) < 1.0) & (np.abs(u) < 0.6) & (u * side > 0.0)
    v = np.where(rib, v * 0.82, v)
    idx, dith = band(v, len(lad), 0.4, None, L.by)
    L.paint(m, idx, lad, dith & ~rib)
    lit = edge(m, side, 0)
    L.put(lit, rim)
    if honey:
        hx = L.X + ((L.Y // 6) % 2) * 3.5
        cell = ((hx % 7) < 1) | ((L.Y % 6) < 1)
        hz = m & (np.abs(u) < 0.7) & (Noise(L.w, 8, rng, 2)(L.X, L.Y) > 0.62)
        L.put(hz & cell, lad[0])
        L.put(hz & ~cell & ((L.X.astype(np.int32) * 3 + L.Y.astype(np.int32)) % 11 == 0), rim, keep=True)
    return m


def drips(L, rng, mask, n, colour, tip, max_len=24):
    """Resin strands dripping from the lower edges of mask, each with a glowing drop."""
    lower = edge(mask, 0, 1)
    ys, xs = np.nonzero(lower & (L.Y < 200))
    if len(ys) == 0:
        return
    for i in rng.choice(len(ys), min(n, len(ys)), replace=False):
        x, y = xs[i], ys[i]
        ln = int(rng.uniform(4, max_len))
        L.put((np.abs(wdx(L.X, x, L.w)) < 0.5) & (L.Y > y) & (L.Y <= y + ln) & ~mask, colour)
        light(L, x, y + ln + 1, tip)


def hive_a(seed):
    """Underground: amber-lit cavern depths with organic columns, ribbed and honeycombed, dripping resin."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280
    gx, gy = 470, 236

    # layer 0: the amber glow of the depths, far columns in silhouette, ceiling and floor
    L0 = Layer(W0)
    dx = wdx(L0.X, gx, W0)
    r = np.sqrt((dx / 1.9) ** 2 + (L0.Y - gy) ** 2)
    wob = (Noise(W0, 5, rng, 4, 0.6)(L0.X, L0.Y) - 0.5) * 70
    bands_at(L0, -(r + wob), "brown0", [(-215, "brown1"), (-160, "brown2"), (-112, "orange2"), (-72, "orange3"),
                                        (-40, "orange4"), (-18, "yellow5")], dpx=5)
    L0.glow[r + wob < 72] = True
    for x, w_ in ((150, 30), (300, 22), (380, 16), (560, 18), (640, 26), (800, 34), (900, 20)):
        m = column_profile(L0, x, w_, rng, bulge=0.6, flare=2.2, cells=6)
        d = np.sqrt((wdx(x, gx, W0) / 1.9) ** 2)
        L0.put(m, "brown2" if d < 110 else "brown1")
        L0.put(edge(m, 1 if x < gx else -1, 0), "orange3" if d < 110 else "brown2")
    ceil = L0.Y < 26 + 14 * Noise(W0, 12, rng, 3)(L0.X, np.zeros_like(L0.X))
    floor = L0.Y > 360 - 12 * Noise(W0, 10, rng, 3)(L0.X, np.zeros_like(L0.X) + 50)
    L0.put(ceil | floor, "brown0")
    L0.put(edge(floor, 0, -1), "brown1")

    # layer 1: organic columns in the haze, rim lit by the glow
    L1 = Layer(W)
    gx1 = gx * W / W0
    lad1 = ladder("brown0 brown1 brown2 skin2")
    for x, w_ in ((70, 46), (330, 34), (520, 26), (900, 52), (1150, 30)):
        organic_column(L1, rng, x, w_, lad1, col("orange3"), gx1, ribs=10, honey=w_ > 40, bulge=0.6)
    for x, y, rr in ((70, 150, 30), (900, 240, 34), (330, 300, 20)):
        nod = blob(L1, x, y, rr * 0.75, rr * 0.6)
        v = np.clip(0.5 + 0.5 * wdx(L1.X, x, W) / rr * (1 if x < gx1 else -1) - (L1.Y - y) / rr * 0.3, 0, 0.999)
        idx, dith = band(v, 4, 0.4, None, L1.by)
        L1.paint(nod, idx, lad1, dith)
        L1.put(edge(nod, 1 if x < gx1 else -1, 0), "orange3")
    roof = L1.Y < 14 + 10 * Noise(W, 14, rng, 3)(L1.X, np.zeros_like(L1.X))
    L1.put(roof, "brown0")
    base1 = L1.Y > 374 - 10 * Noise(W, 12, rng, 3)(L1.X, np.zeros_like(L1.X) + 70)
    L1.put(base1, "brown0")
    L1.put(edge(base1, 0, -1), "brown2")

    # layer 2: closer columns with honeycomb and dripping resin
    L2 = Layer(W)
    lad2 = ladder("brown0 brown0 brown1 brown2")
    allm = np.zeros(L2.a.shape, bool)
    for x, w_ in ((220, 64), (700, 50), (1040, 72)):
        allm |= organic_column(L2, rng, x, w_, lad2, col("orange4"), gx1, ribs=12, honey=True, bulge=0.5)
    drips(L2, rng, allm, 14, col("brown1"), "yellow5")
    for x0, x1, y0 in ((250, 680, 12), (730, 1010, 20)):
        xs = np.arange(x0, x1)
        t = (xs - x0) / (x1 - x0)
        ys = y0 + 30 * 4 * t * (1 - t) + 4 * np.sin(xs / 13)
        mem = np.zeros(L2.a.shape, bool)
        for x, y in zip(xs, ys):
            mem[0:int(y), x % W] = True
        L2.put(mem, "brown0")
        L2.put(edge(mem, 0, 1), "brown1")
        drips(L2, rng, mem, 8, col("brown0"), "orange5", 30)

    # layer 3: near massive columns, nearly black, amber rims
    L3 = Layer(W)
    lad3 = ladder("brown0 brown0 brown1 brown1")
    for x, w_ in ((420, 70), (1180, 54)):
        organic_column(L3, rng, x, w_, lad3, col("orange3"), gx1 + 300, ribs=16, bulge=0.45, flare=1.4)
    L3.put(L3.Y > 388, "brown0")

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.06, 0.03), Spec(0.18, 0.06), Spec(0.36, 0.1), Spec(0.66, 0.2)]
    notes = """hive_a: amber-lit cavern depths: a glowing core far away, organic ribbed columns in three depths
    (honeycomb, dripping resin with glowing drops), ceiling membranes. Columns run off the top and bottom of
    every layer and repeat outwards."""
    return layers, specs, notes


def egg_sac(L, rng, cx, cy, rx, ry, cols):
    """A glowing egg sac: dark membrane rim, glowing jelly, a curled embryo shadow, a highlight.
    cols: [rim, jelly dark, jelly, core, highlight, embryo]."""
    out = blob(L, cx, cy, rx, ry)
    jelly = blob(L, cx, cy, rx - 1, ry - 1)
    core = blob(L, cx - rx * 0.1, cy + ry * 0.1, rx * 0.65, ry * 0.6)
    L.put(out, cols[0], keep=True)
    L.put(jelly, cols[1], keep=True, glow=True)
    L.put(core, cols[2], keep=True, glow=True)
    emb = blob(L, cx + rx * 0.1, cy + ry * 0.3, rx * 0.4, ry * 0.3) & ~blob(L, cx + rx * 0.3, cy + ry * 0.15, rx * 0.2,
                                                                            ry * 0.16)
    L.put(emb & core, cols[5], keep=True)
    hl = blob(L, cx - rx * 0.45, cy - ry * 0.45, max(0.8, rx * 0.15), max(0.8, ry * 0.15))
    L.put(hl, cols[4], keep=True, glow=True)
    L.put(core & ~emb & (L.Y < cy - ry * 0.2), cols[3], keep=True, glow=True)
    return out


def hive_b(seed):
    """Underground: deep violet tunnels receding into a glow, rib arches, clusters of glowing egg sacs."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280
    vx, vy = 480, 200

    # layer 0: the tunnel receding: rings of ribs around the vanishing point, lighter with depth
    L0 = Layer(W0)
    dx = wdx(L0.X, vx, W0)
    rho = np.sqrt((dx / 1.6) ** 2 + (L0.Y - vy) ** 2)
    ang = np.arctan2(L0.Y - vy, dx / 1.6)
    wob = (Noise(W0, 8, rng, 3)(ang * 150 + 500, rho * 0.4) - 0.5) * 0.35
    lr = np.log(np.maximum(rho, 4) / 6) + wob
    ring = (lr * 2.2) % 1.0
    depth = np.clip(1 - rho / 300, 0, 1) ** 1.3
    lit_side = np.clip(0.5 - (L0.Y - vy) / (rho + 1) * 0.5, 0, 1)
    v = depth * 0.92 + np.where(ring < 0.2, 0.1 * lit_side, 0.0) - np.where(ring > 0.8, 0.06, 0.0)
    bands_at(L0, v, "outline", [(0.14, "violet0"), (0.3, "violet1"), (0.46, "purple1"), (0.6, "purple2"),
                                (0.74, "violet2"), (0.86, "purple3"), (0.95, "magenta3")], dpx=0.02)
    L0.glow[v > 0.86] = True
    L0.put(L0.Y < 8, "outline")
    L0.put(L0.Y > 392, "outline")

    # layer 1: rib arches spanning the tunnel
    L1 = Layer(W)
    lad1 = ladder("outline violet0 violet1 purple2")
    ribm = np.zeros(L1.a.shape, bool)
    for cx in (0, 640):
        for k, (rx, ry, th) in enumerate(((330, 330, 22), (300, 300, 16))):
            ccx = cx + k * 320
            d = np.sqrt((wdx(L1.X, ccx, W) / rx) ** 2 + ((L1.Y - 400) / ry) ** 2)
            tt = th / rx * (1 + 0.4 * Noise(W, 10, rng, 2)(L1.X, L1.Y))
            ribm |= (d < 1) & (d > 1 - tt)
    L1.put(ribm, lad1[1])
    ins = ribm & shift(ribm, 0, 1) & ~edge(ribm, 0, -1)
    bump = (Noise(W, 40, rng, 2)(L1.X, L1.Y * 1.5) > 0.6) & ins
    L1.put(bump, lad1[2])
    L1.put(edge(ribm, 0, 1), lad1[3])
    L1.put(edge(ribm, 0, -1), lad1[0])
    floor1 = L1.Y > 372 - 8 * Noise(W, 10, rng, 2)(L1.X, np.zeros_like(L1.X))
    L1.put(floor1, "violet0")
    L1.put(edge(floor1, 0, -1), "violet1")

    # layer 2: clusters of glowing egg sacs, hanging and on the floor
    L2 = Layer(W)
    lime = [col("green1"), col("green2"), col("lime4"), col("lime5"), col("lime7"), col("lime3")]
    teal = [col("teal1"), col("teal2"), col("teal4"), col("teal5"), col("teal7"), col("teal3")]
    floor2 = L2.Y > 360 - 16 * Noise(W, 8, rng, 3)(L2.X, np.zeros_like(L2.X))
    L2.put(floor2, "outline")
    L2.put(edge(floor2, 0, -1), "purple1")
    for cx, cy, n, cols in ((160, 336, 9, lime), (520, 348, 6, teal), (880, 330, 10, lime), (1160, 344, 5, teal)):
        for k in range(n):
            ex = cx + rng.uniform(-44, 44)
            ey = cy + rng.uniform(-18, 12)
            rx = rng.uniform(6, 13)
            egg_sac(L2, rng, ex, ey, rx, rx * rng.uniform(1.15, 1.4), cols)
    for cx, n, cols in ((340, 5, teal), (700, 6, lime), (1020, 4, teal)):
        stalk = Draw(W).line([(cx, 0), (cx + 4, 30), (cx - 2, 60)], 3).mask()
        L2.put(stalk, "purple0")
        L2.put(edge(stalk, -1, 0), "purple1")
        for k in range(n):
            ex = cx + rng.uniform(-18, 18)
            ey = 64 + rng.uniform(0, 40)
            rx = rng.uniform(5, 10)
            egg_sac(L2, rng, ex, ey, rx, rx * 1.3, cols)

    # layer 3: near dark tendrils with a few big sacs
    L3 = Layer(W)
    dr = Draw(W)
    for x0 in (90, 600, 980):
        pts = [(x0 + 10 * np.sin(y / 23 + x0), y) for y in range(0, 230, 6)]
        dr.line(pts, 7)
        dr.line([(x + 4, y) for x, y in pts[:20]], 3)
    tm = dr.mask()
    L3.put(tm, "outline")
    L3.put(edge(tm, -1, 0), "purple1")
    L3.put(edge(tm, 1, 0) & ~edge(tm, -1, 0), "violet1")
    for x0, y0, cols in ((96, 236, lime), (604, 236, teal), (984, 236, lime)):
        egg_sac(L3, rng, x0, y0, 12, 16, cols)
    base3 = L3.Y > 384 - 10 * Noise(W, 6, rng, 2)(L3.X, np.zeros_like(L3.X))
    L3.put(base3, "outline")

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.05, 0.03), Spec(0.18, 0.06), Spec(0.36, 0.1), Spec(0.66, 0.2)]
    notes = """hive_b: deep violet tunnels: rings of ribs receding into a magenta glow, rib arches, clusters of
    glowing egg sacs (lime and teal) on the floor and hanging on stalks, near tendrils that run off the top."""
    return layers, specs, notes


SCENES = {"jungle_a": jungle_a, "jungle_b": jungle_b, "hive_a": hive_a, "hive_b": hive_b}
