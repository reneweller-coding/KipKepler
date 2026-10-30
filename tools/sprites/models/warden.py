"""THE WARDEN -- boss of episode 1 (sheet 128 x 128, anchor = feet centre on the ground line).

The Academy ring's security mech gone rogue: white armour, hazard-striped pod covers, shin plates and trims, a red
eye scanning in a dark visor slot, a siren dome on its head (it calls drones), a missile pod on each shoulder (the
covers flip open, the pods tilt up and fire a fan of missiles) and jump jets in its back unit (it leaps and stomps).

Model space: x forward (it faces right), y up, z towards its right side (the near side). Lengths in target pixels.
"""
import math

import numpy as np

from bake import (Box, Capsule, Chamfer, Cone, Cylinder, Ellipsoid, Paint, Part, Rig, RoundCone, Sheet, Sphere,
                  Subtract, Torus, Union, ik2, keys, material, pixelize, render, rot, trans)

from .bosskit import F, Slab, Stripes, arena, flash, fx_canvas, over, puffs, ring, sparks, streaks, under

YAW = -38.0
SIZE = (128, 128)
ANCHOR = (64, 118)
RENDER_ANCHOR = (64, 117)      # world y = 0 one row up: the outline under the soles is the row above the anchor
LIFT = ANCHOR[1] - RENDER_ANCHOR[1]

# ---------------------------------------------------------------------------------------------------------- materials
material("wd_white", ["slate:3", "slate:4", "steel:5", "steel:6", "steel:7", "white"], style="metal",
         bands=[-0.55, -0.12, 0.33, 0.6], spec=0.94, line_lit="slate:2")
material("wd_yellow", ["orange:2", "orange:3", "yellow:4", "yellow:5", "yellow:6"], bands=[-0.5, -0.1, 0.4, 0.74],
         line_lit="orange:1")
material("wd_dark", ["slate:1", "slate:2", "slate:3", "steel:3"], bands=[-0.4, 0.1, 0.6])
material("wd_gun", ["slate:1", "slate:2", "steel:2", "steel:3", "steel:5"], style="metal", bands=[-0.3, 0.15, 0.55],
         spec=0.93)
material("wd_steel", ["steel:1", "steel:2", "steel:3", "steel:4", "steel:5", "steel:7"], style="metal",
         bands=[-0.45, 0.0, 0.35, 0.65], spec=0.92)
material("wd_slot", ["crimson:1", "red:2", "red:3"], style="emit", bands=[0.3, 0.7], prio=2.0, inner=False)
material("wd_eye", ["red:3", "red:5", "red:6", "white"], style="emit", bands=[0.25, 0.55, 0.85], prio=3.0)
material("wd_lamp", ["orange:4", "yellow:5", "yellow:7"], style="emit", bands=[0.4, 0.8], prio=2.5)
material("wd_siren", ["red:4", "red:5", "orange:6", "white"], style="emit", bands=[0.3, 0.6, 0.85], prio=2.5)
material("wd_siren_off", ["crimson:1", "crimson:2", "red:2", "red:3"], bands=[-0.3, 0.2, 0.6])
material("wd_red", ["crimson:1", "red:2", "red:3", "red:4"], bands=[-0.3, 0.2, 0.6])
material("wd_hole", ["slate:0"], style="flat", inner=False)
material("wd_hot", ["orange:4", "yellow:5", "yellow:6", "white"], style="emit", bands=[0.3, 0.6, 0.85], prio=3.0)
material("wd_flame", ["orange:3", "orange:4", "yellow:5", "yellow:6", "white"], style="emit",
         bands=[0.2, 0.45, 0.7, 0.88], line="orange:2", line_lit="orange:2", inner=False)

# ---------------------------------------------------------------------------------------------------------- skeleton
ANKLE_H = 5.0
L_SH, L_TH, HIP_DROP = 16.0, 14.0, 2.0
L_UP, L_FO = 11.0, 13.0
PELVIS_Y = ANKLE_H + L_SH + L_TH + HIP_DROP          # legs straight

