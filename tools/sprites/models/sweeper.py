"""sweeper -- episode 1 walker (box 26 x 20): a floor-cleaning robot gone haywire, one red eye, scuttling legs.

64 x 64 frames, anchor (32, 60) = bottom centre of the box. Model space: x forward (faces right), y up, z towards
the near side; the model is yawed towards the viewer so the eye on its front reads.
"""
import math

from bake import Box, Capsule, Ellipsoid, Intersect, Paint, Part, RoundCone, Sphere, Union, material
from models._e12_common import A64, S64, anim_jobs, bar_z, make_sheet, puff, shoot, spark, to_px

YAW = -30.0

material("swp_white", ["slate:4", "steel:5", "steel:6", "steel:7", "white"], bands=[-0.62, -0.28, 0.2, 0.72],
         line_lit="slate:2")
material("swp_yellow", ["orange:3", "yellow:3", "yellow:4", "yellow:5"], bands=[-0.4, 0.05, 0.7], line_lit="orange:2")
material("swp_stripe", ["slate:1", "slate:2", "slate:3"], bands=[-0.1, 0.5])
material("swp_dark", ["slate:1", "slate:2", "slate:3", "slate:4"], bands=[-0.4, 0.1, 0.7])
material("swp_leg", ["slate:2", "steel:3", "steel:4", "steel:6"], bands=[-0.3, 0.2, 0.7])
material("swp_bristle", ["teal:2", "teal:3", "teal:4", "teal:5"], bands=[-0.3, 0.2, 0.7], line="teal:1")
material("swp_bristle_dk", ["slate:1", "slate:2", "slate:3"], bands=[0.0, 0.6])
material("swp_eye", ["red:4", "red:5", "orange:6", "white"], style="emit", bands=[0.3, 0.75, 0.93], prio=3.0)
material("swp_eye_dim", ["crimson:2", "red:3", "red:4"], style="emit", bands=[0.4, 0.85], prio=3.0)
material("swp_eye_hurt", ["red:5", "rose:7", "white"], style="emit", bands=[0.3, 0.7], prio=3.0)
material("swp_light", ["teal:4", "cyan:5", "cyan:6"], style="emit", bands=[0.4, 0.8], prio=3.0)


def roller(spin):
    """The front brush roller along z: a core with bristle tufts turning by `spin` degrees."""
    core = bar_z(2.4, -6.2, 6.2, rr=0.8).m("swp_bristle_dk")
    tufts = []
    for k in range(6):
        a = math.radians(spin + 60.0 * k)
        tufts.append(Box(1.6, 0.95, 6.0, r=0.45).rot(0, 0, math.degrees(a)).at(2.5 * math.cos(a), 2.5 * math.sin(a), 0))
    tufts = Union(*tufts).m("swp_bristle")
    caps = Union(bar_z(1.7, 6.2, 7.4).m("swp_dark"), bar_z(1.7, -7.4, -6.2).m("swp_dark"))
    return Union(core, tufts, caps)


def leg_shapes(i, moving, n=8, stride=4.4):
    near, far = [], []
    for si, z in enumerate((5.6, -5.6)):
        for k, (xh, splay) in enumerate(((-6.4, -2.6), (0.0, 0.0), (6.0, 2.4))):
            ph = 0.5 * ((k + si) % 2)                     # tripod gait
            p = (i / n + ph) % 1.0 if moving else 0.25
            if p < 0.5:
                u = p / 0.5
                fx, fy = xh + splay + stride / 2 - stride * u, 0.0
            else:
                u = (p - 0.5) / 0.5
                fx, fy = xh + splay - stride / 2 + stride * u, 2.2 * math.sin(math.pi * u)
            hip = (xh * 0.9, 4.8, z * 0.95)
            foot = (fx, fy + 0.6, z * 1.42)
            knee = ((hip[0] + foot[0]) / 2 + splay * 0.2, max(hip[1], foot[1]) + 2.4, z * 1.5)
            s = Union(Capsule(hip, knee, 1.05).m("swp_leg"), RoundCone(knee, foot, 0.95, 0.6).m("swp_leg"),
                      Sphere(1.25).m("swp_yellow").at(*knee))
            (near if z > 0 else far).append(s)
    return Union(*near), Union(*far)


DOME_C = (-0.6, 8.6, 0.0)
DOME_R = (10.6, 8.2, 7.3)


