"""icebat -- episode 3 swooper (box 26 x 20): a frost bat that hangs from the ceiling, dives at the hero and flies
back.

64 x 64 frames, anchor (32, 44) = the box's bottom centre; the box top (the ceiling when hanging) is row 24. idle =
hanging upside down from the ceiling (the feet grip at the box top), attack = diving, fly = flapping back home.

Model space (frontal): y up (head), z towards the viewer (face, belly), wings spread along +-x in the picture
plane and flap by turning about z (the classic sprite bat: the membranes always show). The whole bat is turned
towards the right (yaw) and leans into its flight.
"""
import math

import numpy as np

from bake import (Capsule, Cone, Ellipsoid, Extrude, Part, RoundCone, Sphere, Union, material, prism, rot, scaling,
                  trans)
from models._e34_common import TAU, Enemy, chip, flash, sparkle

E = Enemy("icebat", (64, 64), (32, 44), "frost bat (episode 3 swooper, faces right)", 3, ground=False)

material("icebat_fur", ["violet:1", "slate:3", "ice:4", "ice:5", "ice:6", "ice:7"], bands=[-0.5, -0.15, 0.2, 0.55, 0.85],
         line_lit="slate:2")
material("icebat_wing", ["violet:0", "violet:1", "violet:2", "blue:2", "blue:3", "blue:4"],
         bands=[-0.55, -0.3, -0.05, 0.3, 0.68])
material("icebat_wing_far", ["violet:1", "violet:2", "blue:2", "blue:3", "blue:4"], bands=[-0.45, -0.1, 0.3, 0.7])
material("icebat_bone", ["violet:1", "slate:3", "ice:4", "ice:5"], bands=[-0.3, 0.2, 0.7], prio=1.5)
material("icebat_frost", ["ice:5", "ice:6", "ice:7", "white"], bands=[-0.3, 0.2, 0.7], line="blue:1",
         line_lit="blue:1", prio=1.6)
material("icebat_skin", ["violet:0", "violet:1", "violet:2", "purple:3"], bands=[-0.3, 0.2, 0.7])
material("icebat_eye", ["cyan:5", "cyan:6", "white"], style="emit", bands=[0.35, 0.8], prio=3.0)
material("icebat_mouth", ["crimson:1", "crimson:2", "crimson:3"], bands=[-0.2, 0.4], prio=2.0)
material("icebat_fang", ["ice:6", "white"], bands=[0.2], prio=3.0)
material("icebat_ear_in", ["purple:2", "purple:3", "rose:4"], bands=[-0.1, 0.5])

# right wing membrane in the picture plane (x out, y up), shoulder at the origin; spread and folded share the count
SPREAD = [(0.0, 0.6), (5.2, 4.2), (9.6, 4.6), (16.0, 2.4), (12.6, -0.4), (13.6, -5.0), (9.4, -3.2), (7.6, -7.6),
          (5.0, -4.0), (1.6, -5.4), (-0.4, -1.2)]
FOLDED = [(0.0, 0.6), (2.6, 3.6), (3.6, 3.4), (4.6, 2.2), (3.8, 0.6), (4.2, -2.4), (3.2, -2.0), (3.2, -5.2),
          (2.2, -3.6), (1.0, -5.0), (-0.4, -1.2)]
WRIST, TIPS = 2, (3, 5, 7)


def wing_poly(spread):
    return [(a[0] + (b[0] - a[0]) * spread, a[1] + (b[1] - a[1]) * spread) for a, b in zip(FOLDED, SPREAD)]


def wing(spread, flap, wrap=0.0, far=False):
    """The right wing (mirrored for the left by the caller): membrane, arm and finger bones, frost tips.
    flap = degrees about z (> 0 raises it), wrap = degrees about y (< 0 folds it forwards round the body)."""
    poly = wing_poly(spread)
    mem = Extrude(poly, 0.3, r=0.12).m("icebat_wing_far" if far else "icebat_wing")
    w0, wr = np.array([*poly[0], 0.2]), np.array([*poly[WRIST], 0.25])
    bones = [Capsule((0, 0.6, 0.2), (poly[1][0], poly[1][1], 0.25), 0.62).m("icebat_bone"),
             Capsule((poly[1][0], poly[1][1], 0.25), wr, 0.55).m("icebat_bone")]
    tips = []
    for k in TIPS:
        t = np.array([*poly[k], 0.2])
        bones.append(Capsule(wr, t, 0.36).m("icebat_bone"))
        if spread > 0.4:
            d = t - wr
            ang = math.degrees(math.atan2(d[1], d[0])) - 90
            tips.append(prism(5, 0.8, 0.3, 1.5, 0.3).m("icebat_frost").rot(0, 0, ang).at(*t))
    thumb = Cone(0.45, 0.05, 0.8).m("icebat_frost").rot(0, 0, 30).at(poly[1][0] - 0.2, poly[1][1] + 0.9, 0.3)
    return Union(mem, *bones, *tips, thumb).rot(0, wrap, flap)


