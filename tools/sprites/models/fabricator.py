"""fabricator -- episode 1 spawner (box 44 x 44): a fabrication block that builds and beams out hoverdrones.

96 x 96 frames, anchor (48, 92) = bottom centre of the box. The big iris hatch faces the viewer (glowing teal from
inside); a welding arm works on the roof, a warning beacon turns, a launch chute points right.
idle = working (arm welds, sparks, steam, lights chase); attack = the iris opens, the core flares, closes again;
hurt = sparks and flicker.
"""
import math

import numpy as np

from bake import Box, Capsule, Cylinder, Ellipsoid, Extrude, Paint, Part, Sphere, Subtract, Torus, Union, material
from models._e12_common import A96, R96, S96, anim_jobs, bar_x, bar_z, make_sheet, puff, put, shoot, spark, to_px

YAW = -28.0
FACE_Z = 11.0
HATCH = (1.5, 20.0)        # hatch centre (x, y) on the front face
HATCH_R = 8.4

material("fab_white", ["slate:3", "slate:4", "steel:5", "steel:6", "steel:7", "white"],
         bands=[-0.6, -0.3, 0.05, 0.4, 0.8], line_lit="slate:2")
material("fab_steel", ["slate:1", "slate:2", "slate:3", "steel:3", "steel:4"], bands=[-0.5, -0.1, 0.35, 0.75])
material("fab_metal", ["slate:2", "steel:3", "steel:4", "steel:5", "steel:7"], style="metal", bands=[-0.35, 0.05, 0.5],
         spec=0.92)
material("fab_yellow", ["orange:3", "yellow:3", "yellow:4", "yellow:5"], bands=[-0.4, 0.05, 0.7], line_lit="orange:2")
material("fab_stripe", ["slate:1", "slate:2", "slate:3"], bands=[-0.1, 0.5])
material("fab_blade", ["slate:1", "slate:2", "steel:3", "steel:4", "steel:5"], style="metal", bands=[-0.3, 0.1, 0.6],
         spec=0.93)
