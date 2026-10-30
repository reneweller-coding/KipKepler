"""crystalcrab -- episode 3 walker (box 30 x 20): a comet crab with violet crystal growths on its frosted shell.

64 x 64 frames, anchor (32, 60) = the box's bottom centre on the ground line. Seen three-quarter from the front
(crabs walk sideways), the face turned towards the walking direction (right). Model space before the yaw: the face
looks along +z, the legs fan out along +-x.
"""
import math

import numpy as np

from bake import Capsule, Ellipsoid, Part, RoundCone, Sphere, Union, material, prism, rot, trans
from models._e34_common import TAU, Enemy, chip, flash, sparkle

E = Enemy("crystalcrab", (64, 64), (32, 60), "crystal crab (episode 3 walker, faces right)", 3)

material("crystalcrab_shell", ["violet:1", "blue:2", "blue:3", "ice:3", "ice:4", "ice:5", "ice:6"],
         bands=[-0.55, -0.25, 0.05, 0.35, 0.62, 0.86], line_lit="blue:1")
material("crystalcrab_belly", ["violet:1", "violet:2", "slate:3", "slate:4"], bands=[-0.35, 0.1, 0.6])
material("crystalcrab_leg", ["violet:1", "blue:2", "blue:3", "ice:4", "ice:5"], bands=[-0.45, -0.05, 0.4, 0.8])
material("crystalcrab_tip", ["ice:4", "ice:5", "ice:6", "ice:7"], bands=[-0.3, 0.2, 0.7], line_lit="blue:1")
material("crystalcrab_claw", ["violet:2", "blue:3", "ice:4", "ice:5", "ice:6", "white"],
         bands=[-0.5, -0.15, 0.25, 0.6, 0.88], line_lit="blue:1")
material("crystalcrab_crystal", ["violet:1", "violet:2", "violet:3", "purple:4", "violet:5", "purple:6", "white"],
         bands=[-0.45, -0.15, 0.12, 0.38, 0.62, 0.86], glow=True, line="violet:0", line_lit="violet:1")
material("crystalcrab_eye", ["cyan:5", "cyan:6", "white"], style="emit", bands=[0.35, 0.8], prio=3.0)
material("crystalcrab_stalk", ["violet:1", "blue:2", "blue:3"], bands=[-0.2, 0.5])

YAW = 22.0
HIP_Z = (4.2, 0.8, -2.6)            # front, middle, back leg roots (z)
FOOT = [(15.2, 6.4), (16.4, 0.6), (15.0, -5.6)]   # (x out, z) home positions of the feet


def leg(s, j, dx, lift):
    """One leg of side s (+1 right, -1 left), j = 0 front .. 2 back; the foot moved by dx along x, lifted."""
    hip = np.array([s * 8.6, 7.4, HIP_Z[j]])
    fx, fz = FOOT[j]
    foot = np.array([s * fx + dx, lift, fz])
    mid = (hip + foot) / 2
    out = np.array([s, 0, 0.35 * (fz / 6.0)])
    knee = mid + np.array([0, 4.6 + 0.4 * lift, 0]) + out * 1.6
    m = "crystalcrab_leg"
    return Union(Capsule(hip, knee, 1.35).m(m), RoundCone(knee, foot + np.array([0, 0.7, 0]), 1.15, 0.55).m(m),
                 RoundCone(foot + np.array([0, 1.8, 0]), foot + np.array([0, 0.45, 0]), 0.75, 0.4)
                 .m("crystalcrab_tip"))