RIG = Rig()
RIG.joint("pelvis", None, (0, PELVIS_Y, 0))
RIG.joint("spine", "pelvis", (0, 3.0, 0))
RIG.joint("head", "spine", (13.0, 29.0, 0))
for _s, _z in (("r", 1), ("l", -1)):
    RIG.joint(f"pa_{_s}", "spine", (-1.0, 25.5, 19.5 * _z))       # pauldron (fixed to the torso)
    RIG.joint(f"pod_{_s}", f"pa_{_s}", (-11.0, 7.0, -1.0 * _z))    # pod hinge on top of the pauldron (rear edge)
    RIG.joint(f"sh_{_s}", f"pa_{_s}", (0.5, -1.0, 3.0 * _z))
    RIG.joint(f"el_{_s}", f"sh_{_s}", (0, -L_UP, 0))
    RIG.joint(f"hip_{_s}", "pelvis", (0, -HIP_DROP, 9.5 * _z))
    RIG.joint(f"kn_{_s}", f"hip_{_s}", (0, -L_TH, 0))
    RIG.joint(f"an_{_s}", f"kn_{_s}", (0, -L_SH, 0))

POD_LEN = 12.0
SIREN = (-3.4, 8.6, 0.0)


def _hazard(shape, n=(0, 1, 1), period=3.2, duty=0.5, offset=0.0):
    return Paint(shape, Stripes(n, period, duty, offset), "wd_dark")


# ---------------------------------------------------------------------------------------------------------- shapes
def _torso():
    hull = Chamfer(14.5, 11.0, 13.0, c=5.0).m("wd_white").at(1.0, 20.0, 0)
    yoke = Chamfer(10.0, 3.2, 16.0, c=2.6).m("wd_white").at(-2.0, 28.0, 0)
    belt = Box(13.4, 1.5, 12.0, r=1.0).m("wd_yellow").at(1.5, 9.4, 0)
    belly = Box(10.0, 3.6, 10.5, r=2.0).m("wd_dark").at(1.5, 5.6, 0)
    waist = Cylinder(8.0, 4.0, rr=1.8).m("wd_dark").at(0, 2.5, 0)
    neck = Cylinder(5.0, 3.0, rr=1.2).m("wd_dark").at(10.0, 28.5, 0)
    back = Box(6.0, 10.0, 10.0, r=2.4).m("wd_gun").at(-16.0, 19.0, 0)
    vents = Paint(Box(1.0, 5.0, 6.0, r=0.5).m("wd_dark").at(-21.8, 19.0, 0), Stripes((0, 1, 0), 2.0, 0.5),
                  "wd_gun")
    for z in (5.0, -5.0):
        back = Union(back, Cylinder(2.0, 3.6, rr=0.6).m("wd_gun").at(-18.5, 30.0, z),
                     Cylinder(1.3, 0.6).m("wd_hole").at(-18.5, 33.5, z))
    nozzles = Union(*[Cone(3.0, 2.0, 1.8).m("wd_dark").at(-18.0, 7.6, z) for z in (5.0, -5.0)])
    return Union(hull, yoke, belt, belly, waist, neck, back, vents, nozzles)


def _plate():
    """The chest plate (its own part, so an inner line frames it) with the status lamp."""
    plate = Chamfer(3.4, 7.6, 9.6, c=2.2).m("wd_white").at(14.6, 18.6, 0)
    lamp = Cylinder(2.1, 0.9, rr=0.5).m("wd_lamp").rot(0, 0, 90).at(17.9, 21.0, 0)
    grille = Paint(Box(0.8, 2.6, 5.0, r=0.4).m("wd_dark").at(17.6, 14.4, 0), Stripes((0, 1, 0), 1.8, 0.5),
                   "wd_gun")
    return Union(plate, lamp, grille)


def _pelvis():
    block = Box(9.0, 4.5, 10.5, r=2.2).m("wd_gun").at(0, -1.5, 0)
    cod = Box(3.2, 4.2, 5.2, r=1.5).m("wd_yellow").at(8.2, -2.5, 0)
    return Union(block, cod)


