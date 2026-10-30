"""Effects -- the fx sheet (64 x 64, anchor = centre) and fx_big (96 x 96, anchor = centre, the large explosion).

Pixel-art effects with stepped colour bands (no soft gradients): explosions are a noisy heat field cut into
white / yellow / orange / red / crimson bands that cools into grey smoke and dissolves.
"""
import math

import numpy as np

from bake import Canvas, Sheet, fbm, pixelize, vnoise

SMALL = (64, 64)
BIG = (96, 96)

HEAT = [(0.92, "white"), (0.74, "yellow:6"), (0.56, "yellow:4"), (0.40, "orange:4"), (0.26, "red:4"),
        (0.14, "crimson:3")]


def canvas(size=SMALL):
    return Canvas(size, (size[0] // 2, size[1] // 2), ss=4)


def done(c, keep_single=True, outline=False, cov=7):
    return pixelize(c, cov=cov, outline=outline, inner=False, keep_single=keep_single)


def F(c, mask, colour, glow=True):
    c.fill(mask, colour, glow=glow, line=False)


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 2


# ---------------------------------------------------------------------------------------------------------- explosions

def explosion(c, t, R, seed, blobs=5, embers=8):
    X, Y = c.X, c.Y
    rng = np.random.default_rng(seed)
    if t <= 0.0:   # first frame: the flash
        d = np.hypot(X, Y)
        F(c, d < R * 0.42, "yellow:6")
        F(c, d < R * 0.32, "white")
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            spike = c.capsule(0, 0, R * 0.62 * math.cos(a), R * 0.62 * math.sin(a), R * 0.07, 0.3) < 0
            F(c, spike, "white")
        return
    cen = [(0.0, 0.0)] + [tuple(rng.uniform(-R * 0.42, R * 0.42, 2)) for _ in range(blobs - 1)]
    rad = [R * 0.62] + list(rng.uniform(R * 0.32, R * 0.5, blobs - 1))
    delay = [0.0] + list(rng.uniform(0.0, 0.25, blobs - 1))
    rise = R * 0.55 * t * t
    n = fbm(X, Y - rise, 3.2 / R, seed + 3, 3)
    field = np.full(X.shape, -9.0)
    heat = np.zeros(X.shape)
    for (cx, cy), r, dl in zip(cen, rad, delay):
        tt = max(0.0, t - dl)
        if tt <= 0:
            continue
        g = 0.45 + 0.75 * ease_out(tt * 1.7)
        cy2 = cy + rise * (0.6 + 0.4 * (cy / R + 0.5))
        d = np.hypot(X - cx, Y - cy2) / (r * g)
        f = 1.0 - d
        field = np.maximum(field, f)
        cool = max(0.0, 1.0 - tt * 1.6)
        heat = np.maximum(heat, np.clip(f, 0, 1) ** 0.8 * 1.05 * cool + cool * 0.22)
    edge = field + (n - 0.5) * 0.55
    inside = edge > 0
    h = heat + (n - 0.5) * 0.3
    # smoke where it has cooled; holes eat it as it dissipates
    smoke = inside & (h < HEAT[-1][0] + 0.06)
    holes = n < (t - 0.42) * 1.25
    smoke &= ~holes
    if smoke.any():
        sm = fbm(X + 7, Y - rise, 2.6 / R, seed + 9, 2)
        lit = (X * -0.6 + (Y - rise) * 0.8) / R
        F(c, smoke, "grey:2", glow=False)
        F(c, smoke & (sm + lit * 0.25 > 0.42), "grey:3", glow=False)
        F(c, smoke & (sm + lit * 0.35 > 0.62), "grey:4", glow=False)
        F(c, smoke & (edge < 0.06), "slate:1", glow=False)
    for thr, colour in reversed(HEAT):
        F(c, inside & (h >= thr) & ~holes, colour)
    # shock ring early on
    if t < 0.32:
        rr = R * (0.55 + t * 1.6)
        ring = np.abs(np.hypot(X, Y) - rr) < max(0.6, R * 0.05 * (1 - t * 2.5))
        F(c, ring & ~inside, "yellow:6" if t < 0.18 else "orange:4")
    # embers flying out on arcs
    for k in range(embers):
        a = rng.uniform(0, 2 * math.pi)
        v = rng.uniform(0.7, 1.0) * R * 1.1
        ex = math.cos(a) * v * t
        ey = math.sin(a) * v * t - 0.9 * R * t * t
        if t < 0.85:
            F(c, c.circle(ex, ey, 1.1) < 0, "yellow:6" if t < 0.4 else "orange:4")


# ---------------------------------------------------------------------------------------------------------- small effects

def muzzle(i):
    c = canvas()
    X, Y = c.X, c.Y
    s = [1.0, 1.25, 0.8, 0.45][i]
    cone = c.polygon([(-1, 0), (3 * s, 3.2 * s), (11 * s, 0.8), (13 * s, 0), (11 * s, -0.8), (3 * s, -3.2 * s)])
    F(c, cone < 0.6, "orange:4")
    F(c, cone < -0.2, "yellow:5")
    F(c, c.circle(1, 0, 3.6 * s) < 0, "yellow:6")
    F(c, c.circle(1, 0, 2.2 * s) < 0, "white")
    for a in (60, -60):
        sp = c.capsule(1, 0, 1 + 6 * s * math.cos(math.radians(a)), 6 * s * math.sin(math.radians(a)), 0.9 * s, 0.2)
        F(c, sp < 0, "yellow:6")
    if i == 3:
        c.erase(c.circle(1, 0, 1.4) < 0)
    return done(c)


def spark(i):
    c = canvas()
    rng = np.random.default_rng(4)
    t = i / 4.0
    if i == 0:
        F(c, c.star(0, 0, 6, 1.6, 4, 45) < 0, "yellow:6")
        F(c, c.circle(0, 0, 2.2) < 0, "white")
        return done(c)
    for k in range(7):
        a = rng.uniform(0, 2 * math.pi)
        v = rng.uniform(13, 21)
        x0, y0 = math.cos(a) * v * (t - 0.12), math.sin(a) * v * (t - 0.12) - 3 * t * t
        x1, y1 = math.cos(a) * v * t, math.sin(a) * v * t - 4 * t * t
        w = 0.7 if i < 3 else 0.5
        F(c, c.capsule(x0, y0, x1, y1, w * 0.6, w) < 0, "orange:4" if i > 2 else "yellow:5")
        F(c, c.circle(x1, y1, w * 0.8) < 0, "white" if i < 3 else "yellow:6")
    if i == 1:
        F(c, c.circle(0, 0, 2.0) < 0, "yellow:6")
    return done(c)


def beam_in(i):
    c = canvas()
    X, Y = c.X, c.Y
    t = i / 7.0
    top = 32.0
    if i <= 2:      # beam strikes down
        bottom = top - (i + 1) * 22
        w = [1.0, 1.6, 2.6][i]
        col_ = (np.abs(X) < w + 1.4) & (Y < top) & (Y > bottom)
        F(c, col_, "blue:4")
        F(c, (np.abs(X) < w + 0.4) & (Y < top) & (Y > bottom), "cyan:5")
        F(c, (np.abs(X) < w * 0.45) & (Y < top) & (Y > bottom), "white")
    if i >= 2:      # flash at the centre, rings
        k = i - 2
        rr = 4 + k * 4.5
        ring = np.abs(np.hypot(X / 1.0, Y / 0.42) - rr) < 1.0 - k * 0.1
        F(c, ring, ("white", "cyan:6", "cyan:5", "cyan:4", "blue:4", "blue:3")[min(k, 5)])
        if k < 3:
            core = np.hypot(X, Y / 1.6) < 7 - k * 2
            F(c, core, "cyan:5")
            F(c, np.hypot(X, Y / 1.6) < 4 - k * 1.2, "white")
        if 2 <= k <= 4:
            col_ = (np.abs(X) < 3.0 - k * 0.6) & (np.abs(Y) < 26 - k * 6)
            F(c, col_, "cyan:4")
    if i >= 4:      # sparkles
        for (x, y), ph in zip(((-10, 8), (9, 13), (12, -4), (-6, -10), (2, 18)), range(5)):
            if (ph + i) % 2 == 0:
                s = 1.8
                F(c, ((np.abs(X - x) < 0.5) & (np.abs(Y - y) < s + 0.6)) | ((np.abs(Y - y) < 0.5) & (np.abs(X - x) < s + 0.6)),
                  "cyan:6")
                F(c, c.circle(x, y, 0.7) < 0, "white")
    return done(c)


def dust(i):
    c = canvas()
    t = i / 5.0
    for sx in (-1, 1):
        for k, (dx, r0) in enumerate(((4.0, 3.2), (9.0, 2.4))):
            x = sx * (dx + 9 * ease_out(t) * (1 + 0.3 * k))
            y = 2.5 + 4.0 * t + k * 0.8
            r = r0 * (1 + 0.6 * t) * (1 - t * 0.55)
            n = vnoise(c.X, c.Y, 0.8, 3 + k)
            blob = c.circle(x, y, r) + (n - 0.5) * 1.2 < 0
            blob &= c.Y > -0.5
            c.fill(blob, "tan:4", line=False)
            c.fill(blob & (c.circle(x - 0.6, y + 0.8, r * 0.6) < 0), "tan:6", line=False)
            c.fill(blob & (c.circle(x + 0.8, y - 0.9, r * 0.75) > 0) & (c.Y < y), "tan:3", line=False)
    if t > 0.6:
        c.erase(vnoise(c.X, c.Y, 0.9, 11) < (t - 0.6) * 2.2)
    return done(c, keep_single=False)


def sparkle(i):
    c = canvas()
    s = [1.0, 3.0, 5.0, 6.5, 4.0, 2.0][i]
    X, Y = c.X, c.Y
    star = ((np.abs(X) < 0.55) & (np.abs(Y) < s + 0.5)) | ((np.abs(Y) < 0.55) & (np.abs(X) < s + 0.5))
    diag = (np.abs(np.abs(X) - np.abs(Y)) < 0.5) & (np.hypot(X, Y) < s * 0.45)
    F(c, star | diag, "yellow:6" if i in (2, 3) else "cyan:6")
    F(c, c.circle(0, 0, 0.6 + s * 0.12) < 0, "white")
    if i in (2, 3):
        F(c, ((np.abs(X) < 0.55) & (np.abs(Y) < s * 0.55)) | ((np.abs(Y) < 0.55) & (np.abs(X) < s * 0.55)), "white")
    return done(c)


def pickup(i):
    c = canvas()
    X, Y = c.X, c.Y
    t = i / 7.0
    rr = 3 + 15 * ease_out(t)
    w = max(0.45, 1.6 * (1 - t))
    ring = np.abs(np.hypot(X, Y) - rr) < w
    F(c, ring, ("white", "cyan:6", "cyan:6", "cyan:5", "cyan:5", "cyan:4", "blue:4", "blue:3")[i])
    if i < 2:
        F(c, c.circle(0, 0, 5 - i * 2) < 0, "white")
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        d = 4 + 20 * ease_out(t)
        x, y = d * math.cos(a), d * math.sin(a) + 2 * t
        s = 2.2 * (1 - t) + 0.6
        if t < 0.95:
            st = ((np.abs(X - x) < 0.5) & (np.abs(Y - y) < s + 0.5)) | ((np.abs(Y - y) < 0.5) & (np.abs(X - x) < s + 0.5))
            F(c, st, "yellow:6" if k % 2 else "cyan:6")
            F(c, c.circle(x, y, 0.6) < 0, "white")
    return done(c)


def splash(i):
    """Something drops into liquid: a jet and a crown rise from the surface (the anchor line) and fall back."""
    c = canvas()
    t = i / 7.0
    X, Y = c.X, c.Y
    rng = np.random.default_rng(8)
    up = math.sin(math.pi * min(1.0, t * 1.25))
    # central jet
    jh = 18 * up
    if jh > 1.5:
        jet = (c.capsule(0, 0, 0, jh, 2.6 * (1 - t * 0.5), 1.2) < 0) & (Y > -0.5)
        c.fill(jet, "ice:5", line=False)
        c.fill(jet & (X < 0.2), "ice:6", line=False)
        c.fill(c.circle(0, jh + 0.8, 1.6 * (1 - t * 0.4)) < 0, "white", line=False)
    # crown walls
    ch = 9 * up
    if ch > 1:
        for sx in (-1, 1):
            x0 = sx * (4.5 + 7 * t)
            wall = c.capsule(x0, 0, x0 + sx * (2 + 3 * t), ch, 1.5, 0.7) < 0
            c.fill(wall & (Y > -0.5), "ice:5", line=False)
            c.fill(c.circle(x0 + sx * (2 + 3 * t), ch + 0.5, 1.0) < 0, "ice:7", line=False)
    # droplets on arcs
    for k in range(10):
        a = rng.uniform(0.35, math.pi - 0.35)
        v = rng.uniform(14, 26)
        tt = t * 1.15
        x = math.cos(a) * v * tt
        y = math.sin(a) * v * tt - 34 * tt * tt
        if y > 0 and 0.08 < t:
            r = rng.uniform(1.3, 1.9) * (1 - 0.3 * t)
            c.fill(c.circle(x, y, r) < 0, "ice:6", line=False)
            c.fill(c.circle(x - 0.35, y + 0.35, r * 0.5) < 0, "white", line=False)
    # ripples on the surface
    rr = 6 + 16 * t
    rip = (np.abs(np.abs(X) - rr) < 1.6) & (Y > -0.6) & (Y < 1.2)
    c.fill(rip, "ice:4" if t > 0.5 else "ice:6", line=False)
    return done(c, keep_single=False)


def smoke(i):
    c = canvas()
    t = i / 7.0
    X, Y = c.X, c.Y
    rise = 14 * t
    n = fbm(X, Y - rise, 0.22, 5, 3)
    blobs = np.full(X.shape, 9.0)
    for (x, y, r) in ((0, 0, 6.5), (-4, 3, 4.5), (4, 4, 5.0), (0, 8, 4.0)):
        blobs = np.minimum(blobs, c.circle(x * (1 + t * 0.6), y * (1 + t * 0.5) + rise, r * (0.6 + 0.8 * t)))
    m = blobs + (n - 0.5) * 3.0 < 0
    m &= ~(n < (t - 0.4) * 1.3)
    c.fill(m, "grey:3", line=False)
    c.fill(m & (n > 0.5), "grey:4", line=False)
    c.fill(m & (n > 0.62) & (X < 2), "grey:5", line=False)
    c.fill(m & (blobs > -1.0) & (Y < rise), "slate:2", line=False)
    return done(c, keep_single=False)


def charge(i):
    c = canvas()
    X, Y = c.X, c.Y
    rng = np.random.default_rng(21)
    pulse = (0.0, 0.6, 1.0, 0.6, 0.2, 0.8)[i]
    for k in range(10):
        a = rng.uniform(0, 2 * math.pi)
        ph = (rng.uniform(0, 1) + i / 6.0) % 1.0
        d = 4 + 16 * (1 - ph)
        x, y = d * math.cos(a), d * math.sin(a)
        x2, y2 = (d + 3.5) * math.cos(a), (d + 3.5) * math.sin(a)
        F(c, c.capsule(x2, y2, x, y, 0.25, 0.6) < 0, "cyan:5" if k % 2 else "blue:4")
        F(c, c.circle(x, y, 0.6) < 0, "white" if ph > 0.6 else "cyan:6")
    r = 3.2 + pulse * 1.4
    F(c, c.circle(0, 0, r + 1.4) < 0, "blue:4")
    F(c, c.circle(0, 0, r) < 0, "cyan:5")
    F(c, c.circle(0, 0, r * 0.62) < 0, "cyan:6")
    F(c, c.circle(0, 0, r * 0.32) < 0, "white")
    ring = np.abs(np.hypot(X, Y) - (r + 4 + 3 * (1 - pulse))) < 0.5
    F(c, ring & (((np.arctan2(Y, X) * 3 / np.pi + i) % 2) < 1), "cyan:4")
    return done(c)


def freeze(i):
    """Ice growing over a small enemy (about 28 x 28 around the centre); the last frame is the full block."""
    c = canvas()
    X, Y = c.X, c.Y
    t = (i + 1) / 8.0
    half = 14.0
    level = -half + 2 * half * min(1.0, t * 1.15)
    block = (np.abs(X) < half) & (np.abs(Y) < half)
    grown = block & (Y < level + vnoise(X, Y, 0.5, 4) * 4 - 2)
    # crystal facets: diagonal bands
    fac = ((X * 0.7 + Y) % 7) < 1.0
    rim = grown & ~((np.abs(X) < half - 1.5) & (np.abs(Y) < half - 1.5))
    inner_lines = grown & fac & ~rim
    c.fill(rim, "ice:5", glow=True)
    c.fill(rim & ((X < -half + 1.5) | (Y > half - 1.5)), "ice:7", glow=True)
    c.fill(inner_lines, "ice:4", glow=True)
    # icicle spikes on the growing front
    for k in range(6):
        x = -12 + k * 4.8
        tip = level + 3 + (k % 2) * 2
        sp = c.polygon([(x - 1.6, level - 1), (x + 1.6, level - 1), (x, tip)])
        c.fill((sp < 0) & block & (t < 1), "ice:6", glow=True)
    if t >= 1.0:
        c.fill(c.polygon([(-half + 2, half - 2), (-half + 7, half - 2), (-half + 2, half - 7)]) < 0, "white", glow=True)
        c.fill(rim & (X > half - 1.5), "ice:4", glow=True)
    for (x, y) in ((-9, -10), (7, -6), (-3, 3)):
        if y < level:
            c.fill(c.circle(x, y, 0.7) < 0, "white", glow=True)
    spr = done(c, outline=False)
    from bake import outline_sprite
    return outline_sprite(spr, "blue:2")


def shatter(i):
    c = canvas()
    t = i / 7.0
    rng = np.random.default_rng(31)
    if i == 0:
        F(c, (np.abs(c.X) < 13) & (np.abs(c.Y) < 13), "ice:6")
        F(c, c.star(0, 0, 16, 4, 4, 0) < 0, "white")
        return done(c)
    for k in range(11):
        a = rng.uniform(0, 2 * math.pi)
        v = rng.uniform(11, 19)
        x = math.cos(a) * v * t + rng.uniform(-6, 6) * (1 - t)
        y = math.sin(a) * v * t + rng.uniform(-6, 6) * (1 - t) - 22 * t * t
        s = rng.uniform(2.2, 4.2) * (1 - 0.3 * t)
        rot_ = rng.uniform(0, 6.3) + t * rng.uniform(-8, 8)
        pts = [(x + s * math.cos(rot_ + q), y + s * math.sin(rot_ + q) * 0.8) for q in (0, 2.3, 3.9)]
        tri = c.polygon(pts) < 0
        c.fill(tri, ("ice:6", "ice:5", "ice:7")[k % 3], glow=True)
        c.fill(tri & (c.circle(*pts[0], s * 0.45) < 0), "white", glow=True)
    spr = done(c, outline=False)
    from bake import outline_sprite
    return outline_sprite(spr, "blue:2")


def zap(i):
    c = canvas()
    rng = np.random.default_rng(40 + i)
    reach = [9, 14, 16, 13, 9, 5][i]
    F(c, c.circle(0, 0, [4, 3, 2.5, 2, 1.5, 1][i]) < 0, "cyan:6")
    F(c, c.circle(0, 0, [2.6, 1.8, 1.4, 1, 0.8, 0.5][i]) < 0, "white")
    for k in range(5):
        a = rng.uniform(0, 2 * math.pi)
        pts = [(0.0, 0.0)]
        for s in range(1, 4):
            d = reach * s / 3.0
            off = rng.uniform(-0.45, 0.45)
            pts.append((d * math.cos(a + off), d * math.sin(a + off)))
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            F(c, c.capsule(x0, y0, x1, y1, 1.1) < 0, "blue:4")
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            F(c, c.capsule(x0, y0, x1, y1, 0.45) < 0, "white" if i < 3 else "cyan:6")
    return done(c)


# ---------------------------------------------------------------------------------------------------------- sheets

def explode(n, R, seed, size=SMALL, embers=8, blobs=5):
    def fn(i):
        c = canvas(size)
        explosion(c, i / float(n - 1) if i else 0.0, R, seed, blobs=blobs, embers=embers)
        return done(c, keep_single=False)
    return fn


ANIMS = [
    # sheet, name, fps, mode, frames, fn, note
    ("fx", "muzzle", 30, "once", 4, muzzle, "at the muzzle point, pointing right"),
    ("fx", "spark", 24, "once", 5, spark, "hit spark"),
    ("fx", "explode_s", 20, "once", 8, explode(8, 10.0, 1, embers=6, blobs=4), ""),
    ("fx", "explode_m", 20, "once", 10, explode(10, 17.0, 2, embers=8, blobs=5), ""),
    ("fx", "explode_l", 18, "once", 12, explode(12, 19.0, 3, embers=10, blobs=6), "64 px version; fx_big has a bigger one"),
    ("fx", "beam_in", 16, "once", 8, beam_in, "ambush enemies beaming in (centre on the enemy)"),
    ("fx", "dust", 16, "once", 6, dust, "anchor on the ground: puffs sit above it, both sides"),
    ("fx", "sparkle", 12, "loop", 6, sparkle, ""),
    ("fx", "pickup", 20, "once", 8, pickup, ""),
    ("fx", "splash", 20, "once", 8, splash, "anchor on the liquid surface; pale so the engine can tint it per liquid"),
    ("fx", "smoke", 12, "once", 8, smoke, "rises from the anchor"),
    ("fx", "charge", 20, "loop", 6, charge, "at the muzzle while charging"),
    ("fx", "freeze", 16, "once", 8, freeze, "ice block about 28 x 28 around the anchor; hold the last frame"),
    ("fx", "shatter", 20, "once", 8, shatter, ""),
    ("fx", "zap", 24, "once", 6, zap, "arc hit"),
    ("fx_big", "explode_l", 18, "once", 12, explode(12, 34.0, 3, BIG, embers=14, blobs=7), "bosses, big enemies"),
]


def frame(job):
    sheet, name, i = job
    fn = next(a[5] for a in ANIMS if a[0] == sheet and a[1] == name)
    return fn(i)


def jobs():
    return [(a[0], a[1], i) for a in ANIMS for i in range(a[4])]


def sheets(frames):
    fx = Sheet("fx", SMALL, (32, 32), cols=16, title="effects (anchor = centre)")
    big = Sheet("fx_big", BIG, (48, 48), cols=8, title="big effects (anchor = centre)")
    for sheet, name, fps, mode, n, fn, note in ANIMS:
        sh = fx if sheet == "fx" else big
        sh.anim(name, fps, mode, [frames[(sheet, name, i)] for i in range(n)], note=note)
    fx.note("glow: all fire and energy pixels; smoke and dust do not glow")
    return [fx, big]
