"""sentry -- episode 1 shooter (box 22 x 40): a slim security robot on reverse-knee legs with a blaster arm.

64 x 64 frames, anchor (32, 60). It patrols (move), stops, aims and fires straight ahead (attack, the gun level in
every frame so the muzzle point holds), idle scans with its visor, hurt jolts back.
Model space: x forward (faces right), y up, z towards the near side; the body is yawed towards the viewer, the gun
arm is turned side-on (like the hero's cannon) so it reads at full length.
"""
import math

import numpy as np

from bake import Box, Capsule, Cylinder, Paint, Part, Rig, RoundCone, Sphere, Union, ik2, material, rot, trans
from models._e12_common import A64, S64, anim_jobs, make_sheet, point_of, puff, shoot, spark, to_px

YAW = -30.0

material("snt_white", ["slate:3", "slate:4", "steel:5", "steel:6", "steel:7", "white"],
         bands=[-0.6, -0.3, 0.05, 0.4, 0.8], line_lit="slate:2")
material("snt_yellow", ["orange:3", "yellow:3", "yellow:4", "yellow:5"], bands=[-0.4, 0.05, 0.7], line_lit="orange:2")
material("snt_dark", ["slate:1", "slate:2", "slate:3", "slate:4"], bands=[-0.4, 0.1, 0.7])
material("snt_steel", ["slate:1", "slate:2", "steel:3", "steel:4", "steel:6"], style="metal",
         bands=[-0.3, 0.15, 0.6], spec=0.93)
material("snt_gun", ["slate:1", "slate:2", "steel:3", "steel:5", "steel:7"], style="metal", bands=[-0.3, 0.1, 0.6],
         spec=0.92)
