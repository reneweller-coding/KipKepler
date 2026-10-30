"""shardling -- episode 3 hopper (box 24 x 26): a small living crystal, a violet geode body with a crown of glowing
cyan shards, big eyes and stubby crystal feet.

64 x 64 frames, anchor (32, 60). idle = on the ground (bouncing in place, shards glinting), attack = in the air (a
forward somersault, feet tucked).
"""
import math

import numpy as np

from bake import Ellipsoid, Extrude, Part, Sphere, Union, material, prism, rot, scaling, trans
from models._e34_common import TAU, Enemy, chip, flash, sparkle

E = Enemy("shardling", (64, 64), (32, 60), "shardling, a living crystal (episode 3 hopper, faces right)", 3)

material("shardling_rock", ["violet:0", "violet:1", "violet:2", "purple:3", "violet:4", "purple:5"],
         bands=[-0.55, -0.25, 0.05, 0.4, 0.78], line_lit="violet:0")
material("shardling_facet", ["violet:1", "violet:3", "purple:4", "violet:5"], bands=[-0.3, 0.2, 0.65])
material("shardling_shard", ["blue:2", "blue:3", "cyan:3", "cyan:4", "cyan:5", "cyan:6", "white"],
         bands=[-0.5, -0.2, 0.05, 0.3, 0.6, 0.85], glow=True, line="blue:1", line_lit="blue:1")
material("shardling_eye", ["cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.75], prio=3.0)
material("shardling_socket", ["violet:0", "outline"], bands=[0.3], prio=2.0)
material("shardling_foot", ["violet:1", "violet:3", "purple:4", "purple:5"], bands=[-0.3, 0.2, 0.7])

SHARDS = [  # (azimuth deg about y, tilt from vertical deg, length scale, radius scale)
    (-170, 14, 1.25, 1.1), (150, 36, 1.0, 0.9), (-130, 40, 0.95, 0.85), (175, 58, 0.75, 0.75),
    (110, 52, 0.7, 0.7), (-100, 60, 0.6, 0.7), (40, 30, 0.62, 0.65), (-40, 26, 0.7, 0.7),
]


def shards(flare=0.0, spin=0.0):
    out = []
    for az, tilt, ls, rs in SHARDS:
        t = tilt + 14 * flare
        p = prism(6, 2.1 * rs, 2.6 * ls, 4.2 * ls, 0.8, twist=spin + az).m("shardling_shard")
        # stand it on the body's surface: up along the tilted direction
        out.append(p.at(0, 2.6 * ls + 4.6, 0).rot(0, 0, -t).rot(0, az, 0))
    return Union(*out)


def body(blink=False, squint=0.0, look=0.0):
    rock = Ellipsoid(8.4, 7.4, 7.0).m("shardling_rock")
    facets = Union(*[prism(5, 2.2, 0.6, 0.8, 0.8, twist=a).m("shardling_facet").rot(70, a, 0).at(
        6.2 * math.cos(math.radians(a)) * 0.9, -2.4, 6.2 * math.sin(math.radians(a)) * 0.9 * -1)
        for a in (-60, -20, 20)])
    face = []
    for z in (1.9, -1.9):
        sock = Ellipsoid(2.0, 2.4 if not blink else 0.6, 1.5).m("shardling_socket").at(6.6, 0.6, z * 1.15)
        eye = Ellipsoid(1.5, (1.9 - 0.8 * squint) if not blink else 0.35, 1.2).m("shardling_eye")             .at(7.4 + look, 0.7, z * 1.15)
        face += [sock, eye]
    brow = Extrude([(-2.6, 0), (2.6, 0), (2.2, 1.2), (-2.2, 0.8)], 0.9, r=0.3).m("shardling_facet") \
        .rot(0, 90, -14).at(6.4, 3.4, 0)
    return Union(rock, facets, brow, *face)


def feet(spread=0.0, tuck=0.0):
    out = []
    for z, dx in ((3.2, 2.8), (-3.2, -2.4)):
        f = prism(5, 2.0, 1.4, 0.8, 1.6).m("shardling_foot")
        y = -7.2 + 3.0 * tuck
        out.append(f.rot(0, 0, (14 if dx > 0 else -10) - 30 * tuck).at(dx + spread * (1 if dx > 0 else -1), y, z))
    return Union(*out)


def parts(root=(0.0, 0.0), roll=0.0, flare=0.0, spin=0.0, blink=False, squint=0.0, tuck=0.0, spread=0.0,
          look=0.0, yaw=-28.0):
    C = trans(root[0], root[1] + 9.9 * 1.14, 0) @ rot(0, 0, roll) @ rot(0, yaw, 0) @ scaling(1.14)
    return [Part(shards(flare, spin).xform(C), name="shards"), Part(body(blink, squint, look).xform(C), name="body"),
            Part(feet(spread, tuck).xform(C), name="feet")]


# ---------------------------------------------------------------------------------------------------------- animations

def idle(i):
    """Bouncing in place on its little feet: squash on the ground, stretch up; shards glint in turn."""
    n = 8
    ph = TAU * i / n
    sq = 1 + 0.08 * math.cos(ph)
    st = 1 / sq
    lift = max(0.0, -math.cos(ph)) * 1.2
    spr = E.draw(parts(root=(0, lift), flare=0.25 * math.cos(ph), blink=i == 6, look=0.3 * math.sin(ph)),
                 squash=(sq, st), pivot=(0, 0))
    glints = {1: (27, 24, 1), 2: (26, 25, 2), 5: (38, 31, 1), 6: (37, 30, 1)}
    if i in glints:
        sparkle(spr, *glints[i])
    return spr


def attack(i):
    """In the air: a forward somersault with the feet tucked, shards flared."""
    n = 8
    roll = -360.0 * i / n
    spr = E.draw(parts(root=(0, 4.0), roll=roll, flare=0.6, tuck=1.0, squint=0.6, spin=12 * i),
                 squash=(0.96, 1.04), pivot=(0, 16))
    if i % 2 == 0:
        sparkle(spr, 18 + (i // 2) % 2 * 2, 40 + (i // 2) % 2 * 3, 1)
    return spr


def hurt(i):
    keys = [(-2.0, 18, 0.9), (-1.2, 10, 0.4), (-0.4, 4, 0.1)]
    rx, roll, fl = keys[i]
    spr = E.draw(parts(root=(rx, 0), roll=roll, flare=fl, blink=True), squash=(1.08, 0.93), pivot=(0, 0))
    if i == 0:
        flash(spr)
    if i < 2:
        for k, (x, y) in enumerate(((22, 30), (42, 33), (34, 25))):
            chip(spr, x - 2 * i, y - 3 * i, k, colours=("cyan:6", "cyan:4", "blue:2"))
    return spr


E.anim("idle", 10, "loop", 8, idle, "on the ground: bouncing, shard glints")
E.anim("attack", 16, "loop", 8, attack, "in the air: forward somersault")
E.anim("hurt", 12, "once", 3, hurt, "")
E.note("glow: eyes and the crystal shards")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
