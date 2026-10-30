"""THE BROODMOTHER -- boss of episode 2 (sheet 160 x 160, anchor = bottom centre of her 84 x 60 box).

The hive queen of Thessa: a huge wasp-like insect in dark teal chitin with a violet crown of horns, two pairs of
translucent veined wings (membrane dithered so the arena shows through), six dangling legs, ivory mandibles, lime
compound eyes and a long segmented abdomen whose bioluminescent bands glow lime (her acid is the same colour).

Model space: x forward (she faces right), y up, z towards the viewer side. The body hangs on the thorax joint; the
view is yawed towards the viewer and tilted a little from above so the wings and the back read.
"""
import math

import numpy as np

from bake import (Box, Capsule, Ellipsoid, Extrude, Paint, Part, Rig, RoundCone, Sheet, Sphere, SmoothUnion, Union,
                  keys, material, pixelize, render, rot, trans)

from .bosskit import F, Slab, Stripes, arena, flash, fx_canvas, over, puffs, sparks, streaks, under

SIZE = (160, 160)
ANCHOR = (80, 128)             # bottom centre of the box; the body hovers above, legs dangle below
YAW = -24.0
TILT = 14.0                    # seen a little from above

# ---------------------------------------------------------------------------------------------------------- materials
material("bm_chitin", ["slate:0", "slate:1", "teal:1", "teal:2", "teal:3", "cyan:5"], style="metal",
         bands=[-0.45, -0.05, 0.35, 0.65], spec=0.9)
material("bm_plate", ["slate:1", "teal:1", "teal:2", "teal:3", "teal:5", "cyan:6"], style="metal",
         bands=[-0.4, 0.0, 0.35, 0.68], spec=0.9)
material("bm_leg", ["slate:0", "slate:1", "teal:1", "teal:2"], bands=[-0.3, 0.2, 0.6])
material("bm_glow", ["green:3", "green:4", "lime:4", "lime:5"], style="emit", bands=[0.25, 0.55, 0.9], prio=2.0,
         line="green:1")
material("bm_glow_hi", ["green:4", "lime:4", "lime:5", "lime:6"], style="emit", bands=[0.25, 0.55, 0.9], prio=2.0,
         line="green:1")
material("bm_eye", ["green:2", "lime:4", "lime:5", "lime:6", "white"], style="emit", bands=[0.1, 0.45, 0.8, 0.97],
         prio=3.0)
material("bm_wing", ["teal:3", "teal:4", "cyan:5", "ice:5", "ice:6", "white"], style="metal",
         bands=[-0.4, 0.0, 0.35, 0.65], spec=0.95, line="teal:1", line_lit="teal:2", inner=False)
material("bm_vein", ["teal:1", "teal:2", "teal:3"], bands=[-0.2, 0.4], line="teal:1", inner=False)
material("bm_horn", ["purple:1", "violet:2", "purple:3", "purple:4", "magenta:5"], bands=[-0.4, 0.0, 0.4, 0.75],
         line_lit="purple:0")
material("bm_ivory", ["brown:2", "tan:3", "tan:5", "tan:7"], bands=[-0.3, 0.2, 0.6])
material("bm_mouth", ["crimson:1", "crimson:2", "rose:3"], bands=[-0.2, 0.5])

WING_MATS = ("bm_wing",)

# ---------------------------------------------------------------------------------------------------------- skeleton
THORAX = (9.0, 37.0)
RIG = Rig()
RIG.joint("thorax", None, (0, 0, 0))
RIG.joint("head", "thorax", (15.0, 5.0, 0))
RIG.joint("ab0", "thorax", (-13.0, -4.0, 0))
RIG.joint("ab1", "ab0", (-16.0, -1.0, 0))
RIG.joint("ab2", "ab1", (-16.0, -2.0, 0))
for _s, _z in (("r", 1), ("l", -1)):
    RIG.joint(f"fw_{_s}", "thorax", (5.0, 11.0, 4.0 * _z))
    RIG.joint(f"hw_{_s}", "thorax", (-4.0, 10.0, 4.0 * _z))
    for _k, (_x, _y) in enumerate(((8.0, -9.0), (1.0, -11.0), (-6.0, -10.0))):
        RIG.joint(f"cx{_k}_{_s}", "thorax", (_x, _y, 6.0 * _z))
        RIG.joint(f"kn{_k}_{_s}", f"cx{_k}_{_s}", (0, -11.0, 0))
        RIG.joint(f"an{_k}_{_s}", f"kn{_k}_{_s}", (0, -13.0, 0))

