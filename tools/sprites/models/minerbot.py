"""minerbot -- episode 3 shooter (box 26 x 38): a tracked mining robot in orange and yellow colony livery, a spinning
drill arm, a shoulder blaster, a cab with a cyan visor and a headlamp.

64 x 64 frames, anchor (32, 60). Model space: x forward, y up, z towards the viewer (the drill arm is the near side),
yawed towards the viewer.
"""
import math

import numpy as np

from bake import (Box, Capsule, Chamfer, Cone, Cylinder, Paint, Part, Sphere, Torus, Union, material, rot, scaling,
                  trans)
from models._e34_common import TAU, Enemy, chip, flash, puff, spark

E = Enemy("minerbot", (64, 64), (32, 60), "mining robot (episode 3 shooter, faces right)", 3)

material("minerbot_orange", ["orange:1", "orange:2", "orange:3", "orange:4", "orange:5"],
         bands=[-0.45, -0.1, 0.3, 0.75], line_lit="orange:1")
material("minerbot_yellow", ["orange:2", "orange:3", "yellow:3", "yellow:4", "yellow:5", "yellow:6"],
         bands=[-0.5, -0.2, 0.15, 0.5, 0.82], line_lit="brown:1")
material("minerbot_dark", ["violet:0", "slate:1", "slate:2", "slate:3", "slate:4"], bands=[-0.4, 0.0, 0.4, 0.8])
material("minerbot_tread", ["violet:0", "slate:1", "slate:2", "grey:3"], bands=[-0.2, 0.3, 0.75])
material("minerbot_lug", ["outline", "violet:0", "slate:1"], bands=[0.0, 0.6])
material("minerbot_steel", ["slate:2", "steel:3", "steel:4", "steel:5", "steel:6", "white"], style="metal",
         bands=[-0.4, 0.0, 0.35, 0.7], spec=0.9)
material("minerbot_drill_dark", ["slate:1", "slate:2", "steel:3", "steel:4"], bands=[-0.3, 0.2, 0.7])
material("minerbot_visor", ["blue:2", "cyan:3", "cyan:4", "cyan:5", "white"], style="glass", bands=[-0.3, 0.15, 0.6],
         spec=0.93, line="outline")
material("minerbot_lamp", ["yellow:5", "yellow:6", "white"], style="emit", bands=[0.3, 0.75], prio=3.0)
material("minerbot_red", ["red:4", "red:6"], style="emit", bands=[0.5], prio=3.0)
material("minerbot_red_off", ["crimson:1", "crimson:2"], bands=[0.4], prio=3.0)
material("minerbot_muzzle", ["orange:4", "yellow:5", "yellow:6", "white"], style="emit", bands=[0.3, 0.6, 0.85],
         prio=3.0)
material("minerbot_muzzle_off", ["brown:2", "orange:3", "orange:4"], bands=[0.0, 0.6], prio=2.0)

YAW = -26.0
S = 1.14


def tracks(phase):
    """Two track loops (z = +-5) with lugs that crawl back by `phase` (0..1 = one lug pitch)."""
    out = []
    for z, sh in ((5.2, 0), (-5.2, -1)):
        loop = Box(10.6, 4.0, 2.4, r=3.9).m("minerbot_tread").at(0, 4.2, z)
        lugs = Union(*[Box(0.55, 6, 3.2).rot(0, 0, 0).at(-12 + 2.4 * (k + phase), 4.2, z) for k in range(11)])
        loop = Paint(loop, lugs, "minerbot_lug")
        out.append((loop, sh))
        if z > 0:
            hubs = Union(*[Cylinder(1.5, 0.5, rr=0.3).m("minerbot_yellow").rot(90, 0, 0).at(x, 4.2, z + 2.3)
                           for x in (-6.6, 0.0, 6.6)])
            caps = Union(*[Cylinder(0.6, 0.6).m("minerbot_dark").rot(90, 0, 0).at(x, 4.2, z + 2.6)
                           for x in (-6.6, 0.0, 6.6)])
            out.append((Union(hubs, caps), 0))
    return out


