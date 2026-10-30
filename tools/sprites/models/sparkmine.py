"""sparkmine -- episode 1 floater (box 18 x 18): a spiked floating mine crackling with sparks, a blinking red core.

64 x 64 frames, anchor (32, 44) = bottom centre of the box; the body centre sits 9 px above it, spike tips and arcs
stick out a little. It explodes on touch (the engine draws the explosion), so only fly and hurt.
"""
import math

import numpy as np

from bake import Cone, Cylinder, Paint, Part, Box, Sphere, Torus, Union, material, rot
from models._e12_common import anim_jobs, bolt, make_sheet, put, shoot, spark, to_px

SIZE, ANCHOR, RANCHOR = (64, 64), (32, 44), (32, 43)
CY = 9.0
R_BODY = 5.6

material("smn_shell", ["slate:1", "slate:2", "slate:3", "steel:3", "steel:5"], style="metal",
         bands=[-0.4, 0.0, 0.45], spec=0.9)
material("smn_yellow", ["orange:3", "yellow:3", "yellow:4", "yellow:5"], bands=[-0.4, 0.05, 0.7], line_lit="orange:2")
material("smn_stripe", ["slate:1", "slate:2", "slate:2"], bands=[0.0, 0.6])
material("smn_spike", ["slate:2", "steel:3", "steel:5", "steel:6", "white"], style="metal", bands=[-0.3, 0.15, 0.6],
         spec=0.9)
material("smn_tip", ["yellow:5", "yellow:6", "white"], style="emit", bands=[0.4, 0.8], prio=2.5)
material("smn_core", ["red:4", "red:5", "orange:6", "white"], style="emit", bands=[0.3, 0.65, 0.9], prio=3.0)
material("smn_core_dim", ["crimson:2", "crimson:3", "red:3"], style="emit", bands=[0.4, 0.85], prio=3.0)
material("smn_core_hurt", ["orange:6", "yellow:7", "white"], style="emit", bands=[0.3, 0.7], prio=3.0)

DIRS = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]
for sx in (1, -1):
    for sy in (1, -1):
        DIRS.append((sx * 0.7071, sy * 0.7071, 0))
for sx in (1, -1):
    for sy in (1, -1):
        DIRS.append((sx * 0.55, sy * 0.55, -0.63))
SPIKE_L = 3.4


def spike(d, hot):
    dx, dy, dz = d
    n = math.sqrt(dx * dx + dy * dy + dz * dz)
    dx, dy, dz = dx / n, dy / n, dz / n
    tilt = math.degrees(math.acos(max(-1.0, min(1.0, dy))))
    az = math.degrees(math.atan2(dz, dx))
    c = Union(Cone(1.45, 0.35, SPIKE_L / 2).m("smn_spike").at(0, R_BODY + SPIKE_L / 2 - 0.4, 0),
              Sphere(0.55).m("smn_tip" if hot else "smn_spike").at(0, R_BODY + SPIKE_L - 0.4, 0))
    return c.rot(0, 0, -tilt).rot(0, -az, 0)


def mine(ang, core, hot_set):
    shell = Sphere(R_BODY).m("smn_shell")
    band = Torus(R_BODY - 0.2, 1.45).m("smn_yellow")
    stripes = Union(*[Box(0.55, 3.0, 3.0).rot(0, -a, 0).at(R_BODY * math.cos(math.radians(a)), 0,
                                                       R_BODY * math.sin(math.radians(a)))
                      for a in range(20, 380, 60)])
    band = Paint(band, stripes, "smn_stripe")
    spikes = [spike(d, k in hot_set) for k, d in enumerate(DIRS)]
    body = Union(shell, band, *spikes).rot(0, 0, ang).rot(14, -20, 0)
    window = Union(Cylinder(2.5, 0.8, rr=0.4).m("smn_shell").rot(90, 0, 0).at(0, 0, R_BODY - 0.3),
                   Sphere(2.05).m(core).at(0, 0, R_BODY + 0.15))
    return body, window


def tips(ang, bob):
    """Screen positions (frame pixels) of the spike tips facing the viewer."""
    M = rot(14, -20, 0) @ rot(0, 0, ang)
    out = []
    for d in DIRS:
        v = np.array(d, float)
        v /= np.linalg.norm(v)
        p = M[:3, :3] @ (v * (R_BODY + SPIKE_L - 0.4))
        if p[2] > -1.0:
            out.append(to_px(p[0], p[1] + CY + bob, RANCHOR))
    return out


ANIMS = [
    ("fly", 14, "loop", 8, "drifting: slow spin, arcs crackle between the spikes, core blinks"),
    ("hurt", 14, "loop", 3, "core flares, sparks burst"),
]


def frame(job):
    name, i = job
    if name == "fly":
        ang = -11.25 * i
        bob = 0.8 * math.sin(2 * math.pi * i / 8)
        core = "smn_core" if i % 4 < 2 else "smn_core_dim"
        hot = {(i * 3) % len(DIRS), (i * 5 + 2) % len(DIRS)}
    else:
        ang, bob, core, hot = -8.0 * i, 0.0, "smn_core_hurt" if i != 1 else "smn_core", set(range(len(DIRS)))
    body, window = mine(ang, core, hot)
    spr = shoot([Part(body.at(0, CY + bob, 0), name="mine"), Part(window.at(0, CY + bob, 0), name="core")],
                size=SIZE, ranchor=RANCHOR)
    tp = tips(ang, bob)
    rng = np.random.default_rng(100 + i + (50 if name == "hurt" else 0))
    if name == "fly":
        drawn = 0
        for k in range(12):
            a, b = rng.choice(len(tp), 2, replace=False)
            (x0, y0), (x1, y1) = tp[a], tp[b]
            dd = abs(x0 - x1) + abs(y0 - y1)
            if dd < 6 or dd > 14:
                continue
            bolt(spr, x0, y0, x1, y1, seed=7 * i + k, segs=3, jitter=2.6, colour="white" if drawn == 0 else "cyan:6",
                 edge="cyan:4")
            drawn += 1
            if drawn == 2:
                break
        for k in range(2):
            x, y = tp[rng.integers(len(tp))]
            dx, dy = rng.integers(-2, 3), rng.integers(-2, 3)
            put(spr, x + dx, y + dy, "cyan:6" if k else "white")
        if i % 3 == 0:
            x, y = tp[rng.integers(len(tp))]
            spark(spr, x, y, 1, c=("white", "cyan:6", "blue:4"))
    else:
        cx, cy = to_px(0, CY, RANCHOR)
        for k in range(4 + 2 * i):
            a = rng.uniform(0, 2 * math.pi)
            d = 7 + 2.5 * i + rng.uniform(0, 3)
            spark(spr, int(cx + d * math.cos(a)), int(cy + d * math.sin(a)), 1 if k % 2 else 2,
                  c=("white", "yellow:6", "orange:4"))
    return spr


def jobs():
    return anim_jobs(ANIMS)


def sheets(frames):
    return make_sheet("sparkmine", SIZE, ANCHOR, "spark mine (episode 1 floater, box 18 x 18, faces right)", ANIMS,
                      frames, notes=["anchor = bottom centre of the box; the body centre is 9 px above it",
                                     "glow: red core, spike tips, the electric arcs and sparks"])
