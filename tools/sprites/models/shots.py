"""Projectiles -- the shots sheet (32 x 32, anchor = centre, all point RIGHT; the engine rotates them).

Energy shots are banded 2D shapes (white core, bright ring, darker halo, no black outline); solid shots
(shell, missile, grenade, disc, shard, seeker) are small 3D models with an outline.
"""
import math

import numpy as np

from bake import (Box, Canvas, Capsule, Cone, Cylinder, Ellipsoid, Extrude, Paint, Part, Sheet, Sphere, Subtract,
                  Torus, Union, fbm, material, pixelize, prism, render, vnoise)

SIZE = (32, 32)
ANCHOR = (16, 16)
SS = 6

material("sh_steel", ["slate:2", "steel:3", "steel:4", "steel:5", "steel:6"], bands=[-0.45, -0.05, 0.35, 0.78])
material("sh_dark", ["slate:1", "slate:2", "slate:3", "slate:4"], bands=[-0.4, 0.05, 0.6])
material("sh_white", ["slate:4", "slate:5", "steel:6", "steel:7"], bands=[-0.45, 0.0, 0.7])
material("sh_violet", ["violet:2", "violet:3", "violet:4", "violet:5"], bands=[-0.4, 0.05, 0.65], line="violet:1")
material("sh_magenta", ["magenta:2", "magenta:3", "magenta:4", "magenta:5"], bands=[-0.4, 0.05, 0.65])
material("sh_red", ["crimson:2", "red:3", "red:4", "red:5"], bands=[-0.4, 0.05, 0.65])
material("sh_olive", ["olive:1", "olive:2", "olive:3", "olive:4"], bands=[-0.4, 0.05, 0.65], line="olive:0")
material("sh_ice", ["blue:3", "ice:3", "ice:4", "ice:5", "ice:6", "white"], bands=[-0.45, -0.15, 0.15, 0.5, 0.85],
         glow=True, line="blue:1")