def chassis(bob=0.0):
    hull = Chamfer(8.2, 5.4, 5.8, 1.6).m("minerbot_orange").at(0, 13.6 + bob, 0)
    stripes = Union(*[Box(0.7, 3.6, 7).rot(0, 0, 40).at(-6 + 2.2 * k, 9.6 + bob, 0) for k in range(7)])
    fender = Paint(Box(11.6, 1.2, 7.4, r=0.6).m("minerbot_yellow").at(0, 9.0 + bob, 0), stripes, "minerbot_dark")
    grill = Union(*[Box(0.35, 2.8, 0.4).m("minerbot_dark").at(8.3, 13.4 + bob, -3 + 1.5 * k) for k in range(5)])
    pack = Box(3.0, 4.6, 4.6, r=1.2).m("minerbot_dark").at(-8.6, 14.4 + bob, 0)
    pipe = Capsule((-9.0, 18.6 + bob, -2.0), (-9.4, 22.4 + bob, -2.4), 0.8).m("minerbot_steel")
    return Union(hull, fender, grill, pack, pipe)


def cab(bob=0.0, look=0.0, lamp=True, blink=False):
    C = trans(0.6, 24.0 + bob, 0) @ rot(0, look, 0)
    shell = Box(6.4, 4.6, 5.4, r=2.0).m("minerbot_yellow")
    visor = Box(2.0, 2.0, 4.4, r=0.9).m("minerbot_visor" if not blink else "minerbot_dark").at(5.0, 0.6, 0)
    brow = Box(1.6, 0.6, 5.0, r=0.3).m("minerbot_dark").at(5.2, 3.0, 0)
    lamp_h = Cylinder(1.5, 0.9, rr=0.4).m("minerbot_dark").rot(0, 0, -90).at(3.6, 4.6, 3.6)
    lamp_g = Cylinder(1.2, 0.4).m("minerbot_lamp" if lamp else "minerbot_drill_dark").rot(0, 0, -90).at(4.7, 4.6, 3.6)
    ant = Capsule((-3.6, 4.0, -2.4), (-4.6, 9.4, -2.6), 0.35).m("minerbot_dark")
    tip = Sphere(0.9).m("minerbot_red" if lamp else "minerbot_red_off").at(-4.6, 9.6, -2.6)
    neck = Cylinder(3.0, 1.6).m("minerbot_dark").at(0, -4.6, 0)
    return Union(shell, visor, brow, lamp_h, lamp_g, ant, tip, neck).xform(C)


DRILL_L = 11.0


def drill_arm(spin, reach=0.0, bob=0.0):
    sh = np.array([1.6, 18.6 + bob, 7.2])
    el = np.array([5.8 + reach, 14.0 + bob, 8.2])
    upper = Union(Sphere(2.4).m("minerbot_orange").at(*sh), Capsule(sh, el, 1.7).m("minerbot_dark"))
    # drill housing and bit along +x from the elbow
    hous = Cylinder(2.6, 2.0, rr=0.7).m("minerbot_orange").rot(0, 0, -90).at(el[0] + 1.6, el[1], el[2])
    ring = Torus(2.4, 0.55).m("minerbot_dark").rot(0, 0, 90).at(el[0] + 3.7, el[1], el[2])
    bit = Cone(2.9, 0.25, DRILL_L / 2).m("minerbot_steel")
    bit = Paint(bit, Union(*[Box(4, 0.5, 4).rot(30, spin + 72 * k, 0).at(0, -4.2 + 1.9 * k, 0) for k in range(6)]),
                "minerbot_drill_dark")
    bit = bit.rot(0, 0, -90).at(el[0] + 4.0 + DRILL_L / 2, el[1], el[2])
    return Union(upper, hous, ring, bit)


GUN_PIVOT = (-1.2, 30.4, -0.8)
GUN_L = 9.6


def gun(pitch, recoil=0.0, hot=False):
    G = trans(*GUN_PIVOT) @ rot(0, 0, pitch)
    mount = Box(2.4, 1.6, 2.2, r=0.7).m("minerbot_dark").at(0, -0.6, 0)
    body = Box(3.8, 1.9, 2.0, r=0.8).m("minerbot_orange").at(2.0 - recoil, 0.6, 0)
    barrel = Cylinder(0.95, GUN_L / 2 - 1.2, rr=0.3).m("minerbot_steel").rot(0, 0, -90).at(
        GUN_L / 2 + 1.0 - recoil, 0.2, 0)
    tip = Cylinder(1.2, 0.7, rr=0.3).m("minerbot_muzzle" if hot else "minerbot_muzzle_off").rot(0, 0, -90).at(
        GUN_L + 0.4 - recoil, 0.2, 0)
    return Union(mount, body, barrel, tip).xform(G)


