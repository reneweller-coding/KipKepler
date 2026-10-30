"""turret -- episode 1 turret (box 26 x 26): an armoured gun dome on a bolted plinth, twin barrels, red sensor eye.

64 x 64 frames, anchor (32, 60) = bottom centre of the box = the floor line under the plinth. Drawn standing on its
base; the engine rotates it by 180 degrees about the anchor when it hangs from a ceiling. The barrels point right at
the box centre height (the engine spawns turret shots at the box centre + 14 px towards the hero).
"""
import math

from bake import Box, Cylinder, Intersect, Paint, Part, Sphere, Torus, Union, material
from models._e12_common import A64, S64, anim_jobs, bar_x, make_sheet, point_of, puff, ring_x, shoot, spark, to_px

YAW = -24.0
GUN_Y = 13.0

material("trt_white", ["slate:4", "steel:5", "steel:6", "steel:7", "white"], bands=[-0.6, -0.25, 0.2, 0.72],
         line_lit="slate:2")
material("trt_base", ["slate:1", "slate:2", "slate:3", "steel:3", "steel:4"], bands=[-0.5, -0.1, 0.35, 0.75])
material("trt_yellow", ["orange:3", "yellow:3", "yellow:4", "yellow:5"], bands=[-0.4, 0.05, 0.7], line_lit="orange:2")
material("trt_stripe", ["slate:1", "slate:2", "slate:3"], bands=[-0.1, 0.5])
material("trt_gun", ["slate:1", "slate:2", "steel:3", "steel:5", "steel:7"], style="metal", bands=[-0.3, 0.1, 0.6],
         spec=0.92)
