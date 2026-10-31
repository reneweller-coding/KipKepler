"""mirrorbot -- episode 1 mirror walker (box 24 x 40): an Academy maintenance robot carrying a tall polished mirror
shield before it. Plain shots from the front glance back off the mirror (the engine throws them back); charged
shots, the lancer, the mortar and the arc go through. Built from the sentry's frame (models/sentry.py).

64 x 64 frames, anchor (32, 60). move: a careful walk behind the shield; attack: the shield thrust forward with a
glint running across it (shown when a shot glances off); idle: the sheen drifts; hurt: jolted back.
"""
import math

import numpy as np

from bake import Box, Capsule, Cylinder, Paint, Part, Rig, RoundCone, Sphere, Union, ik2, material, rot, trans
from models._e12_common import A64, S64, anim_jobs, make_sheet, point_of, puff, shoot, spark, to_px

YAW = -30.0

material("mir_white", ["slate:3", "slate:4", "steel:5", "steel:6", "steel:7", "white"],
         bands=[-0.6, -0.3, 0.05, 0.4, 0.8], line_lit="slate:2")
material("mir_yellow", ["crimson:2", "red:3", "red:4", "orange:5"], bands=[-0.4, 0.05, 0.7], line_lit="crimson:1")
material("mir_dark", ["slate:1", "slate:2", "slate:3", "slate:4"], bands=[-0.4, 0.1, 0.7])
material("mir_steel", ["slate:1", "slate:2", "steel:3", "steel:4", "steel:6"], style="metal",
         bands=[-0.3, 0.15, 0.6], spec=0.93)