# ---------------------------------------------------------------------------------------------------------- shapes
WS = 1.22   # wing scale
FORE = [(x * WS, y * WS) for x, y in [(0, 0), (4.5, 6), (6.0, 18), (4.5, 34), (1.0, 46), (-3.5, 52), (-8.0, 51),
                                      (-10.5, 44), (-11.0, 30), (-9.5, 15), (-6.5, 5), (-3.0, 0)]]
HIND = [(x * WS, y * WS) for x, y in [(0, 0), (4.0, 5), (5.0, 15), (3.0, 28), (-1.0, 37), (-5.5, 40), (-9.0, 37),
                                      (-10.0, 26), (-8.5, 12), (-5.0, 3), (-2.0, 0)]]


def _wing(poly, veins):
    w = Extrude(poly, 0.35, r=0.2).m("bm_wing")
    region = Union(*[Capsule(tuple(np.array(a) * WS), tuple(np.array(b) * WS), r * 1.1) for a, b, r in veins])
    return Paint(w, region, "bm_vein")


def _forewing():
    veins = [((-1, 0, 0), (-1.5, 46, 0), 0.75), ((-2, 8, 0), (3.5, 30, 0), 0.5), ((-3, 10, 0), (-9.0, 36, 0), 0.5),
             ((-1.5, 24, 0), (-7.5, 46, 0), 0.45), ((1.5, 22, 0), (0.5, 44, 0), 0.4), ((-9.5, 22, 0), (4.0, 24, 0), 0.4)]
    return _wing(FORE, veins)


def _hindwing():
    veins = [((-1.5, 0, 0), (-3.0, 36, 0), 0.7), ((-2, 8, 0), (3.0, 22, 0), 0.45), ((-3, 9, 0), (-8.5, 28, 0), 0.45),
             ((-8.0, 18, 0), (3.5, 18, 0), 0.38)]
    return _wing(HIND, veins)


def _thorax():
    body = Ellipsoid(15.5, 13.5, 12.5).m("bm_chitin")
    scutum = Ellipsoid(13.0, 8.0, 10.0).m("bm_plate").at(0.5, 6.5, 0)
    collar = Ellipsoid(6.0, 10.0, 10.5).m("bm_plate").at(12.0, 2.0, 0)
    spines = Union(*[RoundCone((x, 11.0, dz), (x - 6.0, 15.5 + h, dz * 1.4), 2.0, 0.35).m("bm_plate")
                     for x, h, dz in ((6.0, 0.0, 0.0), (-1.0, 1.5, 0.0), (-8.0, -1.5, 0.0), (2.0, -2.5, 6.0))])
    belly = Paint(Ellipsoid(11.0, 6.0, 9.0).m("bm_chitin").at(0, -8.0, 0), Stripes((1, 0, 0), 3.6, 0.4), "bm_glow")
    return Union(body, scutum, collar, spines, belly)