material("snt_helmet", ["slate:1", "slate:2", "slate:3", "steel:3", "steel:4"], bands=[-0.5, -0.1, 0.35, 0.75])
material("snt_visor", ["crimson:3", "red:3", "red:4", "red:5"], style="emit", bands=[0.2, 0.5, 0.85], prio=3.0)
material("snt_visor_hi", ["red:5", "orange:6", "white"], style="emit", bands=[0.3, 0.7], prio=3.5)
material("snt_visor_off", ["crimson:2", "crimson:3"], style="emit", bands=[0.5], prio=3.0)
material("snt_tip", ["red:3", "red:4", "red:5"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("snt_tip_hot", ["red:5", "orange:6", "yellow:7", "white"], style="emit", bands=[0.3, 0.6, 0.85], prio=3.0)
material("snt_beacon", ["teal:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.6, 0.9], prio=3.0)

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
             sh_r=(0, 0, 20), el_r=(0, 0, 40), sh_l=(0, 0, -12), el_l=(0, 0, 30),
             foot_r=(2.0, 0.0, 0.0), foot_l=(-2.0, 0.0, 0.0), visor="snt_visor", scan=0.0, tip="snt_tip",
             beacon=True, lean=0.0)
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
    chest = RoundCone((0, 6.0, 0), (0.4, 10.6, 0), 2.9, 3.9).m("snt_white")
    plate = Box(1.6, 2.8, 3.0, r=1.1).m("snt_white").at(1.9, 8.8, 0)
    stripe = Box(0.45, 2.4, 1.0, r=0.2).m("snt_beacon").at(3.45, 8.8, 1.2)
    waist = Cylinder(1.8, 2.0, rr=0.7).m("snt_dark").at(0, 3.0, 0)
    belt = Box(3.0, 0.9, 3.2, r=0.7).m("snt_yellow").at(0, 0.8, 0)
    hipbox = Box(2.6, 1.4, 3.4, r=0.9).m("snt_dark").at(0, -0.8, 0)
    back = Box(1.6, 3.2, 2.6, r=0.9).m("snt_dark").at(-3.4, 8.6, 0)
    return Union(chest, plate, stripe, waist, belt, hipbox, back)


HEAD_R = 3.5


def head(visor, scan, beacon):
    shell = Union(Cylinder(HEAD_R, 2.3, rr=1.3).at(0, 0, 0), Sphere(HEAD_R - 0.2).at(0, 0.8, 0)).m("snt_helmet")
    slit = Box(4.5, 1.25, 4.5).at(2.2, 0.1, 1.4)
    shell = Paint(shell, slit, visor)
    a = math.radians(15 + 55 * scan)
    dot = Box(1.4, 1.3, 1.4).rot(0, -math.degrees(a), 0).at(HEAD_R * math.cos(a), 0.1, HEAD_R * math.sin(a))
    shell = Paint(shell, dot, "snt_visor_hi")
    brow = Box(1.4, 0.6, 3.0, r=0.3).m("snt_yellow").at(2.6, 2.1, 0)
    fin = Box(2.4, 0.7, 0.7, r=0.35).m("snt_yellow").rot(0, 0, 10).at(-0.8, 4.2, 0)
    light = Sphere(1.05).m("snt_beacon" if beacon else "snt_dark").at(-1.8, 4.6, 0)
    neck = Cylinder(1.0, 1.4).m("snt_dark").at(0, -3.4, 0)
    return Union(shell, brow, fin, light, neck)


def upper_arm():
    return Union(Sphere(2.6).m("snt_yellow").at(0, -0.2, 0),
                 Capsule((0, -0.8, 0), (0, -L_UPPER + 0.6, 0), 1.35).m("snt_steel"),
                 Sphere(1.45).m("snt_dark").at(0, -L_UPPER, 0))


def gun(tip):
    """From the elbow (0) along -y to the muzzle (-GUN_LEN)."""
    L = GUN_LEN
    cuff = Cylinder(2.1, 1.3, rr=0.6).m("snt_white").at(0, -1.4, 0)
    body = Box(2.1, 2.9, 2.1, r=0.9).m("snt_gun").at(0, -4.6, 0)
    mag = Box(1.3, 1.5, 1.4, r=0.5).m("snt_yellow").at(-2.0, -4.4, 0)
    barrel = Cylinder(1.25, 2.4, rr=0.4).m("snt_gun").at(0, -L + 3.2, 0)
    ring = Cylinder(1.7, 0.5, rr=0.3).m("snt_dark").at(0, -L + 2.1, 0)
    em = Cylinder(1.4, 0.95, rr=0.45).m(tip).at(0, -L + 0.95, 0)
    return Union(cuff, body, mag, barrel, ring, em)


def far_arm():
    return Union(Sphere(2.0).m("snt_white").at(0, -0.2, 0),
                 Capsule((0, -0.8, 0), (0, -4.2, 0), 1.2).m("snt_steel"))


def far_fore():
    return Union(Capsule((0, 0, 0), (0, -4.0, 0), 1.15).m("snt_steel"), Sphere(1.5).m("snt_dark").at(0, -4.6, 0))


def thigh():
    return Union(Capsule((0, 0, 0), (0, -L_THIGH + 0.5, 0), 1.45).m("snt_steel"),
                 Sphere(1.9).m("snt_dark"))


def shin():
    return Union(Sphere(1.75).m("snt_yellow"),
                 RoundCone((0, -1.0, 0), (0, -L_SHIN + 0.8, 0), 1.75, 1.05).m("snt_white"))


def foot():
    return Union(Box(3.4, 0.9, 1.9, r=0.6).m("snt_dark").at(1.1, -ANKLE_H + 0.9, 0),
                 Box(1.3, 0.9, 1.6, r=0.5).m("snt_dark").at(-2.2, -ANKLE_H + 0.8, 0),
                 Sphere(1.3).m("snt_steel"))


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
    add(gun(pose["tip"]), "el_r", 0, "gun")
    return out


def muzzle(pose):
    W, _ = solve(pose)
    p = W["el_r"] @ np.array([0, -GUN_LEN, 0, 1.0])
    return p[0], p[1]


# ---------------------------------------------------------------------------------------------------------- animations
WALK = [(5.6, 0.0, 0), (2.8, 0.0, 0), (0.0, 0.0, 0), (-2.8, 0.0, 0), (-5.6, 0.4, -8), (-3.0, 3.4, -6),
        (1.6, 4.0, 4), (5.0, 1.6, 6)]


def walk_pose(i):
    c = math.cos(2 * math.pi * i / 8)
    bob = math.cos(4 * math.pi * i / 8)
    return mkpose(pelvis_y=PY - 0.9 + 0.6 * bob, spine=(0, 0, -4), head=(0, 0, 3),
                  foot_r=WALK[i], foot_l=WALK[(i + 4) % 8],
                  sh_r=(0, 0, 26 + 8 * c), el_r=(0, 0, 44 + 4 * c), sh_l=(0, 0, -10 - 16 * c), el_l=(0, 0, 26),
                  beacon=(i // 2) % 2 == 0, scan=0.2)


def aim_pose(k=0.0, recoil=0.0, tip="snt_tip", visor="snt_visor"):
    """Gun level: shoulder forward, elbow bent so the forearm is horizontal (rz sum = 90)."""
    return mkpose(pelvis_y=PY - 1.2 - 0.3 * k, spine=(0, 0, -3 + 4 * recoil), head=(0, 0, 2),
                  foot_r=(4.4, 0, 0), foot_l=(-3.4, 0, 0), sh_r=(0, 0, 18 - 6 * recoil), el_r=(0, 0, 72 - 4 * recoil),
                  sh_l=(0, 0, -20), el_l=(0, 0, 40), tip=tip, visor=visor, lean=-1.5 * recoil, scan=0.5)


def idle_pose(i):
    b = 0.5 - 0.5 * math.cos(2 * math.pi * i / 6)
    return mkpose(pelvis_y=PY - 0.6 - 0.4 * b, spine=(0, 0, -1 - b), foot_r=(2.8, 0, 0), foot_l=(-2.6, 0, 0),
                  sh_r=(0, 0, 24 - 3 * b), el_r=(0, 0, 38 + 4 * b), scan=[-0.9, -0.3, 0.4, 0.9, 0.3, -0.4][i],
                  beacon=i % 3 != 2)


def hurt_pose(i):
    k = [1.0, 0.8, 0.4, 0.15][i]
    return mkpose(pelvis_y=PY - 1.0 - 0.6 * k, spine=(0, 0, 14 * k), head=(0, 0, 16 * k), root=(-1.6 * k, 0),
                  foot_r=(4.6, 1.2 * k, 14 * k), foot_l=(-2.6, 0, 0), sh_r=(0, 0, -8 * k + 20), el_r=(0, 0, 30),
                  sh_l=(0, 0, 40 * k), el_l=(0, 0, 20), visor="snt_visor" if i % 2 == 0 else "snt_visor_off",
                  beacon=False)


ANIMS = [
    ("move", 14, "loop", 8, "patrol march, contact at 0 and 4"),
    ("attack", 10, "loop", 8, "gun level in every frame: charge 0-4, fire 5 (flash + recoil), recover 6-7"),
    ("idle", 8, "loop", 6, "visor light scans"),
    ("hurt", 14, "loop", 4, "jolted back, sparks"),
]


def attack_spec(i):
    if i <= 4:
        return aim_pose(k=i / 4.0, tip="snt_tip" if i < 2 else "snt_tip_hot"), i
    return aim_pose(recoil=[1.0, 0.5, 0.15][i - 5], tip="snt_tip_hot" if i == 5 else "snt_tip"), i


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
    pose, k = attack_spec(i)
    spr = shoot(parts(pose))
    mx, my = muzzle(pose)
    px, py = to_px(mx, my)
    if k in (2, 3, 4):           # gathering charge at the tip
        r = [0.8, 1.2, 1.7][k - 2]
        for a in range(0, 360, 90 if k < 4 else 45):
            d = 2 + (4 - k) * 1.5
            spr.put(int(round(px + 1 + d * math.cos(math.radians(a + 45 * k)))),
                    int(round(py + d * math.sin(math.radians(a + 45 * k)))), "red:5" if k < 4 else "orange:6",
                    glow=True)
        spark(spr, px + 1, py, 1 if r < 1.5 else 2, c=("white", "orange:6", "red:4"))
    elif k == 5:                 # muzzle flash
        spark(spr, px + 2, py, 2, c=("white", "yellow:6", "red:4"))
        for d in range(3, 6):
            spr.put(px + 1 + d, py, "orange:6" if d < 5 else "red:4", glow=True)
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    pose, _ = attack_spec(5)
    mx, my = muzzle(aim_pose())
    dx, dy = point_of(mx + 1.0, my)
    return make_sheet("sentry", S64, A64, "security sentry robot (episode 1 shooter, box 22 x 40, faces right)",
                      ANIMS, frames, points=[("muzzle", dx, dy, "blaster tip in the attack pose (red enemy_bolt)")],
                      notes=["anchor = bottom centre of the box (feet on the ground line)",
                             "glow: red visor, blaster tip (charging in attack 2-5), teal beacon and chest light"])
