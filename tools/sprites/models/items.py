"""Pickups -- the items sheet (32 x 32, anchor = centre). Treasures, health, keys, ammo, power-ups, weapons.

Every item loops in place (spin, sway or pulse); the engine may add its own bob. Rendered at 6x supersampling.
"""
import math

import numpy as np

from bake import (MATS, Box, Capsule, Chamfer, Cone, Cylinder, Ellipsoid, Extrude, Intersect, Paint, Part, Poly,
                  Sheet, Sphere, Subtract, Torus, Union, col, material, pixelize, prism, render)

SIZE = (32, 32)
ANCHOR = (16, 16)
SS = 6

# ---------------------------------------------------------------------------------------------------------- materials
material("it_crystal", ["violet:2", "violet:3", "violet:4", "blue:4", "cyan:3", "cyan:4", "cyan:5", "cyan:6",
                        "white"],
         bands=[-0.5, -0.32, -0.16, 0.0, 0.16, 0.36, 0.62, 0.86], glow=True, line="violet:1", line_lit="violet:1")
material("it_crystal_core", ["cyan:5", "cyan:6", "white"], style="emit", bands=[0.4, 0.8])
material("it_ruby", ["crimson:2", "crimson:3", "crimson:4", "red:3", "red:4", "red:5", "white"],
         bands=[-0.45, -0.2, 0.05, 0.35, 0.72, 0.93], line="crimson:1", line_lit="crimson:1")
material("it_sapphire", ["blue:2", "blue:3", "blue:4", "blue:5", "blue:6", "white"],
         bands=[-0.4, -0.1, 0.3, 0.6, 0.9], line="blue:1")
material("it_velvet", ["crimson:1", "crimson:2", "crimson:3", "crimson:4"], bands=[-0.3, 0.2, 0.7])
material("it_gold", ["brown:2", "orange:3", "yellow:3", "yellow:4", "yellow:5", "yellow:6", "white"], style="metal",
         bands=[-0.5, -0.15, 0.2, 0.5, 0.75], spec=0.9, line="brown:1", line_lit="brown:1")
material("it_silver", ["slate:2", "steel:3", "steel:4", "steel:5", "steel:6", "steel:7", "white"], style="metal",
         bands=[-0.5, -0.15, 0.2, 0.5, 0.75], spec=0.9)