def claw(s, open_a, lift, big):
    """A pincer on a two-part arm, raised to the front. open_a in degrees, lift raises the whole claw."""
    k = 1.3 if big else 1.0
    sh = np.array([s * 5.4, 8.4, 6.8])
    el = np.array([s * 10.2, 10.6 + 0.4 * lift, 9.4])
    wr = np.array([s * 11.6, 13.2 + lift, 10.0])
    arm = Union(Capsule(sh, el, 1.25).m("crystalcrab_leg"), Capsule(el, wr, 1.35 * k).m("crystalcrab_leg"))
    a = math.radians(open_a)
    palm = Ellipsoid(2.5 * k, 2.6 * k, 1.9 * k).m("crystalcrab_claw").at(0, 1.4 * k, 0)
    fixed = RoundCone((0.9 * k, 3.0 * k, 0), (0.7 * k, 6.6 * k, 0), 1.35 * k, 0.45).m("crystalcrab_claw")
    tipx, tipy = -0.9 * k - 3.6 * k * math.sin(a), 2.6 * k + 3.6 * k * math.cos(a)
    move = RoundCone((-0.9 * k, 2.6 * k, 0), (tipx, tipy, 0), 1.15 * k, 0.4).m("crystalcrab_claw")
    pincer = Union(palm, fixed, move)
    # the hinge side towards the body; tilt the pincer outwards and open it across the picture
    M = trans(*wr) @ rot(0, -s * 25 - YAW * 0.6, -s * 22)
    if s < 0:
        M = M @ np.diag([-1.0, 1, 1, 1])
    return Union(arm, pincer.xform(M))


CRYSTALS = [  # (x, y, z, rz, rx, scale)
    (-3.0, 12.2, -2.8, 14, -8, 1.6),
    (2.6, 12.0, -3.6, -22, -12, 1.2),
    (-8.6, 10.4, -1.2, 44, 4, 0.85),
    (0.2, 12.8, 1.0, -6, 16, 0.7),
    (7.8, 10.0, -0.6, -52, 6, 0.75),
]


def crystals(spin=0.0):
    out = []
    for x, y, z, rz, rx, s in CRYSTALS:
        p = prism(6, 2.5 * s, 2.6 * s, 3.4 * s, 1.0, twist=spin + 15 * x).m("crystalcrab_crystal")
        out.append(p.rot(rx, 0, rz).at(x, y + 2.6 * s, z))
    return Union(*out)


def shell():
    body = Ellipsoid(12.4, 5.8, 9.0).m("crystalcrab_shell").at(0, 9.4, 0)
    belly = Ellipsoid(10.4, 3.2, 7.6).m("crystalcrab_belly").at(0, 6.8, 0.4)
    rim = [Sphere(1.25).m("crystalcrab_tip").at(math.sin(a) * 11.0, 9.0, math.cos(a) * 8.2)
           for a in np.radians([-62, -38, 38, 62])]
    mouth = Ellipsoid(3.4, 1.4, 1.2).m("crystalcrab_belly").at(0, 7.4, 8.0)
    return Union(body, belly, mouth, *rim)


def eyes(blink=False, look=0.0):
    out = []
    for s in (1, -1):
        b = np.array([s * 2.3, 10.4, 7.0])
        t = np.array([s * 3.0 + look, 14.4, 7.8])
        out.append(Capsule(b, t, 0.6).m("crystalcrab_stalk"))
        out.append(Ellipsoid(1.4, 0.5 if blink else 1.35, 1.3).m("crystalcrab_stalk" if blink else "crystalcrab_eye")
                   .at(*t))
    return Union(*out)


def parts(body_y=0.0, roll=0.0, feet=None, claws=(20, 20), claw_lift=(0, 0), blink=False, look=0.0, yaw=YAW,
          root=(0.0, 0.0), pitch=0.0):
    feet = feet or {}
    B = trans(root[0], root[1], 0) @ rot(0, yaw, 0)
    body = trans(0, body_y, 0) @ rot(pitch, 0, roll)
    P = []
    P.append(Part(shell().xform(B @ body), name="shell"))
    P.append(Part(crystals().xform(B @ body), name="crystals"))
    P.append(Part(eyes(blink, look).xform(B @ body), name="eyes"))
    for s in (1, -1):
        for j in range(3):
            dx, lift = feet.get((s, j), (0.0, 0.0))
            far = s < 0 and j == 2 or (s > 0 and j == 2)
            P.append(Part(leg(s, j, dx, lift).xform(B), name=f"leg{s}{j}", shade=-1 if far else 0))
        big = s > 0
        k = 0 if s > 0 else 1
        P.append(Part(claw(s, claws[k], claw_lift[k], big).xform(B @ body), name=f"claw{s}"))
    return P