def head(mouth=0.0, ears=0.0, blink=False):
    """Head centred on the skull; the face looks along +z. mouth 0..1, ears -1 (laid back) .. 1 (perked)."""
    skull = Sphere(3.1).m("icebat_fur")
    cheeks = Ellipsoid(3.4, 2.4, 2.6).m("icebat_fur").at(0, -0.8, 0.2)
    face = Ellipsoid(2.3, 2.0, 1.4).m("icebat_skin").at(0, -0.4, 2.2)
    snout = Ellipsoid(1.3, 1.0, 1.0).m("icebat_skin").at(0, -1.1, 3.3)
    nose = Ellipsoid(0.7, 0.45, 0.4).m("icebat_mouth").at(0, -0.8, 4.2)
    eyes = [Ellipsoid(0.85, 0.3 if blink else 0.9, 0.6).m("icebat_skin" if blink else "icebat_eye")
            .at(x, 0.5, 2.9) for x in (1.15, -1.15)]
    parts = [skull, cheeks, face, snout, nose, *eyes]
    if mouth > 0:
        parts.append(Ellipsoid(1.3, 0.5 + 0.5 * mouth, 0.6).m("icebat_mouth").at(0, -2.2 - 0.3 * mouth, 3.0))
        parts += [Cone(0.4, 0.05, 0.75).m("icebat_fang").rot(0, 0, 180).at(x, -2.2, 3.4) for x in (0.65, -0.65)]
    ear = Extrude([(-1.5, 0), (1.3, 0), (0.6, 5.4)], 0.42, r=0.2).m("icebat_fur")
    ear_in = Extrude([(-0.8, 0.5), (0.7, 0.5), (0.4, 4.0)], 0.2).m("icebat_ear_in").at(0, 0, 0.3)
    e = Union(ear, ear_in)
    lay = 34 * max(0.0, -ears) - 8 * max(0.0, ears)
    for s in (1, -1):
        m = np.diag([s, 1.0, 1, 1])
        parts.append(e.rot(-10 - 25 * max(0.0, -ears), 0, -(12 + lay)).at(1.9, 1.6, -0.2).xform(m))
    return Union(*parts)


def bat(spread=1.0, flap=0.0, wrap=0.0, mouth=0.0, ears=0.0, blink=False, head_t=(0.0, 0.0), legs=0.0,
        flap_l=None, spread_l=None):
    """Body-space shapes [(name, shape, shade)]; the torso centre at the origin. Right wing = +x (the far wing
    once the bat is turned to the right), left wing mirrored."""
    torso = Union(Ellipsoid(3.4, 4.4, 2.9).m("icebat_fur"),
                  Ellipsoid(2.4, 2.8, 1.6).m("icebat_fur").at(0, -0.6, 1.7),
                  prism(5, 0.9, 0.4, 1.4, 0.4).m("icebat_frost").rot(-30, 0, 0).at(0, 2.4, -2.2))
    H = trans(head_t[0], 5.4, 0.6) @ rot(head_t[1], 0, 0)
    legs_s = []
    for s in (1, -1):
        a = np.array([s * 1.6, -3.4, 0.2])
        b = a + np.array([s * 0.8, -2.2 - 0.6 * legs, -0.6 * legs])
        legs_s.append(Capsule(a, b, 0.55).m("icebat_skin"))
        for k in (-1, 0, 1):
            legs_s.append(RoundCone(b, b + np.array([0.5 * k, -0.9, 0.5]), 0.38, 0.18).m("icebat_frost"))
    mirror = np.diag([-1.0, 1, 1, 1])
    fl = flap if flap_l is None else flap_l
    sl = spread if spread_l is None else spread_l
    w_r = wing(spread, flap, wrap, far=True).at(2.2, 1.4, 0)
    w_l = wing(sl, fl, wrap).at(2.2, 1.4, 0).xform(mirror)
    return [("wing_r", w_r, -1), ("legs", Union(*legs_s), 0), ("torso", torso, 0),
            ("head", head(mouth, ears, blink).xform(H), 0), ("wing_l", w_l, 0)]


def scene(M, shapes):
    return [Part(s.xform(M), name=n, shade=sh) for n, s, sh in shapes]


YAW = 34.0     # the face turned towards the right
S = 1.22       # model scale


# ---------------------------------------------------------------------------------------------------------- animations

def fly(i):
    n = 8
    t = i / n
    flap = [58, 34, 4, -26, -40, -24, 10, 40][i]                 # downstroke 0..4, upstroke 4..8
    spread = [0.86, 1.0, 1.0, 0.95, 0.86, 0.66, 0.5, 0.62][i]
    bob = [-1.0, -0.4, 0.4, 1.2, 1.4, 0.8, 0.0, -0.8][i]       # each downstroke lifts the body
    M = trans(0, 9.6 + bob, 0) @ rot(0, YAW, -12) @ rot(10, 0, 0) @ scaling(S)
    shapes = bat(spread, flap, ears=0.6, legs=0.3 * math.sin(TAU * t), head_t=(0.0, -6))
    return E.draw(scene(M, shapes))


