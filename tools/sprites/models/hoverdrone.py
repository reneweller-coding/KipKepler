"""hoverdrone -- episode 1 flier (box 26 x 18): a round security drone with a ducted top rotor and a big lens eye.

64 x 64 frames, anchor (32, 50) = bottom centre of the box (the bottom of the body sphere); the rotor duct sticks
out above the box. The model is yawed towards the viewer and tilted a little so the rotor disc reads.
"""
import math

from bake import Box, Cone, Cylinder, Paint, Part, Sphere, Torus, Union, material
from models._e12_common import anim_jobs, bar_x, make_sheet, puff, shoot, spark, to_px

SIZE, ANCHOR, RANCHOR = (64, 64), (32, 50), (32, 49)
YAW, PITCH = -30.0, 20.0
BODY_Y = 8.6

material("hvd_white", ["slate:4", "steel:5", "steel:6", "steel:7", "white"], bands=[-0.6, -0.25, 0.2, 0.72],
         line_lit="slate:2")
material("hvd_steel", ["slate:2", "slate:3", "steel:3", "steel:4", "steel:6"], style="metal",
         bands=[-0.4, 0.0, 0.5], spec=0.93)
material("hvd_yellow", ["orange:3", "yellow:3", "yellow:4", "yellow:5"], bands=[-0.4, 0.05, 0.7], line_lit="orange:2")
material("hvd_dark", ["slate:1", "slate:2", "slate:3", "slate:4"], bands=[-0.4, 0.1, 0.7])
material("hvd_blade", ["slate:3", "steel:5", "steel:6", "steel:7"], bands=[-0.3, 0.2, 0.7])
material("hvd_lens", ["crimson:3", "red:4", "red:5", "orange:6", "white"], style="emit",
         bands=[0.25, 0.55, 0.82, 0.95], prio=3.0)
material("hvd_lens_hurt", ["red:5", "orange:6", "white"], style="emit", bands=[0.3, 0.7], prio=3.0)
material("hvd_lens_off", ["crimson:2", "crimson:3", "red:3"], style="emit", bands=[0.5, 0.9], prio=3.0)
material("hvd_light", ["teal:4", "cyan:5", "cyan:6"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("hvd_jet", ["teal:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.6, 0.85], prio=2.0,
         line="teal:2", line_lit="teal:2", inner=False)


def body(lens="hvd_lens", light=True, jet=1.0):
    shell = Sphere(8.0).m("hvd_white")
    shell = Paint(shell, Box(10, 4, 10).at(0, -5.6, 0), "hvd_steel")
    band = Torus(7.9, 1.0).m("hvd_yellow").at(0, -1.2, 0)
    a = math.radians(26)
    lx, lz = math.cos(a), math.sin(a)
    hood = Cylinder(3.9, 1.8, rr=0.9).m("hvd_dark").rot(0, 0, -90).rot(0, -26, 0).at(6.6 * lx, 0.4, 6.6 * lz)
    eye = Sphere(3.0).m(lens).at(7.9 * lx, 0.4, 7.9 * lz)
    side = Sphere(1.2).m("hvd_light" if light else "hvd_dark").at(-1.0, 1.6, 7.6)
    back = bar_x(1.9, -9.6, -6.0, -0.6, 0).m("hvd_dark")
    parts = [shell, band, hood, eye, side, back]
    if jet > 0:
        parts.append(Cone(1.5, 0.3, 1.1 * jet).rot(0, 0, 90).at(-10.4 - jet, -0.6, 0).m("hvd_jet"))
    probe = Union(Cylinder(0.5, 1.4).m("hvd_dark").at(0.6, -8.6, 0), Sphere(0.9).m("hvd_dark").at(0.6, -10.0, 0))
    parts.append(probe)
    return Union(*parts)


def rotor(spin):
    mast = Cylinder(1.4, 1.4, rr=0.5).m("hvd_dark").at(0, 8.6, 0)
    hub = Cylinder(1.8, 0.7, rr=0.4).m("hvd_steel").at(0, 10.0, 0)
    duct = Torus(11.0, 0.95).m("hvd_steel").at(0, 10.0, 0)
    blades = Union(*[Box(10.2, 0.3, 1.3, r=0.25).rot(10, spin + 90 * k, 0) for k in range(2)]).m("hvd_blade")
    return Union(mast, hub, duct, blades.at(0, 10.1, 0))


def parts(spin, bob=0.0, tilt=0.0, roll=0.0, lens="hvd_lens", light=True, jet=1.0):
    def place(s):
        s = s.rot(roll, 0, tilt).rot(0, YAW, 0).rot(PITCH, 0, 0)
        return s.at(0, BODY_Y + bob, 0)
    return [Part(place(body(lens, light, jet)), name="body"), Part(place(rotor(spin)), name="rotor")]


ANIMS = [
    ("fly", 16, "loop", 8, "hovering: rotor spins, body bobs and noses forward, rear jet flickers"),
    ("hurt", 14, "loop", 4, "knocked back, lens flickers, sparks"),
]


def frame(job):
    name, i = job
    if name == "fly":
        bob = 1.0 * math.sin(2 * math.pi * i / 8)
        tilt = -7 + 2.0 * math.cos(2 * math.pi * i / 8)
        return shoot(parts(spin=22.5 * i, bob=bob, tilt=tilt, light=i < 4, jet=[1.0, 1.4, 0.8, 1.2][i % 4]),
                     size=SIZE, ranchor=RANCHOR)
    k = [1.0, 0.7, 0.4, 0.15][i]
    spr = shoot(parts(spin=35.0 * i, bob=0.6 * k, tilt=16 * k, roll=-8 * k,
                      lens="hvd_lens_hurt" if i % 2 == 0 else "hvd_lens_off", light=False, jet=0.0),
                size=SIZE, ranchor=RANCHOR)
    x, y = to_px(0, BODY_Y + 6, RANCHOR)
    if i == 0:
        spark(spr, x + 5, y - 2, 2)
    elif i == 1:
        spark(spr, x - 4, y - 4, 1)
        spark(spr, x + 7, y + 2, 1)
    elif i == 2:
        puff(spr, x - 3, y - 4, 1.6)
    else:
        puff(spr, x - 4, y - 7, 1.2)
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("hoverdrone", SIZE, ANCHOR, "hover drone (episode 1 flier, box 26 x 18, faces right)", ANIMS,
                      frames, notes=["anchor = bottom centre of the box (the bottom of the body); the rotor duct "
                                     "sticks out about 5 px above the box",
                                     "glow: red lens, teal side light, rear jet"])
