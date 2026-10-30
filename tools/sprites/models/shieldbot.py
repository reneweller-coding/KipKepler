"""shieldbot -- episode 4 walker (box 30 x 36): a stocky Gloam robot with one big cyan eye, carrying a tall hexagonal
energy shield in front (its front blocks shots).

64 x 64 frames, anchor (32, 60). The shield is held out in front (right) and turned a little towards the viewer so
its face reads.
"""
import math

import numpy as np

from bake import (Box, Capsule, Chamfer, Cylinder, Extrude, Paint, Part, Sphere, Torus, Union, material, prism, rot,
                  scaling, trans)
from models._e34_common import TAU, Biped, Enemy, flash, spark, walk_feet

E = Enemy("shieldbot", (64, 64), (32, 60), "Gloam shield bot (episode 4 walker, faces right)", 4)

material("shieldbot_pane", ["blue:2", "blue:3", "cyan:3", "cyan:4"], style="emit", bands=[0.3, 0.6, 0.85], prio=1.2,
         line="blue:1", line_lit="blue:1")
material("shieldbot_pane_hot", ["cyan:3", "cyan:4", "cyan:5", "cyan:6"], style="emit", bands=[0.3, 0.6, 0.85], prio=1.2,
         line="blue:1", line_lit="blue:1")
material("shieldbot_lattice", ["cyan:5", "cyan:6"], style="emit", bands=[0.5], prio=2.2)
material("shieldbot_pane_hurt", ["magenta:2", "magenta:3", "magenta:4", "magenta:5"], style="emit", bands=[0.3, 0.6, 0.85],
         prio=1.2, line="magenta:1", line_lit="magenta:1")
material("shieldbot_lens", ["blue:2", "cyan:4", "cyan:5", "cyan:6", "white"], style="glass", bands=[-0.2, 0.25, 0.6],
         spec=0.9, glow=True, prio=2.5)

BP = Biped(thigh=5.8, shin=5.6, ankle_h=2.4, upper=6.0, fore=5.6, hip_w=4.2, sh_w=7.0, sh_y=9.6, neck_y=11.4,
           hip_drop=0.8, sh_x=0.4, sole=(-3.0, 4.2))
PY = BP.PELVIS_Y
YAW = -28.0
HEX_R = 11.6          # shield circumradius


def hexagon(r, stretch=1.25):
    return [(r * 0.62 * math.cos(math.radians(a)), r * stretch * 0.62 * math.sin(math.radians(a)) * 1.0)
            for a in range(30, 390, 60)]


def shield(t=0.0, mode="ok"):
    """The shield in its own space: the face looks along +x, centred at the origin, ~22 px tall."""
    pts = [(z * 1.0, y) for z, y in hexagon(HEX_R, 1.32)]
    frame = Extrude(pts, 0.9, r=0.3).m("e34_alloy")
    inner = [(z * 0.84, y * 0.88) for z, y in pts]
    pane_m = {"ok": "shieldbot_pane", "hot": "shieldbot_pane_hot", "hurt": "shieldbot_pane_hurt"}[mode]
    pane = Extrude(inner, 1.2, r=0.2).m(pane_m)
    # hex lattice lines and a shimmer band sweeping up
    lines = []
    for k in range(-3, 4):
        lines.append(Box(9, 0.42, 3).rot(0, 0, 60).at(0, k * 4.2, 0))
        lines.append(Box(9, 0.42, 3).rot(0, 0, -60).at(0, k * 4.2, 0))
    band = Box(12, 0.9, 3).rot(0, 0, 12).at(0, -11 + 22 * t, 0)
    pane = Paint(pane, Union(*lines, band), "shieldbot_lattice")
    studs = [Sphere(0.9).m("e34_magenta").at(z, y, 0.9) for z, y in pts[::2]]
    grip = Chamfer(1.4, 3.0, 1.2, 0.5).m("e34_joint").at(0, 0, -1.6)
    return Union(frame, pane, *studs, grip).rot(0, 90, 0)


