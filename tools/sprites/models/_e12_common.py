"""Shared helpers for the regular enemies of episodes 1 and 2 (models/<id>.py of sweeper ... hivenest).

Frame sizes: 64 x 64 with the sheet anchor (32, 60) (the bottom centre of the hit box) and the render anchor one row
higher (32, 59), so the 1 px outline under feet / bases is the row just above the anchor line (README "ground
line"); 96 x 96 frames (the spawners) use (48, 92) / (48, 91).

World units are target pixels, y up, origin = render anchor. Sprite touch-ups (sparks, lightning, puffs) work in
frame pixels (y down); `to_px` converts.
"""
import math

import numpy as np

from bake import Cylinder, Sheet, Torus, col, pixelize, render

S64, A64, R64 = (64, 64), (32, 60), (32, 59)
S96, A96, R96 = (96, 96), (48, 92), (48, 91)


# ---------------------------------------------------------------------------------------------------------- shapes

def bar_x(r, x0, x1, y=0.0, z=0.0, rr=0.0):
    """A cylinder along x from x0 to x1."""
    return Cylinder(r, abs(x1 - x0) / 2, rr=rr).rot(0, 0, -90).at((x0 + x1) / 2, y, z)


def bar_z(r, z0, z1, x=0.0, y=0.0, rr=0.0):
    """A cylinder along z (towards the viewer) from z0 to z1: axles, wheels, lenses."""
    return Cylinder(r, abs(z1 - z0) / 2, rr=rr).rot(90, 0, 0).at(x, y, (z0 + z1) / 2)


def ring_x(R, r, x, y=0.0, z=0.0):
    return Torus(R, r).rot(0, 0, 90).at(x, y, z)


def ring_z(R, r, x=0.0, y=0.0, z=0.0):
    return Torus(R, r).rot(90, 0, 0).at(x, y, z)


# ---------------------------------------------------------------------------------------------------------- frames

def shoot(parts, size=S64, ranchor=R64, cov=7, canvas=None, under=False, squash=(1.0, 1.0), pivot=(0.0, 0.0),
          keep_single=False, inner=True, ss=4):
    """Renders and pixelizes parts (plus an optional 2D canvas on top, or behind with under=True)."""
    r = render(parts, size, ranchor, ss=ss, squash=squash, pivot=pivot)
    if canvas is not None:
        if under:
            canvas.z[canvas.col >= 0] = -1e6
            r.overlay(canvas, zmode=True)
        else:
            r.overlay(canvas)
    return pixelize(r, cov=cov, keep_single=keep_single, inner=inner)


def to_px(x, y, ranchor=R64):
    """World (x, y up) -> frame pixel (column, row)."""
    return int(round(ranchor[0] + x - 0.5)), int(round(ranchor[1] - y - 0.5))


def point_of(x, y, anchor=A64, ranchor=R64):
    """World point -> sheet point offset (dx, dy) from the sheet anchor (y down)."""
    return x + (ranchor[0] - anchor[0]), -y - (anchor[1] - ranchor[1])


# ---------------------------------------------------------------------------------------------------------- touch-ups

def put(spr, x, y, colour, glow=True, empty_only=False):
    x, y = int(round(x)), int(round(y))
    if empty_only and spr.get(x, y) >= 0:
        return
    spr.put(x, y, colour, glow=glow)


def spark(spr, x, y, size=1, c=("white", "yellow:6", "orange:4"), glow=True):
    """A small four-point spark centred on pixel (x, y)."""
    put(spr, x, y, c[0], glow)
    for k in range(1, size + 1):
        cc = c[1] if k < size or size == 1 else c[2]
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            put(spr, x + dx, y + dy, cc, glow)
    if size >= 2:
        for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
            put(spr, x + dx, y + dy, c[2], glow, empty_only=True)


def line(spr, x0, y0, x1, y1, colour, glow=True, empty_only=False):
    """Bresenham line in frame pixels."""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        put(spr, x0, y0, colour, glow, empty_only)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def bolt(spr, x0, y0, x1, y1, seed, segs=3, jitter=2.0, colour="cyan:6", edge=None, glow=True):
    """A jagged electric arc between two frame pixels (seeded, so frames differ but rebuilds match)."""
    rng = np.random.default_rng(seed)
    pts = [(x0, y0)]
    for k in range(1, segs):
        t = k / segs
        nx, ny = -(y1 - y0), (x1 - x0)
        n = math.hypot(nx, ny) or 1.0
        j = rng.uniform(-jitter, jitter)
        pts.append((x0 + (x1 - x0) * t + nx / n * j, y0 + (y1 - y0) * t + ny / n * j))
    pts.append((x1, y1))
    pts = [(int(round(a)), int(round(b))) for a, b in pts]
    if edge is not None:
        for (a, b), (c, d) in zip(pts, pts[1:]):
            line(spr, a + 1, b, c + 1, d, edge, glow, empty_only=True)
    for (a, b), (c, d) in zip(pts, pts[1:]):
        line(spr, a, b, c, d, colour, glow)


def blob(spr, x, y, r, colour, glow=False, empty_only=False):
    """A filled pixel disc (smoke puffs, spores)."""
    ri = int(math.ceil(r))
    for dy in range(-ri, ri + 1):
        for dx in range(-ri, ri + 1):
            if dx * dx + dy * dy <= r * r + 0.3:
                put(spr, x + dx, y + dy, colour, glow, empty_only)


def puff(spr, x, y, r, shades=("grey:3", "grey:4", "grey:5"), empty_only=True):
    """A small smoke puff: dark rim, lighter top-left core."""
    blob(spr, x, y, r, shades[0], False, empty_only)
    if r >= 1.5:
        blob(spr, x - 0.4, y - 0.4, r - 0.8, shades[1], False, False)
    if r >= 2.2:
        blob(spr, x - 1, y - 1, max(0.6, r - 1.9), shades[2], False, False)


# ---------------------------------------------------------------------------------------------------------- sheets

def anim_jobs(anims):
    """anims: [(name, fps, mode, n_frames, note[, order])] -> [(name, i)]."""
    return [(a[0], i) for a in anims for i in range(a[3])]


def make_sheet(name, size, anchor, title, anims, frames, points=(), notes=(), cols=8):
    """One Sheet from rendered frames. An anim's optional 6th entry is the play order (indices into its frames,
    repeats allowed), e.g. an anticipation once followed by a held loop."""
    sh = Sheet(name, size, anchor, cols=cols, title=title)
    for p in points:
        sh.point(*p)
    for n in notes:
        sh.note(n)
    for a in anims:
        nm, fps, mode, n, note = a[:5]
        idx = sh.anim(nm, fps, mode, [frames[(nm, i)] for i in range(n)], note=note)
        if len(a) > 5 and a[5]:
            order = [idx[k] for k in a[5]]
            sh.anims[-1] = (nm, fps, mode, order, note)
    return [sh]


__all__ = ["S64", "A64", "R64", "S96", "A96", "R96", "bar_x", "bar_z", "ring_x", "ring_z", "shoot", "to_px",
           "point_of", "put", "spark", "line", "bolt", "blob", "puff", "anim_jobs", "make_sheet", "col"]
