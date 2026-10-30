"""Reusable shapes for the backgrounds: ships, lit silhouettes, lights, window strips, skylines, pylons."""
import numpy as np
from PIL import Image, ImageDraw

from bgkit import (Draw, Layer, Noise, band, col, edge, fogged, grow, ladder, mix, ramp_step, shift, stretch, truss,
                   wdx)


def ship_shape(dr, x0, yc, ln, h, rng, facing=1, kind=0):
    """A side-view ship (facing right when facing=1) as polygons in dr. Returns light points {name: (x, y)}."""
    f = facing

    def P(x, y):
        return (x0 + f * x, yc + y)

    top, bot = -h * 0.32, h * 0.30
    if kind == 0:  # liner: long hull, raked nose, bridge
        dr.poly([P(0, top), P(ln * 0.66, top - h * 0.04), P(ln * 0.93, -h * 0.1), P(ln, h * 0.04),
                 P(ln * 0.9, bot * 0.8), P(ln * 0.3, bot), P(0, bot)])
    elif kind == 1:  # freighter: box hull with a cargo spine
        dr.poly([P(0, top), P(ln * 0.8, top), P(ln, -h * 0.05), P(ln, h * 0.12), P(ln * 0.84, bot), P(0, bot)])
        n = int(rng.integers(3, 6))
        cw = ln * 0.6 / n
        for i in range(n):
            cx = ln * 0.12 + i * cw
            dr.rect(min(P(cx, 0)[0], P(cx + cw - 2, 0)[0]), yc + bot - 1, max(P(cx, 0)[0], P(cx + cw - 2, 0)[0]),
                    yc + bot + h * 0.32)
    else:  # corvette: wedge
        dr.poly([P(0, top * 1.2), P(ln * 0.45, top), P(ln, h * 0.02), P(ln * 0.5, bot), P(0, bot * 1.1)])
    # bridge / superstructure
    bx, bw, bh = ln * rng.uniform(0.48, 0.62), ln * rng.uniform(0.12, 0.2), h * rng.uniform(0.28, 0.42)
    dr.poly([P(bx, top + 1), P(bx + bw * 0.12, top - bh), P(bx + bw * 0.85, top - bh), P(bx + bw, top - bh * 0.4),
             P(bx + bw * 1.15, top + 1)])
    # dorsal fin and antenna
    fx = ln * rng.uniform(0.06, 0.16)
    dr.poly([P(fx, top + 1), P(fx + ln * 0.04, top - h * 0.55), P(fx + ln * 0.09, top - h * 0.55),
             P(fx + ln * 0.2, top + 1)])
    ax = bx + bw * 0.5
    dr.line([P(ax, top - bh), P(ax, top - bh - h * 0.35)])
    # engines
    el = ln * rng.uniform(0.07, 0.11)
    ne = int(rng.integers(1, 3))
    eh = (bot - top) / (ne * 1.6)
    for i in range(ne):
        ey = top + (bot - top) * (i + 0.5) / ne
        dr.poly([P(-el, ey - eh * 0.45), P(0, ey - eh * 0.6), P(0, ey + eh * 0.6), P(-el, ey + eh * 0.45)])
    return {"nose": P(ln, h * 0.04), "tail": P(fx + ln * 0.06, top - h * 0.55), "mast": P(ax, top - bh - h * 0.35),
            "eng": [P(-el, top + (bot - top) * (i + 0.5) / ne) for i in range(ne)], "eh": eh, "el": el}


def shade_body(L, m, top, bottom, lad, light_dx=-1, dw=0.4, extra=None):
    """Shades a silhouette lit from the upper left: a vertical value ramp between top and bottom rows, a lighter rim
    on its top / light-facing edges, a darker rim on the shadow side."""
    v = 1 - np.clip((L.Y - top) / max(1, bottom - top), 0, 1)
    v = 0.15 + 0.7 * v
    if extra is not None:
        v = np.clip(v + extra, 0, 0.999)
    idx, dith = band(v, len(lad), dw, None, L.by)
    rim = edge(m, 0, -1) | edge(m, light_dx, 0)
    idx = np.where(rim, np.minimum(idx + 1, len(lad) - 1), idx)
    dark = edge(m, 0, 1) | edge(m, -light_dx, 0)
    idx = np.where(dark & ~rim, np.maximum(idx - 1, 0), idx)
    L.paint(m, idx, lad, dith & ~rim & ~dark)


def light(L, x, y, c, size=1, glint=False):
    """A small emissive light (1 or 2 px, optional cross)."""
    x, y = int(round(x)) % L.w, int(round(y))
    m = np.zeros(L.a.shape, bool)
    for dx in range(size):
        for dy in range(size):
            if 0 <= y + dy < L.h:
                m[y + dy, (x + dx) % L.w] = True
    L.put(m, c, keep=True, glow=True)
    if glint:
        g = np.zeros(L.a.shape, bool)
        for dx, dy in ((-1, 0), (size, 0), (0, -1), (0, size)):
            if 0 <= y + dy < L.h:
                g[y + dy, (x + dx) % L.w] = True
        L.put(g & ~m, ramp_step(col(c), -2), keep=True)


