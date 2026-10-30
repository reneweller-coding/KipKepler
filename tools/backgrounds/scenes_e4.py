"""Backgrounds of episode 4, the Gloam dreadnought: foundry (forge halls, the hull outside) and citadel (the core)."""
import numpy as np

from bgkit import (Draw, Layer, Noise, Spec, band, bands_at, col, dither_mask, edge, fogged, gas_field, grow, ladder,
                   levels, lift, mix, planet, ramp_step, shift, shrink, stars, stretch, swoosh, truss, vbands, wdx)
from shapes import (_px, blob, cone, hazard, lamp_row, light, local, plate, rock, skyline, stamp, window_strips)


# ------------------------------------------------------------------------------------------------------ helpers

def furnace(L, rng, x, base, w, h, lad, mouth):
    """A furnace block: a tapered body with a chimney stack, an arched glowing mouth (bands of mouth colours,
    brightest at the bottom) and lit seams. lad: [dark, body, lit, rim]."""
    dr = Draw(L.w)
    dr.poly([(x - w / 2, base), (x - w * 0.42, base - h), (x + w * 0.42, base - h), (x + w / 2, base)])
    dr.rect(x - w * 0.12, 0, x + w * 0.12, base - h)
    dr.rect(x - w * 0.16, base - h - 6, x + w * 0.16, base - h)
    m = dr.mask()
    plate(L, m, base - h, base, lad, bands=(0.06, 0.5))
    mw, mh = w * 0.3, h * 0.38
    dx = wdx(L.X, x, L.w) / (mw / 2)
    arch = (np.abs(dx) <= 1) & (L.Y <= base) & (L.Y >= base - mh + (mh * 0.35) * (1 - np.sqrt(np.clip(1 - dx * dx, 0, 1))))
    t = (base - L.Y) / mh
    idx = np.clip((1 - t) * len(mouth) + (L.by - 0.5) * 0.5, 0, len(mouth) - 1).astype(np.int32)
    L.paint(arch, idx, ladder(mouth), np.ones(L.a.shape, bool), glow=True)
    L.put(edge(arch, 0, -1) | edge(arch, -1, 0) | edge(arch, 1, 0), lad[0])
    return m


def smoke(L, rng, y0, amp, width, cols, thresholds, cells=3, density=1.0):
    """Billowing smoke: a wispy field quantized into a few dithered levels (binary alpha)."""
    env = swoosh(L, rng, y0, amp, width)
    v = stretch(gas_field(L, rng, cells=cells, warp=200, streak=0.35, sy=1.4) * env, 0, 99.8) * density
    levels(L, v, cols, thresholds, dpx=0.05)
    return v


