"""Backgrounds of episode 3, the comet mines of Ysk: ice (the comet's surface and caves) and crystal (the caverns)."""
import numpy as np

from bgkit import (Draw, Layer, Noise, Spec, band, bands_at, col, dither_mask, edge, fogged, gas_field, grow, ladder,
                   levels, lift, mix, ramp_step, shift, shrink, stars, stretch, swoosh, truss, vbands, wdx)
from shapes import (_px, blob, cone, crystal, crystal_cluster, light, mirror, paint_peaks, peaks_profile, plate, rock,
                    window_strips)


# ------------------------------------------------------------------------------------------------------ helpers

def drill_rig(L, rng, x, base, h, lad, lights=True, flood=None):
    """A mining drill rig: a platform, a house with lit windows, a tapered lattice derrick with a crown block, a
    tank and a boom, beacon and flood lights. flood: an optional colour to light the ground (lifted) around it."""
    dr = Draw(L.w)
    dr.rect(x - h * 0.45, base - h * 0.08, x + h * 0.5, base + 6)
    dr.rect(x - h * 0.38, base - h * 0.24, x - h * 0.05, base - h * 0.08)
    dr.rect(x - h * 0.34, base - h * 0.3, x - h * 0.12, base - h * 0.24)
    tank = Draw(L.w).ellipse(x + h * 0.22, base - h * 0.2, x + h * 0.44, base - h * 0.06).mask()
    hw0, hw1 = h * 0.14, h * 0.035
    truss(dr, x + h * 0.08 - hw0, base - h * 0.08, x + h * 0.08 - hw1, base - h, 2, max(3, h * 0.07))
    truss(dr, x + h * 0.08 + hw0, base - h * 0.08, x + h * 0.08 + hw1, base - h, 2, max(3, h * 0.07))
    for k in range(1, 5):
        yy = base - h * 0.08 - (h * 0.92) * k / 5
        ww = hw0 + (hw1 - hw0) * k / 5
        dr.line([(x + h * 0.08 - ww, yy), (x + h * 0.08 + ww, yy)], 1)
    dr.rect(x + h * 0.08 - hw1 - 2, base - h - 4, x + h * 0.08 + hw1 + 2, base - h)
    dr.line([(x + h * 0.08, base - h * 0.75), (x - h * 0.4, base - h * 0.55)], 2)
    m = dr.mask() | tank
    plate(L, m, base - h, base, lad, bands=(0.05, 0.3))
    if lights:
        window_strips(L, m & (L.Y > base - h * 0.23) & (L.Y < base - h * 0.09) & (L.X < x),
                      [np.full(L.w, int(base - h * 0.2 + k * 4)) for k in range(int(h * 0.12 / 4) + 1)], rng,
                      cols=("yellow5", "orange4"), on=0.85, seg=(2, 6), gap=(1, 3))
        light(L, x + h * 0.08, base - h - 6, "red5", size=2 if h > 60 else 1)
        light(L, x - h * 0.4, base - h * 0.55 + 1, "red4")
        for k in range(3):
            light(L, x - h * 0.4 + k * h * 0.4, base - h * 0.08 - 2, "yellow6")
    if flood is not None:
        d = np.sqrt((wdx(L.X, x, L.w) / (h * 0.9)) ** 2 + ((L.Y - base) / (h * 0.35)) ** 2)
        lit = (np.clip(1 - d, 0, 1) * 1.4 > L.by) & L.a & ~m & ~L.keep
        lift(L, lit, 1)
    return m


