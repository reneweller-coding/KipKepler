"""Level objects -- the objects sheet (64 x 96, anchor = bottom centre: the floor line under the object).

Exit gate (2 x 3 tiles), checkpoint beacon, teleporter pad, switch console, spring, holo sign, laser emitter.
"""
import math

import numpy as np

from bake import (Box, Canvas, Capsule, Cone, Cylinder, Extrude, Intersect, Paint, Part, Sheet, Sphere, Subtract,
                  Torus, Union, col, fbm, material, pixelize, prism, render)

SIZE = (64, 96)
ANCHOR = (32, 96)
RENDER_ANCHOR = (32, 95)     # world y = 0 one row up: the outline under the base is the last row

material("ob_steel", ["slate:2", "steel:3", "steel:4", "steel:5", "steel:6"], bands=[-0.45, -0.05, 0.35, 0.78])
material("ob_steel_dark", ["slate:1", "slate:2", "slate:3", "slate:4"], bands=[-0.4, 0.05, 0.6])
material("ob_orange", ["orange:2", "orange:3", "orange:4", "orange:5"], bands=[-0.42, 0.02, 0.8], line_lit="orange:1")
material("ob_white", ["slate:4", "slate:5", "steel:6", "steel:7"], bands=[-0.45, 0.0, 0.7], line_lit="slate:2")
material("ob_yellow", ["orange:3", "yellow:3", "yellow:4", "yellow:5"], bands=[-0.4, 0.05, 0.7])
material("ob_glass_off", ["violet:1", "violet:2", "slate:3", "slate:5"], style="glass", bands=[-0.2, 0.4],
         spec=0.92)
material("ob_crystal", ["violet:3", "violet:4", "cyan:4", "cyan:5", "cyan:6", "white"],
         bands=[-0.4, -0.1, 0.2, 0.5, 0.8], glow=True, line="violet:1")
