"""rammer -- episode 1 charger (box 34 x 28): a squat bulldozer bot on treads with a striped ram plate.

64 x 64 frames, anchor (32, 60). move = trundling patrol; attack = revving / charging (one loop for both: plate
lowered and pushed out, exhaust blasting, sparks at the plate); hurt = dazed after hitting a wall (smoke, sparks,
stars over the cab).
"""
import math

import numpy as np

from bake import Box, Capsule, Cylinder, Paint, Part, Sphere, Union, material
from models._e12_common import A64, S64, anim_jobs, bar_z, make_sheet, puff, put, shoot, spark, to_px

YAW = -24.0

material("ram_yellow", ["orange:2", "orange:3", "yellow:3", "yellow:4", "yellow:5", "yellow:6"],
         bands=[-0.55, -0.25, 0.1, 0.45, 0.82], line_lit="orange:1")
material("ram_plate", ["orange:3", "yellow:3", "yellow:4", "yellow:5"], bands=[-0.62, -0.42, 0.3],
         line_lit="orange:1")
material("ram_dark", ["slate:1", "slate:2", "slate:3", "slate:4"], bands=[-0.4, 0.1, 0.7])
material("ram_tread", ["outline", "slate:1", "slate:2", "slate:3"], bands=[-0.3, 0.2, 0.7])
material("ram_cleat", ["slate:2", "slate:3", "steel:3", "steel:4"], bands=[-0.3, 0.2, 0.7])
material("ram_steel", ["slate:2", "steel:3", "steel:4", "steel:5", "steel:7"], style="metal", bands=[-0.35, 0.05, 0.5],
         spec=0.92)
material("ram_white", ["slate:4", "steel:5", "steel:6", "steel:7", "white"], bands=[-0.6, -0.25, 0.2, 0.72],
         line_lit="slate:2")
