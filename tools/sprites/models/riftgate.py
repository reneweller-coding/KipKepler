"""riftgate -- episode 4 spawner (box 48 x 64): a Gloam portal, two leaning blade pylons and a pointed lintel of black-
violet alloy on a stepped plinth, magenta neon running up the inner edges, a swirling rift of violet, magenta and
cyan inside. It beams in troopers.

96 x 96 frames, anchor (48, 92). idle = the rift turning, lights chasing; attack = the rift flares (a trooper is
beamed in beside it); hurt = flicker.
"""
import math

import numpy as np

from bake import Box, Chamfer, Extrude, Part, Union, fbm, material, rot, trans
from models._e34_common import TAU, Enemy, flash, spark, sparkle

E = Enemy("riftgate", (96, 96), (48, 92), "Gloam rift gate (episode 4 spawner)", 4)

material("riftgate_light", ["magenta:5", "magenta:6", "white"], style="emit", bands=[0.4, 0.8], prio=2.5)

INNER = 12.6          # rift half width at the waist
RIFT_C = (0.0, 30.0)  # rift centre (world)


def plinth():
    step1 = Extrude([(-25.0, 0.0), (25.0, 0.0), (23.0, 3.0), (-23.0, 3.0)], 7.0, r=0.6).m("e34_alloy")
    step2 = Extrude([(-20.0, 3.0), (20.0, 3.0), (18.4, 5.6), (-18.4, 5.6)], 6.0, r=0.5).m("e34_plate")
    lights = Union(*[Box(1.0, 0.4, 0.3).m("e34_magenta_dim").at(-15 + 6 * k, 1.4, 7.0) for k in range(6)])
    return Union(step1, step2, lights)


def pylon(side, chase):
    """A blade pylon leaning in; side -1 = left, +1 = right. chase = which neon segment is lit."""
    s = side
    outer = [(s * 23.0, 5.0), (s * 15.0, 5.0), (s * 14.6, 30.0), (s * 12.0, 50.0), (s * 6.0, 60.0),
             (s * 9.0, 61.0), (s * 19.6, 50.0), (s * 22.0, 30.0)]
    if s < 0:
        outer = outer[::-1]
    blade = Extrude(outer, 4.2, r=0.7).m("e34_alloy")
    rib = Extrude([(s * 22.6, 10.0), (s * 24.8, 14.0), (s * 23.6, 42.0), (s * 21.4, 40.0)][::(1 if s > 0 else -1)],
                  3.0, r=0.4).m("e34_plate")
    spike = Extrude([(s * 19.6, 50.0), (s * 26.0, 66.0), (s * 15.0, 54.0)][::(1 if s > 0 else -1)], 1.6, r=0.3) \
        .m("e34_plate")
    neon = []
    for k in range(6):
        y0 = 8.0 + 8.6 * k
        x0 = s * (15.2 - 0.07 * max(0.0, y0 - 30) * 1.6)
        m = "riftgate_light" if (k - chase) % 6 in (0, 1) else "e34_magenta_dim"
        neon.append(Box(0.6, 3.4, 0.6).m(m).rot(0, 0, s * (4 if y0 > 30 else 0)).at(x0 - s * 0.9, y0 + 2.0, 3.8))
    return Union(blade, rib, spike, *neon)


def lintel(glow):
    arch = Extrude([(-9.0, 61.0), (-6.0, 60.0), (0.0, 64.6), (6.0, 60.0), (9.0, 61.0), (0.0, 70.0)], 4.6, r=0.6) \
        .m("e34_alloy")
    eye = Extrude([(-2.2, 64.4), (0.0, 63.0), (2.2, 64.4), (0.0, 67.0)], 4.9, r=0.2) \
        .m("e34_magenta" if glow else "e34_magenta_dim")
    return Union(arch, eye)


def frame_parts(chase=0, glow=True, tilt=0.0):
    B = rot(0, -14, tilt)
    return [Part(plinth().xform(B), name="plinth"), Part(pylon(-1, chase).xform(B), name="pylon_l", shade=-1),
            Part(pylon(1, chase).xform(B), name="pylon_r"), Part(lintel(glow).xform(B), name="lintel")]


