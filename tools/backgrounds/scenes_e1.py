"""Backgrounds of episode 1, the Academy Ring: station (views through the ring's windows) and hull (open space)."""
import numpy as np

from bgkit import (Draw, Layer, Noise, Spec, band, bands_at, col, dither_mask, edge, fogged, grow, ladder, mix,
                   lift, nebula, swoosh, planet, ramp_step, ridge, ring_outline, shift, stars, stretch, sun, truss, vbands, wdx)
from shapes import (_px, cone, draw_ship, hazard, lamp_row, light, local, plate, rock, ship, ship_shape, shade_body,
                    skyline, stamp, window_strips)


# ---------------------------------------------------------------------------------------------------- station_a

def station_a(seed):
    """Through the ring's windows: a blue ringed gas giant over the curve of the Academy ring, docked ships."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280

    # layer 0: deep space, stars, the gas giant and a moon
    L0 = Layer(W0)
    wob = (Noise(W0, 5, rng, 3)(L0.X, L0.Y * 0.3) - 0.5) * 36
    vbands(L0, "slate0", [(110, "outline"), (205, "slate1"), (290, "blue1")], dpx=9, wobble=wob)
    # faint cold wisps high up, so the open sky is not empty
    wisp = swoosh(L0, rng, 70, 40, 46)
    nebula(L0, rng, ["outline", "violet1", "blue1"], wisp * np.clip(1 - np.abs(wdx(L0.X, 600, W0)) / 600 + 0.35, 0, 1),
           [0.3, 0.48, 0.7], cells=3, warp=260)
    stars(L0, rng, 330, y1=330, glints=6)
    blue = ["outline", "slate1", "blue1", "blue2", "blue3", "ice4"]
    pale = ["outline", "slate1", "slate2", "ice2", "ice3", "ice4"]
    deep = ["outline", "slate0", "violet1", "slate2", "blue2", "blue3"]
    planet(L0, rng, 600, 150, 104, [ladder(blue), ladder(pale), ladder(deep), ladder(blue)],
           light=(-0.75, -0.5, 0.45), tilt=-0.22, flatten=0.24, band_freq=11, turb=0.3, rings=(1.32, 2.15),
           ring_lad=ladder("slate1 slate2 steel2 steel3 ice3"), rim=col("blue3"), night_rim=col("violet2"),
           levels=[0, 0.1, 0.27, 0.46, 0.68, 0.9, 1.0], dw=0.3)
    planet(L0, rng, 250, 92, 11, [ladder("outline slate1 steel2 steel3 steel4 steel5")], light=(-0.75, -0.5, 0.45),
           band_freq=3, turb=0.6, rim=None, levels=[0, 0.05, 0.2, 0.4, 0.6, 0.85, 1.0], dw=0.3)

    # layer 1: the curve of the Academy ring with its surface districts; a pylon hides the joint of the curve
    L1 = Layer(W)
    sky = col("blue1")
    xs = np.arange(W, dtype=np.float32)
    base = 300 + 34 * (wdx(xs, W / 2, W) / (W / 2)) ** 2
    hull = L1.Y >= base[None, :]
    d = L1.Y - base[None, :]
    hl = fogged("slate1 slate2 steel2 steel3 steel4", sky, 0.3)
    bands_at(L1, d, hl[4], [(1, hl[3]), (4, hl[2]), (14, hl[1]), (40, hl[0])], dpx=2, mask=hull)
    for k in range(6):
        dk = 7 * 1.55 ** k
        m = hull & (np.abs(d - dk) < 0.5)
        L1.put(m, ramp_step(tuple(hl[min(4, max(0, 2 - k // 2))]), -1))
    window_strips(L1, hull, [base + 9, base + 20, base + 33, base + 50, base + 74], rng, on=0.5, seg=(8, 40),
                  gap=(8, 60))
    near_pylon = lambda x: abs(wdx(x, 0, W)) < 46
    district = Noise(W, 3, rng, 2)
    skyline(L1, rng, base, fogged("slate1 slate2 steel2 steel3", sky, 0.42), hmin=4, hmax=34, wmin=8, wmax=26,
            gap=(0, 3), height=lambda x: 0.3 + 1.2 * district(x, 10.0), win_on=0.25, avoid=near_pylon,
            mast_light="red3")
    skyline(L1, rng, base + 2, fogged("slate1 slate2 steel2 steel3", sky, 0.22), hmin=3, hmax=20, wmin=6, wmax=30,
            gap=(4, 30), height=lambda x: 0.4 + district(x, 10.0), win_on=0.35, avoid=near_pylon)
    _pylon(L1, rng, 0, base, sky)

    # layer 2: docked ships on docking towers
    L2 = Layer(W)
    tl = ladder("outline slate0 slate1 slate2")
    plan = [(230, 214, 300, 50, 0, 1, "outline slate1 slate2 steel2 steel3", "brown3"),
            (690, 190, 200, 34, 2, -1, "outline slate1 slate2 slate3 ice3", "red2"),
            (1030, 232, 330, 56, 1, 1, "outline brown1 brown2 tan2 tan3", "orange2")]
    for cx, yc, ln, h, kind, fc, lad, acc in plan:
        _dock_tower(L2, rng, cx + int(rng.integers(-30, 30)), yc + h * 0.5 + (h * 0.3 if kind == 1 else 0), tl)
    for cx, yc, ln, h, kind, fc, lad, acc in plan:
        ship(L2, rng, cx, yc, ln, h, fc, fogged(lad, "slate1", 0.15), col(acc), kind=kind)

    # layer 3: dark near silhouettes, rim lit by the sun (left) and the planet (right): a crane and a dish mast
    L3 = Layer(W)
    dr = Draw(W)
    truss(dr, 420, 400, 420, 150, 26, 16, cw=4, bw=3)
    dr.rect(406, 138, 434, 154)
    truss(dr, 434, 146, 720, 146, 16, 16, cw=4, bw=2)
    truss(dr, 406, 146, 330, 146, 16, 16, cw=4, bw=2)
    dr.rect(296, 136, 332, 170)
    dr.line([(420, 138), (420, 104)], width=3)
    dr.line([(420, 106), (716, 140)], width=1)
    dr.line([(420, 106), (320, 136)], width=1)
    dr.rect(632, 154, 648, 160)
    dr.line([(640, 160), (640, 236)])
    dr.rect(622, 236, 658, 242)
    dr.poly([(626, 242), (654, 242), (648, 252), (632, 252)])
    # dish mast
    truss(dr, 1040, 400, 1040, 252, 18, 12, cw=3, bw=2)
    dr.rect(1028, 244, 1052, 254)
    m3 = dr.mask()
    dish = Draw(W).ellipse(1000, 190, 1080, 236).mask() & ~Draw(W).ellipse(1000, 182, 1080, 224).mask()
    dish |= Draw(W).line([(1040, 244), (1040, 212)], 3).mask() | Draw(W).line([(1040, 212), (1054, 180)]).mask()
    m3 |= dish
    L3.put(m3, "outline")
    L3.put(edge(m3, 0, -1) | edge(m3, -1, 0), "slate2")
    L3.put(edge(m3, 1, 0) & ~edge(m3, 0, -1), "blue1")
    light(L3, 419, 101, "red5", size=2)
    light(L3, 718, 144, "red4")
    light(L3, 639, 253, "yellow5", size=2)
    light(L3, 1054, 178, "red5", size=2)

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.04, 0.02), Spec(0.12, 0.05), Spec(0.3, 0.1), Spec(0.6, 0.2)]
    notes = """station_a: a blue ringed gas giant over the curve of the Academy ring, docked ships, a crane nearest."""
    return layers, specs, notes


def _pylon(L, rng, tx, base, sky):
    """A big communications pylon on the ring hull (it also hides the joint of the hull's curve)."""
    by = int(base[int(tx) % L.w])
    dr = Draw(L.w)
    dr.poly([(tx - 34, by + 6), (tx - 20, by - 60), (tx - 13, 120), (tx + 13, 120), (tx + 20, by - 60),
             (tx + 34, by + 6)])
    dr.rect(tx - 26, 132, tx + 26, 146)
    dr.poly([(tx - 30, 146), (tx + 30, 146), (tx + 22, 156), (tx - 22, 156)])
    dr.rect(tx - 40, by - 64, tx + 40, by - 56)
    dr.poly([(tx - 9, 120), (tx - 5, 76), (tx + 5, 76), (tx + 9, 120)])
    dr.rect(tx - 1, 40, tx, 76)
    dr.rect(tx - 12, 92, tx + 12, 94)
    m = dr.mask() & (L.Y < base[None, :] + 3)
    lad = fogged("slate1 slate2 steel2 steel3 steel4", sky, 0.28)
    v = np.clip(0.75 - 0.6 * (wdx(L.X, tx - 30, L.w) / 70), 0, 0.999)
    idx, dith = band(v, 4, 0.3, None, L.by)
    L.paint(m, idx, lad[:4], dith)
    L.put(edge(m, 0, -1) | edge(m, -1, 0), lad[4])
    window_strips(L, m & ~grow(edge(m, 1, 0) | edge(m, -1, 0), 2) & (L.Y > 160),
                  [np.full(L.w, y) for y in range(166, by - 64, 7)], rng, on=0.55, seg=(2, 9), gap=(2, 5))
    window_strips(L, m & (L.Y > 134) & (L.Y < 144), [np.full(L.w, 138), np.full(L.w, 141)], rng,
                  cols=("cyan5", "ice6"), on=1.0, seg=(30, 50), gap=(1, 2))
    light(L, tx - 1, 38, "red5", size=2)
    light(L, tx - 41, by - 65, "red4")
    light(L, tx + 40, by - 65, "red4")


def _dock_tower(L, rng, tx, ytop, lad):
    """A docking tower from the bottom of the layer up to a clamp under a ship."""
    dr = Draw(L.w)
    tw = int(rng.integers(18, 26))
    dr.poly([(tx - tw / 2 - 4, 400), (tx - tw / 2, ytop + 14), (tx + tw / 2, ytop + 14), (tx + tw / 2 + 4, 400)])
    dr.rect(tx - tw / 2 - 10, ytop, tx + tw / 2 + 10, ytop + 8)
    dr.poly([(tx - tw / 2, ytop + 8), (tx + tw / 2, ytop + 8), (tx + tw / 2 - 2, ytop + 14), (tx - tw / 2 + 2, ytop + 14)])
    for k in range(4):
        yy = int(ytop + 50 + k * 34)
        dr.rect(tx - tw / 2 - 5, yy, tx + tw / 2 + 5, yy + 3)
    side = 1 if rng.random() < 0.5 else -1
    truss(dr, tx + side * tw / 2, ytop + 70, tx + side * (tw / 2 + 50), ytop + 30, 6, 6)
    m = dr.mask()
    plate(L, m, ytop, 400, lad, bands=(0.04, 0.3))
    window_strips(L, m & ~grow(edge(m, 1, 0) | edge(m, -1, 0), 2), [np.full(L.w, int(ytop + 30 + k * 12))
                  for k in range(14)], rng, cols=("orange4", "yellow5"), on=0.4, seg=(2, 6), gap=(3, 9))
    light(L, tx - tw / 2 - 10, ytop - 1, "red4")
    light(L, tx + tw / 2 + 9, ytop - 1, "red4")


# ---------------------------------------------------------------------------------------------------- station_b

def station_b(seed):
    """The hangar interior: the far wall with bays full of warm light, gantries, an overhead crane, near pillars."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280

    # layer 0: the far wall of the hangar
    L0 = Layer(W0)
    vbands(L0, "outline", [(46, "slate0"), (96, "slate1"), (170, "steel1"), (300, "slate1"), (336, "slate0")],
           dpx=6)
    # wall panels: vertical ribs and horizontal girts
    for x in range(0, W0, 48):
        rib = (np.abs(wdx(L0.X, x, W0)) < 2) & (L0.Y > 40) & (L0.Y < 330)
        L0.put(rib, "slate0")
        L0.put((np.abs(wdx(L0.X, x - 2, W0)) < 0.5) & (L0.Y > 40) & (L0.Y < 330), "slate2")
    for y in (70, 118, 300):
        L0.put((np.abs(L0.Y - y) < 1.5), "slate0")
        L0.put((np.abs(L0.Y - y + 2) < 0.5), "steel2")
    # the bays: warm light inside, ship silhouettes, a lit frame
    for bx, bw, bh in ((150, 210, 150), (500, 170, 128), (790, 230, 160)):
        top = 330 - bh
        inside = (np.abs(wdx(L0.X, bx, W0)) < bw / 2) & (L0.Y > top) & (L0.Y < 330)
        bands_at(L0, L0.Y, "brown1", [(top + bh * 0.25, "brown2"), (top + bh * 0.5, "orange2"),
                                     (top + bh * 0.78, "orange3"), (top + bh * 0.93, "yellow4")], dpx=4,
                 mask=inside)
        L0.glow[inside & (L0.Y > top + bh * 0.68)] = True
        # silhouettes inside the bay: a ship nose, crates, a gantry
        dr = Draw(W0)
        sy = 330 - bh * 0.3
        dr.poly([(bx - bw * 0.46, sy - bh * 0.1), (bx - bw * 0.1, sy - bh * 0.12), (bx + bw * 0.2, sy),
                 (bx - bw * 0.1, sy + bh * 0.1), (bx - bw * 0.46, sy + bh * 0.1)])
        dr.poly([(bx - bw * 0.3, sy - bh * 0.1), (bx - bw * 0.22, sy - bh * 0.22), (bx - bw * 0.12, sy - bh * 0.1)])
        dr.rect(bx - bw * 0.3, sy + bh * 0.1, bx - bw * 0.28, 330)
        dr.rect(bx - bw * 0.02, sy + bh * 0.08, bx, 330)
        dr.rect(bx + bw * 0.33, 312, bx + bw * 0.45, 330)
        dr.rect(bx + bw * 0.36, 300, bx + bw * 0.44, 312)
        truss(dr, bx - bw / 2, top + 26, bx + bw / 2, top + 26, 6, 6)
        sil = dr.mask() & inside
        L0.put(sil, "brown1")
        L0.put(edge(sil, 0, -1) & sil, "brown2")
        # frame
        fr = (np.abs(wdx(L0.X, bx, W0)) < bw / 2 + 6) & (L0.Y > top - 8) & (L0.Y < 332) & ~inside
        L0.put(fr, "slate1")
        L0.put(fr & ((np.abs(L0.Y - (top - 8)) < 1) | (np.abs(wdx(L0.X, bx - bw / 2 - 6, W0)) < 1)), "steel2")
        hz = fr & (L0.Y > top - 8) & (L0.Y < top - 2)
        hazard(L0, hz, "yellow3", "slate0", 8)
        lamp_row(L0, top - 14, bx - bw / 2, bx + bw / 2, 24, "yellow5", 1)
    # warm haze from the bays over the lower wall
    haze = np.clip((L0.Y - 200) / 130, 0, 1) * 0.3
    hz = (haze > L0.by) & (L0.Y < 330) & ~L0.glow
    L0.put(hz & (L0.Y > 200), "brown1", keep=True)
    # control room windows high on the wall
    window_strips(L0, L0.Y > 0, [np.full(W0, y) for y in (84, 87, 104, 107)], rng, cols=("cyan4", "ice5", "yellow5"),
                  on=0.5, seg=(10, 40), gap=(20, 80))
    # floor
    floor = L0.Y >= 332
    bands_at(L0, L0.Y, "slate1", [(338, "slate0"), (360, "outline")], dpx=3, mask=floor)
    for bx, bw, bh in ((150, 210, 150), (500, 170, 128), (790, 230, 160)):
        refl = floor & (np.abs(wdx(L0.X, bx, W0)) < bw / 2 - 10) & (L0.Y < 372)
        cover = np.clip(1 - (L0.Y - 332) / 40, 0, 1) * 0.55
        L0.put(refl & (cover > L0.by), "brown2", keep=True)
    for x in range(0, W0, 64):
        L0.put(floor & (np.abs(wdx(L0.X, x + (L0.Y - 332) * 1.2, W0)) < 0.5), "slate1")
    lamp_row(L0, 52, 10, W0, 40, "yellow6", 1)

    # layer 1: gantry walkways with hanging lamps and their light cones
    L1 = Layer(W)
    lad1 = ladder("outline slate1 slate2 steel2 steel3")
    dr = Draw(W)
    truss(dr, 0, 168, W, 168, 14, 14, cw=2, bw=1)
    dr.rect(0, 180, W, 183)
    dr.rect(0, 152, W, 153)
    for x in range(160, W, 320):
        dr.rect(x - 7, 183, x + 7, 400)
        dr.rect(x - 11, 330, x + 11, 400)
        truss(dr, x, 183, x, 330, 14, 12, cw=2, bw=1)
        dr.line([(x - 7, 190), (x - 60, 182)], 2)
        dr.line([(x + 7, 190), (x + 60, 182)], 2)
    m1 = dr.mask()
    plate(L1, m1, 150, 400, lad1, bands=(0.03, 0.2))
    for x in range(80, W, 160):
        dr2 = Draw(W).rect(x - 1, 183, x, 196).rect(x - 5, 196, x + 5, 200)
        L1.put(dr2.mask(), lad1[1])
        cone(L1, x, 201, 22, 120, ["yellow4", "orange3", "brown2"], density=0.28)
        light(L1, x - 3, 200, "yellow6", size=2)
        light(L1, x + 2, 200, "yellow6", size=1)
    window_strips(L1, m1 & (L1.Y > 330), [np.full(W, y) for y in range(340, 396, 8)], rng,
                  cols=("orange4", "yellow5"), on=0.3, seg=(2, 5), gap=(4, 12))

    # layer 2: the overhead crane and a parked shuttle
    L2 = Layer(W)
    lad2 = ladder("outline slate1 slate2 steel2 steel3")
    dr = Draw(W)
    dr.rect(0, 22, W, 34)
    for x in range(0, W, 10):
        dr.rect(x, 34, x + 1, 38)
    dr.rect(0, 38, W, 40)
    # crane bridge
    dr.rect(300, 40, 700, 62)
    dr.rect(470, 62, 530, 80)
    m2 = dr.mask()
    plate(L2, m2, 22, 80, lad2)
    hazard(L2, (L2.Y > 54) & (L2.Y < 61) & (L2.X > 302) & (L2.X < 698), "yellow3", "outline", 10)
    cab = Draw(W).line([(490, 80), (490, 214)]).line([(510, 80), (510, 214)]).mask()
    L2.put(cab, lad2[2])
    box = Draw(W).rect(440, 214, 560, 226).rect(424, 226, 576, 290).mask()
    plate(L2, box, 214, 290, ladder("outline crimson1 red2 red3 orange3"))
    for x in range(430, 572, 8):
        L2.put(box & (np.abs(L2.X - x) < 0.5) & (L2.Y > 230) & (L2.Y < 287), "crimson1")
    light(L2, 499, 82, "red5", size=2)
    # shuttle on a pad
    pad = Draw(W).rect(900, 340, 1160, 352).poly([(920, 352), (1140, 352), (1120, 400), (940, 400)]).mask()
    plate(L2, pad, 340, 400, lad2, bands=(0.1, 0.4))
    hazard(L2, pad & (L2.Y > 343) & (L2.Y < 349), "yellow3", "outline", 8)
    ship(L2, rng, 1030, 306, 220, 50, -1, fogged("outline slate1 slate2 ice2 ice3", "slate1", 0.1), col("blue2"),
         kind=2)
    lamp_row(L2, 338, 906, 1160, 22, "orange5", 1)

    # layer 3: near pillars with hazard stripes and hanging cables
    L3 = Layer(W)
    dr = Draw(W)
    for x in (120, 760):
        dr.rect(x - 22, 0, x + 22, 400)
        dr.rect(x - 30, 0, x + 30, 18)
        dr.rect(x - 28, 360, x + 28, 400)
    m3 = dr.mask()
    L3.put(m3, "outline")
    L3.put(edge(m3, -1, 0) & (L3.Y > 18), "slate2")
    L3.put(shift(edge(m3, -1, 0), -1, 0) & m3 & (L3.Y > 18), "slate1")
    for x in (120, 760):
        hz = (np.abs(wdx(L3.X, x, W)) < 20) & (L3.Y > 300) & (L3.Y < 356)
        hazard(L3, hz, "yellow2", "outline", 12)
        for y in range(40, 300, 52):
            light(L3, x - 14, y, "slate2")
            light(L3, x + 13, y, "slate2")
    # cables hanging from the top, sagging between pillars
    for x0, x1, sag in ((142, 738, 70), (782, 1378, 50), (142, 400, 30)):
        xs = np.arange(x0, x1)
        t = (xs - x0) / (x1 - x0)
        ys = 20 + sag * 4 * t * (1 - t)
        cm = np.zeros(L3.a.shape, bool)
        for x, y in zip(xs, ys):
            cm[int(y):int(y) + 2, x % W] = True
        L3.put(cm, "outline")
    light(L3, 120, 10, "red4", size=2)
    light(L3, 760, 10, "red4", size=2)

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.06, 0.03), Spec(0.18, 0.06), Spec(0.35, 0.1), Spec(0.65, 0.2)]
    notes = """station_b: inside a big hangar: the far wall with three bays full of warm light, gantries with lamp
    cones, an overhead crane with a container, a parked shuttle, near pillars and cables. Layers 2 and 3 have
    structure in their first row (crane rail, pillars): it should repeat upwards."""
    return layers, specs, notes


# ------------------------------------------------------------------------------------------------------- hull_a

def hull_a(seed):
    """Open space outside the ring: a violet nebula, the Academy ring's arc receding, a sun flare."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280

    # layer 0: violet-black space, the nebula, stars, the sun with its flare
    L0 = Layer(W0)
    wob = (Noise(W0, 6, rng, 3)(L0.X, L0.Y * 0.3) - 0.5) * 30
    vbands(L0, "slate0", [(80, "violet0"), (190, "outline"), (330, "violet0")], dpx=8, wobble=wob)
    cool = swoosh(L0, rng, 140, 40, 50)
    nebula(L0, rng, ["violet0", "blue1", "slate2"], cool, [0.25, 0.42, 0.62], cells=4, warp=240)
    env = swoosh(L0, rng, 230, 50, 95)
    neb = nebula(L0, rng, ["violet1", "purple1", "violet2", "purple2", "magenta2", "magenta3"], env,
                 [0.12, 0.22, 0.34, 0.5, 0.7, 0.88])
    env = neb
    stars(L0, rng, 380, y1=390, glints=5)
    stars(L0, rng, 220, mask=env > 0.35, y1=390, glints=2, bright_frac=0.08)
    sx, sy = 150, 92
    sun(L0, sx, sy, [3, 5, 8, 12, 17, 24], ["white", "yellow7", "yellow6", "rose5", "magenta3", "purple2"],
        spikes=(150, 70), spike_cols=["white", "yellow6", "rose5", "magenta3", "purple2"], diag=22)
    # lens flare ghosts along the line through the view centre
    vx, vy = 480 - sx, 200 - sy
    for t, r, c in ((0.55, 3, "rose4"), (0.8, 9, "purple3"), (1.25, 5, "cyan3"), (1.6, 16, "violet3"),
                    (1.75, 2, "rose5")):
        ring_outline(L0, sx + vx * t, sy + vy * t, r, c)

    # layer 1: the Academy ring's arc, receding to the right, spokes to a hub below the view
    L1 = Layer(W)
    _ring_wheel(L1, rng, 640, 236, 470, 165, 7, 86, "violet0")

    # layer 2: solar arrays and radiator fins on masts
    L2 = Layer(W)
    _solar_masts(L2, rng)

    # layer 3: near hull silhouettes, rim lit by the sun
    L3 = Layer(W)
    _hull_near(L3, rng)

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.04, 0.02), Spec(0.1, 0.04), Spec(0.28, 0.1), Spec(0.55, 0.2)]
    notes = """hull_a: open space outside the ring: a violet nebula, the sun with its flare (upper left), the Academy
    ring's arc receding to the right with spokes to the hub, solar arrays, near hull masts."""
    return layers, specs, notes


