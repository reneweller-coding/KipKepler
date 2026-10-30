"""frostgolem -- episode 3 charger (box 40 x 46): a hulking golem of chamfered ice blocks, violet crystals growing from
its shoulders, a cyan core glowing through the cracks of its chest, a small head sunk between the shoulders.

96 x 96 frames, anchor (48, 92). move = heavy walk, attack = wind-up (rear back, roar) then the charge (knuckles
forward, long strides), hurt = dazed after hitting a wall.
"""
import math

import numpy as np

from bake import Box, Capsule, Chamfer, Ellipsoid, Paint, Part, Sphere, Union, material, prism, rot, scaling, trans
from models._e34_common import TAU, Biped, Enemy, chip, flash, puff, sparkle, walk_feet

E = Enemy("frostgolem", (96, 96), (48, 92), "frost golem (episode 3 charger, faces right)", 3)

material("frostgolem_ice", ["violet:1", "violet:2", "blue:2", "blue:3", "ice:3", "ice:4", "ice:5"],
         bands=[-0.55, -0.25, 0.02, 0.3, 0.58, 0.84], line_lit="blue:1")
material("frostgolem_ice_hi", ["blue:2", "ice:3", "ice:4", "ice:5", "ice:6", "ice:7"],
         bands=[-0.45, -0.1, 0.25, 0.55, 0.85], line_lit="blue:1")
material("frostgolem_rock", ["violet:0", "violet:1", "slate:2", "slate:3", "violet:4"], bands=[-0.4, 0.0, 0.4, 0.8])
material("frostgolem_crystal", ["violet:1", "violet:2", "violet:3", "purple:4", "violet:5", "purple:6", "white"],
         bands=[-0.45, -0.15, 0.12, 0.38, 0.62, 0.86], glow=True, line="violet:0", line_lit="violet:1")