material("sh_glow_mag", ["magenta:4", "magenta:6", "white"], style="emit", bands=[0.4, 0.8], prio=2.0)
material("sh_glow_lime", ["green:4", "lime:4", "lime:5"], style="emit", bands=[0.35, 0.75], prio=2.0)
material("sh_glow_red", ["red:4", "red:6", "white"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("sh_flame", ["orange:4", "yellow:5", "white"], style="emit", bands=[0.45, 0.8], inner=False,
         outline=False)


def canvas(ss=SS):
    return Canvas(SIZE, ANCHOR, ss=ss)


def done(c_or_r, outline=False, cov=7, keep_single=True):
    return pixelize(c_or_r, cov=cov, outline=outline, inner=False, keep_single=keep_single)


def energy(c, x0, x1, r_tail, r_head, colours, y=0.0, glow=True):
    """A teardrop of light from the tail x0 to the head x1, banded outer -> inner with `colours`."""
    n = len(colours)
    for k, colour in enumerate(colours):
        f = 1.0 - k / float(n)
        d = c.capsule(x0 + (x1 - x0) * (1 - f) * 0.55, y, x1 - (1 - f) * r_head * 0.4, y, r_tail * f, r_head * f)
        c.fill(d < 0, colour, glow=glow, line=False)


# ---------------------------------------------------------------------------------------------------------- player

def bolt(i, ramp=("cyan:3", "cyan:4", "cyan:6", "white")):
    c = canvas()
    tail = (-9.0, -7.5)[i % 2]
    energy(c, tail, 6.5, 0.6, 3.0, list(ramp))
    return done(c)


def bolt_charged(i):
    c = canvas()
    R, TH = c.polar(1, 0)
    wob = 0.5 * np.sin(TH * 5 + i * 1.6)
    energy(c, -13.0, 7.5, 1.2, 6.0, ["blue:3", "cyan:4", "cyan:5"])
    c.fill(R + wob < 6.2, "cyan:5", glow=True, line=False)
    c.fill(R + wob * 0.6 < 4.6, "cyan:6", glow=True, line=False)
    c.fill(R < 3.0, "white", glow=True, line=False)
    # orbiting sparks
    for k in range(3):
        a = 2 * math.pi * (k / 3.0 + i / 8.0)
        sx, sy = 1 + 7.6 * math.cos(a), 6.0 * math.sin(a)
        c.fill(c.circle(sx, sy, 1.0) < 0, "white", glow=True, line=False)
        c.fill(c.circle(sx - 1.2 * math.sin(a), sy, 0.7) < 0, "cyan:6", glow=True, line=False)
    return done(c)


def bolt_rapid(i):
    c = canvas()
    energy(c, (-6.0, -5.0)[i % 2], 4.5, 0.5, 1.9, ["orange:4", "yellow:5", "white"])
    return done(c)


def pellet(i):
    c = canvas()
    energy(c, (-4.5, -3.5)[i % 2], 2.5, 0.5, 2.6, ["orange:3", "yellow:4", "yellow:6", "white"])
    return done(c)


def disc(i):
    a = 90.0 * i / 4.0
    body = Cylinder(5.4, 0.9, rr=0.45).m("sh_steel")
    notch = Union(*[Box(1.0, 2.0, 5.6).rot(0, k * 90 + a, 0) for k in range(2)])
    body = Paint(body, notch, "sh_dark")
    rim = Torus(5.3, 0.9).m("sh_glow_lime")
    hub = Cylinder(1.4, 1.1, rr=0.3).m("sh_glow_lime")
    shape = Union(body, rim, hub).rot(28, 0, 0).rot(0, 0, -6)
    return done(render([Part(shape)], SIZE, ANCHOR, ss=SS), outline=True)


def cryo(i):
    c = canvas()
    # frosty mist tail
    n = fbm(c.X + i * 3, c.Y, 0.5, 3, 2)
    mist = (c.capsule(-12, 0, 2, 0, 1.0, 4.2) < 0) & (n > 0.42 + 0.03 * (c.X + 12) * -0.3)
    c.fill(mist, "ice:4", glow=True, line=False)
    c.fill(mist & (n > 0.6), "ice:6", glow=True, line=False)
    # the ice spike
    spike = c.polygon([(9.5, 0), (0, 3.2), (-4, 0.0), (0, -3.2)])
    c.fill(spike < 0, "ice:5", glow=True)
    c.fill(c.polygon([(9.5, 0), (0, 3.2), (-1, 0.2)]) < 0, "ice:7", glow=True)
    c.fill(c.polygon([(6, 0), (1, 1.2), (1, -0.6)]) < 0, "white", glow=True)
    for k, (x, y) in enumerate(((-6, 3), (-9, -2), (-3, -4), (-11, 1))):
        if (k + i) % 2 == 0:
            c.fill((np.abs(c.X - x) < 0.5) & (np.abs(c.Y - y) < 1.6) | (np.abs(c.Y - y) < 0.5) & (np.abs(c.X - x) < 1.6),
                   "white", glow=True, line=False)
    spr = done(c, outline=False)
    return spr


def laser(i, n=4):
    """A 32 px horizontal beam segment; tiles seamlessly (patterns repeat every 16 px)."""
    c = canvas()
    X, Y = c.X, c.Y
    ph = i / float(n)
    wav = 0.45 * np.sin(2 * np.pi * (X / 16.0 - ph))
    c.fill(np.abs(Y) < 3.6 + wav, "crimson:3", glow=True, line=False)
    c.fill(np.abs(Y) < 2.6 + wav, "red:4", glow=True, line=False)
    c.fill(np.abs(Y) < 1.6 + wav * 0.5, "rose:6", glow=True, line=False)
    c.fill(np.abs(Y) < 0.8, "white", glow=True, line=False)
    pulse = (((X / 16.0 - ph) % 1.0) < 0.18) & (np.abs(Y) < 2.4)
    c.fill(pulse, "white", glow=True, line=False)
    return done(c)


def mortar(i):
    body = Union(Ellipsoid(5.0, 3.2, 3.2).m("sh_violet"),
                 Cone(3.0, 1.2, 1.4).m("sh_dark").rot(0, 0, 90).at(-5.4, 0, 0),
                 Torus(3.1, 0.6).m("sh_glow_mag" if i % 2 == 0 else "sh_magenta").rot(0, 0, 90).at(1.2, 0, 0),
                 Sphere(1.1).m("sh_glow_mag").at(4.6, 0, 0))
    fins = Union(*[Box(1.4, 2.6, 0.35).m("sh_dark").rot(a, 0, 0).at(-5.6, 0, 0) for a in (0, 90)])
    shape = Union(body, fins).rot(30 + 45 * i, 0, 0)
    return done(render([Part(shape)], SIZE, ANCHOR, ss=SS), outline=True)


def arc(i, n=4):
    """A lightning segment from the left edge to the right edge through the centre line (chainable)."""
    c = canvas()
    rng = np.random.default_rng(11 + i)
    xs = np.linspace(-16, 16, 9)
    ys = np.concatenate([[0], rng.uniform(-5, 5, 7), [0]])
    for k in range(len(xs) - 1):
        d = c.capsule(xs[k], ys[k], xs[k + 1], ys[k + 1], 1.8)
        c.fill(d < 0, "blue:4", glow=True, line=False)
    for k in range(len(xs) - 1):
        d = c.capsule(xs[k], ys[k], xs[k + 1], ys[k + 1], 1.0)
        c.fill(d < 0, "cyan:5", glow=True, line=False)
    for k in range(len(xs) - 1):
        d = c.capsule(xs[k], ys[k], xs[k + 1], ys[k + 1], 0.45)
        c.fill(d < 0, "white", glow=True, line=False)
    # a forked branch
    b = int(rng.integers(2, 6))
    bx, by = xs[b], ys[b]
    ex, ey = bx + rng.uniform(3, 6), by + rng.choice([-1, 1]) * rng.uniform(4, 7)
    c.fill(c.capsule(bx, by, ex, ey, 0.9) < 0, "cyan:5", glow=True, line=False)
    c.fill(c.capsule(bx, by, ex, ey, 0.4) < 0, "white", glow=True, line=False)
    return done(c)


def seeker(i):
    body = Union(Capsule((-4.0, 0, 0), (3.0, 0, 0), 1.6).m("sh_white"),
                 Cone(1.6, 0.25, 1.4).m("sh_magenta").rot(0, 0, -90).at(4.2, 0, 0),
                 Torus(1.65, 0.45).m("sh_magenta").rot(0, 0, 90).at(-1.0, 0, 0))
    fins = Union(*[Extrude([(-5.2, 0), (-3.0, 0), (-4.6, 3.0), (-5.6, 3.0)], 0.3).m("sh_magenta").rot(a, 0, 0)
                   for a in (0, 120, 240)])
    shape = Union(body, fins).rot(20, 0, 0)
    r = render([Part(shape)], SIZE, ANCHOR, ss=SS)
    c = canvas()
    fl = (-9.0, -8.0)[i % 2]
    energy(c, fl, -5.0, 0.4, 1.5, ["orange:4", "yellow:5", "white"])
    c.z[c.col >= 0] = -1e6
    r.overlay(c, zmode=True)
    return done(r, outline=True)


# ---------------------------------------------------------------------------------------------------------- enemy

def enemy_bolt(i):
    return bolt(i, ("crimson:3", "red:4", "orange:5", "yellow:6"))


def enemy_orb(i):
    c = canvas()
    R, TH = c.polar(0, 0)
    pulse = (0.0, 0.5, 1.0, 0.5)[i % 4]
    c.fill(R < 6.0 + pulse * 0.5, "purple:3", glow=True, line=False)
    c.fill(R < 5.0 + pulse * 0.4, "magenta:4", glow=True, line=False)
    c.fill(R < 3.6, "magenta:5", glow=True, line=False)
    c.fill(R < 2.2, "rose:7", glow=True, line=False)
    c.fill(R < 1.1, "white", glow=True, line=False)
    ring = (np.abs(np.hypot(c.X / 8.0, c.Y / 2.6) - 1.0) < 0.12) & ~((R < 5.0) & (c.Y > 0))
    rot = (TH + i * np.pi / 4) % (np.pi / 2) < np.pi / 4
    c.fill(ring & rot, "magenta:6", glow=True, line=False)
    c.fill(ring & ~rot, "purple:4", glow=True, line=False)
    return done(c)


def acid(i):
    c = canvas()
    w = (0.0, 0.6, 0.0, -0.6)[i % 4]
    d = c.capsule(-5.5, 0, 2.5, 0, 1.6, 3.6 + w * 0.3)
    c.fill(d < 0, "green:3")
    c.fill(c.capsule(-4.5, 0.4, 2.5, 0.6, 1.0, 2.8 + w * 0.3) < 0, "lime:4")
    c.fill(c.circle(3.0, 1.4, 1.3) < 0, "lime:6")
    c.fill(c.circle(3.4, 1.8, 0.6) < 0, "white")
    for k, (x, y, r) in enumerate(((-8.5, 1.5, 0.9), (-10.5, -1.0, 0.7), (-7.5, -2.2, 0.6))):
        if (k + i) % 3 != 0:
            c.fill(c.circle(x - (i % 2), y, r) < 0, "lime:4")
    spr = done(c, outline=False, cov=6)
    from bake import outline_sprite
    return outline_sprite(spr, "green:1")


def shard(i):
    p = prism(6, 3.0, 2.0, 5.6, 2.8, twist=0).m("sh_ice").rot(0, 15 * i, 0).rot(0, 0, -90).rot(18, 0, 0)
    return done(render([Part(p)], SIZE, ANCHOR, ss=SS), outline=True)


def missile(i):
    body = Union(Capsule((-6.0, 0, 0), (4.0, 0, 0), 2.2).m("sh_steel"),
                 Cone(2.2, 0.3, 2.0).m("sh_red").rot(0, 0, -90).at(5.6, 0, 0),
                 Torus(2.25, 0.5).m("sh_red").rot(0, 0, 90).at(-1.0, 0, 0),
                 Cylinder(1.6, 0.6).m("sh_dark").rot(0, 0, 90).at(-6.6, 0, 0))
    fins = Union(*[Extrude([(-7.4, 0), (-4.0, 0), (-6.0, 4.0), (-7.8, 4.0)], 0.35).m("sh_red").rot(a, 0, 0)
                   for a in (0, 120, 240)])
    shape = Union(body, fins).rot(15, 0, 0)
    r = render([Part(shape)], SIZE, ANCHOR, ss=SS)
    c = canvas()
    energy(c, (-15.0, -13.0)[i % 2], -7.0, 0.5, 2.2, ["red:4", "orange:4", "yellow:5", "white"])
    c.z[c.col >= 0] = -1e6
    r.overlay(c, zmode=True)
    return done(r, outline=True)


def grenade(i):
    body = Union(Sphere(4.2).m("sh_olive"),
                 Cylinder(4.25, 0.7).m("sh_dark"),
                 Cylinder(1.6, 1.0, rr=0.3).m("sh_steel").at(0, 4.3, 0),
                 Sphere(1.1).m("sh_glow_red" if i % 2 == 0 else "sh_red").at(0, 5.4, 0))
    shape = body.rot(0, 0, -90.0 * i).rot(14, 0, 0)
    return done(render([Part(shape)], SIZE, ANCHOR, ss=SS), outline=True)


def spore(i):
    c = canvas()
    R, TH = c.polar(0, 0)
    spikes = 0.9 * np.maximum(0, np.sin(TH * 7 + i * 0.6)) ** 3
    n = vnoise(c.X, c.Y, 0.9, 5 + i)
    c.fill(R < 4.6 + spikes * 1.8 + n * 0.6, "purple:3")
    c.fill(R < 3.8 + n * 0.5, "purple:4")
    c.fill(R < 2.6, "magenta:5")
    dots = (vnoise(c.X, c.Y, 1.6, 9) > 0.72) & (R < 3.8)
    c.fill(dots, "lime:5", glow=True)
    c.fill(c.circle(-1.0, 1.2, 0.8) < 0, "rose:7")
    spr = done(c, outline=False, cov=6)
    from bake import outline_sprite
    return outline_sprite(spr, "purple:1")


# ---------------------------------------------------------------------------------------------------------- sheet

ANIMS = [
    ("bolt", 16, "loop", 2, bolt, "pulse blaster"),
    ("bolt_charged", 16, "loop", 4, bolt_charged, "charged piercing shot"),
    ("bolt_rapid", 16, "loop", 2, bolt_rapid, "repeater"),
    ("pellet", 16, "loop", 2, pellet, "scatter"),
    ("disc", 16, "loop", 4, disc, "ricochet, spinning"),
    ("cryo", 12, "loop", 2, cryo, "cryo projector"),
    ("laser", 20, "loop", 4, laser, "lancer beam: 32 px segment, tiles horizontally"),
    ("mortar", 12, "loop", 4, mortar, "plasma mortar shell, tumbling"),
    ("arc", 20, "loop", 4, arc, "arc caster: 32 px lightning segment, ends on the centre line (chain or stretch)"),
    ("seeker", 16, "loop", 2, seeker, "homing mini missile"),
    ("enemy_bolt", 16, "loop", 2, enemy_bolt, ""),
    ("enemy_orb", 12, "loop", 4, enemy_orb, ""),
    ("acid", 10, "loop", 4, acid, "spitter"),
    ("shard", 12, "loop", 4, shard, "ice shard"),
    ("missile", 16, "loop", 2, missile, ""),
    ("grenade", 12, "loop", 4, grenade, "tumbling, blinking"),
    ("spore", 8, "loop", 4, spore, ""),
]


def frame(job):
    name, i = job
    fn = next(a[4] for a in ANIMS if a[0] == name)
    return fn(i)


def jobs():
    return [(a[0], i) for a in ANIMS for i in range(a[3])]


def sheets(frames):
    sh = Sheet("shots", SIZE, ANCHOR, cols=16, title="projectiles (anchor = centre, pointing right)")
    sh.note("the engine rotates shots to their direction; glow = all energy pixels")
    for name, fps, mode, n, fn, note in ANIMS:
        sh.anim(name, fps, mode, [frames[(name, i)] for i in range(n)], note=note)
    return [sh]