material("trt_eye", ["red:4", "red:5", "orange:6", "white"], style="emit", bands=[0.3, 0.7, 0.92], prio=3.0)
material("trt_eye_dim", ["crimson:2", "red:3", "red:4"], style="emit", bands=[0.4, 0.85], prio=3.0)
material("trt_tip", ["crimson:3", "red:3", "red:4"], style="emit", bands=[0.4, 0.8], prio=2.5)
material("trt_tip_hot", ["red:5", "orange:6", "yellow:7"], style="emit", bands=[0.35, 0.8], prio=2.5)
material("trt_lamp", ["teal:4", "cyan:5", "cyan:6"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("trt_lamp_red", ["red:4", "red:5", "orange:6"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("trt_lamp_off", ["slate:2", "slate:3"], bands=[0.4])


def base(lamps):
    plinth = Box(12.6, 2.0, 8.0, r=0.9).m("trt_base").at(0, 2.0, 0)
    band = Box(11.4, 1.7, 7.2, r=0.7).m("trt_yellow").at(0, 5.6, 0)
    stripes = Union(*[Box(0.9, 4.0, 10.0).rot(0, 0, 40).at(x, 5.6, 0) for x in range(-16, 17, 5)])
    band = Paint(band, stripes, "trt_stripe")
    feet = Union(*[Box(2.0, 1.0, 8.6, r=0.5).m("trt_base").at(x, 1.0, 0) for x in (-11.0, 11.0)])
    bolts = Union(*[Sphere(0.75).m("trt_gun").at(x, 2.2, 8.0) for x in (-9.8, 9.8)])
    lights = Union(*[Box(0.9, 0.7, 0.5, r=0.3).m(m).at(-3.4 + 3.4 * k, 2.0, 8.0) for k, m in enumerate(lamps)])
    column = Cylinder(4.6, 1.6, rr=0.6).m("trt_base").at(0, 8.4, 0)
    return Union(plinth, band, feet, bolts, lights, column)


HEAD_C = (-1.2, 15.2, 0.0)


def head(eye, tip, spin=0.0, recoil=0.0):
    ball = Intersect(Sphere(8.6), Box(10, 8, 10).at(0, 2.2, 0)).m("trt_white").at(*HEAD_C)
    skirt = Cylinder(7.4, 1.0, rr=0.6).m("trt_base").at(HEAD_C[0], 10.0, 0)
    ring = Torus(7.6, 0.75).m("trt_yellow").at(HEAD_C[0], 10.9, 0)
    mantlet = Box(2.6, 3.4, 4.4, r=1.6).m("trt_base").at(5.6, GUN_Y, 0)
    cam = Box(2.8, 1.8, 2.2, r=0.8).m("trt_base").at(1.2, 23.6, 0.6)
    cam_post = Cylinder(0.8, 1.2).m("trt_base").at(0.4, 22.0, 0.6)
    lens = Sphere(1.9).m(eye).at(3.4, 23.6, 1.2)
    fin = Box(3.2, 0.8, 0.8, r=0.35).m("trt_yellow").rot(0, 0, 14).at(-6.0, 21.4, 0)
    parts = [ball, skirt, ring, mantlet, cam, cam_post, lens, fin]
    x1 = 15.4 - recoil
    for k in range(2):
        a = math.radians(spin + 180 * k + 90)
        y, z = GUN_Y + 1.45 * math.sin(a), 1.45 * math.cos(a)
        parts.append(bar_x(1.05, 6.0, x1 - 1.2, y, z).m("trt_gun"))
        parts.append(bar_x(1.15, x1 - 1.5, x1, y, z).m(tip))
    parts.append(ring_x(2.2, 0.7, 9.4 - recoil * 0.5, GUN_Y, 0).m("trt_base"))
    return Union(*parts)


def parts(lamps=("trt_lamp", "trt_lamp", "trt_lamp"), eye="trt_eye", tip="trt_tip", spin=0.0, recoil=0.0,
          tilt=0.0):
    h = head(eye, tip, spin, recoil)
    if tilt:
        h = h.at(0, -10.0, 0).rot(0, 0, tilt).at(0, 10.0, 0)
    return [Part(base(lamps).rot(0, YAW, 0), name="base"), Part(h.rot(0, YAW, 0), name="head")]


ANIMS = [
    ("idle", 8, "loop", 6, "sensor eye pulses, base lamps chase"),
    ("attack", 12, "loop", 6, "alarm: lamps red, barrels spin, tips glow (not synced to the shots)"),
    ("hurt", 14, "loop", 3, "sparks, eye flickers"),
]

LAMP_ON, LAMP_RED, LAMP_OFF = "trt_lamp", "trt_lamp_red", "trt_lamp_off"


def frame(job):
    name, i = job
    if name == "idle":
        lamps = tuple(LAMP_ON if k == i % 3 else LAMP_OFF for k in range(3))
        eye = "trt_eye" if i not in (3, 4) else "trt_eye_dim"
        return shoot(parts(lamps, eye=eye, tilt=[0, 1, 2, 2, 1, 0][i]))
    if name == "attack":
        lamps = tuple(LAMP_RED if (k + i) % 2 == 0 else LAMP_OFF for k in range(3))
        spr = shoot(parts(lamps, tip="trt_tip_hot" if i % 2 == 0 else "trt_tip", spin=60.0 * i,
                          recoil=0.6 if i % 3 == 0 else 0.0))
        if i % 3 == 0:
            x, y = to_px(15.5, GUN_Y)
            spark(spr, x + 1, y, 1, c=("white", "orange:6", "red:4"))
        return spr
    spr = shoot(parts((LAMP_OFF, LAMP_RED, LAMP_OFF), eye="trt_eye" if i != 1 else "trt_eye_dim",
                      tilt=[-8, -4, -1][i]))
    x, y = to_px(-1, 22)
    if i == 0:
        spark(spr, x + 4, y - 1, 2)
    elif i == 1:
        spark(spr, x - 3, y - 3, 1)
        spark(spr, x + 6, y, 1)
    else:
        puff(spr, x, y - 3, 1.5)
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    dx, dy = point_of(15.5, GUN_Y)
    return make_sheet("turret", S64, A64, "gun turret (episode 1 turret, box 26 x 26, faces right)", ANIMS, frames,
                      points=[("muzzle", dx, dy, "barrel tips (the box centre height)")],
                      notes=["anchor = bottom centre of the box: the floor line under the plinth (upright)",
                             "on a ceiling the engine draws it rotated by 180 degrees about the anchor",
                             "glow: red sensor eye, barrel tips, base lamps"])
