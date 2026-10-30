"""lasereye -- episode 4 beamer (box 28 x 28): a Gloam sentinel eye, a magenta glass lens in an alloy pod held by a
yoke on an angular pylon; four blade petals open around the lens as it charges its beam.

64 x 64 frames, anchor (32, 60). The engine fires the beam from (x + 12, box centre = 14 px up): the lens centre
sits there. idle = watching, attack = charging (0.9 s) then firing (0.45 s).
"""
import math

import numpy as np

from bake import (Box, Capsule, Chamfer, Cylinder, Extrude, Part, Sphere, Torus, Union, material, prism, rot, trans)
from models._e34_common import TAU, Enemy, flash, spark, sparkle

E = Enemy("lasereye", (64, 64), (32, 60), "Gloam laser eye (episode 4 beamer, faces right; drawn on its base)", 4)

material("lasereye_lens", ["magenta:1", "magenta:2", "magenta:3", "magenta:4", "rose:6"], style="glass",
         bands=[-0.3, 0.15, 0.55], spec=0.92, glow=True, prio=2.0)
material("lasereye_lens_hot", ["magenta:3", "magenta:4", "magenta:5", "magenta:6", "white"], style="glass",
         bands=[-0.4, 0.0, 0.4], spec=0.85, glow=True, prio=2.0)
material("lasereye_core", ["magenta:6", "rose:7", "white"], style="emit", bands=[0.3, 0.7], prio=3.0)
material("lasereye_pupil", ["outline", "violet:0"], bands=[0.4], prio=2.5)

EYE_C = (12.0 - 4.4, 14.0)     # pod centre; the lens front reaches x = 12 at the box centre height
POD_R = 7.2


def pylon():
    base = Extrude([(-9.0, 0.0), (9.0, 0.0), (7.6, 2.6), (4.0, 4.0), (-4.0, 4.0), (-7.6, 2.6)], 5.4, r=0.5) \
        .m("e34_alloy")
    plate = Extrude([(-6.0, 2.6), (6.0, 2.6), (4.6, 3.6), (-4.6, 3.6)], 5.7, r=0.3).m("e34_plate")
    lights = Union(*[Box(0.8, 0.35, 0.3).m("e34_magenta_dim").at(-4.8 + 3.2 * k, 1.4, 5.5) for k in range(4)])
    column = Chamfer(2.0, 3.6, 2.0, 0.8).m("e34_joint").at(EYE_C[0] - 3.4, 6.6, 0)
    return Union(base, plate, lights, column)


def yoke(spread=0.0):
    out = []
    for z in (1, -1):
        arm = Extrude([(-2.4, 0.0), (2.0, 0.0), (1.2, 9.6), (-1.6, 11.4)], 0.7, r=0.25).m("e34_plate") \
            .at(EYE_C[0] - 1.0, 8.0, z * (POD_R + 0.9 + spread))
        out.append(arm)
    hub = Chamfer(3.0, 1.2, POD_R + 1.6, 0.5).m("e34_alloy").at(EYE_C[0] - 1.0, 8.6, 0)
    return Union(hub, *out)


def pod(charge=0.0, look=(0.0, 0.0), petals=0.3, hot=False, core=False):
    """Pod in eye space (centre at the origin, the lens looks along +x)."""
    shell = Sphere(POD_R).m("e34_alloy")
    back = Chamfer(3.2, 3.6, 3.6, 1.2).m("e34_plate").at(-4.4, 0, 0)
    fin = Extrude([(-6.0, 2.0), (-2.0, 5.2), (-4.0, 8.4), (-8.6, 5.4)], 0.6, r=0.2).m("e34_plate")
    ring = Torus(5.3, 1.0).m("e34_plate").rot(0, 0, 90).at(4.9, 0, 0)
    lens = Sphere(5.2).m("lasereye_lens_hot" if hot else "lasereye_lens").at(3.2, 0, 0)
    ly, lz = look
    pupil_r = 1.6 - 1.0 * charge
    parts = [shell, back, fin, ring, lens]
    if core:
        parts.append(Sphere(2.2 + 0.9 * charge).m("lasereye_core").at(7.0, 0, 0))
    else:
        parts.append(Box(0.6, pupil_r * 2.0, pupil_r * 0.7, r=0.2).m("lasereye_pupil").at(8.0, ly, lz))
    # four blade petals around the lens, opening (petals 0 = closed over the rim, 1 = flared back)
    for k in range(4):
        a = 45 + 90 * k
        blade = Extrude([(0.0, -1.4), (0.0, 1.4), (4.6, 0.0)], 0.45, r=0.15).m("e34_plate")
        blade = blade.rot(0, 0, 0).at(0, 0, 0)
        tilt = 70 - 80 * petals
        out = blade.rot(0, 0, tilt).at(4.4, 5.6, 0).rot(a, 0, 0)
        parts.append(out)
    return Union(*parts)


