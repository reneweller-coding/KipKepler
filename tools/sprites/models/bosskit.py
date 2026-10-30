"""bosskit -- shared helpers for the four boss sheets (warden, broodmother, colossus, gloam). Not a model itself.

* `Stripes`, `Slab`: Paint regions (hazard stripes, bands, rings) in a part's local space
* 2D effect layers on a `bake.Canvas` (world coordinates, y up, origin = anchor): `flash`, `puffs`, `sparks`,
  `ring`, `beam_glow`; `fx_canvas` makes one, `over` / `under` merge it into a 3D render before pixelizing
* `arena(sheet, ...)`: work/sprites/<sheet>_arena.png -- frames at 1x on the real background layers and terrain
  tiles of the boss's arena, the hero beside them for scale, plus a darkened row with the glow mask and a bloom
  (how the boss reads in a dark level). Preview only.
"""
import math

import numpy as np
from PIL import Image, ImageFilter

from bake import ROOT, WORK, Canvas, Shape, fbm, vnoise

# ---------------------------------------------------------------------------------------------------------- regions


class Stripes(Shape):
    """Paint region: slabs across direction n, `period` apart, `duty` (0..1) of each period inside."""

    def __init__(self, n, period, duty=0.5, offset=0.0):
        n = np.asarray(n, np.float64)
        self.n = n / np.linalg.norm(n)
        self.period, self.duty, self.offset = period, duty, offset

    def sdf(self, p):
        t = (p @ self.n + self.offset) / self.period
        f = t - np.floor(t)
        return np.where(f < self.duty, -1.0, 1.0)

    def bounds(self):
        return np.full(3, -1e4), np.full(3, 1e4)


class Slab(Shape):
    """Paint region: lo <= p.n <= hi (a band across a part)."""

    def __init__(self, n, lo, hi):
        n = np.asarray(n, np.float64)
        self.n = n / np.linalg.norm(n)
        self.lo, self.hi = lo, hi

    def sdf(self, p):
        t = p @ self.n
        return np.maximum(self.lo - t, t - self.hi)

    def bounds(self):
        return np.full(3, -1e4), np.full(3, 1e4)


_GRIDS = {}


def noise3(p, seed=0):
    """Smooth 3D value noise in [0, 1] (lattice of 32^3 random values, wraps)."""
    g = _GRIDS.get(seed)
    if g is None:
        g = _GRIDS[seed] = np.random.default_rng(seed).random((32, 32, 32))
    q = p + 64.0
    i = np.floor(q).astype(np.int64)
    f = q - i
    f = f * f * (3 - 2 * f)
    i0 = i % 32
    i1 = (i + 1) % 32
    out = 0.0
    for cx in (0, 1):
        ix = i1[:, 0] if cx else i0[:, 0]
        wx = f[:, 0] if cx else 1 - f[:, 0]
        for cy in (0, 1):
            iy = i1[:, 1] if cy else i0[:, 1]
            wy = f[:, 1] if cy else 1 - f[:, 1]
            for cz in (0, 1):
                iz = i1[:, 2] if cz else i0[:, 2]
                wz = f[:, 2] if cz else 1 - f[:, 2]
                out = out + g[ix, iy, iz] * wx * wy * wz
    return out


class Veins(Shape):
    """Paint region: thin wiggly lines where a smooth 3D noise crosses 0.5 (glowing cracks, veins). freq = 1 / cell
    size in px, width = half width in noise units (about 0.05 gives 1-2 px lines at freq 0.1)."""

    def __init__(self, freq=0.1, width=0.05, seed=0, offset=(0.0, 0.0, 0.0)):
        self.freq, self.width, self.seed = freq, width, seed
        self.offset = np.asarray(offset, np.float64)

    def sdf(self, p):
        return np.abs(noise3((p + self.offset) * self.freq, self.seed) - 0.5) - self.width

    def bounds(self):
        return np.full(3, -1e4), np.full(3, 1e4)


# ---------------------------------------------------------------------------------------------------------- 2D effects


def fx_canvas(size, anchor, ss=4):
    return Canvas(size, anchor, ss=ss)


def F(c, mask, colour, glow=True, prio=1.0):
    if mask.dtype != bool:
        mask = mask < 0
    if mask.any():
        c.fill(mask, colour, glow=glow, line=False, prio=prio)