def _ring_arc(L, rng, cx, cy, A, B, th0, th1, w0, w1, sky):
    """The ring as an elliptical arch from th0 (near, thick) to th1 (far, thin) degrees, with a lit top face, a
    shaded inner wall with window rows, segment joints and spokes converging on (cx, cy)."""
    dx = wdx(L.X, cx, L.w) / A
    dy = -(L.Y - cy) / B
    rho = np.sqrt(dx * dx + dy * dy)
    th = np.degrees(np.arctan2(dy, dx))
    t = np.clip((th0 - th) / (th0 - th1), 0, 1)              # 0 near .. 1 far
    w = w0 * (w1 / w0) ** t
    rloc = np.sqrt((A * np.cos(np.radians(th))) ** 2 + (B * np.sin(np.radians(th))) ** 2)
    s = (1 - rho) * rloc / w                                  # 0 at the outer edge .. 1 at the inner edge
    inarc = (th <= th0) & (th >= th1) & (s >= 0) & (s <= 1)
    base = "outline slate1 slate2 steel2 steel3 tan4"
    tiers = [fogged(base, sky, 0.0), fogged(base, sky, 0.3), fogged(base, sky, 0.55)]
    tiers_arr = np.stack(tiers)
    tier = np.clip(np.floor(t * 3 + (L.by - 0.5) * 0.5), 0, 2).astype(np.int32)
    top = s < 0.32
    lx = np.clip(0.5 - wdx(L.X, cx, L.w) / (2 * A), 0, 1)
    v = np.where(top, 0.62 + 0.36 * lx - s * 0.4, 0.42 - (s - 0.32) * 0.5)
    idx, dith = band(np.clip(v, 0, 0.999), 6, 0.3, None, L.by)
    rgb = tiers_arr[tier, idx]
    L.rgb[inarc] = rgb[inarc]
    L.a[inarc] = True
    L.keep[inarc] = dith[inarc]
    rim = inarc & ~shift(inarc, 0, -1)
    L.rgb[rim] = tiers_arr[tier, 5][rim]
    seam = inarc & (np.abs(s - 0.32) * w < 0.5)
    L.rgb[seam] = tiers_arr[tier, 0][seam]
    joint = inarc & (np.abs(((th - th1) % 5.0) - 2.5) * np.radians(1) * rloc < 0.5) & (w > 9)
    L.rgb[joint & ~rim] = tiers_arr[tier, 1][joint & ~rim]
    on = Noise(L.w, 40, rng, 1)(L.X, L.Y * 0 + 3) > 0.45
    for sr in (0.5, 0.66, 0.82):
        row = inarc & (np.abs(s - sr) * w < 0.5) & (w > 6)
        lit = row & on & ((L.X.astype(np.int32) % 2) == 0)
        c = np.where(t[..., None] < 0.5, np.array(col("yellow5"), np.uint8), np.array(col("orange4"), np.uint8))
        L.rgb[lit] = c[lit]
        L.keep[lit] = True
        L.glow[lit] = True
    for ths in (150, 112, 74, 40):
        tt = (th0 - ths) / (th0 - th1)
        ww = w0 * (w1 / w0) ** tt
        r0 = 1 - ww / np.sqrt((A * np.cos(np.radians(ths))) ** 2 + (B * np.sin(np.radians(ths))) ** 2)
        px = cx + A * r0 * np.cos(np.radians(ths))
        py = cy - B * r0 * np.sin(np.radians(ths))
        sw = max(2.0, ww * 0.32)
        hx, hy = cx, cy
        ang = np.arctan2(hy - py, hx - px)
        nx, ny = -np.sin(ang), np.cos(ang)
        sm = Draw(L.w).poly([(px + nx * sw / 2, py + ny * sw / 2), (px - nx * sw / 2, py - ny * sw / 2),
                             (hx - nx * sw * 0.8, hy - ny * sw * 0.8), (hx + nx * sw * 0.8, hy + ny * sw * 0.8)]).mask()
        sm &= ~inarc
        lad = tiers[min(2, int(tt * 3))]
        L.put(sm, lad[1])
        L.put(edge(sm, -1, 0) | edge(sm, 0, -1), lad[3])
        L.put(edge(sm, 1, 0), lad[0])
        cl = sm & ~grow(edge(sm, 1, 0) | edge(sm, -1, 0), 1)
        L.put((L.Y.astype(np.int32) % 9 == 0) & cl, "orange4", keep=True, glow=True)


