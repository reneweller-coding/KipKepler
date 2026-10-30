"""Organic materials (rock, ice, chitin ...) for the autotiles: a 32-periodic stone height field per variant (all
variants blend to one common field at the tile border, so they fit together), lit from the top left, quantised to a
ramp, with irregular edges (displacement profiles pinned at the tile corners) and theme hooks for top lips (moss,
frost), undersides (roots, icicles, drips) and inner details."""
import math

import numpy as np
from scipy import ndimage

from tilelib import (T, XX, YY, BORDER, LIGHT, Tile, geom, displaced, qidx, periodic_noise, edge_profile, despeckle,
                     noise_1d)


def worley(rng, n, size=T, aspect=1.0, pts=None):
    """Periodic F1, F2 distance fields of n random points (aspect > 1 squashes cells vertically)."""
    if pts is None:
        pts = rng.uniform(0, size, (n, 2))
    f1 = np.full((size, size), 1e9, np.float32)
    f2 = np.full((size, size), 1e9, np.float32)
    idx = np.zeros((size, size), np.int32)
    for i, (px, py) in enumerate(pts):
        dx = np.abs(XX[:size, :size] - px)
        dx = np.minimum(dx, size - dx)
        dy = np.abs(YY[:size, :size] - py)
        dy = np.minimum(dy, size - dy)
        d = np.sqrt(dx * dx + (dy * aspect) ** 2)
        closer = d < f1
        f2 = np.where(closer, f1, np.minimum(f2, d))
        idx = np.where(closer, i, idx)
        f1 = np.where(closer, d, f1)
    return f1, f2, idx


def stone_height(rng, n=5, aspect=1.0, r=3.0, rough=0.15):
    f1, f2, idx = worley(rng, n, aspect=aspect)
    h = np.clip((f2 - f1) / r, 0, 1)
    h = h * h * (3 - 2 * h)
    h = h + rough * periodic_noise(rng, T, 2.0, 2.0)
    return h.astype(np.float32)


def blend_variants(common, variants, band=(1.5, 10.0)):
    w = np.clip((BORDER - band[0]) / (band[1] - band[0]), 0, 1)
    w = w * w * (3 - 2 * w)
    return [common * (1 - w) + v * w for v in variants]


def shade_height(h, z=0.6, gain=3.0):
    """Light value in about -1 .. 1 of a periodic height field, light from the top left."""
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    return np.clip((0.55 * gx + 0.83 * gy) * gain, -1, 1)


class StoneTex:
    """Per-variant stone patterns: a Voronoi of points with fixed points on the tile border (shared by all
    variants, so cracks cross the border at the same places and neighbours always agree) and free points inside.
    h: 0 on crack pixels, 1 elsewhere; lit: +1 on the lit lip of each stone (below/right of a crack), plus a tone
    per stone; cid: stone id per pixel."""

    def __init__(self, seed, n=3, aspect=1.0, border=(5, 17, 27), nvar=4, tone=0.6, margin=8, keep=1.0, **_):
        rng = np.random.default_rng(seed)
        bpts = [(x, 0.0) for x in border] + [(0.0, y + 0.5) for y in border]
        btone = rng.choice([-1, 0, 0, 1], len(bpts)) * 0.0
        self.h, self.lit, self.cid = [], [], []
        for _v in range(nvar):
            pts = list(bpts)
            tones = list(btone)
            tries = 0
            while len(pts) < len(bpts) + n and tries < 500:
                tries += 1
                p = rng.uniform(margin, T - margin, 2)
                if all(math.hypot(p[0] - q[0], (p[1] - q[1]) * aspect) > 9 for q in pts[len(bpts):]):
                    pts.append((p[0], p[1]))
                    tones.append(rng.choice([-1, 0, 0, 1]) * tone)
            f1, f2, cid = worley(None, 0, aspect=aspect, pts=np.array(pts))
            rx, dn = np.roll(cid, -1, 1), np.roll(cid, -1, 0)
            crack = (cid != rx) | (cid != dn)
            if keep < 1.0:
                other = np.where(cid != rx, rx, dn)
                a, b = np.minimum(cid, other), np.maximum(cid, other)
                hsh = ((a.astype(np.int64) * 7919 + b * 104729 + seed) * 40503) % 1000
                crack &= hsh < keep * 1000
            up, lf = np.roll(crack, 1, 0), np.roll(crack, 1, 1)
            lip = (up | lf) & ~crack
            shadow = ((np.roll(crack, -1, 0)) | (np.roll(crack, -1, 1))) & ~crack & ~lip
            tone_map = np.array(tones)[cid]
            self.h.append(np.where(crack, 0.0, 1.0).astype(np.float32))
            self.lit.append((lip * 1.0 - shadow * 0.7 + tone_map).astype(np.float32))
            self.cid.append(cid)


class Profiles:
    """Edge displacement profiles per variant (carved inwards, pinned at the tile corners)."""

    def __init__(self, seed, top=(0, 2), bottom=(1, 4), side=(0, 2), smooth=3.0, nvar=4):
        rng = np.random.default_rng(seed)
        self.p = []
        for _ in range(nvar):
            self.p.append({
                "t": top[0] + edge_profile(rng, top[1] - top[0], smooth, pin=(top[1] - top[0]) * 0.4),
                "b": bottom[0] + edge_profile(rng, bottom[1] - bottom[0], smooth, pin=(bottom[1] - bottom[0]) * 0.4),
                "l": side[0] + edge_profile(rng, side[1] - side[0], smooth, pin=(side[1] - side[0]) * 0.4),
                "r": side[0] + edge_profile(rng, side[1] - side[0], smooth, pin=(side[1] - side[0]) * 0.4),
            })

    def __getitem__(self, v):
        return self.p[v]