def _head(eye_z=0.0, siren=0):
    shell = Box(8.8, 7.2, 9.0, r=3.6).m("wd_white")
    slot = Box(4.6, 2.8, 10.2, r=1.2).m("wd_slot").at(8.4, 0.2, 0)
    shell = Subtract(shell, slot)
    brow = Box(4.2, 1.5, 9.6, r=1.0).m("wd_yellow").rot(0, 0, -10).at(5.0, 4.4, 0)
    jaw = Paint(Box(4.6, 2.6, 7.0, r=1.3).m("wd_dark").at(5.4, -5.2, 0), Stripes((0, 0, 1), 2.0, 0.5),
                "wd_gun")
    eye = Sphere(2.6).m("wd_eye").at(5.8, 0.2, eye_z)
    ears = Union(*[Cylinder(2.8, 1.0, rr=0.5).m("wd_dark").rot(90, 0, 0).at(-2.6, -0.8, 9.0 * s) for s in (1, -1)])
    base = Cylinder(2.4, 0.9, rr=0.4).m("wd_dark").at(SIREN[0], SIREN[1] - 1.4, 0)
    dome = Sphere(2.6).m("wd_siren" if siren else "wd_siren_off").at(*SIREN)
    ant = Capsule((-6.0, 5.0, 6.5), (-9.5, 13.5, 6.5), 0.55).m("wd_dark")
    return Union(shell, brow, jaw, eye, ears, base, dome, ant)


def _pauldron(side):
    z = 1 if side == "r" else -1
    shell = Ellipsoid(10.0, 8.0, 8.0).m("wd_white").at(0, 1.2, 1.4 * z)
    rim = Ellipsoid(10.4, 2.0, 8.4).m("wd_yellow").at(0, -3.6, 1.4 * z)
    return Union(shell, rim)


def _pod(cover=0.0, hot=False):
    """Missile pod, hinged at its rear bottom edge, tubes facing +x. cover 0 = closed, 1 = flipped open."""
    L = POD_LEN
    box = Box(L / 2, 5.0, 6.0, r=1.6).m("wd_gun").at(L / 2, 5.0, 0)
    tubes = []
    tips = []
    for dy in (2.4, -2.4):
        for dz in (3.0, 0.0, -3.0):
            y, z = 5.0 + dy, dz
            tubes.append(Cylinder(1.25, 2.6).rot(0, 0, 90).at(L, y, z))
            tips.append(Cone(1.1, 0.3, 0.9).m("wd_hot" if hot else "wd_red").rot(0, 0, -90).at(L - 1.6, y, z))
    body = Subtract(box, Union(*tubes).m("wd_hole"))
    fins = Box(3.0, 0.7, 6.4, r=0.3).m("wd_dark").at(2.5, 10.4, 0)
    # the cover: a hazard plate in front of the tubes, hinged at the top front edge
    ang = 115.0 * cover
    lid = _hazard(Box(0.8, 5.1, 6.1, r=0.5).m("wd_yellow"), n=(0, 1, 1), period=3.6)
    lid = lid.at(0.8, -5.1, 0).rot(0, 0, ang).at(L + 0.4, 10.1, 0)
    return Union(body, fins, *tips, lid)


def _upper_arm():
    return Union(Capsule((0, 0, 0), (0, -L_UP + 1.0, 0), 4.0).m("wd_dark"),
                 Box(3.2, 3.8, 3.8, r=1.5).m("wd_gun").at(1.0, -5.0, 0))


def _forearm(side):
    z = 1 if side == "r" else -1
    elbow = Sphere(4.2).m("wd_gun")
    gaunt = Box(6.0, 7.0, 6.0, r=2.6).m("wd_white").at(0.6, -6.4, 0)
    cuff = Box(6.4, 1.5, 6.4, r=1.0).m("wd_yellow").at(0.6, -12.2, 0)
    palm = Box(4.0, 2.6, 4.4, r=1.3).m("wd_dark").at(0.8, -15.2, 0)
    claws = []
    for cz, cx in ((2.8, 2.0), (-2.8, 2.0), (0.0, -3.0)):
        claws.append(RoundCone((cx, -16.0, cz), (cx + (2.0 if cx > 0 else -0.8), -21.0, cz * 1.1), 1.6, 0.8)
                     .m("wd_gun"))
    return Union(elbow, gaunt, cuff, palm, *claws)