def _ring_wheel(L, rng, cx, cy, A, B, w_far, w_near, sky):
    """The Academy ring seen from outside: an ellipse whose far (upper) side is thin and fogged and whose near
    (lower) side is thick and runs off the bottom, with a hub, an axis spindle and spokes."""
    base = "outline slate1 slate2 steel2 steel3 steel4"
    tiers = np.stack([fogged(base, sky, 0.05), fogged(base, sky, 0.3), fogged(base, sky, 0.55)])
    dx = wdx(L.X, cx, L.w)
    dy = L.Y - cy
    th = np.arctan2(-dy / B, dx / A)                           # ellipse angle; pi/2 = far side (top)
    depth = (1 - np.sin(th)) / 2                               # 0 far .. 1 near
    w = w_far * (w_near / w_far) ** depth
    rloc = np.sqrt((A * np.cos(th)) ** 2 + (B * np.sin(th)) ** 2)
    rho = np.sqrt((dx / A) ** 2 + (dy / B) ** 2)
    s = (1 - rho) * rloc / w                                   # 0 outer edge .. 1 inner edge
    band_m = (s >= 0) & (s <= 1)
    tier = np.clip(np.floor((1 - depth) * 3 + (L.by - 0.5) * 0.6), 0, 2).astype(np.int32)
    lx = np.clip(0.5 - dx / (2 * A), 0, 1)                     # the sun is to the left

    def paint_band(m):
        topf = s < 0.3
        v = np.where(topf, 0.66 + 0.33 * lx - s * 0.3, 0.2 + 0.32 * lx - (s - 0.3) * 0.25)
        idx, dith = band(np.clip(v, 0, 0.999), 6, 0.3, None, L.by)
        rgb = tiers[tier, idx]
        L.rgb[m] = rgb[m]
        L.a[m] = True
        L.keep[m] = dith[m]
        L.glow[m] = False
        rim = m & ~shift(band_m, 0, -1) & (dy < 0)
        L.rgb[rim] = tiers[tier, 5][rim]
        low = m & ~shift(band_m, 0, 1) & (dy > 0)
        L.rgb[low] = tiers[tier, 4][low]
        seam = m & (np.abs(s - 0.3) * w < 0.5) & (w > 8)
        L.rgb[seam] = tiers[tier, 0][seam]
        joint = m & ((np.abs(((np.degrees(th) + 360) % 7.5) - 3.75) * np.radians(1) * rloc) < 0.5) & (w > 14)
        L.rgb[joint & ~rim] = tiers[tier, 1][joint & ~rim]
        on = (Noise(L.w, 48, rng, 1)(L.X, np.full_like(L.X, 3.0)) > 0.42) & (L.X.astype(np.int32) % 2 == 0)
        for sr in (0.45, 0.6, 0.75, 0.9):
            row = m & (np.abs(s - sr) * w < 0.5) & (w > (8 if sr < 0.7 else 20)) & on
            c = np.where(depth[..., None] > 0.5, np.array(col("yellow5"), np.uint8),
                         np.array(col("orange4"), np.uint8))
            L.rgb[row] = c[row]
            L.keep[row] = True
            L.glow[row] = True

    far = band_m & (dy <= 0)
    paint_band(far)
    # hub, spindle and spokes
    hub = Draw(L.w).ellipse(cx - 34, cy - 20, cx + 34, cy + 20).mask()
    spindle = Draw(L.w).rect(cx - 6, cy - 120, cx + 6, cy + 60).mask() & ~band_m
    spokes = np.zeros(L.a.shape, bool)
    for ang in (20, 80, 140, 200, 260, 320):
        a = np.radians(ang)
        # inner edge point of the ring at this angle
        dd = (1 - np.sin(a)) / 2
        ww = w_far * (w_near / w_far) ** dd
        rr = np.sqrt((A * np.cos(a)) ** 2 + (B * np.sin(a)) ** 2)
        k = 1 - ww / rr
        px, py = cx + A * k * np.cos(a), cy - B * k * np.sin(a)
        sw = 3 + 9 * dd
        ang2 = np.arctan2(py - cy, px - cx)
        nx, ny = -np.sin(ang2), np.cos(ang2)
        spokes |= Draw(L.w).poly([(cx + nx * sw * 0.7, cy + ny * sw * 0.7), (cx - nx * sw * 0.7, cy - ny * sw * 0.7),
                                  (px - nx * sw / 2, py - ny * sw / 2), (px + nx * sw / 2, py + ny * sw / 2)]).mask()
    spokes &= ~band_m | (dy > 0)
    lad = tiers[1]
    for m, top, bot in ((spokes, cy - B, cy + B), (spindle, cy - 120, cy + 60), (hub, cy - 20, cy + 20)):
        v = np.clip(0.55 + 0.4 * (0.5 - dx / 80) - (L.Y - top) / max(1, bot - top) * 0.3, 0, 0.999)
        idx, dith = band(v, 4, 0.3, None, L.by)
        L.paint(m, idx + 1, lad, dith)
        L.put(edge(m, 0, -1) | edge(m, -1, 0), lad[4])
        L.put(edge(m, 1, 0) & ~edge(m, 0, -1), lad[0])
    hb = hub & ~grow(edge(hub, 0, 1) | edge(hub, 0, -1), 3) & (L.X.astype(np.int32) % 3 == 0)
    L.put(hb & (np.abs(L.Y - cy) < 1), "cyan5", keep=True, glow=True)
    L.put(hb & (np.abs(L.Y - cy - 6) < 1), "yellow5", keep=True, glow=True)
    light(L, cx - 1, cy - 122, "red5", size=2)
    light(L, cx - 1, cy + 61, "red4")
    near = band_m & (dy > 0)
    paint_band(near)


