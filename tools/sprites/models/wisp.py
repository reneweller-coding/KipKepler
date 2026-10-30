"""wisp -- episode 3 floater (box 20 x 20): a cold ghost light that drifts through rock at the hero. A bright core
with a hollow-eyed face, a flickering tail of cold fire streaming behind, motes circling. Mostly glow.

64 x 64 frames, anchor (32, 44) = the box's bottom centre; the body is centred on the box (world y = 10).
2D: drawn into a canvas in stepped colour bands (no blends), noise for the flicker.
"""
import math

import numpy as np

from bake import fbm, outline_sprite, pixelize, vnoise
from models._e34_common import TAU, Enemy, sparkle

E = Enemy("wisp", (64, 64), (32, 44), "wisp, a cold ghost light (episode 3 floater, faces right)", 3, ground=False)

CY = 10.0         # body centre height above the anchor
BANDS = [("violet:3", False), ("blue:4", True), ("cyan:4", True), ("cyan:5", True), ("cyan:6", True), ("white", True)]


def field(c, t, bob, stretch=1.0, scatter=0.0):
    """A 'heat' field: high in the core, falling off along the tail (which streams up-left, behind)."""
    X, Y = c.X, c.Y - (CY + bob)
    # tail: a tapering capsule from the core back and up, its axis wavering
    sway = 1.6 * math.sin(TAU * t)
    L = 13.0 * stretch
    ex, ey = -L, 4.0 + sway
    px, py = X, Y
    ee = ex * ex + ey * ey
    u = np.clip((px * ex + py * ey) / ee, 0, 1)
    # the tail wiggles more the further out it gets
    wig = 2.0 * u * np.sin(TAU * (t * 2 - u * 1.4))
    dx, dy = px - ex * u, py - (ey * u + wig)
    rad = 6.2 * (1 - u) ** 0.8 + 0.6
    d = np.hypot(dx, dy) / rad
    n = fbm(X * 1.0 - t * 18, Y * 1.0 + t * 6, 0.22, 7, 3)
    heat = (1.15 - d) - 0.55 * u + 0.5 * (n - 0.5) * (0.4 + u)
    core = 1.0 - np.hypot(X - 0.6, Y) / 4.6
    heat = np.maximum(heat, core * 1.25)
    if scatter > 0:
        heat -= scatter * (vnoise(X, Y, 0.6, 11) * 0.9)
    return heat


def draw(t, bob=0.0, eyes=True, stretch=1.0, scatter=0.0, motes=True, blink=False):
    c = E.canvas()
    h = field(c, t, bob, stretch, scatter)
    cuts = [0.02, 0.18, 0.36, 0.55, 0.78, 1.0]
    for cut, (colour, glow) in zip(cuts, BANDS):
        c.fill(h >= cut, colour, glow=glow, line=False)
    if eyes:
        # hollow eyes and a small open mouth, facing right
        X, Y = c.X, c.Y - (CY + bob)
        for ex in (1.0, 4.2):
            r = (0.7 if blink else 1.5)
            c.fill(np.hypot((X - ex) / 0.9, (Y - 1.3) / r) < 1.0, "violet:1", glow=False, line=False)
        c.fill(np.hypot((X - 2.9) / 0.9, (Y + 2.2) / 1.1) < 1.0, "violet:2", glow=False, line=False)
    spr = pixelize(c, cov=6, outline=False, inner=False, keep_single=True)
    outline_sprite(spr, "blue:1")
    if motes:
        for k in range(3):
            a = TAU * (t + k / 3.0)
            x = int(round(32 + 1 + 11 * math.cos(a)))
            y = int(round(44 - CY - bob - 3.5 * math.sin(a) - 1))
            sparkle(spr, x, y, 1 if (k + int(t * 8)) % 3 else 0, c1="white", c2="cyan:5")
    return spr


def fly(i):
    n = 8
    t = i / n
    bob = 1.2 * math.sin(TAU * t)
    return draw(t, bob, blink=i == 5)


def hurt(i):
    t = i / 3.0
    return draw(t, 0.0, stretch=1.0 - 0.15 * i, scatter=[0.6, 0.35, 0.1][i], motes=False, blink=True)


E.anim("fly", 12, "loop", 8, fly, "drifting: tail flickers, motes circle")
E.anim("hurt", 12, "once", 3, hurt, "torn apart for a moment")
E.note("almost all of it glows (the eyes and mouth are dark hollows); the engine may add a cold point light")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
