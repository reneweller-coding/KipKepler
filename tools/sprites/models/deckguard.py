"""deckguard -- episode 4 platform rider (box 24 x 42): a Gloam guard posted on the moving platforms. The trooper's
armour (models/trooper.py) with a cyan visor, a round deck shield on the far arm and magnetic boots whose soles glow
cyan (they hold it to the platform).

64 x 64 frames, anchor (32, 60). Poses as the trooper's: patrol (move), shoulder and fire (attack), idle, hurt.
"""
import math

from bake import Box, Cylinder, Torus, Union, material, rot, trans
from models import trooper as tr
from models._e34_common import TAU, Enemy, flash, puff, spark, walk_feet

E = Enemy("deckguard", (64, 64), (32, 60), "Gloam deck guard (episode 4 platform rider, faces right)", 4)

material("dg_shield", ["violet:0", "slate:1", "violet:2", "slate:3", "violet:4", "slate:5", "white"], style="metal",
         bands=[-0.55, -0.3, 0.0, 0.3, 0.6, 0.85], spec=0.9)


def shield():
    """A round deck shield seen from the side, its face towards the viewer, a cyan ring and boss."""
    disc = Cylinder(4.4, 0.55, rr=0.4).m("dg_shield").rot(90, 0, 0)
    ring = Torus(3.4, 0.35).m("e34_cyan").rot(90, 0, 0).at(0, 0, 0.6)
    boss = Cylinder(1.2, 0.4, rr=0.3).m("e34_plate").rot(90, 0, 0).at(0, 0, 0.8)
    return Union(disc, ring, boss)


def sole():
    """Magnetic sole under a boot (glowing)."""
    return Union(Box(2.8, 0.45, 1.5, r=0.2).m("e34_cyan").at(1.2, -2.5, 0),
                 Box(1.0, 0.4, 1.6, r=0.15).m("e34_cyan_dim").at(-1.8, -2.4, 0))


def extras(p):
    return [(shield(), "el_l", "shield", -1, trans(0.4, -3.0, -1.2) @ rot(0, 0, -p["sh_l"][2] * 0.3)),
            (sole(), "an_r", "sole_r", 0, None), (sole(), "an_l", "sole_l", -1, None)]


def draw(p):
    ps, W = tr.parts(p, extras(p))
    return E.draw(ps)


def pose(**kw):
    kw.setdefault("visor", "e34_cyan")
    return tr.pose(**kw)


WALK = walk_feet(8, 7.6, 2.4)


def move(i):
    n = 8
    ph = TAU * i / n
    bob = math.cos(2 * ph)
    p = pose(pelvis_y=tr.PY - 0.7 - 0.4 * bob, spine=(0, -4 * math.cos(ph), -3), head=(0, 0, 2 + 0.8 * bob),
             foot_r=WALK[i], foot_l=WALK[(i + n // 2) % n])
    gx, gy, ang = tr.LOW
    return draw(tr.hold(p, gx, gy + 0.3 * bob, ang + 2 * math.cos(ph)))


def idle(i):
    n = 8
    b = 0.5 - 0.5 * math.cos(TAU * i / n)
    glint = {3: 2.0, 4: 0.6, 5: -0.8}.get(i)
    p = pose(pelvis_y=tr.PY - 0.3 - 0.4 * b, spine=(0, 0, -1 - b), head=(0, [0, 0, -6, -10, -10, -4, 0, 0][i], 1 + b),
             glint=glint)
    gx, gy, ang = tr.LOW
    return draw(tr.hold(p, gx, gy - 0.3 * b, ang))


def attack(i):
    """Shoulder the rifle (0-3), fire at 4 (the engine shoots at 0.4 s), hold."""
    u, lean, rec, hot, fl = tr.ATTACK[i]
    g = [tr.LOW[k] + (tr.AIM[k] - tr.LOW[k]) * u for k in range(3)]
    p = pose(pelvis_y=tr.PY - 0.6, pelvis_x=-0.3 * lean / 3, spine=(0, 10 * u, lean * 0.6), head=(0, 0, -2 * u),
             foot_r=(3.2, 0, 0), foot_l=(-3.0, 0, 0), recoil=rec, hot=bool(hot))
    p = tr.hold(p, g[0] - rec * 0.5, g[1], g[2])
    spr = draw(p)
    mx, my = tr.muzzle_world(p)
    px, py = E.px(mx, my)
    if fl == 2:
        for d, c in ((0, "white"), (1, "white"), (2, "cyan:6"), (3, "cyan:5"), (4, "blue:4")):
            for dy in range(-1 + (d > 2), 2 - (d > 2)):
                spr.put(px + d, py + dy, c, glow=True)
        spark(spr, px + 2, py - 3, 1, hot="cyan:6", cold="blue:4")
    elif fl == 1:
        puff(spr, px + 1, py - 1, 1, ("violet:5", "violet:4", "violet:3"))
    return spr


def hurt(i):
    keys = [(-1.4, 18, 22), (-1.0, 12, 14), (-0.4, 5, 6)]
    px_, sp, hd = keys[i]
    p = pose(pelvis_x=px_, pelvis_y=tr.PY - 0.6, spine=(0, -8, sp), head=(0, 0, hd), foot_r=(4.0, 1.0, 16),
             foot_l=(-2.4, 0, 0), visor="e34_cyan_dim")
    spr = draw(tr.hold(p, tr.LOW[0], tr.LOW[1] + 1.0, tr.LOW[2] + 20))
    if i == 0:
        flash(spr)
    if i < 2:
        spark(spr, 34 - i, 22 + i, 2 - i, hot="cyan:6", cold="blue:4")
    return spr


E.anim("move", 12, "loop", 8, move, "short patrol steps along the platform, rifle low")
E.anim("attack", 10, "once", 8, attack, "shoulder the rifle (0-3), fire at 4 (0.4 s), hold")
E.anim("idle", 8, "loop", 8, idle, "looks down over the platform's edge, visor glint")
E.anim("hurt", 12, "once", 3, hurt, "")

_aim = tr.hold(pose(pelvis_y=tr.PY - 0.6, spine=(0, 10, 1.8), head=(0, 0, -2), foot_r=(3.2, 0, 0), foot_l=(-3.0, 0, 0)),
               *tr.AIM)
_aim["recoil"] = 0.0
mx, my = tr.muzzle_world(_aim)
E.point("muzzle", mx, my, "rifle muzzle, shouldered (attack 3-7)")
E.note("glow: cyan visor slit, chest core line, rifle cells and muzzle, shield ring, magnetic soles")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
