"""brute -- episode 4 heavy (box 40 x 50): a hulking Gloam assault android, barrel chest with a magenta reactor, huge
spiked pauldrons and gauntlets, a small sunken head; it lobs glowing grenades.

96 x 96 frames, anchor (48, 92). attack = the 0.5 s wind-up (grab, haul back over the shoulder) and the release at
frame 6 (the engine throws at 0.5 s from `muzzle`).
"""
import math

import numpy as np

from bake import (Box, Capsule, Chamfer, Cylinder, Extrude, Part, Sphere, Torus, Union, material, prism, rot, scaling,
                  trans)
from models._e34_common import TAU, Biped, Enemy, flash, puff, spark, sparkle, walk_feet

E = Enemy("brute", (96, 96), (48, 92), "Gloam brute (episode 4 heavy, faces right)", 4)

material("brute_grenade", ["magenta:3", "magenta:5", "magenta:6", "white"], style="emit", bands=[0.25, 0.55, 0.85],
         prio=3.0)
material("brute_reactor", ["magenta:3", "magenta:4", "magenta:5", "magenta:6", "white"], style="emit",
         bands=[0.2, 0.45, 0.7, 0.9], prio=2.5)

BP = Biped(thigh=8.2, shin=7.6, ankle_h=3.0, upper=9.0, fore=9.0, hip_w=6.0, sh_w=10.4, sh_y=15.6, neck_y=16.4,
           hip_drop=1.0, sh_x=0.6, sole=(-4.0, 5.6))
PY = BP.PELVIS_Y
YAW = -28.0
S = 1.1


def torso(core=1.0):
    barrel = Chamfer(7.6, 8.4, 8.0, 2.8).m("e34_alloy").at(0.6, 8.6, 0)
    chest = Extrude([(-1.0, 5.0), (6.4, 6.0), (9.4, 11.0), (7.4, 16.0), (-0.4, 16.6)], 6.4, r=0.8).m("e34_plate")
    ring = Torus(2.6, 0.8).m("e34_alloy").rot(0, 0, 90).at(9.0, 10.4, 0)
    core_s = prism(6, 2.2 + 0.3 * core, 0.6, 0.9, 0.9, twist=0).m("brute_reactor").rot(0, 0, -90).at(9.4, 10.4, 0)
    belly = Chamfer(5.4, 3.0, 6.2, 1.2).m("e34_joint").at(0.4, 1.4, 0)
    plates = Union(*[Chamfer(1.4, 1.0, 5.6, 0.4).m("e34_plate").at(5.2, 0.6 + 2.2 * k, 0) for k in range(2)])
    back = Chamfer(3.6, 6.4, 6.0, 1.4).m("e34_alloy").at(-7.4, 10.6, 0)
    exh = Union(*[Cylinder(1.0, 2.4, rr=0.3).m("e34_joint").at(-9.6, 17.0, z) for z in (2.4, -2.4)])
    glow = Union(*[Cylinder(0.7, 0.3).m("e34_magenta_dim").at(-9.6, 19.4, z) for z in (2.4, -2.4)])
    nades = Union(*[Sphere(1.2).m("e34_magenta_dim").at(4.0, 3.6, z) for z in (5.2, 2.6)])
    return Union(barrel, chest, ring, core_s, belly, plates, back, exh, glow, nades)


def head(visor="e34_magenta"):
    skull = Chamfer(3.4, 3.0, 3.2, 1.0).m("e34_plate").at(5.6, 2.6, 0)
    jaw = Chamfer(2.6, 1.6, 2.8, 0.6).m("e34_alloy").at(7.0, 0.4, 0)
    slit = Box(0.8, 0.75, 2.8, r=0.2).m(visor).at(8.8, 3.0, 0)
    horn = Extrude([(2.4, 4.4), (5.4, 5.0), (0.6, 8.0)], 0.6, r=0.2).m("e34_plate")
    neck = Chamfer(2.4, 2.0, 2.6, 0.6).m("e34_joint").at(3.0, 0.8, 0)
    return Union(neck, skull, jaw, slit, horn)


def pauldron(side):
    base = Extrude([(-5.2, -3.0), (4.6, -3.4), (6.0, 1.6), (2.4, 4.6), (-3.2, 4.8), (-6.0, 1.2)], 4.6, r=0.9) \
        .m("e34_plate")
    spikes = [Extrude([(-1.4, 0), (1.4, 0), (-0.4, 5.6)], 0.6, r=0.2).m("e34_alloy").rot(0, 0, a).at(x, 3.8, 0)
              for x, a in ((-2.6, 20), (1.2, 4))]
    trim = Box(5.0, 0.35, 4.8).m("e34_magenta_dim").rot(0, 0, 4).at(0.0, -2.6, 0)
    return Union(base, *spikes, trim).at(0, 1.2, 0)