def circuit(L, rng, mask, n, cols, step=4, max_len=60, via=True):
    """Glowing circuit traces inside mask: random walks on a grid with 90 / 45 degree turns, each ending in a via."""
    ys, xs = np.nonzero(mask & (L.Y.astype(np.int32) % step == 0) & (L.X.astype(np.int32) % step == 0))
    if len(ys) == 0:
        return
    dirs = [(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1)]
    for _ in range(n):
        i = int(rng.integers(0, len(ys)))
        x, y = int(xs[i]), int(ys[i])
        d = int(rng.choice([0, 2, 4, 6]))
        c = col(cols[int(rng.integers(0, len(cols)))])
        length = int(rng.integers(max_len // 4, max_len))
        pts = [(x, y)]
        for k in range(length):
            if rng.random() < 0.08:
                d = (d + int(rng.choice([-1, 1]))) % 8
            elif rng.random() < 0.05:
                d = (d + int(rng.choice([-2, 2]))) % 8
            dx, dy = dirs[d]
            nx, ny = x + dx, y + dy
            if not (0 <= ny < L.h) or not mask[ny, nx % L.w]:
                break
            x, y = nx, ny
            pts.append((x, y))
        if len(pts) < 6:
            continue
        m = np.zeros(L.a.shape, bool)
        for px, py in pts:
            m[py, px % L.w] = True
        L.put(m, c, keep=True, glow=True)
        if via:
            vm = np.zeros(L.a.shape, bool)
            for px, py in (pts[0], pts[-1]):
                for ox in (-1, 0, 1):
                    for oy in (-1, 0, 1):
                        if 0 <= py + oy < L.h and (ox or oy):
                            vm[py + oy, (px + ox) % L.w] = True
            L.put(vm & mask, c, keep=True, glow=True)
            for px, py in (pts[0], pts[-1]):
                L.put(_px(L, px, py), "outline", keep=True)


def shard(L, cx, cy, w, h, lad, rim, tilt=0.0, kind=0):
    """A floating angular monolith: kind 0 a long diamond, 1 an inverted pyramid with a flat top, 2 a slab.
    Two faces (lit left, dark right) and a glowing rim edge. lad: [dark, mid, lit]."""
    c, s = np.cos(tilt), np.sin(tilt)

    def P(u, v):
        return (cx + u * c - v * s, cy + u * s + v * c)

    if kind == 0:
        pts = [P(0, -h / 2), P(w / 2, -h * 0.1), P(0, h / 2), P(-w / 2, -h * 0.1)]
        split = [P(0, -h / 2), P(w * 0.1, h / 2)]
    elif kind == 1:
        pts = [P(-w / 2, -h * 0.3), P(w / 2, -h * 0.3), P(w * 0.1, h / 2)]
        split = [P(-w * 0.1, -h * 0.3), P(w * 0.1, h / 2)]
    else:
        pts = [P(-w / 2, -h / 2), P(w / 2, -h / 2 + h * 0.15), P(w / 2, h / 2), P(-w / 2, h / 2 - h * 0.15)]
        split = [P(w * 0.15, -h / 2), P(w * 0.15, h / 2)]
    m = Draw(L.w).poly(pts).mask()
    sx0, sy0 = split[0]
    sx1, sy1 = split[1]
    side = (wdx(L.X, sx0, L.w) * (sy1 - sy0) - (L.Y - sy0) * (sx1 - sx0)) > 0
    lad = np.asarray(lad, np.uint8)
    L.put(m & ~side, lad[2])
    L.put(m & side, lad[0])
    top = m & (L.Y < cy - h * 0.15) & ~side
    L.put(top, lad[1])
    L.put(edge(m, 0, -1) | edge(m, -1, 0), rim, keep=True, glow=True)
    return m


# ---------------------------------------------------------------------------------------------------- foundry_a

def foundry_a(seed):
    """The dreadnought's forge halls: furnaces, crucibles pouring, molten channels, smoke, a red-orange haze."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280

    # layer 0: the hall's back wall in a red haze, dark furnaces with glowing mouths
    L0 = Layer(W0)
    wob = (Noise(W0, 5, rng, 3)(L0.X, L0.Y * 0.4) - 0.5) * 26
    vbands(L0, "red0", [(110, "crimson1"), (200, "red1"), (262, "red2"), (310, "orange2")], dpx=8, wobble=wob)
    for x in range(60, W0, 120):
        L0.put((np.abs(wdx(L0.X, x, W0)) < 7) & (L0.Y < 340), "crimson1")
        L0.put((np.abs(wdx(L0.X, x - 7, W0)) < 0.6) & (L0.Y < 340), "red2")
    for x, w, h in ((150, 140, 160), (480, 190, 200), (800, 150, 170)):
        fm = furnace(L0, rng, x, 340, w, h, ladder("red0 red0 crimson1 red1"),
                     ["red2", "orange3", "orange4", "yellow5", "yellow6"])
    floor = L0.Y >= 340
    L0.put(floor, "red0")
    for x, w, h in ((150, 140, 160), (480, 190, 200), (800, 150, 170)):
        spill = floor & (np.clip(1 - np.sqrt((wdx(L0.X, x, W0) / (w * 0.4)) ** 2 + ((L0.Y - 340) / 30) ** 2), 0, 1)
                         * 1.2 > L0.by)
        L0.put(spill, "red2", keep=True)
    L0.put(floor & (L0.Y < 342), "red1")

    # layer 1: crucibles on an overhead rail pouring molten streams into a channel, lit from below
    L1 = Layer(W)
    lad1 = ladder("red0 red0 crimson1 red1 red2")
    dr = Draw(W)
    dr.rect(0, 30, W, 42)
    for x in range(0, W, 12):
        dr.rect(x, 42, x + 2, 46)
    rail = dr.mask()
    plate(L1, rail, 30, 46, lad1)
    for x, tilt in ((240, 0.5), (720, 0.0), (1080, 0.35)):
        hook = Draw(W).line([(x - 20, 46), (x - 26, 128)], 2).line([(x + 20, 46), (x + 26, 128)], 2).mask()
        L1.put(hook, "red0")
        cr = Draw(W)
        c, s = np.cos(tilt), np.sin(tilt)
        pts = [(-36, -28), (36, -28), (28, 28), (-28, 28)]
        cr.poly([(x + u * c - v * s, 156 + u * s + v * c) for u, v in pts])
        cm = cr.mask()
        v = np.clip((L1.Y - 128) / 60, 0, 0.999)
        idx, dith = band(v, 3, 0.3, None, L1.by)
        L1.paint(cm, idx, ladder("red0 crimson1 red2"), dith)
        L1.put(edge(cm, 0, 1) | (edge(cm, 1, 0) & (L1.Y > 156)), "orange3")
        L1.put(edge(cm, 0, -1), "orange4", keep=True, glow=True)
        lipx, lipy = x + 36 * c + 28 * s, 156 + 36 * s - 28 * c
        if tilt > 0.2:
            sx = lipx + 2 + (L1.Y - lipy) * 0.05
            st = (np.abs(wdx(L1.X, sx, W)) < 2.5) & (L1.Y > lipy) & (L1.Y < 372)
            L1.put(st, "orange5", keep=True, glow=True)
            L1.put(st & (np.abs(wdx(L1.X, sx, W)) < 1), "yellow6", keep=True, glow=True)
            for k in range(16):
                light(L1, lipx + rng.normal(0, 10), 368 - abs(rng.normal(0, 14)), "yellow5")
    tr = (L1.Y >= 364)
    L1.put(tr, "red0")
    ch = (L1.Y >= 370) & (L1.Y < 378)
    mv = Noise(W, 40, rng, 2)(L1.X, L1.Y * 4)
    L1.paint(ch, np.where(mv > 0.6, 2, np.where(mv > 0.4, 1, 0)), ladder("orange3 orange4 yellow5"),
             np.zeros(L1.a.shape, bool), glow=True)
    L1.put(edge(tr, 0, -1), "red2")
    for x in range(0, W, 160):
        L1.put((np.abs(wdx(L1.X, x, W)) < 5) & (L1.Y >= 46) & (L1.Y < 64), "red0")

    # layer 2: drifting smoke wisps and embers (scrolls on its own)
    L2 = Layer(W)
    env = swoosh(L2, rng, 120, 40, 60)
    v = stretch(gas_field(L2, rng, cells=3, warp=220, streak=0.5, sy=1.6) * env, 0, 99.8)
    L2.put((v > 0.45) & (np.clip((v - 0.45) * 3, 0, 1) > L2.by), "red0", keep=True)
    L2.put((v > 0.7) & (np.clip((v - 0.7) * 4, 0, 1) > L2.by), "crimson0", keep=True)
    env2 = swoosh(L2, rng, 300, 20, 36)
    v2 = stretch(gas_field(L2, rng, cells=4, warp=160, streak=0.5, sy=1.6) * env2, 0, 99.8)
    L2.put((v2 > 0.5) & (np.clip((v2 - 0.5) * 3, 0, 1) > L2.by), "red1", keep=True)
    for _ in range(70):
        light(L2, rng.uniform(0, W), rng.uniform(140, 380), "orange5" if rng.random() < 0.6 else "yellow5")

    # layer 3: near girders, chains and a pipe run, warm darks with orange rims
    L3 = Layer(W)
    dr = Draw(W)
    for x in (200, 900):
        dr.rect(x - 16, 0, x + 16, 400)
    truss(dr, 0, 14, W, 14, 18, 18, cw=3, bw=2)
    for x, ln in ((420, 180), (460, 120), (1120, 210)):
        for y in range(28, ln, 6):
            dr.ellipse(x - 2, y, x + 2, y + 6)
        dr.rect(x - 6, ln, x + 6, ln + 4)
    dr.rect(0, 376, W, 400)
    for x in range(0, W, 64):
        dr.rect(x, 370, x + 8, 376)
    m3 = dr.mask()
    L3.put(m3, "red0")
    L3.put(edge(m3, -1, 0) | edge(m3, 0, -1), "red2")
    L3.put(edge(m3, 1, 0) & ~edge(m3, 0, -1), "crimson1")
    L3.put(edge(m3, 0, 1) & (L3.Y > 20), "orange3")
    for x in (200, 900):
        hz = (np.abs(wdx(L3.X, x, W)) < 13) & (L3.Y > 320) & (L3.Y < 368)
        hazard(L3, hz, "orange2", "red0", 12)
    for x, y in ((420, 186), (460, 126), (1120, 216)):
        light(L3, x, y, "orange4")

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.06, 0.03), Spec(0.2, 0.06), Spec(0.3, 0.08, 0, -6), Spec(0.66, 0.2)]
    notes = """foundry_a: the dreadnought's forge halls: furnaces with glowing mouths in a red haze, crucibles on an
    overhead rail pouring molten metal into a glowing channel, drifting smoke (layer 2 scrolls by itself at
    -6 px/s), near girders, chains and pillars (they run off the top and repeat upwards)."""
    return layers, specs, notes


# ---------------------------------------------------------------------------------------------------- foundry_b

def foundry_b(seed):
    """Outside the dreadnought: its hull and towers against a burning planet."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280

    # layer 0: red-black space, the burning planet
    L0 = Layer(W0)
    vbands(L0, "red0", [(100, "crimson0"), (260, "red0")], dpx=8)
    stars(L0, rng, 160, y1=380, glints=2, tints=("orange", "yellow"), dim="slate", bright_frac=0.06)
    px_, py_, pr = 560, 170, 120
    d = np.sqrt(wdx(L0.X, px_, W0) ** 2 + (L0.Y - py_) ** 2)
    halo = (d > pr) & (d < pr + 18)
    hv = np.clip(1 - (d - pr) / 18, 0, 1)
    L0.put(halo & (hv * 0.9 > L0.by), "red1", keep=True)
    L0.put(halo & (hv * 0.6 > L0.by + 0.2), "red2", keep=True)
    disk = planet(L0, rng, px_, py_, pr, [ladder("red0 crimson1 brown1 red1 brown2 red2")],
                  light=(-0.7, -0.3, 0.6), band_freq=5, turb=1.4, levels=[0, 0.08, 0.22, 0.4, 0.6, 0.8, 1.0], dw=0.3)
    # lava fissures: long glowing lines with a dim halo, a few lava seas, brighter on the night side
    n1 = Noise(W0, 9, rng, 3, 0.5)(L0.X * 1.0, L0.Y * 1.3)
    inner = disk & (d < pr - 2)
    halo_c = (np.abs(n1 - 0.5) < 0.03) & inner
    cracks = (np.abs(n1 - 0.5) < 0.011) & inner
    seas = (Noise(W0, 40, rng, 2)(L0.X + 500, L0.Y) > 0.8) & inner
    L0.put(halo_c | (grow(seas, 1) & inner), "red2", keep=True)
    L0.put(cracks | seas, "orange4", keep=True, glow=True)
    L0.put((cracks | seas) & (Noise(W0, 16, rng, 2)(L0.X, L0.Y) > 0.62), "yellow5", keep=True, glow=True)
    # smoke plumes leaving the planet
    sm = stretch(gas_field(L0, rng, cells=4, warp=120, streak=0.6, sy=2.0), 0, 99) * np.clip(1 - np.abs(d - pr - 6) / 40, 0, 1)
    L0.put((sm > 0.45) & ~disk & (sm * 1.2 - 0.3 > L0.by), "brown1", keep=True)
    L0.put(edge(disk, 0, -1) | edge(disk, -1, 0), "orange3", keep=True, glow=True)

    # layer 1: the dreadnought's far superstructure
    L1 = Layer(W)
    xs = np.arange(W, dtype=np.float32)
    base1 = np.full(W, 330.0)
    lad1 = fogged("red0 crimson1 slate2 steel2", "crimson1", 0.25)
    skyline(L1, rng, base1, lad1, hmin=10, hmax=120, wmin=10, wmax=46, gap=(0, 4),
            height=lambda x: 0.25 + 0.9 * np.clip(1 - abs(wdx(x, 640, W)) / 500, 0, 1),
            win=("orange4", "red4"), win_on=0.2, mast_light="red5")
    L1.put(L1.Y >= 330, lad1[1])
    for y in (338, 352):
        window_strips(L1, L1.Y >= 330, [np.full(W, y)], rng, cols=("orange4", "red4"), on=0.5, seg=(10, 40),
                      gap=(10, 50))

    # layer 2: hull with turrets, glowing vents, antennas
    L2 = Layer(W)
    lad2 = ladder("outline red0 crimson1 slate2 steel2")
    hull_top = 300 + 20 * np.sin(2 * np.pi * xs / W) + 8 * np.sin(6 * np.pi * xs / W)
    hm = L2.Y >= hull_top[None, :]
    plate(L2, hm, 290, 400, lad2, bands=(0.03, 0.2))
    for x in range(20, W, 46):
        L2.put(hm & (np.abs(wdx(L2.X, x, W)) < 0.5) & (L2.Y > hull_top[x] + 4), lad2[1])
    for x in range(40, W, 90):
        v = hm & (np.abs(wdx(L2.X, x, W)) < 10) & (L2.Y > hull_top[x] + 14) & (L2.Y < hull_top[x] + 30) \
            & (L2.Y.astype(np.int32) % 3 == 0)
        L2.put(v, "orange4", keep=True, glow=True)
    for x, sz, ang in ((260, 30, -0.35), (780, 40, -0.2), (1110, 26, -0.45)):
        by = hull_top[x]
        dome = blob(L2, x, by, sz, sz * 0.6) & (L2.Y <= by + 2)
        plate(L2, dome, by - sz * 0.6, by, lad2)
        c, s = np.cos(ang), np.sin(ang)
        for off in (-5, 5):
            bar = Draw(W).line([(x + off * s * -1, by - sz * 0.35 + off * c * 0 + off * 0.0),
                                (x + 90 * c + off * -s, by - sz * 0.35 + 90 * s + off * c)], 5).mask()
            L2.put(bar, lad2[2])
            L2.put(edge(bar, 0, -1), lad2[4])
        light(L2, x, by - sz * 0.6 - 2, "red5")
    for x in (520, 940):
        dr = Draw(W)
        dr.rect(x - 2, hull_top[x] - 90, x + 2, hull_top[x])
        for k in range(4):
            dr.rect(x - 10 + k * 2, hull_top[x] - 80 + k * 16, x + 10 - k * 2, hull_top[x] - 78 + k * 16)
        am = dr.mask()
        L2.put(am, lad2[2])
        L2.put(edge(am, -1, 0), lad2[4])
        light(L2, x, hull_top[x] - 92, "red5", size=2)

    # layer 3: the near hull edge with spikes, a huge barrel silhouette
    L3 = Layer(W)
    dr = Draw(W)
    dr.rect(0, 380, W, 400)
    for x in range(0, W, 80):
        dr.poly([(x, 380), (x + 14, 330 + (x % 160) * 0.2), (x + 28, 380)])
    dr.poly([(560, 400), (600, 300), (1000, 260), (1004, 274), (620, 320), (640, 400)])
    m3 = dr.mask()
    L3.put(m3, "red0")
    L3.put(edge(m3, 0, -1) | edge(m3, -1, 0), "red2")
    L3.put(edge(m3, 1, 0) & ~edge(m3, 0, -1), "crimson1")
    light(L3, 1001, 266, "orange5", size=2)

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.04, 0.02), Spec(0.14, 0.05), Spec(0.32, 0.1), Spec(0.6, 0.2)]
    notes = """foundry_b: outside the dreadnought: a burning planet (lava cracks, smoke) in red-black space, the
    ship's far superstructure, its hull with turrets, vents and antennas, the near hull edge with spikes and a
    gun barrel."""
    return layers, specs, notes


