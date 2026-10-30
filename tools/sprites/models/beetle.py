"""beetle -- episode 2 walker (box 30 x 22): an armoured jungle beetle with a big amber front shield plate.

64 x 64 frames, anchor (32, 60). Its front plate blocks shots (engine side). Violet iridescent wing case with teal
bioluminescent spots, six legs in a tripod gait, a horn on the shield.
"""
import math

from bake import Box, Capsule, Ellipsoid, Intersect, Paint, Part, RoundCone, Sphere, Union, material
from models._e12_common import A64, S64, anim_jobs, make_sheet, shoot, spark, to_px

YAW = -28.0

material("btl_shell", ["violet:1", "violet:2", "purple:3", "purple:4", "violet:5", "teal:5"], style="metal",
         bands=[-0.5, -0.15, 0.2, 0.55], spec=0.86, line="violet:0", line_lit="violet:0")
material("btl_belly", ["violet:1", "violet:2", "purple:2", "purple:3"], bands=[-0.3, 0.2, 0.7], line="violet:0")
material("btl_plate", ["brown:2", "orange:3", "orange:4", "yellow:4", "yellow:5", "yellow:6"], style="metal",
         bands=[-0.55, -0.3, 0.05, 0.45], spec=0.9, line="brown:1", line_lit="brown:1")