material("frostgolem_core", ["cyan:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.6, 0.85], prio=2.5)
material("frostgolem_crack", ["cyan:3", "cyan:4"], style="emit", bands=[0.5], prio=2.0, inner=False)
material("frostgolem_eye", ["cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.75], prio=3.0)
material("frostgolem_snow", ["slate:4", "ice:6", "ice:7", "white"], bands=[-0.3, 0.2, 0.7], line_lit="slate:2")

BP = Biped(thigh=6.8, shin=6.4, ankle_h=3.0, upper=9.6, fore=9.0, hip_w=5.6, sh_w=10.4, sh_y=15.0, neck_y=13.6,
           hip_drop=1.2, sh_x=1.6, sole=(-3.6, 5.2))
PY = BP.PELVIS_Y
S = 1.08            # model scale (the rig lengths above are at 1.0)
SHIFT = -4.0        # recentres the hunched body over the anchor


def cracks(w, h, z, seed):
    """Thin glowing crack lines on a face at depth z (a region for Paint)."""
    rng = np.random.default_rng(seed)
    out = []
    for k in range(3):
        x0, y0 = rng.uniform(-w * 0.6, w * 0.6), rng.uniform(-h * 0.6, h * 0.6)
        a = rng.uniform(-70, 70)
        out.append(Box(rng.uniform(1.6, 3.2), 0.28, 3.0).rot(0, 0, a).at(x0, y0, z))
    return Union(*out)


def torso(core=1.0):
    chest = Chamfer(7.6, 7.8, 7.8, 2.4).m("frostgolem_ice").rot(0, 0, -6).at(0.2, 9.4, 0)
    chest = Paint(chest, cracks(6, 6, 7.8, 3).at(0.2, 9.4, 0), "frostgolem_crack")
    belly = Chamfer(6.2, 4.4, 6.4, 1.8).m("frostgolem_ice_hi").at(1.2, 2.4, 0)
    socket = Ellipsoid(3.6, 3.4, 2.0).m("frostgolem_rock").at(5.4, 12.6, 4.2)
    gem = prism(6, 2.2 + 0.4 * core, 1.4, 1.8, 1.8, twist=10).m("frostgolem_core").rot(70, -40, -10).at(6.2, 12.8, 4.6)
    snow = Ellipsoid(7.0, 2.0, 7.2).m("frostgolem_snow").at(-1.6, 18.8, -0.8)
    back = [prism(6, 1.8 * s, 2.2 * s, 2.8 * s, 1.0).m("frostgolem_crystal").rot(rx, 0, rz).at(x, y, z)
            for x, y, z, rx, rz, s in ((-7.0, 16.0, 2.0, 20, 40, 1.0), (-8.0, 11.0, -1.0, -10, 60, 0.8),
                                       (-6.0, 19.0, -2.0, -14, 24, 0.9))]
    return Union(chest, belly, socket, gem, snow, *back)


def pelvis():
    return Chamfer(6.4, 3.6, 6.2, 1.6).m("frostgolem_ice").at(0, -0.8, 0)


def head(blink=False, roar=0.0):
    skull = Chamfer(4.2, 3.8, 4.0, 1.3).m("frostgolem_ice_hi").at(7.4, 0.6, 0)
    brow = Chamfer(2.4, 1.0, 4.2, 0.5).m("frostgolem_ice").rot(0, 0, -14).at(9.8, 2.6, 0)
    slit = Box(1.2, 0.9 + 1.0 * roar, 3.0, r=0.3).m("frostgolem_rock").at(11.0, -1.2 - 0.7 * roar, 0)
    eyes = [Box(1.0, 0.4 if blink else 1.05, 1.15, r=0.3).m("frostgolem_rock" if blink else "frostgolem_eye")
            .at(11.2, 1.2, z) for z in (1.8, -1.8)]
    spike = prism(5, 1.2, 0.6, 2.4, 0.5).m("frostgolem_crystal").rot(0, 0, 40).at(5.6, 4.6, 0)
    return Union(skull, brow, slit, *eyes, spike)


def shoulder(side):
    block = Chamfer(5.4, 4.6, 5.2, 1.6).m("frostgolem_ice_hi").at(-0.2, 1.0, 0)
    crys = []
    if side == "l":
        spec = ((-1.0, 6.0, -1.2, 10, 14, 1.25), (2.2, 5.4, -2.2, -14, -22, 0.9), (-3.4, 4.6, -0.6, 8, 46, 0.8))
    else:
        spec = ((-0.6, 6.0, 1.0, -10, 12, 1.1), (2.6, 5.2, 1.8, 14, -26, 0.8))
    for x, y, z, rx, rz, s in spec:
        crys.append(prism(6, 1.9 * s, 2.0 * s, 3.4 * s, 0.8).m("frostgolem_crystal").rot(rx, 0, rz)
                    .at(x, y + 2.4 * s, z))
    return Union(block, *crys)


def upper_arm():
    return Chamfer(3.4, 5.4, 3.4, 1.0).m("frostgolem_ice_hi").at(0, -5.0, 0)


def forearm():
    arm = Chamfer(3.8, 4.4, 3.8, 1.2).m("frostgolem_ice_hi").at(0, -3.8, 0)
    fist = Chamfer(4.6, 4.0, 4.4, 1.5).m("frostgolem_ice_hi").at(0.4, -BP.L_FORE + 0.6, 0)
    knuckles = Chamfer(1.4, 1.6, 4.0, 0.6).m("frostgolem_rock").at(4.4, -BP.L_FORE + 0.0, 0)
    return Union(arm, fist, knuckles)


def thigh():
    return Chamfer(3.6, BP.L_THIGH / 2 + 0.8, 3.6, 1.2).m("frostgolem_ice").at(0, -BP.L_THIGH / 2, 0)


def shin():
    return Chamfer(3.4, BP.L_SHIN / 2 + 0.6, 3.4, 1.1).m("frostgolem_ice").at(0, -BP.L_SHIN / 2, 0)


def foot():
    return Chamfer(4.8, 1.6, 3.8, 0.8).m("frostgolem_ice_hi").at(0.8, -BP.ANKLE_H + 1.6, 0)


SH = None


def shapes():
    global SH
    if SH is None:
        SH = dict(pelvis=pelvis(), head=head(), head_b=head(True), sh_l=shoulder("l"), sh_r=shoulder("r"),
                  upper=upper_arm(), fore=forearm(), thigh=thigh(), shin=shin(), foot=foot())
    return SH


def parts(pose, core=1.0, blink=False, roar=0.0):
    SS = shapes()
    W, pose = BP.solve(pose)
    out = []

    def add(shape, joint, name, shade=0, M=None, zbias=0.0):
        X = trans(SHIFT, 0, 0) @ scaling(S) @ (W[joint] if M is None else W[joint] @ M)
        out.append(Part(shape.xform(X), name=name, shade=shade, zbias=zbias))

    add(torso(core), "spine", "torso")
    add(SS["pelvis"], "pelvis", "pelvis")
    add(head(blink, roar) if roar else (SS["head_b"] if blink else SS["head"]), "head", "head")
    for side, sh in (("l", -1), ("r", 0)):
        add(SS["thigh"], f"hip_{side}", f"thigh_{side}", sh)
        add(SS["shin"], f"kn_{side}", f"shin_{side}", sh)
        add(SS["foot"], f"an_{side}", f"foot_{side}", sh)
    add(SS["upper"], "sh_l", "upper_l", -1)
    add(SS["fore"], "el_l", "fore_l", -1)
    add(SS["sh_l"], "sh_l", "shoulder_l", -1, M=rot(0, 0, 0))
    add(SS["upper"], "sh_r", "upper_r")
    add(SS["fore"], "el_r", "fore_r")
    add(SS["sh_r"], "sh_r", "shoulder_r")
    return out


def pose(**kw):
    p = BP.pose(yaw=-26.0, leg_ry=10.0, head=(0, 0, 16), spine=(0, 0, -24), sh_r=(-8, 0, 34), el_r=(0, 0, 16),
                sh_l=(8, 0, 22), el_l=(0, 0, 18), foot_r=(3.4, 0, 0), foot_l=(-3.0, 0, 0))
    p.update(kw)
    return p


def draw(p, **kw):
    return E.draw(parts(p, **kw))


# ---------------------------------------------------------------------------------------------------------- animations

WALK = walk_feet(8, 11.0, 3.6, duty=0.56)


def move(i):
    n = 8
    ph = TAU * i / n
    bob = -abs(math.cos(ph)) * 1.4
    c = math.cos(ph)
    p = pose(pelvis_y=PY - 0.8 + bob, pelvis=(0, 0, 0), spine=(0, -6 * c, -22), head=(0, 0, 16 + 3 * abs(c)),
             sh_r=(-8, 0, 30 + 26 * c), el_r=(0, 0, 18 - 8 * c), sh_l=(8, 0, 24 - 22 * c), el_l=(0, 0, 20 + 8 * c),
             foot_r=WALK[i], foot_l=WALK[(i + n // 2) % n])
    spr = draw(p, core=0.5 + 0.5 * abs(c))
    if i in (0, 4):      # heavy footfall: snow kicks up at the planted foot
        fx = WALK[i][0] if i == 0 else WALK[(i + n // 2) % n][0]
        x, y = E.px((fx * 0.88 + 2) * S + SHIFT, 0)
        puff(spr, x + 5, y - 2, 2, ("ice:7", "ice:6", "ice:5"))
        puff(spr, x - 5, y - 1, 1, ("ice:7", "ice:6", "ice:5"))
    return spr


def windup(i):
    """Rear back with both fists raised (0-3), roar, then drop forward into the charge (4-5)."""
    keys = [
        dict(pelvis_y=PY - 1.0, spine=(0, 0, -4), head=(0, 0, 0), sh_r=(-4, 0, 60), el_r=(0, 0, 50),
             sh_l=(4, 0, 50), el_l=(0, 0, 50), roar=0.2),
        dict(pelvis_y=PY - 0.2, spine=(0, 0, 10), head=(0, 0, 14), sh_r=(-4, 0, 130), el_r=(0, 0, 40),
             sh_l=(4, 0, 120), el_l=(0, 0, 40), roar=0.8),
        dict(pelvis_y=PY + 0.2, spine=(0, 0, 14), head=(0, 0, 20), sh_r=(-4, 0, 150), el_r=(0, 0, 30),
             sh_l=(4, 0, 142), el_l=(0, 0, 30), roar=1.0),
        dict(pelvis_y=PY + 0.2, spine=(0, 0, 14), head=(0, 0, 22), sh_r=(-4, 0, 152), el_r=(0, 0, 26),
             sh_l=(4, 0, 146), el_l=(0, 0, 28), roar=1.0),
        dict(pelvis_y=PY - 2.0, spine=(0, 0, -20), head=(0, 0, 4), sh_r=(-4, 0, 70), el_r=(0, 0, 40),
             sh_l=(4, 0, 60), el_l=(0, 0, 40), roar=0.4),
        dict(pelvis_y=PY - 2.6, spine=(0, 0, -30), head=(0, 0, 12), sh_r=(-4, 0, 40), el_r=(0, 0, 30),
             sh_l=(4, 0, 30), el_l=(0, 0, 30), roar=0.2),
    ]
    k = dict(keys[i])
    roar = k.pop("roar")
    p = pose(foot_r=(4.4, 0, 0), foot_l=(-4.0, 0, 0), **k)
    spr = draw(p, core=1.0, roar=roar)
    if i in (2, 3):
        x, y = E.px(14, 40)
        for d in range(3):
            spr.put(x + 2 + 2 * d + (i - 2), y - 3 + d * 3, "ice:7" if d != 1 else "white")
    return spr


CHARGE = walk_feet(6, 16.0, 5.0, duty=0.42, toe=-36, heel=8)


def charge(i):
    n = 6
    ph = TAU * i / n
    c = math.cos(ph)
    p = pose(pelvis_x=2.4, pelvis_y=PY - 2.0 - 0.8 * abs(math.sin(ph)), spine=(0, -8 * c, -32), head=(0, 0, 18),
             sh_r=(-4, 0, 58 + 18 * c), el_r=(0, 0, 18), sh_l=(4, 0, 50 - 18 * c), el_l=(0, 0, 18),
             foot_r=CHARGE[i], foot_l=CHARGE[(i + n // 2) % n])
    spr = draw(p, core=1.0)
    for k in range(3):
        x, y = E.px(-16 - 4 * k - (i % 2) * 2, 2 + (k * 3 + i) % 5)
        puff(spr, x, y, 1 + (k == 0), ("ice:7", "ice:6", "ice:5"))
    return spr


def hurt(i):
    """Dazed after slamming into a wall: wobbling, crystal sparkles circling the head."""
    n = 6
    ph = TAU * i / n
    p = pose(pelvis_x=-1.2, pelvis_y=PY - 1.4, spine=(0, 8 * math.sin(ph), 4 + 3 * math.sin(ph)),
             head=(8 * math.sin(ph + 1), 0, 4 + 6 * math.cos(ph)), sh_r=(-8, 0, 2), el_r=(0, 0, 12),
             sh_l=(8, 0, 8), el_l=(0, 0, 14), foot_r=(4.6, 0, 0), foot_l=(-3.6, 0, 0))
    spr = draw(p, core=0.3, blink=True)
    hx, hy = BP.point(p, "head", (7.0, 5.0, 0))
    cx, cy = E.px(hx * S + SHIFT, hy * S + 4)
    for k in range(3):
        a = ph + k * TAU / 3
        sparkle(spr, int(round(cx + 8 * math.cos(a))), int(round(cy + 2.6 * math.sin(a))), 1 + (k == 0),
                c2="violet:5")
    return spr


def idle(i):
    n = 8
    b = 0.5 - 0.5 * math.cos(TAU * i / n)
    p = pose(pelvis_y=PY - 0.6 - 0.8 * b, spine=(0, 0, -22 - 3 * b), head=(0, 0, 16 + 3 * b),
             sh_r=(-8, 0, 32 + 4 * b), el_r=(0, 0, 16 + 4 * b), sh_l=(8, 0, 24 - 2 * b), el_l=(0, 0, 18 + 4 * b))
    spr = draw(p, core=0.4 + 0.6 * b, blink=i == 6)
    if i in (2, 3):
        x, y = E.px(14, 34)
        puff(spr, x + i, y - 2 * (i - 2), 1)
    return spr


N_WIND, N_CHARGE = 6, 6
E.anim("move", 10, "loop", 8, move, "heavy walk, contact at 0 and 4")
E.anim("attack", 12, "loop", N_WIND + N_CHARGE, lambda i: windup(i) if i < N_WIND else charge(i - N_WIND),
       "wind-up (0-5, 0.5 s) then the charge strides (6-11 repeated); 2.5 s before it wraps",
       order=list(range(N_WIND)) + list(range(N_WIND, N_WIND + N_CHARGE)) * 4)
E.anim("hurt", 10, "loop", 6, hurt, "dazed after hitting a wall")
E.anim("idle", 8, "loop", 8, idle, "breathing, core pulse")
E.note("glow: eyes, chest core and cracks, shoulder crystals")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