def head(blink=False, look=0.0):
    dome = Chamfer(3.8, 2.8, 3.6, 1.4).m("e34_alloy").at(0.6, 2.0, 0)
    brow = Extrude([(-3.6, 2.6), (4.6, 3.4), (3.6, 5.0), (-2.6, 5.4)], 2.8, r=0.4).m("e34_plate")
    ring = Torus(1.9, 0.6).m("e34_plate").rot(0, 0, 90).at(4.2, 1.8, 0.6)
    lens = Sphere(1.7 if not blink else 0.6).m("shieldbot_lens").at(4.0 + look, 1.8, 0.6)
    ant = Capsule((-2.4, 4.6, 0), (-4.6, 7.4, 0), 0.4).m("e34_alloy")
    tip = Sphere(0.75).m("e34_magenta").at(-4.6, 7.6, 0)
    return Union(dome, brow, ring, lens, ant, tip)


def torso():
    barrel = Chamfer(4.8, 5.0, 5.6, 1.8).m("e34_alloy").at(0, 5.8, 0)
    plate = Extrude([(-2.0, 1.4), (3.4, 2.0), (5.6, 6.6), (3.6, 10.2), (-1.6, 10.0)], 4.0, r=0.6).m("e34_plate")
    vent = Union(*[Box(0.3, 0.3, 2.4).m("e34_magenta_dim").at(5.4, 4.0 + 1.0 * k, 0) for k in range(3)])
    pack = Chamfer(2.6, 4.0, 4.0, 1.0).m("e34_alloy").at(-5.4, 6.6, 0)
    return Union(barrel, plate, vent, pack)


def limb(r, L, mat="e34_alloy"):
    return Capsule((0, 0, 0), (0, -L + 0.6, 0), r).m(mat)


def foot():
    return Union(Extrude([(-3.0, -2.4), (4.6, -2.4), (3.6, -0.6), (0.8, 1.0), (-2.6, 1.0)], 2.2, r=0.4).m("e34_alloy"),
                 Chamfer(0.7, 0.4, 2.2, 0.2).m("e34_magenta_dim").at(-2.8, -1.2, 0))


SH = None


def shapes():
    global SH
    if SH is None:
        SH = dict(torso=torso(), thigh=limb(2.1, BP.L_THIGH), shin=Union(Sphere(2.0).m("e34_plate"),
                  Chamfer(2.0, BP.L_SHIN / 2, 2.0, 0.7).m("e34_plate").at(0, -BP.L_SHIN / 2, 0)),
                  foot=foot(), upper=limb(1.6, BP.L_UPPER), fore=Union(Sphere(1.4).m("e34_joint"),
                  Chamfer(1.8, BP.L_FORE / 2, 1.8, 0.6).m("e34_plate").at(0, -BP.L_FORE / 2, 0)),
                  pauldron=Chamfer(3.0, 2.4, 2.6, 1.0).m("e34_plate").at(0, 0.8, 0),
                  pelvis=Chamfer(3.6, 2.0, 4.6, 0.8).m("e34_alloy").at(0, -0.6, 0))
    return SH


def pose(**kw):
    p = BP.pose(yaw=YAW, leg_ry=14.0, spine=(0, 0, -6), head=(0, 0, 4), sh_r=(-4, 0, 60), el_r=(0, 0, 30),
                sh_l=(6, 0, 40), el_l=(0, 0, 50), foot_r=(3.0, 0, 0), foot_l=(-3.0, 0, 0))
    p.update(kw)
    return p


SHIELD_AT = (9.4, 3.6)      # shield centre in spine space (in front of the chest, the head peeks over)