def icicles(L, rng, specs, from_top=True):
    """Hanging (or standing) ice spikes [(x, length, width)]: returns (mask, u) with u = -1..1 across each spike."""
    m = np.zeros(L.a.shape, bool)
    u = np.zeros(L.a.shape, np.float32)
    n = Noise(256, 6, rng, 2)
    for x, ln, wd in specs:
        y = L.Y[:, 0] if from_top else (L.h - 1 - L.Y[:, 0])
        t = np.clip(y / ln, 0, 1)
        hw = wd / 2 * (1 - t) ** 0.9 * (1 + 0.25 * (n(np.full_like(y, x), y) - 0.5))
        sway = (n(np.full_like(y, x + 99.0), y * 0.5) - 0.5) * wd * 0.3 * t
        uu = (wdx(L.X, x, L.w) - sway[:, None]) / np.maximum(0.5, hw[:, None])
        mm = (np.abs(uu) <= 1) & (y[:, None] < ln)
        u = np.where(mm & ~m, uu, u)
        m |= mm
    return m, u


def ice_shade(L, m, u, lad, streaks=True):
    """Translucent ice: lit left side, darker right, a bright left rim, faint inner streaks. lad: dark to light."""
    lad = np.asarray(lad, np.uint8)
    v = np.clip(0.55 - 0.45 * u, 0, 0.999)
    if streaks:
        st = (np.abs(((L.X + L.Y * 0.05) % 8) - 4) < 0.5) & (np.abs(u) < 0.7)
        v = np.where(st, np.minimum(0.999, v + 0.22), v)
    idx, dith = band(v, len(lad) - 1, 0.35, None, L.by)
    L.paint(m, idx, lad[:-1], dith)
    L.put(edge(m, -1, 0) | (edge(m, 0, -1) & (u < 0.3)), lad[-1])


# -------------------------------------------------------------------------------------------------------- ice_a

