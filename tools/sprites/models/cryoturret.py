"""cryoturret -- episode 3 turret (box 26 x 26): a frosted mining-colony gun gone feral, an ice-crusted dome on a
flared pedestal, a crystal emitter barrel that fires ice shards.

64 x 64 frames, anchor (32, 60) = the base on the ground line. Drawn standing on its base; the engine turns it by
180 degrees for ceilings.
"""
import math

import numpy as np

from bake import (Box, Capsule, Chamfer, Cone, Cylinder, Ellipsoid, Lathe, Paint, Part, Sphere, Torus, Union, material,
                  prism, rot, scaling, trans)
from models._e34_common import TAU, Enemy, chip, flash, puff, sparkle

E = Enemy("cryoturret", (64, 64), (32, 60), "cryo turret (episode 3, faces right; drawn on its base)", 3)

material("cryoturret_steel", ["slate:1", "slate:2", "steel:3", "steel:4", "steel:5", "steel:6"],
         bands=[-0.5, -0.15, 0.2, 0.55, 0.85])
material("cryoturret_dark", ["violet:0", "slate:1", "slate:2", "slate:3"], bands=[-0.3, 0.2, 0.7])
material("cryoturret_paint", ["blue:1", "blue:2", "blue:3", "blue:4", "blue:5"], bands=[-0.45, -0.05, 0.35, 0.75])
material("cryoturret_frost", ["slate:4", "ice:5", "ice:6", "ice:7", "white"], bands=[-0.45, -0.05, 0.35, 0.75],
         line_lit="slate:2")
material("cryoturret_crystal", ["blue:2", "blue:3", "cyan:3", "cyan:4", "cyan:5", "cyan:6", "white"],
         bands=[-0.5, -0.2, 0.05, 0.3, 0.6, 0.85], glow=True, line="blue:1", line_lit="blue:1")
