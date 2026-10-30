"""THE GLOAM -- the final boss (sheet 160 x 160, anchor = bottom centre of its 68 x 84 box).

The Gloam's cold core in a floating war frame, built on the citadel's motifs: a blazing magenta-white core held in
an angular black-violet housing, a corona of dark blades behind it (the black eclipse), an orbit ring around the
core, a spired crown with a cold slit eye, two floating shoulder pylons with cyan thrusters and a stepped
inverted-pyramid keel with magenta window bands (like the Gloam fortresses), and a trail of floating shards.

Designed frontally: X to the right, Y up, Z towards the viewer; the whole frame is turned a little to the right
(TURN) so it faces right like every sheet. Lengths in target pixels; the origin is the anchor.
"""
import math

import numpy as np

from bake import (Box, Capsule, Chamfer, Cone, Cylinder, Extrude, Paint, Part, RoundCone, Sheet, Sphere, Torus,
                  Union, bipyramid, keys, material, pixelize, render, rot, trans)

from .bosskit import F, Slab, Stripes, arena, flash, fx_canvas, over, puffs, ring, sparks, streaks, under

SIZE = (160, 160)
ANCHOR = (80, 132)
TURN = 22.0                    # degrees the front turns towards +x (right)
CORE = (0.0, 44.0)             # core centre (box centre is at y 42)

# ---------------------------------------------------------------------------------------------------------- materials
material("gl_alloy", ["violet:0", "violet:1", "slate:1", "violet:2", "purple:3", "magenta:5"], style="metal",
         bands=[-0.4, 0.0, 0.35, 0.68], spec=0.9, line_lit="purple:1")
material("gl_plate", ["violet:1", "slate:1", "violet:2", "violet:3", "purple:4", "magenta:6"], style="metal",
         bands=[-0.4, 0.0, 0.35, 0.68], spec=0.9, line_lit="purple:1")
material("gl_neon", ["magenta:3", "magenta:5", "magenta:6"], style="emit", bands=[0.3, 0.7], prio=2.2)
material("gl_neon_hi", ["magenta:5", "magenta:6", "white"], style="emit", bands=[0.3, 0.75], prio=2.2)
material("gl_cyan", ["cyan:3", "cyan:5", "cyan:6"], style="emit", bands=[0.3, 0.7], prio=2.2)
material("gl_core", ["magenta:4", "magenta:5", "magenta:6", "magenta:7", "white"], style="emit",
         bands=[0.2, 0.45, 0.7, 0.88], prio=3.0, line="magenta:1")
material("gl_core_hi", ["magenta:6", "magenta:7", "white"], style="emit", bands=[0.25, 0.55], prio=3.0,
         line="magenta:2")
material("gl_core_dim", ["magenta:2", "magenta:3", "magenta:4", "magenta:6"], style="emit", bands=[0.3, 0.6, 0.88],
         prio=3.0, line="magenta:1")