def gloam_block(L, rng, cx, top, w, lad, glow):
    """A floating Gloam fortress: a flat deck carrying a tower and spires, under it an inverted stepped pyramid
    ending in a spike with a glowing tip. Lit from the left; window bands glow along the steps.
    lad: [dark, mid, lit, rim]; glow: colours for the window bands (last = the tip)."""
    lad = np.asarray(lad, np.uint8)
    dr = Draw(L.w)
    dr.rect(cx - w / 2, top, cx + w / 2, top + 6)
    steps = int(rng.integers(3, 6))
    y = top + 6
    hw = w / 2
    sh = max(4, w * rng.uniform(0.07, 0.11))
    bands = []
    for k in range(steps):
        hw2 = hw * rng.uniform(0.62, 0.8)
        dr.poly([(cx - hw, y), (cx + hw, y), (cx + hw2, y + sh), (cx - hw2, y + sh)])
        bands.append((y + sh * 0.5, hw * 0.85))
        y += sh
        hw = hw2
    tip = y + w * rng.uniform(0.3, 0.5)
    dr.poly([(cx - hw, y), (cx + hw, y), (cx, tip)])
    tw = w * rng.uniform(0.18, 0.28)
    th = w * rng.uniform(0.25, 0.45)
    tx = cx + rng.uniform(-0.2, 0.2) * w
    dr.rect(tx - tw / 2, top - th, tx + tw / 2, top)
    dr.poly([(tx - tw / 4, top - th), (tx, top - th - w * 0.35), (tx + tw / 4, top - th)])
    for sx in (cx - w * 0.38, cx + w * 0.34):
        dr.poly([(sx - 2, top), (sx, top - w * rng.uniform(0.15, 0.3)), (sx + 2, top)])
    m = dr.mask()
    split = wdx(L.X, cx - w * 0.08, L.w) < 0
    L.put(m & split, lad[2])
    L.put(m & ~split, lad[0])
    flat = m & ~shift(m, 0, -1)
    L.put(flat, lad[3])
    L.put(edge(m, -1, 0) & ~flat, lad[1])
    for by, bw in bands:
        b = m & (np.abs(L.Y - by) < 0.6) & (np.abs(wdx(L.X, cx, L.w)) < bw) &             ((L.X.astype(np.int32) // 2) % 3 != 0)
        L.put(b, glow[0], keep=True, glow=True)
    win = m & (np.abs(wdx(L.X, tx, L.w)) < tw / 2 - 2) & (L.Y > top - th + 3) & (L.Y < top - 2) &         ((L.Y.astype(np.int32) % 4) == 0) & ((L.X.astype(np.int32) % 3) != 0)
    L.put(win, glow[min(1, len(glow) - 1)], keep=True, glow=True)
    light(L, cx, tip + 1, glow[-1], size=2 if w > 80 else 1)
    return m


# ---------------------------------------------------------------------------------------------------- citadel_a

def citadel_a(seed):
    """The Gloam's core: a void sky, a black eclipse sun ringed with magenta, floating angular structures."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280

    # layer 0: the void and the black sun with its corona and rays
    L0 = Layer(W0)
    vbands(L0, "outline", [(120, "purple0"), (260, "violet0"), (330, "purple1")], dpx=9,
           wobble=(Noise(W0, 5, rng, 3)(L0.X, L0.Y * 0.4) - 0.5) * 30)
    stars(L0, rng, 120, y1=380, glints=1, tints=("magenta", "violet"), dim="violet", bright_frac=0.05)
    sx, sy, sr = 480, 150, 52
    dx = wdx(L0.X, sx, W0)
    d = np.sqrt(dx * dx + (L0.Y - sy) ** 2)
    ang = np.arctan2(L0.Y - sy, dx)
    ray = np.zeros(L0.a.shape, np.float32)
    for k in range(24):
        a = rng.uniform(-np.pi, np.pi)
        ln = rng.uniform(40, 170)
        wd = rng.uniform(0.012, 0.035)
        da = np.abs((ang - a + np.pi) % (2 * np.pi) - np.pi)
        ray = np.maximum(ray, np.clip(1 - da / wd, 0, 1) * np.clip(1 - (d - sr) / ln, 0, 1))
    cor = np.clip(1 - (d - sr) / 46, 0, 1) ** 1.6 + ray * 0.8
    out = d > sr
    levels(L0, np.where(out, cor, 0), ["purple1", "magenta2", "magenta3", "magenta4", "rose5"],
           [0.12, 0.28, 0.46, 0.66, 0.86], dpx=0.04, glow_from=2)
    L0.put(d <= sr, "outline", keep=True)
    L0.put((d > sr) & (d <= sr + 1.3), "rose6", keep=True, glow=True)
    L0.put((d <= sr) & (d > sr - 1.2) & (L0.Y < sy - sr * 0.3), "purple1", keep=True)
    # a faint ring around the sun
    ring = np.abs(np.sqrt((dx / 2.6) ** 2 + ((L0.Y - sy) * 1.0) ** 2) - 64) < 0.7
    L0.put(ring & (d > sr + 2) & ((L0.Y.astype(np.int32) + L0.X.astype(np.int32)) % 2 == 0), "magenta2", keep=True)

    # layer 1: far floating Gloam fortresses, small and fogged, with a few shards
    L1 = Layer(W)
    far = ladder("violet0 violet1 purple1 purple2")
    for x, y, w in ((90, 150, 70), (330, 250, 54), (560, 110, 46), (800, 220, 80), (1060, 140, 60), (1200, 290, 40)):
        gloam_block(L1, rng, x, y, w, far, ["magenta2", "purple3"])
    for i in range(10):
        x = i * W / 10 + rng.uniform(-30, 30)
        h = rng.uniform(16, 40)
        shard(L1, x, rng.uniform(90, 330), h * 0.3, h, ladder("violet0 violet1 purple1"), "purple2",
              tilt=rng.uniform(-0.3, 0.3), kind=0)

    # layer 2: closer fortresses with glowing window bands
    L2 = Layer(W)
    mid = ladder("outline violet0 violet1 purple2")
    for x, y, w in ((180, 210, 130), (620, 120, 110), (1000, 250, 150)):
        gloam_block(L2, rng, x, y, w, mid, ["magenta4", "magenta5", "rose6"])
    for x, y, h in ((420, 300, 50), (820, 90, 36), (1200, 160, 44)):
        shard(L2, x, y, h * 0.35, h, ladder("outline violet1 purple2"), "magenta3", tilt=rng.uniform(-0.4, 0.4))

    # layer 3: near dark shards drifting, magenta rims
    L3 = Layer(W)
    for x, y, w, h, kind, tilt in ((300, 300, 70, 120, 0, 0.3), (820, 110, 36, 90, 0, -0.4),
                                   (1080, 330, 110, 60, 2, -0.12)):
        shard(L3, x, y, w, h, ladder("outline outline violet0"), "magenta3", tilt=tilt, kind=kind)

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.03, 0.02), Spec(0.14, 0.05), Spec(0.32, 0.1), Spec(0.6, 0.2)]
    notes = """citadel_a: the Gloam's core: a void sky with a black eclipse sun ringed with a magenta corona and rays,
    floating Gloam fortresses (inverted stepped pyramids with towers and glowing window bands) in two depths,
    drifting shards, near dark shards."""
    return layers, specs, notes


# ---------------------------------------------------------------------------------------------------- citadel_b

def bus(L, rng, mask, x0, y0, n, length, cols, spacing=3, pads=True, direction=1):
    """A bundle of n parallel circuit traces running sideways from (x0, y0), jogging diagonally now and then,
    ending in pads. Only drawn inside mask. cols: one colour per trace (cycled)."""
    pts = [(x0, y0)]
    x, y = x0, y0
    run = 0
    while run < length:
        seg = int(rng.integers(10, 40))
        for _ in range(seg):
            x += direction
            pts.append((x, y))
        run += seg
        if rng.random() < 0.6 and run < length:
            dy = int(rng.choice([-1, 1]))
            for _ in range(int(rng.integers(3, 10))):
                x += direction
                y += dy
                pts.append((x, y))
    out = np.zeros(L.a.shape, bool)
    for k in range(n):
        m = np.zeros(L.a.shape, bool)
        for px, py in pts:
            yy = py + k * spacing
            if 0 <= yy < L.h:
                m[yy, px % L.w] = True
        m &= mask
        c = cols[k % len(cols)]
        L.put(m, c, keep=True, glow=True)
        out |= m
        if pads:
            for px, py in (pts[0], pts[-1]):
                pm = np.zeros(L.a.shape, bool)
                yy = py + k * spacing
                if 1 <= yy < L.h - 1:
                    pm[yy - 1:yy + 1, [(px - 1) % L.w, px % L.w]] = True
                L.put(pm & mask, c, keep=True, glow=True)
    return out


def citadel_b(seed):
    """Neon circuit canyons in black-violet: a canyon in perspective towards a glow, stepped monolith walls
    covered in bundles of glowing traces, near pillars with neon strips."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280
    xs = np.arange(W, dtype=np.float32)

    def stepped(w, rng, base, amp, step, cells):
        """A stepped skyline: flat runs of random length at levels quantized to step px, following a noise."""
        n = Noise(w, cells, rng, 3)(np.arange(w, dtype=np.float32), np.zeros(w, np.float32) + 3)
        top = np.zeros(w, np.float32)
        x = 0
        while x < w:
            ln = int(rng.integers(30, 90))
            ln = w - x if w - x < 110 else ln
            lvl = np.floor((n[min(w - 1, x + ln // 2)] * amp + rng.uniform(-step, step)) / step) * step
            top[x:x + ln] = base - lvl
            x += ln
        return top

    def walls(L, top, lad, rim, side_rim):
        m = L.Y >= top[None, :]
        L.put(m, lad[1])
        L.put(m & ((L.Y - top[None, :]) > 60), lad[0])
        L.put(m & (np.abs(L.Y - top[None, :] - 60) < 4) & ((L.X.astype(np.int32) + L.Y.astype(np.int32)) % 2 == 0),
              lad[0])
        L.put(edge(m, 0, -1), rim)
        L.put(edge(m, -1, 0) & ~edge(m, 0, -1), side_rim)
        L.put(shift(edge(m, 0, -1), 0, -1) & m & ~edge(m, 0, -1), lad[2])
        return m

    # layer 0: the canyon in perspective, its walls falling towards a glow at the vanishing point
    L0 = Layer(W0)
    vx, vy = 480, 238
    vbands(L0, "outline", [(150, "violet0"), (215, "purple1")], dpx=8)
    gl = np.sqrt((wdx(L0.X, vx, W0) / 4.0) ** 2 + ((L0.Y - vy) * 1.6) ** 2)
    levels(L0, -gl, ["magenta2", "magenta3", "rose4", "rose6"], [-70, -42, -22, -9], dpx=4, glow_from=2)
    dx = wdx(L0.X, vx, W0)
    wall_top = vy - 4 - 190 * (np.abs(dx) / 480) ** 0.9
    wm = (L0.Y >= wall_top) & (L0.Y < vy + 2 + (np.abs(dx) / 480) * 30)
    floor = L0.Y >= vy
    L0.put(floor, "outline")
    near = np.abs(dx) / 480
    bands_at(L0, -near, "violet0", [(-0.62, "violet1"), (-0.3, "purple1"), (-0.12, "purple2")], dpx=0.02,
             mask=wm)
    L0.put(edge(wm, 0, -1), "magenta2")
    # neon lines converging on the vanishing point: on the walls and on the canyon floor
    ang = np.degrees(np.arctan2(L0.Y - vy, dx))
    for a in np.linspace(-170, -10, 22):
        rayw = np.abs(((ang - a + 180) % 360) - 180) < 0.35 * (1 + 30 / (np.abs(dx) + 30))
        on = rayw & wm & ~edge(wm, 0, -1)
        if rng.random() < 0.75:
            L0.put(on, "cyan3" if a < -90 else "magenta3", keep=True, glow=True)
    for a in np.linspace(12, 168, 15):
        rayf = np.abs(((ang - a + 180) % 360) - 180) < 0.3 * (1 + 30 / (np.abs(dx) + 30))
        L0.put(rayf & floor & ~wm, "violet2", keep=True)
    for k in range(1, 9):
        yy = vy + 2 + 1.6 ** k
        if yy < 400:
            L0.put(floor & ~wm & (np.abs(L0.Y - yy) < 0.5), "violet1", keep=True)

    # layer 1: far monolith walls with trace bundles
    L1 = Layer(W)
    top1 = stepped(W, rng, 370, 220, 20, 5)
    m1 = walls(L1, top1, ladder("violet0 violet1 purple1"), col("purple2"), col("violet1"))
    inner1 = m1 & ~grow(edge(m1, 0, -1) | edge(m1, -1, 0) | edge(m1, 1, 0), 3)
    for _ in range(26):
        x = int(rng.integers(0, W))
        y = int(top1[x] + rng.integers(8, 90))
        bus(L1, rng, inner1, x, y, int(rng.integers(2, 5)), int(rng.integers(40, 160)),
            [col("cyan2"), col("cyan3")] if rng.random() < 0.5 else [col("magenta2"), col("magenta3")],
            direction=int(rng.choice([-1, 1])))

    # layer 2: closer walls, bigger bundles and light panels
    L2 = Layer(W)
    top2 = stepped(W, rng, 400, 210, 28, 3)
    top2 = np.where(np.abs(wdx(xs, 640, W)) < 200, np.maximum(top2, 372), top2)
    m2 = walls(L2, top2, ladder("outline violet0 violet1"), col("magenta3"), col("purple2"))
    inner2 = m2 & ~grow(edge(m2, 0, -1) | edge(m2, -1, 0) | edge(m2, 1, 0), 4)
    for _ in range(16):
        x = int(rng.integers(0, W))
        y = int(top2[x] + rng.integers(10, 80))
        bus(L2, rng, inner2, x, y, int(rng.integers(3, 6)), int(rng.integers(60, 220)),
            [col("cyan4"), col("cyan3")] if rng.random() < 0.5 else [col("magenta4"), col("magenta3")],
            spacing=4, direction=int(rng.choice([-1, 1])))
    for k in range(10):
        x = int(rng.integers(0, W))
        y = int(top2[x] + rng.integers(14, 70))
        pm = (np.abs(wdx(L2.X, x, W)) < 7) & (np.abs(L2.Y - y) < 2) & inner2
        L2.put(pm, "cyan5" if k % 2 else "magenta5", keep=True, glow=True)

    # layer 3: near dark pillars with neon strips
    L3 = Layer(W)
    dr = Draw(W)
    for x, w, top in ((150, 40, 120), (190, 18, 60), (760, 50, 170), (1150, 30, 90)):
        dr.rect(x - w / 2, top, x + w / 2, 400)
        dr.rect(x - w / 2 - 6, top, x + w / 2 + 6, top + 6)
    m3 = dr.mask()
    L3.put(m3, "outline")
    L3.put(edge(m3, -1, 0) | edge(m3, 0, -1), "violet1")
    for x, w, top in ((150, 40, 120), (760, 50, 170), (1150, 30, 90)):
        acc = (np.abs(wdx(L3.X, x, W)) < 0.6) & (L3.Y > top + 14) & (L3.Y < 390) & \
              ((L3.Y.astype(np.int32) // 10) % 3 != 0)
        L3.put(acc, "magenta4" if x != 760 else "cyan4", keep=True, glow=True)
        light(L3, x - w / 2 - 6, top - 1, "magenta5")
        light(L3, x + w / 2 + 6, top - 1, "magenta5")

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.04, 0.02), Spec(0.17, 0.05), Spec(0.35, 0.1), Spec(0.64, 0.2)]
    notes = """citadel_b: neon circuit canyons: a canyon in perspective with neon lines converging on a magenta glow,
    stepped monolith walls in two depths covered with bundles of glowing cyan and magenta traces, near dark
    pillars with neon strips (they run off the top of layer 3 and repeat upwards)."""
    return layers, specs, notes


SCENES = {"foundry_a": foundry_a, "foundry_b": foundry_b, "citadel_a": citadel_a, "citadel_b": citadel_b}