material("ob_crystal_dim", ["violet:1", "violet:2", "violet:3", "slate:4"], bands=[-0.3, 0.1, 0.6], line="violet:1")
material("ob_lamp_on", ["cyan:4", "cyan:5", "cyan:6", "white"], style="emit", bands=[0.3, 0.6, 0.85])
material("ob_red", ["red:3", "red:4", "red:6"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("ob_red_dim", ["crimson:2", "crimson:3"], bands=[0.3], prio=3.0)
material("ob_green", ["green:4", "lime:5", "lime:6"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("ob_cyan", ["cyan:4", "cyan:5", "cyan:6"], style="emit", bands=[0.4, 0.8], prio=3.0)
material("ob_pad_glow", ["teal:4", "cyan:4", "cyan:5", "cyan:6"], style="emit", bands=[0.3, 0.6, 0.85])
material("ob_coil", ["slate:2", "steel:3", "steel:5", "steel:6", "white"], style="metal", bands=[-0.4, 0.1, 0.6],
         spec=0.9)
material("ob_rubber", ["slate:1", "slate:2", "slate:3"], bands=[-0.2, 0.5])
material("ob_holo", ["cyan:2"], style="flat", glow=True, line="cyan:1", line_lit="cyan:1", inner=False)
# secret warp gate (second round; registered after the others so nothing above changes)
material("ob_gold", ["brown:2", "orange:3", "yellow:3", "yellow:4", "yellow:5", "white"], style="metal",
         bands=[-0.45, -0.05, 0.35, 0.72], spec=0.9, line="brown:1", line_lit="brown:1")
material("ob_stone", ["violet:1", "violet:2", "slate:3", "slate:4"], bands=[-0.4, 0.05, 0.62])
material("ob_gem", ["violet:5", "magenta:5", "magenta:6", "white"], style="emit", bands=[0.3, 0.6, 0.85], prio=3.0)
material("ob_gem_dim", ["violet:2", "violet:3", "violet:4"], bands=[-0.1, 0.5], prio=2.0, line="violet:1")


def frame_of(parts, canvas=None, under=False, cov=7):
    r = render(parts, SIZE, RENDER_ANCHOR)
    if canvas is not None:
        if under:     # the canvas lies behind the 3D parts
            canvas.z[canvas.col >= 0] = -1e6
            r.overlay(canvas, zmode=True)
        else:
            r.overlay(canvas)
    return pixelize(r, cov=cov)


def canvas():
    return Canvas(SIZE, RENDER_ANCHOR)


# ---------------------------------------------------------------------------------------------------------- exit gate

GATE_W = 19.0    # inner half width
GATE_H = 62.0    # pillar top


def gate_parts(open_, t):
    P = []
    for sx in (-1, 1):
        x = sx * 24.6
        P.append(Box(5.2, GATE_H / 2, 5.0, r=1.4).m("ob_steel").at(x, GATE_H / 2, 0))
        P.append(Box(6.2, 3.0, 6.4, r=1.2).m("ob_steel_dark").at(x, 3.0, 0))
        P.append(Box(5.8, 2.2, 5.6, r=1.0).m("ob_orange").at(x, 20.0, 0))
        P.append(Box(5.8, 2.2, 5.6, r=1.0).m("ob_orange").at(x, 44.0, 0))
        for k in range(4):     # status lights on the inner faces
            m = ("ob_cyan" if (k + int(t * 8)) % 4 != 0 else "ob_lamp_on") if open_ else (
                "ob_red" if k == int(t * 4) % 4 else "ob_red_dim")
            P.append(Sphere(1.05).m(m).at(x - sx * 4.6, 27.0 + 4.0 * k, 3.4))
    arch = Intersect(Torus(25.0, 5.0).rot(90, 0, 0), Box(32, 16, 8).at(0, 16, 0)).m("ob_steel")
    P.append(arch.at(0, GATE_H, 0))
    band = Intersect(Torus(25.0, 5.3).rot(90, 0, 0), Box(32, 2.5, 8).rot(0, 0, 0).at(0, 14, 0)).m("ob_orange")
    for a in (-48, 48):
        P.append(Box(3.0, 5.6, 5.6, r=1.0).m("ob_orange").rot(0, 0, a).at(-25 * math.sin(math.radians(a)),
                                                                          GATE_H + 25 * math.cos(math.radians(a)), 0))
    # beacon on the keystone
    P.append(Cylinder(5.4, 2.0, rr=0.8).m("ob_steel_dark").at(0, GATE_H + 27.0, 0))
    cry = prism(6, 3.0, 1.6, 3.6, 2.4, twist=30 * t).m("ob_crystal" if open_ else "ob_crystal_dim")
    P.append(cry.rot(0, 60 * t, 0).at(0, GATE_H + 30.5, 0))
    return [Part(Union(*P))]


def gate_canvas(open_, t):
    c = canvas()
    X, Y = c.X, c.Y
    cy = 38.0
    # inner opening: rectangle below the arch + the half disc of the arch
    inside = ((np.abs(X) < GATE_W + 0.6) & (Y > 0) & (Y < GATE_H)) | (np.hypot(X, Y - GATE_H) < 20.0)
    if not open_:
        c.fill(inside, "slate:1")
        stripes = inside & (((X + 40) % 6) < 1.0) & (Y > 2)
        c.fill(stripes, "slate:2")
        rows = inside & (np.abs(((Y - 3) % 12) - 0) < 0.8)
        c.fill(rows, "blue:1")
        # a dim locked chevron
        chev = (np.abs(np.abs(X) * 0.9 - (Y - 40)) < 1.6) & (np.abs(X) < 8) & inside
        c.fill(chev, "crimson:2")
        return c
    # open: a swirling vortex
    dx = X / (GATE_W + 1)
    dy = (Y - cy) / 44.0
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    arms = 3
    f = (th * arms / (2 * np.pi) + r * 2.6 - t) % 1.0
    n = fbm(X, Y, 0.18, 7, 2)
    band = (f + 0.25 * n) % 1.0
    c.fill(inside, "violet:2", glow=True)
    c.fill(inside & (band < 0.55), "violet:3", glow=True)
    c.fill(inside & (band < 0.32) & (r < 0.95), "blue:4", glow=True)
    c.fill(inside & (band < 0.18) & (r < 0.85), "cyan:4", glow=True)
    c.fill(inside & (r < 0.42) & (band < 0.6), "cyan:5", glow=True)
    c.fill(inside & (r < 0.26), "cyan:6", glow=True)
    c.fill(inside & (r < 0.13), "white", glow=True)
    # rim
    rim = inside & ~((np.abs(X) < GATE_W - 1.4) & (Y > 0) & (Y < GATE_H) | (np.hypot(X, Y - GATE_H) < 18.6))
    c.fill(rim, "cyan:6", glow=True)
    return c


def gate_frame(open_, i, n):
    t = i / float(n)
    return frame_of(gate_parts(open_, t), gate_canvas(open_, t), under=True)


# ---------------------------------------------------------------------------------------------------------- checkpoint

LAMP_Y = 38.0


def checkpoint_frame(on, i, n):
    """A small lighthouse: white tower with orange bands, a lamp room, a rotating beam when lit."""
    t = i / float(n)
    P = [Box(9.0, 2.2, 7.0, r=1.0).m("ob_steel_dark").at(0, 2.2, 0),
         Cone(4.4, 2.8, 13.0).m("ob_white").at(0, 17.4, 0),
         Cylinder(4.05, 1.5, rr=0.4).m("ob_orange").at(0, 10.0, 0),
         Cylinder(3.35, 1.5, rr=0.4).m("ob_orange").at(0, 22.0, 0),
         Cylinder(5.0, 0.9, rr=0.4).m("ob_steel_dark").at(0, 31.2, 0),
         Cylinder(3.0, 2.4, rr=0.6).m("ob_lamp_on" if on else "ob_glass_off").at(0, 34.6 + 2.6, 0),
         Cone(4.6, 0.8, 2.0).m("ob_orange").at(0, 42.0, 0),
         Sphere(0.9).m("ob_red" if (on and i % 2 == 0) else "ob_red_dim").at(0, 44.6, 0),
         Box(1.4, 2.0, 0.5, r=0.3).m("ob_steel_dark").at(0, 15.0, 3.3)]
    for a_ in (0, 90, 180, 270):
        ca, sa = math.cos(math.radians(a_ + 45)), math.sin(math.radians(a_ + 45))
        P.append(Capsule((3.2 * ca, 32.2, 3.2 * sa), (3.2 * ca, 40.6, 3.2 * sa), 0.45).m("ob_steel_dark"))
    parts = [Part(Union(*P).rot(0, -20, 0))]
    if not on:
        return frame_of(parts)
    phi = 2 * math.pi * t
    cphi, sphi = math.cos(phi), math.sin(phi)
    c = canvas()
    X, Y = c.X, c.Y
    L = 27.0 * abs(cphi)
    if L > 3:
        sgn = 1 if cphi > 0 else -1
        u = X * sgn
        half = 1.4 + np.clip(u, 0, None) * 0.2
        wedge = (u > 3.0) & (u < L) & (np.abs(Y - LAMP_Y) < half)
        c.fill(wedge, "cyan:4", glow=True, line=False)
        c.fill(wedge & (np.abs(Y - LAMP_Y) < half * 0.45), "cyan:6", glow=True, line=False)
        c.fill(wedge & (u > L - 3) & (np.abs(Y - LAMP_Y) < half * 0.45), "cyan:5", glow=True, line=False)
    if sphi > 0.6:   # pointing at the viewer: a flash around the lamp room
        R, TH = c.polar(0, LAMP_Y)
        flash = (R > 4.0) & (R < 7.5) & ((np.abs(np.sin(TH * 4)) > 0.75) | (R < 5.2))
        c.fill(flash, "cyan:6", glow=True, line=False)
    r = render(parts, SIZE, RENDER_ANCHOR)
    if sphi >= -0.2:
        r.overlay(c)
    else:            # beam behind the tower
        c.z[c.col >= 0] = -1e6
        r.overlay(c, zmode=True)
    return pixelize(r)


# ---------------------------------------------------------------------------------------------------------- teleporter

def teleporter_frame(i, n):
    t = i / float(n)
    P = [Cylinder(15.5, 1.6, rr=0.7).m("ob_steel_dark").at(0, 1.6, 0),
         Cylinder(14.0, 1.2, rr=0.6).m("ob_orange").at(0, 3.4, 0),
         Cylinder(11.6, 0.8, rr=0.4).m("ob_pad_glow").at(0, 4.6, 0)]
    for a in range(0, 360, 60):
        ca, sa = math.cos(math.radians(a + 30 * t)), math.sin(math.radians(a + 30 * t))
        P.append(Box(1.0, 0.7, 1.0, r=0.3).m("ob_cyan").at(13.0 * ca, 4.4, 13.0 * sa))
    c = canvas()
    X, Y = c.X, c.Y
    top = 64.0
    col_ = (np.abs(X) < 11.5) & (Y > 5.0) & (Y < top)
    # column edges, dashed and fading upwards
    for sx in (-1, 1):
        edge = (np.abs(X - sx * 11.0) < 0.5) & col_ & (((Y - t * 24) % 8) < 5) & (Y < top - 8)
        c.fill(edge, "cyan:4", glow=True, line=False)
    # rising rings, smaller and dimmer as they rise
    for k in range(3):
        f = (t + k / 3.0) % 1.0
        yy = 7 + f * (top - 12)
        rx = 11.0 - 3.0 * f
        ring = np.abs(np.hypot(X / rx, (Y - yy) / 2.2) - 1.0) < 0.2
        c.fill(ring & col_, ("cyan:6", "cyan:5", "cyan:4")[min(2, int(f * 3))], glow=True, line=False)
    # motes
    for k, x0 in enumerate((-7, -3, 1, 5, 8)):
        y0 = 7 + ((t * 2 + k * 0.29) % 1.0) * (top - 14)
        mote = (np.abs(X - x0) < 0.5) & (Y > y0) & (Y < y0 + 2 + 2 * (k % 2))
        c.fill(mote, "white" if k % 2 else "cyan:6", glow=True, line=False)
    return frame_of([Part(Union(*P).rot(18, 0, 0))], c)


# ---------------------------------------------------------------------------------------------------------- switch

def switch_frame(on, i):
    ang = -38 if not on else 38
    P = [Box(5.0, 4.4, 4.6, r=1.0).m("ob_steel_dark").at(0, 4.4, 0),
         Box(7.4, 6.0, 5.4, r=1.4).m("ob_steel").at(0, 13.6, 0),
         Box(7.6, 1.4, 5.6, r=0.7).m("ob_orange").at(0, 19.6, 0),
         Box(4.6, 2.6, 0.6, r=0.4).m("ob_steel_dark").at(0, 13.0, 5.3),
         Cylinder(1.6, 2.2, rr=0.4).m("ob_steel_dark").rot(90, 0, 0).at(0, 21.2, 0)]
    blink = (i % 2 == 0)
    lt = ("ob_green" if blink else "ob_cyan") if on else "ob_red"
    P.append(Sphere(1.3).m(lt).at(-3.6 if not on else 3.6, 13.0, 5.8))
    P.append(Sphere(0.9).m("ob_red_dim" if on else "ob_steel_dark").at(3.6 if not on else -3.6, 13.0, 5.6))
    lever = Union(Capsule((0, 0, 0), (0, 9.0, 0), 1.0).m("ob_steel"),
                  Sphere(2.3).m("ob_red" if not on else "ob_green").at(0, 9.8, 0))
    P.append(lever.rot(0, 0, -ang).at(0, 21.2, 0))
    return frame_of([Part(Union(*P).scale(1.3).rot(0, -24, 0).rot(8, 0, 0))])


# ---------------------------------------------------------------------------------------------------------- spring

def spring_parts(h, sq=1.0):
    P = [Box(13.0, 1.6, 8.0, r=0.8).m("ob_steel_dark").at(0, 1.6, 0)]
    coils = 4
    for k in range(coils):
        y = 3.4 + (k + 0.5) * (h / coils)
        P.append(Torus(6.0, 1.1).m("ob_coil").rot(0, 0, 6 if k % 2 else -6).at(0, y, 0))
    top = 3.4 + h + 1.4
    pad = Box(12.6, 2.0 * sq, 7.6, r=0.9).m("ob_orange")
    chev = Extrude([(-5.5, -2.6), (0, 1.0), (5.5, -2.6), (5.5, -0.6), (0, 3.0), (-5.5, -0.6)], 3.0).rot(90, 0, 0)
    pad = Paint(pad, chev.at(0, 2.0, 0), "ob_yellow")
    P.append(pad.at(0, top, 0))
    P.append(Box(13.0, 0.7, 8.0, r=0.35).m("ob_steel_dark").at(0, top - 1.6 * sq, 0))
    return [Part(Union(*P).rot(22, -18, 0))]


def spring_frame(i, fire):
    if not fire:
        return frame_of(spring_parts(7.0))
    h = [3.0, 16.0, 11.0, 8.6, 7.0][i]
    sq = [1.15, 0.9, 1.0, 1.0, 1.0][i]
    spr = frame_of(spring_parts(h, sq))
    if i in (1, 2):   # speed lines
        for x in (-11, 0, 11):
            for y in range(69, 75 - 3 * i):
                spr.put(32 + x, y - (10 if i == 1 else 4), "yellow:6", glow=True)
    return spr


# ---------------------------------------------------------------------------------------------------------- sign

def sign_frame(i, n):
    P = [Box(5.0, 1.6, 4.0, r=0.8).m("ob_steel_dark").at(0, 1.6, 0),
         Cylinder(1.3, 8.0, rr=0.4).m("ob_steel").at(0, 11.0, 0),
         Box(3.6, 1.4, 2.6, r=0.6).m("ob_orange").at(0, 19.4, 0),
         Sphere(1.0).m("ob_cyan").at(0, 21.2, 1.2)]
    c = canvas()
    X, Y = c.X, c.Y
    jitter = [0, 0, 1, 0][i % 4]
    x0, x1, y0, y1 = -13 + jitter, 13 + jitter, 24, 40
    panel = (X > x0) & (X < x1) & (Y > y0) & (Y < y1)
    c.fill(panel, "cyan:2", glow=True, mat="ob_holo")
    scan = panel & (((Y + i * 2) % 4) < 1.0)
    c.fill(scan, "cyan:3", glow=True, mat="ob_holo")
    border = panel & ~((X > x0 + 1) & (X < x1 - 1) & (Y > y0 + 1) & (Y < y1 - 1))
    c.fill(border, "cyan:5", glow=True, mat="ob_holo")
    for k, (yy, w) in enumerate(((36.0, 18), (32.0, 14), (28.0, 16))):
        line = (Y > yy - 0.6) & (Y < yy + 0.6) & (X > x0 + 3) & (X < x0 + 3 + w)
        c.fill(line, "cyan:6" if k == 0 else "cyan:5", glow=True, mat="ob_holo")
    beam = (Y > 21.5) & (Y < 24.5) & (np.abs(X) < (Y - 21) * 2.5)
    c.fill(beam, "cyan:4", glow=True, line=False)
    if i == 2:   # flicker: one line drops out
        c.erase(panel & (Y > 31) & (Y < 33))
    return frame_of([Part(Union(*P).rot(0, -20, 0))], c, cov=6)


# ---------------------------------------------------------------------------------------------------------- laser emitter

def emitter_frame(i, on=True, side=False):
    pulse = ["ob_red", "ob_red", "ob_red_dim", "ob_red"][i % 4] if on else "ob_red_dim"
    P = [Box(9.0, 2.4, 7.0, r=1.0).m("ob_steel_dark").at(0, 2.4, 0),
         Box(6.6, 3.2, 5.6, r=1.2).m("ob_steel").at(0, 7.4, 0),
         Box(6.8, 0.9, 5.8, r=0.4).m("ob_orange").at(0, 5.6, 0),
         Cylinder(3.0, 1.6, rr=0.6).m("ob_steel_dark").at(0, 11.6, 0),
         Sphere(2.0).m(pulse).at(0, 13.0, 0)]
    for sx in (-1, 1):
        P.append(Box(0.8, 2.4, 0.8, r=0.3).m("ob_steel").at(sx * 3.6, 13.0, 0))
    shape = Union(*P).rot(12, -20, 0)
    if side:   # mounted on a left wall, firing right: rotate the whole emitter
        shape = shape.rot(0, 0, -90).at(-28.0, 16.0, 0)
    spr = frame_of([Part(shape)])
    if on and i % 4 != 2:
        if side:
            spr.put(32 - 28 + 15, 95 - 16, "white", glow=True)
        else:
            spr.put(32, 95 - 16, "white", glow=True)
    return spr


# ---------------------------------------------------------------------------------------------------------- warp gate

WARP_Y = 40.0     # ring centre above the floor
WARP_R = 16.5     # ring radius (the exit's opening is 38 px wide; this ring is smaller)


def warp_parts(t):
    """The secret warp gate: a gold ring standing in a claw on a violet stone plinth, gems chasing round it, a gold
    star on top."""
    P = [Box(14.0, 2.2, 7.0, r=1.0).m("ob_stone").at(0, 2.2, 0),
         Box(14.2, 0.7, 7.2, r=0.3).m("ob_gold").at(0, 4.6, 0),
         Box(10.0, 1.9, 5.6, r=0.8).m("ob_stone").at(0, 7.0, 0)]
    for sx in (-1, 1):   # the claw holding the ring
        P.append(Capsule((sx * 6.0, 8.0, 0), (sx * 10.6, 25.0, 0), 1.7).m("ob_gold"))
        P.append(Sphere(2.0).m("ob_gold").at(sx * 6.0, 8.6, 0))
        P.append(Cone(1.5, 0.3, 2.6).m("ob_gold").rot(0, 0, sx * 34).at(sx * 12.6, 28.4, 0))
    ring = Torus(WARP_R, 2.8).rot(90, 0, 0).at(0, WARP_Y, 0).m("ob_gold")
    lip = Torus(WARP_R - 2.6, 0.8).rot(90, 0, 0).at(0, WARP_Y, 0).m("ob_gem_dim")
    P += [ring, lip]
    lit = int(t * 8) % 8
    for k in range(8):   # eight gems, a light chasing round them
        a = math.radians(90 - k * 45)
        m = "ob_gem" if k in (lit, (lit + 4) % 8) else "ob_gem_dim"
        P.append(Sphere(1.35).m(m).at(WARP_R * math.cos(a), WARP_Y + WARP_R * math.sin(a), 2.4))
    star = []
    for k in range(8):
        a = math.radians(90 + k * 45)
        r = 5.6 if k % 2 == 0 else 1.9
        star.append((r * math.cos(a), r * math.sin(a)))
    top = WARP_Y + WARP_R + 6.0
    P.append(Extrude(star, 1.0, r=0.4).m("ob_gold").at(0, top, 0))
    P.append(Sphere(1.5).m("ob_gem").at(0, top, 1.0))
    return [Part(Union(*P).rot(0, -14, 0))]


VORTEX = ("violet:1", "violet:2", "purple:3", "magenta:4", "violet:4", "violet:5", "violet:6", "yellow:6", "white")


def warp_canvas(t):
    """The starry inside of the ring: two spiral arms turning, a soft violet core with a gold-white heart."""
    c = canvas()
    X, Y = c.X, c.Y
    R, TH = c.polar(0, WARP_Y)
    inside = R < WARP_R - 1.6
    f = (TH / (2 * np.pi) * 2 - R / 7.5 + t) % 1.0
    n = fbm(X, Y, 0.3, 5, 2)
    band = (f + 0.35 * n) % 1.0
    c.fill(inside, "violet:1", glow=True)
    c.fill(inside & (band < 0.55), "violet:2", glow=True)
    c.fill(inside & (band < 0.3) & (R > 2.5), "purple:3", glow=True)
    c.fill(inside & (band < 0.13) & (R > 4.0), "magenta:4", glow=True)
    c.fill(inside & (R < 6.4) & (band < 0.7), "violet:4", glow=True)
    c.fill(inside & (R < 4.0), "violet:5", glow=True)
    c.fill(inside & (R < 2.4), "yellow:6", glow=True)
    c.fill(inside & (R < 1.2), "white", glow=True)
    return c


def warp_frame(i, n):
    t = i / float(n)
    spr = frame_of(warp_parts(t), warp_canvas(t), under=True)
    ax, ay = RENDER_ANCHOR
    vortex = {col(v) for v in VORTEX}

    def px(x, y):
        return int(round(ax + x)), int(round(ay - y))
    # stars drifting inwards along the spiral, twinkling
    rng = np.random.default_rng(7)
    a0 = rng.uniform(0, 2 * np.pi, 12)
    ph = (np.arange(12) / 12.0 + rng.uniform(0, 0.05, 12))
    for k in range(12):
        u = (t + ph[k]) % 1.0
        r = 13.0 * (1 - u) + 2.5
        a = a0[k] + 2.4 * u
        x, y = px(r * math.cos(a), WARP_Y + r * math.sin(a))
        if spr.get(x, y) not in vortex:
            continue
        if k % 4 == 0 and 0.2 < u < 0.6:
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                if spr.get(x + dx, y + dy) in vortex:
                    spr.put(x + dx, y + dy, "white" if (dx, dy) == (0, 0) else "violet:6", glow=True)
        else:
            spr.put(x, y, ("white", "yellow:6", "violet:6")[k % 3], glow=True)
    # three gold motes orbiting outside the ring, each with a short trail
    for k in range(3):
        for j, c_ in enumerate(("yellow:6", "yellow:4", "orange:4")):
            a = 2 * np.pi * (t + k / 3.0) - j * 0.16
            x, y = px((WARP_R + 6.5) * math.cos(a), WARP_Y + (WARP_R + 6.5) * math.sin(a) * 0.92)
            if spr.get(x, y) < 0:
                spr.put(x, y, c_, glow=j < 2)
    return spr


# ---------------------------------------------------------------------------------------------------------- sheet

ANIMS = [
    ("exit_closed", 4, "loop", 4, "2 x 3 tiles; red lights chase"),
    ("exit_open", 12, "loop", 8, "swirling portal"),
    ("checkpoint_off", 2, "loop", 1, ""),
    ("checkpoint_on", 10, "loop", 6, "lamp lit, lighthouse beam turns"),
    ("teleporter", 12, "loop", 6, "pad with rising beam rings"),
    ("switch_off", 2, "loop", 1, "lever left, red light"),
    ("switch_on", 4, "loop", 2, "lever right, green light blinks"),
    ("spring", 2, "loop", 1, ""),
    ("spring_fire", 20, "once", 5, "compress, launch, settle"),
    ("sign", 8, "loop", 4, "holo panel, flicker"),
    ("laser_emitter", 8, "loop", 4, "floor mounted, fires up from point beam; rotate for walls/ceilings"),
    ("laser_emitter_off", 2, "loop", 1, "same emitter between bursts"),
    ("laser_emitter_side", 8, "loop", 4, "extra: mounted on a left wall, fires right from point beam_side"),
    # second round: appended, so the indices above stay as they are
    ("warp", 10, "loop", 8, "secret warp gate: gold ring on a plinth, starry violet vortex, gems chase, motes orbit"),
]


def frame(job):
    name, i = job
    n = next(a[3] for a in ANIMS if a[0] == name)
    if name.startswith("exit_"):
        return gate_frame(name == "exit_open", i, n)
    if name.startswith("checkpoint_"):
        return checkpoint_frame(name.endswith("_on"), i, n)
    if name == "teleporter":
        return teleporter_frame(i, n)
    if name.startswith("switch_"):
        return switch_frame(name.endswith("_on"), i)
    if name.startswith("spring"):
        return spring_frame(i, name == "spring_fire")
    if name == "sign":
        return sign_frame(i, n)
    if name == "laser_emitter":
        return emitter_frame(i)
    if name == "laser_emitter_off":
        return emitter_frame(i, on=False)
    if name == "laser_emitter_side":
        return emitter_frame(i, side=True)
    if name == "warp":
        return warp_frame(i, n)
    raise KeyError(name)


def jobs():
    return [(a[0], i) for a in ANIMS for i in range(a[3])]


def sheets(frames):
    sh = Sheet("objects", SIZE, ANCHOR, cols=8, title="level objects (anchor = bottom centre on the floor line)")
    sh.point("beam", 0, -17, "laser_emitter: where the fence beam starts (upwards)")
    sh.point("beam_side", -13, -17, "laser_emitter_side: where the beam starts (to the right)")
    sh.point("portal", 0, -39, "exit: centre of the portal opening")
    sh.point("warp", 0, -int(WARP_Y) - 1, "warp: centre of the ring")
    sh.note("exit is 64 x 96 (2 x 3 tiles); the others are about one tile wide and stand on the floor")
    for name, fps, mode, n, note in ANIMS:
        sh.anim(name, fps, mode, [frames[(name, i)] for i in range(n)], note=note)
    return [sh]