material("ram_stripe", ["slate:1", "slate:2", "slate:3"], bands=[-0.1, 0.5])
material("ram_eye", ["red:4", "red:5", "orange:6", "white"], style="emit", bands=[0.3, 0.7, 0.92], prio=3.0)
material("ram_eye_dim", ["crimson:2", "crimson:3", "red:3"], style="emit", bands=[0.4, 0.85], prio=3.0)
material("ram_lamp", ["teal:4", "cyan:5", "cyan:6"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("ram_lamp_red", ["red:4", "red:5", "orange:6"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("ram_flame", ["orange:3", "orange:4", "yellow:5", "yellow:7"], style="emit", bands=[0.25, 0.55, 0.85],
         line="orange:2", line_lit="orange:2", inner=False)


def tread(z, cleat):
    belt = Box(13.0, 3.9, 2.4, r=3.8).m("ram_tread").at(-1.0, 3.9, z)
    stripes = Union(*[Box(0.55, 6.0, 3.2).at(x + cleat, 3.9, z) for x in np.arange(-18.0, 18.0, 3.0)])
    belt = Paint(belt, stripes, "ram_cleat")
    return belt


def wheels(z, spin):
    out = []
    for x in (-9.6, -3.4, 2.8, 8.4):
        r = 2.4 if abs(x) > 9 else 2.1
        hub = bar_z(r, z, z + 0.9, x=x, y=3.9).m("ram_steel")
        spoke = Box(0.45, r - 0.2, 0.6).rot(0, 0, spin).at(x, 3.9, z + 0.9)
        out.append(Paint(hub, spoke, "ram_dark"))
        out.append(bar_z(0.75, z + 0.6, z + 1.1, x=x, y=3.9).m("ram_yellow"))
    return Union(*out)


def chassis(eye, lamp):
    body = Box(10.5, 4.4, 6.2, r=1.8).m("ram_yellow").at(-1.6, 11.0, 0)
    hood = Box(4.0, 2.6, 5.4, r=1.4).m("ram_yellow").at(6.4, 10.0, 0)
    skirt = Box(12.2, 1.3, 7.8, r=0.7).m("ram_dark").at(-1.0, 8.2, 0)
    cab = Box(5.0, 4.2, 5.2, r=2.0).m("ram_yellow").at(-1.6, 18.0, 0)
    visor = Box(1.2, 1.6, 4.6, r=0.7).m("ram_dark").at(3.0, 18.6, 0)
    eyes = Union(Sphere(1.3).m(eye).at(3.8, 18.6, 2.2), Sphere(1.3).m(eye).at(3.8, 18.6, -1.2))
    brow = Box(1.4, 0.75, 5.0, r=0.35).m("ram_dark").rot(0, 0, -18).at(3.2, 20.8, 0)
    roof = Box(5.2, 0.8, 5.4, r=0.5).m("ram_dark").at(-1.8, 22.4, 0)
    beacon = Union(Cylinder(1.1, 0.7, rr=0.3).m("ram_dark").at(-2.4, 23.6, 0),
                   Sphere(1.2).m(lamp).at(-2.4, 24.5, 0))
    pipe = Union(Cylinder(1.3, 4.6, rr=0.5).m("ram_steel").at(-9.2, 19.6, 3.0),
                 Cylinder(1.6, 0.6, rr=0.3).m("ram_dark").at(-9.2, 24.2, 3.0))
    return Union(body, hood, skirt, cab, visor, eyes, brow, roof, beacon, pipe)


def ram(push, drop):
    plate = Box(1.3, 7.6, 7.6, r=0.6).m("ram_steel")
    stripes = Union(*[Box(3.0, 0.62, 16.0).rot(42, 0, 0).at(0, y, 0) for y in np.arange(-15.0, 16.0, 4.6)])
    plate = Paint(plate, Box(2.0, 6.4, 6.4).at(1.0, 0, 0), "ram_plate")
    plate = Paint(plate, Intersect_box(stripes), "ram_stripe")
    lip = Box(1.6, 0.8, 7.8, r=0.4).m("ram_steel").at(0.6, -7.4, 0)
    plate = Union(plate, lip).rot(0, 0, -6 + drop * 6).at(16.0 + push, 9.0 - drop * 1.6, 0)
    arms = Union(Capsule((8.0, 12.0, 3.6), (15.4 + push, 11.0 - drop, 3.6), 0.9),
                 Capsule((8.0, 12.0, -3.6), (15.4 + push, 11.0 - drop, -3.6), 0.9),
                 Capsule((8.5, 6.6, 3.0), (15.4 + push, 5.4 - drop, 3.0), 0.8)).m("ram_dark")
    return Union(plate, arms)


def Intersect_box(stripes):
    """Stripes limited to the front face of the plate."""
    from bake import Intersect
    return Intersect(stripes, Box(2.0, 6.4, 6.4).at(1.0, 0, 0))


def parts(i, cleat=0.0, spin=0.0, bob=0.0, nose=0.0, push=0.0, drop=0.0, eye="ram_eye", lamp="ram_lamp",
          back=0.0):
    def place(s):
        s = s.at(back, bob, 0)
        if nose:                 # nose down pivots on the front of the treads, nose up on the back
            px = 13.0 if nose < 0 else -13.0
            s = s.at(-px, 0, 0).rot(0, 0, nose).at(px, 0, 0)
        return s.rot(0, YAW, 0)
    return [Part(place(chassis(eye, lamp)), name="chassis"),
            Part(place(ram(push, drop)), name="ram"),
            Part(place(Union(tread(5.6, cleat), wheels(8.0, spin))), name="tread_n"),
            Part(place(tread(-5.6, cleat)), name="tread_f", shade=-1)]


ANIMS = [
    ("move", 12, "loop", 8, "trundling: treads roll, engine shakes, exhaust puffs"),
    ("attack", 16, "loop", 8, "revving and charging: plate lowered and out, exhaust flames, sparks off the plate"),
    ("hurt", 10, "loop", 6, "dazed after a wall: tilted back, eyes flicker, smoke and stars over the cab"),
]


def exhaust_px(bob, nose, back=0.0):
    # pipe top in model space (-9.2, 24.8, 3.0), yawed
    a = math.radians(YAW)
    x = (-9.2 + back) * math.cos(a) + 3.0 * math.sin(a)
    return to_px(x, 24.8 + bob)


def frame(job):
    name, i = job
    if name == "move":
        bob = 0.45 if i % 2 else 0.0
        spr = shoot(parts(i, cleat=0.75 * i, spin=-45.0 * i, bob=bob))
        x, y = exhaust_px(bob, 0)
        k = i % 4
        puff(spr, x - k, y - 2 - 2 * k, [1.6, 2.0, 2.3, 2.0][k])
        if k >= 2:
            puff(spr, x - (k - 2), y - 1 - 2 * (k - 2), 1.6)
        return spr
    if name == "attack":
        bob = 0.5 * (i % 2)
        spr = shoot(parts(i, cleat=1.5 * i, spin=-90.0 * i, bob=bob, nose=-4.0, push=1.6, drop=1.0,
                          lamp="ram_lamp_red" if i % 2 == 0 else "ram_dark"))
        x, y = exhaust_px(bob, -4)
        fl = [3, 4, 2, 4, 3, 4, 2, 3][i]
        for k in range(fl):
            put(spr, x - 1 + (k % 2), y - 1 - k, ["yellow:7", "yellow:5", "orange:4", "orange:3"][min(k, 3)])
            put(spr, x + (k % 2), y - 1 - k, ["white", "yellow:6", "orange:5", "orange:3"][min(k, 3)])
        puff(spr, x - 3 - (i % 3), y - fl - 3, 2.3, shades=("grey:2", "grey:3", "grey:4"))
        px, py = to_px(16.5, 1.5)
        spark(spr, px + (i % 3) - 1, py - (i % 2), 1 + (i % 2))
        if i % 2 == 0:
            spark(spr, px - 4, py - 1, 1, c=("yellow:6", "orange:4", "orange:4"))
        return spr
    # hurt: dazed
    rock = [5, 6, 4, 3, 4, 5][i]
    spr = shoot(parts(i, cleat=0.0, nose=rock, eye="ram_eye" if i % 3 == 0 else "ram_eye_dim", lamp="ram_dark",
                      back=-0.5))
    cx, cy = to_px(-1.5, 28.5)
    for k in range(3):
        a = 2 * math.pi * (i / 6 + k / 3)
        sx, sy = cx + int(round(7 * math.cos(a))), cy + int(round(2.2 * math.sin(a)))
        put(spr, sx, sy, "yellow:6")
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            put(spr, sx + dx, sy + dy, "yellow:4" if k else "white")
    x, y = exhaust_px(0, rock)
    puff(spr, x - 1 - (i % 3), y - 3 - (i % 3), 2.0 + 0.3 * (i % 2))
    if i in (0, 3):
        spark(spr, cx + 6, cy + 6, 2)
    elif i in (1, 4):
        spark(spr, cx - 6, cy + 5, 1)
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("rammer", S64, A64, "rammer bulldozer bot (episode 1 charger, box 34 x 28, faces right)", ANIMS,
                      frames, notes=["anchor = bottom centre of the box (treads on the ground line)",
                                     "glow: red eyes, cab beacon (teal; red in attack), exhaust flames and sparks"])