def _thigh():
    return Union(Capsule((0, 0, 0), (0, -L_TH + 1.0, 0), 5.0).m("wd_dark"),
                 Box(2.6, 5.6, 4.6, r=1.8).m("wd_white").at(3.8, -6.0, 0))


def _knee():
    return Union(Sphere(5.0).m("wd_gun"), Box(2.6, 3.2, 4.0, r=1.6).m("wd_white").at(4.0, 0.4, 0))


def _shin():
    shin = RoundCone((0, -1.0, 0), (0, -L_SH + 2.5, 0), 5.2, 6.6).m("wd_white")
    plate = _hazard(Box(2.0, 6.2, 4.4, r=1.0).m("wd_yellow").at(5.8, -8.4, 0), n=(0, 1, 1), period=3.8)
    piston = Capsule((-5.2, -2.0, 0), (-5.8, -11.0, 0), 1.5).m("wd_gun")
    return Union(shin, plate, piston)


def _foot():
    ankle = Sphere(4.0).m("wd_dark")
    sole = Box(10.4, 3.0, 6.8, r=1.8).m("wd_gun").at(2.6, -ANKLE_H + 3.0, 0)
    toe = Box(3.2, 2.4, 7.0, r=1.1).m("wd_yellow").at(10.4, -ANKLE_H + 2.6, 0)
    heel = Box(2.6, 1.8, 5.6, r=0.8).m("wd_dark").at(-7.4, -ANKLE_H + 2.0, 0)
    return Union(ankle, sole, toe, heel)


_S = None


def shapes():
    global _S
    if _S is None:
        _S = dict(torso=_torso(), plate=_plate(), pelvis=_pelvis(), pa_r=_pauldron("r"), pa_l=_pauldron("l"), upper=_upper_arm(),
                  fore_r=_forearm("r"), fore_l=_forearm("l"), thigh=_thigh(), knee=_knee(), shin=_shin(),
                  foot=_foot())
    return _S


# ---------------------------------------------------------------------------------------------------------- posing
BASE = dict(
    root=(0.0, 0.0), yaw=YAW, leg_ry=0.0,
    pelvis_x=0.0, pelvis_y=PELVIS_Y - 2.0,
    pelvis=(0, 0, 0), spine=(0, 0, -3), head=(0, 0, 0),
    sh_r=(0, 0, 14), el_r=(0, 0, 30), sh_l=(0, 0, 22), el_l=(0, 0, 30),
    pod_r=(0, 0, 0), pod_l=(0, 0, 0), cover=0.0, hot=False,
    foot_r=(-4.5, 0.0, 0.0), foot_l=(6.5, 0.0, 0.0),
    squash=(1.0, 1.0), eye=0.0, siren=0, flames=0.0, flick=0,
)