def _solar_masts(L, rng):
    """Solar arrays and radiator fins on lattice masts, catching the sun from the upper left."""
    cell = ladder("outline violet1 blue1 blue2 violet2")
    frame = ladder("outline slate1 slate2 steel3")
    for mx, top, pw, ph, side in ((200, 170, 150, 46, 1), (760, 200, 120, 38, -1), (1060, 150, 90, 70, 1)):
        dr = Draw(L.w)
        truss(dr, mx, 400, mx, top + ph // 2, 10, 10, cw=2, bw=1)
        mm = dr.mask()
        L.put(mm, frame[1])
        L.put(edge(mm, -1, 0), frame[3])
        x0 = mx + (6 if side > 0 else -6 - pw)
        for k in range(2):
            px0 = x0 + k * (pw // 2 + 2)
            pm = Draw(L.w).poly([(px0, top), (px0 + pw // 2 - 2, top - 6), (px0 + pw // 2 - 2, top + ph - 6),
                                 (px0, top + ph)]).mask()
            sheen = np.clip(1 - np.abs((L.X - px0) * 0.6 + (L.Y - top) - 18) / 26, 0, 1)
            v = 0.25 + 0.6 * sheen
            idx, dith = band(np.clip(v, 0, 0.999), 4, 0.4, None, L.by)
            L.paint(pm, idx + 1, cell, dith)
            gy = ((L.Y - top) + (L.X - px0) * 6 / (pw / 2)).astype(np.int32) % 6 == 0
            grid = pm & (((L.X - px0).astype(np.int32) % 7 == 0) | gy)
            L.put(grid, cell[0])
            L.put(edge(pm, 0, -1) | edge(pm, -1, 0), frame[2])
        fm = Draw(L.w).poly([(mx - 3, top + ph + 20), (mx - 3 - side * 40, top + ph + 70),
                             (mx - 3 - side * 40, top + ph + 76), (mx - 3, top + ph + 30)]).mask()
        L.put(fm, frame[1])
        L.put(edge(fm, 0, -1), frame[2])
        light(L, mx, top + ph // 2 - 2, "red4")


def _hull_near(L, rng):
    """Near silhouettes on the hull: a low hull ridge with vents, a big dish and a beacon post, rim lit by the sun
    (warm, left) and the nebula (violet, right)."""
    dr = Draw(L.w)
    xs = np.arange(L.w, dtype=np.float32)
    ridge_y = 374 + 6 * np.sin(2 * np.pi * xs / L.w * 2 + 1.0)
    for x in range(0, L.w, 2):
        dr.rect(x, ridge_y[x], x + 1, 400)
    for x0, w, h in ((80, 40, 10), (140, 16, 18), (470, 60, 8), (700, 26, 14), (1150, 50, 12)):
        dr.rect(x0, ridge_y[x0] - h, x0 + w, ridge_y[x0] + 2)
    # the dish
    dr.rect(290, 340, 330, ridge_y[300])
    dr.poly([(300, 340), (320, 340), (316, 300), (306, 300)])
    m = dr.mask()
    dish = Draw(L.w).ellipse(256, 236, 356, 300).mask() & ~Draw(L.w).ellipse(262, 226, 362, 290).mask()
    arm = Draw(L.w).line([(311, 300), (311, 262)], 3).mask() | Draw(L.w).line([(311, 262), (296, 236)], 1).mask()
    m |= dish | arm
    # beacon post
    post = Draw(L.w).poly([(880, 400), (888, 230), (900, 230), (908, 400)]).rect(876, 220, 912, 232)
    post.poly([(882, 220), (888, 204), (900, 204), (906, 220)]).rect(893, 186, 894, 204)
    for y in (280, 320, 360):
        post.rect(882, y, 906, y + 3)
    m |= post.mask()
    L.put(m, "outline")
    L.put(edge(m, 0, -1) | edge(m, -1, 0), "rose3")
    L.put(edge(m, 1, 0) & ~edge(m, 0, -1), "violet2")
    L.put(shift(edge(m, 0, -1), 0, -1) & m & ~edge(m, 0, -1) & ~edge(m, -1, 0), "purple1")
    light(L, 893, 184, "red5", size=2)
    light(L, 884, 212, "yellow6", size=2)
    light(L, 900, 212, "yellow6", size=2)
    light(L, 295, 234, "red4")
    for x in range(476, 528, 10):
        light(L, x, int(ridge_y[x]) - 5, "cyan4")


# ------------------------------------------------------------------------------------------------------- hull_b

def hull_b(seed):
    """Open space: a beacon tower on a rock in the distance sweeping its beams, a debris field, a dark planet's limb."""
    rng = np.random.default_rng(seed)
    W0, W = 960, 1280

    # layer 0: cold space, the dark planet below, the beacon and its beams
    L0 = Layer(W0)
    wob = (Noise(W0, 5, rng, 3)(L0.X, L0.Y * 0.2) - 0.5) * 40
    vbands(L0, "slate0", [(170, "teal0"), (290, "cyan0")], dpx=10, wobble=wob)
    stars(L0, rng, 360, y1=380, glints=4, tints=("ice", "cyan", "yellow"))
    # the planet: a dome rising from below, night side with faint cloud bands and city lights
    pcx, pcy, pr = 430, 1260, 960
    dx = wdx(L0.X, pcx, W0)
    dist = np.sqrt(dx * dx + (L0.Y - pcy) ** 2)
    disk = dist <= pr
    clouds = Noise(W0, 3, rng, 4)(L0.X, L0.Y * 5.0)
    depth_in = pr - dist
    v = np.clip(0.55 - depth_in / 60, 0, 1) * 0.8 + (clouds - 0.5) * 0.25
    bands_at(L0, v, "outline", [(0.18, "slate0"), (0.32, "slate1"), (0.5, "blue1")], dpx=0.03, mask=disk)
    for _ in range(26):
        x = int(rng.integers(60, 860))
        top = pcy - np.sqrt(max(0, pr * pr - (x - pcx) ** 2))
        if top > 380:
            continue
        y = int(rng.uniform(top + 14, 398))
        for k in range(int(rng.integers(2, 7))):
            xx, yy = x + int(rng.integers(-6, 7)), y + int(rng.integers(-2, 3))
            if 0 <= yy < 400 and disk[yy, xx % W0]:
                L0.put(_px(L0, xx, yy), "orange4" if k % 3 else "yellow5", keep=True, glow=True)
    # atmosphere: a thin glowing rim, brightest towards the beacon side
    rimd = dist - pr
    up = np.clip(1 - np.abs(dx) / 700, 0, 1)
    for d0, d1, c in ((0, 1.2, "cyan4"), (1.2, 2.6, "cyan3"), (2.6, 5.0, "blue2")):
        m = (rimd > d0) & (rimd <= d1) & (up > 0.15)
        L0.put(m, c, keep=True, glow=d0 == 0)
    haze = (rimd > 5) & (rimd < 14) & (np.clip(1 - (rimd - 5) / 9, 0, 1) * 0.5 * up > L0.by)
    L0.put(haze, "blue1", keep=True)
    L0.put(disk & (rimd > -1.5), "ice4", keep=True, glow=True)
    # the beacon: a tower on a floating rock, a prism at the top, two beams
    bx, by = 640, 128
    beams = np.zeros(L0.a.shape, np.float32)
    for ang, wd in ((-152, 7.0), (-18, 5.0)):
        a = np.degrees(np.arctan2(L0.Y - by, wdx(L0.X, bx, W0)))
        da = np.abs((a - ang + 180) % 360 - 180)
        r = np.sqrt(wdx(L0.X, bx, W0) ** 2 + (L0.Y - by) ** 2)
        beams = np.maximum(beams, np.clip(1 - da / wd, 0, 1) * np.clip(1 - r / 620, 0, 1) * (r > 6))
    lift(L0, (beams > 0.05 + L0.by * 0.5) & ~L0.keep, 1)
    lift(L0, (beams > 0.45 + L0.by * 0.4) & ~L0.keep, 1)
    rock(L0, rng, bx, by + 70, 26, ladder("outline slate1 slate2 steel2 steel3"), rim="cyan3", squash=0.6, jag=0.3)
    dr = Draw(W0)
    dr.poly([(bx - 7, by + 62), (bx - 4, by + 12), (bx + 4, by + 12), (bx + 7, by + 62)])
    dr.rect(bx - 9, by + 30, bx + 9, by + 33)
    dr.rect(bx - 6, by + 8, bx + 6, by + 12)
    tm = dr.mask()
    plate(L0, tm, by + 8, by + 62, ladder("outline slate1 slate2 steel3 steel4"))
    prism = Draw(W0).poly([(bx, by - 8), (bx + 6, by), (bx, by + 8), (bx - 6, by)]).mask()
    L0.put(prism, "cyan6", keep=True, glow=True)
    L0.put(prism & (wdx(L0.X, bx, W0) < 0) & (L0.Y < by), "white", keep=True, glow=True)
    L0.put(prism & (wdx(L0.X, bx, W0) > 0) & (L0.Y > by), "cyan4", keep=True, glow=True)
    ring_outline(L0, bx, by, 11, "cyan3")
    for k in (1, 2):
        for s_ in (-1, 1):
            L0.put(_px(L0, bx + s_ * (8 + k), by), "cyan5", keep=True, glow=True)
    window_strips(L0, tm, [np.full(W0, y) for y in range(by + 18, by + 60, 6)], rng, cols=("yellow5",), on=0.7,
                  seg=(1, 3), gap=(1, 4))

    # layer 1: the far debris field, a loose band of small rocks
    L1 = Layer(W)
    lad1 = fogged("outline slate1 slate2 steel2 steel3", "slate1", 0.35)
    lad1b = fogged("outline brown1 brown2 tan2 tan3", "slate1", 0.35)
    for i in range(110):
        x = rng.uniform(0, W)
        y = 210 + 70 * np.sin(2 * np.pi * x / W * 2 + 0.7) + rng.normal(0, 38)
        r = rng.uniform(2.0, 7.5) if rng.random() < 0.85 else rng.uniform(8, 14)
        rock(L1, rng, x, y, r, lad1 if i % 4 else lad1b, rim="cyan2" if r > 4 else None, jag=0.4, craters=1)

    # layer 2: mid debris: rocks, torn hull plates, a broken girder
    L2 = Layer(W)
    lad2 = fogged("outline slate1 slate2 steel2 steel3 steel4", "slate1", 0.12)
    lad2b = fogged("outline brown1 brown2 tan2 tan3 tan4", "slate1", 0.12)
    for i, (x, y, r) in enumerate(((90, 120, 22), (330, 250, 14), (520, 90, 9), (700, 300, 26), (930, 160, 17),
                                   (1180, 280, 11), (1080, 70, 8), (420, 340, 7))):
        rock(L2, rng, x, y, r, lad2b if i % 3 == 1 else lad2, rim="cyan3", jag=0.35, craters=3)
    for x, y, w_, h_, ang in ((240, 170, 46, 22, 0.35), (820, 240, 60, 18, -0.25), (1010, 340, 38, 28, 0.6)):
        _hull_plate(L2, rng, x, y, w_, h_, ang, lad2)
    dr = Draw(W)
    truss(dr, 560, 200, 660, 150, 8, 8, cw=2, bw=1)
    gm = dr.mask()
    L2.put(gm, lad2[2])
    L2.put(edge(gm, 0, -1), lad2[4])

    # layer 3: near dark chunks, rim lit cyan by the beacon
    L3 = Layer(W)
    lad3 = ladder("outline slate0 slate1 slate2")
    rock(L3, rng, 160, 410, 64, lad3, rim="cyan3", squash=0.8, jag=0.25, craters=2)
    rock(L3, rng, 760, 140, 24, lad3, rim="cyan3", jag=0.3, craters=1)
    _hull_plate(L3, rng, 1000, 372, 150, 56, -0.12, ladder("outline slate0 slate1 slate2 steel2"))
    rock(L3, rng, 560, 404, 30, lad3, rim="cyan3", jag=0.3, craters=1)

    layers = [L0, L1, L2, L3]
    specs = [Spec(0.04, 0.02), Spec(0.12, 0.05), Spec(0.3, 0.1), Spec(0.6, 0.2)]
    notes = """hull_b: open space: a beacon on a floating rock sweeping two beams, the night side of a dark planet
    with a glowing rim below, a debris field in three depths."""
    return layers, specs, notes


def _hull_plate(L, rng, cx, cy, w, h, ang, lad):
    """A torn piece of hull: a rotated plate with ribs and a ragged broken edge."""
    ca, sa = np.cos(ang), np.sin(ang)
    R = int(np.hypot(w, h) / 2) + 4
    ys, xs, Yl, Xl = local(L, cx - R, cy - R, 2 * R + 1, 2 * R + 1)
    if Yl.size == 0:
        return
    u = (Xl - cx) * ca + (Yl - cy) * sa
    v = -(Xl - cx) * sa + (Yl - cy) * ca
    rag = Noise(64, 8, rng, 2)(v * 3 + 100, u * 0 + 7) * w * 0.35
    m = (np.abs(v) < h / 2) & (u > -w / 2) & (u < w / 2 - rag)
    lad = np.asarray(lad, np.uint8)
    t = (v + h / 2) / h
    idx = np.where(t < 0.25, len(lad) - 2, np.where(t < 0.7, len(lad) - 3, len(lad) - 4)).astype(np.int32)
    ribs = (np.abs(((u + w / 2) % 9) - 4.5) < 0.6)
    idx = np.where(ribs, np.maximum(idx - 1, 0), idx)
    rgb = lad[idx]
    p = np.pad(m, 1)
    top = m & ~p[0:m.shape[0], 1:1 + m.shape[1]]
    rgb[top] = lad[-1]
    bot = m & ~p[2:2 + m.shape[0], 1:1 + m.shape[1]]
    rgb[bot] = lad[0]
    stamp(L, ys, xs, m, rgb)


def cloud_band(L, rng, slope, y0, width):
    """A soft diagonal band (0..1) broken up by noise: a galaxy's arm or a dust lane."""
    n = Noise(L.w, 4, rng, 5, 0.55)
    yy = y0 + slope * 60 * np.sin(2 * np.pi * L.X / L.w)
    dist = np.abs(L.Y - yy) / width
    base = np.exp(-dist * dist)
    return np.clip(base * (0.35 + 0.9 * n(L.X, L.Y)), 0, 1)


SCENES = {"station_a": station_a, "station_b": station_b, "hull_a": hull_a, "hull_b": hull_b}