def attack(i):
    """Dive: head first towards the prey (down and forward), wings swept back behind it, jaws open."""
    flap = [-56, -64, -52, -62][i]
    spread = [0.66, 0.58, 0.7, 0.6][i]
    M = trans(1.5, 10.0, 0) @ rot(0, YAW - 10, -122) @ rot(12, 0, 0) @ scaling(S)
    spr = E.draw(scene(M, bat(spread, flap, mouth=1.0, ears=-1.0, legs=-0.8, head_t=(0.0, 8),
                              flap_l=flap + 6)))
    # streaks of cold air trailing behind (up-left)
    for k, (x, y) in enumerate(((17, 17 + i % 2), (13, 23 - i % 2), (22, 12))):
        for d in range(3 + (i + k) % 2):
            if spr.get(x - d, y - d) < 0:
                spr.put(x - d, y - d, "ice:6" if d == 0 else "ice:4")
    return spr


def hanging(breathe, ears, blink, look):
    """The bat hanging from its feet (origin = the ceiling grip), wrapped in its closed wings: [(name, shape, shade)]."""
    feet = []
    for s in (1, -1):
        a, b = np.array([s * 1.3, -3.2, 0.0]), np.array([s * 1.0, -0.6, 0.0])
        feet.append(Capsule(a, b, 0.6).m("icebat_skin"))
        for k in (-1, 0, 1):
            feet.append(RoundCone(b, b + np.array([0.5 * k, 0.9, 0.3 * k]), 0.36, 0.18).m("icebat_frost"))
    body = Ellipsoid(3.1, 5.2, 2.6).m("icebat_fur").at(0, -8.0, -0.6)
    w = 1.0 + breathe
    halves = []
    for s, mat in ((1, "icebat_wing_far"), (-1, "icebat_wing")):
        half = Ellipsoid(3.6 * w, 6.6, 2.6 * w).m(mat).rot(0, 0, -s * 9).at(s * 2.1, -8.6, 0.9)
        ridge = Capsule((s * 2.4, -3.8, 2.9), (s * 3.2, -12.6, 2.7), 0.5).m("icebat_bone")
        ridge2 = Capsule((s * 4.4, -5.0, 1.7), (s * 4.7, -11.4, 1.5), 0.42).m("icebat_bone")
        thumb = Cone(0.65, 0.05, 1.1).m("icebat_frost").rot(0, 0, 180 - s * 24).at(s * 3.6, -13.8, 2.0)
        halves.append(Union(half, ridge, ridge2, thumb))
    hd = head(0.0, ears, blink).xform(trans(0, -15.4, 0.8) @ rot(0, look, 180) @ scaling(1.15))
    return [("feet", Union(*feet), 0), ("body", body, 0), ("wing_r", halves[0], -1), ("wing_l", halves[1], 0),
            ("head", hd, 0)]


def idle(i):
    """Hanging from the ceiling wrapped in its wings: a slow sway, breathing, an ear twitch and a blink."""
    n = 8
    t = i / n
    sway = 4 * math.sin(TAU * t)
    breathe = 0.12 * math.sin(TAU * t)
    # built hanging: feet at the top (world y = 20, the ceiling), the cocoon of closed wings, the head below
    M = trans(0.0, 20.6, 0) @ rot(0, 0, sway) @ rot(0, YAW * 0.5, 0)
    shapes = hanging(breathe, ears=[-0.7, -0.7, -0.1, -0.4, -0.7, -0.7, -0.7, -0.7][i], blink=i == 5,
                     look=[0, 0, 0, 6, 10, 10, 4, 0][i])
    spr = E.draw(scene(M, shapes))
    if i in (3, 4):
        sparkle(spr, 27, 33 - (i - 3), 1)
    return spr


def hurt(i):
    flap = [-50, -10, 30][i]
    M = trans(-1.0 + 0.5 * i, 9.0 + 0.4 * i, 0) @ rot(0, YAW, 24 - 10 * i) @ rot(10, 0, 0) @ scaling(S)
    spr = E.draw(scene(M, bat(0.7, flap, mouth=0.6, ears=-1.0, blink=True, flap_l=flap - 30)))
    if i == 0:
        flash(spr)
    if i < 2:
        for k, (x, y) in enumerate(((20, 22), (44, 24), (30, 14))):
            chip(spr, x - 2 * i, y - 2 * i, k)
    return spr


E.anim("idle", 6, "loop", 8, idle, "hanging upside down, feet at the box top (row 24)")
E.anim("fly", 16, "loop", 8, fly, "flapping; downstroke 0-4")
E.anim("attack", 16, "loop", 4, attack, "diving: wings raised in a V, jaws open")
E.anim("hurt", 12, "once", 3, hurt, "")
E.context["idle"] = ("ceiling", 24)
E.note("glow: eyes")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