material("fab_core", ["teal:2", "teal:3", "teal:4", "cyan:4"], style="emit", bands=[0.45, 0.75, 0.92], prio=1.5)
material("fab_core_hi", ["teal:3", "teal:4", "cyan:5", "cyan:6"], style="emit", bands=[0.45, 0.75, 0.92], prio=1.5)
material("fab_core_flare", ["teal:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.45, 0.75, 0.92], prio=1.5)
material("fab_lamp", ["teal:4", "cyan:5", "cyan:6"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("fab_lamp_off", ["slate:2", "slate:3"], bands=[0.4])
material("fab_beacon", ["orange:4", "yellow:5", "yellow:7"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("fab_beacon_dim", ["orange:2", "orange:3"], style="emit", bands=[0.5], prio=3.0)
material("fab_red", ["red:4", "red:5", "orange:6"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("fab_weld", ["cyan:6", "white"], style="emit", bands=[0.5], prio=3.0)


def block():
    base = Box(21.5, 2.8, 12.6, r=1.0).m("fab_steel").at(0, 2.8, 0)
    band = Box(20.6, 1.6, 12.0, r=0.6).m("fab_yellow").at(0, 6.6, 0)
    stripes = Union(*[Box(1.0, 4.0, 14.0).rot(0, 0, 40).at(x, 6.6, 0) for x in np.arange(-26.0, 27.0, 4.6)])
    band = Paint(band, stripes, "fab_stripe")
    body = Box(18.6, 14.8, FACE_Z, r=2.6).m("fab_white").at(0, 22.6, 0)
    recess = bar_z(HATCH_R + 0.8, FACE_Z - 2.0, FACE_Z + 2.0, x=HATCH[0], y=HATCH[1])
    body = Subtract(body, recess.m("fab_steel"))
    roof = Box(17.0, 1.4, 10.2, r=0.8).m("fab_steel").at(0, 38.0, 0)
    vents = Union(*[Box(0.5, 4.2, 0.6, r=0.25).m("fab_steel").at(-14.6 + 1.6 * k, 31.0, FACE_Z + 0.2)
                    for k in range(4)])
    panel = Box(2.2, 4.4, 0.6, r=0.6).m("fab_steel").at(-14.4, 19.0, FACE_Z + 0.2)
    frame_ = Subtract(Box(HATCH_R + 2.6, HATCH_R + 2.6, 0.7, r=2.2).at(HATCH[0], HATCH[1], FACE_Z + 0.2),
                      bar_z(HATCH_R + 0.8, FACE_Z - 2.0, FACE_Z + 2.0, x=HATCH[0], y=HATCH[1])).m("fab_steel")
    rim = Torus(HATCH_R + 0.6, 0.9).m("fab_yellow").rot(90, 0, 0).at(HATCH[0], HATCH[1], FACE_Z + 0.6)
    bolts = Union(*[Sphere(0.75).m("fab_yellow").at(HATCH[0] + (HATCH_R + 1.4) * math.cos(math.radians(a)) * 1.25,
                                                    HATCH[1] + (HATCH_R + 1.4) * math.sin(math.radians(a)) * 1.25,
                                                    FACE_Z + 0.8)
                    for a in range(45, 360, 90)])
    pipes = Union(Capsule((-19.6, 8.0, 6.0), (-19.6, 33.0, 6.0), 1.1), Capsule((-19.6, 33.0, 6.0), (-14.0, 37.6, 6.0), 1.1),
                  Capsule((-20.0, 8.0, 2.2), (-20.0, 28.0, 2.2), 0.9)).m("fab_metal")
    chute = Union(bar_x(3.2, 17.0, 22.6, 28.0, 0.0).m("fab_steel"), Torus(3.2, 0.7).m("fab_yellow").rot(0, 0, 90)
                  .at(22.2, 28.0, 0))
    stack = Union(Cylinder(1.8, 2.6, rr=0.5).m("fab_metal").at(-10.0, 41.4, -3.0),
                  Cylinder(2.1, 0.5, rr=0.3).m("fab_steel").at(-10.0, 44.0, -3.0))
    side = Union(*[Box(0.6, 9.0, 1.2, r=0.3).m("fab_yellow").rot(0, 0, 0).at(18.8, 22.0, -6.0 + 3.0 * k)
                   for k in range(0)])
    return Union(base, band, body, roof, vents, panel, frame_, rim, bolts, pipes, chute, stack)


def iris(open_):
    """Six blades on the hatch; open_ 0 = closed, 1 = retracted to the rim."""
    R = HATCH_R
    rin = R * (0.24 + 0.76 * open_)
    blades = []
    tw = 38.0
    for k in range(6):
        a0, a1 = math.radians(60 * k + 4), math.radians(60 * k + 56)
        b0, b1 = a0 + math.radians(tw), a1 + math.radians(tw)
        poly = [(rin * math.cos(b0), rin * math.sin(b0)), (R * math.cos(a0), R * math.sin(a0)),
                (R * math.cos((a0 + a1) / 2) * 1.02, R * math.sin((a0 + a1) / 2) * 1.02), (R * math.cos(a1), R * math.sin(a1)),
                (rin * math.cos(b1), rin * math.sin(b1))]
        if rin > R * 0.9:
            continue
        blades.append(Extrude(poly, 0.5, r=0.15).m("fab_blade").at(HATCH[0], HATCH[1], FACE_Z - 0.6 + 0.12 * k))
    return blades


def core(mat):
    """A shallow glowing dome in the recess: its emissive bands make concentric rings."""
    return Ellipsoid(HATCH_R + 0.4, HATCH_R + 0.4, 3.2).m(mat).at(HATCH[0], HATCH[1], FACE_Z - 4.2)


def arm(a1, a2, weld):
    """Roof welding arm: turret, two segments, nozzle. a1/a2 in degrees from up, positive = towards +x."""
    base = Union(Cylinder(3.0, 1.0, rr=0.4).m("fab_steel").at(6.0, 40.2, 3.0),
                 Sphere(2.1).m("fab_yellow").at(6.0, 41.6, 3.0))
    s = np.array([6.0, 41.6, 3.0])
    e = s + 9.0 * np.array([math.sin(math.radians(a1)), math.cos(math.radians(a1)), 0])
    t = e + 7.5 * np.array([math.sin(math.radians(a1 + a2)), math.cos(math.radians(a1 + a2)), 0])
    seg = Union(Capsule(tuple(s), tuple(e), 1.35).m("fab_white"), Sphere(1.6).m("fab_steel").at(*e),
                Capsule(tuple(e), tuple(t), 1.1).m("fab_yellow"))
    d = (t - e) / 7.5
    tip = Union(Sphere(1.3).m("fab_steel").at(*t), Sphere(0.85).m("fab_weld" if weld else "fab_steel").at(*(t + d * 1.4)))
    return Union(base, seg, tip), t + d * 2.0


def beacon(phase):
    post = Cylinder(1.3, 1.0, rr=0.4).m("fab_steel").at(13.5, 40.2, -2.0)
    lamp = Sphere(1.6).m("fab_beacon" if phase else "fab_beacon_dim").at(13.5, 42.0, -2.0)
    return Union(post, lamp)


def lamps(states):
    return Union(*[Box(1.0, 0.9, 0.5, r=0.3).m("fab_lamp" if on else "fab_lamp_off").at(-14.4, 21.6 - 2.6 * k, FACE_Z + 0.8)
                   for k, on in enumerate(states)])


def scene(open_=0.0, core_mat="fab_core", a1=30.0, a2=90.0, weld=False, phase=True, lamp_states=(1, 0, 1),
          shake=0.0):
    def place(s):
        return s.at(shake, 0, 0).rot(0, YAW, 0)
    armshape, tip = arm(a1, a2, weld)
    parts = [Part(place(block()), name="block"), Part(place(core(core_mat)), name="core", inner=False),
             Part(place(armshape), name="arm"), Part(place(beacon(phase)), name="beacon"),
             Part(place(lamps(lamp_states)), name="lamps")]
    for k, b in enumerate(iris(open_)):
        parts.append(Part(place(b), name=f"blade{k}"))
    a = math.radians(YAW)
    tx = tip[0] * math.cos(a) + tip[2] * math.sin(a) + shake
    return parts, to_px(tx, tip[1], R96)


ARM = [(30, 100, True), (36, 94, True), (44, 86, False), (34, 74, False), (16, 70, False), (8, 84, True),
       (14, 96, True), (24, 104, False)]


def hatch_px():
    a = math.radians(YAW)
    x = HATCH[0] * math.cos(a) + FACE_Z * math.sin(a)
    return to_px(x, HATCH[1], R96)


ANIMS = [
    ("idle", 8, "loop", 8, "working: the roof arm welds (sparks), beacon turns, lamps chase, steam, hatch glows"),
    ("attack", 12, "loop", 8, "beaming a drone out: iris opens (0-2), core flares (3-5), closes (6-7)"),
    ("hurt", 14, "loop", 3, "sparks, flicker"),
]

OPEN = [0.0, 0.45, 0.85, 1.0, 1.0, 1.0, 0.6, 0.2]
CORE = ["fab_core", "fab_core_hi", "fab_core_hi", "fab_core_flare", "fab_core_flare", "fab_core_hi", "fab_core_hi",
        "fab_core"]


def frame(job):
    name, i = job
    if name == "idle":
        a1, a2, weld = ARM[i]
        lamps_ = tuple(1 if (k + i) % 3 != 0 else 0 for k in range(3))
        ps, tip = scene(0.0, "fab_core_hi" if i % 4 in (1, 2) else "fab_core", a1, a2, weld, i % 2 == 0, lamps_)
        spr = shoot(ps, size=S96, ranchor=R96)
        if weld:
            spark(spr, tip[0], tip[1], 2 if i % 2 else 1, c=("white", "cyan:6", "cyan:4"))
            put(spr, tip[0] + 2 + (i % 2), tip[1] + 2, "yellow:6")
            put(spr, tip[0] - 2, tip[1] + 3 + (i % 3), "orange:5")
        sx, sy = to_px((-10.0 * math.cos(math.radians(YAW)) - 3.0 * math.sin(math.radians(YAW))), 45.0, R96)
        k = i % 4
        puff(spr, sx - k // 2, sy - 2 - 2 * k, [1.6, 2.0, 2.4, 2.0][k], shades=("grey:4", "grey:5", "grey:6"))
        return spr
    if name == "attack":
        ps, tip = scene(OPEN[i], CORE[i], 20, 60, False, True, (1, 1, 1), shake=0.4 if i in (3, 4) else 0.0)
        spr = shoot(ps, size=S96, ranchor=R96)
        hx, hy = hatch_px()
        if 3 <= i <= 5:
            for k in range(8):
                ang = math.radians(45 * k + 22 * i)
                d = HATCH_R + 3 + (i - 3) * 2
                put(spr, int(hx + d * math.cos(ang) * 0.9), int(hy + d * math.sin(ang)), "cyan:6" if k % 2 else "white")
            spark(spr, hx, hy, 3, c=("white", "cyan:6", "cyan:4"))
        return spr
    ps, tip = scene(0.0, "fab_core" if i != 1 else "fab_core_hi", 50, 40, False, i == 1, (0, 1, 0), shake=-0.6)
    spr = shoot(ps, size=S96, ranchor=R96)
    for (x, y, sz) in [((34, 54, 2), (62, 62, 1)), ((44, 50, 1), (60, 74, 2)), ((38, 66, 1),)][i]:
        spark(spr, x, y, sz)
    hx, hy = hatch_px()
    if i == 2:
        puff(spr, hx - 6, 48, 2.0)
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("fabricator", S96, A96, "drone fabricator (episode 1 spawner of hoverdrones, box 44 x 44)", ANIMS,
                      frames, notes=["anchor = bottom centre of the box (the plinth on the ground line)",
                                     "the hatch faces the viewer; the launch chute points right",
                                     "glow: hatch core, panel lamps, beacon, welding arc"])
