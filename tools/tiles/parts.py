"""Shared painters for the small sheets (platform, blocks, liquid) and deco sprites, parameterised by theme colours.
A `Kit` holds a theme's ramps; every painter returns Tiles. Light comes from the top left everywhere."""
import math

import numpy as np
from scipy import ndimage

from tilelib import (T, XX, YY, LIGHT, Tile, RAMPS, C, shape_mask, shade_form, outline_shape, periodic_noise, qidx,
                     rivet, hazard, inset_rect, bevel_rect, inner_depth, edge_dir, noise_1d)

OUT = C("outline", 0)
WHITE = C("white", 0)


class Kit:
    """metal: ramp for frames/housings (8 colours), accent: glow ramp, etc."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


# ------------------------------------------------------------------------------------------------------ geometry


def poly(w, h, pts):
    return shape_mask(w, h, lambda d: d.polygon(pts, fill=1))


def ellipse(w, h, box):
    return shape_mask(w, h, lambda d: d.ellipse(box, fill=1))


def rectm(w, h, x0, y0, x1, y1):
    m = np.zeros((h, w), bool)
    m[max(0, y0): y1 + 1, max(0, x0): x1 + 1] = True
    return m


def box(t, x0, y0, x1, y1, ramp, face, outline=True, bev=1, clip=None, glow=False):
    """A bevelled box: face shade, lighter top/left, darker bottom/right, optional darkest outline ring."""
    hi = min(len(ramp) - 1, face + 2)
    hi1 = min(len(ramp) - 1, face + 1)
    lo = max(0, face - 1)
    lo2 = max(0, face - 2)
    if outline:
        t.rect(x0, y0, x1, y1, ramp[0], clip=clip)
        x0, y0, x1, y1 = x0 + 1, y0 + 1, x1 - 1, y1 - 1
    t.rect(x0, y0, x1, y1, ramp[face], glow, clip=clip)
    for i in range(bev):
        t.rect(x0 + i, y0 + i, x1 - i, y0 + i, ramp[hi if i == 0 else hi1], glow, clip=clip)
        t.rect(x0 + i, y0 + i, x0 + i, y1 - i, ramp[hi1], glow, clip=clip)
        t.rect(x0 + i, y1 - i, x1 - i, y1 - i, ramp[lo2 if i == 0 else lo], glow, clip=clip)
        t.rect(x1 - i, y0 + i + 1, x1 - i, y1 - i, ramp[lo], glow, clip=clip)


def grid(h, w):
    return np.mgrid[0:h, 0:w]


# -------------------------------------------------------------------------------------------------------- spikes


def spike_tile(direction, ramp, base_ramp, n=4, height=17, tip=None, glow_tip=False, base_h=6, jag=0, seed=0,
               outline=None, plate=True):
    """Spikes pointing up/down/left/right on a base plate. ramp: spike shades (dark .. light, 8), base_ramp: plate.
    Drawn pointing up, then flipped/transposed so the lit half always faces the top left."""
    rng = np.random.default_rng(seed)
    up = Tile()
    span = T // n
    yb = T - base_h
    nr = len(ramp)
    for i in range(n):
        cx = i * span + span / 2.0 - 0.5
        hgt = height + (int(rng.integers(-jag, jag + 1)) if jag else 0)
        tipy = yb - hgt
        hw = span / 2.0
        for y in range(max(0, tipy), yb):
            w = (y - tipy + 0.6) / hgt * hw
            xa, xb = int(math.floor(cx - w + 0.5)), int(math.ceil(cx + w - 0.5))
            for x in range(xa, xb + 1):
                if x < 0 or x >= T:
                    continue
                if x <= cx - 0.5:
                    col = ramp[nr - 3]
                else:
                    col = ramp[3]
                if x == xa:
                    col = ramp[nr - 2]
                if x == xb:
                    col = ramp[1]
                if abs(x - cx) < 0.6 and y < tipy + hgt * 0.6:
                    col = ramp[nr - 1]
                if tip is not None and y < tipy + 4:
                    col = tip[2] if x <= cx else tip[1]
                    up.px(x, y, col, glow_tip)
                else:
                    up.px(x, y, col)
    if outline is not None:
        m = up.a.copy()
        o = ndimage.binary_dilation(m) & ~m & (YY < yb)
        up.fill(o, outline)

    def tr(arr):
        if direction == "up":
            return arr
        if direction == "down":
            return arr[::-1]
        if direction == "left":
            return arr.transpose(1, 0, *range(2, arr.ndim))
        return arr.transpose(1, 0, *range(2, arr.ndim))[:, ::-1]
    t = Tile()
    t.c[:] = tr(up.c)
    t.a[:] = tr(up.a)
    t.g[:] = tr(up.g)
    if plate:
        b = base_h - 1
        x0, y0, x1, y1 = {"up": (0, T - base_h, T - 1, T - 1), "down": (0, 0, T - 1, b),
                          "left": (T - base_h, 0, T - 1, T - 1), "right": (0, 0, b, T - 1)}[direction]
        box(t, x0, y0, x1, y1, base_ramp, 3, outline=True)
        for i in range(4):
            if direction in ("up", "down"):
                bx, by = i * 8 + 3, (y0 + y1) // 2 - 1
            else:
                bx, by = (x0 + x1) // 2 - 1, i * 8 + 3
            rivet(t, bx, by, (base_ramp[1], base_ramp[4], base_ramp[6]))
    return t


# --------------------------------------------------------------------------------------------------------- doors


def door_tile(frame_ramp, leaf_ramp, glow_ramp, opening):
    """A stackable door segment: metal frame left/right, two leaves meeting in the middle with a lock light strip;
    opening 0 (closed) .. 3 (nearly open): the leaves slide into the frame."""
    t = Tile()
    fr = frame_ramp
    # frame posts
    for (x0, x1) in ((0, 4), (27, 31)):
        box(t, x0, 0, x1, 31, fr, 3, outline=False)
        t.rect(x0, 0, x1, 0, fr[4])
        t.rect(x0, 31, x1, 31, fr[1])
    t.rect(4, 0, 4, 31, fr[1])
    t.rect(27, 0, 27, 31, fr[2])
    t.rect(0, 0, 0, 31, fr[5])
    t.rect(31, 0, 31, 31, fr[0])
    for y in (4, 12, 20, 28):
        t.px(2, y, fr[6])
        t.px(2, y + 1, fr[1])
        t.px(29, y, fr[5])
        t.px(29, y + 1, fr[1])
    # recess behind the leaves
    t.rect(5, 0, 26, 31, OUT)
    gap = [0, 4, 8, 11][opening]
    lr = leaf_ramp
    gl = glow_ramp
    lw = 11 - gap  # width of each leaf
    if lw > 0:
        # left leaf: x 5 .. 5+lw-1 ; right leaf: 26-lw+1 .. 26
        for side in (0, 1):
            if side == 0:
                a, b = 5, 5 + lw - 1
            else:
                a, b = 26 - lw + 1, 26
            t.rect(a, 0, b, 31, lr[3])
            t.rect(a, 0, b, 0, lr[5])
            t.rect(a, 31, b, 31, lr[1])
            for y in (7, 15, 23):
                t.rect(a, y, b, y, lr[2])
                t.rect(a, y + 1, b, y + 1, lr[4])
            t.rect(a, 0, a, 31, lr[4])
            t.rect(b, 0, b, 31, lr[2])
            # lock strip at the meeting edge
            if side == 0:
                t.rect(b - 1, 2, b, 29, gl[5], glow=True)
                t.rect(b - 1, 2, b - 1, 29, gl[6], glow=True)
                t.rect(b - 1, 2, b, 2, gl[3], glow=True)
            else:
                t.rect(a, 2, a + 1, 29, gl[5], glow=True)
                t.rect(a, 2, a, 29, gl[6], glow=True)
                t.rect(a, 2, a + 1, 2, gl[3], glow=True)
            # key emblem: a small diamond lamp on each leaf
            cx = (a + b) // 2
            if b - a >= 6:
                for (dx, dy) in ((0, -1), (-1, 0), (0, 0), (1, 0), (0, 1)):
                    t.px(cx + dx - (1 if side == 0 else -1), 15 + dy + 1, gl[4], glow=True)
                t.px(cx - (1 if side == 0 else -1), 15, gl[7], glow=True)
    else:
        # fully retracted: just glow stubs at the frame edges
        t.rect(5, 0, 5, 31, gl[3], glow=True)
        t.rect(26, 0, 26, 31, gl[3], glow=True)
    return t


# ---------------------------------------------------------------------------------------------------- toggles


def toggle_on(ramp, glow_ramp, frame, frame_ramp):
    """A solid hard-light block, pulsing over 4 frames."""
    t = Tile()
    box(t, 0, 0, 31, 31, frame_ramp, 3, outline=True)
    t.rect(1, 1, 30, 1, frame_ramp[5])
    t.rect(1, 1, 1, 30, frame_ramp[4])
    pulse = [0, 1, 2, 1][frame]
    t.rect(4, 4, 27, 27, glow_ramp[2 + pulse], glow=True)
    # inner diagonal hatch of brighter light, moving with the frame
    m = (XX >= 5) & (XX <= 26) & (YY >= 5) & (YY <= 26) & (((XX + YY + frame * 2) % 8) < 2)
    t.fill(m, glow_ramp[4 + pulse], glow=True)
    t.rect(4, 4, 27, 4, glow_ramp[5 + min(pulse, 1)], glow=True)
    t.rect(4, 4, 4, 27, glow_ramp[5], glow=True)
    t.rect(4, 27, 27, 27, glow_ramp[2], glow=True)
    t.rect(27, 4, 27, 27, glow_ramp[2], glow=True)
    for (x, y) in ((1, 1), (28, 1), (1, 28), (28, 28)):
        t.rect(x, y, x + 2, y + 2, frame_ramp[5])
        t.px(x + 2, y + 2, frame_ramp[2])
    return t


def toggle_off(glow_ramp, frame):
    """Ghost outline: dashed corners of the block, marching slowly."""
    t = Tile()
    per = 8
    ring = np.zeros((T, T), bool)
    ring[1, 1:31] = ring[30, 1:31] = ring[1:31, 1] = ring[1:31, 30] = True
    # position along the perimeter
    pos = np.zeros((T, T), np.int32)
    pos[1, :] = XX[1, :]
    pos[:, 30] = 31 + YY[:, 30]
    pos[30, :] = 62 + (31 - XX[30, :])
    pos[:, 1] = 93 + (31 - YY[:, 1])
    dash = ((pos + frame * 2) % per) < 4
    t.fill(ring & dash, glow_ramp[4], glow=True)
    corners = np.zeros((T, T), bool)
    for (x, y) in ((1, 1), (30, 1), (1, 30), (30, 30)):
        corners[y, x] = True
    t.fill(corners, glow_ramp[6], glow=True)
    # faint centre mark
    t.fill((XX >= 14) & (XX <= 17) & (YY >= 14) & (YY <= 17) & (((XX + YY) % 2) == 0), glow_ramp[3], glow=True)
    return t


# --------------------------------------------------------------------------------------------------- conveyor


def conveyor_tile(frame, housing, belt, glow_ramp, chevron):
    """A conveyor segment: belt on top moving +x (frame advances 2 px), rollers in a housing below."""
    t = Tile()
    box(t, 0, 0, 31, 31, housing, 3, outline=False)
    t.rect(0, 31, 31, 31, housing[1])
    # belt band
    t.rect(0, 0, 31, 7, belt[1])
    t.rect(0, 0, 31, 0, belt[3])
    t.rect(0, 7, 31, 7, OUT)
    tread = ((XX + 32 - frame * 2) % 8)
    t.fill((YY >= 1) & (YY <= 5) & (tread < 2), belt[2])
    t.fill((YY == 1) & (tread < 2), belt[4])
    # chevrons on the belt
    ch = (YY >= 1) & (YY <= 6) & (((XX - frame * 2 + np.abs(YY - 3.5).astype(int)) % 16) < 2)
    t.fill(ch, chevron)
    # rollers
    for cx in (8, 24):
        rx = cx + 0
        m = ellipse(T, T, (rx - 5, 10, rx + 5, 20))
        t.fill(m, housing[1])
        m2 = ellipse(T, T, (rx - 4, 11, rx + 4, 19))
        t.fill(m2, housing[4])
        t.fill(m2 & (YY > 15), housing[2])
        ang = frame * math.pi / 4
        for a in (ang, ang + math.pi / 2):
            px_, py_ = int(round(rx + 3 * math.cos(a))), int(round(15 + 3 * math.sin(a)))
            t.px(px_, py_, housing[1])
        t.px(rx, 15, housing[6])
    # status lights
    t.rect(3, 25, 28, 27, housing[1])
    for i in range(6):
        on = (i - frame) % 4 == 0
        t.rect(4 + i * 4, 26, 5 + i * 4, 26, glow_ramp[5] if on else glow_ramp[2], glow=on)
    return t


# ------------------------------------------------------------------------------------------------------- liquid


def liquid_tiles(ramp, crest, glow=True, seed=1, wave_amp=1.6, line_col=None, bubble_cols=None, band=3):
    """Row 0: surface (4 frames), row 1: body (4 frames); both 32-periodic in x (and the body in y), looping in
    time. ramp: [deep, body, light band, lighter, ...]; crest: (crest colour, crest highlight)."""
    rng = np.random.default_rng(seed)
    x = np.arange(T)
    surf, body = [], []
    lc = line_col or ramp[2]
    bc = bubble_cols or (ramp[3], ramp[-1])
    ph0 = rng.uniform(0, 1, 3)
    for f in range(4):
        ph = f / 4.0
        bt = Tile()
        bt.fill(np.ones((T, T), bool), ramp[1], glow)
        for j in range(2):
            yj = 9 + 16 * j + 1.6 * np.sin(2 * math.pi * (x / 32.0 * (1 + j) + ph * (1 if j == 0 else -1) + ph0[j]))
            seg = np.sin(2 * math.pi * (x / 32.0 * 2 + ph0[2] + j * 0.37 + ph * (1 if j else -1))) > -0.1
            for xx in x[seg]:
                bt.px(int(xx), int(round(yj[xx])) % T, lc, glow)
        for i, bx in enumerate((7, 22)):
            by = (24 - f * 8 + i * 16) % T
            wob = int(round(math.sin(f * math.pi / 2 + i)))
            bt.px(bx + wob, by, bc[0], glow)
            bt.px(bx + wob + 1, by, bc[0], glow)
            bt.px(bx + wob, by - 1 if by > 0 else T - 1, bc[1], glow)
        body.append(bt)
        st = bt.copy()
        wave = 4.5 + wave_amp * np.sin(2 * math.pi * (x / 32.0 + ph)) + 0.7 * np.sin(2 * math.pi * (2 * x / 32.0 - ph))
        top = np.round(wave).astype(int)
        st.clear(YY < top[None, :])
        d = YY - top[None, :]
        st.fill((d >= 1) & (d <= band), ramp[2], glow)
        st.fill((d >= 1) & (d <= 1), ramp[3], glow)
        st.fill(d == 0, crest[0], glow)
        hi = (d == 0) & (np.roll(top, -1)[None, :] >= top[None, :]) & (np.roll(top, 1)[None, :] > top[None, :])
        st.fill(hi, crest[1], glow)
        surf.append(st)
    return [surf, body]


# --------------------------------------------------------------------------------------------- deco primitives


def grid(h, w):
    return np.mgrid[0:h, 0:w]


def line_m(w, h, pts, width=1):
    return shape_mask(w, h, lambda d: d.line(pts, fill=1, width=width))


def finish(t, outline=OUT):
    """Adds a 1 px dark outline around the opaque pixels (sprite/deco convention)."""
    if outline is not None:
        m = t.a.copy()
        o = ndimage.binary_dilation(m, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)) & ~m
        t.fill(o, outline)
    return t


def pad(t, n=1):
    """A copy of t with n transparent pixels around it (room for the outline)."""
    o = Tile(t.w + 2 * n, t.h + 2 * n)
    o.blit(t, n, n)
    return o


def d_lamp(w, h, housing, glow, shape="round"):
    """A wall lamp: housing plate with a glowing lens."""
    t = Tile(w + 2, h + 2)
    box(t, 1, 1, w, h, housing, 3, outline=False)
    lens = ellipse(t.w, t.h, (3, 3, w - 2, h - 2)) if shape == "round" else rectm(t.w, t.h, 3, 3, w - 2, h - 2)
    t.fill(lens, glow[4], glow=True)
    gy, gx = grid(t.h, t.w)
    cy = (3 + h - 2) / 2
    t.fill(lens & (gy < cy), glow[5], glow=True)
    t.fill(lens & (gy < cy - 1) & (gx < (3 + w - 2) / 2), glow[7], glow=True)
    return finish(t)


def d_pipe(w, h, ramp, horizontal=True, flanges=(), base=3):
    """A pipe with round shading across it and flanges at the given positions."""
    t = Tile(w, h)
    gy, gx = grid(h, w)
    rel = (gy + 0.5) / h if horizontal else (gx + 0.5) / w
    val = base + 1.9 * np.cos(rel * math.pi + 0.45)
    idx = np.clip(np.round(val), 1, len(ramp) - 1).astype(int)
    t.fill_idx(np.ones((h, w), bool), ramp, idx)
    for f in flanges:
        if horizontal:
            t.fill_idx(rectm(w, h, f, 0, f + 2, h - 1), ramp, np.clip(idx + 1, 0, len(ramp) - 1))
            t.rect(f + 2, 0, f + 2, h - 1, ramp[1])
        else:
            t.fill_idx(rectm(w, h, 0, f, w - 1, f + 2), ramp, np.clip(idx + 1, 0, len(ramp) - 1))
            t.rect(0, f + 2, w - 1, f + 2, ramp[1])
    return t


def d_crate(w, h, ramp, face=3, brace=True, band=None):
    t = Tile(w, h)
    box(t, 0, 0, w - 1, h - 1, ramp, face, outline=True)
    box(t, 2, 2, w - 3, h - 3, ramp, face - 1, outline=False)
    if brace:
        inner = rectm(w, h, 3, 3, w - 4, h - 4)
        m = line_m(w, h, [(3, 3), (w - 4, h - 4)], 2) | line_m(w, h, [(w - 4, 3), (3, h - 4)], 2)
        t.fill(m & inner, ramp[face])
        mm = line_m(w, h, [(3, 3), (w - 4, h - 4)], 1) | line_m(w, h, [(w - 4, 3), (3, h - 4)], 1)
        t.fill(mm & inner, ramp[face + 1])
    if band is not None:
        t.rect(2, h // 2 - 1, w - 3, h // 2, band)
    for (x, y) in ((1, 1), (w - 3, 1), (1, h - 3), (w - 3, h - 3)):
        t.px(x, y, ramp[face + 2])
    return t


def d_screen(w, h, frame, glow, kind="graph", seed=0):
    """A wall screen with an invented glyph-free readout (graph, bars or radar)."""
    rng = np.random.default_rng(seed)
    t = Tile(w, h)
    box(t, 0, 0, w - 1, h - 1, frame, 3, outline=True)
    sx0, sy0, sx1, sy1 = 3, 3, w - 4, h - 4
    t.rect(sx0, sy0, sx1, sy1, glow[1], glow=True)
    gy, gx = grid(h, w)
    scr = rectm(w, h, sx0, sy0, sx1, sy1)
    t.fill(scr & (((gy - sy0) % 3) == 2), glow[0], glow=True)
    if kind == "graph":
        for x in range(sx0 + 1, sx1):
            y = int((sy0 + sy1) / 2 + math.sin(x * 0.7 + seed) * (sy1 - sy0) * 0.3 + rng.uniform(-1, 1))
            t.px(x, y, glow[6], True)
            t.px(x, y + 1, glow[4], True)
    elif kind == "bars":
        for x in range(sx0 + 2, sx1 - 1, 3):
            hh = int(rng.integers(2, sy1 - sy0 - 1))
            t.rect(x, sy1 - hh, x + 1, sy1 - 1, glow[5], glow=True)
            t.px(x, sy1 - hh, glow[7], True)
    else:
        cx, cy = (sx0 + sx1) // 2, (sy0 + sy1) // 2
        r = min(sx1 - sx0, sy1 - sy0) // 2 - 1
        ring = ellipse(w, h, (cx - r, cy - r, cx + r, cy + r)) & ~ellipse(w, h, (cx - r + 1, cy - r + 1, cx + r - 1,
                                                                                cy + r - 1))
        t.fill(ring, glow[4], glow=True)
        t.fill(line_m(w, h, [(cx, cy), (cx + r - 1, cy - r // 2)]), glow[6], glow=True)
        t.px(cx + 2, cy + 2, glow[7], True)
    t.rect(sx0, sy0, sx1, sy0, glow[2], glow=True)
    return t


def d_porthole(d, frame, space=None, glass=None):
    """A round window onto space: frame ring with bolts, dark glass with a few stars and a highlight."""
    t = Tile(d, d)
    outer = ellipse(d, d, (0, 0, d - 1, d - 1))
    inner = ellipse(d, d, (4, 4, d - 5, d - 5))
    shade_form(t, outer, frame, 4, spread=2.2, round_=True)
    t.fill(outer & ~ndimage.binary_erosion(outer), frame[1])
    sp = space or [OUT, RAMPS["blue"][1], RAMPS["blue"][2]]
    t.fill(inner, sp[0])
    gy, gx = grid(d, d)
    t.fill(inner & (gy > d * 0.6), sp[1])
    rng = np.random.default_rng(d)
    for _ in range(d // 5):
        x, y = rng.integers(5, d - 5, 2)
        if inner[y, x]:
            t.px(int(x), int(y), WHITE)
    rim = inner & ~ndimage.binary_erosion(inner)
    t.fill(rim & (gy + gx < d), frame[1])
    hl = inner & ((gx - gy) > d * 0.15) & ((gx - gy) < d * 0.25) & (gy < d * 0.5)
    t.fill(hl, glass or sp[2])
    for a in range(0, 360, 45):
        x = int(round(d / 2 - 0.5 + (d / 2 - 2) * math.cos(math.radians(a))))
        y = int(round(d / 2 - 0.5 + (d / 2 - 2) * math.sin(math.radians(a))))
        t.px(x, y, frame[6])
    return t


# ------------------------------------------------------------------------------------------ generic block parts


def breakable_block(v, ramp, crack_dark, glow_col=None, seed=0, face=3, tex=True, edge_hi=None):
    """A bevelled block of a lighter, weaker material with a crack pattern (variant v); glow_col lights the crack."""
    t = Tile()
    box(t, 0, 0, 31, 31, ramp, face, outline=True)
    rng = np.random.default_rng(seed + v)
    if tex:
        h = periodic_noise(rng, T, 3, 3)
        inner = rectm(T, T, 2, 2, 29, 29)
        t.fill(inner & (h > 1.0), ramp[face + 1])
        t.fill(inner & (h < -1.0), ramp[face - 1])
    pts = [[(6, 4), (12, 12), (10, 19), (17, 26)], [(26, 5), (19, 13), (21, 20), (13, 27)],
           [(4, 16), (12, 14), (17, 18), (27, 15)], [(15, 3), (13, 12), (19, 18), (16, 28)]][v % 4]
    inner = rectm(T, T, 2, 2, 29, 29)
    cm = line_m(T, T, pts, 2) & inner
    t.fill(cm, crack_dark)
    if glow_col is not None:
        t.fill(line_m(T, T, pts, 1) & inner, glow_col, glow=True)
    # side branches
    a, b = pts[1], pts[2]
    t.fill(line_m(T, T, [a, (a[0] + 5, a[1] - 3)], 1) & inner, crack_dark)
    t.fill(line_m(T, T, [b, (b[0] - 5, b[1] + 2)], 1) & inner, crack_dark)
    t.rect(1, 1, 30, 1, edge_hi or ramp[min(len(ramp) - 1, face + 2)])
    return t


def crumble_block(stage, ramp, top=None, face=3, thick=12):
    """A slab on its last legs: intact, cracking, cracking more, falling apart. top: (lip, lip highlight)."""
    t = Tile()
    pieces = [(0, 15), (16, 31)] if stage < 3 else [(0, 9), (11, 20), (22, 31)]
    for i, (a, b) in enumerate(pieces):
        dy = 0 if stage < 3 else [3, 6, 2][i]
        dx = 0 if stage < 3 else [-1, 0, 1][i]
        box(t, a + dx, dy, b + dx, thick + dy, ramp, face, outline=True)
        if top is not None:
            t.rect(a + dx + 1, dy, b + dx - 1, dy + 1, top[0])
            t.rect(a + dx + 1, dy, b + dx - 1, dy, top[1])
        if stage < 3:
            # hanging debris under the slab
            t.rect(a + 5, thick + 1, a + 6, thick + 3 + (i * 2), ramp[2])
            t.px(a + 5, thick + 1, ramp[4])
    dark = ramp[0]
    if stage >= 1:
        t.fill(line_m(T, T, [(9, 2), (12, 7), (10, thick - 1)]), dark)
    if stage >= 2:
        t.fill(line_m(T, T, [(22, 2), (19, 7), (23, thick - 1)]), dark)
        t.fill(line_m(T, T, [(15, 3), (16, thick)]), dark)
    if stage == 3:
        for (x, y) in ((12, 22), (20, 26), (5, 27), (27, 24)):
            t.rect(x, y, x + 1, y + 1, ramp[3])
            t.px(x + 1, y + 1, ramp[1])
    return t


def gem_cluster(w, h, ramp, glow=True, seed=0, n=4, base_y=None, direction="up", spread=0.9):
    """Faceted crystal prisms growing from the bottom edge (direction up) or top edge (down)."""
    rng = np.random.default_rng(seed)
    t = Tile(w, h)
    nr = len(ramp)
    by = h - 1 if base_y is None else base_y
    for i in range(n):
        cx = w / 2 + (i - (n - 1) / 2) * (w / (n + 0.5)) + rng.uniform(-1, 1)
        hh = h * (0.45 + 0.55 * rng.random()) if i != n // 2 else h - 1
        ww = max(3.0, w / (n + 1) * 1.2)
        lean = (cx - w / 2) / w * spread * hh
        tipx = cx + lean
        if direction == "up":
            body = [(cx - ww / 2, by), (cx - ww / 2 + lean * 0.7, by - hh + ww * 0.8), (tipx, by - hh),
                    (cx + ww / 2 + lean * 0.7, by - hh + ww * 0.8), (cx + ww / 2, by)]
        else:
            body = [(cx - ww / 2, 0), (cx - ww / 2 + lean * 0.7, hh - ww * 0.8), (tipx, hh),
                    (cx + ww / 2 + lean * 0.7, hh - ww * 0.8), (cx + ww / 2, 0)]
        m = poly(w, h, body)
        gy, gx = grid(h, w)
        mid = cx + lean * ((by - gy) / max(1, hh) if direction == "up" else gy / max(1, hh)) * 0.7
        t.fill(m, ramp[nr - 4], glow)
        t.fill(m & (gx < mid), ramp[nr - 2], glow)
        t.fill(m & (gx < mid - ww * 0.25), ramp[nr - 1], glow)
        t.fill(m & (gx > mid + ww * 0.2), ramp[nr - 5], glow)
        e = m & ~ndimage.binary_erosion(m)
        t.fill(e & (gx > mid), ramp[max(0, nr - 6)], glow)
    return t