def gauntlet(fist=True):
    arm = Chamfer(3.6, 4.6, 3.6, 1.2).m("e34_alloy").at(0, -4.0, 0)
    cuff = Chamfer(4.0, 1.4, 4.0, 0.8).m("e34_plate").at(0, -1.2, 0)
    knuck = Chamfer(3.4, 3.0, 3.6, 1.2).m("e34_plate").at(0.6, -BP.L_FORE - 0.4, 0) if fist else None
    stud = Box(0.3, 2.0, 0.4).m("e34_magenta_dim").at(3.6, -4.6, 0)
    return Union(arm, cuff, knuck, stud)


def thigh():
    return Union(Chamfer(3.6, BP.L_THIGH / 2 + 0.8, 3.8, 1.2).m("e34_alloy").at(0, -BP.L_THIGH / 2, 0),
                 Chamfer(1.2, 3.0, 3.0, 0.5).m("e34_plate").at(3.2, -3.4, 0))


def shin():
    return Union(Sphere(2.6).m("e34_plate"),
                 Chamfer(3.2, BP.L_SHIN / 2, 3.2, 1.0).m("e34_alloy").at(0, -BP.L_SHIN / 2 - 0.4, 0),
                 Extrude([(0.6, 1.6), (3.8, 0.4), (2.6, -6.4), (0.4, -7.0)], 2.6, r=0.5).m("e34_plate"))


def foot():
    return Extrude([(-4.0, -3.0), (6.6, -3.0), (5.0, -0.6), (1.6, 1.6), (-3.6, 1.6)], 3.4, r=0.6).m("e34_alloy")


SH = None


def shapes():
    global SH
    if SH is None:
        SH = dict(pelvis=Chamfer(5.4, 2.8, 6.4, 1.2).m("e34_alloy").at(0, -1.0, 0), pl=pauldron("l"), pr=pauldron("r"),
                  upper=Union(Sphere(3.0).m("e34_joint"), Capsule((0, 0, 0), (0, -BP.L_UPPER + 1.0, 0), 2.6)
                              .m("e34_alloy")),
                  fore=gauntlet(), thigh=thigh(), shin=shin(), foot=foot(), head=head())
    return SH


def pose(**kw):
    p = BP.pose(yaw=YAW, leg_ry=10.0, spine=(0, 0, -10), head=(0, 0, 8), sh_r=(-10, 0, 22), el_r=(0, 0, 22),
                sh_l=(10, 0, 12), el_l=(0, 0, 26), foot_r=(4.6, 0, 0), foot_l=(-4.2, 0, 0))
    p.update(kw)
    return p


def parts(p, core=1.0, grenade=0.0, visor="e34_magenta"):
    SS = shapes()
    W, _ = BP.solve(p)
    out = []

    def add(shape, joint, name, shade=0, M=None, zbias=0.0):
        X = scaling(S) @ (W[joint] if M is None else W[joint] @ M)
        out.append(Part(shape.xform(X), name=name, shade=shade, zbias=zbias))

    add(torso(core), "spine", "torso")
    add(SS["pelvis"], "pelvis", "pelvis")
    add(SS["head"] if visor == "e34_magenta" else head(visor), "head", "head")
    for side, sh in (("l", -1), ("r", 0)):
        add(SS["thigh"], f"hip_{side}", f"thigh_{side}", sh)
        add(SS["shin"], f"kn_{side}", f"shin_{side}", sh)
        add(SS["foot"], f"an_{side}", f"foot_{side}", sh)
    add(SS["upper"], "sh_l", "upper_l", -1)
    add(SS["fore"], "el_l", "fore_l", -1)
    add(SS["pl"], "sh_l", "pauldron_l", -1, M=rot(0, 0, -p["sh_l"][2] * 0.7))
    add(SS["upper"], "sh_r", "upper_r")
    add(SS["fore"], "el_r", "fore_r")
    add(SS["pr"], "sh_r", "pauldron_r", M=rot(0, 0, -p["sh_r"][2] * 0.7))
    if grenade > 0:
        g = Union(Sphere(2.0).m("brute_grenade"), Torus(2.0, 0.5).m("e34_alloy"))
        add(g, "el_r", "grenade", M=trans(2.6, -BP.L_FORE - 1.6, 1.2), zbias=10)
    return out


def hand(p):
    W, _ = BP.solve(p)
    q = scaling(S) @ W["el_r"] @ np.array([2.6, -BP.L_FORE - 1.6, 1.2, 1.0])
    return q[0], q[1]


def draw(p, **kw):
    return E.draw(parts(p, **kw))


