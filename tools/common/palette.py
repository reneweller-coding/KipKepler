"""The shared palette of Kip Kepler.

Every generator picks its colours from these ramps so sprites, tiles and backgrounds belong together. A ramp runs
from the darkest shade (index 0) to the lightest; shadows lean towards blue-violet, highlights towards warm yellow
(hue shifting), the saturation peaks in the middle.

    from common.palette import ramp, RAMPS, OUTLINE, quantize
    steel = ramp("steel")        # 8 RGB tuples, dark to light
    img = quantize(img, ["steel", "orange", "cyan"])   # snap a PIL RGBA image to those ramps
"""
import colorsys

import numpy as np
from PIL import Image

SHADES = 8

# name: (hue degrees, saturation 0-1 at the middle, lightness range lo-hi)
_BASE = {
    "grey":    (230, 0.06, 0.06, 0.94),
    "steel":   (212, 0.20, 0.07, 0.90),
    "slate":   (235, 0.28, 0.06, 0.82),
    "blue":    (218, 0.72, 0.07, 0.86),
    "cyan":    (190, 0.80, 0.07, 0.90),
    "teal":    (168, 0.62, 0.06, 0.84),
    "green":   (128, 0.58, 0.06, 0.84),
    "lime":    (86,  0.72, 0.08, 0.90),
    "olive":   (62,  0.42, 0.06, 0.82),
    "yellow":  (48,  0.88, 0.10, 0.93),
    "orange":  (26,  0.88, 0.08, 0.88),
    "red":     (4,   0.78, 0.07, 0.84),
    "crimson": (346, 0.70, 0.06, 0.82),
    "magenta": (312, 0.68, 0.07, 0.86),
    "purple":  (276, 0.58, 0.06, 0.84),
    "violet":  (252, 0.62, 0.07, 0.86),
    "brown":   (24,  0.42, 0.06, 0.78),
    "tan":     (34,  0.38, 0.10, 0.88),
    "skin":    (22,  0.52, 0.12, 0.90),
    "rose":    (352, 0.42, 0.10, 0.90),
    "ice":     (200, 0.45, 0.10, 0.96),
}

OUTLINE = (17, 13, 30)
WHITE = (250, 250, 255)


def _hue_shift(h, t):
    """Shadows lean towards 250 deg (blue-violet), highlights towards 55 deg (warm yellow)."""
    def towards(h, target, amount):
        d = ((target - h + 540) % 360) - 180
        return (h + d * amount) % 360
    if t < 0.5:
        return towards(h, 250, (0.5 - t) * 0.5)
    return towards(h, 55, (t - 0.5) * 0.35)


def ramp(name, n=SHADES):
    """The ramp's n shades, dark to light, as RGB tuples."""
    h, s, lo, hi = _BASE[name]
    out = []
    for i in range(n):
        t = i / (n - 1)
        hh = _hue_shift(h, t)
        light = lo + (hi - lo) * t
        sat = s * (0.55 + 0.45 * max(0.0, 1 - abs(t - 0.55) * 2) ** 0.7) if s > 0.1 else s
        r, g, b = colorsys.hls_to_rgb(hh / 360.0, light, min(1.0, sat))
        out.append((int(round(r * 255)), int(round(g * 255)), int(round(b * 255))))
    return out


RAMPS = {name: ramp(name) for name in _BASE}


def palette(names=None):
    """All colours of the named ramps (all ramps when None) plus OUTLINE and WHITE, as an (N, 3) uint8 array."""
    names = names or list(RAMPS)
    cols = [OUTLINE, WHITE]
    for n in names:
        cols.extend(RAMPS[n])
    return np.array(cols, dtype=np.uint8)


def quantize(img, names=None, alpha_cut=128):
    """Snaps every pixel of a PIL image to the nearest palette colour (in a perceptual-ish weighting) and makes alpha
    binary. Returns a new RGBA image."""
    a = np.asarray(img.convert("RGBA")).astype(np.float32)
    pal = palette(names).astype(np.float32)
    rgb = a[..., :3].reshape(-1, 3)
    w = np.array([0.30, 0.59, 0.11], dtype=np.float32) * 3
    d = (((rgb[:, None, :] - pal[None, :, :]) ** 2) * w).sum(-1)
    idx = d.argmin(1)
    out = pal[idx].reshape(a.shape[0], a.shape[1], 3)
    alpha = np.where(a[..., 3] >= alpha_cut, 255, 0).astype(np.float32)[..., None]
    return Image.fromarray(np.concatenate([out, alpha], -1).astype(np.uint8), "RGBA")


def swatch(path, scale=24):
    """Writes a picture of all ramps (one row each) for checking by eye."""
    names = list(RAMPS)
    img = Image.new("RGB", (SHADES * scale + 120, len(names) * scale), (40, 40, 40))
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for row, n in enumerate(names):
        for i, c in enumerate(RAMPS[n]):
            d.rectangle([i * scale, row * scale, (i + 1) * scale - 1, (row + 1) * scale - 1], fill=c)
        d.text((SHADES * scale + 6, row * scale + 6), n, fill=(230, 230, 230))
    img.save(path)


if __name__ == "__main__":
    import sys
    swatch(sys.argv[1] if len(sys.argv) > 1 else "palette.png")