def rift(c, t, power=0.0, flick=1.0):
    """The rift into a canvas: a swirling oval of stepped bands (dark core, magenta and cyan arms)."""
    X, Y = c.X - RIFT_C[0], c.Y - RIFT_C[1]
    ry = 25.0 + 2.0 * power
    rx = INNER * 0.88 + 2.4 * power
    r = np.hypot(X / rx, Y / ry)
    a = np.arctan2(Y / ry, X / rx)
    swirl = a * 2 + 5.0 * np.log(np.maximum(r, 0.05)) - TAU * t * 2
    arms = 0.5 + 0.5 * np.sin(swirl)
    n = fbm(X * 0.9, Y * 0.9 + t * 20, 0.25, 21, 2)
    inside = r < 1.0
    v = (arms * 0.7 + n * 0.5) * (0.4 + 0.6 * r) + power * 0.25
    edge = r > 0.86
    c.fill(inside, "violet:1", line=False)
    c.fill(inside & (v > 0.38), "purple:2", glow=True, line=False)
    c.fill(inside & (v > 0.55), "magenta:3", glow=True, line=False)
    c.fill(inside & (v > 0.7), "magenta:5", glow=True, line=False)
    c.fill(inside & (v > 0.84) & (r > 0.35), "cyan:5", glow=True, line=False)
    c.fill(inside & (v > 0.95) & (r > 0.35), "white", glow=True, line=False)
    c.fill(inside & edge & (arms > 0.35 * flick), "magenta:6", glow=True, line=False)
    core = r < 0.22 + 0.1 * power
    c.fill(core, "violet:0" if power < 0.5 else "magenta:6", glow=power >= 0.5, line=False)
    if power > 0.6:
        c.fill(r < 0.12, "white", glow=True, line=False)


def draw(t, chase, power=0.0, glow=True, flick=1.0, tilt=0.0):
    c = E.canvas()
    rift(c, t, power, flick)
    return E.draw(frame_parts(chase, glow, tilt), canvas=c, under=True)


def arc(spr, x0, y0, x1, y1, seed, c1="white", c2="magenta:6"):
    rng = np.random.default_rng(seed)
    n = max(3, int(math.hypot(x1 - x0, y1 - y0) / 3))
    pts = [(x0 + (x1 - x0) * k / n + (rng.uniform(-2, 2) if 0 < k < n else 0),
            y0 + (y1 - y0) * k / n + (rng.uniform(-2, 2) if 0 < k < n else 0)) for k in range(n + 1)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        steps = int(max(abs(bx - ax), abs(by - ay))) + 1
        for s in range(steps + 1):
            x = int(round(ax + (bx - ax) * s / steps))
            y = int(round(ay + (by - ay) * s / steps))
            spr.put(x, y, c1, glow=True)
            if spr.get(x + 1, y) < 0:
                spr.put(x + 1, y, c2, glow=True)


# ---------------------------------------------------------------------------------------------------------- animations

def idle(i):
    n = 8
    return draw(i / n, i % 6, power=0.0)


def attack(i):
    """The rift flares open, arcs crackle to the pylons, the core goes white (a trooper beams in beside it)."""
    n = 8
    power = [0.4, 0.8, 1.0, 1.0, 1.0, 0.9, 0.7, 0.4][i]
    spr = draw(i / n * 2, (i * 2) % 6, power=power)
    cx, cy = E.px(*RIFT_C)
    if 1 <= i <= 6:
        for k in range(2):
            side = 1 if (i + k) % 2 else -1
            arc(spr, cx + side * 3, cy - 8 + 12 * k, cx + side * 15, cy - 14 + 18 * k + (i % 3) * 3, i * 7 + k)
        sparkle(spr, cx + [-6, 4, -2, 6, -4, 2][i - 1], cy - 20 + 3 * i, 2, c1="white", c2="magenta:5")
    return spr


def hurt(i):
    spr = draw(0.3 * i, 3, power=0.2, glow=i == 1, flick=0.3, tilt=[-1.5, 1.0, -0.4][i])
    if i == 0:
        flash(spr)
    cx, cy = E.px(*RIFT_C)
    if i < 2:
        spark(spr, cx - 14 + 6 * i, cy + 10 - 8 * i, 2, hot="magenta:6", cold="violet:5")
        spark(spr, cx + 12, cy - 12, 1, hot="magenta:6", cold="violet:5")
    return spr


E.anim("idle", 8, "loop", 8, idle, "the rift turns, lights chase up the pylons")
E.anim("attack", 12, "loop", 8, attack, "beaming in: the rift flares, arcs crackle")
E.anim("hurt", 12, "once", 3, hurt, "")
E.note("glow: the rift, the neon edges, the lintel eye, plinth lights")
E.note("the engine sets attack only for the tick it spawns: hold it ~0.6 s to show the flare")

jobs, frame, sheets = E.jobs, E.frame, E.sheets
