"""brineeel -- episode 2 lurker (box 30 x 22): a long dark-green eel with a pale belly, glowing cyan spots along its
flank, a fin crest and a wide jaw. It waits under the surface of a pool and leaps at whoever passes above; the
engine shows it only while it is out of the water.

64 x 64 frames, anchor (32, 60) (the bottom centre of its box). attack: the leap -- rising nose up (0-1), the arc
over the top (2-3), diving back (4-5); move: the same body wriggling (the engine's fallback); hurt: a jolt.
Model space: x forward (faces right), y up, z towards the viewer. The body is a chain of round cones along a curve.
"""
import math

from bake import Ellipsoid, Paint, Part, RoundCone, Sphere, Union, Box, Cone, material
from models._e12_common import A64, S64, anim_jobs, make_sheet, shoot, spark

YAW = -16.0

material("eel_skin", ["teal:0", "teal:1", "teal:2", "green:2", "teal:3", "green:3"],
         bands=[-0.55, -0.25, 0.1, 0.45, 0.8], line="teal:0", line_lit="teal:0")
material("eel_belly", ["tan:3", "tan:4", "tan:5", "tan:6"], bands=[-0.3, 0.2, 0.65], line="brown:1")
material("eel_fin", ["violet:1", "purple:3", "purple:4", "magenta:5"], bands=[-0.3, 0.2, 0.7], line="violet:0")
material("eel_spot", ["teal:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.6, 0.88], prio=3.0)
material("eel_eye", ["orange:4", "yellow:5", "yellow:6", "white"], style="emit", bands=[0.3, 0.6, 0.88], prio=3.2)
material("eel_mouth", ["crimson:1", "crimson:2", "red:3"], bands=[0.0, 0.6], prio=2.6)
material("eel_tooth", ["ice:6", "white"], bands=[0.4], prio=3.0)

N = 12          # segments
LENGTH = 36.0   # body length (target pixels)


def curve(bend, tilt, lift):
    """Points along the body from the tail (0) to the head (N): heading tilt (degrees at the middle), bending bend
    (degrees over the whole length; + curls the head up), centred at x 0, height lift."""
    pts, a = [], math.radians(tilt - bend / 2)
    step = LENGTH / N
    x, y = 0.0, 0.0
    pts.append((x, y))
    for k in range(N):
        a += math.radians(bend) / N
        x += step * math.cos(a)
        y += step * math.sin(a)
        pts.append((x, y))
    mx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
    my = min(p[1] for p in pts)
    return [(px - mx, py - my + lift) for px, py in pts]


def radius(k):
    t = k / N
    return 0.9 + 3.0 * math.sin(math.pi * min(1.0, 0.25 + 0.75 * t)) ** 0.8


def body(bend, tilt, lift, jaw=10.0, wiggle=0.0):
    pts = curve(bend, tilt, lift)
    segs = []
    for k in range(N):
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        w = wiggle * math.sin(k * 0.9) * (1 - k / N)
        segs.append(RoundCone((x0, y0 + w, 0), (x1, y1 + w, 0), radius(k), radius(k + 1)))
    skin = Union(*segs).m("eel_skin")
    # The pale belly along the lower side, the glowing spots along the flank.
    hx, hy = pts[-1]
    px, py = pts[-2]
    ang = math.degrees(math.atan2(hy - py, hx - px))
    for k in range(2, N - 1, 2):
        x, y = pts[k]
        skin = Paint(skin, Sphere(radius(k) * 0.8).at(x, y - radius(k) * 0.75, 0), "eel_belly")
    spots = [Sphere(0.75).m("eel_spot").at(pts[k][0], pts[k][1] + 0.4, radius(k) * 0.95) for k in range(3, N - 1, 2)]
    # The crest along the back.
    fins = []
    for k in range(2, N - 2, 2):
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        a = math.atan2(y1 - y0, x1 - x0)
        nx, ny = -math.sin(a), math.cos(a)
        r = radius(k)
        fins.append(Cone(1.0, 0.1, 2.0 + 0.6 * math.sin(k)).m("eel_fin").rot(0, 0, math.degrees(a) - 90 + 25)
                    .at(x0 + nx * (r + 0.6), y0 + ny * (r + 0.6), 0))
    # The head: an ellipsoid along the last heading, an open jaw, an eye, teeth.
    head = Ellipsoid(5.4, 3.7, 3.6).m("eel_skin").rot(0, 0, ang).at(hx + 1.2 * math.cos(math.radians(ang)),
                                                                   hy + 1.2 * math.sin(math.radians(ang)), 0)
    jawa = math.radians(ang - jaw)
    lower = Ellipsoid(4.2, 1.5, 2.9).m("eel_belly").rot(0, 0, ang - jaw).at(hx + 1.8 * math.cos(jawa),
                                                                          hy + 1.8 * math.sin(jawa) - 1.4, 0)
    mouth = Box(2.6, 0.5, 2.8).m("eel_mouth").rot(0, 0, ang - jaw / 2).at(hx + 3.0 * math.cos(math.radians(ang)),
                                                                        hy + 3.0 * math.sin(math.radians(ang)) - 0.6, 0)
    ea = math.radians(ang)
    eye = Sphere(1.35).m("eel_eye").at(hx + 1.6 * math.cos(ea) - 0.6 * math.sin(ea), hy + 1.6 * math.sin(ea) + 1.2, 2.6)
    teeth = [Cone(0.35, 0.05, 0.9).m("eel_tooth").rot(0, 0, 180 + ang).at(
        hx + (2.4 + 0.9 * j) * math.cos(ea), hy + (2.4 + 0.9 * j) * math.sin(ea) - 0.3, 1.4) for j in range(3)]
    return Union(skin, *spots, *fins, head, lower, mouth, eye, *teeth)


def parts(bend, tilt, lift, jaw=10.0, wiggle=0.0):
    return [Part(body(bend, tilt, lift, jaw, wiggle).scale(1.0).rot(0, YAW, 0), name="eel")]


LEAP = [  # bend, tilt, lift, jaw
    (40, 55, 3.0, 22), (30, 35, 5.0, 26), (-10, 8, 7.0, 18), (-40, -12, 6.0, 12), (-50, -40, 4.0, 8), (-30, -60, 2.0, 6),
]

ANIMS = [
    ("attack", 12, "loop", 6, "the leap: rising nose up (0-1), the arc over the top (2-3), diving back (4-5)"),
    ("move", 10, "loop", 4, "wriggling near the top of the leap (the engine's fallback)"),
    ("hurt", 14, "loop", 3, "jolted, jaw wide"),
]


def frame(job):
    name, i = job
    if name == "attack":
        b, t, l, j = LEAP[i]
        return shoot(parts(b, t, l, j))
    if name == "move":
        return shoot(parts(-10 + 14 * math.sin(i * math.pi / 2), 0, 6.0, 14, wiggle=1.2 * math.cos(i * math.pi / 2)))
    spr = shoot(parts([30, 10, -20][i], 20, 5.0, 30))
    if i == 0:
        spark(spr, 40, 38, 2)
    elif i == 1:
        spark(spr, 26, 42, 1)
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("brineeel", S64, A64, "brine eel (episode 2 lurker, box 30 x 22, faces right)", ANIMS, frames,
                      notes=["anchor = bottom centre of the box; drawn only while it is out of its pool",
                             "glow: cyan flank spots, amber eye"])