def parts(p, t=0.0, mode="ok", blink=False, look=0.0, push=0.0):
    S = shapes()
    W, _ = BP.solve(p)
    out = []

    def add(shape, joint, name, shade=0, M=None, zbias=0.0):
        X = scaling(1.12) @ (W[joint] if M is None else W[joint] @ M)
        out.append(Part(shape.xform(X), name=name, shade=shade, zbias=zbias))

    add(head(blink, look), "head", "head")
    add(S["torso"], "spine", "torso")
    add(S["pelvis"], "pelvis", "pelvis")
    for side, sh in (("l", -1), ("r", 0)):
        add(S["thigh"], f"hip_{side}", f"thigh_{side}", sh)
        add(S["shin"], f"kn_{side}", f"shin_{side}", sh)
        add(S["foot"], f"an_{side}", f"foot_{side}", sh)
    for side, sh in (("l", -1), ("r", 0)):
        add(S["upper"], f"sh_{side}", f"upper_{side}", sh)
        add(S["fore"], f"el_{side}", f"fore_{side}", sh)
        add(S["pauldron"], f"sh_{side}", f"pauldron_{side}", sh)
    # the shield: in front of the chest, turned towards the viewer (the whole model is yawed away by YAW)
    M = trans(SHIELD_AT[0] + push, SHIELD_AT[1], 2.4) @ rot(0, -46, 0)
    add(shield(t, mode), "spine", "shield", M=M)
    return out


def draw(p, **kw):
    sq = kw.pop("squash", (1.0, 1.0))
    return E.draw(parts(p, **kw), squash=sq)


# ---------------------------------------------------------------------------------------------------------- animations

WALK = walk_feet(8, 8.0, 2.8)


def move(i):
    n = 8
    ph = TAU * i / n
    bob = math.cos(2 * ph)
    p = pose(pelvis_y=PY - 0.8 - 0.6 * bob, spine=(0, -4 * math.cos(ph), -8), head=(0, 0, 6 + bob),
             foot_r=WALK[i], foot_l=WALK[(i + n // 2) % n])
    return draw(p, t=i / n)


def idle(i):
    n = 8
    b = 0.5 - 0.5 * math.cos(TAU * i / n)
    p = pose(pelvis_y=PY - 0.4 - 0.4 * b, spine=(0, 0, -6 - b), head=(0, 0, 4 + b))
    return draw(p, t=i / n, blink=i == 5, look=[0, 0, 0.3, 0.5, 0.5, 0, -0.3, 0][i])


def attack(i):
    """Shield bash: brace (0-1), shove forward (2-3, the pane flares), recover."""
    keys = [(0.0, -2, -1.0, "ok"), (-1.6, -2, -1.6, "ok"), (2.6, -16, 0.8, "hot"), (3.4, -18, 1.2, "hot"),
            (1.6, -12, 0.4, "ok"), (0.4, -8, 0.0, "ok")]
    push, sp, px_, mode = keys[i]
    p = pose(pelvis_x=px_, pelvis_y=PY - 1.2, spine=(0, 0, sp), head=(0, 0, 8), foot_r=(4.4, 0, 0),
             foot_l=(-3.8, 0, 0))
    spr = draw(p, t=i / 6, mode=mode, push=push)
    if i == 3:
        for y in (24, 31, 38):
            spark(spr, 47, y, 1, hot="cyan:6", cold="cyan:4")
    return spr


def hurt(i):
    keys = [(-1.6, 10, "hurt"), (-1.0, 6, "ok"), (-0.4, 2, "hurt")]
    px_, sp, mode = keys[i]
    p = pose(pelvis_x=px_, pelvis_y=PY - 0.8, spine=(0, -6, sp - 4), head=(0, 0, 10), foot_r=(4.0, 0.8, 10))
    spr = draw(p, t=0.5, mode=mode, blink=True)
    if i == 0:
        flash(spr)
    if i < 2:
        spark(spr, 45 - i, 30 + 2 * i, 2 - i, hot="magenta:6", cold="magenta:4")
    return spr


E.anim("move", 10, "loop", 8, move, "heavy walk behind the shield; the shimmer sweeps up")
E.anim("idle", 8, "loop", 8, idle, "")
E.anim("attack", 12, "once", 6, attack, "shield bash (the walker brain does not use it yet)")
E.anim("hurt", 12, "once", 3, hurt, "the pane flickers magenta")
E.note("glow: eye lens, shield pane and lattice, magenta studs and vents")
E.note("the shield covers the front (right) from about 10 to 32 px above the anchor")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