material("gl_flame", ["blue:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.6, 0.85], line="blue:2",
         line_lit="blue:2", inner=False)
material("gl_hole", ["violet:0", "outline"], bands=[0.3], inner=False)


# ---------------------------------------------------------------------------------------------------------- shapes
def _blade(r0, length, w, hz=1.2):
    """A corona blade pointing up from radius r0 (to be rotated about z around the core)."""
    poly = [(-w, r0), (-w * 0.55, r0 + length * 0.6), (0, r0 + length), (w * 0.55, r0 + length * 0.6), (w, r0)]
    b = Extrude(poly, hz, r=0.3).m("gl_alloy")
    return Paint(b, Slab((0, 1, 0), r0 + length * 0.72, 1e3), "gl_neon")


def _corona(spin=0.0, ext=1.0, n=12):
    out = [Torus(18.0, 2.8).m("gl_alloy").rot(90, 0, 0),
           Paint(Torus(18.0, 1.0).m("gl_alloy").rot(90, 0, 0).at(0, 0, 2.2), Slab((0, 1, 0), -1e3, 1e3), "gl_neon")]
    for k in range(n):
        a = spin + 360.0 * k / n
        sa = math.sin(math.radians(a + 90))      # blade direction's y component (blades point along +y at a = 0)
        long_ = (k % 2 == 0)
        ln = (36.0 if long_ else 24.0) * ext * (0.55 if sa < -0.55 else 1.0)
        out.append(_blade(17.5, ln, 4.0 if long_ else 2.8).rot(0, 0, a))
    return Union(*out).at(CORE[0], CORE[1], -7.0)


def _housing():
    octa = [(16.5 * math.cos(math.radians(22.5 + 45 * k)), 16.5 * math.sin(math.radians(22.5 + 45 * k)))
            for k in range(8)]
    plate = Extrude(octa, 3.6, r=0.8).m("gl_plate")
    hole = Cylinder(10.6, 8.0).rot(90, 0, 0)
    frame = plate - hole.m("gl_hole")
    rim = Paint(Torus(11.2, 1.1).m("gl_alloy").rot(90, 0, 0).at(0, 0, 3.0), Slab((0, 1, 0), -1e3, 1e3), "gl_neon")
    studs = Union(*[Box(1.6, 1.6, 1.2, r=0.4).m("gl_neon").rot(0, 0, 45).at(13.6 * math.cos(math.radians(a)),
                                                                              13.6 * math.sin(math.radians(a)), 3.6)
                    for a in (90, 210, 330)])
    return Union(frame, rim, studs).at(CORE[0], CORE[1], 1.0)


def _crown():
    spire = Extrude([(-9.5, 57), (-6.5, 69), (0, 88), (6.5, 69), (9.5, 57), (0, 60)], 4.2, r=0.6).m("gl_plate")
    slit = Paint(spire, Slab((0, 1, 0), 66.2, 68.2), "gl_neon_hi")
    horns = []
    for s in (1, -1):
        horns.append(Extrude([(7 * s, 58), (19 * s, 78), (12 * s, 63)], 2.4, r=0.4).m("gl_alloy").at(0, 0, -1.0))
    keystone = bipyramid(4, 2.4, 3.0, 3.0, twist=45).m("gl_neon").at(0, 80.0, 3.5)
    return Union(slit, *horns, keystone)


def _keel():
    poly = [(-15, 33), (15, 33), (11, 26), (8, 18), (4, 10), (0, 3), (-4, 10), (-8, 18), (-11, 26)]
    k = Extrude(poly, 6.0, r=1.0).m("gl_alloy")
    k = Paint(k, Union(*[Box(20, 0.6, 2.0).at(0, y, 6.0) for y in (29.2, 21.8, 14.5)]), "gl_neon")
    steps = Union(*[Chamfer(13.0 - 3.2 * j, 1.4, 7.2 - 0.6 * j, c=0.8).m("gl_plate").at(0, 31.5 - 7.4 * j, 0)
                    for j in range(3)])
    return Union(k, steps)


def _pylon(side, thrust=0.0, flick=0):
    """A floating shoulder blade (local origin at its centre)."""
    s = 1 if side == "r" else -1
    poly = [(0, -20), (6, -11), (8.5, 12), (5, 25), (1, 30), (-3, 14), (-2.5, -11)]
    poly = [(x * s, y) for x, y in poly]
    blade = Extrude(poly, 3.2, r=0.6).m("gl_plate")
    edge = Paint(blade, Slab((s, 0, 0), -1e3, -1.2), "gl_neon")
    fin = Extrude([(x * s, y) for x, y in [(5, 6), (13, 16), (7, 20)]], 1.6, r=0.3).m("gl_alloy").at(0, 0, -1.5)
    nozzle = Cone(2.6, 1.6, 1.6).m("gl_alloy").at(1.5 * s, -20.5, 0)
    jet = None
    if thrust > 0:
        ln = thrust * (1.0 + 0.25 * math.sin(flick * 2.1 + s))
        jet = RoundCone((1.5 * s, -22.0, 0), (1.5 * s, -22.0 - ln, 0), 2.2, 0.6).m("gl_flame")
    eye = Sphere(1.6).m("gl_cyan").at(4.0 * s, 8.0, 3.2)
    return Union(edge, fin, nozzle, eye), jet


def _orbit(ang):
    return Torus(20.0, 0.75).m("gl_neon").rot(72, 0, ang).at(CORE[0], CORE[1], 0)


def _core(level):
    m = {0: "gl_core_dim", 1: "gl_core", 2: "gl_core_hi"}[level]
    return Union(Sphere(9.6).m(m), Sphere(5.4).m("gl_core_hi" if level else "gl_core").at(1.0, 1.0, 5.2)).at(
        CORE[0], CORE[1], 1.5)


def _shards(bob):
    out = []
    for k, (y, r, h) in enumerate(((-3.0, 2.8, 4.0), (-11.5, 2.2, 3.2), (-18.5, 1.6, 2.4))):
        dy = bob * (0.6 + 0.5 * k)
        out.append(bipyramid(4, r, h, h * 1.3, twist=45).m("gl_alloy").at(0, y + dy, 0))
        out.append(Sphere(r * 0.45).m("gl_neon").at(0, y + dy + 0.2, r * 0.75))
    return Union(*out)


# ---------------------------------------------------------------------------------------------------------- posing
BASE = dict(lift=0.0, tilt=0.0, spread=0.0, pyl=0.0, spin=0.0, ext=1.0, core=1, orbit=0.0, thrust=5.0, flick=0,
            bob=0.0, squash=(1.0, 1.0))


def P(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def view(p):
    return trans(0, p["lift"], 0) @ trans(0, CORE[1], 0) @ rot(0, TURN, p["tilt"]) @ trans(0, -CORE[1], 0)


def parts(p):
    V = view(p)
    out = []

    def add(shape, M=None, name="", inner=True, zbias=0.0):
        if shape is not None:
            out.append(Part(shape.xform(V if M is None else V @ M), name=name, inner=inner, zbias=zbias))

    add(_corona(p["spin"], p["ext"]), name="corona")
    add(_core(p["core"]), name="core")
    add(_housing(), name="housing")
    add(_orbit(p["orbit"]), name="orbit", inner=False)
    add(_crown(), name="crown")
    add(_keel(), name="keel")
    add(_shards(p["bob"]), name="shards")
    for side, s in (("r", 1), ("l", -1)):
        dx = 29.0 + 9.0 * p["spread"]
        M = trans(dx * s, CORE[1] + 2.0 + p["pyl"], 0) @ rot(0, 0, -s * (6 + 16 * p["spread"]))
        blade, jet = _pylon(side, p["thrust"], p["flick"] + (3 if s < 0 else 0))
        add(blade, M, name=f"pylon_{side}")
        add(jet, M, name=f"jet_{side}", inner=False)
    return out


def core_point(p):
    q = view(p) @ np.array([CORE[0], CORE[1], 0, 1.0])
    return q[0], q[1]


# ---------------------------------------------------------------------------------------------------------- animations
TAU = 2 * math.pi
STEP = 360.0 / 12 / 8           # 2 * STEP per frame: one long+short blade period (60 deg) per 8-frame loop


def fly(i):
    b = math.sin(TAU * i / 8)
    return P(lift=2.0 * b, pyl=-1.5 * b, spin=-STEP * 2 * i, orbit=45.0 * i, core=2 if i in (0, 4) else 1,
             thrust=5.0 + 1.5 * (i % 2), flick=i, bob=-1.5 * b, tilt=0.8 * math.cos(TAU * i / 8))


def idle(i):
    b = math.sin(TAU * i / 8)
    return P(lift=1.2 * b, pyl=-1.0 * b, spread=-0.35, spin=-STEP * 2 * i, orbit=22.5 * i, ext=0.7, core=0,
             thrust=2.5 + (i % 2), flick=i, bob=-1.0 * b)


def attack_frames():
    """6 frames at 10 fps, once (0.6 s before the blink): flinch in, then BURST open, hold blazing."""
    seq = [dict(spread=-0.5, ext=0.75, core=0, lift=-1.0, fx="draw"),
           dict(spread=1.0, ext=1.35, core=2, lift=1.5, fx="burst0"),
           dict(spread=1.1, ext=1.4, core=2, lift=2.0, fx="burst1"),
           dict(spread=1.05, ext=1.38, core=2, lift=1.5, fx="burst2"),
           dict(spread=1.0, ext=1.35, core=2, lift=1.0, fx="burst3"),
           dict(spread=1.0, ext=1.35, core=2, lift=1.0, fx="burst2")]
    out = []
    for k, d in enumerate(seq):
        d = dict(d)
        fx = d.pop("fx")
        out.append((P(spin=-STEP * 3 * k, orbit=60.0 * k, thrust=7.0, flick=k, **d), fx))
    return out


def anims():
    return [
        ("fly", 10, "loop", [(fly(i), None) for i in range(8)],
         "hovering: corona turns, orbit ring spins, pylons float, thrusters flicker, core pulses"),
        ("attack", 10, "once", attack_frames(),
         "flinch in, BURST open at frame 1 (orbs/bolts), holds blazing (0.6 s, then the blink)"),
        ("idle", 8, "loop", [(idle(i), None) for i in range(8)], "dormant: closed up, core dim, slow drift"),
    ]


# ---------------------------------------------------------------------------------------------------------- effects
def _effects(fx, p):
    c = fx_canvas(SIZE, ANCHOR)
    back = fx_canvas(SIZE, ANCHOR)
    if fx is None:
        return c, back
    x, y = core_point(p)
    if fx == "draw":
        for k in range(6):
            a = math.radians(30 + 60 * k)
            sparks(c, [(x + 22 * math.cos(a), y + 22 * math.sin(a), 0.9)], cols=("magenta:6", "white"))
            streaks(c, [(x + 18 * math.cos(a), y + 18 * math.sin(a), x + 12 * math.cos(a), y + 12 * math.sin(a))],
                    cols=("magenta:5", "magenta:7"), w=0.5)
    elif fx.startswith("burst"):
        d = int(fx[-1])
        if d == 0:
            flash(c, x, y, 20.0, rays=8, ang=0, cols=("magenta:5", "magenta:7", "white"))
        r = 24 + 9 * d
        ring(back, x, y, r, r, 0.9, "magenta:6" if d < 2 else "magenta:4", prio=2.5)
        if d >= 1:
            ring(back, x, y, r - 8, r - 8, 0.7, "magenta:4", prio=2.5)
        for k in range(8):
            a = math.radians(22.5 + 45 * k + 10 * d)
            rr = 18 + 7 * d
            sparks(c, [(x + rr * math.cos(a), y + rr * math.sin(a), 1.0)], cols=("magenta:6", "white"))
    return c, back


def frame(job):
    name, i = job
    p, fx = {a[0]: a[3] for a in anims()}[name][i]
    R = render(parts(p), SIZE, ANCHOR)
    c, back = _effects(fx, p)
    under(R, back)
    over(R, c)
    return pixelize(R)


def jobs():
    return [(a[0], i) for a in anims() for i in range(len(a[3]))]


def sheets(frames):
    sh = Sheet("gloam", SIZE, ANCHOR, cols=16, title="THE GLOAM, its cold core in a floating war frame (faces right)")
    x, y = core_point(BASE)
    sh.point("muzzle", x, -y, "the core: orb rings, bolts (WorldBoss fires from the box centre, 0 -42)")
    sh.point("crown", 0, -84, "the slit eye / spire tip (missiles)")
    sh.note("anchor = bottom centre of the 68 x 84 box; the keel tip touches it, the shards hang below")
    sh.note("attack is one-shot (0.6 s, WorldBoss state 1 before the blink): play it from frame 0, it holds frame 5")
    sh.note("glow: core, neon trims, window bands, slit eye, cyan thrusters, bursts")
    for name, fps, mode, specs, note in anims():
        sh.anim(name, fps, mode, [frames[(name, i)] for i in range(len(specs))], note=note)
    idx = {a[0]: a[3] for a in sh.anims}
    arena(sh, [idx["idle"][0], idx["fly"][0], idx["fly"][4], idx["attack"][0], idx["attack"][1], idx["attack"][4]],
          air=30)
    return [sh]
