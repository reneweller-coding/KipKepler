"""Helpers for Kip Kepler's procedural pixel-art parallax backgrounds.

A background is four Layer objects painted with palette colours only. The painting model is value banding: a scalar
field (light, depth, density) is cut into a few flat bands, and only the pixels next to a band edge get an ordered
(Bayer) dither. Shapes are wrapped horizontally, so every layer repeats seamlessly.

    from bgkit import Layer, Noise, col, ladder, band
    L = Layer(1280)
    v = Noise(1280, 3, rng, 4)(L.X, L.Y)            # periodic fbm in [0, 1]
    idx, dith = band(v, 4)                         # 4 bands, dither mask at the band edges
    L.paint(v > 0.3, idx, ladder("slate1 slate2 blue2 blue3"), dith)
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from common.palette import OUTLINE, RAMPS, WHITE  # noqa: E402

H = 400  # every layer is 400 px high

# --------------------------------------------------------------------------------------------------------- colours

PAL = np.array([OUTLINE, WHITE] + [c for n in RAMPS for c in RAMPS[n]], dtype=np.uint8)
_PALF = PAL.astype(np.float32)
_WEIGHT = np.array([0.30, 0.59, 0.11], np.float32) * 3


def col(spec):
    """A palette colour from 'steel3', 'outline', 'white' or an RGB tuple (passed through)."""
    if not isinstance(spec, str):
        return tuple(int(v) for v in spec)
    if spec == "outline":
        return OUTLINE
    if spec == "white":
        return WHITE
    return RAMPS[spec[:-1]][int(spec[-1])]


def ladder(specs):
    """A list of colours ('slate1 slate2 blue2' or a list) as an (n, 3) uint8 array, dark to light."""
    if isinstance(specs, str):
        specs = specs.split()
    return np.array([col(s) for s in specs], np.uint8)


def _palette_of(ramps):
    if ramps is None:
        return _PALF
    cols = []
    for r in ramps:
        if r == "outline":
            cols.append(OUTLINE)
        elif r == "white":
            cols.append(WHITE)
        else:
            cols.extend(RAMPS[r])
    return np.array(cols, np.float32)


def nearest(rgb, ramps=None):
    """The nearest palette colour (weighted RGB distance) to one RGB triple, optionally only from some ramps."""
    pal = _palette_of(ramps)
    d = (((pal - np.asarray(rgb, np.float32)[None]) ** 2) * _WEIGHT).sum(-1)
    return tuple(int(v) for v in pal[d.argmin()])


def mix(c1, c2, t, ramps=None):
    """The palette colour nearest to the blend of c1 and c2 (t = 0 gives c1). For atmospheric perspective."""
    a, b = np.array(col(c1), np.float32), np.array(col(c2), np.float32)
    return nearest(a + (b - a) * t, ramps)


def fogged(specs, sky, t, ramps=None):
    """A ladder whose colours are all pulled towards the sky colour by t."""
    if isinstance(specs, str):
        specs = specs.split()
    return np.array([mix(s, sky, t, ramps) for s in specs], np.uint8)


def snap(img):
    """Snaps an (h, w, 3) array to the nearest palette colours (exact matches stay)."""
    flat = img.reshape(-1, 3).astype(np.float32)
    keys, inv = np.unique(flat, axis=0, return_inverse=True)
    d = (((keys[:, None, :] - _PALF[None]) ** 2) * _WEIGHT).sum(-1)
    return PAL[d.argmin(1)][inv.ravel()].reshape(img.shape)


# ----------------------------------------------------------------------------------------------------------- noise

def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def _sample(g, x, y):
    ny, nx = g.shape
    x0 = np.floor(x)
    y0 = np.floor(y)
    sx = _fade(x - x0)
    sy = _fade(y - y0)
    x0 = x0.astype(np.int64) % nx
    y0 = y0.astype(np.int64) % ny
    x1 = (x0 + 1) % nx
    y1 = (y0 + 1) % ny
    a, b, c, d = g[y0, x0], g[y0, x1], g[y1, x0], g[y1, x1]
    return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy


class Noise:
    """Fractal value noise in [0, 1], periodic in x over w px (and in y over about 2048 px).

    cells: lattice cells across w for the first octave (any integer); each further octave doubles them."""

    def __init__(self, w, cells, rng, octaves=4, gain=0.5, lac=2):
        self.w = w
        self.oct = []
        n, amp, total = cells, 1.0, 0.0
        for _ in range(octaves):
            ni = max(1, int(round(n)))
            cell = w / ni
            ny = max(2, int(round(2048 / cell)))
            self.oct.append((rng.random((ny, ni)).astype(np.float32), cell, amp))
            total += amp
            amp *= gain
            n *= lac
        self.total = total

    def __call__(self, X, Y):
        out = 0.0
        for g, cell, amp in self.oct:
            out = out + amp * _sample(g, np.asarray(X, np.float32) / cell, np.asarray(Y, np.float32) / cell)
        return out / self.total


def stretch(v, lo=2, hi=98):
    """Rescales v so its lo..hi percentiles map to 0..1 (clipped)."""
    a, b = np.percentile(v, lo), np.percentile(v, hi)
    return np.clip((v - a) / max(1e-6, b - a), 0, 1)


def ridge(w, rng, cells, octaves=5, gain=0.5):
    """A periodic 1D fbm over w px, stretched to 0..1 (for skylines)."""
    n = Noise(w, cells, rng, octaves, gain)
    x = np.arange(w, dtype=np.float32)
    return stretch(n(x, np.full_like(x, 37.0)), 0, 100)


# --------------------------------------------------------------------------------------------------------- banding

BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16


def bayer(h, w):
    """The 4x4 Bayer thresholds (0..1) tiled over h x w (w must be a multiple of 4 for a seamless wrap)."""
    return np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]


def band(v, n, dw=0.35, edges=None, by=None):
    """Cuts v (0..1) into n flat bands; pixels within dw/2 band widths of an edge get an ordered dither.

    edges: optional n+1 increasing values of v at the band borders (default equal widths).
    Returns (index 0..n-1, mask of the pixels the dither moved)."""
    v = np.asarray(v, np.float32)
    if edges is None:
        x = v * n
    else:
        x = np.interp(v, edges, np.arange(len(edges), dtype=np.float32))
    plain = np.clip(np.floor(x), 0, n - 1).astype(np.int32)
    if dw <= 0:
        return plain, np.zeros(v.shape, bool)
    if by is None:
        by = bayer(*v.shape)
    idx = np.clip(np.floor(x + (by - 0.5) * dw), 0, n - 1).astype(np.int32)
    return idx, idx != plain


def dither_mask(v, by=None):
    """True where v (0..1, a coverage) beats the Bayer threshold: a dithered soft edge for a mask."""
    if by is None:
        by = bayer(*np.shape(v))
    return np.asarray(v) > by


# ----------------------------------------------------------------------------------------------------------- masks

def wdx(X, cx, w):
    """Signed horizontal distance from cx on a ring of width w."""
    return (X - cx + w / 2) % w - w / 2


def shift(m, dx, dy, fill=False):
    """m shifted so that out[y, x] = m[y + dy, x + dx]; wraps in x, pads with fill in y."""
    out = np.roll(m, -dx, axis=1)
    if dy > 0:
        out = np.concatenate([out[dy:], np.full((dy,) + out.shape[1:], fill, out.dtype)], 0)
    elif dy < 0:
        out = np.concatenate([np.full((-dy,) + out.shape[1:], fill, out.dtype), out[:dy]], 0)
    return out


def edge(m, dx, dy):
    """Pixels of mask m whose neighbour at (+dx, +dy) is outside m (the side of m facing that direction)."""
    return m & ~shift(m, dx, dy, False)


def grow(m, r=1):
    """Dilates m by r px (4-neighbourhood steps), wrapping in x."""
    out = m.copy()
    for _ in range(r):
        out = out | shift(out, 1, 0) | shift(out, -1, 0) | shift(out, 0, 1) | shift(out, 0, -1)
    return out


def shrink(m, r=1):
    """Erodes m by r px."""
    return ~grow(~m, r)


class Draw:
    """PIL drawing on a 1-bit mask with horizontal wrap: every shape is drawn at x - w, x and x + w."""

    def __init__(self, w, h=H):
        self.w, self.h = w, h
        self.img = Image.new("L", (w, h), 0)
        self.d = ImageDraw.Draw(self.img)

    def _offs(self):
        return (-self.w, 0, self.w)

    def poly(self, pts, fill=255):
        for o in self._offs():
            self.d.polygon([(x + o, y) for x, y in pts], fill=fill)
        return self

    def rect(self, x0, y0, x1, y1, fill=255):
        for o in self._offs():
            self.d.rectangle([x0 + o, y0, x1 + o, y1], fill=fill)
        return self

    def ellipse(self, x0, y0, x1, y1, fill=255):
        for o in self._offs():
            self.d.ellipse([x0 + o, y0, x1 + o, y1], fill=fill)
        return self

    def line(self, pts, width=1, fill=255):
        for o in self._offs():
            self.d.line([(x + o, y) for x, y in pts], fill=fill, width=width)
        return self

    def mask(self):
        return np.asarray(self.img) > 127


def truss(dr, x0, y0, x1, y1, thick, step=None, chords=True, fill=255, cw=1, bw=1):
    """A lattice girder from (x0, y0) to (x1, y1): two chords thick px apart (cw px wide) and a zigzag of braces
    (bw px wide)."""
    p0, p1 = np.array([x0, y0], float), np.array([x1, y1], float)
    d = p1 - p0
    ln = max(1e-6, np.hypot(*d))
    u = d / ln
    nrm = np.array([-u[1], u[0]]) * thick / 2
    a0, a1, b0, b1 = p0 + nrm, p1 + nrm, p0 - nrm, p1 - nrm
    if chords:
        dr.line([tuple(a0), tuple(a1)], width=cw, fill=fill)
        dr.line([tuple(b0), tuple(b1)], width=cw, fill=fill)
    step = step or max(3, thick)
    n = max(1, int(ln / step))
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        pa = a0 + (a1 - a0) * t0 if i % 2 == 0 else b0 + (b1 - b0) * t0
        pb = b0 + (b1 - b0) * t1 if i % 2 == 0 else a0 + (a1 - a0) * t1
        dr.line([tuple(pa), tuple(pb)], width=bw, fill=fill)


# ----------------------------------------------------------------------------------------------------------- layer

class Layer:
    """One parallax layer: palette RGB, binary alpha, a keep mask (pixels the cleanup must not touch: stars,
    dither, lights) and a glow mask (emissive pixels)."""

    def __init__(self, w, h=H):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), np.uint8)
        self.a = np.zeros((h, w), bool)
        self.keep = np.zeros((h, w), bool)
        self.glow = np.zeros((h, w), bool)
        self.Y, self.X = np.mgrid[0:h, 0:w].astype(np.float32)
        self.by = bayer(h, w)

    def put(self, mask, c, keep=False, glow=False):
        """Paints one colour where mask is set."""
        mask = np.asarray(mask, bool)
        self.rgb[mask] = col(c)
        self.a[mask] = True
        self.keep[mask] = keep
        self.glow[mask] = glow

    def paint(self, mask, idx, lad, dith=None, glow=False):
        """Paints ladder colours lad[idx] where mask is set; dith marks dither pixels (kept by the cleanup)."""
        mask = np.asarray(mask, bool)
        lad = np.asarray(lad, np.uint8) if not isinstance(lad, np.ndarray) else lad
        idx = np.clip(np.broadcast_to(idx, mask.shape), 0, len(lad) - 1)
        self.rgb[mask] = lad[idx[mask]]
        self.a[mask] = True
        self.keep[mask] = False if dith is None else np.broadcast_to(dith, mask.shape)[mask]
        if isinstance(glow, np.ndarray):
            self.glow[mask] = glow[mask]
        else:
            self.glow[mask] = glow

    def shade(self, mask, v, lad, dw=0.35, edges=None, glow=False):
        """Bands the field v (0..1) into the ladder's colours inside mask."""
        idx, dith = band(v, len(lad), dw, edges, self.by)
        self.paint(mask, idx, lad, dith, glow)

    def erase(self, mask):
        mask = np.asarray(mask, bool)
        self.a[mask] = False
        self.keep[mask] = False
        self.glow[mask] = False
        self.rgb[mask] = 0

    def key(self):
        k = (self.rgb[..., 0].astype(np.int32) << 16) | (self.rgb[..., 1].astype(np.int32) << 8) | self.rgb[..., 2]
        return np.where(self.a, k, -1)

    def cleanup(self, passes=2):
        """Removes lone pixels (no 4-neighbour of the same colour / alpha) that are not marked keep, replacing
        each with the most common colour among its 8 neighbours."""
        for _ in range(passes):
            k = self.key()
            nb = [shift(k, dx, dy, -2) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            same = sum((n == k) for n in nb)
            # rows 0 and h-1 compare against padding; treat the outside as the same colour there
            same[0] += 1
            same[-1] += 1
            lone = (same == 0) & ~self.keep
            ys, xs = np.nonzero(lone)
            if len(ys) == 0:
                return
            n8 = []
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
                n8.append(shift(k, dx, dy, -2)[ys, xs])
            n8 = np.stack(n8, 1)
            n8 = np.where(n8 == -2, -3, n8)
            cnt = (n8[:, :, None] == n8[:, None, :]).sum(1)
            cnt = np.where(n8 == -3, -1, cnt)
            pick = n8[np.arange(len(ys)), cnt.argmax(1)]
            opaque = pick >= 0
            self.a[ys, xs] = opaque
            self.rgb[ys, xs, 0] = np.where(opaque, (pick >> 16) & 255, 0)
            self.rgb[ys, xs, 1] = np.where(opaque, (pick >> 8) & 255, 0)
            self.rgb[ys, xs, 2] = np.where(opaque, pick & 255, 0)
            self.glow[ys, xs] = False

    def rgba(self):
        out = np.zeros((self.h, self.w, 4), np.uint8)
        out[..., :3] = np.where(self.a[..., None], self.rgb, 0)
        out[..., 3] = np.where(self.a, 255, 0)
        return out

    def glow_rgba(self):
        g = self.glow & self.a
        out = np.zeros((self.h, self.w, 4), np.uint8)
        out[..., :3] = np.where(g[..., None], self.rgb, 0)
        out[..., 3] = np.where(g, 255, 0)
        return out


# ------------------------------------------------------------------------------------------------------ elements

def bands_at(L, field, first, steps, dpx=4.0, mask=None, glow=False):
    """Flat colour bands along a field (e.g. y): `first` below steps[0], then each (threshold, colour) from its
    threshold on. Within +-dpx (field units) of a threshold the edge is an ordered dither."""
    mask = np.ones(L.a.shape, bool) if mask is None else mask
    f = field + (L.by - 0.5) * 2 * dpx
    plain = np.zeros(L.a.shape, np.int32)
    idx = np.zeros(L.a.shape, np.int32)
    for i, (t, _) in enumerate(steps):
        plain[field >= t] = i + 1
        idx[f >= t] = i + 1
    lad = ladder([first] + [c for _, c in steps])
    L.paint(mask, idx, lad, idx != plain, glow)


def vbands(L, first, steps, dpx=4.0, mask=None, wobble=None):
    """A banded vertical gradient: `first` at the top, then each (y, colour) from that row down, dithered seams.
    wobble: optional per-pixel y offset (array) for wavy band edges."""
    bands_at(L, L.Y if wobble is None else L.Y + wobble, first, steps, dpx, mask)


def stars(L, rng, n, mask=None, y0=3, y1=None, glints=4, tints=("ice", "rose", "yellow", "cyan"), dim="slate",
          bright_frac=0.12):
    """Scatters stars: most single dim pixels, some bright ones, a few with a cross glint. Marked keep and glow."""
    y1 = y1 or L.h
    placed = np.zeros(L.a.shape, bool)
    out = []
    tries = 0
    while len(out) < n and tries < n * 20:
        tries += 1
        x, y = int(rng.integers(0, L.w)), int(rng.integers(y0, y1))
        if mask is not None and not mask[y, x]:
            continue
        ys0, ys1 = max(0, y - 2), min(L.h, y + 3)
        xs = [(x + d) % L.w for d in range(-2, 3)]
        if placed[ys0:ys1][:, xs].any():
            continue
        placed[y, x] = True
        out.append((x, y))
    dimc = [col(dim + "3"), col(dim + "4"), col("steel4")]
    for i, (x, y) in enumerate(out):
        r = rng.random()
        if i < glints:
            _glint(L, x, y, rng.choice(tints), big=i < max(1, glints // 2))
        elif r < bright_frac:
            t = rng.choice(tints)
            L.put(_pt(L, x, y), col(t + str(int(rng.integers(5, 7)))), keep=True, glow=True)
        else:
            L.put(_pt(L, x, y), dimc[int(rng.integers(0, len(dimc)))], keep=True, glow=r < 0.4)
    return out


def _pt(L, x, y):
    m = np.zeros(L.a.shape, bool)
    if 0 <= y < L.h:
        m[y, x % L.w] = True
    return m


def _glint(L, x, y, tint, big=False):
    """A bright star with a cross glint (arms fading outwards) and dim diagonal hints for the big ones."""
    arm = 4 if big else 2
    cols = [col("white"), col(tint + "6"), col(tint + "4"), col(tint + "3"), col("slate3")]
    L.put(_pt(L, x, y), cols[0], keep=True, glow=True)
    for k in range(1, arm + 1):
        c = cols[min(len(cols) - 1, k if big else k + 1)]
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            L.put(_pt(L, x + dx, y + dy), c, keep=True, glow=k <= 2)
    if big:
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            L.put(_pt(L, x + dx, y + dy), cols[3], keep=True, glow=False)


def cloud_field(L, rng, cells=3, octaves=5, warp=40.0, warp_cells=2, stretch_y=1.0):
    """A domain-warped periodic fbm field (0..1) for nebulas, mist and smoke."""
    wn = Noise(L.w, warp_cells, rng, 3)
    wn2 = Noise(L.w, warp_cells, rng, 3)
    f = Noise(L.w, cells, rng, octaves, 0.55)
    X, Y = L.X, L.Y * stretch_y
    qx = (wn(X, Y) - 0.5) * 2 * warp
    qy = (wn2(X, Y) - 0.5) * 2 * warp
    return stretch(f(X + qx, Y + qy), 1, 99)


def sphere(L, cx, cy, r, light=(-0.6, -0.55, 0.58)):
    """Per-pixel sphere data for a disk: (mask, nx, ny, nz, lambert). light is (x right, y down, z to viewer)."""
    dx = wdx(L.X, cx, L.w) / r
    dy = (L.Y - cy) / r
    d2 = dx * dx + dy * dy
    m = d2 <= 1.0
    nz = np.sqrt(np.clip(1 - d2, 0, 1))
    lv = np.array(light, np.float32)
    lv /= np.linalg.norm(lv)
    lam = dx * lv[0] + dy * lv[1] + nz * lv[2]
    return m, dx, dy, nz, lam


def _unit(v):
    v = np.asarray(v, np.float64)
    return v / np.linalg.norm(v)


def planet(L, rng, cx, cy, r, tables, light=(-0.7, -0.45, 0.55), tilt=-0.18, flatten=0.22, band_freq=9.0,
           turb=0.25, rings=None, ring_lad=None, rim=None, night_rim=None, dw=0.45, levels=None, ring_back=True):
    """A banded gas giant (or rocky planet with tables of one row) with optional rings.

    tables: list of ladders (dark to light), one per band type; every ladder has the same length.
    rings: (inner, outer) radii as multiples of r, drawn in the planet's equator plane; ring_lad: their ladder.
    rim: colour of a 1-px lit atmosphere edge outside the lit limb; night_rim: same on the dark limb.
    levels: optional light thresholds for the ladder bands (len + 1 values from 0 to 1)."""
    Lv = _unit(light)
    e1 = np.array([np.cos(tilt), np.sin(tilt), 0.0])
    m = np.array([-np.sin(tilt), np.cos(tilt), 0.0])
    ca = flatten
    sa = np.sqrt(1 - ca * ca)
    e2 = ca * m + sa * np.array([0, 0, 1.0])
    N = np.cross(e1, e2)
    dx = wdx(L.X, cx, L.w).astype(np.float64)
    dy = (L.Y - cy).astype(np.float64)
    d2 = (dx * dx + dy * dy) / (r * r)
    disk = d2 <= 1.0
    zs = np.sqrt(np.clip(1 - d2, 0, 1)) * r
    lat = (dx * N[0] + dy * N[1] + zs * N[2]) / r
    lon = np.arctan2(dx * e2[0] + dy * e2[1] + zs * e2[2], dx * e1[0] + dy * e1[1] + zs * e1[2])
    lam = (dx * Lv[0] + dy * Lv[1] + zs * Lv[2]) / r
    nz = zs / r

    # ring density profile over the radius
    if rings:
        rin, rout = rings
        rr = np.linspace(0, 1, 512)
        prof = Noise(512, 6, rng, 4, 0.6)(rr * 512, np.zeros_like(rr) + 5)
        prof = stretch(prof, 0, 100) * 0.6 + 0.4
        prof *= np.clip(np.minimum(rr / 0.08, (1 - rr) / 0.12), 0, 1)
        gap = np.abs(rr - 0.63) < 0.035
        prof[gap] *= 0.15
        prof[np.abs(rr - 0.25) < 0.015] *= 0.4

        def ring_density(rho):
            t = (rho / r - rin) / (rout - rin)
            ok = (t >= 0) & (t <= 1)
            return np.where(ok, np.interp(np.clip(t, 0, 1), rr, prof), 0.0)

    # planet surface
    tn = Noise(1024, 4, rng, 4, 0.55)
    bn = Noise(1024, 3, rng, 3, 0.5)
    lat_n = bn(np.full_like(lat, 300.0), (lat + 1) * 512 / band_freq * 1.0)
    s = (lat + 1) * band_freq * 0.5 + (lat_n - 0.5) * 2.2 + (tn((lon + np.pi) * 160, (lat + 1) * 420) - 0.5) * turb * 6
    btype = np.floor(s).astype(np.int64) % len(tables)
    # band order: a pseudo-random sequence, so neighbours differ
    seq = rng.permutation(np.arange(64) % len(tables))
    btype = seq[np.floor(s).astype(np.int64) % 64]
    v = np.clip(lam, 0, 1) ** 0.75 * (0.55 + 0.45 * nz ** 0.5)
    v = np.clip(v * 1.1, 0, 0.999)
    if rings:
        tt = -(dx * N[0] + dy * N[1] + zs * N[2]) / np.dot(Lv, N)
        hx, hy, hz = dx + tt * Lv[0], dy + tt * Lv[1], zs + tt * Lv[2]
        rho = np.sqrt(hx * hx + hy * hy + hz * hz)
        shadow = (tt > 0) & (ring_density(rho) > 0.45)
        v = np.where(shadow, v * 0.45, v)
    n = len(tables[0])
    idx, dith = band(v, n, dw, levels, L.by)
    tab = np.array([np.asarray(t, np.uint8) for t in tables])
    rgb = tab[btype, idx]
    L.rgb[disk] = rgb[disk]
    L.a[disk] = True
    L.keep[disk] = dith[disk]
    if rim is not None:
        d = np.sqrt(d2)
        out = (d > 1) & (d <= 1 + 1.6 / r)
        ldir = (dx * Lv[0] + dy * Lv[1]) / np.maximum(1e-6, np.sqrt(dx * dx + dy * dy))
        L.put(out & (ldir > 0.25), rim, keep=True)
        if night_rim is not None:
            L.put(out & (ldir < -0.55), night_rim, keep=True)
    if rings:
        cosa = ca
        a_ = dx * e1[0] + dy * e1[1]
        b_ = (dx * m[0] + dy * m[1]) / cosa
        rho = np.sqrt(a_ * a_ + b_ * b_)
        dens = ring_density(rho)
        z = b_ * sa
        front = z > 0
        vis = (dens > 0.18) & (front | ~disk if ring_back else front)
        # planet shadow on the ring
        Q = np.stack([a_ * e1[0] + b_ * e2[0], a_ * e1[1] + b_ * e2[1], a_ * e1[2] + b_ * e2[2]], -1)
        bq = Q @ Lv
        c = (Q * Q).sum(-1) - r * r
        disc = bq * bq - c
        shad = (disc > 0) & ((-bq - np.sqrt(np.clip(disc, 0, None))) > 0)
        lit = np.where(shad, dens * 0.3, dens)
        n2 = len(ring_lad)
        ridx, rd = band(np.clip(lit, 0, 0.999), n2, 0.4, None, L.by)
        lad2 = np.asarray(ring_lad, np.uint8)
        L.rgb[vis] = lad2[ridx[vis]]
        L.a[vis] = True
        L.keep[vis] = rd[vis]
    return disk


def light_shafts(L, rng, mask, x_centres, width, angle, colour_up, strength_field=None, dw=0.6):
    """Diagonal light shafts: inside each shaft, pixels of mask move one step up their ramp via colour_up
    (a function rgb -> rgb). Shaft edges are dithered."""
    t = np.tan(np.radians(angle))
    cover = np.zeros(L.a.shape, np.float32)
    for cx, wd in zip(x_centres, width):
        d = np.abs(wdx(L.X - L.Y * t, cx, L.w))
        cover = np.maximum(cover, np.clip(1 - d / wd, 0, 1))
    if strength_field is not None:
        cover = cover * strength_field
    hit = mask & dither_mask(np.clip(cover * 1.8 - 0.4, 0, 1), L.by)
    return hit


def recolour(L, mask, mapping):
    """Replaces colours inside mask by a mapping {from rgb: to rgb} (colours not in the mapping stay)."""
    for a, b in mapping.items():
        a, b = col(a), col(b)
        m = mask & L.a & np.all(L.rgb == np.array(a, np.uint8), -1)
        L.rgb[m] = b


def ramp_step(c, k=1):
    """The colour k shades lighter (negative: darker) within its own ramp; OUTLINE/WHITE map to slate."""
    c = tuple(int(v) for v in c)
    for name, r in RAMPS.items():
        if c in r:
            i = r.index(c)
            return r[int(np.clip(i + k, 0, len(r) - 1))]
    if c == OUTLINE:
        return RAMPS["slate"][max(0, k)] if k > 0 else OUTLINE
    return c


def lift(L, mask, k=1):
    """Moves every colour inside mask k shades up its ramp (light shafts, glows, haze)."""
    m = mask & L.a
    if not m.any():
        return
    keys = L.rgb[m]
    uniq, inv = np.unique(keys, axis=0, return_inverse=True)
    new = np.array([ramp_step(tuple(u), k) for u in uniq], np.uint8)
    L.rgb[m] = new[inv.ravel()]


# ----------------------------------------------------------------------------------------------------- output

class Spec:
    """A layer's bg.txt entry."""

    def __init__(self, px, py, yoff=0, scroll=0.0):
        self.px, self.py, self.yoff, self.scroll = px, py, yoff, scroll


def flat_edges(L, top=None, bottom=None, n_top=10, n_bot=10):
    """Makes layer 0's first and last rows one colour (the engine fills beyond them): dithers the n rows next to
    each edge towards that colour (default: the edge row's most common colour)."""
    for row, c, n, sign in ((0, top, n_top, 1), (L.h - 1, bottom, n_bot, -1)):
        k = L.key()[row]
        if c is None:
            vals, cnt = np.unique(k, return_counts=True)
            kk = int(vals[cnt.argmax()])
            c = ((kk >> 16) & 255, (kk >> 8) & 255, kk & 255)
        if (k == k[0]).all() and tuple(L.rgb[row, 0]) == tuple(col(c)):
            continue
        dist = (L.Y - row) * sign
        cover = np.clip(1 - dist / n, 0, 1)
        m = (dist >= 0) & ((cover > L.by) | (dist < 1))
        L.put(m, c, keep=True)


def finish(layers):
    """Cleanup, then checks: palette only, binary alpha, layer 0 opaque with flat first and last rows."""
    flat_edges(layers[0])
    for i, L in enumerate(layers):
        L.cleanup()
        if i == 0:
            assert L.a.all(), "layer 0 must be opaque"
    pal = set(map(tuple, PAL.tolist()))
    for i, L in enumerate(layers):
        used = set(map(tuple, np.unique(L.rgb[L.a].reshape(-1, 3), axis=0).tolist()))
        bad = used - pal
        assert not bad, f"layer {i}: colours outside the palette: {sorted(bad)[:5]}"
        assert 640 <= L.w <= 1280 and L.h == H and L.w % 4 == 0


def edge_rows(L0):
    """Layer 0's top and bottom fill colours (its first and last rows must be flat)."""
    top, bot = L0.rgb[0], L0.rgb[-1]
    assert (top == top[0]).all(), "layer 0 row 0 is not one colour"
    assert (bot == bot[0]).all(), "layer 0 last row is not one colour"
    return tuple(int(v) for v in top[0]), tuple(int(v) for v in bot[0])


def save(name, layers, specs, notes=""):
    """Writes assets/bg/<name>/layer<n>.png (+ layer<n>_glow.png when it has emissive pixels) and bg.txt."""
    out = ROOT / "assets" / "bg" / name
    out.mkdir(parents=True, exist_ok=True)
    for i, L in enumerate(layers):
        Image.fromarray(L.rgba(), "RGBA").save(out / f"layer{i}.png", optimize=True)
        gp = out / f"layer{i}_glow.png"
        if (L.glow & L.a).any():
            Image.fromarray(L.glow_rgba(), "RGBA").save(gp, optimize=True)
        elif gp.exists():
            gp.unlink()
    top, bot = edge_rows(layers[0])
    lines = [
        f"# {name} -- parallax background, made by tools/backgrounds/make_bg.py (do not edit by hand)",
    ]
    for n in notes.strip().splitlines():
        lines.append("# " + n.strip())
    lines += [
        "# layer<n> <parallax x> <parallax y> <y offset> [scroll px/s]",
        "#   screen x of the layer = -camera_x * parallax_x (wrapped, the layer repeats horizontally)",
        "#   screen y of the layer's top row = y offset + rise * parallax_y, where rise = how far the camera's top",
        "#   is above its lowest position in the level (px, >= 0); so at the bottom of a level the layer's top",
        "#   sits at the y offset and climbing moves the layers down",
        "#   scroll: the layer's own drift in px/s (negative = to the left), added to its x",
        "#   above / below a layer the engine repeats its first / last row (clamp to edge); for layer 0 these",
        "#   rows are flat and equal to the fill colours",
        "#   layer<n>_glow.png (when present): the layer's emissive pixels for bloom, same size",
    ]
    for i, s in enumerate(specs):
        sc = f" {s.scroll:g}" if s.scroll else ""
        lines.append(f"layer{i} {s.px:g} {s.py:g} {s.yoff:d}{sc}")
    lines.append("# fill <top r g b> <bottom r g b>: the colours above and below layer 0")
    lines.append(f"fill {top[0]} {top[1]} {top[2]} {bot[0]} {bot[1]} {bot[2]}")
    (out / "bg.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


# ---------------------------------------------------------------------------------------------------- preview

def compose(layers, specs, camx, rise, vw=640, vh=400, t=0.0):
    """The view the engine would draw: layers back to front, x wrapped, y clamped to the edge rows."""
    out = np.zeros((vh, vw, 3), np.uint8)
    for L, s in zip(layers, specs):
        img = L.rgba()
        top = int(round(s.yoff + rise * s.py))
        sy = np.clip(np.arange(vh) - top, 0, L.h - 1)
        sx = (np.arange(vw) + int(round(camx * s.px - s.scroll * t))) % L.w
        src = img[sy][:, sx]
        a = src[..., 3:] > 0
        out = np.where(a, src[..., :3], out)
    return out


def fake_tiles(view):
    """Draws a few gameplay-like tiles (teal ground, orange and blue platforms) to judge contrast."""
    v = view.copy()
    def tile(x, y, base):
        r = RAMPS[base]
        v[y:y + 32, x:x + 32] = r[3]
        v[y + 4:y + 32, x:x + 32] = r[2]
        v[y:y + 2, x:x + 32] = r[5]
        v[y + 2:y + 4, x:x + 32] = r[4]
        v[y + 30:y + 32, x:x + 32] = r[1]
        v[y:y + 32, x + 31:x + 32] = r[1]
        v[y + 10:y + 12, x + 8:x + 14] = r[4]
    for x in range(0, 640, 32):
        tile(x, 336, "teal")
        tile(x, 368, "teal")
    for x in range(96, 224, 32):
        tile(x, 240, "orange")
    for x in range(384, 544, 32):
        tile(x, 176, "blue")
    for x in range(544, 640, 32):
        tile(x, 272, "green")
    # the hero's box, roughly
    v[292:336, 300:320] = RAMPS["orange"][4]
    v[292:300, 300:320] = RAMPS["skin"][5]
    return v


def preview(name, layers, specs, cams=((0, 0), (1700, 0), (3300, 420)), crop=(150, 60)):
    """work/bg/<name>_preview.png: three composited views (the second with fake tiles over it) and a 2x crop."""
    gap = 4
    views = [compose(layers, specs, cx, rs) for cx, rs in cams]
    views[1] = fake_tiles(views[1])
    cx, cy = crop
    c = views[0][cy:cy + 200, cx:cx + 320]
    c2 = np.repeat(np.repeat(c, 2, 0), 2, 1)
    rows = views + [c2]
    tot = sum(r.shape[0] for r in rows) + gap * (len(rows) - 1)
    out = np.full((tot, 640, 3), 40, np.uint8)
    y = 0
    for r in rows:
        out[y:y + r.shape[0], :r.shape[1]] = r
        y += r.shape[0] + gap
    p = ROOT / "work" / "bg" / f"{name}_preview.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out).save(p)
    return p


def seams(name, layers, half=160):
    """work/bg/<name>_seams.png: each layer tiled twice, cropped around the wrap point, over a checkerboard."""
    rows = []
    for L in layers:
        img = L.rgba()
        two = np.concatenate([img, img], 1)[:, L.w - half:L.w + half]
        bg = np.full(two.shape[:2] + (3,), 70, np.uint8)
        yy, xx = np.mgrid[0:two.shape[0], 0:two.shape[1]]
        bg[((yy // 8 + xx // 8) % 2) == 0] = 100
        rows.append(np.where(two[..., 3:] > 0, two[..., :3], bg))
    out = np.concatenate(rows, 1)
    out[:, [half + i * 2 * half for i in range(len(layers))], :] = (255, 0, 255)
    p = ROOT / "work" / "bg" / f"{name}_seams.png"
    Image.fromarray(out).save(p)
    return p


def layers_sheet(name, layers):
    """work/bg/<name>_layers.png: every layer alone (layer 0 at the top) over a checkerboard, for inspection."""
    rows = []
    W = max(L.w for L in layers)
    for L in layers:
        img = L.rgba()
        bg = np.full((L.h, W, 3), 70, np.uint8)
        yy, xx = np.mgrid[0:L.h, 0:W]
        bg[((yy // 8 + xx // 8) % 2) == 0] = 100
        bg[:, :L.w] = np.where(img[..., 3:] > 0, img[..., :3], bg[:, :L.w])
        rows.append(bg)
        rows.append(np.full((4, W, 3), 255, np.uint8))
    p = ROOT / "work" / "bg" / f"{name}_layers.png"
    Image.fromarray(np.concatenate(rows, 0)).save(p)
    return p


def swoosh(L, rng, y0, amp, width, harmonics=2, wvar=0.45):
    """A soft band (0..1) along a periodic wavy centre line: the envelope of a nebula, a mist bank or a galaxy arm."""
    t = 2 * np.pi * L.X / L.w
    yc = np.full(L.X.shape, float(y0), np.float32)
    wd = np.full(L.X.shape, float(width), np.float32)
    for k in range(1, harmonics + 1):
        yc += amp / k * np.sin(k * t + rng.uniform(0, 2 * np.pi))
        wd *= 1 + wvar / k * np.sin(k * t + rng.uniform(0, 2 * np.pi))
    d = (L.Y - yc) / np.maximum(4, wd)
    return np.exp(-d * d)


def gas_field(L, rng, cells=3, warp=300.0, gain=0.58, octaves=7, streak=0.25, sy=1.6):
    """A wispy gas density (0..1): a rough fbm, strongly domain-warped, mixed with horizontal streaks."""
    wx, wy = Noise(L.w, cells, rng, 5, 0.55), Noise(L.w, cells, rng, 5, 0.55)
    f = Noise(L.w, cells * 2, rng, octaves, gain)
    sc = max(1, int(round(cells * 2 * 0.35)))                  # streaks: fewer cells across, sampled at X (wraps)
    s = Noise(L.w, sc, rng, 5, 0.6)
    X, Y = L.X, L.Y * sy
    qx, qy = (wx(X, Y) - 0.5) * warp, (wy(X, Y) - 0.5) * warp
    base = stretch(f(X + qx, Y + qy), 1, 99.5)
    ky = 2.5 * (cells * 2) / sc
    st = stretch(s(X + qx * 2.5, Y * ky + qy * 2 * ky / 2.5), 1, 99.5)
    return np.clip(base * (1 - streak) + st * streak, 0, 1)


def levels(L, v, cols, thresholds, dpx=0.05, mask=None, glow_from=None):
    """Paints the levels of a field: cols[i] where v >= thresholds[i] (the highest wins), dithered within dpx of
    each threshold. Below thresholds[0] nothing is painted. glow_from: index from which the levels glow."""
    f2 = v + (L.by - 0.5) * 2 * dpx
    idx = np.full(L.a.shape, -1, np.int32)
    plain = np.full(L.a.shape, -1, np.int32)
    for i, t in enumerate(thresholds):
        idx[f2 >= t] = i
        plain[v >= t] = i
    m = idx >= 0
    if mask is not None:
        m &= mask
    glow = False if glow_from is None else (idx >= glow_from)
    L.paint(m, np.maximum(idx, 0), ladder(cols), idx != plain, glow)
    return idx


def nebula(L, rng, cols, envelope, thresholds=None, gamma=1.8, dpx=0.05, mask=None, **field):
    """A quantized wispy gas cloud painted over L: cols from the faintest to the brightest, envelope (0..1) shapes
    where it lives. field: gas_field parameters. Returns the density."""
    v = stretch(envelope ** 0.8 * gas_field(L, rng, **field) ** gamma, 0, 99.9)
    thresholds = thresholds or list(np.linspace(0.12, 0.8, len(cols)))
    levels(L, v, cols, thresholds, dpx, mask)
    return v


def sun(L, cx, cy, radii, cols, spikes=(90, 50), spike_cols=None, diag=18):
    """A bright sun: concentric banded discs (radii inner to outer with cols, dithered edges) and diffraction
    spikes (horizontal / vertical lengths). Everything is kept and the inner part glows."""
    d = np.sqrt(wdx(L.X, cx, L.w) ** 2 + (L.Y - cy) ** 2)
    for i in range(len(radii) - 1, -1, -1):
        r = radii[i]
        cover = np.clip((r + 1.5 - d) / 3.0, 0, 1)
        m = dither_mask(cover, L.by) if i > 0 else d <= r
        L.put(m, cols[i], keep=True, glow=i <= 2)
    spike_cols = spike_cols or cols
    for (dx, dy), ln in (((1, 0), spikes[0]), ((0, 1), spikes[1]), ((1, 1), diag), ((1, -1), diag)):
        for s in (-1, 1):
            for k in range(radii[0] + 1, ln):
                t = k / ln
                ci = min(len(spike_cols) - 1, int(t * len(spike_cols)))
                if t > 0.55 and k % 2 == 1:
                    continue
                x, y = int(round(cx + s * dx * k)), int(round(cy + s * dy * k))
                if 0 <= y < L.h:
                    L.put(_onept(L, x, y), spike_cols[ci], keep=True, glow=t < 0.4)
                if k < ln * 0.25 and dx * dy == 0:
                    for o in (-1, 1):
                        x2, y2 = x + o * dy, y + o * dx
                        if 0 <= y2 < L.h:
                            L.put(_onept(L, x2, y2), spike_cols[min(len(spike_cols) - 1, ci + 2)], keep=True)


def _onept(L, x, y):
    m = np.zeros(L.a.shape, bool)
    m[int(y), int(x) % L.w] = True
    return m


def ring_outline(L, cx, cy, r, c, gap_every=0):
    """A 1-px circle (a lens flare ghost)."""
    d = np.sqrt(wdx(L.X, cx, L.w) ** 2 + (L.Y - cy) ** 2)
    m = np.abs(d - r) < 0.55
    if gap_every:
        ang = np.arctan2(L.Y - cy, wdx(L.X, cx, L.w))
        m &= (np.floor((ang + np.pi) / (2 * np.pi) * gap_every * 2) % 2) == 0
    L.put(m, c, keep=True)
    return m
