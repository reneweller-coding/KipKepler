"""springbot -- episode 1 hopper (box 24 x 28): a box-headed robot on a big chrome coil spring and a heavy foot pad.

64 x 64 frames, anchor (32, 60). idle = on the ground, spring compressed and bouncing (winding up for the next hop);
attack = in the air, spring stretched and wobbling, arms up. hurt = jolted, sparks.
"""
import math

from bake import Box, Capsule, Cylinder, Part, Sphere, Torus, Union, material
from models._e12_common import A64, S64, anim_jobs, make_sheet, puff, shoot, spark, to_px

YAW = -26.0

material("spb_white", ["slate:4", "steel:5", "steel:6", "steel:7", "white"], bands=[-0.6, -0.25, 0.2, 0.72],
         line_lit="slate:2")
material("spb_yellow", ["orange:3", "yellow:3", "yellow:4", "yellow:5"], bands=[-0.4, 0.05, 0.7], line_lit="orange:2")
material("spb_dark", ["slate:1", "slate:2", "slate:3", "slate:4"], bands=[-0.4, 0.1, 0.7])
material("spb_screen", ["outline", "slate:1", "slate:2", "blue:2"], bands=[-0.3, 0.2, 0.7])
material("spb_chrome", ["slate:2", "steel:3", "steel:5", "steel:6", "white"], style="metal", bands=[-0.4, 0.0, 0.45],
         spec=0.88)
material("spb_eye", ["red:4", "red:5", "orange:6", "white"], style="emit", bands=[0.3, 0.7, 0.92], prio=3.0)
material("spb_eye_shut", ["crimson:3", "red:3"], style="emit", bands=[0.6], prio=3.0)
material("spb_light", ["teal:4", "cyan:5", "cyan:6"], style="emit", bands=[0.4, 0.8], prio=3.0)

FOOT_H = 2.2
SCALE = 1.15


def spring(length, wob=0.0):
    """Coil rings, each its own part so dark inner lines separate them."""
    rings = []
    n = 5
    for k in range(n):
        y = FOOT_H + 0.9 + k * (length - 1.8) / (n - 1)
        rings.append(Torus(3.2 - 0.12 * k, 0.72).m("spb_chrome").rot(16 if k % 2 == 0 else -16, 0, 0)
                     .at(wob * k / n, y, 0))
    return rings


def foot():
    pad = Cylinder(5.4, 1.1, rr=0.6).m("spb_dark").at(0, 1.1, 0)
    rim = Torus(5.3, 0.65).m("spb_yellow").at(0, 1.6, 0)
    boss = Cylinder(2.2, 0.6, rr=0.3).m("spb_chrome").at(0, 2.5, 0)
    return Union(pad, rim, boss)


def head(eye="spb_eye", arm=0.0, light=True):
    """Head-body, origin at its bottom centre."""
    collar = Cylinder(2.6, 0.9, rr=0.4).m("spb_dark").at(0, 0.6, 0)
    box = Box(5.6, 4.9, 5.0, r=2.4).m("spb_white").at(0, 5.8, 0)
    band = Box(5.75, 0.8, 5.15, r=0.6).m("spb_yellow").at(0, 2.6, 0)
    screen = Box(1.2, 2.6, 3.9, r=1.0).m("spb_screen").at(4.9, 6.6, 0)
    eyes = Union(Sphere(1.15).m(eye).at(5.9, 6.8, 1.8), Sphere(1.15).m(eye).at(5.9, 6.8, -1.4))
    ears = Union(Cylinder(1.8, 0.55, rr=0.3).m("spb_dark").rot(90, 0, 0).at(-0.8, 6.4, 5.1),
                 Cylinder(1.8, 0.55, rr=0.3).m("spb_dark").rot(90, 0, 0).at(-0.8, 6.4, -5.1),
                 Cylinder(0.9, 0.5, rr=0.3).m("spb_yellow").rot(90, 0, 0).at(-0.8, 6.4, 5.6))
    mast = Capsule((-1.4, 10.4, 0), (-2.6, 13.4, 0), 0.45).m("spb_dark")
    bulb = Sphere(1.2).m("spb_light" if light else "spb_dark").at(-2.7, 13.8, 0)
    a = math.radians(arm)
    arms = []
    for z in (5.8, -5.8):
        s = (1.2, 4.6, z)
        h = (1.2 + 6.0 * math.sin(a), 4.6 - 6.0 * math.cos(a), z * 1.25)
        arms.append(Union(Capsule(s, h, 0.75).m("spb_dark"), Sphere(1.25).m("spb_yellow").at(*h)))
    return Union(collar, box, band, screen, eyes, ears, mast, bulb), arms


def parts(length, lift=0.0, tilt=0.0, wob=0.0, eye="spb_eye", arm=20.0, light=True, squash=0.0):
    hb, arms = head(eye, arm, light)
    top = FOOT_H + length

    def place(s, pivot_y=0.0):
        if tilt:
            s = s.at(0, -pivot_y, 0).rot(0, 0, tilt).at(0, pivot_y, 0)
        return s.at(0, lift, 0).scale(SCALE).rot(0, YAW, 0)
    return [Part(place(hb.at(wob, top, 0), FOOT_H), name="head"),
            Part(place(foot()), name="foot")] + [Part(place(r, FOOT_H), name=f"ring{k}")
                                                 for k, r in enumerate(spring(length, wob))]


ANIMS = [
    ("idle", 10, "loop", 8, "on the ground: spring compressed, bouncing, winding up"),
    ("attack", 12, "loop", 8, "in the air: spring stretched and wobbling, arms up"),
    ("hurt", 14, "loop", 3, "jolted, sparks"),
]

IDLE_LEN = [6.0, 5.2, 4.6, 4.4, 4.8, 5.6, 6.4, 6.6]
AIR_LEN = [12.5, 13.5, 12.0, 10.8, 11.6, 13.0, 13.6, 12.6]


def frame(job):
    name, i = job
    if name == "idle":
        L = IDLE_LEN[i]
        blink = i == 5
        return shoot(parts(L, wob=0.4 * math.sin(2 * math.pi * i / 8), arm=28 + 10 * (6.6 - L),
                           eye="spb_eye_shut" if blink else "spb_eye", light=i < 4))
    if name == "attack":
        L = AIR_LEN[i]
        spr = shoot(parts(L, lift=2.0, wob=0.7 * math.sin(2 * math.pi * i / 8), tilt=4 * math.sin(2 * math.pi * i / 8),
                          arm=158 + 12 * math.sin(4 * math.pi * i / 8), light=i % 2 == 0))
        return spr
    spr = shoot(parts(6.0, tilt=[14, 9, 4][i], eye="spb_eye_shut" if i == 1 else "spb_eye", arm=60, light=False))
    x, y = to_px(-1, 23)
    if i == 0:
        spark(spr, x + 5, y - 2, 2)
    elif i == 1:
        spark(spr, x - 3, y - 4, 1)
        spark(spr, x + 7, y, 1)
    else:
        puff(spr, x, y - 4, 1.6)
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("springbot", S64, A64, "spring bot (episode 1 hopper, box 24 x 28, faces right)", ANIMS, frames,
                      notes=["anchor = bottom centre of the box (the foot pad on the ground line)",
                             "attack frames are lifted 2 px (the spring hangs below the body in the air)",
                             "glow: red eyes, antenna bulb"])
