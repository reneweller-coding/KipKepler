"""THE COLOSSUS -- boss of episode 3 (sheet 192 x 192, anchor = feet centre on the ground line).

A crystal giant of the comet: a hunched, gorilla-like mass of dark violet-tinted rock armoured with pale ice plates,
violet crystal clusters bursting from its shoulders, back and forearms, a cyan core blazing in a cavity of its chest,
two cyan eyes under an ice brow and fists studded with cyan knuckle crystals that light up for the ice beam.

Its one `attack` serves both WorldBoss attacks: fists up (0-0.6 s), SLAM at 0.7 s (frame 7), fists stay on the floor
with the knuckle crystals blazing while the engine draws the low ice beam (1.0-1.6 s), rise (to 2.0 s).

Model space: x forward (it faces right), y up, z towards its right side (the near side). Lengths in target pixels.
"""
import math

import numpy as np

from bake import (Box, Capsule, Chamfer, Ellipsoid, Paint, Part, Rig, RoundCone, Sheet, SmoothUnion, Sphere,
                  Union, bipyramid, ik2, keys, material, pixelize, prism, render, rot, trans)

from .bosskit import F, Slab, Stripes, Veins, arena, flash, fx_canvas, over, puffs, ring, sparks, streaks, under

YAW = -36.0
SIZE = (192, 192)
ANCHOR = (96, 182)
RENDER_ANCHOR = (96, 181)
LIFT = ANCHOR[1] - RENDER_ANCHOR[1]

# ---------------------------------------------------------------------------------------------------------- materials
material("cl_rock", ["violet:0", "slate:1", "slate:2", "slate:3"], bands=[-0.45, 0.0, 0.5])
material("cl_rock2", ["violet:0", "violet:1", "slate:1", "slate:2"], bands=[-0.4, 0.0, 0.5])
material("cl_ice", ["blue:2", "blue:3", "ice:3", "ice:5", "ice:6", "white"], style="glass",
         bands=[-0.45, -0.05, 0.3, 0.65], spec=0.92, line="blue:1", line_lit="blue:1")
material("cl_cryst", ["violet:1", "violet:2", "violet:3", "violet:4", "violet:6", "white"], style="metal",
         bands=[-0.35, 0.05, 0.4, 0.72], spec=0.9, line="violet:0")
material("cl_knuck", ["blue:2", "cyan:3", "ice:4", "ice:5", "white"], style="glass", bands=[-0.3, 0.2, 0.6],
         spec=0.93, line="blue:1", prio=1.5)