material("cryoturret_lens", ["cyan:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.6, 0.85], prio=2.5)
material("cryoturret_lens_dim", ["blue:3", "cyan:3", "cyan:4", "cyan:5"], style="emit", bands=[0.3, 0.6, 0.85],
         prio=2.5)
material("cryoturret_hot", ["cyan:6", "white"], style="emit", bands=[0.5], prio=3.0)
material("cryoturret_lamp", ["red:4", "red:6"], style="emit", bands=[0.5], prio=3.0)
material("cryoturret_lamp_off", ["crimson:1", "crimson:2"], bands=[0.4], prio=3.0)

HEAD_Y = 11.4       # swivel centre height (x S = the box centre)
BARREL = 12.8       # emitter tip ahead of the swivel centre
S = 1.16            # model scale


def base():
    ped = Lathe([(11.0, 0.0), (11.0, 1.2), (9.6, 2.4), (6.4, 3.6), (5.0, 6.0), (5.4, 8.4), (4.6, 9.2)]) \
        .m("cryoturret_paint")
    ring = Torus(9.8, 0.9).m("cryoturret_steel").at(0, 1.6, 0)
    bolts = [Sphere(0.75).m("cryoturret_steel").at(9.0 * math.cos(a), 2.4, 9.0 * math.sin(a))
             for a in np.radians([-150, -110, -70, -30, 10, 50])]
    snow = Ellipsoid(8.4, 1.8, 6.0).m("cryoturret_frost").at(-2.0, 3.4, -1.0)
    icicles = [Cone(0.8, 0.05, 1.6 + 0.5 * k).m("cryoturret_frost").rot(0, 0, 180)
               .at(-9.8 + 2.4 * k, 0.6 - 0.4 * k, 4.0) for k in range(3)]
    return Union(ped, ring, *bolts, snow)


def head(charge=0.0, recoil=0.0, lamp=True, glow=1.0):
    """Head in swivel space (centre at the origin, barrel along +x)."""
    dome = Sphere(6.6).m("cryoturret_paint")
    dome = Paint(dome, Box(10, 1.0, 10).at(0, -1.4, 0), "cryoturret_steel")
    collar = Cylinder(6.2, 1.2, rr=0.6).m("cryoturret_steel").at(0, -4.8, 0)
    cap = Ellipsoid(5.6, 2.6, 5.4).m("cryoturret_frost").at(-1.4, 4.4, -0.4)
    cap2 = Ellipsoid(2.2, 1.6, 2.4).m("cryoturret_frost").at(2.4, 5.0, 1.4)
    icic = [Cone(0.7, 0.05, 1.5).m("cryoturret_frost").rot(0, 0, 180).at(x, 1.6, 5.6) for x in (-3.8, -1.6)]
    # emitter: a steel sleeve with fins holding a crystal spike
    r = -recoil
    sleeve = Cylinder(2.5, 3.4, rr=0.8).m("cryoturret_steel").rot(0, 0, -90).at(5.6 + r, -0.2, 0)
    fins = [Box(1.6, 0.35, 3.0, r=0.2).m("cryoturret_dark").rot(a, 0, 0).at(5.0 + r, -0.2, 0) for a in (0, 60, 120)]
    band = Torus(2.6, 0.6).m("cryoturret_dark").rot(0, 0, 90).at(8.4 + r, -0.2, 0)
    spike = prism(6, 1.9, 2.0, 3.0, 0.4).m("cryoturret_crystal").rot(0, 0, -90).at(10.0 + r, -0.2, 0)
    lens_m = "cryoturret_lens" if glow > 0.5 else "cryoturret_lens_dim"
    lens = Sphere(2.2).m(lens_m).at(3.6, 1.0, 4.6)
    lens_ring = Torus(2.3, 0.55).m("cryoturret_steel").rot(90, 0, 0).at(3.6, 1.0, 5.0)
    lamp_s = Sphere(0.95).m("cryoturret_lamp" if lamp else "cryoturret_lamp_off").at(-3.6, 3.2, 4.6)
    pipe = Capsule((-5.8, -2.6, 2.6), (-6.8, -5.0, 1.0), 0.8).m("cryoturret_dark")
    parts = [dome, collar, cap, cap2, *icic, sleeve, *fins, band, spike, lens, lens_ring, lamp_s, pipe]
    if charge > 0:
        parts.append(Sphere(0.9 + 1.4 * charge).m("cryoturret_hot").at(BARREL + 0.4 + r, -0.2, 0))
    return Union(*parts)


def parts(yaw=-24.0, aim=0.0, **kw):
    B = scaling(S) @ rot(0, -16, 0)
    H = trans(0, HEAD_Y * S, 0) @ rot(0, yaw, aim) @ scaling(S)
    return [Part(base().xform(B), name="base"), Part(head(**kw).xform(H), name="head")]


def muzzle_world(yaw=-24.0, aim=0.0):
    H = trans(0, HEAD_Y * S, 0) @ rot(0, yaw, aim) @ scaling(S)
    p = H @ np.array([BARREL + 1.0, -0.2, 0, 1.0])
    return p[0], p[1]


# ---------------------------------------------------------------------------------------------------------- animations

def idle(i):
    """Dormant scan: the head swings slowly, the lens breathes, the warning lamp blinks."""
    n = 8
    yaw = -24 + 14 * math.sin(TAU * i / n)
    spr = E.draw(parts(yaw=yaw, aim=-4, lamp=i < 4, glow=1.0 if i in (0, 1, 2, 6, 7) else 0.0))
    if i in (4, 5):
        puff(spr, 22 - (i - 4), 33 - 2 * (i - 4), 1 + (i - 4))
    return spr


ATTACK = [  # recoil, charge, lens glow, flash ring
    (2.2, 0.0, 1, 2), (1.4, 0.0, 1, 1), (0.6, 0.0, 0, 0), (0.2, 0.0, 0, 0), (0.0, 0.0, 0, 0), (0.0, 0.0, 0, 0),
    (0.0, 0.0, 1, 0), (0.0, 0.0, 1, 0), (0.0, 0.25, 1, 0), (0.0, 0.5, 1, 0), (0.0, 0.75, 1, 0), (0.0, 1.0, 1, 0),
]


def attack(i):
    """One 1.5 s firing cycle (the engine shoots every 1.5 s): fire + recoil (0), vent (2-5), charge (8-11)."""
    rec, ch, gl, ring = ATTACK[i]
    spr = E.draw(parts(yaw=-12, aim=0, recoil=rec, charge=ch, glow=gl, lamp=True))
    mx, my = muzzle_world(-12, 0)
    px, py = E.px(mx - rec, my)
    if ring:
        rr = 3 if ring == 2 else 4
        for a in range(0, 360, 30):
            x = int(round(px + 1 + rr * math.cos(math.radians(a))))
            y = int(round(py + rr * math.sin(math.radians(a)) * 1.2))
            if spr.get(x, y) < 0:
                spr.put(x, y, "white" if ring == 2 else "cyan:6", glow=True)
        sparkle(spr, px + 2, py, 2 if ring == 2 else 1)
    if i in (2, 3, 4):
        k = i - 2
        puff(spr, 23 - k, 36 - 2 * k, 1 + k)
        puff(spr, 41 + k, 41 - k, 1 + (k > 0))
    return spr


def hurt(i):
    rec = [1.6, 0.8, 0.2][i]
    spr = E.draw(parts(yaw=-30, aim=10 - 4 * i, recoil=rec, glow=0, lamp=i != 1), squash=(1.04, 0.96))
    if i == 0:
        flash(spr)
    if i < 2:
        for k, (x, y) in enumerate(((24, 32), (40, 30), (33, 25))):
            chip(spr, x - 2 * i, y - 3 * i, k)
    return spr


E.anim("idle", 6, "loop", 8, idle, "dormant scan")
E.anim("attack", 8, "loop", 12, attack, "one shot per loop (1.5 s): fire at 0, vent 2-5, charge 8-11")
E.anim("hurt", 12, "once", 3, hurt, "")
mx, my = muzzle_world(-12, 0)
E.point("muzzle", mx, my, "emitter tip (attack pose)")
E.note("glow: lens, crystal emitter, warning lamp, muzzle ring")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