def ice_a(seed):
    """The comet's surface: an ice field under a black sky, the comet's tail streaming overhead, gas jets, drill
    rigs with their lights."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280

    # layer 0: black sky, stars, the tail, jets, far ice
    L0 = Layer(W0)
    vbands(L0, "slate0", [(230, "outline"), (300, "slate1")], dpx=8)
    stars(L0, rng, 300, y1=330, glints=4, tints=("ice", "cyan"))
    env = swoosh(L0, rng, 128, 56, 62, wvar=0.5)
    tail = stretch(gas_field(L0, rng, cells=3, warp=150, streak=0.75, sy=3.2) ** 1.3 * env, 0, 99.8)
    levels(L0, tail, ["slate1", "ice1", "ice2", "ice3", "cyan4", "ice5"], [0.12, 0.22, 0.34, 0.5, 0.68, 0.84],
           dpx=0.035, glow_from=4)
    ion = swoosh(L0, rng, 78, 30, 14, wvar=0.3)
    ion_v = stretch(gas_field(L0, rng, cells=4, warp=60, streak=0.9, sy=5.0) * ion, 0, 99.8)
    levels(L0, ion_v, ["violet1", "blue2", "blue3"], [0.3, 0.55, 0.8], dpx=0.04, mask=tail < 0.22)
    for jx in (210, 610, 760):
        jet = np.clip(1 - np.abs(wdx(L0.X, jx, W0)) / np.maximum(1, 3 + (330 - L0.Y) * 0.12), 0, 1)
        jet *= np.clip((330 - L0.Y) / 30, 0, 1) * np.clip(1 - (330 - L0.Y) / 220, 0, 1)
        L0.put((jet * 0.9 > L0.by) & (L0.Y < 330), "ice3", keep=True)
        L0.put((jet * 0.5 > L0.by + 0.25) & (L0.Y < 330), "ice5", keep=True, glow=True)
    top0, rel0, hw0 = peaks_profile(W0, rng, 336, [(x, rng.uniform(10, 34), rng.uniform(30, 70))
                                                   for x in np.linspace(0, W0, 16, endpoint=False)])
    paint_peaks(L0, top0, rel0, hw0, ladder("slate1 slate2 ice2 ice3"), rng=rng)

    # layer 1: ice ridges, far drill rigs
    L1 = Layer(W)
    pk = [(x + rng.uniform(-30, 30), rng.uniform(30, 90), rng.uniform(40, 90)) for x in np.linspace(0, W, 12,
                                                                                                    endpoint=False)]
    top1, rel1, hw1 = peaks_profile(W, rng, 372, pk, rough=2.5)
    paint_peaks(L1, top1, rel1, hw1, ladder("ice1 slate2 ice2 ice4"), rng=rng)
    for x in (300, 820, 1130):
        drill_rig(L1, rng, x, int(top1[x - 20:x + 20].max()) + 2, 60, ladder("outline slate1 slate2 steel2"))

    # layer 2: ice blocks and a big rig with work lights
    L2 = Layer(W)
    pk2 = [(80, 120, 60), (230, 60, 50), (520, 90, 70), (690, 150, 50), (980, 80, 90), (1200, 110, 55)]
    top2, rel2, hw2 = peaks_profile(W, rng, 400, pk2, rough=3)
    paint_peaks(L2, top2, rel2, hw2, ladder("ice0 ice1 ice2 ice3"), rng=rng)
    drill_rig(L2, rng, 400, 380, 160, ladder("outline slate1 slate2 steel2 steel3"), flood=True)

    # layer 3: near dark ice shards
    L3 = Layer(W)
    pk3 = [(160, 120, 30), (210, 60, 26), (880, 150, 34), (940, 80, 30), (620, 40, 40)]
    top3, rel3, hw3 = peaks_profile(W, rng, 410, pk3, rough=2)
    paint_peaks(L3, top3, rel3, hw3, ladder("outline ice0 ice1 ice2"), cracks=False)

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.04, 0.02), Spec(0.14, 0.05), Spec(0.32, 0.1), Spec(0.6, 0.2)]
    notes = """ice_a: the comet's surface under a black sky: the comet's tail streaming overhead with a thin ion tail,
    gas jets rising from the far ice, ice ridges with distant drill rigs, a big rig with work lights, near shards."""
    return layers, specs, notes


# -------------------------------------------------------------------------------------------------------- ice_b

def ice_b(seed):
    """An ice cave: blue light falling in shafts through openings in the roof, icicles, frozen pillars."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280
    ang = 18.0

    # layer 0: the cave's back wall with shafts of light and the openings they come from
    L0 = Layer(W0)
    # frozen cascades: a wall of vertical ice flows, lighter low down
    wall = Noise(W0, 12, rng, 4, 0.5)(L0.X, L0.Y * 0.18)
    v = np.clip(0.12 + (L0.Y - 40) / 560 + (wall - 0.5) * 0.5, 0, 0.999)
    bands_at(L0, v, "ice0", [(0.24, "blue1"), (0.4, "ice1"), (0.6, "ice2")], dpx=0.03)
    flow = (np.abs(((L0.X + 7 * np.sin(L0.Y / 23)) % 24) - 12) < 0.6) & (v > 0.3) & (L0.Y > 30)
    L0.put(flow, "ice1")
    sh = np.zeros(L0.a.shape, np.float32)
    t = np.tan(np.radians(ang))
    for cx, wd in ((180, 34), (520, 52), (760, 26)):
        d = np.abs(wdx(L0.X - L0.Y * t, cx, W0))
        sh = np.maximum(sh, np.clip(1 - d / wd, 0, 1) ** 0.7)
        hole = blob(L0, cx, 4, wd * 0.8, 10)
        L0.put(hole, "ice6", keep=True, glow=True)
        L0.put(blob(L0, cx, 2, wd * 0.5, 6), "white", keep=True, glow=True)
    lift(L0, (sh * 0.8 > L0.by) & ~L0.keep, 1)
    ic, iu = icicles(L0, rng, [(x + rng.uniform(-20, 20), rng.uniform(24, 80), rng.uniform(10, 24))
                               for x in range(20, W0, 74)])
    ice_shade(L0, ic & (L0.Y > 6), iu, ladder("ice0 blue1 ice1 ice2"), streaks=False)
    sm, su = icicles(L0, rng, [(x, rng.uniform(20, 60), rng.uniform(16, 36)) for x in range(10, W0, 96)],
                     from_top=False)
    ice_shade(L0, sm, su, ladder("ice0 blue1 ice1 ice2"), streaks=False)
    L0.put(L0.Y > 384, "ice0")
    L0.put((L0.Y < 8) & ~L0.glow, "ice0")

    # layer 1: big stalactites and stalagmites, translucent
    L1 = Layer(W)
    lad1 = ladder("ice1 ice2 ice3 ice4")
    L1.put(L1.Y < 6 + 4 * Noise(W, 20, rng, 2)(L1.X, np.zeros_like(L1.X)), "ice1")
    st, su = icicles(L1, rng, [(x + rng.uniform(-30, 30), rng.uniform(70, 170), rng.uniform(26, 56))
                               for x in range(60, W, 210)])
    ice_shade(L1, st, su, lad1)
    gm, gu = icicles(L1, rng, [(x + rng.uniform(-30, 30), rng.uniform(50, 130), rng.uniform(30, 64))
                               for x in range(120, W, 210)], from_top=False)
    ice_shade(L1, gm, gu, lad1)
    # a frozen pillar where a stalactite meets a stalagmite
    pil = (np.abs(wdx(L1.X, 900 + 10 * np.sin(L1.Y / 30), W)) < 14 + 8 * np.abs(np.sin(L1.Y / 47)))
    ice_shade(L1, pil, wdx(L1.X, 900 + 10 * np.sin(L1.Y / 30), W) / 22, lad1)
    L1.put(L1.Y > 388, "ice1")

    # layer 2: haze in the shafts, closer icicle clusters
    L2 = Layer(W)
    t = np.tan(np.radians(ang))
    hz = np.zeros(L2.a.shape, np.float32)
    for cx, wd in ((240, 40), (700, 60), (1010, 30)):
        d = np.abs(wdx(L2.X - L2.Y * t, cx, W))
        hz = np.maximum(hz, np.clip(1 - d / wd, 0, 1) * np.clip(L2.Y / 120, 0, 1) * np.clip((400 - L2.Y) / 200, 0, 1))
    L2.put(hz * 0.32 > L2.by, "ice4", keep=True)
    L2.put(hz * 0.18 > L2.by + 0.05, "ice6", keep=True, glow=True)
    lad2 = ladder("ice0 ice1 ice2 ice3 ice4")
    st2, su2 = icicles(L2, rng, [(x + rng.uniform(-20, 20), rng.uniform(40, 110), rng.uniform(12, 30))
                                 for x in range(30, W, 150)])
    ice_shade(L2, st2, su2, lad2)
    g2, gu2 = icicles(L2, rng, [(x, rng.uniform(40, 90), rng.uniform(30, 50)) for x in (180, 560, 1100)],
                      from_top=False)
    ice_shade(L2, g2, gu2, lad2)

    # layer 3: near dark icicles from the roof and shards on the floor
    L3 = Layer(W)
    L3.put(L3.Y < 4, "ice0")
    st3, su3 = icicles(L3, rng, [(x, rng.uniform(60, 140), rng.uniform(20, 40)) for x in (120, 170, 640, 1000, 1030)])
    L3.put(st3, "ice0")
    L3.put(edge(st3, -1, 0), "ice2")
    g3, gu3 = icicles(L3, rng, [(x, rng.uniform(40, 100), rng.uniform(30, 60)) for x in (330, 820, 1220)],
                      from_top=False)
    L3.put(g3, "ice0")
    L3.put(edge(g3, -1, 0) | edge(g3, 0, -1), "ice2")

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.06, 0.03), Spec(0.18, 0.06), Spec(0.36, 0.1), Spec(0.66, 0.2)]
    notes = """ice_b: an ice cave: shafts of blue light through openings in the roof brighten the back wall, icicles
    and stalagmites in three depths, haze in the shafts (layer 2, sparse dithered pixels), near dark icicles.
    The icicles of layers 1-3 hang from the first row and repeat upwards as ice."""
    return layers, specs, notes