def over(raster, c):
    """Effect canvas on top of the render."""
    if (c.col >= 0).any():
        raster.overlay(c)
    return raster


def under(raster, c):
    """Effect canvas behind the render (only where the render is empty)."""
    m = c.col >= 0
    if m.any():
        c.z[m] = -1e6
        raster.overlay(c, zmode=True)
    return raster


def flash(c, x, y, r, rays=4, ang=45.0, cols=("orange:5", "yellow:6", "white"), prio=2.0):
    """A star-shaped muzzle flash / impact flare."""
    F(c, c.star(x, y, r, r * 0.32, rays, ang), cols[0], prio=prio)
    F(c, c.circle(x, y, r * 0.55), cols[1], prio=prio)
    F(c, c.star(x, y, r * 0.62, r * 0.18, rays, ang), cols[1], prio=prio)
    F(c, c.circle(x, y, r * 0.3), cols[2], prio=prio)


def puffs(c, blobs, shades=("grey:2", "grey:3", "grey:4", "grey:5"), seed=0, holes=0.0, glow=False, prio=1.0):
    """Noisy dust/smoke balls [(x, y, r), ...] lit from the top left in stepped shades (dark rim .. light top).
    holes (0..1) eats the clouds as they dissipate."""
    X, Y = c.X, c.Y
    field = np.full(X.shape, -9.0)
    lit = np.full(X.shape, -9.0)
    for x, y, r in blobs:
        if r <= 0.2:
            continue
        d = np.hypot(X - x, Y - y) / r
        f = 1.0 - d
        sel = f > field
        field = np.where(sel, f, field)
        lit = np.where(sel, ((X - x) * -0.55 + (Y - y) * 0.8) / r, lit)
    n = fbm(X, Y, 0.45, seed, 2)
    edge = field + (n - 0.5) * 0.5
    inside = edge > 0
    if holes > 0:
        inside &= ~(fbm(X + 11, Y, 0.3, seed + 5, 2) < holes * 0.75)
    if not inside.any():
        return
    F(c, inside, shades[0], glow=glow, prio=prio)
    F(c, inside & (lit + (n - 0.5) * 0.6 > -0.45) & (edge > 0.08), shades[1], glow=glow, prio=prio)
    F(c, inside & (lit + (n - 0.5) * 0.6 > 0.05) & (edge > 0.12), shades[2], glow=glow, prio=prio)
    if len(shades) > 3:
        F(c, inside & (lit + (n - 0.5) * 0.6 > 0.45) & (edge > 0.2), shades[3], glow=glow, prio=prio)


def sparks(c, pts, cols=("yellow:6", "white"), prio=3.0, size=0.9):
    """Small bright dots [(x, y), ...] (or (x, y, size))."""
    for p in pts:
        x, y = p[0], p[1]
        s = p[2] if len(p) > 2 else size
        F(c, c.circle(x, y, s), cols[0], prio=prio)
        if s > 0.8:
            F(c, c.circle(x, y, s * 0.45), cols[1], prio=prio)


def streaks(c, segs, cols=("orange:5", "yellow:6"), prio=3.0, w=0.6):
    """Short bright lines [(x0, y0, x1, y1), ...] (spark trails, speed lines)."""
    for x0, y0, x1, y1 in segs:
        F(c, c.capsule(x0, y0, x1, y1, w, w * 0.6), cols[0], prio=prio)
        F(c, c.capsule(x0, y0, x0 + (x1 - x0) * 0.4, y0 + (y1 - y0) * 0.4, w * 0.7, w * 0.4), cols[1], prio=prio)


def ring(c, x, y, rx, ry, w, colour, glow=True, prio=2.0, arc=None):
    """An elliptic ring (shock wave, halo); arc = (a0, a1) degrees keeps only that part."""
    d = np.abs(np.hypot((c.X - x) / rx, (c.Y - y) / ry) - 1.0) * min(rx, ry) - w
    m = d < 0
    if arc is not None:
        a = np.degrees(np.arctan2((c.Y - y) / ry, (c.X - x) / rx)) % 360
        a0, a1 = arc[0] % 360, arc[1] % 360
        m &= ((a >= a0) & (a <= a1)) if a0 <= a1 else ((a >= a0) | (a <= a1))
    F(c, m, colour, glow=glow, prio=prio)


