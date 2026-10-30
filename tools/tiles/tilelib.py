"""Building blocks of the Kip Kepler tile generator.

Everything here works on small numpy canvases (a `Tile`: RGB, binary alpha, emissive flag per pixel) and only ever
writes colours taken from the shared palette (tools/common/palette.py): ramp shades, OUTLINE and WHITE.

The autotile machinery (`geom`) turns an 8-bit neighbour mask (bit 0 N, 1 NE, 2 E, 3 SE, 4 S, 5 SW, 6 W, 7 NW) into
per-pixel fields of a 32 x 32 tile: is the pixel solid, how deep is it below the nearest exposed surface, which way
does that surface face. The theme painters turn those fields into material: lips on top, bevels on the sides,
shadowed undersides, rounded or chamfered outer corners, notches in inner corners. Because every field only depends
on the 3 x 3 cells around a tile, neighbouring tiles agree along their shared border, and the interior textures are
32-periodic and blended to a common border band, so any variant fits next to any other.
"""
import os
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common.palette import OUTLINE, RAMPS, WHITE, palette  # noqa: E402

T = 32
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

# neighbour bits
N, NE, E, SE, S, SW, W, NW = (1 << i for i in range(8))
DIRS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

LIGHT = np.array([-0.55, -0.83])  # towards the light: top left, mostly top

_B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32)
BAYER = (np.tile(_B4, (16, 16)) + 0.5) / 16.0  # 64 x 64, values in (0, 1)

YY, XX = np.mgrid[0:T, 0:T]
BORDER = np.minimum(np.minimum(XX, T - 1 - XX), np.minimum(YY, T - 1 - YY)).astype(np.float32)


def C(name, i):
    """One palette colour: ramp shade, or 'outline' / 'white'."""
    if name == "outline":
        return OUTLINE
    if name == "white":
        return WHITE
    return RAMPS[name][i]


def mix_ramp(*items):
    """A material ramp made of palette colours, e.g. mix_ramp(('slate', 0), ('steel', 1), ...)."""
    return [C(n, i) for n, i in items]