material("it_pcb", ["green:1", "green:2", "green:3", "green:4"], bands=[-0.3, 0.2, 0.7], line="green:0")
material("it_die", ["slate:1", "slate:2", "slate:3"], bands=[0.0, 0.6])
material("it_led", ["cyan:5", "cyan:6", "white"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("it_led_red", ["red:4", "red:6", "white"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("it_led_lime", ["lime:4", "lime:6", "white"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("it_magcore", ["magenta:3", "magenta:4", "magenta:5", "magenta:6", "white"], style="emit",
         bands=[0.2, 0.5, 0.75, 0.92])
material("it_emerald", ["green:3", "green:5", "lime:6"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("it_white", ["slate:4", "slate:5", "steel:6", "steel:7", "white"], bands=[-0.45, -0.05, 0.4, 0.8],
         line_lit="slate:2")
material("it_redglass", ["crimson:2", "red:3", "red:4", "red:5", "white"], style="glass", bands=[-0.3, 0.2, 0.6],
         spec=0.94, glow=True, line="crimson:1")
material("it_redglass_hi", ["red:3", "red:4", "red:5", "red:6", "white"], style="glass", bands=[-0.3, 0.2, 0.6],
         spec=0.94, glow=True, line="crimson:1")
material("it_cross", ["crimson:3", "red:3", "red:4"], bands=[-0.2, 0.5], line="red:1")
material("it_cross_hi", ["red:3", "red:4", "red:5"], bands=[-0.2, 0.5], glow=True, line="red:1")
material("it_dark", ["slate:1", "slate:2", "slate:3", "slate:4"], bands=[-0.4, 0.1, 0.7])
material("it_steel", ["steel:2", "steel:3", "steel:4", "steel:5", "steel:6", "white"], style="metal",
         bands=[-0.45, -0.05, 0.35, 0.7], spec=0.9)
material("it_card_blue", ["blue:2", "blue:3", "blue:4", "blue:5"], bands=[-0.5, -0.05, 0.6],
         line="blue:1", line_lit="blue:1")
material("it_card_gold", ["orange:3", "yellow:3", "yellow:4", "yellow:5"], bands=[-0.5, -0.05, 0.6],
         line="brown:1", line_lit="brown:1")
material("it_print", ["steel:6", "steel:7", "white"], bands=[0.0, 0.5], prio=2.0)
material("it_print_dark", ["brown:2", "brown:3", "brown:3"], bands=[0.0, 0.5], prio=2.0)
material("it_stripe", ["slate:1", "slate:2", "slate:3"], bands=[-0.1, 0.5])
material("it_lime_glow", ["green:3", "green:4", "lime:4", "lime:5"], style="emit", bands=[0.3, 0.6, 0.85])
material("it_lime_glow2", ["green:4", "lime:4", "lime:5", "lime:6"], style="emit", bands=[0.3, 0.6, 0.85])
# lore datapad (second round; registered after the others so nothing above changes)
material("it_pad", ["slate:1", "slate:2", "steel:3", "steel:4", "steel:5"], bands=[-0.45, -0.05, 0.45, 0.85],
         line_lit="slate:1")
material("it_pad_rim", ["orange:2", "orange:3", "orange:4", "orange:5"], bands=[-0.4, 0.05, 0.7], line_lit="orange:1")
material("it_pad_screen", ["cyan:1"], style="flat", prio=1.5, line="blue:1", inner=False)
material("it_led_orange", ["orange:4", "orange:5", "yellow:6"], style="emit", bands=[0.4, 0.8], prio=3.0)

ORB = {
    "overdrive": ["crimson:2", "red:3", "red:4", "orange:4", "orange:5", "yellow:6"],
    "boots": ["blue:2", "blue:3", "blue:4", "blue:5", "blue:6", "white"],
    "shield": ["teal:2", "teal:3", "teal:4", "teal:5", "teal:6", "white"],
}
for k, c in ORB.items():
    material(f"it_orb_{k}", c, style="glass", bands=[-0.45, -0.05, 0.35, 0.7], spec=0.93, glow=True,
             line="outline")

# weapons: body colour ramps and accent / glow colours
WEAPON = {
    "repeater": (["orange:2", "orange:3", "orange:4", "orange:5", "orange:6"], ["yellow:4", "yellow:6", "white"]),
    "scatter": (["orange:3", "yellow:3", "yellow:4", "yellow:5", "yellow:6"], ["orange:4", "yellow:6", "white"]),
    "ricochet": (["green:2", "green:3", "green:4", "green:5", "lime:6"], ["green:4", "lime:4", "lime:6"]),
    "cryo": (["ice:2", "ice:3", "ice:4", "ice:5", "ice:6"], ["cyan:4", "cyan:6", "white"]),
    "lancer": (["slate:4", "slate:5", "steel:6", "steel:7", "white"], ["red:4", "red:6", "white"]),
    "mortar": (["violet:2", "violet:3", "violet:4", "violet:5", "violet:6"], ["magenta:4", "magenta:6", "white"]),
    "arc": (["blue:2", "blue:3", "blue:4", "blue:5", "blue:6"], ["cyan:5", "cyan:6", "white"]),
    "seeker": (["magenta:2", "magenta:3", "magenta:4", "magenta:5", "magenta:6"], ["crimson:4", "rose:6", "white"]),
}
for k, (body, glow) in WEAPON.items():
    material(f"wp_{k}", body, bands=[-0.45, -0.05, 0.35, 0.75], line="outline", line_lit=body[0])
    material(f"wp_{k}_glow", glow, style="emit", bands=[0.35, 0.8], prio=2.0)
material("wp_red", ["crimson:2", "red:3", "red:4", "red:5"], bands=[-0.3, 0.15, 0.65])


# ---------------------------------------------------------------------------------------------------------- helpers

def bar_x(r, x0, x1, y=0.0, z=0.0, rr=0.0):
    """A cylinder along x from x0 to x1."""
    return Cylinder(r, (x1 - x0) / 2, rr=rr).rot(0, 0, -90).at((x0 + x1) / 2, y, z)


def ring_x(R, r, x, y=0.0, z=0.0):
    return Torus(R, r).rot(0, 0, 90).at(x, y, z)


def frame_of(parts, cov=7, outline=True):
    return pixelize(render(parts, SIZE, ANCHOR, ss=SS), cov=cov, outline=outline)


def sparkle(spr, x, y, size, c1="white", c2="cyan:6"):
    spr.put(x, y, c1, glow=True)
    for k in range(1, size + 1):
        c = c1 if k < size else c2
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            spr.put(x + dx, y + dy, c, glow=True)


def icon(spr, rows, x0, y0, colour, glow=True):
    """Hand-pixelled icon: rows of strings, '#' sets a pixel."""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "#":
                spr.put(x0 + i, y0 + j, colour, glow=glow)
            elif ch == "o":
                spr.put(x0 + i, y0 + j, "outline", glow=False)


# ---------------------------------------------------------------------------------------------------------- treasures

def crystal(t):
    spin = 60.0 * t           # hexagonal: 60 degrees repeat
    main = prism(6, 5.3, 3.6, 7.0, 5.2).m("it_crystal").rot(0, spin, 0).rot(10, 0, 8).at(0, 0.8, 0)
    core = prism(6, 2.0, 2.4, 3.0, 2.4).m("it_crystal_core").rot(0, spin + 30, 0).rot(10, 0, 8).at(0.2, 0.6, 2.6)
    s1 = prism(6, 2.1, 1.2, 3.4, 1.6).m("it_crystal").rot(0, -spin * 1.0 + 15, 0).rot(0, 0, 42).at(-5.4, -6.4, 0.5)
    s2 = prism(6, 1.8, 1.0, 2.8, 1.4).m("it_crystal").rot(0, spin + 20, 0).rot(0, 0, -38).at(5.0, -7.0, -0.5)
    return [Part(main), Part(s1), Part(s2)]


def crystal_frame(i):
    spr = frame_of(crystal(i / 8.0))
    stars = {0: [(11, 4, 2)], 1: [(12, 5, 1)], 3: [(21, 13, 1)], 4: [(20, 12, 2)], 5: [(21, 13, 1)], 6: [(9, 19, 1)]}
    for x, y, s in stars.get(i, []):
        sparkle(spr, x, y, s)
    return spr


def gem(t):
    spin = 45.0 * t
    planes = [(0, 1, 0, 2.6)]
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        ca, sa = math.cos(a), math.sin(a)
        s35, c35 = math.sin(math.radians(42)), math.cos(math.radians(42))
        n = np.array([ca * s35, c35, sa * s35])
        planes.append((*n, n @ np.array([6.6 * ca, 0.6, 6.6 * sa])))
        a2 = math.radians(i * 45)
        planes.append((math.cos(a2), 0, math.sin(a2), 6.9))
        s50, c50 = math.sin(math.radians(50)), math.cos(math.radians(50))
        n2 = np.array([ca * s50, -c50, sa * s50])
        planes.append((*n2, n2 @ np.array([0, -7.6, 0])))
    g = Poly(planes, 9).m("it_ruby").rot(0, spin, 0).rot(24, 0, 0).at(0, 1.0, 0)
    return [Part(g)]


def gem_frame(i):
    spr = frame_of(gem(i / 6.0))
    if i in (1, 4):
        sparkle(spr, 12 if i == 1 else 20, 9 if i == 1 else 11, 1, "white", "rose:6")
    return spr


def chip(t):
    spin = 90.0 * t
    parts = [Box(6.4, 0.9, 6.4, r=0.4).m("it_pcb"), Box(3.4, 0.7, 3.4, r=0.4).m("it_die").at(0, 1.2, 0),
             Sphere(0.9).m("it_led").at(1.6, 1.9, 1.6)]
    for k in range(4):
        off = -4.2 + k * 2.8
        for sx, sz, hx, hz in ((7.0, off, 0.9, 0.55), (-7.0, off, 0.9, 0.55), (off, 7.0, 0.55, 0.9), (off, -7.0, 0.55, 0.9)):
            parts.append(Box(hx, 0.35, hz, r=0.2).m("it_gold").at(sx, -0.3, sz))
    lines = [Box(0.3, 0.2, 2.2).m("it_gold").at(-4.8, 0.95, 2.6), Box(2.0, 0.2, 0.3).m("it_gold").at(-3.0, 0.95, -4.8)]
    shape = Union(*parts, *lines).rot(0, spin, 0).rot(38, 0, 0)
    return [Part(shape)]


def cube(t):
    spin = 90.0 * t
    frame = Subtract(Box(5.4, 5.4, 5.4, r=0.7),
                     Union(Box(4.0, 4.0, 7), Box(4.0, 7, 4.0), Box(7, 4.0, 4.0))).m("it_gold")
    core = Box(3.0, 3.0, 3.0, r=1.0).m("it_magcore").rot(0, -2 * spin + 20, 0)
    return [Part(Union(frame, core).rot(0, spin + 20, 0).rot(28, 0, 0))]


def idol(t):
    ang = 28.0 * math.sin(2 * math.pi * t)
    base = Cylinder(5.6, 1.3, rr=0.5).m("it_gold").at(0, -9.0, 0)
    step = Cylinder(4.4, 0.9, rr=0.4).m("it_gold").at(0, -7.2, 0)
    body = Ellipsoid(4.2, 4.8, 3.6).m("it_gold").at(0, -1.8, 0)
    belly = Sphere(1.2).m("it_emerald").at(3.6, -1.6, 0)
    head = Ellipsoid(4.4, 4.0, 4.0).m("it_gold").at(0.4, 5.6, 0)
    eye1 = Sphere(1.05).m("it_emerald").at(3.8, 6.0, 1.6)
    eye2 = Sphere(1.05).m("it_emerald").at(3.8, 6.0, -1.6)
    ears = [Cone(1.4, 0.3, 1.8).m("it_gold").rot(z * 30, 0, 0).at(-0.2, 10.0, z * 2.4) for z in (1, -1)]
    arms = [Capsule((1.0, 0.8, z * 3.4), (3.4, -1.2, z * 1.4), 1.1).m("it_gold") for z in (1, -1)]
    return [Part(Union(base, step, body, belly, head, eye1, eye2, *ears, *arms).rot(0, ang - 35, 0))]


def crown(t):
    ang = 22.0 * math.sin(2 * math.pi * t)
    band = Subtract(Cylinder(7.0, 2.5, rr=0.6), Cylinder(6.0, 4.0)).m("it_gold")
    velvet = Ellipsoid(6.2, 4.6, 6.2).m("it_velvet").at(0, 0.6, 0)
    parts = [band, velvet, Torus(7.0, 0.85).m("it_gold").at(0, -2.4, 0)]
    for i in range(5):
        a = math.radians(i * 72 + 90)
        ca, sa = math.cos(a), math.sin(a)
        parts.append(Cone(2.5, 0.35, 2.4).m("it_gold").at(6.3 * ca, 4.6, 6.3 * sa))
        parts.append(Sphere(1.15).m("it_gold").at(6.3 * ca, 7.3, 6.3 * sa))
        b2 = a + math.radians(36)
        gm = "it_ruby" if i % 2 == 0 else "it_sapphire"
        parts.append(Sphere(1.3).m(gm).at(7.0 * math.cos(b2), 0.0, 7.0 * math.sin(b2)))
    return [Part(Union(*parts).rot(0, ang - 90, 0).rot(26, 0, 0).at(0, -1.2, 0))]


# ---------------------------------------------------------------------------------------------------------- health, keys, ammo

def health(t, big=False):
    hi = (t * 4) % 2 < 1
    glass = "it_redglass_hi" if hi else "it_redglass"
    if not big:
        body = Cylinder(4.3, 3.8, rr=1.2).m(glass)
        caps = [Cylinder(4.9, 1.4, rr=0.7).m("it_white").at(0, y, 0) for y in (4.6, -4.6)]
        knob = Cylinder(1.9, 0.9, rr=0.4).m("it_white").at(0, 6.4, 0)
        return [Part(Union(body, *caps, knob).rot(0, 20, 0).rot(8, 0, 0).at(0, 0.0, 0))]
    box = Box(8.6, 6.4, 4.4, r=1.6).m("it_white")
    cross = Union(Box(1.2, 4.2, 5.0, r=0.3), Box(4.2, 1.2, 5.0, r=0.3)).m("it_cross_hi" if hi else "it_cross")
    shape = Paint(box, cross, "it_cross_hi" if hi else "it_cross")
    latch = Box(1.8, 1.0, 4.7, r=0.4).m("it_dark").at(0, 3.0, 0)
    handle = Subtract(Box(3.6, 2.2, 1.0, r=0.8), Box(2.4, 1.2, 2.0)).m("it_dark").at(0, 7.4, 0)
    return [Part(Union(shape, latch, handle).rot(0, -22, 0).rot(10, 0, 0).at(0, -0.8, 0))]


def health_frame(i, big):
    spr = frame_of(health(i / 4.0, big))
    if not big:
        icon(spr, ["  #  ", "  #  ", "#####", "  #  ", "  #  "], 14, 14, "white", glow=True)
    return spr


def keycard(t, kind):
    """A landscape key card held nearly face-on; a shine band sweeps across it."""
    m = "it_card_blue" if kind == "blue" else "it_card_gold"
    card = Box(7.2, 4.8, 0.6, r=0.7).m(m)
    card = Subtract(card, Cylinder(0.8, 2.0).rot(90, 0, 0).at(-5.4, 3.0, 0))
    sweep = -14 + 28 * t
    card = Paint(card, Box(0.9, 9, 2).rot(0, 0, -30).at(sweep, 0, 0), "it_print")
    stripe = Box(7.25, 0.85, 0.66).m("it_stripe").at(0, -2.9, 0)
    chipc = Box(1.5, 1.2, 0.7, r=0.3).m("it_silver" if kind == "gold" else "it_gold").at(4.4, 1.6, 0)
    led = Sphere(0.7).m("it_led" if kind == "blue" else "it_led_red").at(-5.4, -1.0, 0.5)
    return [Part(Union(card, stripe, chipc, led).rot(0, -16, 0).rot(10, 0, -6))]


KEY_GLYPH = [" ##       ", "#  #######", "#  #  # # ", " ##       "]


def keycard_frame(i, kind):
    spr = frame_of(keycard(i / 6.0, kind))
    c = "white" if kind == "blue" else "brown:2"
    icon(spr, KEY_GLYPH, 10, 14, c, glow=False)
    return spr


def ammo(t):
    hi = (t * 4) % 2 < 1
    body = Cylinder(3.3, 4.6, rr=0.8).m("it_steel")
    window = Box(4.0, 2.8, 4.0)
    shape = Paint(body, window, "it_lime_glow2" if hi else "it_lime_glow")
    caps = [Cylinder(3.7, 0.9, rr=0.4).m("it_dark").at(0, y, 0) for y in (4.2, -4.2)]
    tip = Cylinder(1.4, 0.8, rr=0.3).m("it_steel").at(0, 5.6, 0)
    return [Part(Union(shape, *caps, tip).scale(1.3).rot(0, 30 * t, 0).rot(0, 0, -28))]


# ---------------------------------------------------------------------------------------------------------- power-ups

ICONS = {
    "overdrive": ["    ###", "   ### ", "  ###  ", " ######", "   ### ", "  ###  ", " ##    ", "#      "],
    "boots": ["   #   ", "  ###  ", " ## ## ", "##   ##", "   #   ", "  ###  ", " ## ## ", "##   ##"],
    "shield": ["#######", "###o###", "###o###", "###o###", " ##o## ", " ##o## ", "  ###  ", "   #   "],
}


def power(t, kind):
    orb = Sphere(6.8).m(f"it_orb_{kind}")
    cap = [Cylinder(2.6, 0.9, rr=0.45).m("it_steel").at(0, y, 0) for y in (6.5, -6.5)]
    return [Part(orb), Part(Union(*cap).rot(14, 0, 0))]


def power_frame(i, kind):
    spr = frame_of(power(i / 6.0, kind))
    rows = ICONS[kind]
    w = max(len(r) for r in rows)
    x0 = 16 - w // 2 + (1 if kind == "shield" else 0)
    y0 = 16 - len(rows) // 2
    # icon with a dark drop shadow so it reads on the glass
    icon(spr, [r.replace("#", "o") for r in rows], x0 + 1, y0 + 1, "outline", glow=False)
    icon(spr, [r.replace("o", "#") for r in rows], x0, y0, "white", glow=True)
    icon(spr, ["".join("o" if ch == "o" else " " for ch in r) for r in rows], x0, y0, "outline", glow=False)
    if i in (1, 2, 3):
        sparkle(spr, (10, 11, 12)[i - 1], (10, 9, 10)[i - 1], 1, "white", "white")
    return spr


# ---------------------------------------------------------------------------------------------------------- weapons

def weapon(t, kind):
    """Small floating guns, about 26 px long, pointing right, swaying."""
    ang = 18.0 * math.sin(2 * math.pi * t)
    B, G = f"wp_{kind}", f"wp_{kind}_glow"
    grip = Box(1.3, 2.5, 1.2, r=0.6).m("it_dark").rot(0, 0, -16).at(-2.6, -3.4, 0)
    if kind == "repeater":   # triple barrel, drum
        parts = [Box(4.6, 2.5, 2.2, r=1.0).m(B).at(-2.0, 0, 0),
                 bar_x(0.9, 1.0, 9.6, 1.1, 0.9).m("it_steel"), bar_x(0.9, 1.0, 9.6, 1.1, -0.9).m("it_steel"),
                 bar_x(0.9, 1.0, 9.6, -0.5, 0).m("it_steel"),
                 ring_x(1.9, 0.6, 8.6, 0.4).m("it_dark"), ring_x(1.9, 0.6, 3.4, 0.4).m(B),
                 Cylinder(2.3, 1.5, rr=0.6).m("it_dark").rot(90, 0, 0).at(-3.2, -2.3, 0),
                 Box(3.0, 0.5, 2.3, r=0.2).m(G).at(-2.4, 1.5, 0), grip]
    elif kind == "scatter":  # wide flared muzzle, pump, stock
        parts = [Box(4.8, 2.3, 2.2, r=0.9).m(B).at(-1.6, 0, 0),
                 bar_x(1.2, 2.0, 5.0, 0.3).m("it_steel"),
                 Cone(1.4, 3.4, 1.9).m(B).rot(0, 0, -90).at(6.6, 0.3, 0),
                 Cylinder(2.4, 0.5).m("it_dark").rot(0, 0, -90).at(8.4, 0.3, 0),
                 Box(2.4, 0.9, 1.7, r=0.45).m("it_dark").at(2.4, -1.9, 0),
                 Box(2.4, 1.5, 1.6, r=0.6).m(B).rot(0, 0, 12).at(-7.6, -0.7, 0),
                 Box(2.2, 0.45, 2.3).m(G).at(-1.8, 1.2, 0), grip]
    elif kind == "ricochet":  # disc launcher: glowing disc on top
        parts = [Box(5.4, 2.0, 2.2, r=0.9).m(B).at(0, -0.6, 0),
                 Torus(3.8, 0.85).m(G).rot(38, 0, 0).at(-0.6, 2.6, 0),
                 Cylinder(3.2, 0.45).m("it_steel").rot(38, 0, 0).at(-0.6, 2.6, 0),
                 Cylinder(0.9, 0.9).m("it_dark").rot(38, 0, 0).at(-0.6, 2.6, 0),
                 Box(2.4, 1.0, 2.6, r=0.45).m(B).at(6.4, -0.3, 0),
                 Box(0.5, 0.45, 2.7).m("it_dark").at(8.6, -0.3, 0), grip]
    elif kind == "cryo":     # frost tank and nozzle
        parts = [Box(5.0, 2.1, 2.2, r=1.0).m(B).at(-1.2, -0.3, 0),
                 Capsule((-4.4, 2.6, 0), (1.8, 2.6, 0), 1.8).m(G),
                 ring_x(1.9, 0.5, -2.2, 2.6).m("it_steel"), ring_x(1.9, 0.5, 0.2, 2.6).m("it_steel"),
                 Cone(1.9, 0.9, 1.5).m(B).rot(0, 0, -90).at(5.2, -0.3, 0),
                 bar_x(0.75, 6.6, 8.8, -0.3).m("it_steel"), Sphere(0.9).m(G).at(9.0, -0.3, 0), grip]
    elif kind == "lancer":   # long beam emitter with red rings
        parts = [Box(3.8, 2.0, 2.0, r=0.9).m(B).at(-4.8, 0, 0),
                 bar_x(1.2, -1.2, 9.4, 0.3).m(B),
                 ring_x(1.95, 0.55, 1.6, 0.3).m("wp_red"), ring_x(1.95, 0.55, 4.4, 0.3).m("wp_red"),
                 ring_x(1.95, 0.55, 7.2, 0.3).m("wp_red"),
                 Sphere(1.35).m(G).at(9.8, 0.3, 0),
                 Box(2.0, 0.5, 1.6).m("wp_red").at(-4.6, 1.9, 0), grip]
    elif kind == "mortar":   # chunky tube angled up, bore towards the viewer
        tube = Subtract(Cylinder(3.0, 4.4, rr=0.8).m(B), Cylinder(2.0, 2.0).at(0, 4.6, 0).m("it_dark"))
        shell = Sphere(1.8).m(G).at(0, 3.2, 0)
        muzzle = Torus(3.1, 0.7).m(B).at(0, 4.0, 0)
        bands = Union(Torus(3.1, 0.5).m("it_dark").at(0, 1.0, 0), Torus(3.1, 0.5).m("it_dark").at(0, -2.4, 0))
        gun = Union(tube, shell, muzzle, bands).rot(-40, 0, -50).at(1.6, 1.6, 0)
        parts = [gun, Box(5.0, 1.5, 3.0, r=0.7).m("it_dark").at(-1.2, -3.8, 0),
                 Cylinder(1.5, 1.4).m("it_steel").rot(90, 0, 0).at(-0.6, -1.6, 0)]
    elif kind == "arc":      # coil gun with a forked tip
        parts = [Box(4.2, 2.2, 2.0, r=0.9).m("it_dark").at(-4.2, 0, 0),
                 bar_x(0.85, -1.2, 7.0).m("it_steel")]
        for k in range(3):
            parts.append(ring_x(1.9, 0.75, 0.4 + 2.4 * k).m(G))
        parts += [Box(1.7, 0.45, 0.6).m("it_steel").rot(0, 0, 12).at(8.4, 1.1, 0),
                  Box(1.7, 0.45, 0.6).m("it_steel").rot(0, 0, -12).at(8.4, -1.1, 0),
                  Box(2.4, 0.45, 2.1).m(B).at(-4.2, 1.4, 0), grip]
    else:                    # seeker: missile pod, three missiles poking out
        pod = Box(5.0, 3.6, 3.2, r=1.0).m(B)
        parts = [pod, Box(1.5, 0.9, 1.0, r=0.4).m("it_dark").at(-1.0, 4.2, 0),
                 Sphere(0.75).m(G).at(-1.0, 4.4, 1.1), grip.at(1.0, 0.2, 0)]
        for y, z in ((1.5, 0.0), (-1.3, 1.25), (-1.3, -1.25)):
            parts.append(bar_x(1.0, 3.0, 6.2, y, z).m("it_white"))
            parts.append(Cone(1.0, 0.15, 1.1).m("wp_red").rot(0, 0, -90).at(7.3, y, z))
            parts.append(ring_x(1.15, 0.35, 4.8, y, z).m("it_dark"))
    return [Part(Union(*parts).scale(1.25).rot(0, ang - 14, 0).rot(8, 0, 0).at(0, 0.4, 0))]


# ---------------------------------------------------------------------------------------------------------- lore

PAD_Y = -4.5     # the pad's centre (world y, up from the cell centre); the hologram floats above it


def datapad(t):
    """A small Beacon Corps datapad, tilted back and yawing gently: dark frame, orange corner bumpers, a glowing
    screen with lines of text, an orange status light."""
    yaw = -20.0 + 10.0 * math.sin(2 * math.pi * t)
    body = Box(5.6, 6.8, 0.75, r=0.9).m("it_pad")
    screen = Box(4.5, 5.2, 3.0).at(0, 0.5, 0)
    body = Paint(body, screen, "it_pad_screen")
    bumpers = [Sphere(1.25).m("it_pad_rim").at(sx * 5.1, sy * 6.3, 0) for sx in (-1, 1) for sy in (-1, 1)]
    led = Sphere(0.8).m("it_led_orange").at(0.0, -6.1, 0.6)
    pad = Union(body, *bumpers, led).rot(-24, 0, 0).rot(0, yaw, 0).rot(0, 0, -5)
    return [Part(pad.at(0, PAD_Y + 0.6 * math.sin(2 * math.pi * t), 0))]


TEXT = [6, 4, 5, 2, 6, 3, 5, 4]   # line lengths of the scrolling text (px)


def screen_text(spr, i):
    """Glowing lines of text on the dark screen, drawn per pixel row (1 px lines, 1 px gaps), scrolling up one line
    every two frames; the first line is a brighter heading. Returns the screen's top row and centre column."""
    scr = spr.mat == MATS["it_pad_screen"].id
    ys = np.nonzero(scr.any(1))[0]
    if not len(ys):
        return 15, 16
    top = int(ys.min())
    rows = [y for y in range(top + 1, int(ys.max())) if (y - top) % 2 == 1]
    for k, y in enumerate(rows):
        xs = np.nonzero(scr[y])[0]
        if len(xs) < 4:
            continue
        x0 = int(xs.min()) + 1
        ln = (len(xs) - 3) if k == 0 else TEXT[(k + i // 2) % len(TEXT)]
        for x in range(x0, min(int(xs.max()), x0 + ln)):
            if scr[y, x]:
                spr.put(x, y, "cyan:6" if k == 0 else "cyan:5", glow=True)
    allx = np.nonzero(scr.any(0))[0]
    return top, int(round((allx.min() + allx.max()) / 2))


# a tiny Beacon (lighthouse) glyph for the hologram, '#' lit, '+' dim
BEACON_GLYPH = ["  #  ", " ### ", "# + #", " +++ ", " #+# ", " +#+ ", " #+# ", "#####"]


def lore_frame(i, n=8):
    t = i / float(n)
    spr = pixelize(render(datapad(t), SIZE, ANCHOR, ss=SS), cov=7)
    top_y, cx = screen_text(spr, i)
    # the projection: a fan of faint light from the screen up to the hologram
    holo_y0 = 2 + (1 if i in (2, 3) else 0)          # the glyph's top row (it bobs against the pad)
    flicker = i == 5
    gx0 = cx - 2
    for yy in range(holo_y0 + len(BEACON_GLYPH), top_y - 1):
        half = 1 + (top_y - yy) // 3
        for xx in (cx - half, cx + half):
            if spr.get(xx, yy) < 0 and (xx + yy + i) % 2 == 0:
                spr.put(xx, yy, "cyan:3", glow=True)
    # the hologram: the Beacon Corps lighthouse, scanlines rolling down it
    for j, row in enumerate(BEACON_GLYPH):
        for k, ch in enumerate(row):
            if ch == " ":
                continue
            x, y = gx0 + k + (1 if flicker and j % 2 else 0), holo_y0 + j
            scan = (j + i) % 4 == 0
            if ch == "#":
                spr.put(x, y, "white" if (scan and not flicker) else ("cyan:5" if flicker else "cyan:6"), glow=True)
            else:
                spr.put(x, y, "cyan:4" if not scan else "cyan:5", glow=True)
    # a beam of light from the glyph's lamp, sweeping once per loop
    beam = [1, 2, 3, 2, 1, -1, -2, -1][i]
    ly = holo_y0 + 2
    for k in range(1, abs(beam) + 2):
        x = gx0 + 2 + (k + 1) * (1 if beam > 0 else -1)
        if spr.get(x, ly) < 0:
            spr.put(x, ly, "cyan:5" if k < abs(beam) + 1 else "cyan:4", glow=True)
    if i in (1, 6):
        sparkle(spr, (24, 7)[i == 6], (9, 8)[i == 6], 1, "white", "cyan:6")
    return spr


# ---------------------------------------------------------------------------------------------------------- sheet

ANIMS = [
    # name, fps, mode, frames, note
    ("crystal", 12, "loop", 8, "prism shard, spinning"),
    ("gem", 10, "loop", 6, "treasure 100"),
    ("chip", 8, "loop", 6, "treasure 200"),
    ("cube", 8, "loop", 6, "treasure 300"),
    ("idol", 8, "loop", 6, "treasure 500"),
    ("crown", 8, "loop", 6, "treasure 1000"),
    ("health", 6, "loop", 4, "+20"),
    ("health_big", 6, "loop", 4, "+60"),
    ("key_blue", 8, "loop", 6, ""),
    ("key_gold", 8, "loop", 6, ""),
    ("ammo", 6, "loop", 4, "energy cell"),
    ("power_overdrive", 10, "loop", 6, ""),
    ("power_boots", 10, "loop", 6, ""),
    ("power_shield", 10, "loop", 6, ""),
] + [(f"weapon_{k}", 8, "loop", 6, "") for k in WEAPON] + [
    # second round: appended, so the indices above stay as they are
    ("lore", 8, "loop", 8, "logbook page: holo datapad, the Beacon glyph floats above it"),
]


def frame(job):
    name, i = job
    n = next(a[3] for a in ANIMS if a[0] == name)
    t = i / float(n)
    if name == "crystal":
        return crystal_frame(i)
    if name == "gem":
        return gem_frame(i)
    if name == "chip":
        return frame_of(chip(t))
    if name == "cube":
        return frame_of(cube(t))
    if name == "idol":
        return frame_of(idol(t))
    if name == "crown":
        return frame_of(crown(t))
    if name in ("health", "health_big"):
        return health_frame(i, name == "health_big")
    if name.startswith("key_"):
        return keycard_frame(i, name[4:])
    if name == "ammo":
        return frame_of(ammo(t))
    if name.startswith("power_"):
        return power_frame(i, name[6:])
    if name.startswith("weapon_"):
        return frame_of(weapon(t, name[7:]))
    if name == "lore":
        return lore_frame(i, n)
    raise KeyError(name)


def jobs():
    return [(a[0], i) for a in ANIMS for i in range(a[3])]


def sheets(frames):
    sh = Sheet("items", SIZE, ANCHOR, cols=16, title="pickups (anchor = centre of the 32 px cell)")
    sh.note("all loop in place; the engine may add a bob. glow: crystal, lights, power orbs, weapon energy parts")
    for name, fps, mode, n, note in ANIMS:
        sh.anim(name, fps, mode, [frames[(name, i)] for i in range(n)], note=note)
    return [sh]