# ---------------------------------------------------------------------------------------------------------- animations

WALK = walk_feet(8, 12.0, 3.8, duty=0.56)


def move(i):
    n = 8
    ph = TAU * i / n
    c = math.cos(ph)
    bob = -abs(math.cos(ph)) * 1.2
    p = pose(pelvis_y=PY - 1.0 + bob, spine=(0, -7 * c, -12), head=(0, 0, 10), sh_r=(-10, 0, 22 + 22 * c),
             el_r=(0, 0, 24 - 6 * c), sh_l=(10, 0, 14 - 20 * c), el_l=(0, 0, 26 + 6 * c),
             foot_r=WALK[i], foot_l=WALK[(i + n // 2) % n])
    spr = draw(p, core=0.6 + 0.4 * abs(c))
    if i in (0, 4):
        fx = (WALK[i][0] if i == 0 else WALK[(i + n // 2) % n][0]) * S
        x, y = E.px(fx + 2, 0)
        puff(spr, x + 6, y - 2, 2, ("grey:5", "grey:4", "grey:3"))
    return spr


def idle(i):
    n = 8
    b = 0.5 - 0.5 * math.cos(TAU * i / n)
    p = pose(pelvis_y=PY - 0.6 - 0.8 * b, spine=(0, 0, -10 - 2 * b), head=(0, [0, 0, 8, 12, 12, 4, 0, 0][i], 10 + b),
             sh_r=(-10, 0, 22 + 3 * b), sh_l=(10, 0, 12 - 3 * b))
    return draw(p, core=0.4 + 0.6 * b)


WIND = [  # sh_r rz, el_r, spine (ry, rz), grenade, lean x
    (30, 40, (0, -14), 0.0, 0.0),        # reach for the belt
    (20, 70, (-6, -12), 0.6, 0.0),       # grenade in hand
    (90, 80, (-14, -6), 1.0, -0.4),      # haul up
    (150, 70, (-22, 2), 1.0, -1.0),      # over the shoulder
    (176, 60, (-28, 6), 1.0, -1.6),      # fully back (anticipation)
    (178, 58, (-30, 7), 1.0, -1.8),      # hold
    (64, 10, (14, -18), 1.0, 1.4),       # release: arm whips forward
]


def attack(i):
    sh, el, (sry, srz), g, lean = WIND[i]
    p = pose(pelvis_x=lean, pelvis_y=PY - 1.4, spine=(0, sry, srz), head=(0, 0, 12), sh_r=(-12, 0, sh),
             el_r=(0, 0, el), sh_l=(10, 0, 40 if i >= 3 else 20), el_l=(0, 0, 50), foot_r=(6.0, 0, 0),
             foot_l=(-5.6, 0, 0))
    spr = draw(p, core=1.0, grenade=g)
    if g >= 1.0:
        x, y = E.px(*hand(p))
        sparkle(spr, x + 2, y - 3, 1 if i % 2 else 2, c1="white", c2="magenta:5")
    return spr


def hurt(i):
    keys = [(-1.6, 10, 18), (-1.0, 6, 12), (-0.4, 2, 6)]
    px_, sp, hd = keys[i]
    p = pose(pelvis_x=px_, pelvis_y=PY - 1.0, spine=(0, -8, sp - 10), head=(0, 0, hd), sh_r=(-10, 0, -10),
             sh_l=(10, 0, 30), foot_r=(6.0, 1.2, 14))
    spr = draw(p, core=0.2, visor="e34_magenta_dim")
    if i == 0:
        flash(spr)
    if i < 2:
        spark(spr, 52 - i, 44 + i, 2 - i, hot="magenta:6", cold="violet:5")
        spark(spr, 40, 52, 1, hot="magenta:6", cold="violet:5")
    return spr


E.anim("move", 10, "loop", 8, move, "heavy stomp, contact at 0 and 4")
E.anim("attack", 12, "once", 7, attack, "wind-up 0-5 (0.5 s), release at 6 (the engine throws at 0.5 s)")
E.anim("idle", 8, "loop", 8, idle, "")
E.anim("hurt", 12, "once", 3, hurt, "")
_rel = pose(pelvis_x=1.4, pelvis_y=PY - 1.4, spine=(0, 14, -18), head=(0, 0, 12), sh_r=(-12, 0, 64), el_r=(0, 0, 10),
            sh_l=(10, 0, 40), el_l=(0, 0, 50), foot_r=(6.0, 0, 0), foot_l=(-5.6, 0, 0))
hx, hy = hand(_rel)
E.point("muzzle", hx, hy, "throwing hand at the release (attack 6)")
E.note("glow: visor, chest reactor, grenade in hand, exhausts, trims")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