def noise(c, freq, seed):
    return vnoise(c.X, c.Y, freq, seed)


# ---------------------------------------------------------------------------------------------------------- arena preview

THEMES = {"warden": "station", "broodmother": "hive", "colossus": "crystal", "gloam": "citadel"}


def _layers(theme, w, h, floor_y, camx=40):
    """The background layers composited for a view of w x h with the floor row at floor_y."""
    base = ROOT / "assets" / "bg" / f"{theme}_a"
    txt = (base / "bg.txt").read_text(encoding="utf-8").splitlines()
    fill = None
    par = {}
    for ln in txt:
        s = ln.split("#")[0].split()
        if not s:
            continue
        if s[0] == "fill":
            v = [int(t) for t in s[1:7]]
            fill = (tuple(v[:3]), tuple(v[3:]))
        elif s[0].startswith("layer"):
            par[int(s[0][5:])] = float(s[1])
    out = Image.new("RGBA", (w, h), fill[1] + (255,) if fill else (20, 20, 30, 255))
    for k in range(4):
        p = base / f"layer{k}.png"
        if not p.exists():
            continue
        im = Image.open(p).convert("RGBA")
        lw, lh = im.size
        top = h - 360              # a 360 px view at the bottom of a level: its last row is the layer's row 360
        x = -(int(camx * par.get(k, 0.5)) % lw)
        while x < w:
            out.paste(im, (x, top), im)
            x += lw
    return out


def _terrain(theme, w, h, floor_y):
    """Floor tiles from row floor_y down (top surface tiles, then filled ones)."""
    t = Image.open(ROOT / "assets" / "tiles" / theme / "terrain_a.png").convert("RGBA")
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    def tile(mask, variant):
        idx = variant * 256 + mask
        r, c = divmod(idx, 16)
        return t.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32))

    for i, x in enumerate(range(0, w, 32)):
        out.alpha_composite(tile(124, i % 4), (x, floor_y))
        y = floor_y + 32
        while y < h:
            out.alpha_composite(tile(255, (i + y // 32) % 4), (x, y))
            y += 32
    return out


def _hero():
    im = Image.open(ROOT / "assets" / "sprites" / "hero.png").convert("RGBA")
    return im.crop((0, 0, 64, 64)), (32, 60)


def arena(sheet, picks, air=0, theme=None, scale=2, gap=10):
    """picks: frame indices to show; air: how far above the floor the anchor sits (fliers)."""
    theme = theme or THEMES.get(sheet.name, "station")
    fw, fh = sheet.fw, sheet.fh
    ax, ay = sheet.anchor
    hero, (hx, hy) = _hero()
    W = 80 + len(picks) * (fw + gap)
    floor_y = fh + 12 + air - (fh - ay) + 10
    H = floor_y + 56
    bg = _layers(theme, W, H, floor_y)
    bg.alpha_composite(_terrain(theme, W, H, floor_y))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bg.alpha_composite(hero, (30 - hx, floor_y - hy))
    for k, i in enumerate(picks):
        f = sheet.frames[i]
        x = 80 + k * (fw + gap)
        y = floor_y - air - ay
        bg.alpha_composite(Image.fromarray(f.rgba(), "RGBA"), (x, y))
        glow.alpha_composite(Image.fromarray(f.glow_rgba(), "RGBA"), (x, y))
    lit = bg.convert("RGB")
    dark = Image.eval(lit, lambda v: int(v * 0.33))
    g = glow.convert("RGB")
    bloom = g.filter(ImageFilter.GaussianBlur(4))
    dark = Image.fromarray(np.clip(np.asarray(dark, np.int32) + np.asarray(bloom, np.int32) * 1.4, 0, 255)
                           .astype(np.uint8))
    gm = np.asarray(glow)[..., 3] > 0
    da = np.asarray(dark).copy()
    da[gm] = np.asarray(g)[gm]
    dark = Image.fromarray(da)
    out = Image.new("RGB", (W, H * 2), (0, 0, 0))
    out.paste(lit, (0, 0))
    out.paste(dark, (0, H))
    out = out.resize((W * scale, H * 2 * scale), Image.NEAREST)
    WORK.mkdir(parents=True, exist_ok=True)
    out.save(WORK / f"{sheet.name}_arena.png")
