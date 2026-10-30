"""blinker -- episode 4 blinker (box 24 x 36): a phasing Gloam assassin, a slender android with a crescent blade crest,
two cyan eyes, long angular coat tails; it teleports near the hero and casts an orb from its hand.

64 x 64 frames, anchor (32, 60). idle = standing, flickering out of phase; attack = the 0.5 s before the shot (the
hand comes up, the orb gathers, release). The engine spawns the orb at the box centre; `muzzle` marks the hand.
"""
import math

import numpy as np

from bake import (Box, Capsule, Chamfer, Extrude, Part, Sphere, Union, ik2, material, rot, scaling, trans)
from models._e34_common import TAU, Biped, Enemy, flash, glitch, recolor, spark, sparkle, walk_feet

E = Enemy("blinker", (64, 64), (32, 60), "Gloam blinker, a phasing assassin (episode 4, faces right)", 4)

material("blinker_orb", ["magenta:4", "magenta:5", "magenta:6", "white"], style="emit", bands=[0.25, 0.55, 0.85],
         prio=3.0)
material("blinker_coat", ["violet:1", "violet:2", "slate:2", "violet:3", "slate:4", "violet:5"],
         bands=[-0.4, -0.05, 0.3, 0.6, 0.85], line_lit="violet:0")

BP = Biped(thigh=6.6, shin=6.4, ankle_h=2.0, upper=5.4, fore=5.2, hip_w=2.2, sh_w=3.6, sh_y=10.4, neck_y=12.2,
           hip_drop=0.6, sh_x=-0.2, sole=(-1.8, 3.4))
PY = BP.PELVIS_Y
YAW = -34.0
SC = 1.0            # model scale


def head(eyes="e34_cyan"):
    skull = Extrude([(-2.4, -1.6), (2.2, -2.2), (3.4, -0.4), (2.8, 2.4), (-0.6, 3.4), (-2.8, 1.8)], 2.2, r=0.6) \
        .m("e34_alloy").at(0, 0.8, 0)
    mask = Chamfer(1.2, 1.8, 1.9, 0.6).m("e34_plate").at(2.4, 0.4, 0)
    ey = [Box(0.7, 0.5, 0.6, r=0.12).m(eyes).at(3.4, 1.0, z) for z in (0.95, -0.95)]
    crest = Extrude([(-1.0, 2.6), (1.4, 3.6), (-2.4, 7.8), (-7.6, 9.0), (-4.2, 6.4), (-3.2, 3.6)], 0.45, r=0.15) \
        .m("e34_plate")
    edge = Extrude([(-2.4, 7.8), (-7.6, 9.0), (-6.8, 8.2)], 0.5, r=0.1).m("e34_cyan_dim")
    return Union(skull, mask, *ey, crest, edge)


def torso():
    chest = Chamfer(2.6, 3.6, 3.2, 1.2).m("e34_alloy").at(0.2, 7.6, 0)
    plate = Extrude([(-0.4, 4.4), (2.8, 5.0), (3.4, 9.4), (1.2, 11.0), (-1.0, 10.0)], 2.4, r=0.4).m("e34_plate")
    line = Box(0.3, 2.6, 0.4).m("e34_cyan").at(3.4, 7.4, 0)
    waist = Chamfer(1.8, 2.2, 2.4, 0.6).m("e34_joint").at(0, 2.8, 0)
    collar = Extrude([(-2.6, 10.4), (2.0, 10.6), (1.0, 12.8), (-3.6, 13.6)], 2.8, r=0.4).m("blinker_coat")
    return Union(chest, plate, line, waist, collar)


def coat(flut=0.0, lift=0.0):
    """Two long angular tails from the waist, hanging behind; flut ripples them, lift blows them back."""
    out = []
    for z, ph in ((1.6, 0.0), (-1.6, 1.3)):
        f = flut * math.sin(ph) + lift
        pts = [(-1.6, 2.0), (1.2, 1.4), (0.6 - 1.0 * f, -6.0), (-1.4 - 2.4 * f, -11.0 + 1.6 * f),
               (-3.4 - 3.4 * f, -9.0 + 2.6 * f), (-3.6 - 1.4 * f, -3.0)]
        out.append(Extrude(pts, 0.4, r=0.15).m("blinker_coat").at(0, 0, z * 1.4))
        hem = [pts[2], pts[3], pts[4]]
        for a, b in zip(hem, hem[1:]):
            out.append(Capsule((a[0], a[1], z * 1.4), (b[0], b[1], z * 1.4), 0.42).m("e34_cyan_dim"))
    belt = Chamfer(2.2, 0.8, 2.6, 0.3).m("e34_plate").at(0, 1.6, 0)
    return Union(belt, *out)


