"""burrower -- episode 3 burrower (box 30 x 24): an ice worm, armoured segments with frost spikes, a round maw ringed
by four mandibles, small digging claws behind the head.

64 x 64 frames, anchor (32, 60). It is invisible underground; the engine plays move on the ground and attack while
it is in the air (the leap out of the ground, falling off ledges).
"""
import math

import numpy as np

from bake import (Capsule, Cone, Cylinder, Ellipsoid, Intersect, Box, Part, RoundCone, Sphere, Torus, Union, material,
                  prism, rot, trans)
from models._e34_common import TAU, Enemy, chip, flash, sparkle

E = Enemy("burrower", (64, 64), (32, 60), "ice worm (episode 3 burrower, faces right)", 3)

material("burrower_plate", ["blue:1", "blue:2", "blue:3", "ice:3", "ice:4", "ice:5", "ice:7"],
         bands=[-0.55, -0.25, 0.0, 0.3, 0.6, 0.88], line_lit="blue:1")
material("burrower_flesh", ["violet:0", "violet:1", "purple:2", "purple:3", "rose:4"], bands=[-0.4, -0.05, 0.35, 0.75])
material("burrower_spike", ["ice:5", "ice:6", "white"], bands=[-0.1, 0.5], line="blue:1", line_lit="blue:1",
         prio=1.5)
material("burrower_maw", ["outline", "crimson:1", "crimson:2", "crimson:3"], bands=[-0.2, 0.3, 0.7], prio=2.0)
material("burrower_tooth", ["ice:6", "white"], bands=[0.2], prio=2.5)
material("burrower_mandible", ["violet:0", "violet:1", "violet:2", "purple:3", "purple:4"],
         bands=[-0.4, 0.0, 0.4, 0.8])