# ---------------------------------------------------------------------------------------------------- crystal_a

def rock_band(L, rng, top, lad, rim=None):
    """Solid rock below a per-column top line, shaded by depth, with a rim on its upper edge."""
    m = L.Y >= top[None, :]
    lad = np.asarray(lad, np.uint8)
    depth = L.Y - top[None, :]
    tex = Noise(L.w, L.w // 24, rng, 3)(L.X, L.Y)
    v = np.clip(0.75 - depth / 80 + (tex - 0.5) * 0.4, 0, 0.999)
    idx, dith = band(v, len(lad), 0.35, None, L.by)
    L.paint(m, idx, lad, dith)
    if rim is not None:
        L.put(edge(m, 0, -1), rim)
    return m


def crystal_a(seed):
    """A vast crystal cavern: giant glowing spires far away, clusters on outcrops, near dark rock."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280
    xs0 = np.arange(W0, dtype=np.float32)
    xs = np.arange(W, dtype=np.float32)

    # layer 0: the dark cavern, a cold glow behind giant spires
    L0 = Layer(W0)
    vbands(L0, "outline", [(70, "violet0"), (160, "violet1")], dpx=8,
           wobble=(Noise(W0, 6, rng, 3)(L0.X, L0.Y) - 0.5) * 30)
    gl = np.sqrt((wdx(L0.X, 480, W0) / 2.4) ** 2 + ((L0.Y - 250) * 1.0) ** 2)
    gl += (Noise(W0, 5, rng, 3)(L0.X, L0.Y) - 0.5) * 50
    levels(L0, -gl, ["slate1", "teal1", "cyan1", "teal2"], [-220, -160, -110, -60], dpx=6)
    for x, h, w, ang in ((230, 150, 20, 6), (420, 120, 16, -8), (660, 140, 18, 4), (780, 100, 14, -5)):
        crystal(L0, x, 380, h, w, ang, ladder("violet1 slate2 slate2 teal2"))
    for x, h, w, ang in ((300, 300, 46, -4), (360, 200, 30, 8), (520, 340, 56, 3), (600, 230, 34, -10),
                         (700, 180, 26, 12), (140, 160, 24, -6), (840, 210, 32, 5)):
        crystal(L0, x, 390, h, w, ang, ladder("teal0 teal1 teal2 cyan3"), glow_core="cyan4")
    top0 = 360 + 16 * Noise(W0, 8, rng, 3)(xs0, np.zeros_like(xs0))
    rock_band(L0, rng, top0, ladder("outline violet0 violet1"), rim="slate2")
    ceil = L0.Y < 30 + 26 * Noise(W0, 9, rng, 3)(L0.X, np.zeros_like(L0.X))
    L0.put(ceil, "outline")

    # layer 1: crystal clusters on outcrops, violet and cyan
    L1 = Layer(W)
    top1 = 330 + 40 * Noise(W, 5, rng, 4)(xs, np.zeros_like(xs) + 3)
    vio = ladder("violet1 violet2 purple3 magenta4")
    cya = ladder("blue1 blue2 cyan3 cyan5")
    for x, s, lad, core in ((120, 120, vio, "magenta5"), (420, 90, cya, "cyan6"), (640, 150, vio, "magenta5"),
                            (930, 110, cya, "cyan6"), (1150, 80, vio, "magenta5")):
        crystal_cluster(L1, rng, x, int(top1[x]) + 8, s, lad, n=int(rng.integers(4, 7)), glow_core=core)
    rock_band(L1, rng, top1, ladder("outline violet0 violet1 slate2"), rim="violet2")

    # layer 2: rock ledges with clusters
    L2 = Layer(W)
    top2 = 350 + 40 * Noise(W, 4, rng, 4)(xs, np.zeros_like(xs) + 9)
    for x, s, lad, core in ((260, 70, cya, "cyan6"), (760, 90, vio, "magenta5"), (1060, 60, cya, "cyan6")):
        crystal_cluster(L2, rng, x, int(top2[x]) + 6, s, lad, n=5, glow_core=core)
    rock_band(L2, rng, top2, ladder("outline outline violet0 violet1"), rim="violet2")
    # a hanging rock with crystals growing down
    hang = blob(L2, 520, 0, 90, 46) | blob(L2, 600, 10, 50, 30)
    L2.put(hang, "violet0")
    L2.put(edge(hang, 0, 1), "violet1")
    for k in range(5):
        crystal(L2, 470 + k * 26, 40 + rng.uniform(-6, 6), rng.uniform(26, 50), rng.uniform(8, 12),
                180 + rng.uniform(-20, 20), cya, glow_core="cyan6")

    # layer 3: near dark rock with a few small glowing crystals
    L3 = Layer(W)
    top3 = 380 + 30 * Noise(W, 3, rng, 4)(xs, np.zeros_like(xs) + 21) - 60 * np.clip(
        1 - np.abs(wdx(xs, 200, W)) / 120, 0, 1) - 40 * np.clip(1 - np.abs(wdx(xs, 900, W)) / 90, 0, 1)
    m3 = L3.Y >= top3[None, :]
    L3.put(m3, "outline")
    L3.put(edge(m3, 0, -1), "violet1")
    for x in (180, 220, 880, 915):
        crystal(L3, x, int(top3[x]) + 6, rng.uniform(20, 40), rng.uniform(7, 11), rng.uniform(-25, 25),
                ladder("violet0 violet1 violet2 purple4"), glow_core="magenta5")

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.05, 0.02), Spec(0.17, 0.05), Spec(0.35, 0.1), Spec(0.64, 0.2)]
    notes = """crystal_a: a vast crystal cavern: giant teal spires glowing far away in a cold haze, violet and cyan
    clusters on outcrops, a hanging rock with crystals growing down, near dark rock."""
    return layers, specs, notes


# ---------------------------------------------------------------------------------------------------- crystal_b

def crystal_b(seed):
    """An underground lake of light: glowing crystals along the far shore and on islands, all mirrored in the
    still water. All layers share one vertical parallax, so the waterline stays aligned."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280
    wl = 236
    xs0 = np.arange(W0, dtype=np.float32)
    xs = np.arange(W, dtype=np.float32)

    def ripple(k):
        return 2 * np.sin(k * 0.9) if k % 5 < 3 else -1

    def dim(c):
        return ramp_step(c, -1)

    # layer 0: the far wall, its crystals and the glowing water
    L0 = Layer(W0)
    vbands(L0, "outline", [(80, "violet0"), (170, "violet1")], dpx=8,
           wobble=(Noise(W0, 6, rng, 3)(L0.X, L0.Y) - 0.5) * 24)
    gl = np.abs(L0.Y - (wl - 30)) + (Noise(W0, 6, rng, 3)(L0.X, L0.Y) - 0.5) * 30
    levels(L0, -gl, ["purple1", "purple2"], [-60, -26], dpx=5, mask=L0.Y < wl)
    shore = wl - 4 - 16 * Noise(W0, 7, rng, 3)(xs0, np.zeros_like(xs0))
    cr = np.zeros(L0.a.shape, bool)
    for x in range(30, W0, 48):
        m = crystal(L0, x + rng.uniform(-16, 16), int(shore[x % W0]) + 8, rng.uniform(30, 110),
                    rng.uniform(8, 20), rng.uniform(-15, 15),
                    ladder("violet1 purple2 magenta3 rose5") if (x // 48) % 2 else ladder("blue1 blue2 cyan3 cyan5"),
                    glow_core="white")
        if m is not None:
            cr |= m
    m = L0.Y >= shore[None, :]
    L0.put(m & (L0.Y < wl), "violet0")
    L0.put(edge(m, 0, -1) & (L0.Y < wl), "purple2")
    # the water: luminous near the far shore, darker towards us
    bands_at(L0, L0.Y, "purple2", [(wl + 10, "violet1"), (wl + 40, "violet0"), (wl + 100, "outline")], dpx=5,
             mask=L0.Y >= wl)
    mirror(L0, wl, ripple, dim, src=cr)
    wv = (L0.Y >= wl) & ((L0.Y - wl) % 6 == 0)
    sheen = wv & (Noise(W0, 24, rng, 2)(L0.X, L0.Y * 3) > 0.58)
    L0.put(sheen & (L0.Y < wl + 50), "cyan3", keep=True, glow=True)
    L0.put(sheen & (L0.Y >= wl + 50), "violet2", keep=True)
    L0.put((L0.Y == wl), "magenta3", keep=True)

    # layer 1: crystal islands and their reflections
    L1 = Layer(W)
    for x, w_, s, lad, core in ((180, 60, 110, ladder("blue1 blue2 cyan3 cyan6"), "white"),
                                (650, 90, 150, ladder("violet1 violet2 magenta3 rose6"), "white"),
                                (1040, 50, 90, ladder("blue1 blue2 cyan3 cyan6"), "white")):
        isl = (blob(L1, x, wl + 2, w_, 9) | blob(L1, x - w_ * 0.3, wl + 2, w_ * 0.4, 14)) & (L1.Y < wl)
        L1.put(isl, "violet0")
        L1.put(edge(isl, 0, -1), "purple2")
        crystal_cluster(L1, rng, x, wl - 6, s, lad, n=6, glow_core=core)
    mirror(L1, wl, ripple, dim)
    L1.put((L1.Y == wl) & L1.a, "magenta3")

    # layer 2: shore rocks with crystals, mirrored
    L2 = Layer(W)
    wl2 = 300
    for x, w_, h_ in ((60, 70, 30), (480, 44, 20), (900, 80, 36)):
        rk = (blob(L2, x, wl2 + 4, w_, h_) | blob(L2, x + w_ * 0.4, wl2 + 4, w_ * 0.5, h_ * 0.6)) & (L2.Y < wl2)
        v = np.clip(0.75 - (L2.Y - (wl2 - h_)) / h_ * 0.6 - wdx(L2.X, x, W) / w_ * 0.4, 0, 0.999)
        idx, dith = band(v, 3, 0.3, None, L2.by)
        L2.paint(rk, idx, ladder("violet0 violet1 purple2"), dith)
        L2.put(edge(rk, 0, -1) | edge(rk, -1, 0), "magenta3")
        crystal_cluster(L2, rng, x + w_ * 0.2, int(wl2 - h_ * 0.6), 70, ladder("violet0 violet1 purple3 magenta5"),
                        n=4, glow_core="magenta6")
    mirror(L2, wl2, ripple, dim)
    L2.put((L2.Y == wl2) & L2.a, "magenta3")

    # layer 3: near stalactites with crystal tips, dark foreground rocks
    L3 = Layer(W)
    for x, ln, wd in ((140, 120, 56), (190, 70, 30), (760, 150, 64), (1100, 90, 44)):
        t = np.clip(L3.Y / ln, 0, 1)
        dxw = wdx(L3.X, x, W)
        st = (np.abs(dxw) < wd / 2 * (1 - t) ** 0.8) & (L3.Y < ln)
        L3.put(st, "outline")
        L3.put(edge(st, -1, 0), "purple2")
        L3.put(edge(st, 1, 0) & ~edge(st, -1, 0), "violet1")
        crystal(L3, x, ln - 6, 26, 10, 180, ladder("violet0 violet1 purple3 magenta5"), glow_core="magenta6")
    fg = L3.Y > 372 + 16 * Noise(W, 5, rng, 3)(L3.X, np.zeros_like(L3.X))
    L3.put(fg, "outline")
    L3.put(edge(fg, 0, -1), "purple2")

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.05, 0.03), Spec(0.17, 0.03), Spec(0.35, 0.03), Spec(0.62, 0.03)]
    notes = """crystal_b: an underground lake of light: glowing crystals along the far shore and on islands, mirrored
    in the water (waterline at y 236 in every layer). All layers use the same vertical parallax so the
    reflections stay aligned with the waterline; keep it that way. Stalactites of layer 3 hang from its first
    row."""
    return layers, specs, notes


SCENES = {"ice_a": ice_a, "ice_b": ice_b, "crystal_a": crystal_a, "crystal_b": crystal_b}