def limb(r, L, mat="e34_alloy"):
    return Capsule((0, 0, 0), (0, -L + 0.6, 0), r).m(mat)


def fore():
    return Union(Sphere(0.95).m("e34_joint"), Chamfer(1.1, BP.L_FORE / 2, 1.1, 0.4).m("e34_plate")
                 .at(0, -BP.L_FORE / 2, 0), Box(0.25, 1.6, 1.15).m("e34_cyan_dim").at(0.95, -BP.L_FORE / 2, 0))


def shin():
    return Union(Sphere(1.1).m("e34_plate"),
                 Extrude([(-1.2, 0.0), (1.4, -0.4), (0.8, -BP.L_SHIN), (-0.8, -BP.L_SHIN)], 1.2, r=0.3)
                 .m("e34_alloy"))


def foot():
    return Extrude([(-1.8, -2.0), (4.6, -2.0), (2.4, -0.6), (0.6, 0.8), (-1.4, 0.8)], 1.2, r=0.3).m("e34_alloy")


SH = None


def shapes():
    global SH
    if SH is None:
        SH = dict(torso=torso(), thigh=limb(1.45, BP.L_THIGH), shin=shin(), foot=foot(), upper=limb(1.05, BP.L_UPPER),
                  fore=fore(), pelvis=Chamfer(2.2, 1.4, 2.6, 0.6).m("e34_alloy").at(0, -0.4, 0),
                  pad=Extrude([(-1.8, -1.0), (2.2, -1.2), (2.0, 1.4), (-1.0, 2.4)], 1.6, r=0.4).m("e34_plate"))
    return SH


def pose(**kw):
    p = BP.pose(yaw=YAW, leg_ry=14.0, spine=(0, 0, 0), head=(0, 0, -4), sh_r=(-8, 0, 12), el_r=(0, 0, 24),
                sh_l=(8, 0, -10), el_l=(0, 0, 20), foot_r=(3.2, 0, 0), foot_l=(-2.0, 0, 0), wr_r=(0, 0, 0))
    p.update(kw)
    return p


def parts(p, flut=0.0, lift=0.0, orb=0.0, eyes="e34_cyan"):
    S = shapes()
    W, _ = BP.solve(p)
    out = []

    def add(shape, joint, name, shade=0, M=None, zbias=0.0):
        X = scaling(SC) @ (W[joint] if M is None else W[joint] @ M)
        out.append(Part(shape.xform(X), name=name, shade=shade, zbias=zbias))

    add(coat(flut, lift), "pelvis", "coat", -1)
    add(head(eyes), "head", "head")
    add(S["torso"], "spine", "torso")
    add(S["pelvis"], "pelvis", "pelvis")
    for side, sh in (("l", -1), ("r", 0)):
        add(S["thigh"], f"hip_{side}", f"thigh_{side}", sh)
        add(S["shin"], f"kn_{side}", f"shin_{side}", sh)
        add(S["foot"], f"an_{side}", f"foot_{side}", sh)
    add(S["upper"], "sh_l", "upper_l", -1)
    add(S["fore"], "el_l", "fore_l", -1)
    add(S["pad"], "sh_l", "pad_l", -1)
    add(S["upper"], "sh_r", "upper_r", zbias=20 if orb else 0)
    add(S["fore"], "el_r", "fore_r", zbias=20 if orb else 0)
    add(S["pad"], "sh_r", "pad_r")
    if orb > 0:
        add(Sphere(0.8 + 2.0 * orb).m("blinker_orb"), "el_r", "orb", M=trans(1.4, -BP.L_FORE - 1.2 - 1.2 * orb, 0),
            zbias=30)
    return out, W


def hand(p, orb=1.0):
    W, _ = BP.solve(p)
    q = scaling(SC) @ W["el_r"] @ np.array([1.4, -BP.L_FORE - 1.2 - 1.2 * orb, 0, 1.0])
    return q[0], q[1]


def draw(p, **kw):
    ps, W = parts(p, **kw)
    return E.draw(ps)


