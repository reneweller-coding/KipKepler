"""Kip Kepler, cadet of the Beacon Corps -- the hero sheet (64 x 64, anchor at the feet centre).

Model space: x forward (he faces right), y up, z towards his right side (the near side). The whole model is yawed
towards the viewer (YAW) so the visor and chest read. Lengths in target pixels.
"""
import math

import numpy as np

from bake import (Box, Capsule, Cone, Cylinder, Ellipsoid, Extrude, Paint, Part, Rig, RoundCone, Sphere, Subtract,
                  Torus, Union, ik2, material, rot, trans)

YAW = -38.0
ANCHOR = (32, 60)
SIZE = (64, 64)
RENDER_ANCHOR = (32, 59)     # world y = 0 one row up, so the 1 px outline under the soles is row 59

# ---------------------------------------------------------------------------------------------------------- materials
B4 = [-0.42, 0.02, 0.80]
material("kip_white", ["slate:4", "slate:5", "steel:6", "steel:7", "white"], bands=[-0.5, -0.1, 0.45, 0.86],
         line_lit="slate:2")
material("kip_orange", ["orange:2", "orange:3", "orange:4", "orange:5"], bands=B4, line_lit="orange:1")
material("kip_dark", ["slate:1", "slate:2", "slate:3", "slate:4"], bands=[-0.4, 0.1, 0.75])
material("kip_sole", ["slate:1", "slate:2"], bands=[0.3])
material("kip_visor", ["blue:2", "cyan:3", "cyan:4", "cyan:5", "cyan:6", "white"], style="glass",
         bands=[-0.45, -0.05, 0.45, 0.8], spec=0.95, line="outline")
material("kip_glint", ["white"], style="flat", prio=1.0)
material("kip_gun", ["steel:2", "steel:3", "steel:4", "steel:6", "white"], style="metal", bands=[-0.4, 0.1, 0.75],
         spec=0.93)