material("mir_helmet", ["slate:1", "slate:2", "slate:3", "steel:3", "steel:4"], bands=[-0.5, -0.1, 0.35, 0.75])
material("mir_visor", ["violet:3", "magenta:4", "magenta:5", "magenta:6"], style="emit", bands=[0.2, 0.5, 0.85], prio=3.0)
material("mir_visor_hi", ["magenta:6", "rose:6", "white"], style="emit", bands=[0.3, 0.7], prio=3.5)
material("mir_visor_off", ["violet:2", "violet:3"], style="emit", bands=[0.5], prio=3.0)
material("mir_beacon", ["teal:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.6, 0.9], prio=3.0)
material("mir_glass", ["blue:2", "slate:4", "steel:5", "ice:6", "ice:7", "white"], style="metal",
         bands=[-0.5, -0.2, 0.15, 0.45, 0.8], spec=0.97, prio=2.0)
material("mir_rim", ["slate:2", "steel:4", "steel:6", "white"], style="metal", bands=[-0.3, 0.2, 0.7], spec=0.9)
material("mir_glint", ["white"], style="flat", prio=3.6, glow=True)
material("mir_edge", ["teal:4", "cyan:5", "cyan:6"], style="emit", bands=[0.4, 0.8], prio=3.0)

# ---------------------------------------------------------------------------------------------------------- skeleton
ANKLE_H, L_THIGH, L_SHIN = 2.2, 8.2, 8.6
PY = 17.6
L_UPPER, GUN_LEN = 5.0, 11.5

RIG = Rig()
RIG.joint("pelvis", None, (0, PY, 0))
RIG.joint("spine", "pelvis", (0, 1.6, 0))
RIG.joint("head", "spine", (0.8, 15.4, 0))
RIG.joint("sh_r", "spine", (0.0, 10.4, 5.0))
RIG.joint("el_r", "sh_r", (0, -L_UPPER, 0))
RIG.joint("sh_l", "spine", (0.0, 10.4, -4.8))
RIG.joint("el_l", "sh_l", (0, -4.8, 0))
for side, z in (("r", 1), ("l", -1)):
    RIG.joint(f"hip_{side}", "pelvis", (0, -0.6, 2.7 * z))
    RIG.joint(f"kn_{side}", f"hip_{side}", (0, -L_THIGH, 0))
    RIG.joint(f"an_{side}", f"kn_{side}", (0, -L_SHIN, 0))


def mkpose(**kw):
    p = dict(root=(0.0, 0.0), pelvis_y=PY, pelvis=(0, 0, 0), spine=(0, 0, 0), head=(0, 0, 0),
             sh_r=(0, 0, 60), el_r=(0, 0, 30), sh_l=(0, 0, -12), el_l=(0, 0, 30),
             foot_r=(2.0, 0.0, 0.0), foot_l=(-2.0, 0.0, 0.0), visor="mir_visor", scan=0.0, tip=None,
             beacon=True, lean=0.0, push=0.0, glint=None)
    p.update(kw)
    return p


def solve(p):
    pose = dict(p)
    rx, ry, rz = pose["sh_r"]
    pose["sh_r"] = (rx, ry - YAW, rz)          # gun arm side-on
    RIG.joints["pelvis"] = (None, np.array([0.0, pose["pelvis_y"], 0.0]))
    P0 = RIG.solve(pose)
    for side in ("r", "l"):
        fx, fy, pitch = pose[f"foot_{side}"]
        hip = P0[f"hip_{side}"][:3, 3]
        a1, a2 = ik2((hip[0], hip[1]), (fx, fy + ANKLE_H), L_THIGH, L_SHIN, bend=-1.0)
        parent = pose["pelvis"][2]
        pose[f"hip_{side}"] = (0, 0, a1 - parent)
        pose[f"kn_{side}"] = (0, 0, a2)
        pose[f"an_{side}"] = (0, 0, pitch - (a1 + a2))
    base = trans(pose["root"][0], pose["root"][1], 0) @ rot(0, 0, pose["lean"]) @ rot(0, YAW, 0)
    return RIG.solve(pose, base), pose


# ---------------------------------------------------------------------------------------------------------- shapes

def torso():
    chest = RoundCone((0, 6.0, 0), (0.4, 10.6, 0), 2.9, 3.9).m("mir_white")
    plate = Box(1.6, 2.8, 3.0, r=1.1).m("mir_white").at(1.9, 8.8, 0)
    stripe = Box(0.45, 2.4, 1.0, r=0.2).m("mir_beacon").at(3.45, 8.8, 1.2)
    waist = Cylinder(1.8, 2.0, rr=0.7).m("mir_dark").at(0, 3.0, 0)
    belt = Box(3.0, 0.9, 3.2, r=0.7).m("mir_yellow").at(0, 0.8, 0)
    hipbox = Box(2.6, 1.4, 3.4, r=0.9).m("mir_dark").at(0, -0.8, 0)
    back = Box(1.6, 3.2, 2.6, r=0.9).m("mir_dark").at(-3.4, 8.6, 0)
    return Union(chest, plate, stripe, waist, belt, hipbox, back)


HEAD_R = 3.5


def head(visor, scan, beacon):
    shell = Union(Cylinder(HEAD_R, 2.3, rr=1.3).at(0, 0, 0), Sphere(HEAD_R - 0.2).at(0, 0.8, 0)).m("mir_helmet")
    slit = Box(4.5, 1.25, 4.5).at(2.2, 0.1, 1.4)
    shell = Paint(shell, slit, visor)
    a = math.radians(15 + 55 * scan)
    dot = Box(1.4, 1.3, 1.4).rot(0, -math.degrees(a), 0).at(HEAD_R * math.cos(a), 0.1, HEAD_R * math.sin(a))
    shell = Paint(shell, dot, "mir_visor_hi")
    brow = Box(1.4, 0.6, 3.0, r=0.3).m("mir_yellow").at(2.6, 2.1, 0)
    fin = Box(2.4, 0.7, 0.7, r=0.35).m("mir_yellow").rot(0, 0, 10).at(-0.8, 4.2, 0)
    light = Sphere(1.05).m("mir_beacon" if beacon else "mir_dark").at(-1.8, 4.6, 0)
    neck = Cylinder(1.0, 1.4).m("mir_dark").at(0, -3.4, 0)
    return Union(shell, brow, fin, light, neck)


def upper_arm():
    return Union(Sphere(2.6).m("mir_yellow").at(0, -0.2, 0),
                 Capsule((0, -0.8, 0), (0, -L_UPPER + 0.6, 0), 1.35).m("mir_steel"),
                 Sphere(1.45).m("mir_dark").at(0, -L_UPPER, 0))


def mirror(glint=None):
    """The mirror shield in spine space, its face forward (+x): a tall rounded slab in a steel rim, a cyan edge light;
    glint: where the white sheen band crosses it (-1 .. 1, None = none)."""
    glass = Box(0.9, 7.2, 4.6, r=0.7).m("mir_glass")
    if glint is not None:
        glass = Paint(glass, Box(2.0, 1.4, 6.0).rot(30, 0, 0).at(0.4, 6.0 * glint, 0), "mir_glint")
    rim = Box(0.7, 7.8, 5.2, r=0.9).m("mir_rim").at(-0.5, 0, 0)
    edge = Box(0.4, 7.4, 0.35, r=0.15).m("mir_edge").at(0.2, 0, 4.9)
    grip = Box(1.2, 1.6, 1.2, r=0.4).m("mir_dark").at(-1.4, 0, 0)
    return Union(glass, rim, edge, grip)


def far_arm():
    return Union(Sphere(2.0).m("mir_white").at(0, -0.2, 0),
                 Capsule((0, -0.8, 0), (0, -4.2, 0), 1.2).m("mir_steel"))


def far_fore():
    return Union(Capsule((0, 0, 0), (0, -4.0, 0), 1.15).m("mir_steel"), Sphere(1.5).m("mir_dark").at(0, -4.6, 0))


def thigh():
    return Union(Capsule((0, 0, 0), (0, -L_THIGH + 0.5, 0), 1.45).m("mir_steel"),
                 Sphere(1.9).m("mir_dark"))


def shin():
    return Union(Sphere(1.75).m("mir_yellow"),
                 RoundCone((0, -1.0, 0), (0, -L_SHIN + 0.8, 0), 1.75, 1.05).m("mir_white"))


def foot():
    return Union(Box(3.4, 0.9, 1.9, r=0.6).m("mir_dark").at(1.1, -ANKLE_H + 0.9, 0),
                 Box(1.3, 0.9, 1.6, r=0.5).m("mir_dark").at(-2.2, -ANKLE_H + 0.8, 0),
                 Sphere(1.3).m("mir_steel"))


def parts(pose):
    W, pose = solve(pose)
    out = []

    def add(shape, joint, shade=0, name=""):
        out.append(Part(shape.xform(W[joint]), name=name, shade=shade))

    add(far_arm(), "sh_l", -1, "arm_l")
    add(far_fore(), "el_l", -1, "fore_l")
    add(torso(), "spine", 0, "torso")
    add(head(pose["visor"], pose["scan"], pose["beacon"]), "head", 0, "head")
    for side, sh in (("r", 0), ("l", -1)):
        add(thigh(), f"hip_{side}", sh, f"thigh_{side}")
        add(shin(), f"kn_{side}", sh, f"shin_{side}")
        add(foot(), f"an_{side}", sh, f"foot_{side}")
    add(upper_arm(), "sh_r", 0, "arm_r")
    add(far_fore(), "el_r", 0, "fore_r")
    out.append(Part(mirror(pose["glint"]).xform(W["spine"] @ trans(6.2 + pose["push"], 8.4, 2.0)), name="mirror", shade=0))
    return out


def muzzle(pose):
    W, _ = solve(pose)
    p = W["el_r"] @ np.array([0, -GUN_LEN, 0, 1.0])
    return p[0], p[1]


# ---------------------------------------------------------------------------------------------------------- animations
WALK = [(4.6, 0.0, 0), (2.3, 0.0, 0), (0.0, 0.0, 0), (-2.3, 0.0, 0), (-4.6, 0.4, -8), (-2.4, 3.0, -6),
        (1.4, 3.4, 4), (4.0, 1.4, 6)]


def walk_pose(i):
    bob = math.cos(4 * math.pi * i / 8)
    return mkpose(pelvis_y=PY - 1.1 + 0.5 * bob, spine=(0, 0, -6), head=(0, 0, 4),
                  foot_r=WALK[i], foot_l=WALK[(i + 4) % 8], beacon=(i // 2) % 2 == 0, scan=0.3,
                  glint=[None, None, -0.8, -0.3, None, None, None, None][i])


def guard_pose(push=0.0, glint=None, visor="mir_visor", recoil=0.0):
    return mkpose(pelvis_y=PY - 1.4, spine=(0, 0, -8 + 6 * recoil), head=(0, 0, 4), foot_r=(4.4, 0, 0),
                  foot_l=(-3.4, 0, 0), push=push - 1.2 * recoil, glint=glint, visor=visor, lean=-1.5 * recoil, scan=0.5)


def idle_pose(i):
    b = 0.5 - 0.5 * math.cos(2 * math.pi * i / 6)
    return mkpose(pelvis_y=PY - 0.8 - 0.4 * b, spine=(0, 0, -3 - b), foot_r=(2.8, 0, 0), foot_l=(-2.6, 0, 0),
                  scan=[-0.9, -0.3, 0.4, 0.9, 0.3, -0.4][i], beacon=i % 3 != 2,
                  glint=[-0.9, -0.5, -0.1, 0.3, 0.7, None][i])


def hurt_pose(i):
    k = [1.0, 0.8, 0.4, 0.15][i]
    return mkpose(pelvis_y=PY - 1.0 - 0.6 * k, spine=(0, 0, 14 * k), head=(0, 0, 16 * k), root=(-1.6 * k, 0),
                  foot_r=(4.6, 1.2 * k, 14 * k), foot_l=(-2.6, 0, 0), sh_l=(0, 0, 40 * k), el_l=(0, 0, 20),
                  visor="mir_visor" if i % 2 == 0 else "mir_visor_off", beacon=False, push=-1.0 * k)


ANIMS = [
    ("move", 12, "loop", 8, "careful walk behind the mirror, contact at 0 and 4"),
    ("attack", 14, "once", 6, "the mirror thrust forward, a glint runs across it (a shot glances off)"),
    ("idle", 8, "loop", 6, "visor scans, the sheen drifts across the mirror"),
    ("hurt", 14, "loop", 4, "jolted back, sparks"),
]


def frame(job):
    name, i = job
    if name == "move":
        return shoot(parts(walk_pose(i)))
    if name == "idle":
        return shoot(parts(idle_pose(i)))
    if name == "hurt":
        spr = shoot(parts(hurt_pose(i)))
        hx, hy = to_px(-1, 37)
        if i == 0:
            spark(spr, hx + 4, hy, 2)
        elif i == 1:
            spark(spr, hx - 2, hy - 2, 1)
            spark(spr, hx + 6, hy + 3, 1)
        elif i == 2:
            puff(spr, hx, hy - 2, 1.6)
        else:
            puff(spr, hx - 1, hy - 5, 1.2)
        return spr
    push, glint, rec = [(0.6, -0.9, 0.0), (1.4, -0.4, 0.3), (1.6, 0.1, 0.5), (1.4, 0.6, 0.3), (1.0, None, 0.1),
                        (0.6, None, 0.0)][i]
    spr = shoot(parts(guard_pose(push, glint, "mir_visor_hi" if i in (1, 2) else "mir_visor", rec)))
    if i in (1, 2):
        mx, my = to_px(9.6 + push, 26.0)
        spark(spr, mx, my - 2 * i, 2 if i == 1 else 1, c=("white", "cyan:6", "teal:4"))
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("mirrorbot", S64, A64, "mirror bot (episode 1 mirror walker, box 24 x 40, faces right)",
                      ANIMS, frames,
                      notes=["anchor = bottom centre of the box (feet on the ground line)",
                             "the mirror faces forward: plain shots from the front glance back (engine)",
                             "glow: magenta visor, cyan mirror edge, teal beacon, the glint"])