def muzzle_world(pitch, bob=0.0):
    W = rot(0, YAW, 0) @ scaling(S) @ trans(0, bob, 0) @ trans(*GUN_PIVOT) @ rot(0, 0, pitch)
    p = W @ np.array([GUN_L + 1.4, 0.2, 0, 1.0])
    return p[0], p[1]


def parts(phase=0.0, spin=0.0, bob=0.0, look=0.0, pitch=26.0, recoil=0.0, hot=False, lamp=True, blink=False,
          reach=0.0, tilt=0.0):
    B = rot(0, YAW, 0) @ scaling(S)
    U = B @ rot(0, 0, tilt)
    P = []
    for shape, sh in tracks(phase):
        P.append(Part(shape.xform(B), name="track", shade=sh))
    P.append(Part(chassis(bob).xform(U), name="chassis"))
    P.append(Part(gun(pitch, recoil, hot).xform(U @ trans(0, bob, 0)), name="gun"))
    P.append(Part(cab(bob, look, lamp, blink).xform(U), name="cab"))
    P.append(Part(drill_arm(spin, reach, bob).xform(U), name="drill"))
    return P


# ---------------------------------------------------------------------------------------------------------- animations

def move(i):
    n = 8
    bob = 0.35 * math.sin(2 * TAU * i / n)
    return E.draw(parts(phase=i / n, spin=45 * i, bob=bob, tilt=0.8 * math.sin(TAU * i / n), lamp=i % 4 != 3,
                        pitch=26 + 3 * math.sin(TAU * i / n)))


def idle(i):
    n = 8
    look = [0, 0, -14, -20, -20, -6, 8, 4][i]
    return E.draw(parts(spin=25 * i, look=look, lamp=i not in (3, 7), blink=i == 5, pitch=26 - look * 0.3))


ATTACK = [  # pitch, recoil, hot, tilt, flash
    (24, 0, 0, 0.0, 0), (14, 0, 0, 0.4, 0), (4, 0, 0, 0.8, 0), (0, 0, 1, 1.0, 0),
    (0, 2.2, 1, -1.6, 2), (0, 1.2, 1, -0.8, 1), (0, 0.4, 0, 0.0, 0), (0, 0, 0, 0.0, 0),
]


def attack(i):
    """Swing the shoulder blaster down to level (0-3, the barrel heats), fire (4) with recoil, settle."""
    pitch, rec, hot, tilt, fl = ATTACK[i]
    spr = E.draw(parts(spin=45 * i, pitch=pitch, recoil=rec, hot=bool(hot), tilt=tilt, reach=-1.0))
    mx, my = muzzle_world(pitch)
    px, py = E.px(mx - rec, my)
    if fl == 2:
        for d, c in ((0, "white"), (1, "yellow:6"), (2, "yellow:5"), (3, "orange:4")):
            for dy in range(-1 + (d > 1), 2 - (d > 1)):
                spr.put(px + d, py + dy, c, glow=True)
        spark(spr, px + 2, py - 3, 1)
        spark(spr, px + 1, py + 3, 1)
    elif fl == 1:
        puff(spr, px + 1, py - 1, 1, ("grey:6", "grey:5", "grey:4"))
    return spr


def hurt(i):
    keys = [(-4, 1, 0.0), (-2.5, 0, 0.2), (-1, 0, 0.0)]
    tilt, blink, bob = keys[i]
    spr = E.draw(parts(tilt=tilt, blink=bool(blink), lamp=i == 2, pitch=40, look=12, bob=bob))
    if i == 0:
        flash(spr)
    if i < 2:
        spark(spr, 24 - i, 28 - 2 * i, 2 - i)
        spark(spr, 40, 34 - i, 1)
    return spr


E.anim("move", 12, "loop", 8, move, "treads crawl, drill spins")
E.anim("idle", 6, "loop", 8, idle, "looks around")
E.anim("attack", 10, "once", 8, attack, "aim 0-3, fire at 4 (0.4-0.5 s, the engine shoots at 0.45 s)")
E.anim("hurt", 12, "once", 3, hurt, "")
mx, my = muzzle_world(0)
E.point("muzzle", mx, my, "shoulder blaster tip, level")
E.note("glow: headlamp, antenna light, blaster tip and flash")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