material("btl_rim", ["brown:1", "brown:2", "brown:3", "orange:3"], bands=[-0.3, 0.2, 0.7], line="brown:0")
material("btl_leg", ["violet:0", "violet:1", "purple:2", "purple:3"], bands=[-0.3, 0.2, 0.7], line="outline")
material("btl_spot", ["teal:4", "cyan:5", "cyan:6"], style="emit", bands=[0.4, 0.8], prio=2.5)
material("btl_spot_dim", ["teal:3", "teal:4", "teal:5"], style="emit", bands=[0.4, 0.8], prio=2.5)
material("btl_eye", ["orange:4", "yellow:6", "white"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("btl_eye_hurt", ["red:4", "orange:6", "white"], style="emit", bands=[0.4, 0.8], prio=3.0)


def shell(spots, breathe=0.0):
    c = (-3.6, 9.4 + breathe, 0)
    case = Ellipsoid(10.0, 8.0 + breathe * 0.5, 7.6).m("btl_shell").at(*c)
    case = Intersect(case, Box(14, 10, 10).at(0, 12.6, 0))
    seam = Box(11, 0.5, 0.45).at(-3.6, 17.2, 0)
    case = Paint(case, seam, "btl_belly")
    belly = Ellipsoid(9.6, 3.6, 6.4).m("btl_belly").at(-2.4, 6.4, 0)
    out = [case, belly]
    for k, (x, y, z) in enumerate(((-9.4, 11.6, 5.2), (-4.6, 14.2, 5.4), (0.2, 12.4, 5.8), (-7.2, 16.0, 2.4),
                                   (-1.8, 16.8, 2.6))):
        out.append(Sphere(1.05 if k < 3 else 0.85).m(spots[k % len(spots)]).at(x, y + breathe, z))
    return Union(*out)


def plate(eye, lift=0.0):
    """The front shield: a rounded amber pronotum over the head, a rim, a forward horn, eyes under the lip."""
    dome = Ellipsoid(6.4, 7.4, 7.8).at(5.4, 8.8, 0)
    shield = Intersect(dome, Box(6.0, 10, 10).at(7.6, 10.4, 0)).m("btl_plate")
    rim = Intersect(Ellipsoid(6.8, 7.8, 8.2).at(5.4, 8.8, 0), Box(6.0, 0.7, 10).at(7.6, 2.4, 0)).m("btl_rim")
    ridge = Paint(shield, Box(9, 0.45, 0.5).rot(0, 0, -30).at(7.0, 12.6, 0), "btl_rim")
    horn = Union(RoundCone((8.8, 13.6, 0), (12.6, 17.0, 0), 1.9, 1.0), RoundCone((12.6, 17.0, 0), (14.6, 20.2, 0), 1.0, 0.4)
                 ).m("btl_plate")
    head = Ellipsoid(3.4, 2.6, 4.2).m("btl_belly").at(9.2, 3.2, 0)
    eyes = Union(Sphere(1.05).m(eye).at(11.2, 3.6, 2.4), Sphere(0.95).m(eye).at(11.4, 3.6, -1.6))
    jaws = Union(RoundCone((11.4, 2.4, 1.6), (13.8, 1.4, 1.0), 0.8, 0.35),
                 RoundCone((11.4, 2.4, -1.6), (13.6, 1.4, -1.2), 0.8, 0.35)).m("btl_rim")
    feel = Union(Capsule((6.8, 15.4, 2.6), (3.6, 19.4, 5.0), 0.35), Capsule((6.8, 15.4, -2.6), (4.0, 19.2, -3.8), 0.35)
                 ).m("btl_leg")
    return Union(ridge, rim, horn, head, eyes, jaws, feel).at(0, lift, 0)


def legs(i, moving, n=8, stride=5.0):
    near, far = [], []
    for si, z in enumerate((5.4, -5.4)):
        for k, (xh, splay) in enumerate(((-7.6, -3.6), (-2.8, 0.0), (2.2, 3.4))):
            ph = 0.5 * ((k + si) % 2)
            p = (i / n + ph) % 1.0 if moving else 0.25
            if p < 0.5:
                u = p / 0.5
                fx, fy = xh + splay + stride / 2 - stride * u, 0.0
            else:
                u = (p - 0.5) / 0.5
                fx, fy = xh + splay - stride / 2 + stride * u, 2.6 * math.sin(math.pi * u)
            hip = (xh, 5.6, z * 0.9)
            foot = (fx, fy + 0.6, z * 1.55)
            knee = ((hip[0] + foot[0]) / 2 + splay * 0.25, max(hip[1], foot[1]) + 3.0, z * 1.6)
            s = Union(Capsule(hip, knee, 1.0).m("btl_leg"), RoundCone(knee, foot, 0.85, 0.45).m("btl_leg"))
            (near if z > 0 else far).append(s)
    return Union(*near), Union(*far)


def parts(i=0, moving=False, bob=0.0, spots=("btl_spot",), eye="btl_eye", tilt=0.0, push=0.0, breathe=0.0):
    def place(s):
        s = s.at(push, bob, 0)
        if tilt:
            s = s.at(15, 0, 0).rot(0, 0, tilt).at(-15, 0, 0)       # rock back about the rear feet
        return s.scale(1.1).rot(0, YAW, 0)
    near, far = legs(i, moving)
    return [Part(place(shell(spots, breathe)), name="shell"), Part(place(plate(eye)), name="plate"),
            Part(place(near), name="legs_n"), Part(place(far), name="legs_f", shade=-1)]


ANIMS = [
    ("move", 14, "loop", 8, "tripod walk"),
    ("idle", 8, "loop", 6, "breathing, glow spots pulse"),
    ("hurt", 14, "loop", 3, "rocks back"),
]


def frame(job):
    name, i = job
    if name == "move":
        bob = 0.4 * math.cos(4 * math.pi * i / 8)
        sp = ("btl_spot", "btl_spot_dim") if (i // 2) % 2 == 0 else ("btl_spot_dim", "btl_spot")
        return shoot(parts(i, True, bob=bob, spots=sp))
    if name == "idle":
        b = 0.5 - 0.5 * math.cos(2 * math.pi * i / 6)
        sp = ("btl_spot",) if i in (2, 3, 4) else ("btl_spot_dim",)
        return shoot(parts(0, False, breathe=0.5 * b, spots=sp))
    spr = shoot(parts(2, True, tilt=[8, 11, 4][i], push=-1.0, eye="btl_eye_hurt", spots=("btl_spot_dim",)))
    x, y = to_px(12, 17)
    if i < 2:
        spark(spr, x + 2 + i, y - 2 - i, 1, c=("white", "yellow:6", "orange:4"))
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("beetle", S64, A64, "shield beetle (episode 2 walker, box 30 x 22, armoured front, faces right)",
                      ANIMS, frames, notes=["anchor = bottom centre of the box (feet on the ground line)",
                                            "the amber plate covers the front third of the box (x > +5)",
                                            "glow: teal shell spots, amber eyes under the plate"])