material("cl_glow", ["cyan:3", "cyan:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.15, 0.4, 0.7, 0.92],
         prio=2.5, line="blue:1")
material("cl_crack", ["cyan:3", "cyan:4"], style="emit", bands=[0.5], prio=2.2, inner=False)
material("cl_crack_hi", ["cyan:4", "cyan:5"], style="emit", bands=[0.5], prio=2.2, inner=False)
material("cl_core", ["cyan:4", "cyan:5", "cyan:6", "ice:7", "white"], style="emit", bands=[0.2, 0.45, 0.7, 0.9],
         prio=3.0, line="blue:1")
material("cl_core_hi", ["cyan:5", "cyan:6", "ice:7", "white"], style="emit", bands=[0.25, 0.5, 0.75], prio=3.0,
         line="blue:1")
material("cl_eye", ["cyan:5", "cyan:6", "white"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("cl_hole", ["violet:0", "outline"], bands=[0.3], inner=False)

# ---------------------------------------------------------------------------------------------------------- skeleton
ANKLE_H = 7.0
L_SH, L_TH, HIP_DROP = 16.0, 16.0, 3.0
L_UP, L_FO = 18.0, 20.0
PELVIS_Y = ANKLE_H + L_SH + L_TH + HIP_DROP

RIG = Rig()
RIG.joint("pelvis", None, (0, PELVIS_Y, 0))
RIG.joint("spine", "pelvis", (0, 4.0, 0))
RIG.joint("chest", "spine", (2.0, 14.0, 0))
RIG.joint("head", "chest", (14.0, 19.0, 0))
for _s, _z in (("r", 1), ("l", -1)):
    RIG.joint(f"sh_{_s}", "chest", (0.0, 15.0, 24.0 * _z))
    RIG.joint(f"el_{_s}", f"sh_{_s}", (0, -L_UP, 0))
    RIG.joint(f"wr_{_s}", f"el_{_s}", (0, -L_FO, 0))
    RIG.joint(f"hip_{_s}", "pelvis", (0, -HIP_DROP, 11.5 * _z))
    RIG.joint(f"kn_{_s}", f"hip_{_s}", (0, -L_TH, 0))
    RIG.joint(f"an_{_s}", f"kn_{_s}", (0, -L_SH, 0))


def _cluster(spec, mat="cl_cryst"):
    """Crystal prisms [(x, y, z, r, len, rx, rz), ...] pointing along their local +y, tilted by rx/rz."""
    out = []
    for x, y, z, r, ln, rx, rz in spec:
        out.append(prism(6, r, ln * 0.35, ln * 0.45, 0.5, twist=17 * (x + z)).m(mat).at(0, ln * 0.3, 0)
                   .rot(rx, 0, rz).at(x, y, z))
    return Union(*out)


def _cracked(shape, seed, hi=False, freq=0.075, width=0.024):
    return Paint(shape, Veins(freq, width, seed), "cl_crack_hi" if hi else "cl_crack")


# ---------------------------------------------------------------------------------------------------------- shapes
def _belly(hi=False):
    return _cracked(Union(Ellipsoid(16.0, 13.0, 17.0).m("cl_rock").at(2.0, 6.0, 0),
                          Box(12.0, 5.0, 14.0, r=3.0).m("cl_rock2").at(2.0, -2.0, 0)), 3, hi)


def _chest(core_hi=False):
    mass = SmoothUnion(Ellipsoid(19.0, 17.0, 23.0).m("cl_rock").at(2.0, 8.0, 0),
                       Ellipsoid(17.0, 15.0, 21.0).m("cl_rock").at(-8.0, 16.0, 0), k=4.0)
    mass = _cracked(mass, 7, core_hi)
    rim = Union(*[_cluster([(18.5, 7.0 + dy, 8.5 * s, 2.0, 7.0, -70 * s, -60 + 25 * dy / 7.0)], mat="cl_ice")
                  for s in (1, -1) for dy in (-7.0, 7.0)])
    cavity = Ellipsoid(6.5, 10.0, 8.0).m("cl_hole").at(18.0, 7.0, 0)
    core = Union(bipyramid(6, 6.4, 8.0, 8.0, twist=10).m("cl_core_hi" if core_hi else "cl_core").at(21.5, 7.0, 0),
                 bipyramid(5, 2.6, 4.5, 3.0, twist=30).m("cl_core").rot(0, 0, -50).at(22.0, 1.5, 4.0),
                 bipyramid(5, 2.2, 4.0, 3.0, twist=50).m("cl_core").rot(0, 0, 40).at(21.0, 13.0, -3.0))
    back = _cluster([(-15, 25, 0, 5.4, 26, 0, 30), (-8, 28, 9, 4.4, 21, -22, 16), (-8, 28, -9, 4.4, 20, 22, 18),
                     (-22, 18, 7, 3.6, 16, -30, 52), (-22, 18, -7, 3.6, 16, 30, 55), (-2, 29, 4, 3.0, 13, -10, 6),
                     (-25, 9, 0, 3.0, 12, 0, 80)])
    return Union(mass, rim, cavity, core, back)


def _head(eyes=1.0):
    skull = _cracked(Chamfer(8.0, 7.0, 8.5, c=3.0).m("cl_rock").at(1.0, 0, 0), 11)
    jaw = Chamfer(6.0, 3.0, 6.5, c=1.8).m("cl_rock2").at(4.0, -5.5, 0)
    brow = Chamfer(4.0, 2.4, 9.5, c=1.4).m("cl_ice").rot(0, 0, -14).at(7.0, 4.0, 0)
    eye_m = "cl_eye" if eyes > 0 else "cl_rock2"
    eyes_ = Union(*[Ellipsoid(2.2, 1.6, 1.8).m(eye_m).at(8.6, 0.8, 3.8 * s) for s in (1, -1)])
    horns = _cluster([(-1, 6, 3, 2.4, 13, -16, 26), (-3, 5, -3, 2.0, 10, 20, 34), (2, 6, 0, 1.8, 8, 0, 4)],
                     mat="cl_ice")
    return Union(skull, jaw, brow, eyes_, horns)


def _shoulder(side):
    z = 1 if side == "r" else -1
    ball = _cracked(Sphere(11.0).m("cl_rock"), 13 + (z > 0))
    ice = _cluster([(0, 8, 4 * z, 4.8, 17, -16 * z, -4), (-5, 9, 8 * z, 3.6, 13, -46 * z, 26)], mat="cl_ice")
    vio = _cluster([(-7, 6, 9 * z, 2.6, 12, -60 * z, 50)])
    return Union(ball, ice, vio)


def _upper():
    return _cracked(Capsule((0, 0, 0), (0, -L_UP + 2.0, 0), 8.6).m("cl_rock"), 17)


def _fore(side, glow=False):
    z = 1 if side == "r" else -1
    arm = _cracked(RoundCone((0, 0, 0), (0, -L_FO + 4.0, 0), 9.0, 11.5).m("cl_rock"), 19 + (z > 0))
    elbow = Sphere(8.6).m("cl_rock2")
    bracer = _cluster([(7, -7, 3 * z, 3.4, 12, 0, -62), (8, -13, -2 * z, 3.0, 10, 0, -70)], mat="cl_ice")
    spikes = _cluster([(-7, -5, 4 * z, 3.0, 14, -40 * z, 62), (-8, -12, 3 * z, 2.6, 12, -30 * z, 76)])
    fist = _cracked(Chamfer(11.0, 10.0, 10.5, c=3.8).m("cl_rock").at(1.0, -L_FO - 3.5, 0), 23)
    km = "cl_glow" if glow else "cl_knuck"
    knuckles = Union(*[bipyramid(5, 2.8, 4.4, 1.0, twist=20 * k).m(km).rot(0, 0, -70).at(11.2, -L_FO - 3.5 + dy, dz)
                       for k, (dy, dz) in enumerate(((4.5, 4.5), (4.5, -4.5), (-3.0, 5.0), (-3.0, -4.5)))])
    return Union(arm, elbow, bracer, spikes, fist, knuckles)


def _thigh():
    return _cracked(Capsule((0, 0, 0), (0, -L_TH + 2.0, 0), 10.0).m("cl_rock"), 29)


def _shin():
    shin = _cracked(RoundCone((0, 0, 0), (0, -L_SH + 3.0, 0), 9.5, 11.0).m("cl_rock"), 31)
    knee = _cluster([(6, 2, 0, 3.0, 9, 0, -50), (5, 3, 4, 2.2, 7, -40, -40)], mat="cl_ice")
    return Union(shin, knee)


def _foot():
    block = Chamfer(14.0, 4.2, 10.5, c=2.6).m("cl_rock").at(3.0, -ANKLE_H + 4.2, 0)
    ankle = Sphere(8.0).m("cl_rock2")
    toes = _cluster([(15, -ANKLE_H + 3.5, 6, 2.2, 8, 0, -72), (16, -ANKLE_H + 3.0, -1, 2.2, 8, 0, -76),
                     (14, -ANKLE_H + 3.5, -7, 2.0, 7, 0, -72)], mat="cl_ice")
    return Union(block, ankle, toes)


_S = None


def shapes():
    global _S
    if _S is None:
        _S = dict(sh_r=_shoulder("r"), sh_l=_shoulder("l"), upper=_upper(), thigh=_thigh(),
                  shin=_shin(), foot=_foot())
    return _S


# ---------------------------------------------------------------------------------------------------------- posing
BASE = dict(root=(0.0, 0.0), yaw=YAW, leg_ry=0.0, pelvis_x=0.0, pelvis_y=PELVIS_Y - 3.0,
            pelvis=(0, 0, 0), spine=(0, 0, -8), chest=(0, 0, -14), head=(0, 0, 10),
            sh_r=(-10, 0, 8), el_r=(0, 0, 14), wr_r=(0, 0, 0), sh_l=(8, 0, 16), el_l=(0, 0, 14), wr_l=(0, 0, 0),
            foot_r=(-6.0, 0.0, 0.0), foot_l=(8.0, 0.0, 0.0), squash=(1.0, 1.0), core=False, glow=False, eyes=1.0)


def P(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


SOLE = ((-11.0, -ANKLE_H), (17.0, -ANKLE_H))


def _leg_ik(pose, P0, side):
    fx, fy, pitch = pose[f"foot_{side}"]
    sp, cp = math.sin(math.radians(pitch)), math.cos(math.radians(pitch))
    low = min(x * sp + y * cp for x, y in SOLE)
    fy = max(fy, -low - ANKLE_H)
    hip = P0[f"hip_{side}"][:3, 3]
    a1, a2 = ik2((hip[0], hip[1]), (fx, fy + ANKLE_H), L_TH, L_SH, bend=1.0)
    parent = pose["pelvis"][2]
    pose[f"hip_{side}"] = (0, 0, a1 - parent)
    pose[f"kn_{side}"] = (0, 0, a2)
    pose[f"an_{side}"] = (0, 0, pitch - (a1 + a2))


def solve(pose):
    pose = dict(pose)
    RIG.joints["pelvis"] = (None, np.array([pose["pelvis_x"], pose["pelvis_y"], 0.0]))
    P0 = RIG.solve(pose)
    for side in ("r", "l"):
        if pose.get(f"foot_{side}") is not None and f"hip_{side}" not in pose:
            _leg_ik(pose, P0, side)
    base = trans(pose["root"][0], pose["root"][1], 0) @ rot(0, pose["yaw"], 0)
    return RIG.solve(pose, base), pose


def parts(pose):
    S = shapes()
    W, pose = solve(pose)
    out = []

    def add(shape, joint, shade=0, name="", zbias=0.0):
        if shape is not None:
            out.append(Part(shape.xform(W[joint]), name=name, shade=shade, zbias=zbias))

    add(_belly(pose["core"]), "spine", name="belly")
    add(_chest(pose["core"]), "chest", name="chest")
    add(_head(pose["eyes"]), "head", name="head")
    for side, sh in (("r", 0), ("l", -1)):
        add(S["thigh"], f"hip_{side}", shade=sh, name=f"thigh_{side}")
        add(S["shin"], f"kn_{side}", shade=sh, name=f"shin_{side}")
        add(S["foot"], f"an_{side}", shade=sh, name=f"foot_{side}")
        add(S[f"sh_{side}"], f"sh_{side}", shade=sh, name=f"sh_{side}")
        add(S["upper"], f"sh_{side}", shade=sh, name=f"upper_{side}")
        add(_fore(side, pose["glow"]), f"el_{side}", shade=sh, name=f"fore_{side}")
    return out, W


def world_point(pose, joint, local):
    W, _ = solve(pose)
    q = W[joint] @ np.array([*local, 1.0])
    return q[0], q[1]


def to_px(pose, x, y):
    sx, sy = pose["squash"]
    return x * sx, -(y * sy) - LIFT


def knuckles(pose, side="r"):
    return world_point(pose, f"el_{side}", (13.0, -L_FO - 1.0, 0))


def arm_to(pose, side, target, bend=-1.0):
    """Puts the fist centre at a model-space target (x forward, y up; before the yaw) with 2-bone IK in the arm's
    swing plane. The near arm (r) sits at z +24, so its screen x is about 0.81 x - 14 (yaw -36)."""
    p = dict(pose)
    RIG.joints["pelvis"] = (None, np.array([p["pelvis_x"], p["pelvis_y"], 0.0]))
    P0 = RIG.solve({k: v for k, v in p.items() if k in RIG.joints})
    sh = P0[f"sh_{side}"][:3, 3]
    a1, a2 = ik2((sh[0], sh[1]), target, L_UP, L_FO + 3.5, bend=bend)
    parent = sum(p[j][2] for j in ("pelvis", "spine", "chest"))
    p[f"sh_{side}"] = (p[f"sh_{side}"][0], 0, a1 - parent)
    p[f"el_{side}"] = (0, 0, a2)
    return p


# ---------------------------------------------------------------------------------------------------------- animations
PY = BASE["pelvis_y"]
TAU = 2 * math.pi


def idle(i):
    b = 0.5 - 0.5 * math.cos(TAU * i / 8)
    return P(pelvis_y=PY - 1.0 * b, spine=(0, 0, -8 + 1.5 * b), chest=(0, 0, -14 + 2.5 * b), head=(0, 4 - 6 * b, 10 - 3 * b),
             sh_r=(-10, 0, 8 - 3 * b), el_r=(0, 0, 14 + 4 * b), sh_l=(8, 0, 16 - 3 * b), el_l=(0, 0, 14 + 4 * b),
             core=i in (3, 4, 5), eyes=0 if i == 6 else 1)


WALK = [(17.0, 0.0, 6), (10.2, 0.0, 0), (3.4, 0.0, 0), (-3.4, 0.0, 0), (-10.2, 0.0, 0), (-17.0, 0.0, -10),
        (-10.0, 7.0, -14), (1.0, 10.0, -4), (11.0, 7.0, 6), (16.0, 2.5, 8)]


def move(i):
    """10 frames: planted feet move 6.8 px per frame (68 px/cycle, 54 px/s at 8 fps)."""
    phi = i / 10.0
    c = math.cos(TAU * phi)
    bob = math.cos(2 * TAU * phi)
    return P(pelvis_x=1.5, pelvis_y=PY - 2.0 - 2.0 * bob, pelvis=(6 * c, 0, 0), spine=(-3 * c, -6 * c, -9),
             chest=(-3 * c, -4 * c, -16), head=(0, 5 * c, 12 + 2 * bob), sh_r=(-10, 0, 8 - 22 * c),
             el_r=(0, 0, 18 - 6 * c), sh_l=(8, 0, 16 + 20 * c), el_l=(0, 0, 18 + 6 * c),
             foot_r=WALK[i], foot_l=WALK[(i + 5) % 10], core=i in (0, 5))


def attack_frames():
    """20 frames at 10 fps (2.0 s): raise (0-5), smash (6), SLAM at 7 (0.7 s), crouched on the fists, knuckle
    crystals blaze for the beam (10-15 = 1.0-1.6 s), rise (16-19)."""
    out = []
    keys_ = [
        # t, rise, spine, chest, head, fist height above the shoulder (raise) or floor target, glow, fx
        (0, dict(py=0.0, sp=-8, ch=-14, hd=10, up=0.0)),
        (3, dict(py=3.0, sp=4, ch=8, hd=-6, up=1.0)),
        (5, dict(py=3.5, sp=6, ch=12, hd=-10, up=1.0)),
    ]
    for k in range(20):
        fx = None
        glow = False
        core = False
        sq = (1.0, 1.0)
        if k <= 5:
            v = keys([(t, d) for t, d in keys_], k)
            p = P(pelvis_y=PY + v["py"], spine=(0, 0, v["sp"]), chest=(0, 0, v["ch"]), head=(0, 0, v["hd"]),
                  foot_r=(-9.0, 0, 0), foot_l=(11.0, 0, 0), core=k >= 3)
            u = v["up"]
            p["sh_r"] = (-30 * u - 10 * (1 - u), 0, 8 + 160 * u)
            p["el_r"] = (0, 0, 14 - 4 * u)
            p["sh_l"] = (30 * u + 8 * (1 - u), 0, 16 + 152 * u)
            p["el_l"] = (0, 0, 14 - 4 * u)
            glow = k >= 3
            if k >= 3:
                fx = "gather"
        elif k == 6:
            p = P(pelvis_y=PY - 3.0, spine=(0, 0, -16), chest=(0, 0, -20), head=(0, 0, 14), foot_r=(-9.0, 0, 0),
                  foot_l=(11.0, 0, 0), sh_r=(-12, 0, 92), el_r=(0, 0, 10), sh_l=(12, 0, 88), el_l=(0, 0, 10),
                  core=True)
            glow = True
            fx = "smear"
        else:
            # crouched on the fists: from impact (7) through the beam (10-15) to standing (19)
            u = keys([(7, 1.0), (15, 0.92), (19, 0.0)], k)
            p = P(pelvis_y=PY - 9.0 * u, spine=(0, 0, -8 - 20 * u), chest=(0, 0, -14 - 14 * u),
                  head=(0, 0, 10 + 8 * u), foot_r=(-9.0 + 3 * (1 - u), 0, 0), foot_l=(11.0 - 3 * (1 - u), 0, 0),
                  core=True)
            if k <= 16:
                p = arm_to(p, "r", (46.0, 11.0 + 3 * (k == 16)), bend=-1.0)
                p = arm_to(p, "l", (30.0, 12.0 + 3 * (k == 16)), bend=-1.0)
            else:
                w = (k - 16) / 3.0
                p.update(sh_r=(-8, 0, 60 - 44 * w), el_r=(0, 0, 10 + 16 * w), sh_l=(8, 0, 64 - 40 * w),
                         el_l=(0, 0, 10 + 12 * w))
            if k == 7:
                sq = (1.06, 0.93)
            glow = 9 <= k <= 15
            fx = {7: "slam0", 8: "slam1", 9: "slam2", 10: "beam0", 11: "beam1", 12: "beam0", 13: "beam1",
                  14: "beam0", 15: "beam1"}.get(k)
        p.update(glow=glow or p.get("glow", False), squash=sq)
        if core:
            p["core"] = True
        out.append((p, fx, k))
    return out


def charge(i):
    """6 frames: shoulder-first charge, head down, arms swept back, long strides."""
    RUN = [(18.0, 0.0, 6), (6.0, 0.0, 0), (-8.0, 0.0, -6), (-18.0, 4.0, -24), (-4.0, 12.0, -10), (12.0, 8.0, 4)]
    phi = i / 6.0
    c = math.cos(TAU * phi)
    return P(pelvis_x=4.0, pelvis_y=PY - 3.0 - 1.5 * math.cos(2 * TAU * phi), spine=(0, -4 * c, -20),
             chest=(0, -3 * c, -22), head=(0, 0, 18), sh_r=(-10, 0, -30 - 20 * c), el_r=(0, 0, 30),
             sh_l=(10, 0, -24 + 20 * c), el_l=(0, 0, 30), foot_r=RUN[i], foot_l=RUN[(i + 3) % 6], core=True)


def anims():
    return [
        ("idle", 6, "loop", [(idle(i), None, i) for i in range(8)], "breathing, the core pulses, eyes blink"),
        ("move", 8, "loop", [(move(i), "step" if i in (0, 5) else None, i) for i in range(10)],
         "slow heavy steps, contacts at 0 and 5, 54 px/s at 8 fps"),
        ("attack", 10, "once", attack_frames(),
         "fists up 0-0.6 s, SLAM at frame 7 (0.7 s), knuckles blaze for the beam 1.0-1.6 s, rise to 2.0 s"),
        ("charge", 10, "loop", [(charge(i), "step" if i in (0, 3) else None, i) for i in range(6)],
         "shoulder charge (WorldBoss state 3 after its 0.5 s wind-up; the engine uses move today)"),
    ]


# ---------------------------------------------------------------------------------------------------------- effects
ICE = ("blue:3", "ice:4", "ice:6", "white")


def _effects(fx, pose, k):
    c = fx_canvas(SIZE, RENDER_ANCHOR)
    back = fx_canvas(SIZE, RENDER_ANCHOR)
    if fx is None:
        return c, back
    if fx == "gather":
        xa, ya = world_point(pose, "el_r", (2.0, -L_FO - 3.0, 0))
        xb, yb = world_point(pose, "el_l", (2.0, -L_FO - 3.0, 0))
        flash(c, (xa + xb) / 2, max(ya, yb) + 8, 7.0 + 3.0 * (k - 3), rays=4, ang=45 * (k % 2),
              cols=("cyan:4", "cyan:6", "white"))
        for s in ("r", "l"):
            x, y = world_point(pose, f"el_{s}", (2.0, -L_FO - 3.0, 0))
            cv = c if s == "r" else back
            sparks(cv, [(x - 9, y + 5, 0.9), (x + 8, y - 6, 0.9), (x + 2, y + 10, 0.8)], cols=("cyan:6", "white"))
    elif fx == "smear":
        for s in ("r", "l"):
            x, y = world_point(pose, f"el_{s}", (2.0, -L_FO - 3.0, 0))
            streaks(back, [(x - 4, y + 14, x - 2, y + 30), (x + 4, y + 12, x + 6, y + 28)],
                    cols=("ice:6", "white"), w=0.8)
    elif fx.startswith("slam"):
        d = int(fx[-1])
        x0 = 33.0
        if d == 0:
            flash(c, x0, 3.0, 14.0, rays=4, ang=0, cols=("cyan:5", "ice:6", "white"))
        # ice shards bursting up and out of the floor in front
        rng = np.random.default_rng(5)
        for j in range(7):
            sx = x0 + rng.uniform(-30, 30)
            h = rng.uniform(6, 14) * (1.0 - 0.3 * d)
            lean = (sx - x0) * 0.25
            if d < 2 or j % 2 == 0:
                F(c, c.polygon([(sx - 2.4, 0.0), (sx + lean, h), (sx + 2.4, 0.0)]), "ice:5", glow=False)
                F(c, c.polygon([(sx - 0.8, 0.0), (sx + lean * 0.9, h * 0.9), (sx + 1.0, 0.0)]), "white", glow=False)
        puffs(c, [(x0 - 22 - 8 * d, 4 + 2 * d, 6 + 1.5 * d), (x0 + 24 + 8 * d, 4 + 2 * d, 6 + 1.5 * d),
                  (x0, 6 + 2 * d, 5 + d)], shades=("blue:3", "ice:3", "ice:5", "ice:6"), seed=31 + d,
              holes=0.2 * d)
        if d <= 1:
            ring(c, x0, 1.5, 34 + 18 * d, 5 + d, 0.8, "white" if d == 0 else "ice:6", arc=(180, 360))
            ring(back, x0, 1.5, 34 + 18 * d, 5 + d, 0.8, "white" if d == 0 else "ice:6", arc=(0, 180))
        sparks(c, [(x0 - 12 - 6 * d, 18 + 6 * d), (x0 + 14 + 6 * d, 20 + 5 * d), (x0 + 4, 24 + 7 * d)],
               cols=("ice:6", "white"))
    elif fx.startswith("beam"):
        d = int(fx[-1])
        x, y = knuckles(pose, "r")
        flash(c, x + 1.5, y, 7.0 + 2 * d, rays=4, ang=45 * d, cols=("cyan:4", "cyan:6", "white"))
        sparks(c, [(x - 4, y + 7 + 2 * d, 0.8), (x + 6, y - 6 - d, 0.8)], cols=("cyan:6", "white"))
        puffs(back, [(x - 10, 3.0, 4.0 + d), (x + 8, 3.0, 3.5)], shades=("blue:3", "ice:3", "ice:5", "ice:6"),
              seed=41 + d)
    elif fx == "step":
        fx_x = pose["foot_r"][0] if k == 0 else pose["foot_l"][0]
        puffs(back, [(fx_x + 14, 2.5, 3.6), (fx_x - 10, 2.5, 3.0)], shades=("blue:3", "ice:3", "ice:5", "ice:6"),
              seed=3 + k)
    return c, back


def frame(job):
    name, i = job
    pose, fx, k = {a[0]: a[3] for a in anims()}[name][i]
    ps, W = parts(pose)
    R = render(ps, SIZE, RENDER_ANCHOR, squash=pose["squash"])
    c, back = _effects(fx, pose, k)
    under(R, back)
    over(R, c)
    return pixelize(R)


def jobs():
    return [(a[0], i) for a in anims() for i in range(len(a[3]))]


def sheets(frames):
    sh = Sheet("colossus", SIZE, ANCHOR, cols=12, title="THE COLOSSUS, the crystal giant of the comet (faces right)")
    A = {a[0]: a[3] for a in anims()}
    beam = A["attack"][12][0]
    mx, my = to_px(beam, *knuckles(beam, "r"))
    sh.point("muzzle", mx, my, "knuckle crystals during the beam (attack 10-15); WorldBoss starts the beam at +30 -20")
    cx, cy = to_px(BASE, *world_point(BASE, "chest", (24.0, 7.0, 0)))
    sh.point("core", cx, cy, "the chest core (weak-spot light, idle pose)")
    sh.point("slam", 33, -LIFT, "where the fists hit the floor (attack 7)")
    sh.note("anchor = feet centre on the ground line (box 76 x 108); the soles' lowest row is anchor y - 1")
    sh.note("attack is one-shot, timed to WorldBoss states 1 (slam, 1.5 s) and 2 (beam, 2.0 s): play it from frame 0")
    sh.note("glow: core, eyes, knuckle crystals while charged, impact flash, ice sparks")
    for name, fps, mode, specs, note in anims():
        sh.anim(name, fps, mode, [frames[(name, i)] for i in range(len(specs))], note=note)
    idx = {a[0]: a[3] for a in sh.anims}
    arena(sh, [idx["idle"][0], idx["move"][2], idx["attack"][4], idx["attack"][7], idx["attack"][12],
               idx["charge"][1]])
    return [sh]