def _head(jaw=0.0, glow=False):
    skull = Ellipsoid(11.5, 10.0, 10.5).m("bm_chitin").at(6.5, 0, 0)
    face = Ellipsoid(6.0, 7.0, 7.0).m("bm_plate").at(14.0, -2.5, 0)
    eyes = Union(*[Ellipsoid(6.2, 7.2, 4.0).m("bm_eye").rot(0, 25 * s, 0).at(8.5, 1.5, 7.2 * s) for s in (1, -1)])
    eyes = Paint(eyes, Stripes((1, 1, 0), 2.2, 0.22), "bm_glow")
    ocelli = Union(*[Sphere(1.3).m("bm_eye").at(9.5 + dx, 7.6, dz) for dx, dz in ((0, 0), (-1.8, 2.6), (-1.8, -2.6))])
    mouth = Ellipsoid(3.4, 3.0, 4.4).m("bm_mouth").at(17.5, -6.5, 0) if jaw > 0.3 else None
    horns = []
    for dz, (tx, ty), r in ((0.0, (-6.0, 26.0), 2.8), (5.0, (-9.0, 22.0), 2.4), (-5.0, (-9.0, 22.0), 2.4),
                            (8.5, (-10.0, 16.0), 1.9), (-8.5, (-10.0, 16.0), 1.9)):
        mid = (tx * 0.3 + 6.0, ty * 0.6 + 3.0, dz * 1.3)
        horns.append(RoundCone((6.0, 7.0, dz * 0.8), mid, r, r * 0.7).m("bm_horn"))
        horns.append(RoundCone(mid, (tx, ty, dz * 1.6), r * 0.7, 0.35).m("bm_horn"))
    mands = []
    for sg in (1, -1):
        a = math.radians(6 + 40 * jaw)
        base = np.array([16.0, -6.5, 4.0 * sg])
        mid = base + np.array([7.5 * math.cos(a), -7.5 * math.sin(a), 2.6 * sg * (1 + jaw)])
        tip = mid + np.array([1.0, -6.0, -4.2 * sg])
        mands.append(RoundCone(tuple(base), tuple(mid), 2.6, 1.7).m("bm_ivory"))
        mands.append(RoundCone(tuple(mid), tuple(tip), 1.7, 0.4).m("bm_ivory"))
    ants = []
    for sg in (1, -1):
        b = (13.0, 5.5, 2.4 * sg)
        m = (18.0, 15.0, 4.0 * sg)
        t = (13.0, 24.0, 5.0 * sg)
        ants.append(Capsule(b, m, 0.7).m("bm_leg"))
        ants.append(Capsule(m, t, 0.55).m("bm_leg"))
    return Union(skull, face, eyes, ocelli, mouth, *horns, *mands, *ants)


def _abdomen_part(k, bright):
    """Abdomen pieces on the three joints: two segments each; glowing membranes and belly bands between plates."""
    g = "bm_glow_hi" if bright else "bm_glow"
    segs = {0: [(-3.0, 0.0, 12.0, 12.0, 11.5), (-14.0, -1.0, 13.5, 14.5, 13.0)],
            1: [(-7.0, -1.0, 13.0, 14.0, 12.5), (-17.0, -2.0, 11.0, 11.5, 10.5)],
            2: [(-6.0, -2.0, 8.5, 8.5, 8.0), (-14.0, -4.0, 6.0, 5.8, 5.4)]}[k]
    out = []
    for x, y, rx, ry, rz in segs:
        plate = Ellipsoid(rx * 0.62, ry, rz).m("bm_chitin").at(x, y, 0)
        belly = Slab((0, 1, 0), -1e3, y - ry * 0.3)
        out.append(Paint(plate, belly, g))
        out.append(Ellipsoid(rx * 0.5, ry * 0.88, rz * 0.88).m(g).at(x - rx * 0.55, y, 0))
    if k == 2:
        out.append(RoundCone((-18.0, -5.0, 0), (-27.0, -10.5, 0), 2.6, 0.4).m("bm_ivory"))
    return Union(*out)


def _leg(k, side):
    femur = Capsule((0, 0, 0), (0, -11.0, 0), 2.6 - 0.2 * k).m("bm_leg")
    knee = Sphere(2.5).m("bm_plate").at(0, -11.0, 0)
    spike = RoundCone((-0.5, -4.0, 0), (-3.5, -7.0, 0), 0.9, 0.2).m("bm_horn")
    return Union(femur, knee, spike)


def _shin(k):
    tib = RoundCone((0, 0, 0), (0, -13.0, 0), 2.2, 1.4).m("bm_leg")
    spur = RoundCone((0.0, -3.5, 0), (2.4, -7.0, 0), 0.9, 0.25).m("bm_ivory")
    return Union(tib, spur)


def _foot():
    tar = RoundCone((0, 0, 0), (1.0, -7.0, 0), 1.3, 0.8).m("bm_leg")
    claw = RoundCone((1.0, -7.0, 0), (3.4, -9.5, 0), 0.8, 0.25).m("bm_ivory")
    return Union(tar, claw)


_S = None


