"""trooper -- episode 4 shooter (box 24 x 42): a Gloam soldier android, black-violet alloy with lighter plates, an
angular wedge helmet with a magenta visor slit, a long rifle with cyan cells.

64 x 64 frames, anchor (32, 60). The jetpacker (models/jetpacker.py) reuses this armour.
Model space: x forward, y up, z towards the viewer (the right side, near, holds the rifle grip).
"""
import math

import numpy as np

from bake import (Box, Capsule, Chamfer, Cylinder, Extrude, Paint, Part, Sphere, Union, ik2, material, prism, rot,
                  trans)
from models._e34_common import TAU, Biped, Enemy, flash, puff, spark, walk_feet

E = Enemy("trooper", (64, 64), (32, 60), "Gloam trooper (episode 4 shooter, faces right)", 4)

material("trooper_glint", ["white"], style="flat", prio=3.0, glow=True)

BP = Biped(thigh=8.0, shin=7.6, ankle_h=2.2, upper=5.6, fore=5.4, hip_w=2.6, sh_w=4.4, sh_y=11.2, neck_y=13.2,
           hip_drop=0.6, sh_x=-0.2, sole=(-2.2, 3.6))
PY = BP.PELVIS_Y
YAW = -30.0


# ---------------------------------------------------------------------------------------------------------- shapes

def helmet(visor="e34_magenta", glint=None):
    """Wedge helmet around the head joint: a sharp brow pointing forward, a swept crest behind."""
    prof = [(-3.0, -1.6), (2.4, -2.0), (4.2, 0.4), (4.4, 2.0), (2.6, 4.2), (-1.0, 4.8), (-4.2, 3.4), (-4.0, 0.4)]
    shell = Extrude(prof, 2.9, r=0.7).m("e34_alloy").at(0, 1.0, 0)
    face = Chamfer(1.4, 1.6, 2.4, 0.6).m("e34_plate").at(3.2, 0.2, 0)
    slit = Box(0.7, 0.55, 2.7, r=0.15).m(visor).at(4.2, 1.9, 0)
    if glint is not None:
        slit = Paint(slit, Box(1.2, 1.2, 0.5).at(4.2, 1.9, glint), "trooper_glint")
    crest = Extrude([(-1.0, 4.0), (1.8, 4.6), (-3.0, 7.2), (-5.4, 6.6)], 0.5, r=0.2).m("e34_plate").at(0, 0.6, 0)
    jaw = Chamfer(1.8, 1.0, 2.0, 0.5).m("e34_joint").at(1.0, -1.4, 0)
    return Union(shell, face, slit, crest, jaw)


def torso(core="e34_magenta"):
    chest = Chamfer(3.4, 4.0, 4.4, 1.6).m("e34_alloy").at(0.2, 8.0, 0)
    plate = Chamfer(1.2, 3.4, 3.4, 0.9).m("e34_plate").at(3.0, 8.6, 0)
    core_l = Box(0.4, 2.4, 0.6, r=0.15).m(core).at(4.1, 8.4, 0)
    belly = Chamfer(2.4, 2.4, 3.2, 0.8).m("e34_joint").at(0.0, 3.0, 0)
    back = Chamfer(1.6, 3.2, 3.2, 0.8).m("e34_plate").at(-3.6, 8.6, 0)
    collar = Chamfer(2.4, 0.9, 3.0, 0.5).m("e34_alloy").at(0.4, 12.4, 0)
    return Union(chest, plate, core_l, belly, back, collar)


def pelvis():
    return Union(Chamfer(2.8, 1.8, 3.6, 0.8).m("e34_alloy").at(0, -0.4, 0),
                 Chamfer(0.9, 1.6, 3.0, 0.4).m("e34_plate").at(2.6, -0.8, 0))


def pauldron():
    p = Extrude([(-3.2, -1.6), (3.0, -1.8), (3.6, 1.0), (1.0, 2.6), (-1.6, 4.4), (-3.4, 2.0)], 2.3, r=0.5)         .m("e34_plate")
    edge = Box(2.4, 0.3, 2.4).m("e34_magenta_dim").rot(0, 0, 8).at(0.6, -1.2, 0)
    return Union(p, edge).at(0, 0.8, 0)


def upper_arm():
    return Capsule((0, -0.4, 0), (0, -BP.L_UPPER + 0.6, 0), 1.25).m("e34_alloy")


def forearm():
    g = Chamfer(1.5, 2.2, 1.5, 0.6).m("e34_plate").at(0, -2.4, 0)
    hand = Sphere(1.2).m("e34_joint").at(0, -BP.L_FORE, 0)
    return Union(Sphere(1.1).m("e34_joint"), g, hand)


def thigh():
    return Union(Capsule((0, 0, 0), (0, -BP.L_THIGH + 1.0, 0), 1.75).m("e34_alloy"),
                 Chamfer(1.0, 2.4, 1.6, 0.4).m("e34_plate").at(1.4, -2.8, 0))


