"""bake.py -- the sprite baker of Kip Kepler (Dead Cells' trick in numpy).

Models are built from 3D signed-distance primitives (boxes with bevels, spheres, ellipsoids, capsules, cones,
cylinders, tori, lathes, extrusions, convex polyhedra), each rigid part hanging on a joint of a simple skeleton. A
frame is ray-traced orthographically at `ss` times the target size (default 4x) into a z-buffer, cel-shaded per
material from palette ramps (light from the top left front), then reduced to the target size by a weighted
majority (mode) filter -- no averaging, so no new colours -- cleaned of stray pixels, given dark inner lines where
a nearer part overlaps a farther one, and a 1 px outline.

    from bake import *
    material("suit", ["orange:2", "orange:3", "orange:4", "orange:5"], bands=[-0.3, 0.15, 0.65])
    body = Box(4, 6, 3, r=1.5).m("suit")
    r = render([Part(body.at(0, 6, 0))], size=(32, 32), anchor=(16, 30))
    spr = pixelize(r)                       # Sprite: rgba + glow, alpha 0/255, palette colours only

Coordinates: world units are target pixels. x right, y UP, z towards the viewer; the origin is the frame's anchor.
2D effects use `Canvas` (same grid, same pixelizer). Sheets are written with `Sheet` (PNG + .txt atlas + _glow.png,
contact sheets and GIF previews in work/sprites/). See README.md.
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from common.palette import OUTLINE, RAMPS, WHITE, palette as _palette  # noqa: E402

ASSETS = ROOT / "assets" / "sprites"
WORK = ROOT / "work" / "sprites"

# --------------------------------------------------------------------------------------------------------------
# Palette

PAL = _palette()                     # (N, 3) uint8: 0 OUTLINE, 1 WHITE, then 8 shades per ramp
RAMP_NAMES = list(RAMPS)
PAL_LOOKUP = {tuple(int(v) for v in c): i for i, c in enumerate(PAL)}


def col(spec):
    """Palette index of a colour spec: an int, "outline", "white", "ramp:shade" (e.g. "orange:3") or (ramp, shade)."""
    if isinstance(spec, (int, np.integer)):
        return int(spec)
    if isinstance(spec, tuple):
        name, i = spec
        return 2 + RAMP_NAMES.index(name) * 8 + int(i)
    if spec == "outline":
        return 0
    if spec == "white":
        return 1
    name, i = spec.split(":")
    i = int(i)
    if not 0 <= i < 8:
        raise ValueError(spec)
    return 2 + RAMP_NAMES.index(name) * 8 + i


def rgb(spec):
    return tuple(int(v) for v in PAL[col(spec)])


# --------------------------------------------------------------------------------------------------------------
# Materials

LIGHT = np.array([-0.55, 0.70, 0.50])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


class Material:
    """A shading recipe: `colours` are palette specs dark -> light (the shade steps).

    style  "cel"   lambert bands (thresholds `bands` on N.L, len(colours)-1 of them)
           "metal" like cel, plus the last colour as a specular band where R.V > `spec`
           "glass" like metal, plus a lighter horizon band (visors)
           "emit"  bands on facing N.V (core brightest); counts as emissive (glow mask)
           "flat"  colours[0] everywhere
    prio   weight in the majority filter (small important details > 1 survive the downsampling)
    line   outline / inner line colour on the shadow side; line_lit on the lit (top, left) side
    inner  draw dark inner lines where this material lies behind another part
    outline  False: no outline around this material's pixels (light beams, holograms, sparks)
    glow   emissive: written into the _glow mask
    """

    def __init__(self, name, colours, style="cel", bands=None, spec=0.9, prio=1.0, line="outline", line_lit=None,
                 inner=True, glow=None, rim=0.0, outline=True):
        self.name = name
        self.colours = [col(c) for c in colours]
        self.style = style
        k = len(self.colours) - (1 if style in ("metal", "glass") else 0)
        if bands is None:
            bands = list(np.linspace(-0.45, 0.70, max(1, k - 1))) if k > 1 else []
            if style == "emit":
                bands = list(np.linspace(0.25, 0.85, max(1, k - 1))) if k > 1 else []
        self.bands = np.array(bands, dtype=np.float32)
        self.spec = spec
        self.prio = prio
        self.line = col(line)
        self.line_lit = col(line_lit) if line_lit is not None else self.line
        self.inner = inner
        self.glow = (style == "emit") if glow is None else glow
        self.rim = rim
        self.outline = outline
        self.id = -1


MATS = {}
MAT_LIST = []


def material(name, colours, **kw):
    """Registers (or replaces) a material and returns its id."""
    m = Material(name, colours, **kw)
    if name in MATS:
        m.id = MATS[name].id
        MAT_LIST[m.id] = m
    else:
        m.id = len(MAT_LIST)
        MAT_LIST.append(m)
    MATS[name] = m
    return m.id


def mat_id(name):
    if name is None:
        return -1
    return MATS[name].id


material("_noline", ["white"], style="flat", inner=False, outline=False)   # canvas fills with line=False


# --------------------------------------------------------------------------------------------------------------
# Transforms


def rot(rx=0.0, ry=0.0, rz=0.0):
    """4x4 rotation, degrees, R = Ry @ Rx @ Rz (z swing first, then x tilt, then y yaw)."""
    ax, ay, az = (math.radians(v) for v in (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    M = np.eye(4)
    M[:3, :3] = Ry @ Rx @ Rz
    return M


def trans(x=0.0, y=0.0, z=0.0):
    M = np.eye(4)
    M[:3, 3] = (x, y, z)
    return M


def scaling(s):
    M = np.eye(4)
    M[:3, :3] *= s
    return M


def apply(M, p):
    return p @ M[:3, :3].T + M[:3, 3]


def _corners(lo, hi):
    return np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])


# --------------------------------------------------------------------------------------------------------------
# Shapes (signed distance functions). p is an (N, 3) float array; sdf returns (N,).


def _len(v):
    return np.sqrt((v * v).sum(-1))


def _dot2(v):
    return (v * v).sum(-1)


class Shape:
    matname = None

    def m(self, name):
        """Sets the material (inner shapes with their own material keep theirs)."""
        self.matname = name
        return self

    def sdf(self, p):
        raise NotImplementedError

    def bounds(self):
        raise NotImplementedError

    def _mats(self, p):
        return np.full(len(p), -1, np.int16)

    def mats(self, p):
        ids = self._mats(p)
        if self.matname is not None:
            ids[ids < 0] = mat_id(self.matname)
        return ids

    # transforms and booleans
    def at(self, x=0.0, y=0.0, z=0.0):
        return Xform(self, trans(x, y, z))

    def rot(self, rx=0.0, ry=0.0, rz=0.0):
        return Xform(self, rot(rx, ry, rz))

    def scale(self, s):
        return Xform(self, scaling(s))

    def xform(self, M):
        return Xform(self, M)

    def __or__(self, o):
        return Union(self, o)

    def __sub__(self, o):
        return Subtract(self, o)

    def __and__(self, o):
        return Intersect(self, o)


class Xform(Shape):
    """Rigid transform with uniform scale."""

    def __init__(self, shape, M):
        if isinstance(shape, Xform) and shape.matname is None:
            M = M @ shape.M
            shape = shape.shape
        self.shape = shape
        self.M = M
        self.Minv = np.linalg.inv(M)
        self.s = float(np.cbrt(abs(np.linalg.det(M[:3, :3]))))

    def sdf(self, p):
        return self.shape.sdf(apply(self.Minv, p)) * self.s

    def _mats(self, p):
        return self.shape.mats(apply(self.Minv, p))

    def bounds(self):
        lo, hi = self.shape.bounds()
        c = apply(self.M, _corners(lo, hi))
        return c.min(0), c.max(0)


class Union(Shape):
    def __init__(self, *shapes):
        self.shapes = [s for s in shapes if s is not None]

    def sdf(self, p):
        d = self.shapes[0].sdf(p)
        for s in self.shapes[1:]:
            d = np.minimum(d, s.sdf(p))
        return d

    def _mats(self, p):
        ds = np.stack([s.sdf(p) for s in self.shapes])
        w = ds.argmin(0)
        out = np.full(len(p), -1, np.int16)
        for i, s in enumerate(self.shapes):
            sel = w == i
            if sel.any():
                out[sel] = s.mats(p[sel])
        return out

    def bounds(self):
        b = [s.bounds() for s in self.shapes]
        return np.min([x[0] for x in b], 0), np.max([x[1] for x in b], 0)


class SmoothUnion(Union):
    def __init__(self, *shapes, k=1.0):
        super().__init__(*shapes)
        self.k = k

    def sdf(self, p):
        d = self.shapes[0].sdf(p)
        k = self.k
        for s in self.shapes[1:]:
            d2 = s.sdf(p)
            h = np.clip(0.5 + 0.5 * (d2 - d) / k, 0, 1)
            d = d2 * (1 - h) + d * h - k * h * (1 - h)
        return d

    def bounds(self):
        lo, hi = super().bounds()
        return lo - self.k, hi + self.k


class Subtract(Shape):
    """a minus b; the carved surface takes b's material when b has one."""

    def __init__(self, a, b):
        self.a, self.b = a, b

    def sdf(self, p):
        return np.maximum(self.a.sdf(p), -self.b.sdf(p))

    def _mats(self, p):
        out = self.a.mats(p)
        if self.b.matname is not None:
            carved = -self.b.sdf(p) > self.a.sdf(p)
            if carved.any():
                out[carved] = self.b.mats(p[carved])
        return out

    def bounds(self):
        return self.a.bounds()


