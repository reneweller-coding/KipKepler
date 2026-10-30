"""jetpacker -- episode 4 gunship (box 26 x 36): a Gloam trooper (same armour, models/trooper.py) under a heavy
angular jetpack with two cyan plasma jets, legs dangling, rifle levelled.

64 x 64 frames, anchor (32, 54) = the box's bottom centre (the feet hang there; the jets reach below). fly = hovering,
attack = a shot (recoil, muzzle flash).
"""
import math

import numpy as np

from bake import Box, Chamfer, Cone, Cylinder, Extrude, RoundCone, Union, rot, trans
from models import trooper as T
from models._e34_common import TAU, Enemy, flash, puff, spark

E = Enemy("jetpacker", (64, 64), (32, 54), "Gloam jet trooper (episode 4 gunship, faces right)", 4, ground=False)

NOZZLES = ((-7.4, 2.8, 2.4), (-7.4, 2.8, -2.4))    # spine space


def pack():
    shell = Chamfer(3.0, 5.6, 4.4, 1.4).m("e34_alloy").at(-6.2, 7.6, 0)
    wing = Extrude([(-8.6, 11.0), (-4.0, 11.8), (-6.6, 14.4), (-11.6, 13.2)], 4.8, r=0.4).m("e34_plate")
    vents = Union(*[Box(0.3, 2.4, 0.3).m("e34_cyan_dim").at(-9.2, 8.0, z) for z in (-2.0, 0.0, 2.0)])
    noz = []
    for x, y, z in NOZZLES:
        noz.append(Cone(1.9, 1.3, 1.2).m("e34_joint").at(x, y - 0.6, z))
        noz.append(Cylinder(1.3, 0.25).m("e34_cyan").at(x, y - 1.9, z))
    straps = Chamfer(0.6, 4.2, 4.0, 0.3).m("e34_joint").at(-3.2, 8.0, 0)
    return Union(shell, wing, vents, straps, *noz)


def flames(length, flick):
    out = []
    for k, (x, y, z) in enumerate(NOZZLES):
        ln = length * (1.0 + 0.2 * math.sin(flick * 2.1 + k * 1.9))
        out.append(RoundCone((x, y - 1.8, z), (x - 1.4, y - 2.0 - ln, z), 2.0, 0.4).m("e34_flame_c"))
    return Union(*out)


def pose(bob=0.0, sway=0.0, lean=0.0, recoil=0.0, hot=False):
    p = T.pose(root=(0.0, 0.0), pelvis_y=T.PY - 4.4 + bob, spine=(0, 8, -6 + lean), head=(0, 0, 4 - lean * 0.5),
               foot_r=None, foot_l=None, leg_ry=6.0, recoil=recoil, hot=hot)
    p.update({"hip_r": (0, 0, 44 + sway), "kn_r": (0, 0, -84 - sway), "an_r": (0, 0, 46),
              "hip_l": (0, 0, 22 - sway), "kn_l": (0, 0, -62 + sway), "an_l": (0, 0, 40)})
    gx, gy, ang = T.AIM
    return T.hold(p, gx - recoil * 0.5, gy, ang - lean * 0.4)


def draw(p, length, flick):
    extra = [(pack(), "spine", "pack", 0, None), (flames(length, flick), "spine", "flames", 0, None)]
    ps, W = T.parts(p, extra)
    return E.draw(ps)


def fly(i):
    n = 8
    ph = TAU * i / n
    p = pose(bob=0.9 * math.sin(ph), sway=6 * math.sin(ph + 1.0), lean=2 * math.sin(ph))
    return draw(p, 10.5 + 2.0 * math.cos(ph * 2), i)


ATTACK = [(1.8, 4, 1, 2), (1.0, 3, 1, 1), (0.4, 1, 0, 0), (0.0, 0, 0, 0)]   # recoil, lean, hot, flash


def attack(i):
    rec, lean, hot, fl = ATTACK[i]
    p = pose(bob=0.2, sway=2, lean=lean, recoil=rec, hot=bool(hot))
    spr = draw(p, 12.0 - i * 0.6, i + 3)
    mx, my = T.muzzle_world(p)
    px, py = E.px(mx, my)
    if fl == 2:
        for d, c in ((0, "white"), (1, "white"), (2, "magenta:6"), (3, "magenta:5"), (4, "magenta:4")):
            for dy in range(-1 + (d > 2), 2 - (d > 2)):
                spr.put(px + d, py + dy, c, glow=True)
        spark(spr, px + 2, py - 3, 1, hot="magenta:6", cold="magenta:4")
    elif fl == 1:
        puff(spr, px + 1, py - 1, 1, ("violet:5", "violet:4", "violet:3"))
    return spr


def hurt(i):
    p = pose(bob=-0.6 * (2 - i), sway=14 - 5 * i, lean=-10 + 3 * i)
    p["visor"] = "e34_magenta_dim"
    spr = draw(p, [4.0, 7.0, 9.0][i], i)
    if i == 0:
        flash(spr)
    if i < 2:
        spark(spr, 30 - i, 20 + i, 2 - i, hot="magenta:6", cold="violet:5")
    return spr


E.anim("fly", 12, "loop", 8, fly, "hovering: bob, legs sway, jets flicker")
E.anim("attack", 14, "once", 4, attack, "one shot: flash at 0, recoil; the engine sets attack on the shot")
E.anim("hurt", 12, "once", 3, hurt, "")
mx, my = T.muzzle_world(pose())
E.point("muzzle", mx, my, "rifle muzzle (fly and attack)")
_W, _ = T.BP.solve(pose())
_q = _W["spine"] @ np.array([NOZZLES[0][0], NOZZLES[0][1] - 2.2, 0.0, 1.0])
E.point("thruster", _q[0], _q[1], "jet nozzles (particles)")
E.note("glow: visor, rifle cells and muzzle, the jets and nozzle rings")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