def shin():
    return Union(Sphere(1.45).m("e34_plate"),
                 Chamfer(1.7, BP.L_SHIN / 2, 1.6, 0.6).m("e34_alloy").at(0, -BP.L_SHIN / 2, 0),
                 Extrude([(0.6, 1.0), (2.2, 0.0), (1.4, -4.2), (0.2, -5.0)], 1.3, r=0.3).m("e34_plate"))


def boot():
    b = Extrude([(-2.2, -2.2), (4.6, -2.2), (3.2, -0.6), (1.0, 0.9), (-1.8, 0.9)], 1.7, r=0.4).m("e34_alloy")
    return Union(b, Chamfer(0.8, 0.5, 1.8, 0.2).m("e34_magenta_dim").at(-2.0, -0.9, 0))


RIFLE_L = 13.0       # grip (origin) to muzzle, along +x
GRIP2 = 4.6          # foregrip ahead of the grip


def rifle(recoil=0.0, hot=False):
    r = -recoil
    body = Chamfer(4.0, 1.25, 0.9, 0.5).m("e34_alloy").at(1.6 + r, 0.6, 0)
    stock = Extrude([(-5.6, -0.6), (-2.0, 0.2), (-2.0, 1.6), (-4.2, 1.2)], 0.7, r=0.3).m("e34_plate").at(r, 0, 0)
    barrel = Extrude([(5.4, 0.2), (11.6, 0.4), (12.4, 1.0), (5.4, 1.5)], 0.6, r=0.2).m("e34_plate").at(r, 0, 0)
    cells = Union(*[Box(0.6, 0.45, 0.25).m("e34_cyan").at(0.6 + 1.6 * k + r, 0.9, 0.95) for k in range(3)])
    tip = Box(0.6, 0.5, 0.55, r=0.15).m("e34_magenta" if hot else "e34_magenta_dim").at(12.6 + r, 0.75, 0)
    grip = Chamfer(0.6, 1.4, 0.6, 0.2).m("e34_joint").rot(0, 0, -14).at(-0.2 + r, -0.8, 0)
    sight = Chamfer(1.2, 0.5, 0.4, 0.2).m("e34_alloy").at(2.4 + r, 2.1, 0)
    return Union(body, stock, barrel, cells, tip, grip, sight)


SH = None


def shapes():
    global SH
    if SH is None:
        SH = dict(torso=torso(), pelvis=pelvis(), pauldron=pauldron(), upper=upper_arm(), fore=forearm(),
                  thigh=thigh(), shin=shin(), boot=boot())
    return SH


# ---------------------------------------------------------------------------------------------------------- posing

def hold(p, gx, gy, ang, lean=0.0):
    """Puts the rifle grip at (gx, gy) in spine space pointing at ang degrees (spine space) and solves both arms."""
    p = dict(p)
    a = math.radians(ang)
    fg = (gx + GRIP2 * math.cos(a), gy + GRIP2 * math.sin(a))
    for side, tgt, rx in (("r", (gx, gy), -6), ("l", fg, 8)):
        s = (BP.rig.joints[f"sh_{side}"][1][0], BP.rig.joints[f"sh_{side}"][1][1])
        a1, a2 = ik2(s, tgt, BP.L_UPPER, BP.L_FORE, bend=-1.0)
        p[f"sh_{side}"] = (rx, 0, a1)
        p[f"el_{side}"] = (0, 0, a2)
    p["rifle"] = (gx, gy, ang)
    return p


def pose(**kw):
    p = BP.pose(yaw=YAW, leg_ry=12.0, head=(0, 0, 0), spine=(0, 0, 0), foot_r=(2.4, 0, 0), foot_l=(-2.2, 0, 0),
                rifle=None, recoil=0.0, hot=False, glint=None, visor="e34_magenta")
    p.update(kw)
    return p


def parts(p, extra=None):
    S = shapes()
    W, q = BP.solve(p)
    out = []

    def add(shape, joint, name, shade=0, M=None, zbias=0.0):
        X = W[joint] if M is None else W[joint] @ M
        out.append(Part(shape.xform(X), name=name, shade=shade, zbias=zbias))

    add(helmet(p["visor"], p["glint"]), "head", "helmet")
    add(S["torso"], "spine", "torso")
    add(S["pelvis"], "pelvis", "pelvis")
    for side, sh in (("l", -1), ("r", 0)):
        add(S["thigh"], f"hip_{side}", f"thigh_{side}", sh)
        add(S["shin"], f"kn_{side}", f"shin_{side}", sh)
        add(S["boot"], f"an_{side}", f"boot_{side}", sh)
    add(S["upper"], "sh_l", "upper_l", -1)
    add(S["fore"], "el_l", "fore_l", -1)
    add(S["pauldron"], "sh_l", "pauldron_l", -1, M=rot(0, 0, -p["sh_l"][2] * 0.6))
    if p.get("rifle") is not None:
        gx, gy, ang = p["rifle"]
        add(rifle(p["recoil"], p["hot"]), "spine", "rifle", M=trans(gx, gy, 1.6) @ rot(0, 0, ang))
    add(S["upper"], "sh_r", "upper_r")
    add(S["fore"], "el_r", "fore_r")
    add(S["pauldron"], "sh_r", "pauldron_r", M=rot(0, 0, -p["sh_r"][2] * 0.6))
    if extra:
        for shape, joint, name, sh, M in extra:
            add(shape, joint, name, sh, M)
    return out, W