class Intersect(Shape):
    def __init__(self, a, b):
        self.a, self.b = a, b

    def sdf(self, p):
        return np.maximum(self.a.sdf(p), self.b.sdf(p))

    def _mats(self, p):
        out = self.a.mats(p)
        if self.b.matname is not None:
            sel = self.b.sdf(p) > self.a.sdf(p)
            if sel.any():
                out[sel] = self.b.mats(p[sel])
        return out

    def bounds(self):
        la, ha = self.a.bounds()
        lb, hb = self.b.bounds()
        return np.maximum(la, lb), np.minimum(ha, hb)


class Paint(Shape):
    """Paints material `name` onto `shape` wherever the surface lies inside `region` (any shape)."""

    def __init__(self, shape, region, name):
        self.shape, self.region, self.paint = shape, region, name

    def sdf(self, p):
        return self.shape.sdf(p)

    def _mats(self, p):
        out = self.shape.mats(p)
        inside = self.region.sdf(p) < 0
        out[inside] = mat_id(self.paint)
        return out

    def bounds(self):
        return self.shape.bounds()


class Round(Shape):
    def __init__(self, shape, r):
        self.shape, self.r = shape, r

    def sdf(self, p):
        return self.shape.sdf(p) - self.r

    def _mats(self, p):
        return self.shape.mats(p)

    def bounds(self):
        lo, hi = self.shape.bounds()
        return lo - self.r, hi + self.r


class Shell(Shape):
    def __init__(self, shape, t):
        self.shape, self.t = shape, t

    def sdf(self, p):
        return np.abs(self.shape.sdf(p)) - self.t

    def _mats(self, p):
        return self.shape.mats(p)

    def bounds(self):
        lo, hi = self.shape.bounds()
        return lo - self.t, hi + self.t


# primitives ---------------------------------------------------------------------------------------------------


class Sphere(Shape):
    def __init__(self, r):
        self.r = r

    def sdf(self, p):
        return _len(p) - self.r

    def bounds(self):
        return np.full(3, -self.r), np.full(3, self.r)


class Ellipsoid(Shape):
    def __init__(self, rx, ry, rz):
        self.r = np.array([rx, ry, rz], dtype=np.float64)

    def sdf(self, p):
        k0 = _len(p / self.r)
        k1 = _len(p / (self.r * self.r))
        return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)

    def bounds(self):
        return -self.r, self.r.copy()


class Box(Shape):
    """Half extents hx, hy, hz, edges rounded (bevelled) by r."""

    def __init__(self, hx, hy, hz, r=0.0):
        self.h = np.array([hx, hy, hz], dtype=np.float64)
        self.r = min(r, float(self.h.min()))

    def sdf(self, p):
        q = np.abs(p) - (self.h - self.r)
        return _len(np.maximum(q, 0)) + np.minimum(q.max(-1), 0) - self.r

    def bounds(self):
        return -self.h, self.h.copy()


class Chamfer(Shape):
    """A box with 45-degree chamfered edges of size c (hard bevel instead of a round one)."""

    def __init__(self, hx, hy, hz, c=1.0):
        self.h = np.array([hx, hy, hz], dtype=np.float64)
        self.c = c

    def sdf(self, p):
        q = np.abs(p)
        d = (q - self.h).max(-1)
        s = 1 / math.sqrt(2)
        hx, hy, hz = self.h
        c = self.c
        e1 = (q[:, 0] + q[:, 1] - (hx + hy - c)) * s
        e2 = (q[:, 1] + q[:, 2] - (hy + hz - c)) * s
        e3 = (q[:, 0] + q[:, 2] - (hx + hz - c)) * s
        return np.maximum.reduce([d, e1, e2, e3])

    def bounds(self):
        return -self.h, self.h.copy()


class RoundCone(Shape):
    """A capsule from a to b with radius r1 at a and r2 at b (IQ's round cone)."""

    def __init__(self, a, b, r1, r2=None):
        self.a = np.array(a, dtype=np.float64)
        self.b = np.array(b, dtype=np.float64)
        self.r1 = r1
        self.r2 = r1 if r2 is None else r2
        if np.allclose(self.a, self.b):
            self.b = self.a + np.array([0, 1e-3, 0])

    def sdf(self, p):
        a, b, r1, r2 = self.a, self.b, self.r1, self.r2
        ba = b - a
        l2 = ba @ ba
        rr = r1 - r2
        a2 = l2 - rr * rr
        il2 = 1.0 / l2
        pa = p - a
        y = pa @ ba
        z = y - l2
        x2 = _dot2(pa * l2 - y[:, None] * ba)
        y2 = y * y * l2
        z2 = z * z * l2
        k = np.sign(rr) * rr * rr * x2
        d_b = np.sqrt(x2 + z2) * il2 - r2
        d_a = np.sqrt(x2 + y2) * il2 - r1
        d_m = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - r1
        return np.where(np.sign(z) * a2 * z2 > k, d_b, np.where(np.sign(y) * a2 * y2 < k, d_a, d_m))

    def bounds(self):
        r = max(self.r1, self.r2)
        return np.minimum(self.a, self.b) - r, np.maximum(self.a, self.b) + r