material("kip_tip", ["cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.75], prio=3.0)
material("kip_light", ["red:4", "orange:5"], style="emit", bands=[0.6], prio=3.0)
material("kip_chestlight", ["cyan:5", "cyan:6"], style="emit", bands=[0.6], prio=2.0)
material("kip_flame", ["orange:3", "orange:4", "yellow:4", "yellow:6"], style="emit", bands=[0.25, 0.55, 0.85],
         line="orange:2", line_lit="orange:2", inner=False)

# ---------------------------------------------------------------------------------------------------------- skeleton
L_THIGH, L_SHIN, ANKLE_H = 7.0, 6.6, 2.1
L_UPPER, L_FORE = 5.4, 4.8
HIP_DROP = 0.8
PELVIS_Y = ANKLE_H + L_SHIN + L_THIGH + HIP_DROP  # standing straight

RIG = Rig()
RIG.joint("pelvis", None, (0, PELVIS_Y, 0))
RIG.joint("spine", "pelvis", (0, 1.2, 0))
RIG.joint("head", "spine", (0.7, 11.6, 0))
RIG.joint("pack", "spine", (0, 0, 0))
for side, z in (("r", 1), ("l", -1)):
    RIG.joint(f"sh_{side}", "spine", (0.1, 9.0, 5.7 * z))
    RIG.joint(f"el_{side}", f"sh_{side}", (0, -L_UPPER, 0))
    RIG.joint(f"wr_{side}", f"el_{side}", (0, -L_FORE, 0))
    RIG.joint(f"hip_{side}", "pelvis", (0, -HIP_DROP, 3.0 * z))
    RIG.joint(f"kn_{side}", f"hip_{side}", (0, -L_THIGH, 0))
    RIG.joint(f"an_{side}", f"kn_{side}", (0, -L_SHIN, 0))

# ---------------------------------------------------------------------------------------------------------- shapes
HEAD_R = 8.3
HEAD_C = (0.4, 8.2, 0.0)
VISOR = (6.0, 4.6, 7.9, 6.2, -0.6)   # cut box half extents x, y, z and its centre x, y (head space)


def _helmet():
    shell = Sphere(HEAD_R).m("kip_white")
    cut = Box(VISOR[0], VISOR[1], VISOR[2], r=3.2).at(VISOR[3], VISOR[4], 0)
    shell = Subtract(shell, cut)
    # ear pods: a dark hub ringed in orange, set back behind the visor
    ear = Cylinder(2.0, 0.8, rr=0.45).m("kip_orange").rot(90, 0, 0)
    ear_r = ear.at(-3.4, -1.6, HEAD_R - 0.6)
    ear_l = ear.at(-3.4, -1.6, -(HEAD_R - 0.6))
    hub = Cylinder(0.95, 0.5, rr=0.3).m("kip_dark").rot(90, 0, 0).at(-3.4, -1.6, HEAD_R + 0.3)
    # fin along the top
    fin = Extrude([(-6.5, 4.5), (-3.0, 9.7), (1.5, 9.6), (3.5, 7.0), (0.0, 6.0)], 0.9, r=0.5).m("kip_orange")
    return Union(shell, ear_r, ear_l, hub, fin).at(*HEAD_C)


def _visor(glint=None):
    v = Sphere(HEAD_R - 0.9).m("kip_visor")
    if glint is not None:
        band = Box(0.75, 9, 9).rot(0, 0, 32).at(glint, 0, 0)
        v = Paint(v, band, "kip_glint")
    return v.at(*HEAD_C)


def _antenna(blink=True):
    stalk = Capsule((0, 0, 0), (-3.2, 5.4, 0), 0.45).m("kip_dark")
    tip = Sphere(1.0).m("kip_light" if blink else "kip_dark").at(-3.2, 5.6, 0)
    return Union(stalk, tip).at(HEAD_C[0] - 3.4, HEAD_C[1] - 0.2, HEAD_R - 0.6)


def _torso():
    body = Box(4.7, 5.6, 5.0, r=2.8).m("kip_orange").at(0, 5.9, 0)
    belt = Box(5.0, 1.1, 5.3, r=1.0).m("kip_dark").at(0, 0.7, 0)
    collar = Torus(3.7, 1.25).m("kip_dark").at(0.5, 11.4, 0)
    return Union(body, belt, collar)


def _pack(thrust):
    shell = Box(2.6, 4.7, 4.3, r=1.7).m("kip_white").at(-6.9, 6.6, 0)
    cap = Box(2.8, 1.3, 4.5, r=1.1).m("kip_orange").at(-6.9, 10.6, 0)
    strap = Box(0.6, 4.2, 4.95, r=0.5).m("kip_dark").at(-4.2, 6.6, 0)
    parts = [shell, cap, strap]
    for z in (2.3, -2.3):
        parts.append(Cone(1.55, 1.05, 1.0).m("kip_dark").at(-7.4, 1.2, z))
    return Union(*parts)


def _flames(thrust, flick):
    if thrust <= 0:
        return None
    out = []
    for k, z in enumerate((2.3, -2.3)):
        ln = thrust * (1.0 + 0.18 * math.sin(flick * 2.4 + k * 1.7))
        out.append(RoundCone((-7.4, 0.2, z), (-8.0 - 0.4 * ln, 0.2 - 1.15 * ln, z), 1.6, 0.4).m("kip_flame"))
    return Union(*out)


def _upper_arm():
    return Union(Sphere(2.45).m("kip_white").at(0, -0.4, 0),
                 Capsule((0, -1.0, 0), (0, -L_UPPER + 0.6, 0), 1.95).m("kip_white"))


def _elbow():
    return Sphere(1.75).m("kip_dark")


def _forearm_l():
    return Union(Capsule((0, 0, 0), (0, -L_FORE + 1.2, 0), 1.75).m("kip_white"),
                 Cylinder(2.0, 0.9, rr=0.5).m("kip_orange").at(0, -L_FORE + 1.4, 0),
                 Sphere(1.9).m("kip_dark").at(0, -L_FORE - 0.4, 0))


CANNON_LEN = 9.4


def _cannon():
    """The arm cannon replaces the right forearm: from the elbow (0) along -y to the muzzle (-CANNON_LEN)."""
    L = CANNON_LEN
    cuff = Cylinder(3.0, 1.1, rr=0.6).m("kip_orange").at(0, -1.5, 0)
    body = Cylinder(3.0, L * 0.30, rr=1.2).m("kip_gun").at(0, -L * 0.50, 0)
    band = Cylinder(3.1, 0.65, rr=0.4).m("kip_orange").at(0, -L * 0.74, 0)
    nose = Cone(2.7, 2.2, 0.8).m("kip_gun").at(0, -L + 2.2, 0)
    tip = Cylinder(2.05, 1.0, rr=0.35).m("kip_tip").at(0, -L + 0.75, 0)
    return Union(cuff, body, band, nose, tip)


def _thigh():
    return Capsule((0, 0, 0), (0, -L_THIGH + 0.8, 0), 2.55).m("kip_orange")


def _knee():
    return Sphere(1.95).m("kip_dark")


def _shin():
    return Union(RoundCone((0, -0.6, 0), (0, -L_SHIN + 1.2, 0), 2.05, 2.25).m("kip_white"))


def _boot():
    upper = Box(2.6, 1.9, 2.5, r=1.3).m("kip_orange").at(0.1, 0.0, 0)
    foot = Box(4.0, 1.4, 2.65, r=1.3).m("kip_orange").at(1.1, -1.0, 0)
    sole = Box(4.15, 0.55, 2.7, r=0.5).m("kip_sole").at(1.1, -ANKLE_H + 0.55, 0)
    return Union(upper, foot, sole)


SHAPES = None


def shapes():
    global SHAPES
    if SHAPES is None:
        SHAPES = dict(helmet=_helmet(), torso=_torso(), upper=_upper_arm(), elbow=_elbow(), fore_l=_forearm_l(),
                      cannon=_cannon(), thigh=_thigh(), knee=_knee(), shin=_shin(), boot=_boot())
    return SHAPES


# ---------------------------------------------------------------------------------------------------------- posing

BASE = dict(
    root=(0.0, 0.0),        # world offset of the model origin (feet centre on the ground)
    body_rot=0.0,           # whole-body roll about the root (die)
    yaw=YAW,
    gun_ry=None,            # shoulder twist that shows the cannon side-on (None = -yaw)
    leg_ry=16.0,            # hips turned back towards a side view (legs swing nearly in the picture plane)
    pelvis_x=0.0, pelvis_y=PELVIS_Y - 0.3,
    pelvis=(0, 0, 0), spine=(0, 0, 0), head=(0, 0, 0),
    sh_r=(-6, 0, 8), el_r=(0, 0, 58), sh_l=(6, 0, -10), el_l=(0, 0, 28), wr_l=(0, 0, 0),
    foot_r=(2.6, 0.0, 0.0), foot_l=(-2.4, 0.0, 0.0),
    squash=(1.0, 1.0),
    thrust=0.0, flick=0.0, glint=None, blink=True,
    arm_front=False,        # draw the cannon arm over everything (raised in front of the helmet)
)


def mkpose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


BOOT_SOLE = ((-2.95, -ANKLE_H), (5.15, -ANKLE_H))   # heel and toe under the ankle


def _leg_ik(pose, P, side):
    fx, fy, pitch = pose[f"foot_{side}"]
    sp, cp = math.sin(math.radians(pitch)), math.cos(math.radians(pitch))
    low = min(x * sp + y * cp for x, y in BOOT_SOLE)       # lowest sole point after the pitch
    fy = max(fy, -low - ANKLE_H)                          # keep heel and toe out of the floor
    hip = P[f"hip_{side}"][:3, 3]
    a1, a2 = ik2((hip[0], hip[1]), (fx, fy + ANKLE_H), L_THIGH, L_SHIN, bend=1.0)
    parent = pose["pelvis"][2]
    pose[f"hip_{side}"] = (0, 0, a1 - parent)
    pose[f"kn_{side}"] = (0, 0, a2)
    pose[f"an_{side}"] = (0, 0, pitch - (a1 + a2))


def solve(pose):
    """Returns the model->world matrices of all joints for a pose dict."""
    pose = dict(pose)
    rx, ry, rz = pose["sh_r"]
    gun = -pose["yaw"] if pose["gun_ry"] is None else pose["gun_ry"]
    pose["sh_r"] = (rx, ry + gun, rz)
    RIG.joints["pelvis"] = (None, np.array([pose["pelvis_x"], pose["pelvis_y"], 0.0]))
    P0 = RIG.solve(pose)
    for side in ("r", "l"):
        if pose.get(f"foot_{side}") is not None and f"hip_{side}" not in pose:
            _leg_ik(pose, P0, side)
    lr = pose["leg_ry"]
    if lr:
        px, py, pz = pose["pelvis"]
        sx, sy, sz = pose["spine"]
        pose["pelvis"] = (px, py + lr, pz)
        pose["spine"] = (sx, sy - lr, sz)
    base = trans(pose["root"][0], pose["root"][1], 0) @ rot(0, 0, pose["body_rot"]) @ rot(0, pose["yaw"], 0)
    return RIG.solve(pose, base), pose


def parts(pose):
    S = shapes()
    W, pose = solve(pose)
    out = []

    def add(shape, joint, M=None, shade=0, name="", inner=True, zbias=0.0):
        if shape is None:
            return
        X = W[joint] if M is None else W[joint] @ M
        out.append(Part(shape.xform(X), name=name, shade=shade, inner=inner, zbias=zbias))

    add(S["helmet"], "head", name="helmet")
    add(_visor(pose["glint"]), "head", name="visor")
    add(_antenna(pose["blink"]), "head", name="antenna")
    add(S["torso"], "spine", name="torso")
    add(_pack(pose["thrust"]), "spine", name="pack")
    add(_flames(pose["thrust"], pose["flick"]), "spine", name="flame", inner=False)
    add(Box(3.9, 2.3, 4.3, r=1.8).m("kip_orange").at(0, -0.6, 0), "pelvis", name="pelvis")
    for side, sh in (("r", 0), ("l", -1)):
        add(S["thigh"], f"hip_{side}", shade=sh, name=f"thigh_{side}")
        add(S["knee"], f"kn_{side}", shade=sh, name=f"knee_{side}")
        add(S["shin"], f"kn_{side}", shade=sh, name=f"shin_{side}")
        add(S["boot"], f"an_{side}", shade=sh, name=f"boot_{side}")
    add(S["upper"], "sh_l", shade=-1, name="upper_l")
    add(S["elbow"], "el_l", shade=-1, name="elbow_l")
    add(S["fore_l"], "el_l", shade=-1, name="fore_l")
    zb = 30.0 if pose["arm_front"] else 0.0
    add(S["upper"], "sh_r", name="upper_r", zbias=zb)
    add(S["elbow"], "el_r", name="elbow_r", zbias=zb)
    add(S["cannon"], "el_r", name="cannon", zbias=zb)
    return out, W


def muzzle(pose):
    W, _ = solve(pose)
    p = W["el_r"] @ np.array([0, -CANNON_LEN, 0, 1.0])
    return p[0], p[1]


# ---------------------------------------------------------------------------------------------------------- aiming

def aim(p, ang, elbow=0.0, iters=4):
    """Points the cannon (forearm) at world angle `ang` degrees (0 = forward, 90 = up); the elbow keeps a bend of
    `elbow` degrees and the shoulder is solved for."""
    p = dict(p)
    p["el_r"] = (0, 0, elbow)
    rx = p["sh_r"][0]
    rz = ang + 90 - elbow - p["spine"][2] - p["pelvis"][2] - p["body_rot"]
    for _ in range(iters):
        p["sh_r"] = (rx, 0, rz)
        W, _ = solve(p)
        a = W["el_r"] @ np.array([0, 0, 0, 1.0])
        b = W["el_r"] @ np.array([0, -CANNON_LEN, 0, 1.0])
        got = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        rz += ((ang - got + 180) % 360) - 180
    p["sh_r"] = (rx, 0, rz)
    return p


def world_point(pose, joint, local):
    W, _ = solve(pose)
    q = W[joint] @ np.array([*local, 1.0])
    return q[0], q[1]


def muzzle_px(pose):
    """Muzzle offset from the anchor in sheet convention (dx right, dy down), squash included."""
    x, y = muzzle(pose)
    sx, sy = pose["squash"]
    return x * sx, -(y * sy) - (ANCHOR[1] - RENDER_ANCHOR[1])


# ---------------------------------------------------------------------------------------------------------- animations
from bake import PAL, Sheet, col, empty_sprite, pixelize, render  # noqa: E402

PY = BASE["pelvis_y"]
TAU = 2 * math.pi


def P(**kw):
    return mkpose(**kw)


def F(pose, **post):
    """A frame spec: a pose plus post effects (tint, scan, beam, sparks, sparkle, ground, lift, smoke)."""
    return dict(pose=pose, **post)


def idle(i, n=8):
    b = 0.5 - 0.5 * math.cos(TAU * i / n)
    glints = {2: -1.5, 3: 1.8, 4: 4.6}
    return P(pelvis_y=PY - 0.75 * b, spine=(0, 0, 0.6 - 1.8 * b), head=(0, 0, 1.0 - 2.4 * b),
             sh_l=(6, 0, -10 + 4 * b), el_l=(0, 0, 26 + 6 * b), sh_r=(-6, 0, 8 - 3 * b), el_r=(0, 0, 58 + 4 * b),
             glint=glints.get(i), blink=i < 4)


RUN_FOOT = [(7.6, 0.0, 14), (3.4, 0.0, 0), (-1.8, 0.0, 0), (-6.6, 0.5, -22), (-9.8, 3.6, -48), (-8.8, 7.6, -64),
            (-4.0, 9.2, -38), (2.6, 8.6, -8), (7.4, 6.0, 8), (9.2, 2.6, 16)]


def run(i, shoot=False):
    phi = i / 10.0
    c = math.cos(TAU * phi)
    bob = math.cos(2 * TAU * (phi - 0.1))
    p = P(pelvis_x=1.2, pelvis_y=PY - 1.3 - 0.8 * bob, spine=(0, -7 * c, -13), head=(0, 0, 10 + 2 * bob),
          sh_l=(8, 0, 48 * c), el_l=(0, 0, 72 - 12 * c), sh_r=(-8, 0, 18 - 30 * c), el_r=(0, 0, 78 + 10 * c),
          foot_r=RUN_FOOT[i], foot_l=RUN_FOOT[(i + 5) % 10], flick=i)
    if shoot:
        p.update(spine=(0, 8, -6), head=(0, 0, 5 + 2 * bob))
        p = aim(p, 0)
    return p


def jump_poses():
    return [
        P(pelvis_y=PY - 2.6, spine=(0, 0, -14), head=(0, 0, 9), sh_l=(6, 0, -38), el_l=(0, 0, 45),
          sh_r=(-6, 0, -22), el_r=(0, 0, 76), foot_r=(2.8, 0, 0), foot_l=(-2.4, 0, 0), squash=(1.1, 0.89),
          thrust=1.2, flick=0),
        P(pelvis_y=PY, spine=(0, 0, 3), head=(0, 0, 7), sh_l=(8, 0, 150), el_l=(0, 0, 25), sh_r=(-8, 0, 55),
          el_r=(0, 0, 45), foot_r=(1.6, 1.2, -42), foot_l=(-1.8, 1.8, -52), squash=(0.92, 1.1), thrust=6.5,
          flick=1),
        P(pelvis_y=PY, spine=(0, 0, -2), head=(0, 0, 5), sh_l=(8, 0, 128), el_l=(0, 0, 42), sh_r=(-8, 0, 48),
          el_r=(0, 0, 58), foot_r=(4.2, 5.6, -10), foot_l=(-2.6, 2.4, -42), thrust=5.0, flick=2),
        P(pelvis_y=PY, spine=(0, 0, -4), head=(0, 0, 3), sh_l=(10, 0, 112), el_l=(0, 0, 52), sh_r=(-8, 0, 40),
          el_r=(0, 0, 66), foot_r=(4.6, 6.6, -4), foot_l=(-1.8, 3.6, -30), thrust=3.8, flick=3),
    ]


def apex_poses():
    out = []
    for k in range(3):
        w = (-1, 0, 1)[k]
        out.append(P(pelvis_y=PY + 0.3, spine=(0, 0, -3), head=(0, 0, 2), sh_l=(10, 0, 70 + 6 * w), el_l=(0, 0, 60),
                     sh_r=(-10, 0, -34 - 4 * w), el_r=(0, 0, 100), foot_r=(4.4, 7.6, -4), foot_l=(-0.8, 5.8, -22),
                     thrust=1.6 + 0.5 * (k % 2), flick=k + 4, squash=(1.03, 0.98)))
    return out


def fall_poses():
    out = []
    for k in range(4):
        w = (1, 0, -1, 0)[k]
        out.append(P(pelvis_y=PY + 0.2, spine=(0, 0, 3), head=(0, 0, -6), sh_l=(10, 0, -128 + 10 * w),
                     el_l=(0, 0, 25), sh_r=(-10, 0, 104 - 8 * w), el_r=(0, 0, 18), foot_r=(3.6, 2.8 + 0.6 * w, -20),
                     foot_l=(-2.4, 1.2 - 0.5 * w, -42)))
    return out


def land_poses():
    return [
        P(pelvis_x=0.6, pelvis_y=PY - 3.6, spine=(0, 0, -17), head=(0, 0, 11), sh_l=(8, 0, -42), el_l=(0, 0, 52),
          sh_r=(-8, 0, -18), el_r=(0, 0, 84), foot_r=(3.2, 0, 0), foot_l=(-3.0, 0, 0), squash=(1.13, 0.87)),
        P(pelvis_x=0.4, pelvis_y=PY - 2.4, spine=(0, 0, -10), head=(0, 0, 7), sh_l=(8, 0, -28), el_l=(0, 0, 44),
          sh_r=(-8, 0, -6), el_r=(0, 0, 72), foot_r=(3.0, 0, 0), foot_l=(-2.8, 0, 0), squash=(1.05, 0.95)),
        P(pelvis_y=PY + 0.2, spine=(0, 0, -1), head=(0, 0, 2), sh_l=(6, 0, -14), el_l=(0, 0, 30), sh_r=(-6, 0, 6),
          el_r=(0, 0, 60), foot_r=(2.7, 0, 0), foot_l=(-2.5, 0, 0), squash=(0.97, 1.03)),
        idle(0),
    ]


UP_ELBOW = 10.0


def shoot_base(up=False):
    if up:
        return P(pelvis_x=0.5, pelvis_y=PY - 0.9, spine=(0, 0, 3), head=(0, 0, 12), sh_l=(10, 0, -40),
                 el_l=(0, 0, 40), sh_r=(-4, 0, 0), foot_r=(3.6, 0, 0), foot_l=(-3.4, 0, 0), arm_front=True)
    return P(pelvis_y=PY - 0.7, spine=(0, 12, -3), head=(0, 0, 4), sh_l=(10, 0, -24), el_l=(0, 0, 46),
             foot_r=(3.6, 0, 0), foot_l=(-3.4, 0, 0))


def shoot_poses(up=False):
    b = shoot_base(up)
    ang = 90 if up else 0
    kick = dict(b)
    if up:
        kick.update(pelvis_y=PY - 1.8, spine=(0, 0, 5))
    else:
        kick.update(pelvis_x=-0.9, spine=(0, 12, 1))
    el = UP_ELBOW if up else 0.0
    return [aim(kick, ang, el), aim(b, ang, el), aim(b, ang, el), aim(b, ang, el)]


def hurt_poses():
    return [
        P(pelvis_x=-1.0, pelvis_y=PY - 0.4, spine=(0, -8, 16), head=(0, 0, 22), sh_l=(12, 0, 132), el_l=(0, 0, 30),
          sh_r=(-12, 0, -48), el_r=(0, 0, 30), foot_r=(4.2, 1.6, 22), foot_l=(-1.5, 0, 0), squash=(0.95, 1.04)),
        P(pelvis_x=-1.6, pelvis_y=PY - 0.6, spine=(0, -6, 21), head=(0, 0, 17), sh_l=(12, 0, 112), el_l=(0, 0, 40),
          sh_r=(-12, 0, -36), el_r=(0, 0, 46), foot_r=(4.6, 2.4, 26), foot_l=(-2.0, 0.4, 10)),
        P(pelvis_x=-0.5, pelvis_y=PY - 0.8, spine=(0, 0, 8), head=(0, 0, 8), sh_l=(8, 0, 40), el_l=(0, 0, 40),
          sh_r=(-8, 0, 0), el_r=(0, 0, 60), foot_r=(3.0, 0.4, 10), foot_l=(-2.4, 0, 0)),
    ]


def lying(rot_deg, lift=0.0, knees=1.0, arm=0.0):
    """Kip on his back: hips flexed, knees up."""
    p = P(body_rot=rot_deg, root=(19.0 * math.sin(math.radians(rot_deg)), 12.0 + lift), pelvis_y=PY,
          spine=(0, 0, 4), leg_ry=0.0,
          head=(0, 0, 10), sh_l=(14, 0, 120 + 20 * arm), el_l=(0, 0, 40), sh_r=(-14, 0, 150 - 15 * arm),
          el_r=(0, 0, 30), foot_r=None, foot_l=None, blink=False)
    p.update({"hip_r": (0, 0, 58 * knees), "kn_r": (0, 0, -95 * knees), "an_r": (0, 0, 40 * knees),
              "hip_l": (0, 0, 38 * knees), "kn_l": (0, 0, -70 * knees), "an_l": (0, 0, 30 * knees)})
    return p


def die_frames():
    h = hurt_poses()
    fr = [F(h[0]),
          F(P(pelvis_x=-2.2, pelvis_y=PY - 1.2, spine=(0, -5, 25), head=(0, 0, 26), sh_l=(14, 0, 150),
              el_l=(0, 0, 25), sh_r=(-14, 0, -60), el_r=(0, 0, 25), foot_r=(5.2, 3.2, 32), foot_l=(-1.0, 0, 5)),
            ground=True),
          F(P(body_rot=28, root=(4.0, 6.0), spine=(0, 0, 18), head=(0, 0, 22), sh_l=(14, 0, 160), el_l=(0, 0, 25),
              sh_r=(-14, 0, 160), el_r=(0, 0, 25), foot_r=(6.0, 4.0, 30), foot_l=(2.0, 1.0, 20)), ground=True),
          F(lying(62, knees=0.6, arm=1.0), ground=True),
          F(dict(lying(90, knees=0.8, arm=1.0), squash=(1.06, 0.9)), ground=True, sparks=0),
          F(lying(86, knees=1.1, arm=0.5), ground=True, lift=3, sparks=1),
          F(lying(90, knees=1.0, arm=0.0), ground=True, sparks=2)]
    for k in range(5):
        fr.append(F(lying(90, knees=1.0, arm=-0.15 * (k % 2)), ground=True, sparks=3 + k, smoke=k))
    return fr


def teleport_frames():
    st = dict(idle(0), head=(0, 0, 10), spine=(0, 0, 2))
    return [
        F(st, sparkle=0),
        F(st, tint=True, sparkle=1),
        F(st, tint=True, scan=0),
        F(dict(st, squash=(0.74, 1.12)), tint=True, scan=1),
        F(dict(st, squash=(0.48, 1.26)), tint=True, scan=0, beam=(1, 0, 64)),
        F(dict(st, squash=(0.24, 1.42)), tint=True, scan=1, beam=(2, 0, 64)),
        F(None, beam=(2, 0, 64)),
        F(None, beam=(1, 18, 64)),
        F(None, beam=(0, 40, 64), sparkle=2),
        F(None, sparkle=3),
    ]


def appear_frames():
    st = idle(0)
    return [
        F(None, beam=(0, 30, 64)),
        F(None, beam=(1, 0, 64)),
        F(None, beam=(2, 0, 64)),
        F(dict(st, squash=(0.26, 1.4)), tint=True, scan=0, beam=(2, 0, 64)),
        F(dict(st, squash=(0.55, 1.22)), tint=True, scan=1, beam=(1, 0, 64)),
        F(dict(st, squash=(0.84, 1.07)), tint=True, scan=0),
        F(st, tint=True, scan=1),
        F(st, tint=True),
        F(dict(land_poses()[1]), sparkle=1),
        F(idle(0)),
    ]


def victory_frames():
    """Crouch, hop while turning to the camera, land, both arms up in a V (fist pump)."""
    crouch = P(pelvis_y=PY - 2.8, spine=(0, 0, -12), head=(0, 0, 10), sh_l=(8, 0, -30), el_l=(0, 0, 50),
               sh_r=(-8, 0, -10), el_r=(0, 0, 80), foot_r=(2.8, 0, 0), foot_l=(-2.6, 0, 0), squash=(1.08, 0.92))

    def v(yaw, lift, k, air, sq=(1.0, 1.0), th=0.0, glint=None, py=PY, pump=0.0):
        p = P(yaw=yaw, gun_ry=0.0, leg_ry=0.0, root=(0, lift), pelvis_y=py, spine=(0, 0, 0), head=(0, 0, 8),
              sh_r=(-150 * k, 0, 0), el_r=(0, 0, 0), sh_l=(140 * k, 0, 0), el_l=(0, 0, 30 + 40 * pump),
              squash=sq, thrust=th, flick=int(lift), glint=glint)
        if air:
            p.update(foot_r=(2.0, 3.4, -20), foot_l=(-1.0, 2.6, -30))
        else:
            p.update(foot_r=(1.2, 0, 0), foot_l=(-1.2, 0, 0))
        return p

    out = [F(crouch),
           F(v(-58, 5, 0.6, True, (0.94, 1.07), 4.0)),
           F(v(-72, 8, 0.9, True, th=2.5)),
           F(v(-80, 9, 1.0, True, th=1.0)),
           F(v(-80, 6, 1.0, True)),
           F(v(-80, 2, 1.0, False)),
           F(v(-80, 0, 0.95, False, (1.08, 0.92), py=PY - 2.4)),
           F(v(-80, 0, 1.0, False, glint=-1.5, pump=1.0)),
           F(v(-80, 0, 1.0, False, glint=2.0, pump=0.4)),
           F(v(-80, 0, 1.0, False, pump=1.0))]
    return out


PUSH_FOOT = [(-1.0, 0, 0), (-2.4, 0, 0), (-3.8, 0, 0), (-5.2, 0, -8), (-6.4, 0.8, -26), (-4.4, 3.4, -22),
             (-2.0, 3.2, -6), (-0.6, 1.0, 0)]


def push_poses():
    out = []
    for i in range(8):
        b = math.sin(TAU * i / 8)
        p = P(pelvis_x=2.4, pelvis_y=PY - 1.8 + 0.3 * abs(b), spine=(0, 4 * b, -30), head=(0, 0, 20),
              sh_l=(6, 0, 108 + 4 * b), el_l=(0, 0, 18), foot_r=PUSH_FOOT[i], foot_l=PUSH_FOOT[(i + 4) % 8], flick=i)
        out.append(aim(p, -6 + 3 * b))
    return out


def lookup_poses():
    return [P(head=(0, 0, 11), spine=(0, 0, 2), sh_r=(-6, 0, 6), el_r=(0, 0, 60)),
            P(head=(0, 0, 22), spine=(0, 0, 4), pelvis_y=PY - 0.2, sh_r=(-6, 0, 4), el_r=(0, 0, 62)),
            P(head=(0, 0, 23), spine=(0, 0, 4), pelvis_y=PY - 0.4, sh_r=(-6, 0, 4), el_r=(0, 0, 62), glint=2.0)]


def skid_poses():
    return [
        P(pelvis_x=-1.6, pelvis_y=PY - 3.0, spine=(0, -6, 18), head=(0, 0, -4), sh_l=(12, 0, 118), el_l=(0, 0, 30),
          sh_r=(-12, 0, -34), el_r=(0, 0, 50), foot_r=(7.6, 0, 24), foot_l=(-3.6, 0, 0), squash=(1.05, 0.95)),
        P(pelvis_x=-1.2, pelvis_y=PY - 2.6, spine=(0, -5, 15), head=(0, 0, -2), sh_l=(12, 0, 104), el_l=(0, 0, 36),
          sh_r=(-12, 0, -24), el_r=(0, 0, 56), foot_r=(7.2, 0, 20), foot_l=(-3.4, 0, -4)),
        P(pelvis_x=-0.6, pelvis_y=PY - 1.8, spine=(0, -3, 10), head=(0, 0, 0), sh_l=(10, 0, 80), el_l=(0, 0, 40),
          sh_r=(-10, 0, -10), el_r=(0, 0, 62), foot_r=(6.2, 0, 12), foot_l=(-3.0, 0, 0)),
    ]


def air_shoot(poses, up=False):
    out = []
    for p in poses:
        q = dict(p)
        sx, sy = q["squash"]
        q.update(spine=(0, 8, q["spine"][2]), squash=(1 + (sx - 1) * 0.4, 1 + (sy - 1) * 0.4))
        if up:
            q.update(spine=(0, 0, q["spine"][2] + 3), head=(0, 0, 12), sh_r=(-4, 0, 0), arm_front=True)
        out.append(aim(q, 90 if up else 0, UP_ELBOW if up else 0.0))
    return out


ANIMS = None


def anims():
    """[(name, fps, mode, [frame spec...], note)] -- frame specs are dicts (see F)."""
    global ANIMS
    if ANIMS is not None:
        return ANIMS
    A = []
    A.append(("idle", 8, "loop", [F(idle(i)) for i in range(8)], "breathing, visor glint, antenna blink"))
    A.append(("run", 22, "loop", [F(run(i)) for i in range(10)], "contact at 0 and 5"))
    A.append(("run_shoot", 22, "loop", [F(run(i, True)) for i in range(10)], "same phase as run"))
    A.append(("jump", 16, "once", [F(p) for p in jump_poses()], "crouch, stretch, rise x2 (thrusters)"))
    A.append(("apex", 12, "loop", [F(p) for p in apex_poses()], ""))
    A.append(("fall", 12, "loop", [F(p) for p in fall_poses()], ""))
    A.append(("land", 20, "once", [F(p) for p in land_poses()], "squash and recover"))
    A.append(("shoot", 20, "once", [F(p) for p in shoot_poses()], "frame 0 = recoil"))
    A.append(("jump_shoot", 16, "once", [F(p) for p in air_shoot(jump_poses())], "same frames as jump"))
    A.append(("fall_shoot", 12, "loop", [F(p) for p in air_shoot(fall_poses())], "same frames as fall"))
    A.append(("shoot_up", 20, "once", [F(p) for p in shoot_poses(up=True)], "frame 0 = recoil"))
    A.append(("jump_shoot_up", 16, "once", [F(p) for p in air_shoot(jump_poses(), up=True)],
              "same frames as jump"))
    A.append(("hurt", 14, "once", [F(p) for p in hurt_poses()], ""))
    A.append(("die", 12, "once", die_frames(), "falls on his back, helmet sparks"))
    A.append(("teleport", 16, "once", teleport_frames(), "beam out; frames 6-9 only the beam"))
    A.append(("appear", 16, "once", appear_frames(), "beam in"))
    A.append(("victory", 12, "loop", victory_frames(), "hop with the cannon raised"))
    A.append(("push", 10, "loop", [F(p) for p in push_poses()], "hands at x+11 (the wall)"))
    A.append(("look_up", 8, "once", [F(p) for p in lookup_poses()], ""))
    A.append(("skid", 16, "once", [F(p) for p in skid_poses()], ""))
    ANIMS = A
    return A


# ---------------------------------------------------------------------------------------------------------- post effects

def _rgb(spr):
    out = np.zeros((spr.h, spr.w, 3), np.float32)
    m = spr.col >= 0
    out[m] = PAL[spr.col[m]]
    return out


def _tint(spr):
    """Teleport look: every colour mapped by brightness onto the cyan ramp, glowing."""
    m = spr.col >= 0
    c = _rgb(spr)
    lum = 0.30 * c[..., 0] + 0.59 * c[..., 1] + 0.11 * c[..., 2]
    idx = np.clip(np.round(lum / 255.0 * 6.0) + 1, 1, 7).astype(int)
    base = col("cyan:0")
    spr.col[m] = (base + idx[m]).astype(np.int16)
    edge = m & (spr.col == base + 1)
    spr.col[edge] = col("blue:1")
    spr.emit[m] = True
    spr.emit[edge] = False


def _scan(spr, phase):
    for y in range(spr.h):
        if (y + phase) % 2 == 0:
            spr.col[y, :] = -1
            spr.emit[y, :] = False


def _beam(spr, width, y0, y1):
    """A vertical teleport beam over the anchor column from world height y0 to y1."""
    ax, ay = ANCHOR
    rings = ["white", "cyan:6", "cyan:4", "blue:4"]
    for y in range(max(0, ay - y1), ay - y0):
        flick = (y * 7) % 5 == 0
        for d in range(width + 2):
            c = rings[min(d + (1 if flick and d else 0), 3)]
            for x in (ax - 1 - d, ax + d):
                if d <= width or spr.get(x, y) < 0:
                    spr.put(x, y, c, glow=True)
    if width >= 2:  # ground flash
        for d, c in enumerate(("white", "cyan:6", "cyan:6", "cyan:4", "cyan:4", "blue:4", "blue:3")):
            for x in (ax - 1 - d, ax + d):
                spr.put(x, ay - 1, c, glow=True)
                if d < 4:
                    spr.put(x, ay - 2, "cyan:6" if d < 2 else "cyan:4", glow=True)


def _sparkle(spr, x, y, size):
    spr.put(x, y, "white", glow=True)
    for k in range(1, size + 1):
        c = "cyan:6" if k < size else "cyan:4"
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            spr.put(x + dx, y + dy, c, glow=True)


def _spark(spr, x, y, size):
    spr.put(x, y, "white", glow=True)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        spr.put(x + dx, y + dy, "yellow:5", glow=True)
    if size > 1:
        for dx, dy in ((2, -2), (-2, -2), (2, 2), (-2, 2)):
            spr.put(x + dx, y + dy, "orange:4", glow=True)


def _ground(spr):
    bb = spr.bbox()
    if bb is None:
        return spr
    dy = (ANCHOR[1] - 1) - bb[3]
    return spr.shifted(0, dy) if dy else spr


SPARK_PATTERN = [[(0, -2, 2)], [(-4, -1, 1), (3, -3, 2)], [(1, -4, 1)], [(-3, -2, 2)], [(2, -1, 1)],
                 [(-1, -3, 2)], [(3, -2, 1)], []]


def frame(job):
    """Renders one frame: job = (anim name, index)."""
    name, i = job
    spec = {a[0]: a[3] for a in anims()}[name][i]
    pose = spec["pose"]
    if pose is not None:
        ps, W = parts(pose)
        spr = pixelize(render(ps, SIZE, RENDER_ANCHOR, squash=pose["squash"]))
        if spec.get("tint"):
            _tint(spr)
        if "scan" in spec:
            _scan(spr, spec["scan"])
    else:
        spr = empty_sprite(*SIZE)
    if spec.get("ground"):
        spr = _ground(spr)
        if spec.get("lift"):
            spr = spr.shifted(0, -spec["lift"])
    if "beam" in spec:
        _beam(spr, *spec["beam"])
    if "sparkle" in spec:
        pts = [[(24, 30, 2), (40, 22, 1)], [(22, 20, 2), (42, 34, 2), (36, 12, 1)], [(30, 8, 2), (36, 14, 1)],
               [(32, 4, 2)]][spec["sparkle"]]
        for x, y, s in pts:
            _sparkle(spr, x, y, s)
    if "sparks" in spec and pose is not None:
        hx, hy = world_point(pose, "head", HEAD_C)
        cx = int(round(ANCHOR[0] + hx))
        cy = int(round(ANCHOR[1] - hy))
        bb = spr.bbox()
        top = bb[1] if bb else cy - 8
        k = spec["sparks"]
        for dx, dy, s in SPARK_PATTERN[k % len(SPARK_PATTERN)]:
            _spark(spr, cx + dx, top + dy, s)
        if "smoke" in spec:
            sm = spec["smoke"]
            for j in range(2):
                yy = top - 3 - sm * 2 - j * 4
                xx = cx - 1 + ((sm + j) % 2)
                if yy > 1:
                    for dx, dy, c in ((0, 0, "grey:4"), (1, 0, "grey:3"), (0, -1, "grey:5"), (1, -1, "grey:4")):
                        if spr.get(xx + dx, yy + dy) < 0:
                            spr.put(xx + dx, yy + dy, c)
    return spr


def jobs():
    return [(a[0], i) for a in anims() for i in range(len(a[3]))]


def sheets(frames):
    sh = Sheet("hero", SIZE, ANCHOR, cols=16, title="Kip Kepler, cadet of the Beacon Corps (faces right)")
    A = {a[0]: a[3] for a in anims()}
    ms = [muzzle_px(s["pose"]) for s in A["shoot"][1:]]
    mu = [muzzle_px(s["pose"]) for s in A["shoot_up"][1:]]
    mx, my = np.mean(ms, 0)
    ux, uy = np.mean(mu, 0)
    sh.point("muzzle", mx, my, "cannon tip: shoot, run_shoot, jump_shoot, fall_shoot")
    sh.point("muzzle_up", ux, uy, "cannon tip: shoot_up, jump_shoot_up")
    tx, ty = world_point(BASE, "spine", (-7.6, -0.6, 0))
    sh.point("thruster", tx, -ty - (ANCHOR[1] - RENDER_ANCHOR[1]), "backpack nozzles (jet particles), standing pose")
    sh.note("anchor = feet centre on the ground line (the soles' lowest pixel row is anchor y - 1)")
    sh.note("glow: cannon tip (tint it per weapon), antenna light, thruster flames, teleport beam")
    for name, fps, mode, specs, note in anims():
        sh.anim(name, fps, mode, [frames[(name, i)] for i in range(len(specs))], note=note)
    return [sh]