def body(eye="swp_eye", blink=True, look=40.0):
    dome = Intersect(Ellipsoid(*DOME_R), Box(12, 8.5, 9).at(0, 8.5, 0)).m("swp_white").at(*DOME_C)
    chassis = Box(11.6, 2.4, 7.6, r=2.0).m("swp_yellow").at(0, 7.0, 0)
    stripes = Union(*[Box(1.5, 5.0, 10.0).rot(0, 0, 40).at(x, 7.0, 0) for x in range(-15, 16, 6)])
    chassis = Paint(chassis, stripes, "swp_stripe")
    belly = Box(10.4, 1.2, 6.4, r=0.9).m("swp_dark").at(0, 4.3, 0)
    a = math.radians(look)
    ex, ez = 9.0 * math.cos(a) - 0.6, 6.4 * math.sin(a)
    lens = Union(Sphere(3.1).m("swp_dark").at(ex - 1.0, 11.6, ez * 0.88), Sphere(2.8).m(eye).at(ex - 0.3, 11.6, ez))
    arms = Union(Capsule((8.0, 5.4, 6.8), (11.6, 4.0, 6.8), 0.85), Capsule((8.0, 5.4, -6.8), (11.6, 4.0, -6.8), 0.85)
                 ).m("swp_dark")
    mast = Capsule((-5.0, 14.6, 2.0), (-7.4, 19.0, 2.0), 0.5).m("swp_dark")
    tip = Sphere(1.15).m("swp_light" if blink else "swp_dark").at(-7.5, 19.4, 2.0)
    return Union(dome, chassis, belly, lens, arms, mast, tip)


def parts(i=0, moving=False, spin=0.0, bob=0.0, tilt=0.0, push=0.0, eye="swp_eye", blink=True, look=40.0):
    def place(s):
        s = s.at(push, bob, 0)
        if tilt:
            s = s.at(8, 0, 0).rot(0, 0, tilt).at(-8, 0, 0)
        return s.rot(0, YAW, 0)
    near, far = leg_shapes(i, moving)

    def place_legs(s):           # feet stay planted: no bob
        s = s.at(push, 0, 0)
        if tilt:
            s = s.at(8, 0, 0).rot(0, 0, tilt).at(-8, 0, 0)
        return s.rot(0, YAW, 0)
    return [Part(place(body(eye, blink, look)), name="body"),
            Part(place_legs(roller(spin).at(11.6, 4.0, 0)), name="roller"),
            Part(place_legs(near), name="legs_n"),
            Part(place_legs(far), name="legs_f", shade=-1)]


ANIMS = [
    ("move", 18, "loop", 8, "tripod scuttle, the brush roller spins"),
    ("idle", 8, "loop", 6, "the eye scans, antenna blinks"),
    ("hurt", 14, "loop", 4, "jolted back, eye flares, sparks"),
]


def frame(job):
    name, i = job
    if name == "move":
        bob = 0.45 * math.cos(4 * math.pi * i / 8)
        return shoot(parts(i, True, spin=-22.5 * i, bob=bob, blink=(i // 2) % 2 == 0))
    if name == "idle":
        look = [40, 52, 62, 52, 40, 26][i]
        return shoot(parts(0, False, spin=-6.0 * i, bob=0.3 * math.sin(2 * math.pi * i / 6), look=look,
                           blink=i < 3))
    # hurt
    tilt = [9.0, 13.0, 6.0, 2.0][i]
    spr = shoot(parts(2, True, spin=10.0 * i, tilt=tilt, push=-1.2 if i < 2 else -0.4,
                      eye="swp_eye_hurt" if i % 2 == 0 else "swp_eye_dim", blink=False))
    x, y = to_px(4, 17)
    if i == 0:
        spark(spr, x + 3, y - 1, 2)
    elif i == 1:
        spark(spr, x - 3, y - 3, 1)
        spark(spr, x + 5, y + 1, 1)
    elif i == 2:
        puff(spr, x - 1, y - 3, 1.6)
    else:
        puff(spr, x - 2, y - 6, 1.2)
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("sweeper", S64, A64, "floor sweeper robot (episode 1 walker, box 26 x 20, faces right)", ANIMS,
                      frames, notes=["anchor = bottom centre of the box (feet on the ground line)",
                                     "glow: the red eye, the antenna light"])