def Capsule(a, b, r):
    return RoundCone(a, b, r, r)


class Cylinder(Shape):
    """Along y: radius r, half height h, edges rounded by rr."""

    def __init__(self, r, h, rr=0.0):
        self.r, self.h, self.rr = r, h, rr

    def sdf(self, p):
        d0 = np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2) - self.r + self.rr
        d1 = np.abs(p[:, 1]) - self.h + self.rr
        return np.minimum(np.maximum(d0, d1), 0) + np.sqrt(np.maximum(d0, 0) ** 2 + np.maximum(d1, 0) ** 2) - self.rr

    def bounds(self):
        return np.array([-self.r, -self.h, -self.r]), np.array([self.r, self.h, self.r])


class Cone(Shape):
    """Capped cone along y: radius r1 at y=-h, r2 at y=+h."""

    def __init__(self, r1, r2, h):
        self.r1, self.r2, self.h = r1, r2, h

    def sdf(self, p):
        r1, r2, h = self.r1, self.r2, self.h
        qx = np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2)
        qy = p[:, 1]
        k1 = np.array([r2, h])
        k2 = np.array([r2 - r1, 2 * h])
        cax = qx - np.minimum(qx, np.where(qy < 0, r1, r2))
        cay = np.abs(qy) - h
        t = np.clip(((k1[0] - qx) * k2[0] + (k1[1] - qy) * k2[1]) / (k2 @ k2), 0, 1)
        cbx = qx - k1[0] + k2[0] * t
        cby = qy - k1[1] + k2[1] * t
        s = np.where((cbx < 0) & (cay < 0), -1.0, 1.0)
        return s * np.sqrt(np.minimum(cax * cax + cay * cay, cbx * cbx + cby * cby))

    def bounds(self):
        r = max(self.r1, self.r2)
        return np.array([-r, -self.h, -r]), np.array([r, self.h, r])


class Torus(Shape):
    """In the xz plane: ring radius R, tube radius r."""

    def __init__(self, R, r):
        self.R, self.r = R, r

    def sdf(self, p):
        q0 = np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2) - self.R
        return np.sqrt(q0 * q0 + p[:, 1] ** 2) - self.r

    def bounds(self):
        e = self.R + self.r
        return np.array([-e, -self.r, -e]), np.array([e, self.r, e])


def sd_polygon(v, px, py):
    """Signed distance of 2D points to a closed polygon v [(x, y), ...] (IQ)."""
    v = np.asarray(v, dtype=np.float64)
    n = len(v)
    d = (px - v[0, 0]) ** 2 + (py - v[0, 1]) ** 2
    s = np.ones_like(px)
    j = n - 1
    for i in range(n):
        ex, ey = v[j, 0] - v[i, 0], v[j, 1] - v[i, 1]
        wx, wy = px - v[i, 0], py - v[i, 1]
        ee = ex * ex + ey * ey
        t = np.clip((wx * ex + wy * ey) / ee, 0, 1) if ee > 0 else 0
        bx, by = wx - ex * t, wy - ey * t
        d = np.minimum(d, bx * bx + by * by)
        c1 = py >= v[i, 1]
        c2 = py < v[j, 1]
        c3 = ex * wy > ey * wx
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
        j = i
    return s * np.sqrt(d)


class Lathe(Shape):
    """A profile [(r, y), ...] (r >= 0, listed bottom to top along the outside) revolved around the y axis."""

    def __init__(self, profile):
        prof = [(float(r), float(y)) for r, y in profile]
        poly = [(0.0, prof[0][1])] + prof + [(0.0, prof[-1][1])]
        self.poly = np.array(poly)

    def sdf(self, p):
        q = np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2)
        return sd_polygon(self.poly, q, p[:, 1])

    def bounds(self):
        r = self.poly[:, 0].max()
        return np.array([-r, self.poly[:, 1].min(), -r]), np.array([r, self.poly[:, 1].max(), r])


class Extrude(Shape):
    """A 2D polygon [(x, y), ...] in the xy plane extruded to half depth hz, edges rounded by r."""

    def __init__(self, poly, hz, r=0.0):
        self.poly = np.array(poly, dtype=np.float64)
        self.hz, self.r = hz, r

    def sdf(self, p):
        d = sd_polygon(self.poly, p[:, 0], p[:, 1]) + self.r
        w1 = np.abs(p[:, 2]) - self.hz + self.r
        return np.minimum(np.maximum(d, w1), 0) + np.sqrt(np.maximum(d, 0) ** 2 + np.maximum(w1, 0) ** 2) - self.r

    def bounds(self):
        lo = self.poly.min(0)
        hi = self.poly.max(0)
        return np.array([lo[0], lo[1], -self.hz]), np.array([hi[0], hi[1], self.hz])


class Poly(Shape):
    """Convex polyhedron: the intersection of half spaces n.p <= d, planes [(nx, ny, nz, d), ...]."""

    def __init__(self, planes, extent):
        pl = np.array(planes, dtype=np.float64)
        n = pl[:, :3] / np.linalg.norm(pl[:, :3], axis=1, keepdims=True)
        self.n = n
        self.d = pl[:, 3] / np.linalg.norm(pl[:, :3], axis=1)
        self.extent = extent

    def sdf(self, p):
        return (p @ self.n.T - self.d).max(-1)

    def bounds(self):
        e = self.extent
        return np.full(3, -e), np.full(3, e)


def bipyramid(sides, r, h_top, h_bot, twist=0.0):
    """A faceted crystal: a `sides`-gon of radius r at y=0, apex at +h_top and -h_bot."""
    planes = []
    for i in range(sides):
        a = math.radians(twist + 360.0 * (i + 0.5) / sides)
        ca, sa = math.cos(a), math.sin(a)
        apo = r * math.cos(math.pi / sides)
        # top face through the apex (0, h_top, 0) and the edge at apothem apo
        for h, sgn in ((h_top, 1), (h_bot, -1)):
            n = np.array([ca * h, sgn * apo, sa * h])
            d = n @ np.array([0, sgn * h, 0])
            planes.append((*n, d))
    return Poly(planes, max(r, h_top, h_bot))


def prism(sides, r, h_mid, h_top, h_bot, twist=0.0):
    """A crystal shard: a `sides`-gon column from -h_mid..h_mid with pointed ends of extra height h_top / h_bot."""
    planes = []
    apo = r * math.cos(math.pi / sides)
    for i in range(sides):
        a = math.radians(twist + 360.0 * (i + 0.5) / sides)
        ca, sa = math.cos(a), math.sin(a)
        planes.append((ca, 0, sa, apo))
        for h, sgn in ((h_top, 1), (h_bot, -1)):
            n = np.array([ca * h, sgn * apo, sa * h])
            d = n @ np.array([0, sgn * (h + h_mid), 0])
            planes.append((*n, d))
    return Poly(planes, max(r, h_mid + max(h_top, h_bot)))


# --------------------------------------------------------------------------------------------------------------
# Skeleton