def muzzle_world(p):
    W, _ = BP.solve(p)
    gx, gy, ang = p["rifle"]
    q = W["spine"] @ trans(gx, gy, 1.6) @ rot(0, 0, ang) @ np.array([RIFLE_L + 0.4 - p["recoil"], 0.75, 0, 1.0])
    return q[0], q[1]


def draw(p, extra=None, **kw):
    ps, W = parts(p, extra)
    return E.draw(ps, **kw)


# ---------------------------------------------------------------------------------------------------------- animations

WALK = walk_feet(8, 9.4, 3.0)
LOW = (2.6, 4.8, -24)       # low ready: grip, angle (spine space)
AIM = (1.8, 8.6, 0)         # shouldered


def move(i):
    n = 8
    ph = TAU * i / n
    bob = math.cos(2 * ph)
    p = pose(pelvis_y=PY - 0.6 - 0.5 * bob, spine=(0, -5 * math.cos(ph), -4), head=(0, 0, 3 + 1.0 * bob),
             foot_r=WALK[i], foot_l=WALK[(i + n // 2) % n])
    gx, gy, ang = LOW
    return draw(hold(p, gx, gy + 0.3 * bob, ang + 2 * math.cos(ph)))


def idle(i):
    n = 8
    b = 0.5 - 0.5 * math.cos(TAU * i / n)
    glint = {2: 2.4, 3: 0.8, 4: -0.8, 5: -2.4}.get(i)
    p = pose(pelvis_y=PY - 0.3 - 0.4 * b, spine=(0, 0, -1 - b), head=(0, [0, 0, 6, 10, 10, 4, 0, 0][i], 1 + b),
             glint=glint)
    gx, gy, ang = LOW
    return draw(hold(p, gx, gy - 0.3 * b, ang))


ATTACK = [  # blend low -> aim, lean, recoil, hot, flash
    (0.0, 0, 0.0, 0, 0), (0.35, 2, 0.0, 0, 0), (0.75, 3, 0.0, 0, 0), (1.0, 3, 0.0, 1, 0),
    (1.0, 6, 1.6, 1, 2), (1.0, 4, 0.8, 1, 1), (1.0, 3, 0.2, 0, 0), (1.0, 3, 0.0, 0, 0),
]


def attack(i):
    """Raise the rifle to the shoulder (0-3), fire at 4 (the engine shoots at 0.45 s), hold."""
    u, lean, rec, hot, fl = ATTACK[i]
    g = [LOW[k] + (AIM[k] - LOW[k]) * u for k in range(3)]
    p = pose(pelvis_y=PY - 0.6, pelvis_x=-0.3 * lean / 3, spine=(0, 10 * u, lean * 0.6), head=(0, 0, -2 * u),
             foot_r=(3.2, 0, 0), foot_l=(-3.0, 0, 0), recoil=rec, hot=bool(hot))
    p = hold(p, g[0] - rec * 0.5, g[1], g[2])
    spr = draw(p)
    mx, my = muzzle_world(p)
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
    keys = [(-1.4, 18, 22), (-1.0, 12, 14), (-0.4, 5, 6)]
    px_, sp, hd = keys[i]
    p = pose(pelvis_x=px_, pelvis_y=PY - 0.6, spine=(0, -8, sp), head=(0, 0, hd), foot_r=(4.0, 1.0, 16),
             foot_l=(-2.4, 0, 0), visor="e34_magenta_dim")
    spr = draw(hold(p, LOW[0], LOW[1] + 1.0, LOW[2] + 20))
    if i == 0:
        flash(spr)
    if i < 2:
        spark(spr, 34 - i, 22 + i, 2 - i, hot="magenta:6", cold="violet:5")
    return spr


E.anim("move", 12, "loop", 8, move, "patrol march, rifle at low ready")
E.anim("attack", 10, "once", 8, attack, "shoulder the rifle (0-3), fire at 4 (0.4-0.5 s), hold")
E.anim("idle", 8, "loop", 8, idle, "breathing, visor glint sweeps")
E.anim("hurt", 12, "once", 3, hurt, "")

_aim = hold(pose(pelvis_y=PY - 0.6, spine=(0, 10, 1.8), head=(0, 0, -2), foot_r=(3.2, 0, 0), foot_l=(-3.0, 0, 0)),
            *AIM)
_aim["recoil"] = 0.0
mx, my = muzzle_world(_aim)
E.point("muzzle", mx, my, "rifle muzzle, shouldered (attack 3-7)")
E.note("glow: visor slit, chest core line, rifle cells and muzzle, boot heels")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