def window_strips(L, mask, rows, rng, cols=("yellow5", "orange5", "yellow6", "ice6"), on=0.6, seg=(6, 30),
                  gap=(4, 40), glow=True):
    """Rows of 1-px lit windows inside mask: rows is a list of per-column y arrays (or ints)."""
    for ry in rows:
        x = int(rng.integers(0, 20))
        while x < L.w:
            n = int(rng.integers(*seg))
            if rng.random() < on:
                c = col(rng.choice(cols))
                for k in range(0, n, 2):
                    xx = (x + k) % L.w
                    yy = int(ry[xx]) if hasattr(ry, "__len__") else int(ry)
                    if 0 <= yy < L.h and mask[yy, xx] and rng.random() < 0.85:
                        L.put(_px(L, xx, yy), c, keep=True, glow=glow)
            x += n + int(rng.integers(*gap))


def _px(L, x, y):
    m = np.zeros(L.a.shape, bool)
    m[int(y), int(x) % L.w] = True
    return m




def skyline(L, rng, base, lad, x0=0, x1=None, hmin=6, hmax=40, wmin=8, wmax=34, gap=(0, 5), height=None,
            win=("yellow5", "orange4"), win_on=0.3, kinds=(0.55, 0.2, 0.12, 0.13), avoid=None, mast_light="red4"):
    """Buildings standing on base (per-column y array), lit from the upper left.

    lad: [shadow, base, lit, rim]. height: optional function x -> 0..1 scaling the heights (districts).
    kinds: probabilities of block, stepped block, dome, mast tower. avoid: function x -> True to leave a gap.
    Paints only above the base line, so the buildings follow the curve of the ground."""
    W = L.w
    x1 = W if x1 is None else x1
    lad = np.asarray(lad, np.uint8)
    above = L.Y < base[None, :]
    x = x0
    while x < x1:
        w = int(rng.integers(wmin, wmax + 1))
        if avoid is not None and avoid(x + w / 2):
            x += w
            continue
        hm = height(x + w / 2) if height is not None else 1.0
        h = int(hmin + (hmax - hmin) * rng.random() ** 1.4 * hm)
        cols = np.arange(x, x + w) % W
        by = int(base[cols].min())
        kind = rng.choice(4, p=kinds)
        m = np.zeros(L.a.shape, bool)
        if kind == 3:
            w = int(rng.integers(3, 7))
            cols = np.arange(x, x + w) % W
            h = int(h * 1.6) + 8
        top = by - h
        m[max(0, top):, cols] = True
        if kind == 1:
            w2 = max(3, int(w * rng.uniform(0.35, 0.6)))
            c2 = np.arange(x + int(rng.integers(0, w - w2 + 1)), x + w) [:w2] % W
            t2 = top - int(h * rng.uniform(0.25, 0.6)) - 2
            m[max(0, t2):, c2] = True
        m &= above
        if kind == 2:
            m[:] = False
            ry = min(h, int(w * 0.55)) + 2
            dxw = wdx(L.X, x + w / 2, W) / (w / 2)
            dyw = (L.Y - by) / ry
            m = (dxw * dxw + dyw * dyw <= 1) & above
            v = np.clip(0.5 - 0.5 * dxw - 0.4 * dyw, 0, 0.999)
            idx, dith = band(v, 3, 0.4, None, L.by)
            L.paint(m, idx + 0, lad[[0, 1, 2]], dith)
            L.put(edge(m, 0, -1) & (dxw < 0.2), lad[3])
        else:
            L.put(m, lad[1])
            colsx = np.zeros(W, bool)
            colsx[cols] = True
            left = m & ~shift(m, -1, 0)
            lw = max(1, w // 4)
            lit = np.zeros_like(m)
            for k in range(lw):
                lit |= shift(left, -k, 0)
            L.put(lit & m, lad[2])
            L.put(edge(m, 0, -1), lad[3])
            L.put(edge(m, 1, 0) & ~edge(m, 0, -1), lad[0])
            # windows: floors 4 px apart, columns 3 px apart, in the unlit face
            if win and w >= 6:
                for fy in range(top + 3, by - 2, 4):
                    if rng.random() > win_on:
                        continue
                    c = col(rng.choice(win))
                    for cx in range(x + lw + 1, x + w - 1, 3):
                        if rng.random() < 0.7 and 0 <= fy < L.h and m[fy, cx % W] and not lit[fy, cx % W]:
                            L.put(_px(L, cx, fy), c, keep=True, glow=True)
            if kind == 3:
                mh = int(rng.integers(6, 16))
                mx = x + w // 2
                mm = np.zeros(L.a.shape, bool)
                mm[max(0, top - mh):max(0, top), mx % W] = True
                L.put(mm, lad[2])
                if mast_light and top - mh - 1 >= 0:
                    light(L, mx, top - mh - 1, mast_light)
        x += w + int(rng.integers(gap[0], gap[1] + 1))


def draw_ship(L, rng, cx, yc, ln, h, kind, facing, lad, accent, wins=("ice6", "yellow6", "cyan5"),
              engine=("cyan6", "cyan5", "cyan3")):
    """A docked ship centred on cx: shaded hull (lad dark to light, 5+), an accent stripe, window rows, engine glow
    and nav lights. Returns its mask."""
    dr = Draw(L.w)
    pts = ship_shape(dr, cx - facing * ln / 2, yc, ln, h, rng, facing, kind)
    m = dr.mask()
    top, bot = yc - h * 0.32, yc + h * 0.3
    v = 1 - np.clip((L.Y - (top - h * 0.5)) / (bot - top + h * 0.5), 0, 1)
    v = np.where(L.Y < top + 2, np.maximum(v, 0.72), v)
    idx, dith = band(np.clip(v * 0.98, 0, 0.999), len(lad), 0.35, [0, 0.2, 0.42, 0.62, 0.8, 1.0][:len(lad) + 1]
                     if len(lad) == 5 else None, L.by)
    rim = edge(m, 0, -1) | edge(m, -1, 0)
    dark = edge(m, 0, 1) | edge(m, 1, 0)
    idx = np.where(rim, np.minimum(idx + 1, len(lad) - 1), idx)
    idx = np.where(dark & ~rim, 0, idx)
    L.paint(m, idx, lad, dith & ~rim & ~dark)
    inner = m & ~grow(rim | dark, 2)
    # panel lines
    pl = inner & (np.abs((L.X - cx) % 21 - 10) < 0.5) & (L.Y > top + 3) & (L.Y < bot - 2)
    L.put(pl, lad[1])
    # accent stripe
    sy = int(yc + h * 0.06)
    xa, xb = sorted([cx - facing * ln * 0.25, cx + facing * ln * 0.3])
    st = inner & (L.Y >= sy) & (L.Y < sy + max(2, h // 18)) & (wdx(L.X, (xa + xb) / 2, L.w) ** 2 < ((xb - xa) / 2) ** 2)
    L.put(st, accent)
    # windows
    for wy in (int(yc - h * 0.14), int(yc - h * 0.14) + 3):
        x = int(min(xa, xb) - ln * 0.15)
        while x < max(xa, xb) + ln * 0.25:
            n = int(rng.integers(4, 14))
            c = col(rng.choice(wins))
            if rng.random() < 0.75:
                for k in range(0, n, 2):
                    xx = (x + k) % L.w
                    if inner[wy, xx] and not st[wy, xx]:
                        L.put(_px(L, xx, wy), c, keep=True, glow=True)
            x += n + int(rng.integers(3, 10))
    # engines
    for ex, ey in pts["eng"]:
        e = pts["eh"] * 0.38
        for k in range(-int(e), int(e) + 1):
            core = abs(k) < e * 0.5
            light(L, ex - facing * 1, ey + k, engine[0] if core else engine[1])
            ln_pl = int(3 + (e - abs(k)) * 1.2)
            for j in range(2, 2 + ln_pl):
                if (j + k) % 2 == 0 or j < 3:
                    light(L, ex - facing * j, ey + k, engine[2] if j > 2 else engine[1])
    light(L, *pts["nose"], "white")
    light(L, *pts["tail"], "red5")
    light(L, *pts["mast"], "green5")
    return m


def plate(L, m, top, bot, lad, light_dx=-1, bands=(0.22, 0.62), dith=True):
    """Shades one hull part (mask m spanning rows top..bot) as a lit box: top rim lad[-1], upper band lad[-2],
    middle lad[-3], lower lad[-4], bottom rim lad[0]; the light-facing side rim one step lighter."""
    lad = np.asarray(lad, np.uint8)
    n = len(lad)
    t = (L.Y - top) / max(1.0, bot - top)
    if dith:
        t = t + (L.by - 0.5) * 0.06
    idx = np.full(L.a.shape, n - 4 if n >= 4 else 0, np.int32)
    idx[t < bands[1]] = n - 3
    idx[t < bands[0]] = n - 2
    plain = np.full(L.a.shape, n - 4 if n >= 4 else 0, np.int32)
    t0 = (L.Y - top) / max(1.0, bot - top)
    plain[t0 < bands[1]] = n - 3
    plain[t0 < bands[0]] = n - 2
    rim = edge(m, 0, -1)
    side = edge(m, light_dx, 0) & ~rim
    dark = (edge(m, 0, 1) | edge(m, -light_dx, 0)) & ~rim
    idx = np.where(side, np.minimum(idx + 1, n - 1), idx)
    idx = np.where(rim, n - 1, idx)
    idx = np.where(dark, 0, idx)
    L.paint(m, idx, lad, (idx != plain) & ~rim & ~side & ~dark)


def ship(L, rng, cx, yc, ln, h, facing, lad, accent=None, wins=("ice6", "yellow6", "cyan5"),
         engine=("cyan6", "cyan5", "cyan3"), kind=None):
    """A side-view starship of separately shaded parts (engine block, hull, nose, superstructure, keel modules,
    fins), centred on (cx, yc), length ln, hull height h. lad: 5+ colours dark to light. Returns its mask."""
    f = facing
    x0 = cx - f * ln / 2
    kind = int(rng.integers(0, 3)) if kind is None else kind

    def P(x, y):
        return (x0 + f * x * ln, yc + y * h)

    parts = []  # (polygon, top row, bottom row)

    def part(pts):
        pp = [P(x, y) for x, y in pts]
        ys = [p[1] for p in pp]
        parts.append((pp, min(ys), max(ys)))

    # fins first (behind)
    part([(0.04, -0.4), (0.12, -0.95), (0.2, -0.95), (0.26, -0.4)])
    if kind != 1:
        part([(0.06, 0.4), (0.14, 0.85), (0.2, 0.85), (0.24, 0.4)])
    # keel modules
    if kind == 1:
        n = int(rng.integers(3, 5))
        for i in range(n):
            a = 0.24 + i * 0.5 / n
            part([(a, 0.38), (a + 0.5 / n - 0.015, 0.38), (a + 0.5 / n - 0.015, 0.78), (a, 0.78)])
    else:
        part([(0.3, 0.4), (0.62, 0.4), (0.58, 0.62), (0.34, 0.62)])
    # engine block
    part([(0.0, -0.5), (0.2, -0.5), (0.2, 0.5), (0.0, 0.5)])
    # main hull
    if kind == 2:
        part([(0.16, -0.4), (0.7, -0.3), (0.7, 0.42), (0.16, 0.42)])
    else:
        part([(0.16, -0.42), (0.74, -0.42), (0.74, 0.42), (0.16, 0.42)])
    # nose
    if kind == 0:
        part([(0.72, -0.42), (0.86, -0.36), (1.0, 0.0), (0.94, 0.3), (0.72, 0.42)])
    elif kind == 1:
        part([(0.72, -0.42), (0.92, -0.42), (1.0, -0.1), (1.0, 0.2), (0.9, 0.42), (0.72, 0.42)])
    else:
        part([(0.68, -0.3), (1.0, 0.06), (0.92, 0.3), (0.68, 0.42)])
    # superstructure
    bx = rng.uniform(0.4, 0.56)
    bw = rng.uniform(0.12, 0.2)
    part([(bx, -0.4), (bx + 0.02, -0.82), (bx + bw * 0.8, -0.82), (bx + bw, -0.58), (bx + bw + 0.04, -0.4)])
    if rng.random() < 0.7:
        b2 = rng.uniform(0.2, 0.32)
        part([(b2, -0.4), (b2, -0.62), (b2 + 0.12, -0.62), (b2 + 0.14, -0.4)])

    full = np.zeros(L.a.shape, bool)
    for pp, top, bot in parts:
        m = Draw(L.w).poly(pp).mask()
        plate(L, m, top, bot, lad)
        full |= m
    # antenna
    ax, ay = P(bx + bw * 0.4, -0.82)
    am = Draw(L.w).line([(ax, ay), (ax, ay - h * 0.5)]).mask()
    L.put(am, lad[2])
    light(L, ax, ay - h * 0.5 - 1, "green5")
    inner = full & ~grow(edge(full, 0, -1) | edge(full, 0, 1) | edge(full, 1, 0) | edge(full, -1, 0), 2)
    # accent stripe on the hull
    if accent is not None:
        sy = int(yc + h * 0.1)
        a, b = sorted([P(0.2, 0)[0], P(0.7, 0)[0]])
        st = inner & (L.Y >= sy) & (L.Y < sy + max(2, int(h // 16))) & (np.abs(wdx(L.X, (a + b) / 2, L.w)) < (b - a) / 2)
        L.put(st, accent)
    # windows
    for wy in (int(yc - h * 0.18), int(yc - h * 0.18) + 3):
        a, b = sorted([P(0.24, 0)[0], P(0.92, 0)[0]])
        x = int(a)
        while x < b:
            n = int(rng.integers(4, 16))
            c = col(rng.choice(wins))
            if rng.random() < 0.7:
                for k in range(0, n, 2):
                    xx = (x + k) % L.w
                    if 0 <= wy < L.h and inner[wy, xx]:
                        L.put(_px(L, xx, wy), c, keep=True, glow=True)
            x += n + int(rng.integers(3, 10))
    # bridge windows
    wx, wy = P(bx + 0.03, -0.72)
    for k in range(int(bw * ln * 0.7)):
        xx = int(wx + f * k)
        if full[int(wy), xx % L.w] and k % 3 != 2:
            L.put(_px(L, xx, wy), "cyan5", keep=True, glow=True)
    # engine nozzles and glow
    for ey in ((-0.25, 0.25) if kind != 2 else (0.0,)):
        ex, eyy = P(0.0, ey)
        e = h * 0.16
        nm = Draw(L.w).poly([(ex, eyy - e), (ex - f * h * 0.14, eyy - e * 1.3), (ex - f * h * 0.14, eyy + e * 1.3),
                             (ex, eyy + e)]).mask()
        plate(L, nm, eyy - e * 1.3, eyy + e * 1.3, lad)
        gx = ex - f * h * 0.14
        for k in range(-int(e), int(e) + 1):
            core = abs(k) < e * 0.5
            light(L, gx - f, eyy + k, engine[0] if core else engine[1])
            for j in range(2, 2 + int(2 + (e - abs(k)) * 0.8)):
                if (j + k) % 2 == 0 or j < 3:
                    light(L, gx - f * j, eyy + k, engine[2] if j > 2 else engine[1])
    nx, ny = P(1.0, 0.0 if kind != 1 else -0.1)
    light(L, nx, ny, "white")
    fx, fy = P(0.16, -0.95)
    light(L, fx, fy - 1, "red5")
    return full


def cone(L, x, y, half_angle, length, cols, density=0.5, direction=90.0, falloff=1.0, mask=None):
    """A dithered light cone from (x, y) (direction in degrees, 90 = down): sparse pixels of cols (inner to outer
    bands) whose coverage fades with distance. Binary alpha, so it reads as haze over whatever is behind."""
    dx = wdx(L.X, x, L.w)
    dy = L.Y - y
    d = np.sqrt(dx * dx + dy * dy)
    ang = np.degrees(np.arctan2(dy, dx)) - direction
    ang = (ang + 180) % 360 - 180
    a = np.abs(ang) / half_angle
    inside = (a < 1) & (d < length) & (d > 1)
    cover = density * (1 - d / length) ** falloff * (1 - a ** 2)
    m = inside & (cover > L.by)
    if mask is not None:
        m &= mask
    n = len(cols)
    ci = np.clip((a * n).astype(np.int32), 0, n - 1)
    L.paint(m, ci, ladder(cols), np.ones(L.a.shape, bool))
    L.glow[m] = False
    return m


def hazard(L, m, c1="yellow4", c2="outline", period=8, slope=1):
    """Diagonal hazard stripes inside mask m."""
    k = ((L.X + L.Y * slope) // (period // 2)).astype(np.int32) % 2 == 0
    L.put(m & k, c1)
    L.put(m & ~k, c2)


def lamp_row(L, y, x0, x1, step, c="yellow6", size=2):
    for x in range(int(x0), int(x1), int(step)):
        light(L, x, y, c, size=size)


def local(L, x0, y0, w, h):
    """Index helpers for a local box (x wraps): returns (ys, xs, Yl, Xl) with local float grids."""
    y0, y1 = max(0, int(y0)), min(L.h, int(y0 + h))
    xs = np.arange(int(x0), int(x0 + w)) % L.w
    Yl, Xl = np.mgrid[y0:y1, int(x0):int(x0 + w)].astype(np.float32)
    return slice(y0, y1), xs, Yl, Xl


def stamp(L, ys, xs, m, rgb, keep=None, glow=None):
    """Writes local colours (h, w, 3) where local mask m is set."""
    sub = L.rgb[ys][:, xs]
    sub[m] = rgb[m]
    L.rgb[ys, xs] = sub
    a = L.a[ys][:, xs]
    a[m] = True
    L.a[ys, xs] = a
    k = L.keep[ys][:, xs]
    k[m] = False if keep is None else keep[m]
    L.keep[ys, xs] = k
    g = L.glow[ys][:, xs]
    g[m] = False if glow is None else glow[m]
    L.glow[ys, xs] = g


def rock(L, rng, cx, cy, r, lad, light_dir=(-0.7, -0.7), rim=None, rim_dir=(1.0, 0.0), squash=1.0, jag=0.35,
         craters=3, angle=0.0, n=11):
    """An asteroid / debris rock: a jagged polygon shaded by a fake normal (light from light_dir), optional rim
    light colour on the side facing rim_dir, a few craters. lad: dark to light (4+)."""
    R = r * (1 + jag) + 2
    ys, xs, Yl, Xl = local(L, cx - R, cy - R, 2 * R + 1, 2 * R + 1)
    if Yl.size == 0:
        return
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False) + rng.uniform(0, 1)
    rad = r * (1 + rng.uniform(-jag, jag * 0.6, n))
    pts = [(cx + np.cos(a + angle) * rr, cy + np.sin(a + angle) * rr * squash) for a, rr in zip(ang, rad)]
    img = Image.new("L", (Xl.shape[1], Xl.shape[0]), 0)
    ImageDraw.Draw(img).polygon([(x - Xl[0, 0], y - Yl[0, 0]) for x, y in pts], fill=255)
    m = np.asarray(img) > 127
    dx, dy = (Xl - cx) / r, (Yl - cy) / (r * squash)
    nz = np.sqrt(np.clip(1 - 0.6 * (dx * dx + dy * dy), 0, 1))
    ld = np.array([light_dir[0], light_dir[1], 0.8])
    ld /= np.linalg.norm(ld)
    v = np.clip(dx * ld[0] * 0.7 + dy * ld[1] * 0.7 + nz * ld[2], 0, 1)
    tex = Noise(64, 4, rng, 3)(Xl * 2, Yl * 2)
    v = np.clip(v * 0.85 + (tex - 0.5) * 0.3, 0, 0.999)
    for _ in range(craters if r > 6 else 0):
        ccx, ccy, cr = cx + rng.uniform(-0.5, 0.5) * r, cy + rng.uniform(-0.5, 0.5) * r * squash, rng.uniform(1.2, r * 0.25)
        dd = ((Xl - ccx) ** 2 + ((Yl - ccy) / 0.7) ** 2) / (cr * cr)
        v = np.where(dd < 1, v * 0.55, v)
        v = np.where((dd >= 1) & (dd < 1.6) & (Yl > ccy), np.minimum(0.999, v * 1.25), v)
    by = L.by[ys][:, xs]
    idx = np.clip(np.floor(v * len(lad) + (by - 0.5) * 0.4), 0, len(lad) - 1).astype(np.int32)
    lad = np.asarray(lad, np.uint8)
    rgb = lad[idx]
    # outline edges: dark bottom-right, rim on the rim side
    def e(dx_, dy_):
        p = np.pad(m, 1)
        return m & ~p[1 + dy_:1 + dy_ + m.shape[0], 1 + dx_:1 + dx_ + m.shape[1]]
    dark = e(1, 1) | e(0, 1)
    rgb[dark] = lad[0]
    if rim is not None:
        rd = e(int(np.sign(rim_dir[0])), int(np.sign(rim_dir[1])))
        rgb[rd] = col(rim)
    stamp(L, ys, xs, m, rgb, keep=(idx != np.clip(np.floor(v * len(lad)), 0, len(lad) - 1)) & ~dark)
    return m


def mesa_profile(w, rng, base, mesas, noise_amp=3.0):
    """Skyline of flat-topped buttes: mesas = [(cx, half_width, height, cliff, talus)], all wrapped in x. The tops
    get small notches and bumps, the shoulders round off, the cliffs have a ledge, the talus is concave.
    Returns (top y per column, index of the owning mesa per column, signed distance from its centre)."""
    xs = np.arange(w, dtype=np.float32)
    top = np.full(w, float(base))
    owner = np.full(w, -1, np.int32)
    rel = np.zeros(w, np.float32)
    nz = Noise(w, 40, rng, 3, 0.6)(xs, np.full_like(xs, 11.0)) - 0.5
    for i, (cx, hw, h, cliff, talus) in enumerate(mesas):
        d = wdx(xs, cx, w)
        t = np.abs(d)
        ledge = rng.uniform(0.35, 0.6)
        sh = min(6.0, hw * 0.15)
        y_top = base - h + np.clip((t - (hw - sh)) / sh, 0, 1) ** 2 * 3 + nz * 2 * noise_amp * 0.5
        u = np.clip((t - hw) / cliff, 0, 1)                       # 0..1 down the cliff, with a ledge
        drop = np.where(u < 0.45, u / 0.45 * ledge, np.where(u < 0.6, ledge, ledge + (u - 0.6) / 0.4 * (1 - ledge)))
        y_cliff = base - h + drop * h * 0.66
        v = np.clip((t - hw - cliff) / max(1, talus), 0, 1)
        y_talus = base - h * 0.34 * (1 - v) ** 2
        y = np.where(t <= hw, y_top, np.where(t <= hw + cliff, y_cliff, y_talus)) + nz * noise_amp * (t > hw)
        better = y < top
        top = np.where(better, y, top)
        owner = np.where(better, i, owner)
        rel = np.where(better, d, rel)
    return top, owner, rel


def paint_mesas(L, top, owner, rel, mesas, lad, strata=None, mask=None, seed=7, base=None):
    """Shades a mesa skyline as broad value shapes: the cliff facing the light (left) lit, the front face in two
    tones darkening downwards, the right cliff in shadow; a lit top edge, thin vertical weathering streaks from
    the top, two thin dithered strata per mesa. lad: [shadow, dark, body, lit, rim]."""
    lad = np.asarray(lad, np.uint8)
    rng = np.random.default_rng(seed)
    body = L.Y >= top[None, :]
    if mask is not None:
        body &= mask
    hs = np.array([m[2] for m in mesas] + [1], np.float32)
    hw = np.array([m[1] for m in mesas] + [1], np.float32)[owner]
    ptop = (np.max(top) if base is None else base) - hs[owner]          # plateau level per column
    t = np.abs(rel) / np.maximum(hw, 1)
    left = (rel < 0)[None, :] & np.ones_like(body)
    face = (t > 0.97)[None, :] & np.ones_like(body)
    depth = L.Y - top[None, :]
    rd = (L.Y - ptop[None, :]) / np.maximum(1, hs[owner][None, :])     # 0 at the plateau .. 1 at the base
    v = 0.75 - rd * 0.5 + (L.by - 0.5) * 0.12
    idx = np.where(v > 0.5, 2, 1)
    idx = np.where(face & left, 3, idx)
    idx = np.where(face & ~left, 0, idx)
    idx = np.where((depth < 3) & ~(face & ~left), 3, idx)
    # thin weathering streaks hanging from the top
    sx = rng.random(L.w) < 0.16
    sl = rng.uniform(6, 46, L.w)
    streak = sx[None, :] & (depth > 2) & (depth < sl[None, :]) & ~face
    idx = np.where(streak, np.maximum(idx - 1, 0), idx)
    # two thin strata per mesa at random relative heights
    s1 = np.array([rng.uniform(0.25, 0.45) for _ in mesas] + [9], np.float32)[owner]
    s2 = np.array([rng.uniform(0.55, 0.75) for _ in mesas] + [9], np.float32)[owner]
    hh = np.maximum(1, hs[owner])[None, :]
    st = ((np.abs(rd - s1[None, :]) * hh < 0.8) | (np.abs(rd - s2[None, :]) * hh < 0.8)) &          ((L.X.astype(np.int32) + L.Y.astype(np.int32)) % 3 != 0) & ~(face & ~left)
    idx = np.where(st, np.maximum(idx - 1, 0), idx)
    rim = body & ~shift(body, 0, -1)
    L.paint(body, idx, lad[:4], (v > 0.5) != ((0.75 - rd * 0.5) > 0.5))
    L.put(rim & ~(face & ~left), lad[4])
    return body


def crowns(w, rng, base, n, rmin, rmax, jitter=6):
    """A bumpy canopy line: the top y per column of n overlapping round crowns along a base line."""
    xs = np.arange(w, dtype=np.float32)
    top = np.full(w, float(base) + rmax)
    for i in range(n):
        cx = (i + rng.uniform(-0.4, 0.4)) * w / n
        r = rng.uniform(rmin, rmax)
        cy = base + rng.uniform(-jitter, jitter)
        d = wdx(xs, cx, w)
        y = np.where(np.abs(d) < r, cy - np.sqrt(np.clip(r * r - d * d, 0, None)) * 0.8, 1e9)
        top = np.minimum(top, y)
    return top


def column_profile(L, cx, width, rng, bulge=0.4, cells=4, flare=1.8, top_flare_y=40, bot_flare_y=340, ret_u=False):
    """An organic column's mask: a vertical body whose half width wobbles with y and flares at the ceiling and
    floor. ret_u: also return u, the horizontal position inside the column (-1 left edge .. 1 right edge)."""
    n = Noise(256, cells, rng, 3)
    y = L.Y[:, 0]
    hwid = width / 2 * (1 + bulge * (n(np.full_like(y, 30.0), y) - 0.5) * 2)
    hwid = hwid * (1 + flare * np.clip((top_flare_y - y) / top_flare_y, 0, 1) ** 2
                   + flare * np.clip((y - bot_flare_y) / (L.h - bot_flare_y), 0, 1) ** 2)
    sway = (n(np.full_like(y, 90.0), y * 0.5) - 0.5) * width * 0.8
    u = (wdx(L.X, cx, L.w) - sway[:, None]) / np.maximum(1.0, hwid[:, None])
    m = np.abs(u) <= 1
    return (m, u) if ret_u else m


def blob(L, cx, cy, rx, ry):
    dx = wdx(L.X, cx, L.w) / rx
    dy = (L.Y - cy) / ry
    return dx * dx + dy * dy <= 1.0


def peaks_profile(w, rng, base, peaks, rough=2.0):
    """A jagged skyline of sharp peaks [(cx, height, half_width)] (wrapped), each with its own left / right slope
    and a notch or shoulder: returns (top y per column, signed distance from the owning peak, its half width)."""
    xs = np.arange(w, dtype=np.float32)
    top = np.full(w, float(base))
    rel = np.zeros(w, np.float32)
    hw_ = np.ones(w, np.float32)
    nz = (Noise(w, 60, rng, 2)(xs, np.full_like(xs, 3.0)) - 0.5) * 2 * rough
    for cx, h, hw in peaks:
        d = wdx(xs, cx, w)
        sl, sr = rng.uniform(0.6, 1.4), rng.uniform(0.6, 1.4)
        y = base - h + np.where(d < 0, -d / (hw * sl), d / (hw * sr)) * h
        sd = rng.uniform(0.3, 0.6) * hw * (1 if rng.random() < 0.5 else -1)
        y2 = base - h * rng.uniform(0.55, 0.8) + np.abs(d - sd) / (hw * 0.5) * h
        y = np.minimum(y, y2) + nz
        better = y < top
        top = np.where(better, y, top)
        rel = np.where(better, d, rel)
        hw_ = np.where(better, hw, hw_)
    return top, rel, hw_


def paint_peaks(L, top, rel, hw, lad, cracks=True, rng=None, mask_extra=None):
    """Shades a peak skyline: the face left of each summit lit (its upper part brightest), the right one in
    shadow with a faint reflected band low down, split by a wandering ridge line; a bright rim on the lit edges,
    crack lines. lad: [shadow, mid, lit, rim]."""
    lad = np.asarray(lad, np.uint8)
    body = L.Y >= top[None, :]
    if mask_extra is not None:
        body &= mask_extra
    depth = L.Y - top[None, :]
    rr = rel[None, :] + depth * 0.35 * np.sin(depth / 13 + rel[None, :] * 0.07)
    lit = rr < 0
    ll = depth + (L.by - 0.5) * 8
    idx = np.where(lit, np.where(ll < 26, 2, 1), np.where(ll > 70, 1, 0))
    idx = np.where(lit & (ll > 90), 0, idx)
    L.paint(body, idx, lad[:3], (idx != np.where(lit, np.where(depth < 26, 2, 1), np.where(depth > 70, 1, 0))))
    L.put(edge(body, 0, -1) & lit, lad[3])
    L.put(edge(body, -1, 0) & lit & ~edge(body, 0, -1), lad[3])
    if cracks and rng is not None:
        cr = (Noise(L.w, L.w // 10, rng, 2)(L.X + L.Y * 0.6, L.Y * 0.2) > 0.74) & body & (depth > 4)
        cr &= ((L.X.astype(np.int32) + L.Y.astype(np.int32)) % 3 == 0)
        L.put(cr & lit, lad[1])
        L.put(cr & ~lit, lad[1])
    return body


def mirror(L, y_water, ripple=None, darken=None, mask=None, src=None):
    """Reflects the layer above the waterline into the rows below it: row y_water + k takes row y_water - k,
    shifted sideways by ripple(k) px; darken maps colours (rgb -> rgb) for the reflection. src: optional mask of
    the pixels that reflect (others leave the water as it is)."""
    out_rgb = L.rgb.copy()
    out_a = L.a.copy()
    srcm = L.a if src is None else (L.a & src)
    changed = np.zeros(L.a.shape, bool)
    for k in range(1, L.h - y_water):
        src_y = y_water - k
        dst = y_water + k - 1
        if src_y < 0 or dst >= L.h:
            break
        sh = 0 if ripple is None else int(ripple(k))
        row_rgb = np.roll(L.rgb[src_y], sh, axis=0)
        row_a = np.roll(srcm[src_y], sh)
        m = row_a if mask is None else row_a & mask[dst]
        out_rgb[dst][m] = row_rgb[m]
        out_a[dst] |= m
        changed[dst] |= m
    if darken is not None:
        below = (L.Y >= y_water) & changed
        keys = out_rgb[below]
        uniq, inv = np.unique(keys, axis=0, return_inverse=True)
        new = np.array([darken(tuple(u)) for u in uniq], np.uint8)
        out_rgb[below] = new[inv.ravel()]
    below = (L.Y >= y_water) & changed
    L.rgb[below] = out_rgb[below]
    L.a[below] = out_a[below]
    L.keep[below] = True
    L.glow[below] = False


def crystal(L, x, y, h, w, ang, lad, glow_core=None, tip=None, keep=True):
    """A hexagonal crystal prism standing at (x, y), height h, width w, tilted ang degrees from vertical: three
    facets (lit left, mid, dark right), a pointed tip, bright edges, an optional glowing core line.
    lad: [dark, mid, lit, edge]. Returns its mask."""
    a = np.radians(ang)
    dvec = np.array([np.sin(a), -np.cos(a)])
    pvec = np.array([np.cos(a), np.sin(a)])
    R = h + w
    ys, xs, Yl, Xl = local(L, x - R, y - R, 2 * R + 1, 2 * R + 1)
    if Yl.size == 0:
        return None
    rx, ry = Xl - x, Yl - y
    along = rx * dvec[0] + ry * dvec[1]
    across = rx * pvec[0] + ry * pvec[1]
    tip = tip if tip is not None else w * 0.9
    hw = np.where(along < h - tip, w / 2, w / 2 * np.clip((h - along) / tip, 0, 1))
    m = (along >= -2) & (along <= h) & (np.abs(across) <= hw)
    u = across / np.maximum(0.5, hw)
    lad = np.asarray(lad, np.uint8)
    idx = np.where(u < -0.3, 2, np.where(u < 0.35, 1, 0)).astype(np.int32)
    rgb = lad[idx]
    p = np.pad(m, 1)
    def e(dx_, dy_):
        return m & ~p[1 + dy_:1 + dy_ + m.shape[0], 1 + dx_:1 + dx_ + m.shape[1]]
    ed = e(-1, 0) | e(0, -1)
    seam = (np.abs(u + 0.3) < 0.5 / np.maximum(0.5, hw) * 1.0) | (np.abs(u - 0.35) < 0.5 / np.maximum(0.5, hw))
    rgb[seam & m] = lad[3] if w > 7 else rgb[seam & m]
    rgb[ed] = lad[3]
    tipline = m & (np.abs(along - (h - tip)) < 0.6) & (w > 9)
    rgb[tipline] = lad[2]
    g = np.zeros_like(m)
    if glow_core is not None and w >= 6:
        core = m & (np.abs(across + w * 0.08) < 0.6) & (along > 3) & (along < h - tip * 0.6)
        rgb[core] = col(glow_core)
        g = core | ed
    stamp(L, ys, xs, m, rgb, keep=np.full(m.shape, keep), glow=g)
    full = np.zeros(L.a.shape, bool)
    sub = full[ys][:, xs]
    sub[m] = True
    full[ys, xs] = sub
    return full


def crystal_cluster(L, rng, x, y, size, lad, n=5, spread=60.0, glow_core=None):
    """A cluster of crystals fanning out from (x, y)."""
    out = np.zeros(L.a.shape, bool)
    order = sorted(range(n), key=lambda k: -abs(k - n // 2))
    for k in order:
        t = (k - (n - 1) / 2) / max(1, (n - 1) / 2)
        ang = t * spread / 2 + rng.uniform(-8, 8)
        h = size * (1 - 0.55 * abs(t)) * rng.uniform(0.8, 1.1)
        w = max(3, h * rng.uniform(0.2, 0.3))
        m = crystal(L, x + t * size * 0.15, y, h, w, ang, lad, glow_core)
        if m is not None:
            out |= m
    return out