class Rig:
    """Joints with a parent and an offset; a pose gives each joint a rotation (rx, ry, rz) in degrees."""

    def __init__(self):
        self.joints = {}
        self.order = []

    def joint(self, name, parent, offset):
        self.joints[name] = (parent, np.array(offset, dtype=np.float64))
        self.order.append(name)

    def solve(self, pose, base=None):
        """Model-space 4x4 matrices of all joints. pose[name] = (rx, ry, rz) or a dict; base = root matrix."""
        out = {}
        for name in self.order:
            parent, off = self.joints[name]
            P = out[parent] if parent else (base if base is not None else np.eye(4))
            r = pose.get(name, (0, 0, 0))
            if isinstance(r, dict):
                r = (r.get("rx", 0), r.get("ry", 0), r.get("rz", 0))
            out[name] = P @ trans(*off) @ rot(*r)
        return out

    def chain_angle(self, pose, name):
        """Accumulated z rotation of a joint's ancestors (sagittal plane), for IK in the parent's frame."""
        a = 0.0
        parent = self.joints[name][0]
        while parent:
            r = pose.get(parent, (0, 0, 0))
            a += r[2] if not isinstance(r, dict) else r.get("rz", 0)
            parent = self.joints[parent][0]
        return a


def ik2(base, target, l1, l2, bend=1.0):
    """Two-bone IK in the xy plane. Angles measured from 'down' towards +x, degrees.
    Returns (a1 absolute angle of the first bone, a2 angle of the second bone relative to the first).
    bend=+1 puts the middle joint forward (+x, knees), -1 backward (elbows of a hanging arm)."""
    bx, by = base
    tx, ty = target
    dx, dy = tx - bx, ty - by
    d = math.hypot(dx, dy)
    d = min(max(d, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-4)
    phi = math.atan2(dx, -dy)
    ca = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    alpha = math.acos(max(-1.0, min(1.0, ca)))
    a1 = phi + alpha * bend
    kx, ky = bx + l1 * math.sin(a1), by - l1 * math.cos(a1)
    a_s = math.atan2(tx - kx, -(ty - ky))
    return math.degrees(a1), math.degrees(a_s - a1)


# --------------------------------------------------------------------------------------------------------------
# Animation helpers


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 2


def ease_in(t):
    t = min(max(t, 0.0), 1.0)
    return t * t


def lerp(a, b, t):
    if isinstance(a, (tuple, list)):
        return type(a)(lerp(x, y, t) for x, y in zip(a, b))
    return a + (b - a) * t


def keys(table, t, ease=smooth):
    """Interpolates a keyframe list [(time, value), ...] (values: numbers, tuples or dicts of those) at time t."""
    if t <= table[0][0]:
        return table[0][1]
    for (t0, v0), (t1, v1) in zip(table, table[1:]):
        if t <= t1:
            u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            if isinstance(v0, dict):
                return {k: lerp(v0[k], v1.get(k, v0[k]), u) for k in v0}
            return lerp(v0, v1, u)
    return table[-1][1]


# --------------------------------------------------------------------------------------------------------------
# Rendering


class Part:
    """A rigid piece of a scene: shape (already placed in world space), shade offset (-1 darkens the far limbs),
    whether inner lines are drawn on it, and zbias (added to its depth: > 0 draws it in front of parts it really
    lies behind -- the sprite artist's licence, e.g. an arm raised in front of a big helmet)."""

    def __init__(self, shape, name="", shade=0, inner=True, zbias=0.0):
        self.shape, self.name, self.shade, self.inner, self.zbias = shape, name, shade, inner, zbias


class Raster:
    """Supersampled buffers: col (palette index, -1 empty), mat, part, z, emit, prio. Size h x w (= ss * target)."""

    def __init__(self, w, h, ss, anchor):
        self.w, self.h, self.ss, self.anchor = w, h, ss, anchor
        self.col = np.full((h, w), -1, np.int16)
        self.mat = np.full((h, w), -1, np.int16)
        self.part = np.full((h, w), -1, np.int16)
        self.z = np.full((h, w), -1e9, np.float32)
        self.emit = np.zeros((h, w), bool)
        self.prio = np.ones((h, w), np.float32)
        self.n = np.zeros((h, w, 3), np.float32)
        self.part_inner = None

    def grid(self):
        """World coordinates (x, y) of every supersample centre."""
        ax, ay = self.anchor
        xs = (np.arange(self.w) + 0.5) / self.ss - ax
        ys = ay - (np.arange(self.h) + 0.5) / self.ss
        return np.meshgrid(xs, ys)

    def overlay(self, other, zmode=False):
        """Copies other's opaque samples on top (or by depth when zmode)."""
        m = other.col >= 0
        if zmode:
            m &= other.z > self.z
        for k in ("col", "mat", "part", "z", "emit", "prio"):
            getattr(self, k)[m] = getattr(other, k)[m]
        self.n[m] = other.n[m]
        return self

    def erase(self, mask):
        self.col[mask] = -1
        self.mat[mask] = -1
        self.part[mask] = -1
        self.z[mask] = -1e9
        self.emit[mask] = False


def _trace(shape, X, Y, z0, z1, steps=96, eps=0.004):
    """Sphere-traces rays (x, y, z0) -> (x, y, z1) along -z. Returns hit mask and hit z."""
    n = len(X)
    hit = np.zeros(n, bool)
    zh = np.full(n, -1e9)
    idx = np.arange(n)
    z = np.full(n, float(z0))
    x, y = X, Y
    for _ in range(steps):
        if len(idx) == 0:
            break
        p = np.stack([x, y, z], -1)
        d = shape.sdf(p)
        h = d < eps
        if h.any():
            hit[idx[h]] = True
            zh[idx[h]] = z[h]
        keep = ~h
        z = z - np.maximum(d, eps * 0.5) * 0.92
        keep &= z > z1
        idx, x, y, z = idx[keep], x[keep], y[keep], z[keep]
    return hit, zh


def _normals(shape, p, e=0.03):
    ex = np.array([e, 0, 0])
    ey = np.array([0, e, 0])
    ez = np.array([0, 0, e])
    nx = shape.sdf(p + ex) - shape.sdf(p - ex)
    ny = shape.sdf(p + ey) - shape.sdf(p - ey)
    nz = shape.sdf(p + ez) - shape.sdf(p - ez)
    n = np.stack([nx, ny, nz], -1)
    return n / np.maximum(_len(n), 1e-9)[:, None]


def render(parts, size, anchor, ss=4, squash=(1.0, 1.0), pivot=(0.0, 0.0)):
    """Ray-traces the parts into a Raster of size (w, h) * ss. squash = (sx, sy) scales the picture about the world
    point `pivot` (stretch and squash without breaking the distance fields)."""
    w, h = size
    R = Raster(w * ss, h * ss, ss, anchor)
    sx, sy = squash
    ax, ay = anchor
    shade = np.zeros((R.h, R.w), np.int16)
    for pi, part in enumerate(parts):
        lo, hi = part.shape.bounds()
        # world bbox -> screen samples (accounting for the squash)
        x0 = pivot[0] + (lo[0] - pivot[0]) * sx
        x1 = pivot[0] + (hi[0] - pivot[0]) * sx
        y0 = pivot[1] + (lo[1] - pivot[1]) * sy
        y1 = pivot[1] + (hi[1] - pivot[1]) * sy
        c0 = max(0, int(math.floor((x0 + ax) * ss)) - 1)
        c1 = min(R.w, int(math.ceil((x1 + ax) * ss)) + 1)
        r0 = max(0, int(math.floor((ay - y1) * ss)) - 1)
        r1 = min(R.h, int(math.ceil((ay - y0) * ss)) + 1)
        if c0 >= c1 or r0 >= r1:
            continue
        cs = np.arange(c0, c1)
        rs = np.arange(r0, r1)
        CC, RR = np.meshgrid(cs, rs)
        Xs = (CC + 0.5) / ss - ax
        Ys = ay - (RR + 0.5) / ss
        Xw = pivot[0] + (Xs - pivot[0]) / sx
        Yw = pivot[1] + (Ys - pivot[1]) / sy
        hit, zh = _trace(part.shape, Xw.ravel(), Yw.ravel(), hi[2] + 0.5, lo[2] - 0.5)
        if not hit.any():
            continue
        rr = RR.ravel()[hit]
        cc = CC.ravel()[hit]
        zz = zh[hit]
        nearer = zz + part.zbias > R.z[rr, cc]
        if not nearer.any():
            continue
        rr, cc, zz = rr[nearer], cc[nearer], zz[nearer]
        p = np.stack([Xw.ravel()[hit][nearer], Yw.ravel()[hit][nearer], zz], -1)
        nrm = _normals(part.shape, p)
        if sx != 1.0 or sy != 1.0:
            nrm = nrm / np.array([sx, sy, 1.0])
            nrm /= _len(nrm)[:, None]
        mids = part.shape.mats(p)
        R.z[rr, cc] = zz + part.zbias
        R.part[rr, cc] = pi
        R.mat[rr, cc] = mids
        R.n[rr, cc] = nrm
        shade[rr, cc] = part.shade
        R.col[rr, cc] = -2  # resolved by _shade()
    R.part_inner = np.array([p.inner for p in parts] + [False], bool)
    _shade(R, shade)
    return R


def _shade(R, shade_off):
    m = R.col == -2
    R.col[~m] = -1
    if not m.any():
        return
    for mat in MAT_LIST:
        sel = m & (R.mat == mat.id)
        if not sel.any():
            continue
        N = R.n[sel].astype(np.float64)
        steps = shade_steps(mat, N)
        steps = np.clip(steps + shade_off[sel], 0, len(mat.colours) - 1)
        R.col[sel] = np.array(mat.colours, np.int16)[steps]
        R.emit[sel] = mat.glow
        R.prio[sel] = mat.prio
    bad = m & (R.mat < 0)
    if bad.any():  # parts without material: magenta flag
        R.col[bad] = col("magenta:5")


def shade_steps(mat, N):
    k = len(mat.colours)
    v = N @ LIGHT
    if mat.style == "flat":
        return np.zeros(len(N), np.int64)
    if mat.style == "emit":
        return np.digitize(N[:, 2], mat.bands)
    s = np.digitize(v, mat.bands)
    if mat.rim > 0:
        rim = (N[:, 2] < mat.rim) & (N[:, 1] > 0.2) & (N[:, 0] < 0.3)
        s = np.where(rim, s + 1, s)
    if mat.style == "glass":
        horizon = (N[:, 1] > -0.32) & (N[:, 1] < -0.05) & (N[:, 2] > 0.25)
        s = np.where(horizon, np.minimum(s + 1, k - 2), s)
    if mat.style in ("metal", "glass"):
        s = np.minimum(s, k - 2)
        Rz = 2 * v * N[:, 2] - LIGHT[2]
        s = np.where(Rz > mat.spec, k - 1, s)
    return s


# --------------------------------------------------------------------------------------------------------------
# 2D canvas (effects, shots, hand-made icons) on the same supersampled grid


class Canvas(Raster):
    """A Raster to draw 2D shapes into. X, Y are world coordinates (target pixels, y up, origin = anchor).

    c.fill(c.circle(0, 0, 5), "yellow:5", glow=True)
    """

    def __init__(self, size, anchor, ss=4):
        w, h = size
        super().__init__(w * ss, h * ss, ss, anchor)
        self.X, self.Y = self.grid()
        self.layer = 0.0

    def fill(self, mask, colour, glow=False, mat=None, prio=1.0, z=None, part=0, line=True):
        """Paints `colour` where mask is True (or where a distance array is < 0). line=False: no outline/inner
        lines around these pixels (beams, sparks, holograms)."""
        if mask.dtype != bool:
            mask = mask < 0
        c = col(colour)
        self.col[mask] = c
        self.emit[mask] = glow
        self.prio[mask] = prio
        if mat is None and not line:
            mat = "_noline"
        self.mat[mask] = mat_id(mat) if isinstance(mat, str) else (-1 if mat is None else mat)
        self.part[mask] = part
        self.layer += 1
        self.z[mask] = self.layer if z is None else z

    def bands(self, field, cuts, colours, glow=False, prio=1.0, part=0):
        """field >= cuts[i] gets colours[i] (cuts ascending, later = inner/brighter)."""
        for cut, c in zip(cuts, colours):
            g = glow[cuts.index(cut)] if isinstance(glow, (list, tuple)) else glow
            self.fill(field >= cut, c, glow=g, prio=prio, part=part)

    # distance helpers (negative inside)
    def circle(self, x, y, r):
        return np.hypot(self.X - x, self.Y - y) - r

    def ellipse(self, x, y, rx, ry, ang=0.0):
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        u = (self.X - x) * ca + (self.Y - y) * sa
        v = -(self.X - x) * sa + (self.Y - y) * ca
        k = np.hypot(u / rx, v / ry)
        return (k - 1) * min(rx, ry)

    def capsule(self, ax, ay, bx, by, r1, r2=None):
        r2 = r1 if r2 is None else r2
        px, py = self.X - ax, self.Y - ay
        ex, ey = bx - ax, by - ay
        ee = ex * ex + ey * ey
        t = np.clip((px * ex + py * ey) / ee, 0, 1) if ee > 0 else np.zeros_like(px)
        return np.hypot(px - ex * t, py - ey * t) - (r1 + (r2 - r1) * t)

    def rect(self, x0, y0, x1, y1, r=0.0):
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hx, hy = abs(x1 - x0) / 2 - r, abs(y1 - y0) / 2 - r
        qx = np.abs(self.X - cx) - hx
        qy = np.abs(self.Y - cy) - hy
        return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r

    def polygon(self, pts):
        return sd_polygon(pts, self.X, self.Y)

    def star(self, x, y, r_out, r_in, n=4, ang=0.0):
        pts = []
        for i in range(2 * n):
            a = math.radians(ang + 90 + 180.0 * i / n)
            r = r_out if i % 2 == 0 else r_in
            pts.append((x + r * math.cos(a), y + r * math.sin(a)))
        return self.polygon(pts)

    def polar(self, x=0.0, y=0.0):
        dx, dy = self.X - x, self.Y - y
        return np.hypot(dx, dy), np.arctan2(dy, dx)


def vnoise(X, Y, freq=1.0, seed=0):
    """Smooth value noise in [0, 1] at world coordinates."""
    rng = np.random.default_rng(seed)
    perm = rng.random((257, 257))
    x = X * freq + 64.3
    y = Y * freq + 91.7
    xi = np.floor(x).astype(int)
    yi = np.floor(y).astype(int)
    fx = x - xi
    fy = y - yi
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    xi %= 256
    yi %= 256
    a = perm[xi, yi]
    b = perm[xi + 1, yi]
    c = perm[xi, yi + 1]
    d = perm[xi + 1, yi + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(X, Y, freq=1.0, seed=0, octaves=3):
    s = 0.0
    a = 1.0
    tot = 0.0
    for o in range(octaves):
        s = s + a * vnoise(X, Y, freq * (2 ** o), seed + o * 17)
        tot += a
        a *= 0.5
    return s / tot


# --------------------------------------------------------------------------------------------------------------
# Pixelizer


class Sprite:
    """A finished frame: rgba (h, w, 4) uint8 with alpha 0/255, glow likewise; plus index buffers for touch-ups."""

    def __init__(self, col, mat, emit, part=None, z=None):
        self.col = col          # (h, w) palette index or -1
        self.mat = mat
        self.emit = emit
        self.part = part
        self.z = z

    @property
    def h(self):
        return self.col.shape[0]

    @property
    def w(self):
        return self.col.shape[1]

    def rgba(self):
        out = np.zeros((self.h, self.w, 4), np.uint8)
        m = self.col >= 0
        out[m, :3] = PAL[self.col[m]]
        out[m, 3] = 255
        return out

    def glow_rgba(self):
        out = np.zeros((self.h, self.w, 4), np.uint8)
        m = (self.col >= 0) & self.emit
        out[m, :3] = PAL[self.col[m]]
        out[m, 3] = 255
        return out

    def put(self, x, y, colour, glow=False):
        """Sets one pixel (frame pixel coordinates, y down)."""
        if 0 <= x < self.w and 0 <= y < self.h:
            self.col[y, x] = col(colour)
            self.emit[y, x] = glow
            self.mat[y, x] = -1

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return int(self.col[y, x])
        return -1

    def paste(self, other, dx=0, dy=0, under=False):
        """Copies other's opaque pixels (offset dx, dy); under=True only into empty pixels."""
        for y in range(other.h):
            ty = y + dy
            if not 0 <= ty < self.h:
                continue
            for x in range(other.w):
                tx = x + dx
                if 0 <= tx < self.w and other.col[y, x] >= 0 and (not under or self.col[ty, tx] < 0):
                    self.col[ty, tx] = other.col[y, x]
                    self.emit[ty, tx] = other.emit[y, x]
                    self.mat[ty, tx] = other.mat[y, x]
        return self

    def copy(self):
        return Sprite(self.col.copy(), self.mat.copy(), self.emit.copy(),
                      None if self.part is None else self.part.copy(), None if self.z is None else self.z.copy())

    def shifted(self, dx, dy):
        out = Sprite(np.full_like(self.col, -1), np.full_like(self.mat, -1), np.zeros_like(self.emit))
        return out.paste(self, dx, dy)

    def bbox(self):
        ys, xs = np.nonzero(self.col >= 0)
        if len(xs) == 0:
            return None
        return xs.min(), ys.min(), xs.max(), ys.max()


def empty_sprite(w, h):
    return Sprite(np.full((h, w), -1, np.int16), np.full((h, w), -1, np.int16), np.zeros((h, w), bool))


def _shift(a, dy, dx, fill):
    out = np.full_like(a, fill)
    h, w = a.shape[:2]
    ys = slice(max(dy, 0), h + min(dy, 0))
    yd = slice(max(-dy, 0), h + min(-dy, 0))
    xs = slice(max(dx, 0), w + min(dx, 0))
    xd = slice(max(-dx, 0), w + min(-dx, 0))
    out[ys, xs] = a[yd, xd]
    return out


DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def pixelize(R, cov=7, clean=True, inner=True, outline=True, inner_dz=1.0, keep_single=False):
    """Supersampled Raster -> Sprite.

    cov       how many of the ss*ss samples must be covered for a pixel to be opaque (of 16 at ss=4)
    clean     removes isolated pixels (single odd colours, lone pixels, pin holes)
    inner     dark inner lines on the far side of depth steps between different parts
    outline   1 px outline outside the silhouette (materials pick its colour)
    """
    ss = R.ss
    H, W = R.h // ss, R.w // ss

    def blocks(a):
        return a.reshape(H, ss, W, ss).swapaxes(1, 2).reshape(H, W, ss * ss)

    C = blocks(R.col)
    Pw = blocks(R.prio)
    filled = C >= 0
    n_op = filled.sum(-1)
    eq = C[..., :, None] == C[..., None, :]
    score = (eq * Pw[..., None, :]).sum(-1)
    score = np.where(filled, score, -1.0)
    best = score.argmax(-1)[..., None]
    pick = lambda a: np.take_along_axis(blocks(a), best, -1)[..., 0]  # noqa: E731
    thr = cov * (ss * ss) / 16.0
    opaque = n_op >= thr
    col1 = np.where(opaque, pick(R.col), -1).astype(np.int16)
    mat1 = np.where(opaque, pick(R.mat), -1).astype(np.int16)
    part1 = np.where(opaque, pick(R.part), -1).astype(np.int16)
    z1 = np.where(opaque, pick(R.z), -1e9).astype(np.float32)
    emit1 = opaque & pick(R.emit)
    prio1 = np.where(opaque, pick(R.prio), 1.0)

    if clean:
        _despeckle(col1, mat1, part1, z1, emit1, prio1, keep_single)
    if inner:
        _inner_lines(col1, mat1, part1, z1, emit1, inner_dz, R.part_inner)
    if outline:
        _outline(col1, mat1, emit1)
    return Sprite(col1, mat1, emit1, part1, z1)


def _despeckle(col1, mat1, part1, z1, emit1, prio1, keep_single):
    for _ in range(2):
        nb = [_shift(col1, dy, dx, -1) for dy, dx in DIRS4]
        op = col1 >= 0
        n_op = sum((n >= 0).astype(int) for n in nb)
        # lone opaque pixels
        if not keep_single:
            lone = op & (n_op == 0) & (prio1 <= 1.0)
            col1[lone] = -1
            mat1[lone] = -1
            emit1[lone] = False
        # pin holes
        hole = (~op) & (n_op == 4)
        if hole.any():
            nbm = [_shift(mat1, dy, dx, -1) for dy, dx in DIRS4]
            nbz = [_shift(z1, dy, dx, -1e9) for dy, dx in DIRS4]
            nbp = [_shift(part1, dy, dx, -1) for dy, dx in DIRS4]
            nbe = [_shift(emit1, dy, dx, False) for dy, dx in DIRS4]
            col1[hole] = nb[0][hole]
            mat1[hole] = nbm[0][hole]
            z1[hole] = nbz[0][hole]
            part1[hole] = nbp[0][hole]
            emit1[hole] = nbe[0][hole]
        # unique-colour pixels with >= 3 equal neighbours
        op = col1 >= 0
        unique = op.copy()
        for n in nb:
            unique &= n != col1
        for i in range(4):
            cnt = sum((nb[j] == nb[i]).astype(int) for j in range(4))
            sel = unique & (nb[i] >= 0) & (cnt >= 3) & (prio1 <= 1.0)
            if sel.any():
                dy, dx = DIRS4[i]
                col1[sel] = nb[i][sel]
                mat1[sel] = _shift(mat1, dy, dx, -1)[sel]
                emit1[sel] = _shift(emit1, dy, dx, False)[sel]
                unique &= ~sel


def _inner_lines(col1, mat1, part1, z1, emit1, dz, part_inner=None):
    line = np.zeros(col1.shape, bool)
    for dy, dx in DIRS4:
        cq = _shift(col1, dy, dx, -1)
        pq = _shift(part1, dy, dx, -1)
        zq = _shift(z1, dy, dx, -1e9)
        cond = (col1 >= 0) & (cq >= 0) & (pq != part1) & (pq >= 0) & (part1 >= 0) & (z1 < zq - dz)
        if part_inner is not None:
            cond &= part_inner[np.where(part1 >= 0, part1, -1)]
        line |= cond
    if not line.any():
        return
    for m in MAT_LIST:
        sel = line & (mat1 == m.id)
        if sel.any() and m.inner:
            col1[sel] = m.colours[0] if m.style != "emit" else m.colours[0]
            if m.style == "emit":
                emit1[sel] = True
            else:
                emit1[sel] = False


def _outline(col1, mat1, emit1):
    op = col1 >= 0
    out = np.full(col1.shape, -1, np.int16)
    # lit sides first (the pixel above / left of the sprite), dark sides override
    order = [((1, 0), True), ((0, 1), True), ((-1, 0), False), ((0, -1), False)]
    line_of = np.array([m.line for m in MAT_LIST] + [0], np.int16)
    lit_of = np.array([m.line_lit for m in MAT_LIST] + [0], np.int16)
    has_line = np.array([m.outline for m in MAT_LIST] + [True], bool)
    for (dy, dx), lit in order:
        # neighbour at (y+dy, x+dx) is opaque: shift brings it to (y, x)
        nq = _shift(op, -dy, -dx, False)
        mq = _shift(mat1, -dy, -dx, -1)
        sel = (~op) & nq & has_line[mq]
        lut = lit_of if lit else line_of
        out[sel] = lut[mq[sel]]
    m = out >= 0
    col1[m] = out[m]
    mat1[m] = -1
    emit1[m] = False


def outline_sprite(spr, colour="outline", lit=None):
    """Adds a 1 px outline (one colour) around a Sprite (used for hand-drawn frames)."""
    op = spr.col >= 0
    sel = np.zeros_like(op)
    for dy, dx in DIRS4:
        sel |= _shift(op, dy, dx, False)
    sel &= ~op
    spr.col[sel] = col(colour)
    if lit is not None:
        top = (~op) & _shift(op, -1, 0, False)
        spr.col[top & sel] = col(lit)
    spr.emit[sel] = False
    return spr


# --------------------------------------------------------------------------------------------------------------
# Sheets


BG_DARK = (34, 50, 66)
BG_LIGHT = (196, 204, 214)


class Sheet:
    """Collects frames and animations and writes assets/sprites/<name>.png/.txt/_glow.png plus previews."""

    def __init__(self, name, frame, anchor, cols=16, title=""):
        self.name = name
        self.fw, self.fh = frame
        self.anchor = anchor
        self.cols = cols
        self.title = title
        self.frames = []
        self.anims = []
        self.points = []
        self.notes = []

    def point(self, name, dx, dy, note=""):
        self.points.append((name, int(round(dx)), int(round(dy)), note))

    def note(self, text):
        self.notes.append(text)

    def add(self, spr):
        if spr.w != self.fw or spr.h != self.fh:
            raise ValueError(f"{self.name}: frame {spr.w}x{spr.h}, expected {self.fw}x{self.fh}")
        self.frames.append(spr)
        return len(self.frames) - 1

    def anim(self, name, fps, mode, frames, note=""):
        """frames: Sprites (added) or ints (existing frame indices), mixed allowed."""
        idx = [f if isinstance(f, (int, np.integer)) else self.add(f) for f in frames]
        self.anims.append((name, fps, mode, idx, note))
        return idx

    def image(self, glow=False):
        n = len(self.frames)
        cols = min(self.cols, n)
        rows = (n + cols - 1) // cols
        out = np.zeros((rows * self.fh, cols * self.fw, 4), np.uint8)
        for i, f in enumerate(self.frames):
            r, c = divmod(i, cols)
            out[r * self.fh:(r + 1) * self.fh, c * self.fw:(c + 1) * self.fw] = f.glow_rgba() if glow else f.rgba()
        return out

    def text(self):
        lines = [f"# {self.name} -- {self.title}" if self.title else f"# {self.name}",
                 "# generated by tools/sprites/build.py -- do not edit by hand"]
        for n in self.notes:
            lines.append(f"# {n}")
        lines.append(f"frame {self.fw} {self.fh}")
        lines.append(f"anchor {self.anchor[0]} {self.anchor[1]}")
        for name, dx, dy, note in self.points:
            lines.append(f"point {name} {dx} {dy}" + (f"    # {note}" if note else ""))
        for name, fps, mode, idx, note in self.anims:
            if note:
                lines.append(f"# {name}: {note}")
            lines.append(f"anim {name} {fps:g} {mode} " + " ".join(str(i) for i in idx))
        return "\n".join(lines) + "\n"

    def write(self, previews=True):
        ASSETS.mkdir(parents=True, exist_ok=True)
        img = self.image()
        Image.fromarray(img, "RGBA").save(ASSETS / f"{self.name}.png", optimize=True)
        g = self.image(glow=True)
        gp = ASSETS / f"{self.name}_glow.png"
        if g[..., 3].any():
            Image.fromarray(g, "RGBA").save(gp, optimize=True)
        elif gp.exists():
            gp.unlink()
        (ASSETS / f"{self.name}.txt").write_text(self.text(), encoding="utf-8", newline="\n")
        if previews:
            self.previews()
        return check_sheet(self.name)

    # previews ------------------------------------------------------------------------------------------------
    def _frame_img(self, i, bg, scale, glow_over=False):
        f = self.frames[i]
        a = f.rgba()
        im = Image.new("RGB", (self.fw, self.fh), bg)
        im.paste(Image.fromarray(a, "RGBA"), (0, 0), Image.fromarray(a, "RGBA"))
        return im.resize((self.fw * scale, self.fh * scale), Image.NEAREST)

    def contact(self, bg, scale, max_w=1500, page_h=1500):
        """Contact pages: one row group per animation, frames at `scale`, anchor marked."""
        pages = []
        fw, fh = self.fw * scale, self.fh * scale
        per_row = max(1, (max_w - 10) // (fw + 4))
        rows = []
        for name, fps, mode, idx, _ in self.anims:
            for k in range(0, len(idx), per_row):
                rows.append((name if k == 0 else "", fps if k == 0 else None, mode, idx[k:k + per_row]))
        y = 0
        cur = []
        for r in rows:
            hgt = fh + 16
            if y + hgt > page_h and cur:
                pages.append(cur)
                cur, y = [], 0
            cur.append(r)
            y += hgt
        if cur:
            pages.append(cur)
        out = []
        txt = (230, 230, 230) if sum(bg) < 400 else (20, 20, 30)
        for pg in pages:
            W = 10 + per_row * (fw + 4)
            Hh = sum(fh + 16 for _ in pg) + 4
            im = Image.new("RGB", (W, Hh), bg)
            d = ImageDraw.Draw(im)
            y = 2
            for name, fps, mode, idx in pg:
                if name:
                    total = next(len(a[3]) for a in self.anims if a[0] == name)
                    d.text((4, y), f"{name}  {total}f  {fps:g}fps {mode}", fill=txt)
                x = 6
                for i in idx:
                    fr = self._frame_img(i, bg, scale)
                    im.paste(fr, (x, y + 14))
                    ax, ay = self.anchor
                    d.line([(x + ax * scale - 3, y + 14 + ay * scale), (x + ax * scale + 3, y + 14 + ay * scale)],
                           fill=(255, 0, 255))
                    d.text((x + 2, y + 14 + 1), str(i), fill=txt)
                    x += fw + 4
                y += fh + 16
            out.append(im)
        return out

    def previews(self, scale=None):
        WORK.mkdir(parents=True, exist_ok=True)
        for old in WORK.glob(f"{self.name}_*_[0-9]*.png"):
            old.unlink()
        scale = scale or (3 if self.fw <= 64 else 2)
        if self.fw <= 32:
            scale = 5
        self.scene()
        for tag, bg in (("dark", BG_DARK), ("light", BG_LIGHT)):
            for k, im in enumerate(self.contact(bg, scale)):
                im.save(WORK / f"{self.name}_{tag}_{k}.png")
        gdir = WORK / "gif"
        gdir.mkdir(exist_ok=True)
        for name, fps, mode, idx, _ in self.anims:
            ims = [self._frame_img(i, BG_DARK, 4) for i in idx]
            ims[0].save(gdir / f"{self.name}_{name}.gif", save_all=True, append_images=ims[1:],
                        duration=int(round(1000 / fps)), loop=0, disposal=1)
    def scene(self, picks=None, scale=3, per=8):
        """work/sprites/<name>_scene.png: frames at game size on station / jungle / light backdrops, enlarged."""
        picks = picks or [idx[0] for _, _, _, idx, _ in self.anims]
        rows = []
        for k in range(0, len(picks), per):
            sl = [self.frames[i] for i in picks[k:k + per]]
            for kind in ("station", "jungle", "light"):
                rows.append(compose_scene(sl, self.anchor, kind))
        W = max(r.width for r in rows)
        out = Image.new("RGB", (W, sum(r.height for r in rows)), (0, 0, 0))
        y = 0
        for r in rows:
            out.paste(r, (0, y))
            y += r.height
        out.resize((out.width * scale, out.height * scale), Image.NEAREST).save(WORK / f"{self.name}_scene.png")

    def strips(self):
        # 1x and 2x strip of the first frame of every anim (game size check)
        strip = Image.new("RGB", (len(self.anims) * (self.fw + 2) + 2, self.fh + 4), BG_DARK)
        for k, (name, fps, mode, idx, _) in enumerate(self.anims):
            a = self.frames[idx[0]].rgba()
            strip.paste(Image.fromarray(a, "RGBA"), (2 + k * (self.fw + 2), 2), Image.fromarray(a, "RGBA"))
        strip.save(WORK / f"{self.name}_1x.png")
        strip.resize((strip.width * 2, strip.height * 2), Image.NEAREST).save(WORK / f"{self.name}_2x.png")


def mock_background(w, h, kind):
    """A rough level-like backdrop from the palette to judge sprites in context (not an asset)."""
    rng = np.random.default_rng(3)
    img = np.zeros((h, w, 3), np.uint8)
    if kind == "station":
        top, bot = np.array(rgb("blue:2"), float), np.array(rgb("teal:2"), float)
        for y in range(h):
            img[y] = top + (bot - top) * y / h
        for x0 in range(0, w, 32):
            img[:, x0] = rgb("blue:1")
            img[:, x0 + 1] = rgb("blue:3")
        for y0 in range(8, h, 48):
            img[y0, :] = rgb("teal:3")
        for k in range(12):
            x, y = rng.integers(0, w - 6), rng.integers(4, h - 30)
            img[y:y + 2, x:x + 5] = rgb("cyan:5")
        floor = [rgb("steel:6"), rgb("steel:4"), rgb("steel:3"), rgb("steel:3"), rgb("slate:2")]
    elif kind == "jungle":
        top, bot = np.array(rgb("teal:3"), float), np.array(rgb("green:2"), float)
        for y in range(h):
            img[y] = top + (bot - top) * y / h
        X, Y = np.meshgrid(np.arange(w), np.arange(h))
        n = fbm(X.astype(float), Y.astype(float), 0.05, 5)
        img[n > 0.62] = rgb("green:3")
        img[n > 0.7] = rgb("lime:3")
        floor = [rgb("lime:4"), rgb("green:4"), rgb("brown:3"), rgb("brown:2"), rgb("brown:1")]
    else:
        top, bot = np.array(rgb("slate:5"), float), np.array(rgb("steel:6"), float)
        for y in range(h):
            img[y] = top + (bot - top) * y / h
        floor = [rgb("grey:7"), rgb("grey:6"), rgb("grey:5"), rgb("grey:5"), rgb("grey:4")]
    return img, floor


def compose_scene(sprites, anchor, kind, gap=6, ground=None):
    """Sprites side by side at 1x on a mock backdrop, standing on a floor at the anchor line."""
    fw, fh = sprites[0].w, sprites[0].h
    W = len(sprites) * (fw + gap) + gap
    H = fh + 16
    img, floor = mock_background(W, H, kind)
    gy = 8 + (anchor[1] if ground is None else ground)
    for k, c in enumerate(floor):
        img[gy + k] = c
    img[gy + len(floor):] = floor[-1]
    im = Image.fromarray(img)
    for i, s in enumerate(sprites):
        a = Image.fromarray(s.rgba(), "RGBA")
        im.paste(a, (gap + i * (fw + gap), 8), a)
    return im


def check_sheet(name):
    """Validates assets/sprites/<name>.png/.txt against DESIGN.md. Returns a list of problems (empty = fine)."""
    probs = []
    png = ASSETS / f"{name}.png"
    txt = ASSETS / f"{name}.txt"
    im = np.asarray(Image.open(png).convert("RGBA"))
    fw = fh = None
    anchor = None
    anims = {}
    for ln in txt.read_text(encoding="utf-8").splitlines():
        s = ln.split("#")[0].split()
        if not s:
            continue
        if s[0] == "frame":
            fw, fh = int(s[1]), int(s[2])
        elif s[0] == "anchor":
            anchor = (int(s[1]), int(s[2]))
        elif s[0] == "point":
            if len(s) != 4:
                probs.append(f"bad point line: {ln}")
        elif s[0] == "anim":
            if s[3] not in ("loop", "once"):
                probs.append(f"bad mode: {ln}")
            float(s[2])
            if s[1] in anims:
                probs.append(f"duplicate anim {s[1]}")
            anims[s[1]] = [int(v) for v in s[4:]]
        else:
            probs.append(f"unknown line: {ln}")
    if fw is None or anchor is None:
        probs.append("frame/anchor missing")
        return probs
    H, W = im.shape[:2]
    if W % fw or H % fh:
        probs.append(f"png {W}x{H} not a multiple of {fw}x{fh}")
    n = (W // fw) * (H // fh)
    for a, idx in anims.items():
        if not idx:
            probs.append(f"anim {a} empty")
        for i in idx:
            if i < 0 or i >= n:
                probs.append(f"anim {a}: index {i} out of range ({n})")
    al = im[..., 3]
    if not np.isin(al, (0, 255)).all():
        probs.append("alpha not binary")
    pal = {tuple(int(v) for v in c) for c in PAL}
    cols = {tuple(int(v) for v in c) for c in im[al == 255][:, :3].reshape(-1, 3)}
    off = cols - pal
    if off:
        probs.append(f"{len(off)} colours outside the palette")
    gp = ASSETS / f"{name}_glow.png"
    if gp.exists():
        g = np.asarray(Image.open(gp).convert("RGBA"))
        if g.shape != im.shape:
            probs.append("glow size differs")
        if not np.isin(g[..., 3], (0, 255)).all():
            probs.append("glow alpha not binary")
    return probs