# ---------------------------------------------------------------------------------------------------------- animations

def gait(i, n=8, stride=3.6, lift=2.6):
    """Tripod scuttle: legs (R0, L1, R2) and (L0, R1, L2) alternate. Returns {(s, j): (dx, lift)}."""
    feet = {}
    for s in (1, -1):
        for j in range(3):
            grp = (j + (0 if s > 0 else 1)) % 2
            ph = (i / n + 0.5 * grp) % 1.0
            if ph < 0.5:
                u = ph / 0.5
                feet[(s, j)] = (stride / 2 - stride * u, 0.0)
            else:
                u = (ph - 0.5) / 0.5
                feet[(s, j)] = (-stride / 2 + stride * (u * u * (3 - 2 * u)), lift * math.sin(math.pi * u))
    return feet


def move(i):
    n = 8
    feet = gait(i, n)
    bob = 0.55 * math.cos(2 * TAU * i / n)
    roll = 3.5 * math.sin(TAU * i / n)
    cl = (14 + 10 * math.sin(TAU * i / n), 14 + 10 * math.sin(TAU * i / n + 2))
    lift = (0.8 * math.sin(TAU * i / n), 0.8 * math.sin(TAU * i / n + math.pi))
    spr = E.draw(parts(body_y=0.4 + bob, roll=roll, feet=feet, claws=cl, claw_lift=lift))
    return spr


def idle(i):
    n = 8
    b = 0.5 - 0.5 * math.cos(TAU * i / n)
    snap = [10, 34, 6, 6, 18, 18, 18, 12][i]
    snap2 = [18, 18, 18, 12, 10, 34, 6, 6][i]
    spr = E.draw(parts(body_y=-0.5 * b, claws=(snap, snap2), claw_lift=(0.6 * b, -0.4 * b), blink=i == 5,
                       look=[0, 0, 0.4, 0.6, 0.6, 0, -0.4, 0][i]))
    if i in (2, 3):
        sparkle(spr, 26 + i, 38 - i, 1 if i == 2 else 2)
    return spr


def attack(i):
    """Claw snap: rear back with both claws high (anticipation), lunge, snap shut, recover."""
    keys = [  # body_y, pitch, root x, claws open, claw lift
        (0.0, 0, 0.0, 20, 0.0),
        (-0.6, -10, -1.2, 38, 2.4),
        (-0.8, -14, -1.6, 44, 3.0),
        (0.6, 12, 2.4, 40, -0.6),
        (0.4, 14, 2.8, 2, -1.0),
        (0.2, 8, 1.6, 4, -0.4),
        (0.0, 2, 0.6, 14, 0.0),
    ]
    by, pitch, rx, op, cl = keys[i]
    spr = E.draw(parts(body_y=by, pitch=pitch, root=(rx, 0), claws=(op, op), claw_lift=(cl, cl)))
    if i == 4:
        sparkle(spr, E.px(17, 13)[0], E.px(17, 13)[1], 2)
    return spr


def hurt(i):
    keys = [(-1.6, 1.0, -9, 40), (-1.0, 0.4, -5, 30), (-0.3, 0.0, -2, 22)]
    rx, by, roll, op = keys[i]
    spr = E.draw(parts(root=(rx, 0), body_y=by, roll=roll, claws=(op, op), claw_lift=(1.4, 1.4), blink=True))
    if i == 0:
        flash(spr)
    if i < 2:
        for k, (x, y) in enumerate(((22, 40), (40, 37), (30, 34))):
            chip(spr, x - 2 * i, y - 3 * i, k)
    return spr


E.anim("move", 14, "loop", 8, move, "tripod scuttle, contact at 0 and 4")
E.anim("idle", 8, "loop", 8, idle, "claws snapping, crystal glint")
E.anim("attack", 14, "once", 7, attack, "claw snap: rear back (1-2), lunge and snap (3-4)")
E.anim("hurt", 12, "once", 3, hurt, "knocked back, ice chips")
E.note("glow: eyes and the crystal growths")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