def bayer(h, w, ox=0, oy=0):
    b = np.tile(_B4, (h // 4 + 2, w // 4 + 2))
    return (b[oy % 4: oy % 4 + h, ox % 4: ox % 4 + w] + 0.5) / 16.0


def qidx(val, n, dither=0.0, ox=0, oy=0):
    """Float shade values (0 .. n-1) to integer indices, with optional ordered dithering of the given strength."""
    h, w = val.shape
    if dither > 0:
        val = val + (bayer(h, w, ox, oy) - 0.5) * dither
    return np.clip(np.floor(val + 0.5), 0, n - 1).astype(np.int32)


# --------------------------------------------------------------------------------------------------------- canvas


class Tile:
    """A small RGBA canvas with an emissive flag per pixel. Alpha is binary."""

    def __init__(self, w=T, h=T):
        self.w, self.h = w, h
        self.c = np.zeros((h, w, 3), np.uint8)
        self.a = np.zeros((h, w), bool)
        self.g = np.zeros((h, w), bool)

    def fill(self, m, col, glow=False):
        m = np.asarray(m, bool)
        self.c[m] = col
        self.a[m] = True
        self.g[m] = glow

    def fill_idx(self, m, cols, idx, glow=False):
        """Paints pixels of mask m with cols[idx] (idx an int array of the canvas shape or a scalar)."""
        m = np.asarray(m, bool)
        lut = np.array(cols, np.uint8)
        idx = np.broadcast_to(np.asarray(idx), m.shape)
        self.c[m] = lut[np.clip(idx[m], 0, len(cols) - 1)]
        self.a[m] = True
        if isinstance(glow, np.ndarray):
            self.g[m] = glow[m]
        else:
            self.g[m] = glow

    def px(self, x, y, col, glow=False):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.c[y, x] = col
            self.a[y, x] = True
            self.g[y, x] = glow

    def rect(self, x0, y0, x1, y1, col, glow=False, clip=None):
        """Filled rectangle, inclusive corners. clip: optional bool mask that limits painting."""
        m = np.zeros((self.h, self.w), bool)
        m[max(0, y0): max(0, y1 + 1), max(0, x0): max(0, x1 + 1)] = True
        if clip is not None:
            m &= clip
        self.fill(m, col, glow)

    def clear(self, m):
        m = np.asarray(m, bool)
        self.a[m] = False
        self.g[m] = False

    def copy(self):
        t = Tile(self.w, self.h)
        t.c[:] = self.c
        t.a[:] = self.a
        t.g[:] = self.g
        return t

    def blit(self, other, x, y):
        """Draws other (opaque pixels only) at x, y."""
        h, w = other.h, other.w
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        sub = other.a[y0 - y: y1 - y, x0 - x: x1 - x]
        self.c[y0:y1, x0:x1][sub] = other.c[y0 - y: y1 - y, x0 - x: x1 - x][sub]
        self.a[y0:y1, x0:x1][sub] = True
        self.g[y0:y1, x0:x1][sub] = other.g[y0 - y: y1 - y, x0 - x: x1 - x][sub]

    def rgba(self):
        out = np.zeros((self.h, self.w, 4), np.uint8)
        out[..., :3] = self.c
        out[..., 3] = np.where(self.a, 255, 0)
        out[~self.a, :3] = 0
        return out

    def glow_rgba(self):
        out = np.zeros((self.h, self.w, 4), np.uint8)
        m = self.g & self.a
        out[m, :3] = self.c[m]
        out[m, 3] = 255
        return out


# ---------------------------------------------------------------------------------------------------------- noise


def periodic_noise(rng, size=T, sx=6.0, sy=6.0, h=None):
    """Smooth noise that tiles with period `size` (FFT-filtered white noise), normalised to std 1. sx, sy: feature
    size in pixels along x and y (anisotropic for brushed metal or strata)."""
    hh = h or size
    wn = rng.standard_normal((hh, size))
    f = np.fft.fft2(wn)
    ky = np.fft.fftfreq(hh)[:, None]
    kx = np.fft.fftfreq(size)[None, :]
    filt = np.exp(-((kx * sx) ** 2 + (ky * sy) ** 2) * 2.0)
    n = np.real(np.fft.ifft2(f * filt))
    n -= n.mean()
    s = n.std()
    return (n / s if s > 0 else n).astype(np.float32)


def noise_1d(rng, n=T, smooth=4.0, periodic=True):
    w = rng.standard_normal(n)
    if periodic:
        f = np.fft.fft(w)
        k = np.fft.fftfreq(n)
        v = np.real(np.fft.ifft(f * np.exp(-(k * smooth) ** 2 * 2.0)))
    else:
        v = ndimage.gaussian_filter1d(w, smooth / 2, mode="nearest")
    v -= v.mean()
    s = v.std()
    return v / s if s > 0 else v


def seamless_variants(rng, nvar=4, sx=6.0, sy=6.0, band=(2.0, 9.0), common_amp=1.0):
    """nvar 32-periodic noise fields that agree with each other near the tile border (all blend to one common field
    there), so any variant fits next to any other without a seam."""
    common = periodic_noise(rng, T, sx, sy) * common_amp
    w = np.clip((BORDER - band[0]) / (band[1] - band[0]), 0, 1)
    w = w * w * (3 - 2 * w)
    out = []
    for _ in range(nvar):
        v = periodic_noise(rng, T, sx, sy)
        out.append(common * (1 - w) + v * w)
    return out


def edge_profile(rng, amp, smooth=3.0, pin=0.0, ramp_px=4.0):
    """A 32-long edge displacement profile in [0, amp], pinned to `pin` at both ends (so neighbouring tiles meet)."""
    v = noise_1d(rng, T, smooth, periodic=False)
    v = (v - v.min()) / max(1e-6, v.max() - v.min()) * amp
    x = np.arange(T)
    env = np.clip(np.minimum(x, T - 1 - x) / ramp_px, 0, 1)
    env = env * env * (3 - 2 * env)
    return pin * (1 - env) + v * env


# ------------------------------------------------------------------------------------------------------- geometry


def window(mask):
    w = np.zeros((96, 96), bool)
    w[32:64, 32:64] = True
    for i, (dx, dy) in enumerate(DIRS):
        if mask & (1 << i):
            w[32 + dy * 32: 64 + dy * 32, 32 + dx * 32: 64 + dx * 32] = True
    return w


def struct_el(r, kind):
    yy, xx = np.mgrid[-r: r + 1, -r: r + 1]
    if kind == "chamfer":
        return (np.abs(xx) + np.abs(yy)) <= r
    if kind == "square":
        return np.ones_like(xx, bool)
    return (xx * xx + yy * yy) <= r * r + r * 0.6


class Geom:
    """Per-pixel fields of one autotile mask (32 x 32 arrays)."""

    pass


@lru_cache(maxsize=None)
def geom(mask, r=3, kind="round"):
    w = window(mask)
    P = 16
    wp = np.pad(w, P, mode="edge")
    if r > 0:
        wp = ndimage.binary_opening(wp, structure=struct_el(r, kind))
    sl = (slice(P + 32, P + 64), slice(P + 32, P + 64))
    g = Geom()
    g.mask = mask
    g.solid = wp[sl].copy()
    if wp.all():
        g.depth = np.full((T, T), 99.0, np.float32)
        g.nx = np.zeros((T, T), np.float32)
        g.ny = np.zeros((T, T), np.float32)
    else:
        d, ind = ndimage.distance_transform_edt(wp, return_indices=True)
        oy, ox = np.mgrid[0: wp.shape[0], 0: wp.shape[1]]
        vx = (ind[1] - ox).astype(np.float32)
        vy = (ind[0] - oy).astype(np.float32)
        ln = np.maximum(np.hypot(vx, vy), 1e-6)
        nxw = ndimage.gaussian_filter(vx / ln, 0.8)
        nyw = ndimage.gaussian_filter(vy / ln, 0.8)
        ln = np.maximum(np.hypot(nxw, nyw), 1e-6)
        g.depth = (d[sl] - 1.0).astype(np.float32)
        g.nx = (nxw / ln)[sl]
        g.ny = (nyw / ln)[sl]
        g.depth[~g.solid] = -1
    g.depth = np.minimum(g.depth, 99.0)
    g.wt = np.clip((-g.ny - 0.35) / 0.5, 0, 1)
    g.wb = np.clip((g.ny - 0.35) / 0.5, 0, 1)
    g.wl = np.clip((-g.nx - 0.35) / 0.5, 0, 1)
    g.wr = np.clip((g.nx - 0.35) / 0.5, 0, 1)
    g.lit = g.nx * LIGHT[0] + g.ny * LIGHT[1]
    g.top = not (mask & N)
    g.bottom = not (mask & S)
    g.left = not (mask & W)
    g.right = not (mask & E)
    return g


class Shape:
    """Geometry after edge displacement: solid, depth, facing, light (copies; the cached Geom stays untouched)."""

    pass


def displaced(g, prof=None, carve_at=-0.35):
    """Applies per-side displacement profiles (dict with 't', 'b', 'l', 'r' -> 32 floats, carved inwards)."""
    s = Shape()
    s.mask = g.mask
    s.nx, s.ny, s.lit = g.nx, g.ny, g.lit
    s.wt, s.wb, s.wl, s.wr = g.wt, g.wb, g.wl, g.wr
    s.top, s.bottom, s.left, s.right = g.top, g.bottom, g.left, g.right
    if prof is None:
        s.depth = g.depth.copy()
        s.solid = g.solid.copy()
        s.disp = np.zeros((T, T), np.float32)
        return s
    wsum = g.wt + g.wb + g.wl + g.wr
    disp = (g.wt * prof["t"][None, :] + g.wb * prof["b"][None, :] + g.wl * prof["l"][:, None]
            + g.wr * prof["r"][:, None]) / np.maximum(wsum, 1e-3)
    disp = np.where(wsum > 1e-3, disp, 0)
    s.disp = disp
    s.depth = g.depth - disp
    s.solid = g.solid & (s.depth > carve_at)
    return s


# -------------------------------------------------------------------------------------------------- drawing helpers


def shape_mask(w, h, draw_fn):
    """A bool mask drawn with PIL: draw_fn(ImageDraw) paints with fill=1."""
    im = Image.new("L", (w, h), 0)
    draw_fn(ImageDraw.Draw(im))
    return np.asarray(im) > 0


def inner_depth(m):
    """Distance of each pixel of mask m to the outside of m (1 at the border pixels)."""
    return ndimage.distance_transform_edt(np.pad(m, 1))[1:-1, 1:-1]


def edge_dir(m):
    """For each pixel of m: unit vector to the nearest pixel outside m."""
    mp = np.pad(m, 1)
    d, ind = ndimage.distance_transform_edt(mp, return_indices=True)
    oy, ox = np.mgrid[0: mp.shape[0], 0: mp.shape[1]]
    vx = (ind[1] - ox).astype(np.float32)
    vy = (ind[0] - oy).astype(np.float32)
    ln = np.maximum(np.hypot(vx, vy), 1e-6)
    return (vx / ln)[1:-1, 1:-1], (vy / ln)[1:-1, 1:-1], d[1:-1, 1:-1]


def shade_form(t, m, cols, base, spread=1.6, rim=True, outline=None, glow=False, round_=True, dither=0.0, ox=0,
               oy=0):
    """Paints mask m as a lit form from top left: base shade index in cols, brighter towards top/left edges, darker
    towards bottom/right. round_: pillow shading over the whole shape, else flat face with a bevel ring."""
    if not m.any():
        return
    nx, ny, d = edge_dir(m)
    lit = nx * LIGHT[0] + ny * LIGHT[1]
    if round_:
        h = ndimage.gaussian_filter(m.astype(np.float32), 1.6)
        gy, gx = np.gradient(h)
        ln = np.maximum(np.hypot(gx, gy), 1e-6)
        l2 = -(gx / ln * LIGHT[0] + gy / ln * LIGHT[1])
        fall = np.clip(1.0 - (d - 1) / 6.0, 0, 1)
        val = base + spread * l2 * fall * 0.9 + spread * 0.25 * np.clip(d - 3, 0, 4) / 4 * 0
    else:
        ring = np.clip(2.0 - d, 0, 1)
        val = base + spread * lit * ring
    if rim:
        val = np.where(d < 1.5, val + np.where(lit > 0.2, 0.6, np.where(lit < -0.2, -0.6, 0)), val)
    idx = qidx(val, len(cols), dither, ox, oy)
    t.fill_idx(m, cols, idx, glow)
    if outline is not None:
        ring = m & ~ndimage.binary_erosion(m)
        t.fill(ring, outline, False)


def outline_shape(t, m, col):
    """A 1 px outline just outside mask m (4-connected)."""
    o = ndimage.binary_dilation(m, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)) & ~m
    t.fill(o, col)


def line_mask(w, h, pts, width=1):
    return shape_mask(w, h, lambda d: d.line(pts, fill=1, width=width))


def rivet(t, x, y, cols, clip=None, size=2):
    """A rivet head at x, y (top-left pixel). cols: (shadow, base, highlight)."""
    sh, base, hi = cols
    pts = []
    if size == 2:
        pts = [(x, y, hi), (x + 1, y, base), (x, y + 1, base), (x + 1, y + 1, sh), (x + 2, y + 1, sh), (x + 1, y + 2, sh)]
        pts = [(x, y, hi), (x + 1, y, base), (x, y + 1, base), (x + 1, y + 1, sh)]
    else:
        pts = [(x + 1, y, hi), (x, y + 1, hi), (x + 1, y + 1, base), (x + 2, y + 1, base), (x + 1, y + 2, base),
               (x + 2, y + 2, sh), (x + 2, y, base), (x, y + 2, base)]
    for px_, py_, c in pts:
        if 0 <= px_ < t.w and 0 <= py_ < t.h and (clip is None or clip[py_, px_]):
            t.px(px_, py_, c)


def bevel_rect(t, x0, y0, x1, y1, face, hi, sh, clip=None, glow=False):
    t.rect(x0, y0, x1, y1, face, glow, clip)
    t.rect(x0, y0, x1, y0, hi, glow, clip)
    t.rect(x0, y0, x0, y1, hi, glow, clip)
    t.rect(x0, y1, x1, y1, sh, glow, clip)
    t.rect(x1, y0, x1, y1, sh, glow, clip)


def inset_rect(t, x0, y0, x1, y1, face, sh, hi, clip=None, glow=False):
    """A recessed rectangle: shadow on top/left, highlight on bottom/right."""
    t.rect(x0, y0, x1, y1, face, glow, clip)
    t.rect(x0, y0, x1, y0, sh, False, clip)
    t.rect(x0, y0, x0, y1, sh, False, clip)
    t.rect(x0 + 1, y1, x1, y1, hi, False, clip)
    t.rect(x1, y0 + 1, x1, y1, hi, False, clip)


def hazard(t, m, c1, c2, period=6, ox=0, oy=0, slope=1):
    """Diagonal stripes in mask m."""
    s = ((XX[: t.h, : t.w] + ox) + slope * (YY[: t.h, : t.w] + oy)) % period
    t.fill(m & (s < period // 2), c1)
    t.fill(m & (s >= period // 2), c2)


def facing(g):
    """Dominant facing per pixel: 0 top, 1 bottom, 2 left, 3 right (ties go to top/bottom)."""
    w = np.stack([g.wt + 1e-3, g.wb + 1e-3, g.wl, g.wr])
    return w.argmax(0)


def edge_bands(t, g, depth, specs, region=None, glow=None):
    """Paints the bands along exposed edges: specs = {'t': [colour at depth 0, depth 1, ...], 'b': ..., 'l': ...,
    'r': ...}; a None entry leaves that pixel alone. depth: float depth field (often scaled per facing)."""
    f = facing(g)
    di = np.floor(depth).astype(int)
    sol = g.solid if region is None else region
    for fi, key in enumerate("tblr"):
        spec = specs.get(key)
        if not spec:
            continue
        for i, col in enumerate(spec):
            if col is None:
                continue
            m = sol & (f == fi) & (di == i)
            gl = bool(glow and glow.get(key) and i in glow[key])
            t.fill(m, col, gl)


def despeckle(idx, m, passes=1):
    """Replaces isolated single pixels of an index map (inside mask m) with the majority of their 4 neighbours."""
    for _ in range(passes):
        p = np.pad(idx, 1, mode="edge")
        nb = np.stack([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]])
        same = (nb == idx[None]).sum(0)
        med = np.median(nb, axis=0).astype(idx.dtype)
        idx = np.where(m & (same == 0), med, idx)
    return idx


# ---------------------------------------------------------------------------------------------------- sheets / io


def autotile_sheet(paint, nvar=4, cols=16):
    """Builds a 16 x 64 sheet: paint(mask, variant) -> Tile. Index = variant * 256 + mask."""
    rows = nvar * 256 // cols
    sheet = Tile(cols * T, rows * T)
    for v in range(nvar):
        for m in range(256):
            i = v * 256 + m
            tile = paint(m, v)
            x, y = (i % cols) * T, (i // cols) * T
            sheet.c[y: y + T, x: x + T] = tile.c
            sheet.a[y: y + T, x: x + T] = tile.a
            sheet.g[y: y + T, x: x + T] = tile.g
    return sheet


def grid_sheet(tiles, cols, tw=T, th=T):
    """tiles: list of rows (lists of Tile)."""
    rows = len(tiles)
    sheet = Tile(cols * tw, rows * th)
    for r, row in enumerate(tiles):
        for c, tile in enumerate(row):
            sheet.blit(tile, c * tw, r * th)
    return sheet


_PAL = None


def check_palette(arr):
    """Raises if any opaque pixel is not a palette colour or alpha is not binary."""
    global _PAL
    if _PAL is None:
        _PAL = {tuple(int(v) for v in c) for c in palette()}
    a = arr[..., 3]
    if not np.isin(a, (0, 255)).all():
        raise ValueError("alpha not binary")
    cols = {tuple(int(v) for v in c) for c in arr[a == 255][:, :3].reshape(-1, 3)}
    bad = cols - _PAL
    if bad:
        raise ValueError("colours outside the palette: %s" % sorted(bad)[:8])


def save_sheet(sheet, path, glow=True):
    """Writes path (+ path_glow.png when the sheet has emissive pixels). Returns True when a glow file was written."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rgba = sheet.rgba()
    check_palette(rgba)
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)
    gpath = path[:-4] + "_glow.png"
    if glow and (sheet.g & sheet.a).any():
        Image.fromarray(sheet.glow_rgba(), "RGBA").save(gpath, optimize=True)
        return True
    if os.path.exists(gpath):
        os.remove(gpath)
    return False


def pack_atlas(items, width=512):
    """Shelf-packs deco sprites. items: list of (name, Tile, place, weight, glow). Returns (sheet, lines)."""
    order = sorted(range(len(items)), key=lambda i: (-items[i][1].h, -items[i][1].w))
    x = y = shelf = 0
    pos = {}
    for i in order:
        tl = items[i][1]
        w, h = tl.w + 2, tl.h + 2
        if x + w > width:
            x, y, shelf = 0, y + shelf, 0
        pos[i] = (x + 1, y + 1)
        x += w
        shelf = max(shelf, h)
    height = y + shelf
    height = (height + 31) // 32 * 32
    sheet = Tile(width, height)
    lines = []
    for i, (name, tl, place, weight, glow) in enumerate(items):
        px_, py_ = pos[i]
        sheet.blit(tl, px_, py_)
        lines.append("%s %d %d %d %d %s %g%s" % (name, px_, py_, tl.w, tl.h, place, weight, " glow" if glow else ""))
    return sheet, lines