# ---------------------------------------------------------------------------------------------------------- animations

def phase(spr, k):
    """Out-of-phase flicker: two slices of rows shifted sideways and tinted cyan, scan lines dropped out."""
    bb = spr.bbox()
    if bb is None:
        return
    top, bot = bb[1], bb[3]
    for j, (f, sh) in enumerate(((0.28, 3), (0.62, -3))):
        h0 = int(top + (bot - top) * (f + 0.08 * (k % 2)))
        rows = list(range(h0, h0 + 3 + j))
        glitch(spr, rows, sh if k % 2 else -sh)
        for y in rows:
            for x in range(spr.w):
                c = spr.get(x, y)
                if c > 1:
                    spr.put(x, y, "cyan:5" if (x + y) % 2 else "cyan:3", glow=True)
    for y in range(top, bot, 2):
        if (y + k) % 5 == 0:
            for x in range(spr.w):
                if spr.get(x, y) >= 0:
                    spr.col[y, x] = -1
                    spr.emit[y, x] = False


def idle(i):
    n = 8
    t = i / n
    b = 0.5 - 0.5 * math.cos(TAU * t)
    p = pose(pelvis_y=PY - 0.3 - 0.3 * b, spine=(0, 0, -2 - b), head=(0, 0, -4 + 2 * b), sh_r=(-8, 0, 10 + 4 * b),
             sh_l=(8, 0, -10 - 3 * b))
    spr = draw(p, flut=0.25 * math.sin(TAU * t), lift=0.15)
    if i in (3, 6):
        phase(spr, i)
    return spr


def attack(i):
    """The hand comes up (0-2), the orb gathers (2-4), release with a flash (5)."""
    keys = [  # shoulder rz, elbow, spine lean, orb size
        (10, 24, 0, 0.0), (50, 40, 4, 0.0), (80, 20, 8, 0.25), (86, 12, 8, 0.6), (86, 10, 8, 1.0), (84, 8, 10, 0.6)]
    sh, el, lean, orb = keys[i]
    p = pose(pelvis_y=PY - 0.8, spine=(0, 8, -lean * 0.5), head=(0, 0, -2), sh_r=(-14, 0, sh), el_r=(0, 0, el),
             sh_l=(10, 0, -28), el_l=(0, 0, 30), foot_r=(4.0, 0, 0), foot_l=(-3.0, 0, 0))
    spr = draw(p, flut=0.3, lift=0.5, orb=orb)
    hx, hy = hand(p, orb)
    x, y = E.px(hx, hy)
    if 2 <= i <= 4:
        for k in range(2):
            a = TAU * (k / 2 + i * 0.2)
            sparkle(spr, int(round(x + 5 * math.cos(a))), int(round(y + 5 * math.sin(a))), 1, c1="white",
                    c2="magenta:5")
    if i == 5:
        sparkle(spr, x + 1, y, 3, c1="white", c2="magenta:6")
    return spr


def hurt(i):
    keys = [(-1.2, 16), (-0.8, 10), (-0.3, 4)]
    px_, sp = keys[i]
    p = pose(pelvis_x=px_, pelvis_y=PY - 0.6, spine=(0, -8, sp), head=(0, 0, 14), sh_r=(-10, 0, -30),
             sh_l=(10, 0, 40), foot_r=(4.0, 1.0, 14))
    spr = draw(p, flut=0.6, lift=0.7, eyes="e34_cyan_dim")
    if i == 0:
        flash(spr)
        phase(spr, 1)
    return spr


E.anim("idle", 8, "loop", 8, idle, "coat sways; phase glitches at 3 and 6")
E.anim("attack", 12, "once", 6, attack, "hand up, orb gathers, release at 5 (0.42-0.5 s)")
E.anim("hurt", 12, "once", 3, hurt, "")
_p = pose(pelvis_y=PY - 0.8, spine=(0, 8, -4), head=(0, 0, -2), sh_r=(-14, 0, 86), el_r=(0, 0, 10),
          sh_l=(10, 0, -28), el_l=(0, 0, 30), foot_r=(4.0, 0, 0), foot_l=(-3.0, 0, 0))
hx, hy = hand(_p, 1.0)
E.point("muzzle", hx, hy, "casting hand with the orb (attack 4)")
E.note("glow: eyes, crest edge, chest line, the orb; idle frames 3 and 6 are glitched (phasing)")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