EYE_W = (8.6, 15.0)       # pod centre in the world; turned towards the viewer the lens centre lands near (12, 14)
EYE_YAW = -54.0


def cradle():
    collar = __import__("bake").Torus(POD_R + 0.2, 1.0).m("e34_plate").rot(0, 0, 90).at(-1.4, 0, 0)
    claws = [Extrude([(-3.0, 0.0), (0.6, 0.0), (2.4, 3.4), (-1.4, 2.2)], 0.6, r=0.2).m("e34_alloy")
             .at(-1.0, POD_R - 0.6, 0).rot(a, 0, 0) for a in (0, 120, 240)]
    return Union(collar, *claws)


def parts(charge=0.0, look=(0.0, 0.0), aim=(0.0, 0.0), petals=0.3, hot=False, core=False, shake=0.0):
    B = rot(0, -32, 0)
    P = [Part(pylon().xform(B), name="pylon")]
    E_ = trans(EYE_W[0] + shake, EYE_W[1], 0) @ rot(0, EYE_YAW + aim[0], aim[1])
    P.append(Part(cradle().xform(E_), name="cradle", shade=0))
    P.append(Part(pod(charge, look, petals, hot, core).xform(E_), name="pod"))
    return P


# ---------------------------------------------------------------------------------------------------------- animations

def idle(i):
    """Watching: the pod sweeps slowly, the pupil slit darts, the lens pulses."""
    n = 8
    t = i / n
    aim = (-10 * math.sin(TAU * t), 3 * math.sin(2 * TAU * t))
    look = (0.6 * math.sin(TAU * t + 1), 0.8 * math.cos(TAU * t))
    return E.draw(parts(look=look, aim=aim, petals=0.25 + 0.1 * math.sin(TAU * t), hot=i in (0, 1)))


N_CHARGE, N_FIRE = 11, 5


def attack(i):
    """Charge (0-10, 0.9 s): petals open, the lens heats, sparks gather. Fire (11-15, 0.45 s): white-hot core."""
    if i < N_CHARGE:
        u = i / (N_CHARGE - 1)
        spr = E.draw(parts(charge=u, petals=0.3 + 0.7 * u, hot=u > 0.4, core=u > 0.7))
        cx, cy = E.px(12.0, 14.0)
        for k in range(3):
            a = TAU * (k / 3 + u * 0.8)
            r = 10 * (1 - u) + 3
            sparkle(spr, int(round(cx + r * math.cos(a))), int(round(cy + r * math.sin(a) * 0.8)),
                    1 if (i + k) % 2 else 0, c1="white", c2="magenta:5")
        return spr
    k = i - N_CHARGE
    shake = [-0.8, -0.4, -0.6, -0.3, 0.0][k]
    spr = E.draw(parts(charge=1.0, petals=1.05, hot=True, core=True, shake=shake))
    cx, cy = E.px(12.0, 14.0)
    for d in range(0, 8):              # the beam's root (the engine draws the beam itself)
        for dy in (-1, 0, 1):
            c = "white" if abs(dy) == 0 or d < 2 else "magenta:6"
            if d > 5 and dy:
                continue
            spr.put(cx + d, cy + dy, c, glow=True)
    spark(spr, cx + 2, cy - 4 + (k % 2) * 8, 1, hot="magenta:6", cold="magenta:4")
    return spr


def hurt(i):
    spr = E.draw(parts(aim=(18 - 6 * i, 10 - 4 * i), petals=0.1, look=(0.8, 0.0)))
    if i == 0:
        flash(spr)
    if i < 2:
        spark(spr, 30 - i, 26 + i, 2 - i, hot="magenta:6", cold="violet:5")
    return spr


E.anim("idle", 6, "loop", 8, idle, "watching")
E.anim("attack", 12, "loop", N_CHARGE + N_FIRE, attack,
       "charge 0-10 (0.9 s), fire 11-15 (0.45 s); one loop = one engine charge+beam cycle")
E.anim("hurt", 12, "once", 3, hurt, "")
E.point("muzzle", 12, 14, "lens centre = the engine's beam origin (x + 12, box centre)")
E.note("glow: lens, core, petal sparks, base lights; the beam itself is drawn by the engine")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
