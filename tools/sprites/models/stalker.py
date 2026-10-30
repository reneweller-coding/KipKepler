"""stalker -- episode 2 charger (box 36 x 30): a lean raptor-like predator with glowing stripes.

64 x 64 frames, anchor (32, 60). move = prowling walk; attack = the charge (one loop for the 0.5 s wind-up and the
sprint: head low, jaws open, stripes blazing); hurt = dazed after hitting a wall (head lolling, stars).
Digitigrade legs: two-bone IK from the hip to an ankle held above the toes.
"""
import math

from bake import Box, Cone, Ellipsoid, Paint, Part, RoundCone, Sphere, Union, ik2, material
from models._e12_common import A64, S64, anim_jobs, make_sheet, put, shoot, to_px

YAW = -18.0
L1, L2 = 7.6, 7.8

material("stk_skin", ["slate:1", "slate:2", "blue:2", "slate:3", "slate:4", "steel:5"],
         bands=[-0.55, -0.25, 0.1, 0.45, 0.8], line="outline", line_lit="outline")
material("stk_belly", ["tan:3", "tan:4", "tan:5", "tan:6"], bands=[-0.3, 0.2, 0.65], line="brown:1")
material("stk_stripe", ["teal:3", "teal:4", "cyan:5"], style="emit", bands=[0.3, 0.7], prio=2.0)
material("stk_stripe_hot", ["teal:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.6, 0.85], prio=2.0)
material("stk_stripe_off", ["slate:2", "teal:2", "teal:3"], bands=[-0.2, 0.5], prio=2.0)
material("stk_eye", ["orange:4", "yellow:6", "white"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("stk_eye_shut", ["slate:1", "slate:2"], bands=[0.5], prio=3.0)
material("stk_claw", ["tan:5", "tan:7", "white"], bands=[0.0, 0.5], prio=2.0)
material("stk_mouth", ["crimson:1", "crimson:2", "crimson:3"], bands=[0.0, 0.6], line="outline")
material("stk_crest", ["violet:1", "violet:2", "purple:3", "purple:4"], bands=[-0.3, 0.2, 0.7], line="violet:0")


def body(stripes, lean=0.0, breathe=0.0):
    trunk = Ellipsoid(8.8, 5.0 + breathe, 4.6).rot(0, 0, 8).m("stk_skin").at(0.6, 16.6, 0)
    trunk = Paint(trunk, Ellipsoid(8.0, 3.0, 4.4).rot(0, 0, 8).at(1.4, 13.6, 0), "stk_belly")
    bands_ = Union(*[Box(0.65, 4.0, 6.0).rot(0, 0, -16).at(x, 20.0 + x * 0.12, 0) for x in (-5.6, -2.4, 0.8, 4.0)])
    trunk = Paint(trunk, bands_, stripes)
    return trunk


def tail(sway, stripes):
    pts = [(-6.4, 16.6), (-12.6, 17.6), (-18.4, 18.4 + sway * 0.6), (-23.6, 19.2 + sway * 1.4)]
    rad = [(3.6, 2.6), (2.6, 1.7), (1.7, 0.6)]
    segs = [RoundCone((a[0], a[1], 0), (b[0], b[1], 0), r1, r2).m("stk_skin") for (a, b), (r1, r2) in
            zip(zip(pts, pts[1:]), rad)]
    rings = Union(*[Box(0.55, 4.0, 4.0).rot(0, 0, -6).at(x, 18.0 + (x + 12) * -0.1, 0) for x in (-11.0, -15.6, -19.8)])
    return Paint(Union(*segs), rings, stripes)


def head(jaw, eye, neck=(0.0, 0.0)):
    """Neck from the chest to the skull; neck = (dx, dy) head offset (lower = attack)."""
    hx, hy = 12.6 + neck[0], 24.4 + neck[1]
    neck_s = RoundCone((6.8, 19.6, 0), (hx - 2.0, hy - 0.6, 0), 3.0, 2.2).m("stk_skin")
    skull = Ellipsoid(4.0, 2.9, 2.8).m("stk_skin").at(hx, hy, 0)
    snout = RoundCone((hx + 1.0, hy - 0.2, 0), (hx + 6.0, hy - 1.4, 0), 2.2, 1.2).m("stk_skin")
    a = math.radians(-jaw)
    jx, jy = hx + 0.4, hy - 1.6
    tip = (jx + 5.4 * math.cos(a) - 0.0, jy + 5.4 * math.sin(a) - 0.6)
    lower = RoundCone((jx, jy, 0), (tip[0], tip[1], 0), 1.4, 0.8).m("stk_skin")
    mouth = RoundCone((jx + 0.6, jy + 0.3, 0), (hx + 5.2, hy - 1.6, 0), 1.0, 0.6).m("stk_mouth") if jaw > 6 else None
    teeth = []
    if jaw > 6:
        for k in range(3):
            t = 0.35 + 0.22 * k
            teeth.append(Cone(0.45, 0.05, 0.6).m("stk_claw").rot(180, 0, 0).at(hx + 1.6 + 4.0 * t, hy - 2.0 - 0.9 * t, 1.0))
            teeth.append(Cone(0.45, 0.05, 0.6).m("stk_claw").at(jx + (tip[0] - jx) * t, jy + (tip[1] - jy) * t + 1.0, 0.9))
    eye_s = Sphere(1.05).m(eye).at(hx + 1.4, hy + 0.9, 2.0)
    brow = Box(1.6, 0.5, 1.0, r=0.25).m("stk_crest").rot(0, 0, -14).at(hx + 1.2, hy + 2.1, 1.8)
    crest = [Cone(0.9, 0.1, 1.4).m("stk_crest").rot(0, 0, 40 + 12 * k).at(hx - 2.6 - 1.4 * k, hy + 1.8 - 0.5 * k, 0)
             for k in range(3)]
    parts = [neck_s, skull, snout, lower, eye_s, brow, *crest, *teeth]
    if mouth is not None:
        parts.append(mouth)
    return Union(*parts)


def leg(foot, z, pitch=0.0):
    """Digitigrade leg to the toe contact point foot = (x, y); returns the shape in model space."""
    fx, fy = foot
    ax, ay = fx - 1.8, fy + 3.8
    hip = (-3.6, 14.6)
    a1, a2 = ik2(hip, (ax, ay), L1, L2, bend=1.0)
    r1, r2 = math.radians(a1), math.radians(a1 + a2)
    knee = (hip[0] + L1 * math.sin(r1), hip[1] - L1 * math.cos(r1))
    thigh = RoundCone((hip[0], hip[1], z), (knee[0], knee[1], z), 3.0, 1.6)
    shin = RoundCone((knee[0], knee[1], z), (ax, ay, z), 1.4, 1.0)
    meta = RoundCone((ax, ay, z), (fx, fy + 0.6, z), 1.0, 0.8)
    toe = RoundCone((fx, fy + 0.6, z), (fx + 2.8, fy + 0.4, z), 0.8, 0.5)
    claw = Cone(0.6, 0.05, 0.8).m("stk_claw").rot(0, 0, -100).at(fx + 3.6, fy + 0.4, z)
    sickle = Cone(0.55, 0.05, 0.9).m("stk_claw").rot(0, 0, -20).at(fx + 0.8, fy + 1.8, z)
    return Union(Union(thigh, shin, meta, toe).m("stk_skin"), claw, sickle)


def arms(z, reach=0.0):
    s, e, h = (7.4, 15.2, z), (9.0 + reach, 12.6, z * 1.1), (11.0 + reach * 1.6, 13.4 + reach * 0.6, z * 1.1)
    return Union(RoundCone(s, e, 1.0, 0.7).m("stk_skin"), RoundCone(e, h, 0.7, 0.5).m("stk_skin"),
                 Cone(0.45, 0.05, 0.7).m("stk_claw").rot(0, 0, -110).at(h[0] + 0.8, h[1] - 0.2, h[2]))


def parts(foot_n, foot_f, bob=0.0, pitch=0.0, sway=0.0, jaw=4.0, eye="stk_eye", stripes="stk_stripe", neck=(0, 0),
          reach=0.0, breathe=0.0):
    def place(s, rotate=True):
        s = s.at(0, bob, 0)
        if pitch and rotate:
            s = s.at(3.6, -14.6, 0).rot(0, 0, pitch).at(-3.6, 14.6, 0)
        return s.rot(0, YAW, 0)
    upper = Union(body(stripes, breathe=breathe), tail(sway, stripes), head(jaw, eye, neck))
    return [Part(place(upper), name="body"),
            Part(place(arms(2.6, reach)), name="arm_n"), Part(place(arms(-2.6, reach)), name="arm_f", shade=-1),
            Part(leg(foot_n, 3.2).rot(0, YAW, 0), name="leg_n"),
            Part(leg(foot_f, -3.2).rot(0, YAW, 0), name="leg_f", shade=-1)]


WALK = [(6.0, 0.0), (3.0, 0.0), (0.0, 0.0), (-3.0, 0.0), (-6.0, 0.2), (-3.4, 3.4), (1.6, 4.2), (5.0, 1.8)]
RUN = [(9.0, 0.0), (4.4, 0.0), (-0.6, 0.0), (-5.4, 0.6), (-8.8, 3.6), (-5.6, 6.6), (1.0, 7.0), (6.8, 4.0)]

ANIMS = [
    ("move", 12, "loop", 8, "prowling walk, contact at 0 and 4"),
    ("attack", 16, "loop", 8, "charge: head low, jaws open, stripes blazing, long strides"),
    ("hurt", 10, "loop", 6, "dazed after a wall: head lolls, eyes shut, stars"),
]


def frame(job):
    name, i = job
    if name == "move":
        ph = 2 * math.pi * i / 8
        bob = 0.5 * math.cos(2 * ph)
        return shoot(parts(WALK[i], WALK[(i + 4) % 8], bob=bob - 0.3, sway=1.4 * math.sin(ph),
                           neck=(0.0, 0.6 * math.cos(2 * ph)), jaw=3.0,
                           stripes="stk_stripe" if i % 4 < 2 else "stk_stripe_off"))
    if name == "attack":
        ph = 2 * math.pi * i / 8
        bob = 0.9 * math.cos(2 * ph)
        return shoot(parts(RUN[i], RUN[(i + 4) % 8], bob=bob - 1.6, pitch=-9.0, sway=0.8 * math.sin(ph),
                           jaw=26 + 6 * math.sin(2 * ph), neck=(1.6, -2.6), stripes="stk_stripe_hot", reach=1.0))
    ph = 2 * math.pi * i / 6
    spr = shoot(parts((3.4, 0.0), (-3.0, 0.0), bob=-1.2, pitch=4.0, sway=-2.0, jaw=12,
                      neck=(-1.2 + 0.8 * math.sin(ph), -3.4 + 0.6 * math.cos(ph)),
                      eye="stk_eye_shut", stripes="stk_stripe_off", breathe=0.3 * math.sin(ph)))
    cx, cy = to_px(11.0 + 0.8 * math.sin(ph), 27.0)
    for k in range(3):
        a = 2 * math.pi * (i / 6 + k / 3)
        sx, sy = cx + int(round(5.5 * math.cos(a))), cy + int(round(1.8 * math.sin(a)))
        put(spr, sx, sy, "yellow:6")
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            put(spr, sx + dx, sy + dy, "yellow:4" if k else "white")
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("stalker", S64, A64, "stalker raptor (episode 2 charger, box 36 x 30, faces right)", ANIMS,
                      frames, notes=["anchor = bottom centre of the box (feet on the ground line)",
                                     "the tail sticks out about 5 px behind the box",
                                     "glow: teal body stripes (brighter in attack), amber eye, daze stars"])