def P(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


SOLE = ((-10.0, -ANKLE_H), (13.6, -ANKLE_H))


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
    lr = pose["leg_ry"]
    if lr:
        px, py, pz = pose["pelvis"]
        sx, sy, sz = pose["spine"]
        pose["pelvis"] = (px, py + lr, pz)
        pose["spine"] = (sx, sy - lr, sz)
    base = trans(pose["root"][0], pose["root"][1], 0) @ rot(0, pose["yaw"], 0)
    return RIG.solve(pose, base), pose


def _flames(pose):
    t = pose["flames"]
    if t <= 0:
        return None
    out = []
    for k, z in enumerate((5.0, -5.0)):
        ln = t * (1.0 + 0.2 * math.sin(pose["flick"] * 2.3 + k * 1.9))
        out.append(RoundCone((-18.0, 5.5, z), (-21.0 - 0.3 * ln, 5.5 - ln, z), 3.4, 1.3).m("wd_flame"))
    return Union(*out)


def parts(pose):
    S = shapes()
    W, pose = solve(pose)
    out = []

    def add(shape, joint, shade=0, name="", inner=True, zbias=0.0):
        if shape is None:
            return
        out.append(Part(shape.xform(W[joint]), name=name, shade=shade, inner=inner, zbias=zbias))

    add(S["torso"], "spine", name="torso")
    add(S["plate"], "spine", name="plate")
    add(_flames(pose), "spine", name="flames", inner=False)
    add(S["pelvis"], "pelvis", name="pelvis")
    add(_head(pose["eye"], pose["siren"]), "head", name="head")
    for side, sh in (("r", 0), ("l", -1)):
        add(S["thigh"], f"hip_{side}", shade=sh, name=f"thigh_{side}")
        add(S["knee"], f"kn_{side}", shade=sh, name=f"knee_{side}")
        add(S["shin"], f"kn_{side}", shade=sh, name=f"shin_{side}")
        add(S["foot"], f"an_{side}", shade=sh, name=f"foot_{side}")
        add(S[f"pa_{side}"], f"pa_{side}", shade=sh, name=f"pa_{side}")
        add(_pod(pose["cover"], pose["hot"]), f"pod_{side}", shade=sh, name=f"pod_{side}")
        add(S["upper"], f"sh_{side}", shade=sh, name=f"upper_{side}")
        add(S[f"fore_{side}"], f"el_{side}", shade=sh, name=f"fore_{side}")
    return out, W


def world_point(pose, joint, local):
    W, _ = solve(pose)
    q = W[joint] @ np.array([*local, 1.0])
    return q[0], q[1]


def to_px(pose, x, y):
    """World point -> sheet offset from the anchor (dx right, dy down), squash included."""
    sx, sy = pose["squash"]
    return x * sx, -(y * sy) - LIFT


def pod_mouth(pose, side="r"):
    return world_point(pose, f"pod_{side}", (POD_LEN + 1.0, 5.0, 0))


# ---------------------------------------------------------------------------------------------------------- animations
PY = BASE["pelvis_y"]
TAU = 2 * math.pi


def idle(i, n=8):
    b = 0.5 - 0.5 * math.cos(TAU * i / n)
    eye = [-4.2, -3.0, 0.0, 3.0, 4.2, 3.0, 0.0, -3.0][i]
    return P(pelvis_y=PY - 0.8 * b, spine=(0, 0, -3 + 1.5 * b), head=(0, 4 - 8 * b, -1.5 * b),
             sh_r=(0, 0, 10 - 3 * b), el_r=(0, 0, 24 + 6 * b), sh_l=(0, 0, 4 - 2 * b), el_l=(0, 0, 20 + 5 * b),
             eye=eye, siren=1 if i in (0, 1) else 0)


# walk: 8 frames, contacts at 0 and 4, planted feet move 7.5 px per frame (75 px/s at 10 fps)
WALK = [(15.0, 0.0, 8), (7.5, 0.0, 0), (0.0, 0.0, 0), (-7.5, 0.0, 0), (-15.0, 0.0, -8), (-9.0, 6.0, -18),
        (3.5, 9.0, -4), (12.5, 4.5, 8)]


def move(i):
    phi = i / 8.0
    c = math.cos(TAU * phi)
    bob = math.cos(2 * TAU * phi)          # low at the contacts
    return P(pelvis_x=1.0, pelvis_y=PY - 1.6 - 1.4 * bob, spine=(5 * c, -6 * c, -9),
             head=(0, -4 * c, 4 + 1.5 * bob), sh_r=(0, 0, 10 - 26 * c), el_r=(0, 0, 30 - 8 * c),
             sh_l=(0, 0, 4 + 22 * c), el_l=(0, 0, 26 + 8 * c), foot_r=WALK[i], foot_l=WALK[(i + 4) % 8],
             eye=3.5, siren=0)


def attack_frames():
    """Missiles: 14 frames at 10 fps (the state lasts 1.4 s, the missiles leave at 0.5 s = frame 5)."""
    out = []
    # (pod pitch, cover, crouch, spine pitch, hot, fx)
    seq = [(8, 0.25, 0.6, -5, False, None), (24, 0.6, 1.4, -7, False, None), (44, 0.95, 2.4, -8, False, None),
           (62, 1.0, 3.0, -8, True, "charge0"), (68, 1.0, 3.2, -8, True, "charge1"),
           (74, 1.0, 4.4, -3, True, "fire"), (70, 1.0, 3.6, -5, False, "smoke0"), (66, 1.0, 3.0, -6, False, "smoke1"),
           (60, 1.0, 2.6, -6, False, "smoke2"), (50, 0.9, 2.2, -5, False, "smoke3"), (36, 0.7, 1.6, -4, False, None),
           (22, 0.45, 1.0, -4, False, None), (10, 0.2, 0.5, -3, False, None), (0, 0.0, 0.0, -3, False, None)]
    for k, (pod, cov, cr, sp, hot, fx) in enumerate(seq):
        brace = min(1.0, cr / 3.0)
        p = P(pelvis_y=PY - cr, spine=(0, 0, sp), head=(0, 0, 6 * brace), pod_r=(0, 0, 0.8 * pod),
              pod_l=(0, 0, 0.8 * pod),
              cover=cov, hot=hot, sh_r=(-14 * brace, 0, 18 + 8 * brace), el_r=(0, 0, 40 + 10 * brace),
              sh_l=(14 * brace, 0, 10 + 6 * brace), el_l=(0, 0, 36 + 8 * brace),
              foot_r=(5.0 + 2.5 * brace, 0, 0), foot_l=(-5.0 - 2.5 * brace, 0, 0), eye=2.5,
              squash=(1.03, 0.97) if fx == "fire" else (1.0, 1.0))
        out.append((p, fx, k))
    return out


def jump_frames():
    """8 frames at 12 fps, once: push-off with the jets, arms flung out, tuck, falls feet first with the arms raised
    wide (holds frame 7 until it lands)."""
    def up(py, sp, hd, ab, sw, el, fr, fl, **kw):
        # ab: arms abducted (out to the sides), sw: swung forward, el: elbow bend
        return P(pelvis_y=PY + py, spine=(0, 0, sp), head=(0, 0, hd), sh_r=(-ab, 0, sw), el_r=(0, 0, el),
                 sh_l=(ab, 0, sw + 6), el_l=(0, 0, el), foot_r=fr, foot_l=fl, **kw)
    t = [
        up(1.0, 6, -6, 10, -38, 16, (-1.0, 0, -22), (4.0, 0, -18), squash=(0.92, 1.09), flames=17, flick=0,
           fx="blast"),
        up(1.0, 2, -2, 40, -10, 30, (-1.0, 8.0, -18), (6.0, 6.0, -10), flames=18, flick=1),
        up(1.0, -2, 2, 70, 10, 46, (2.0, 12.0, -6), (7.0, 10.5, 0), flames=12, flick=2),
        up(1.0, -5, 5, 96, 20, 58, (2.0, 13.0, 0), (7.0, 12.0, 4), flames=6, flick=3),
        up(1.0, -5, 8, 112, 22, 66, (1.0, 10.0, 2), (6.0, 9.5, 4), flames=2, flick=4),
        up(1.0, -3, 10, 120, 20, 70, (0.0, 5.0, 2), (5.5, 5.0, 4)),
        up(0.6, -2, 10, 124, 18, 72, (-1.0, 1.5, 2), (5.5, 1.5, 4)),
        up(0.6, -2, 10, 125, 18, 73, (-1.0, 1.0, 2), (5.5, 1.0, 4), flick=5),
    ]
    out = []
    for k, p in enumerate(t):
        fx = p.pop("fx", None)
        out.append((p, fx, k))
    return out


def land_frames():
    """7 frames at 10 fps, once (0.7 s, the state after the stomp): impact, fists on the floor, dust, rise."""
    seq = [(7.0, (1.1, 0.88), 0), (6.6, (1.05, 0.94), 1), (5.6, (1.02, 0.98), 2), (4.0, (1, 1), 3),
           (2.4, (1, 1), 4), (1.0, (1, 1), 5), (0.0, (1, 1), 6)]
    out = []
    for k, (cr, sq, d) in enumerate(seq):
        u = cr / 7.0
        p = P(pelvis_y=PY - cr, spine=(0, 0, -3 - 26 * u), head=(0, 0, 18 * u), sh_r=(-10 * u, 0, 14 + 52 * u),
              el_r=(0, 0, 30 - 18 * u), sh_l=(10 * u, 0, 22 + 46 * u), el_l=(0, 0, 30 - 16 * u),
              foot_r=(-4.5 - 2.5 * u, 0, 0), foot_l=(6.5 + 2.0 * u, 0, 0), squash=sq, eye=3.0, siren=0)
        out.append((p, f"dust{d}", k))
    return out


def summon_frames():
    """12 frames at 10 fps, once (calling drones, 1.2 s; they beam in at 0.6 s): near arm up, siren blazing."""
    out = []
    for k in range(12):
        up = keys([(0, 0.0), (3, 1.0), (9, 1.0), (11, 0.0)], k)
        on = 3 <= k <= 9
        p = P(pelvis_y=PY - 0.5 * up, spine=(0, 0, -3 + 4 * up), head=(0, 10 * up, 6 * up),
              sh_r=(-16 * up, 0, 10 + 150 * up), el_r=(0, 0, 24 - 4 * up), sh_l=(0, 0, 4 - 10 * up),
              el_l=(0, 0, 20 + 20 * up), eye=1.0, siren=1 if (on and k % 2 == 1) or k in (4, 6) else 0)
        out.append((p, f"siren{k - 3}" if on else None, k))
    return out


def anims():
    return [
        ("idle", 6, "loop", [(idle(i), None, i) for i in range(8)], "hydraulic breathing, the eye scans, siren blink"),
        ("move", 10, "loop", [(move(i), "step" if i in (0, 4) else None, i) for i in range(8)],
         "heavy walk, contacts at 0 and 4, 75 px/s at 10 fps"),
        ("attack", 10, "once", attack_frames(),
         "missile volley: covers open, pods tilt up, charge, FIRE at frame 5 (0.5 s), smoke, pods back (1.4 s)"),
        ("jump", 12, "once", jump_frames(), "jets on take-off, tuck, fists up, falls feet first (holds frame 7)"),
        ("land", 10, "once", land_frames(), "stomp impact, fists on the floor, dust ring, rises (0.7 s)"),
        ("summon", 10, "once", summon_frames(), "calls drones: arm up, siren flashing 0.3-0.9 s (1.2 s)"),
    ]


# ---------------------------------------------------------------------------------------------------------- effects
def _effects(fx, pose, k):
    c = fx_canvas(SIZE, RENDER_ANCHOR)
    back = fx_canvas(SIZE, RENDER_ANCHOR)
    if fx is None:
        return c, back
    mouths = [pod_mouth(pose, s) for s in ("r", "l")]
    if fx.startswith("charge"):
        r = 2.2 if fx == "charge0" else 3.0
        for mx, my in mouths:
            F(c, c.circle(mx, my, r), "orange:5", prio=2.5)
            F(c, c.circle(mx, my, r * 0.55), "yellow:6", prio=2.5)
        if fx == "charge1":
            mx, my = mouths[0]
            sparks(c, [(mx - 4, my + 3, 0.7), (mx + 4, my + 5, 0.7)])
    elif fx == "fire":
        for j, (mx, my) in enumerate(mouths):
            flash(c if j == 0 else back, mx + 1.0, my + 2.0, 9.0 if j == 0 else 7.0, rays=4, ang=20)
        mx, my = mouths[0]
        streaks(c, [(mx - 2, my + 6, mx - 6, my + 15), (mx + 3, my + 6, mx + 8, my + 16)])
    elif fx.startswith("smoke"):
        s = int(fx[-1])
        rise = 5 + 5 * s
        for j, (mx, my) in enumerate(mouths):
            cv = c if j == 0 else back
            r = 3.0 + 1.2 * s
            puffs(cv, [(mx - 1, my + rise, r), (mx + 3, my + rise - 4, r * 0.8), (mx - 4, my + rise + 3, r * 0.7)],
                  seed=7 + j + s, holes=0.25 * s)
    elif fx == "step":
        fx_x = pose["foot_r"][0] if k == 0 else pose["foot_l"][0]
        puffs(back, [(fx_x + 8, 2.0, 2.4), (fx_x - 6, 1.8, 2.0)], shades=("grey:3", "grey:4", "grey:5", "grey:6"),
              seed=3 + k)
    elif fx == "blast":
        puffs(back, [(-14, 3.0, 6.0), (-24, 2.5, 4.5), (-6, 2.5, 4.0), (8, 2.5, 4.0)],
              shades=("grey:3", "grey:4", "grey:5", "grey:6"), seed=21)
        flash(back, -16, 4, 9.0, rays=4, ang=0)
    elif fx.startswith("dust"):
        d = int(fx[-1])
        if d <= 5:
            spread = 14 + 6 * d
            r = 6.5 + 0.8 * d
            lift = 3.0 + 1.6 * d
            puffs(c, [(spread + 6, lift, r), (spread - 4, lift + 2, r * 0.85), (spread + 13, lift - 1, r * 0.55),
                      (-spread - 4, lift, r), (-spread + 6, lift + 2, r * 0.85), (-spread - 11, lift - 1, r * 0.55)],
                  shades=("grey:3", "grey:4", "grey:5", "grey:6"), seed=11 + d, holes=0.17 * d)
        if d <= 1:
            rc = "white" if d == 0 else "steel:7"
            ring(c, 0, 1.5, 30 + 14 * d, 5.0 + d, 0.8, rc, arc=(180, 360))
            ring(back, 0, 1.5, 30 + 14 * d, 5.0 + d, 0.8, rc, arc=(0, 180))
            sparks(c, [(-26 - 8 * d, 10 + 3 * d), (28 + 8 * d, 12 + 3 * d), (-14, 18 + 4 * d), (16, 19 + 3 * d)])
    elif fx.startswith("siren"):
        s = int(fx[5:])
        hx, hy = world_point(pose, "head", SIREN)
        if pose["siren"]:
            flash(c, hx, hy + 1, 7.0, rays=4, ang=0, cols=("red:5", "orange:6", "white"))
        for q in range(2):
            rr = 6 + ((s * 5 + q * 9) % 18)
            if rr < 22:
                ring(c, hx, hy, rr, rr * 0.55, 0.7, "red:5" if q == 0 else "orange:5", arc=(10, 170))
    return c, back


def frame(job):
    name, i = job
    spec = {a[0]: a[3] for a in anims()}[name][i]
    pose, fx, k = spec
    ps, W = parts(pose)
    R = render(ps, SIZE, RENDER_ANCHOR, squash=pose["squash"])
    c, back = _effects(fx, pose, k)
    under(R, back)
    over(R, c)
    return pixelize(R)


def jobs():
    return [(a[0], i) for a in anims() for i in range(len(a[3]))]


def sheets(frames):
    sh = Sheet("warden", SIZE, ANCHOR, cols=16, title="THE WARDEN, the Academy's security mech gone rogue (faces right)")
    A = {a[0]: a[3] for a in anims()}
    fire = A["attack"][5][0]
    mx, my = to_px(fire, *pod_mouth(fire, "r"))
    fx_, fy_ = to_px(fire, *pod_mouth(fire, "l"))
    sh.point("muzzle", mx, my, "near missile pod mouth at the firing frame (attack 5); missiles leave upwards")
    sh.point("muzzle2", fx_, fy_, "far missile pod mouth (attack 5)")
    bx, by = to_px(BASE, *world_point(BASE, "head", SIREN))
    sh.point("siren", bx, by, "siren dome on the head (summon: drones are called here)")
    jx, jy = to_px(BASE, *world_point(BASE, "spine", (-17.0, 4.0, 0)))
    sh.point("jets", jx, jy, "jump-jet nozzles under the back unit")
    sh.note("anchor = feet centre on the ground line (box 60 x 78); the soles' lowest row is anchor y - 1")
    sh.note("attack/jump/land/summon are one-shots timed to WorldBoss states: play them from frame 0 on change")
    sh.note("glow: red eye, siren, lamps, charged missile tips, muzzle flashes, jet flames")
    for name, fps, mode, specs, note in anims():
        sh.anim(name, fps, mode, [frames[(name, i)] for i in range(len(specs))], note=note)
    idx = {a[0]: a[3] for a in sh.anims}
    arena(sh, [idx["idle"][0], idx["move"][2], idx["attack"][3], idx["attack"][5], idx["jump"][4], idx["jump"][7],
               idx["land"][0], idx["summon"][5]])
    return [sh]