def rock_shape(m, v, prof, round_r=5):
    return displaced(geom(m, round_r, "round"), prof[v])


def rock_fill(t, s, tex, v, ramp, base, tex_amp=1.0, edge_amp=1.3, edge_w=6.0, deep=(10.0, 16.0, 0.9),
              crack=0.12, crack_col=None, dither=0.0, calm=(8.0, 20.0, 0.5), rim=True, rim_hi=None, rim_lo=None,
              region=None, thr=0.3, rim2=True):
    """Fills the solid pixels of shape s with stones: three clean tones per stone (lit top-left side, face, shadow
    side), dark cracks between them, a lighter band along lit edges and a darker one along shadowed edges."""
    sol = s.solid if region is None else region
    k = s.depth
    n = len(ramp)
    c = 1 - np.clip((k - calm[0]) / (calm[1] - calm[0]), 0, 1) * calm[2]
    L = tex.lit[v] * c
    tone = np.where(L > thr, 1.0, np.where(L < -thr, -1.0, 0.0))
    val = base + tex_amp * tone
    near = np.clip(1 - (k - 1) / edge_w, 0, 1)
    val = val + near * s.lit * edge_amp
    val = val - np.clip((k - deep[0]) / deep[1], 0, 1) * deep[2]
    idx = qidx(val, n, dither)
    idx = despeckle(idx, sol, 1)
    t.fill_idx(sol, ramp, idx)
    if crack is not None and crack_col is not None:
        cm = sol & thin_cracks(tex.h[v], crack) & (k > 1.5)
        t.fill(cm, crack_col)
    if rim:
        hi = rim_hi if rim_hi is not None else ramp[min(n - 1, int(base) + 3)]
        lo = rim_lo if rim_lo is not None else ramp[0]
        r0 = sol & (k < 1)
        t.fill(r0 & (s.lit > 0.25), hi)
        t.fill(r0 & (s.lit < -0.3), lo)
        if rim2:
            r1 = sol & (k >= 1) & (k < 2)
            t.fill(r1 & (s.lit < -0.5), ramp[1])
    return t


def thin_cracks(h, c):
    """Pixels where h is below c and a local minimum across x or y: crack lines about one pixel wide."""
    lx = (h <= np.roll(h, 1, 1)) & (h <= np.roll(h, -1, 1))
    ly = (h <= np.roll(h, 1, 0)) & (h <= np.roll(h, -1, 0))
    d1 = (h <= np.roll(np.roll(h, 1, 0), 1, 1)) & (h <= np.roll(np.roll(h, -1, 0), -1, 1))
    d2 = (h <= np.roll(np.roll(h, 1, 0), -1, 1)) & (h <= np.roll(np.roll(h, -1, 0), 1, 1))
    return (h < c) & (lx | ly | d1 | d2)


def column_rng(seed, v, salt=0):
    return np.random.default_rng(seed * 131 + v * 17 + salt)


def top_surface_y(s):
    """For each column: y of the topmost solid pixel that faces up (or 99)."""
    yy = np.where(s.solid & (s.wt > 0.5), YY, 99)
    return yy.min(0)


def bottom_surface_y(s):
    yy = np.where(s.solid & (s.wb > 0.5), YY, -1)
    return yy.max(0)


def hang(t, s, v, seed, cols_fn, count=(2, 4), length=(2, 7), xs_range=(3, 28), width=1, glow_fn=None,
         wiggle=False):
    """Hanging strands (roots, drips, icicles) below exposed undersides. cols_fn(i, n, y) -> colour per pixel
    (i = position along the strand 0 .. n-1)."""
    if not s.bottom:
        return
    rng = column_rng(seed, v, 7)
    by = bottom_surface_y(s)
    nh = int(rng.integers(count[0], count[1] + 1))
    xs = rng.choice(np.arange(xs_range[0], xs_range[1] + 1), size=nh, replace=False)
    for x in xs:
        y0 = by[x]
        if y0 < 0 or not s.solid[y0, x] or s.wb[y0, x] < 0.6:
            continue
        ln = int(rng.integers(length[0], length[1] + 1))
        ph = rng.uniform(0, 6.28)
        for i in range(ln):
            y = y0 + 1 + i
            if y >= T:
                break
            off = int(round(math.sin(i * 0.7 + ph) * 1.2)) if wiggle else 0
            wd = width if i < ln * 0.6 else 1
            for dx in range(wd):
                xx = x + dx + off
                if 0 <= xx < T and not s.solid[y, xx]:
                    col = cols_fn(i, ln, dx)
                    t.px(xx, y, col, bool(glow_fn and glow_fn(i, ln)))


def tufts(t, s, v, seed, cols_fn, count=(3, 6), height=(1, 3), xs_range=(2, 29), glow_fn=None):
    """Blades / shards sticking up from exposed tops into the carved band above the surface."""
    if not s.top:
        return
    rng = column_rng(seed, v, 3)
    ty = top_surface_y(s)
    nh = int(rng.integers(count[0], count[1] + 1))
    xs = rng.choice(np.arange(xs_range[0], xs_range[1] + 1), size=nh, replace=False)
    for x in xs:
        y0 = ty[x]
        if y0 >= 99 or y0 == 0:
            continue
        hgt = int(rng.integers(height[0], height[1] + 1))
        for i in range(hgt):
            y = y0 - 1 - i
            if y < 0 or s.solid[y, x]:
                break
            t.px(x, y, cols_fn(i, hgt), bool(glow_fn and glow_fn(i, hgt)))