def shapes():
    global _S
    if _S is None:
        _S = dict(thorax=_thorax(), fore=_forewing(), hind=_hindwing(), shin=_shin(0), foot=_foot(),
                  legs=[_leg(k, "r") for k in range(3)])
    return _S


# ---------------------------------------------------------------------------------------------------------- posing
LEG_BASE = {0: ((0, 0, 40), (0, 0, -55), (0, 0, -20)), 1: ((0, 0, 10), (0, 0, -40), (0, 0, -15)),
            2: ((0, 0, -25), (0, 0, -25), (0, 0, -10))}

BASE = dict(root=(THORAX[0], THORAX[1]), pitch=0.0, head=(0, 0, 0), ab0=(0, 0, 8), ab1=(0, 0, 10), ab2=(0, 0, 12),
            fw=0.0, hw=10.0, sweep=18.0, jaw=0.0, bright=False, legs=0.0, reach=0.0, sway=0.0)


def P(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def solve(pose):
    q = {}
    q["head"] = pose["head"]
    for j in ("ab0", "ab1", "ab2"):
        q[j] = pose[j]
    # wings: elevation angle from vertical (phi) about the body x axis, swept back about z
    for s, sg in (("r", 1), ("l", -1)):
        q[f"fw_{s}"] = (sg * pose["fw"], 0, pose["sweep"])
        q[f"hw_{s}"] = (sg * pose["hw"], 0, pose["sweep"] + 22)
        for k in range(3):
            a, b, c = LEG_BASE[k]
            sw = pose["sway"] * (1 if k != 1 else -1)
            spread = 18 + 6 * k
            rz_a = a[2] + sw + pose["reach"] * (60 if k == 0 else 25 if k == 1 else -10)
            rz_b = b[2] - pose["legs"] * 20 - pose["reach"] * (20 if k == 0 else 10)
            q[f"cx{k}_{s}"] = (-sg * spread, 0, rz_a)
            q[f"kn{k}_{s}"] = (0, 0, rz_b)
            q[f"an{k}_{s}"] = (0, 0, c[2] - pose["reach"] * 25)
    base = (rot(TILT, 0, 0) @ rot(0, YAW, 0) @ trans(pose["root"][0], pose["root"][1], 0)
            @ rot(0, 0, pose["pitch"]))
    return RIG.solve(q, base)


def parts(pose):
    S = shapes()
    W = solve(pose)
    out = []

    def add(shape, joint, shade=0, name="", inner=True, zbias=0.0):
        if shape is not None:
            out.append(Part(shape.xform(W[joint]), name=name, shade=shade, inner=inner, zbias=zbias))

    add(S["thorax"], "thorax", name="thorax")
    add(_head(pose["jaw"]), "head", name="head")
    for k in range(3):
        add(_abdomen_part(k, pose["bright"]), f"ab{k}", name=f"ab{k}")
    for s, sh in (("r", 0), ("l", -1)):
        for k in range(3):
            add(S["legs"][k], f"cx{k}_{s}", shade=sh, name=f"leg{k}{s}")
            add(S["shin"], f"kn{k}_{s}", shade=sh, name=f"shin{k}{s}")
            add(S["foot"], f"an{k}_{s}", shade=sh, name=f"foot{k}{s}")
    add(S["hind"], "hw_l", shade=-1, name="hw_l", inner=False)
    add(S["fore"], "fw_l", shade=-1, name="fw_l", inner=False)
    add(S["hind"], "hw_r", name="hw_r", inner=False)
    add(S["fore"], "fw_r", name="fw_r", inner=False)
    return out, W


def world_point(pose, joint, local):
    W = solve(pose)
    q = W[joint] @ np.array([*local, 1.0])
    return q[0], q[1]


def mouth(pose):
    return world_point(pose, "head", (21.5, -8.5, 0))


# ---------------------------------------------------------------------------------------------------------- dithering
def dither_wings(spr):
    """Membrane interior pixels in a checker pattern: the arena shows through (veins and rims stay solid)."""
    ids = [__import__("bake").MATS[m].id for m in WING_MATS]
    m = np.isin(spr.mat, ids)
    inner = m.copy()
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        inner &= np.roll(np.roll(m, dy, 0), dx, 1)
    yy, xx = np.mgrid[0:spr.h, 0:spr.w]
    holes = inner & ((xx + yy) % 2 == 0)
    spr.col[holes] = -1
    spr.mat[holes] = -1
    spr.emit[holes] = False
    return spr


# ---------------------------------------------------------------------------------------------------------- animations
TAU = 2 * math.pi
BEAT = [-12.0, 22.0, 58.0, 26.0]           # wing angle from vertical over one beat (up, mid, down, mid)


def fly(i):
    """8 frames: two wing beats over one slow bob."""
    b = math.sin(TAU * i / 8)
    return P(root=(THORAX[0], THORAX[1] + 1.8 * b), pitch=2.0 * b, fw=BEAT[i % 4], hw=BEAT[(i + 1) % 4] + 6,
             ab0=(0, 0, 8 - 3 * b), ab1=(0, 0, 10 - 3 * b), ab2=(0, 0, 12 - 4 * b), head=(0, 0, -2 * b),
             sway=6 * b, legs=0.3 + 0.2 * b, bright=i in (0, 1, 7))


def idle(i):
    """8 frames: one slow, deep beat; glow breathing."""
    w = [-16.0, -6.0, 14.0, 40.0, 62.0, 44.0, 18.0, -4.0][i]
    b = math.sin(TAU * i / 8)
    return P(root=(THORAX[0], THORAX[1] + 1.2 * b), pitch=1.5 * b, fw=w, hw=w + 8, sway=4 * b, legs=0.1,
             ab0=(0, 0, 8 - 2 * b), ab1=(0, 0, 10 - 2 * b), ab2=(0, 0, 13 - 3 * b), bright=i in (2, 3, 4),
             head=(0, 0, -3 + 2 * b))


def attack(i):
    """6 frames: the dive / lunge: pitched down, wings swept back and buzzing, forelegs reaching, jaws wide,
    abdomen curled under, glow blazing."""
    b = [0, 1, 0, -1, 0, 1][i]
    return P(root=(THORAX[0] - 1.0, THORAX[1] - 2.0 + b), pitch=-24.0, fw=[-2.0, 34.0, 12.0, 40.0, 2.0, 34.0][i],
             hw=[10.0, 44.0, 20.0, 48.0, 12.0, 42.0][i], sweep=50.0, jaw=0.9 + 0.1 * (i % 2),
             ab0=(0, 0, 16), ab1=(0, 0, 22), ab2=(0, 0, 30), head=(0, 0, 14), reach=1.0, legs=0.0, sway=3 * b,
             bright=True)


def spit(i):
    """7 frames at 12 fps: rear back (anticipation), abdomen pumps, head snaps forward and spits, recover."""
    seq = [dict(pitch=6, head=(0, 0, -16), jaw=0.2, ab0=(0, 0, 4), ab1=(0, 0, 6), ab2=(0, 0, 8), fx=None),
           dict(pitch=10, head=(0, 0, -24), jaw=0.5, ab0=(0, 0, 14), ab1=(0, 0, 16), ab2=(0, 0, 18), fx="gather"),
           dict(pitch=12, head=(0, 0, -26), jaw=0.6, ab0=(0, 0, 16), ab1=(0, 0, 20), ab2=(0, 0, 22), fx="gather2"),
           dict(pitch=-8, head=(0, 0, 14), jaw=1.0, ab0=(0, 0, 4), ab1=(0, 0, 4), ab2=(0, 0, 6), fx="spit"),
           dict(pitch=-6, head=(0, 0, 10), jaw=0.9, ab0=(0, 0, 6), ab1=(0, 0, 8), ab2=(0, 0, 10), fx="drip"),
           dict(pitch=-2, head=(0, 0, 4), jaw=0.5, ab0=(0, 0, 8), ab1=(0, 0, 10), ab2=(0, 0, 12), fx="drip2"),
           dict(pitch=0, head=(0, 0, 0), jaw=0.1, ab0=(0, 0, 8), ab1=(0, 0, 10), ab2=(0, 0, 12), fx=None)]
    s = dict(seq[i])
    fx = s.pop("fx")
    p = P(fw=BEAT[i % 4], hw=BEAT[(i + 1) % 4] + 6, bright=i in (1, 2, 3), legs=0.3, **s)
    return p, fx


def anims():
    return [
        ("fly", 14, "loop", [(fly(i), None) for i in range(8)], "two wing beats per bob; abdomen glow pulses"),
        ("attack", 16, "loop", [(attack(i), f"dash{i % 3}") for i in range(6)],
         "dive / lunge: pitched down, wings buzzing back, forelegs and jaws open, abdomen curled"),
        ("idle", 9, "loop", [(idle(i), None) for i in range(8)], "slow deep beat, glow breathing"),
        ("spit", 12, "once", [spit(i) for i in range(7)],
         "rears back, spits at frame 3 (0.25 s) from the muzzle, recovers (0.58 s)"),
    ]


# ---------------------------------------------------------------------------------------------------------- effects
def _effects(fx, pose):
    c = fx_canvas(SIZE, ANCHOR)
    if fx is None:
        return c
    mx, my = mouth(pose)
    if fx.startswith("gather"):
        r = 2.0 if fx == "gather" else 3.0
        F(c, c.circle(mx - 1, my, r), "lime:5", prio=2.5)
        F(c, c.circle(mx - 1, my + 0.5, r * 0.5), "yellow:7", prio=2.5)
    elif fx == "spit":
        F(c, c.ellipse(mx + 7, my - 1, 6.0, 3.6, -12), "green:3", prio=2.5)
        F(c, c.ellipse(mx + 7.5, my - 0.6, 4.6, 2.6, -12), "lime:5", prio=2.5)
        F(c, c.circle(mx + 9, my, 1.6), "yellow:7", prio=2.5)
        sparks(c, [(mx + 15, my + 2, 1.0), (mx + 13, my - 4, 0.9), (mx + 4, my - 4, 0.8)], cols=("lime:6", "white"))
    elif fx.startswith("dash"):
        d = int(fx[-1])
        for k, (y, x0, ln) in enumerate(((52, -40, 16), (38, -50, 22), (24, -44, 14), (64, -30, 12))):
            o = ((d + k) % 3) * 4
            F(c, c.capsule(x0 - o, y, x0 - o - ln, y + 2, 0.55, 0.3), "ice:6", glow=False, prio=2.5)
    elif fx.startswith("drip"):
        k = 0 if fx == "drip" else 1
        for dx, dy, r in ((0.5, -3.0 - 4 * k, 1.2), (-1.5, -7.0 - 5 * k, 0.9)):
            F(c, c.circle(mx + dx, my + dy, r), "lime:5", prio=2.5)
    return c


def frame(job):
    name, i = job
    pose, fx = {a[0]: a[3] for a in anims()}[name][i]
    ps, W = parts(pose)
    R = render(ps, SIZE, ANCHOR)
    over(R, _effects(fx, pose))
    spr = pixelize(R)
    return dither_wings(spr)


def jobs():
    return [(a[0], i) for a in anims() for i in range(len(a[3]))]


def sheets(frames):
    sh = Sheet("broodmother", SIZE, ANCHOR, cols=16, title="THE BROODMOTHER, the hive queen of Thessa (faces right)")
    A = {a[0]: a[3] for a in anims()}
    mx, my = mouth(A["spit"][3][0])
    sh.point("muzzle", mx, -my, "mouth at the spitting frame (spit 3): acid leaves here")
    ax, ay = mouth(A["fly"][0][0])
    sh.point("mouth", ax, -ay, "mouth in the fly pose")
    tx, ty = world_point(BASE, "ab2", (-26.0, -10.0, 0))
    sh.point("sting", tx, -ty, "abdomen tip (mothlings could hatch here)")
    sh.note("anchor = bottom centre of the 84 x 60 box: the body hovers above it, legs and sting hang below")
    sh.note("wing membranes are dithered (every other pixel clear) so the arena shows through")
    sh.note("glow: compound eyes, ocelli, abdomen bands and belly, acid")
    for name, fps, mode, specs, note in anims():
        sh.anim(name, fps, mode, [frames[(name, i)] for i in range(len(specs))], note=note)
    idx = {a[0]: a[3] for a in sh.anims}
    arena(sh, [idx["fly"][0], idx["fly"][2], idx["idle"][4], idx["attack"][0], idx["attack"][1], idx["spit"][2],
               idx["spit"][3]], air=28)
    return [sh]