material("burrower_eye", ["cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.75], prio=3.0)
material("burrower_claw", ["violet:1", "slate:2", "slate:4", "ice:5"], bands=[-0.3, 0.2, 0.7])

NSEG = 6
YAW = -24.0
HEAD_YAW = -34.0    # the head turns further to show the maw


def seg_radius(k):
    return 5.3 - 0.55 * k


def segment(k, c):
    """Segment k (0 = just behind the head) at centre c: soft body, armour plate on top, frost spike."""
    r = seg_radius(k)
    body = Ellipsoid(r * 0.85, r, r * 0.92).m("burrower_flesh").at(*c)
    plate = Intersect(Ellipsoid(r * 0.95, r * 1.08, r * 1.04).m("burrower_plate"),
                      Box(r * 2, r * 2, r * 2).at(0, r * 1.6, 0)).at(*c)
    rim = Torus(r * 0.98, 0.45).m("burrower_plate").rot(0, 0, 90).rot(0, 0, -8).at(c[0] - r * 0.55, c[1] + 0.2, c[2])
    if k % 2 == 0:
        spike = prism(5, 1.2, 0.5, 2.6 - 0.25 * k, 0.3).m("burrower_spike").rot(0, 0, 24).at(
            c[0] - 0.3, c[1] + r * 1.05 + 0.8, c[2])
        return Union(body, plate, rim, spike)
    return Union(body, plate, rim)


def head(c, gape=0.0, tilt=0.0, blink=False):
    """The head at c looking along +x; gape 0..1 opens the mandibles."""
    H = trans(*c) @ rot(0, HEAD_YAW, tilt)
    skull = Ellipsoid(5.6, 5.2, 5.2).m("burrower_flesh")
    crest = Intersect(Ellipsoid(6.0, 5.6, 5.6).m("burrower_plate"), Box(7, 6, 8).at(-2.4, 6.6, 0))
    horn = prism(5, 1.2, 0.6, 2.6, 0.4).m("burrower_spike").rot(0, 0, 50).at(-1.0, 5.2, 0)
    horn2 = prism(5, 0.9, 0.4, 1.8, 0.3).m("burrower_spike").rot(0, 0, 60).at(-3.4, 4.6, 0)
    lip = __import__("bake").Torus(3.0 + 0.9 * gape, 0.9).m("burrower_flesh").rot(0, 0, 90).at(4.9, -0.6, 0)
    maw = Cylinder(3.0 + 0.9 * gape, 0.7).m("burrower_maw").rot(0, 0, -90).at(4.9, -0.6, 0)
    teeth = []
    for a in range(0, 360, 45):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        rr = 2.6 + 0.8 * gape
        teeth.append(Cone(0.55, 0.05, 0.8).m("burrower_tooth").rot(0, 0, 90).rot(a, 0, 0)
                     .at(5.4, -0.6 + rr * ca, rr * sa))
    mand = []
    for a in (35, 145, 215, 325):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        spread = 18 + 32 * gape
        base = np.array([4.6, -0.6 + 3.4 * ca, 3.4 * sa])
        out = np.array([0.0, ca, sa])
        tip = base + np.array([3.4 - 1.2 * gape, 0, 0]) + out * (1.0 + 2.6 * gape)
        hook = tip + np.array([0.6, 0, 0]) - out * (1.3 - 0.6 * gape)
        mand.append(Union(RoundCone(base, tip, 0.95, 0.5).m("burrower_mandible"),
                          RoundCone(tip, hook, 0.5, 0.2).m("burrower_mandible")))
    eyes = []
    for z in (1, -1):
        for dx, dy, dz, r in ((2.4, 2.4, 3.6, 0.95), (0.8, 3.0, 4.4, 0.75), (-0.8, 3.0, 4.8, 0.6)):
            m = "burrower_flesh" if blink else "burrower_eye"
            eyes.append(Sphere(r).m(m).at(dx, dy, z * dz))
    return Union(skull, crest, horn, horn2, lip, maw, *teeth, *mand, *eyes).xform(H)


def claws(c, phase):
    out = []
    for z in (3.0, -3.0):
        for k, dph in ((0, 0.0), (1, 0.5)):
            a = math.sin(TAU * (phase + dph) + (0 if z > 0 else math.pi))
            base = np.array([c[0] - 4.2 * k, c[1] - 2.6, c[2] + z])
            tip = base + np.array([1.6 + 1.6 * a, -2.8 + 0.8 * max(0.0, a), 0.4 * np.sign(z)])
            out.append(Union(RoundCone(base, tip, 0.9, 0.5).m("burrower_claw"),
                             Cone(0.5, 0.05, 0.8).m("burrower_spike").rot(0, 0, 160).at(*(tip + [0.3, -0.4, 0]))))
    return Union(*out)


RISE = (8.4, 5.6, 1.6, 0.0, 0.0, 0.4, 1.4)     # the forebody rears up like a striking sandworm


def body_line(wave_t, amp, arch=0.0, lift=0.0, rear=1.0):
    """Centres of head + segments: reared forebody, a travelling hump (crawl), an arch (leap)."""
    pts = []
    x = 8.6
    for k in range(NSEG + 1):
        r = 5.2 if k == 0 else seg_radius(k - 1)
        hump = amp * max(0.0, math.sin(TAU * wave_t + 1.05 * k)) ** 1.5
        y = r + RISE[k] * rear + hump + arch * (1 - ((k - 2.6) / 3.6) ** 2) * 6 + lift
        pts.append((x, y, 0.0))
        x -= (4.0 - 0.2 * k) if k else 3.6
    return pts


def parts(pts, gape=0.0, tilt=0.0, blink=False, claw_ph=0.0, roll=0.0, root=(0.0, 0.0)):
    B = trans(root[0], root[1], 0) @ rot(0, YAW, roll)
    P = []
    for k in range(NSEG - 1, -1, -1):
        P.append(Part(segment(k, pts[k + 1]).xform(B), name=f"seg{k}"))
    P.append(Part(claws(pts[1], claw_ph).xform(B), name="claws"))
    P.append(Part(head(pts[0], gape, tilt, blink).xform(B), name="head"))
    return P


# ---------------------------------------------------------------------------------------------------------- animations

def move(i):
    """Crawl: a hump travels from the head down the body; the head bobs, mandibles work, claws dig."""
    n = 8
    t = i / n
    pts = body_line(-t, 2.0)
    pts[0] = (pts[0][0], pts[0][1] + 1.2 * math.sin(TAU * t + 1.0), 0.0)
    gape = 0.25 + 0.25 * math.sin(TAU * t)
    return E.draw(parts(pts, gape=gape, tilt=6 * math.sin(TAU * t + 1), claw_ph=t))


def idle(i):
    n = 8
    t = i / n
    pts = body_line(0.0, 0.0)
    pts[0] = (pts[0][0], pts[0][1] + 1.0 + 1.0 * math.sin(TAU * t), 0.0)
    gape = [0.1, 0.5, 0.1, 0.1, 0.6, 0.15, 0.1, 0.1][i]
    return E.draw(parts(pts, gape=gape, tilt=10 + 6 * math.sin(TAU * t), blink=i == 6))


def attack(i):
    """In the air: arched, maw wide open, mandibles snapping, ice chunks breaking off."""
    n = 6
    t = i / n
    pts = body_line(t, 0.6, arch=1.0 + 0.15 * math.sin(TAU * t), lift=1.0, rear=0.5)
    # head and tail curl: the head points forward-up, the tail trails down
    pts = [(x, y + (2.6 if k == 0 else 0.0) - max(0, k - 4) * 1.6, z) for k, (x, y, z) in enumerate(pts)]
    gape = 0.75 + 0.25 * math.sin(TAU * t * 2)
    spr = E.draw(parts(pts, gape=gape, tilt=18, claw_ph=t * 2))
    for k, (x, y) in enumerate(((16, 52), (22, 56), (44, 55), (40, 50), (13, 46))):
        yy = y - 2 * ((i + k) % 3)
        chip(spr, x + (k % 2) * ((i % 2) * 2 - 1), yy, k)
    return spr


def hurt(i):
    pts = body_line(0.0, 0.0)
    pts = [(x - [1.6, 0.9, 0.3][i], y + (1.2 if k == 0 else 0.0), z) for k, (x, y, z) in enumerate(pts)]
    spr = E.draw(parts(pts, gape=0.8 - 0.3 * i, tilt=24 - 8 * i, blink=True))
    if i == 0:
        flash(spr)
    if i < 2:
        for k, (x, y) in enumerate(((28, 40), (44, 42), (36, 36))):
            chip(spr, x - 2 * i, y - 3 * i, k)
    return spr


E.anim("move", 12, "loop", 8, move, "crawl: a hump runs down the body")
E.anim("attack", 12, "loop", 6, attack, "in the air (bursting out, falling): arched, maw open")
E.anim("idle", 8, "loop", 8, idle, "head raised, mandibles clicking (not used by the engine yet)")
E.anim("hurt", 12, "once", 3, hurt, "")
E.note("glow: eyes")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
