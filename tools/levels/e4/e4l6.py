"""e4l6 -- Neon Labyrinth / Neonlabyrinth (citadel, dark). Teleporters, switches + toggle gates, blinkers.

A maze of 8 x 4 cells (24 x 12 tiles each, walls 2 thick), joined by doorways and girder shafts.
  (0,1) start: switch A (taught) opens gate A to (1,1); a second switch A behind the gate.
  (2,2) teleporters taught: a pad to the sealed rooms (5,0)/(6,0), which hold switch B.
  Gate B (6,1)->(7,1) leads up to (7,0) with switch C; gate C (6,2)->(7,2) is the exit vault.
  A second pair of pads joins the far corners (7,3) and (0,0).
Teleporters are pairs of pads: a sending pad in a corner, an arriving pad (no target) beside it.
Secrets: three fake doorways between cells.
"""
from kit import Map, main

PX, PY = 26, 14          # cell pitch
CW, CH = 24, 12          # cell interior


def build():
    m = Map(216, 63)
    m.key('name', 'Neon Labyrinth')
    m.key('name.de', 'Neonlabyrinth')
    m.key('theme', 'citadel')
    m.key('tint', 1)
    m.key('bg', 'citadel_b')
    m.key('music', 'e4_citadel')
    m.key('dark', 0.45)
    m.key('par', 600)
    T = m.legend('a', 'enemy trooper')
    TL = m.legend('b', 'enemy trooper left')
    TA = m.legend('e', 'enemy trooper ambush')
    BL = m.legend('i', 'enemy blinker')
    BLA = m.legend('j', 'enemy blinker ambush')
    G = m.legend('g', 'enemy gloamhound')
    GL = m.legend('h', 'enemy gloamhound left')
    SB = m.legend('t', 'enemy shieldbot')
    EY = m.legend('z', 'enemy lasereye')
    BR = m.legend('w', 'enemy brute')
    JP = m.legend('y', 'enemy jetpacker')
    m.legend('q', 'switch A')
    m.legend('r', 'switch B')
    m.legend('s', 'switch C')
    m.legend('A', 'toggle A solid')
    m.legend('G', 'toggle B solid')
    m.legend('Z', 'toggle C solid')
    m.legend('1', 'teleport U')        # (2,2) -> (5,0)
    m.legend('2', 'teleport V')        # (5,0) -> (2,2)
    m.legend('3', 'teleport W')        # (7,3) -> (0,0)
    m.legend('4', 'teleport Y')        # (0,0) -> (7,3)
    m.legend('U', 'teleport')          # arriving pads
    m.legend('V', 'teleport')
    m.legend('W', 'teleport')
    m.legend('Y', 'teleport')
    m.legend('n', 'sign sign.e4l6.teleport')
    m.legend('m', 'sign sign.e4l6.switch')
    m.legend('L', 'light magenta 6')
    m.legend('l', 'light cyan 6')
    m.legend('O', 'light violet 6')
    m.legend('o', 'power overdrive')
    m.legend('p', 'power shield')
    m.legend('c', 'treasure crown')
    m.legend('x', 'treasure cube')

    def X0(c):
        return 2 + PX * c

    def Y0(r):
        return 2 + PY * r

    for c in range(8):
        for r in range(4):
            m.room(X0(c), Y0(r), CW, CH)

    def door(c, r, ch='.', secret=False):
        """The doorway east of cell (c, r): 2 x 3 at the floor."""
        x, y = X0(c) + CW, Y0(r) + 9
        if ch == '.':
            m.room(x, y, 2, 3)
            if secret:
                m.box(x, y, 2, 3, '?')
        else:
            m.box(x, y, 2, 3, ch)

    shafts = []

    def shaft(c, r, side):
        """A girder shaft from cell (c, r+1) up to (c, r): a 3-wide hole in the floor, girders alternating."""
        X = X0(c) + (3 if side == 'W' else 16)
        y0 = Y0(r + 1)
        m.room(X + 1, y0 - 2, 3, 2)
        shafts.append((X, y0))

    # ------------------------------------------------------------------ the maze's connections
    for c, r in ((0, 0), (1, 0), (3, 0), (5, 0),
                 (1, 1), (3, 1), (4, 1), (5, 1),
                 (0, 2), (2, 2), (3, 2), (4, 2),
                 (0, 3), (1, 3), (2, 3), (4, 3), (5, 3), (6, 3)):
        door(c, r)
    door(0, 1, 'A')                        # gate A: start -> (1,1)
    door(6, 1, 'G')                        # gate B: (6,1) -> (7,1)
    door(6, 2, 'Z')                        # gate C: (6,2) -> the exit vault (7,2)
    for c, r, side in ((1, 0, 'E'), (2, 0, 'W'), (3, 0, 'E'), (7, 0, 'W'),
                       (1, 1, 'W'), (4, 1, 'W'), (6, 1, 'E'),
                       (0, 2, 'E'), (2, 2, 'E'), (4, 2, 'E'), (5, 2, 'W'), (6, 2, 'W')):
        shaft(c, r, side)

    def P(c, r, lx, ly, ch):
        m.put(X0(c) + lx, Y0(r) + ly, ch)

    def Hl(c, r, lx, ly, w, ch='-'):
        m.hl(X0(c) + lx, Y0(r) + ly, w, ch)

    def Bx(c, r, lx, ly, w, h, ch='%'):
        m.box(X0(c) + lx, Y0(r) + ly, w, h, ch)

    def lights(c, r, a='l', b='L'):
        P(c, r, 5, 2, a)
        P(c, r, 18, 2, b)

    # ------------------------------------------------------------------ row 0
    # (0,0) the west archive: arriving pad from (7,3)
    P(0, 0, 1, 11, '4')
    P(0, 0, 4, 11, 'W')
    Hl(0, 0, 8, 9, 4)
    Hl(0, 0, 12, 6, 4)
    Bx(0, 0, 16, 3, 6, 1)
    P(0, 0, 18, 2, '*')
    P(0, 0, 20, 2, '$')
    P(0, 0, 20, 11, TL)
    P(0, 0, 12, 11, G)
    P(0, 0, 6, 2, 'L')
    P(0, 0, 14, 9, 'l')
    # (1,0) a block with a blinker, spikes at the west door
    Hl(1, 0, 2, 11, 2, '^')
    Bx(1, 0, 7, 9, 6, 3)
    P(1, 0, 9, 8, BL)
    Hl(1, 0, 8, 6, 4)
    P(1, 0, 10, 5, '*')
    P(1, 0, 12, 5, '$')
    P(1, 0, 21, 11, G)
    lights(1, 0, 'l', 'O')
    # (2,0) the high shelves, a laser eye; a fake doorway east
    Hl(2, 0, 11, 9, 4)
    Hl(2, 0, 15, 6, 4)
    Bx(2, 0, 19, 3, 5, 1)
    P(2, 0, 21, 2, '*')
    P(2, 0, 22, 11, EY)
    P(2, 0, 13, 11, '$')
    lights(2, 0, 'L', 'l')
    # (3,0) a plasma pool with a bridge
    Hl(3, 0, 6, 12, 7, '~')
    Hl(3, 0, 7, 9, 5)
    P(3, 0, 9, 8, '*')
    P(3, 0, 13, 11, T)
    P(3, 0, 2, 11, '$')
    P(3, 0, 3, 11, 'x')
    lights(3, 0, 'O', 'L')
    # (4,0) pillars, a jetpacker
    Bx(4, 0, 6, 9, 2, 3)
    Bx(4, 0, 14, 9, 2, 3)
    Hl(4, 0, 8, 6, 6)
    P(4, 0, 11, 5, '*')
    P(4, 0, 18, 6, JP)
    P(4, 0, 20, 11, '+')
    lights(4, 0)
    # (5,0) sealed: arriving pad from (2,2), switch B
    P(5, 0, 1, 11, '2')
    P(5, 0, 4, 11, 'U')
    P(5, 0, 13, 11, 'r')
    Bx(5, 0, 9, 9, 2, 3)
    Hl(5, 0, 15, 8, 4)
    P(5, 0, 17, 7, '*')
    P(5, 0, 20, 11, BLA)
    lights(5, 0, 'L', 'O')
    # (6,0) sealed treasury
    Hl(6, 0, 4, 9, 4)
    Hl(6, 0, 9, 6, 4)
    Hl(6, 0, 14, 3, 4)
    P(6, 0, 16, 2, '*')
    P(6, 0, 11, 5, '$')
    P(6, 0, 6, 8, '$')
    P(6, 0, 20, 11, SB)
    P(6, 0, 22, 11, 'H')
    lights(6, 0, 'O', 'l')
    # (7,0) switch C, a brute
    P(7, 0, 19, 11, 's')
    Bx(7, 0, 12, 10, 3, 2)
    P(7, 0, 13, 9, '*')
    P(7, 0, 22, 11, BR)
    P(7, 0, 10, 4, 'O')
    P(7, 0, 20, 4, 'L')

    # ------------------------------------------------------------------ row 1
    # (0,1) the start: switch A taught, gate A in the east doorway
    P(0, 1, 2, 11, 'P')
    P(0, 1, 9, 11, 'm')
    P(0, 1, 13, 11, 'q')
    Hl(0, 1, 15, 9, 4)
    P(0, 1, 17, 8, '*')
    P(0, 1, 7, 11, '$')
    lights(0, 1, 'l', 'L')
    # (1,1) behind gate A: the second switch A, shafts up (east) and down (west)
    P(1, 1, 1, 11, 'q')
    Bx(1, 1, 10, 10, 3, 2)
    P(1, 1, 11, 9, '*')
    P(1, 1, 14, 11, TL)
    lights(1, 1, 'O', 'l')
    # (2,1) spikes and a hound, shaft up (west)
    Hl(2, 1, 11, 11, 3, '^')
    Hl(2, 1, 10, 8, 5)
    P(2, 1, 12, 7, '*')
    P(2, 1, 19, 11, GL)
    P(2, 1, 22, 11, '&')
    lights(2, 1, 'L', 'l')
    # (3,1) shaft up (east)
    Bx(3, 1, 6, 9, 4, 3)
    Hl(3, 1, 10, 6, 4)
    P(3, 1, 12, 5, '*')
    P(3, 1, 7, 8, T)
    P(3, 1, 22, 11, '$')
    lights(3, 1)
    # (4,1) a blinker
    Hl(4, 1, 12, 9, 5)
    Hl(4, 1, 17, 6, 4)
    P(4, 1, 19, 5, '*')
    P(4, 1, 14, 11, BL)
    P(4, 1, 1, 11, '$')
    lights(4, 1, 'O', 'L')
    # (5,1) a laser eye on a dais
    Bx(5, 1, 16, 11, 5, 1)
    P(5, 1, 18, 10, EY)
    Hl(5, 1, 6, 9, 4)
    Hl(5, 1, 10, 6, 4)
    P(5, 1, 12, 5, '*')
    P(5, 1, 3, 11, '+')
    P(5, 1, 8, 11, TA)
    lights(5, 1, 'l', 'O')
    # (6,1) before gate B, shaft down (east)
    Hl(6, 1, 4, 9, 5)
    P(6, 1, 6, 8, '*')
    P(6, 1, 9, 11, TL)
    P(6, 1, 1, 11, '$')
    lights(6, 1)
    # (7,1) behind gate B, shaft up (west)
    Bx(7, 1, 13, 9, 4, 3)
    Hl(7, 1, 17, 6, 4)
    P(7, 1, 19, 5, '*')
    P(7, 1, 15, 8, TL)
    P(7, 1, 21, 11, BLA)
    lights(7, 1, 'O', 'L')

    # ------------------------------------------------------------------ row 2
    # (0,2) a blinker, shaft down (east)
    Hl(0, 2, 6, 9, 5)
    P(0, 2, 8, 8, '*')
    P(0, 2, 11, 11, BL)
    P(0, 2, 2, 11, '$')
    lights(0, 2, 'L', 'l')
    # (1,2) a hound run, shaft up (west); a fake doorway east
    Hl(1, 2, 12, 9, 4)
    P(1, 2, 13, 8, '*')
    P(1, 2, 18, 11, GL)
    P(1, 2, 22, 11, '$')
    lights(1, 2)
    # (2,2) teleporters taught: a pad to the sealed rooms
    P(2, 2, 1, 11, '1')
    P(2, 2, 4, 11, 'V')
    P(2, 2, 7, 11, 'n')
    P(2, 2, 10, 11, 'C')
    Hl(2, 2, 9, 7, 5)
    Hl(2, 2, 14, 10, 3)
    P(2, 2, 11, 6, '*')
    P(2, 2, 22, 11, '&')
    lights(2, 2, 'O', 'l')
    # (3,2) pillars and spikes
    Bx(3, 2, 7, 9, 2, 3)
    Hl(3, 2, 9, 11, 4, '^')
    Bx(3, 2, 13, 9, 2, 3)
    Hl(3, 2, 9, 7, 4)
    P(3, 2, 10, 6, '*')
    P(3, 2, 19, 11, TL)
    P(3, 2, 3, 11, '$')
    lights(3, 2, 'L', 'O')
    # (4,2) a checkpoint, shafts up (west) and down (east)
    P(4, 2, 11, 11, 'C')
    Hl(4, 2, 9, 8, 4)
    P(4, 2, 10, 7, '*')
    P(4, 2, 1, 11, '+')
    lights(4, 2)
    # (5,2) shieldbot, shaft down (west)
    Bx(5, 2, 13, 10, 6, 2)
    P(5, 2, 15, 9, '*')
    P(5, 2, 20, 11, SB)
    P(5, 2, 11, 11, '$')
    lights(5, 2, 'O', 'L')
    # (6,2) before gate C, shafts up (west... east) and down (west)
    Hl(6, 2, 10, 9, 4)
    Hl(6, 2, 14, 6, 4)
    P(6, 2, 16, 5, '*')
    P(6, 2, 12, 11, T)
    P(6, 2, 22, 11, BLA)
    lights(6, 2, 'l', 'L')
    # (7,2) the exit vault
    P(7, 2, 18, 11, 'E')
    Hl(7, 2, 6, 9, 4)
    P(7, 2, 8, 8, '$')
    P(7, 2, 12, 11, '$')
    P(7, 2, 14, 11, 'c')
    lights(7, 2, 'O', 'L')

    # ------------------------------------------------------------------ row 3
    # (0,3) shaft up (east)
    Bx(0, 3, 5, 10, 4, 2)
    Hl(0, 3, 9, 8, 4)
    P(0, 3, 10, 7, '*')
    P(0, 3, 2, 11, '$')
    P(0, 3, 12, 11, GL)
    lights(0, 3)
    # (1,3) a brute between blocks
    Bx(1, 3, 4, 10, 2, 2)
    Bx(1, 3, 18, 10, 2, 2)
    Hl(1, 3, 9, 8, 6)
    P(1, 3, 11, 7, '*')
    P(1, 3, 12, 11, BR)
    lights(1, 3, 'L', 'O')
    # (2,3) shaft up (east)
    Hl(2, 3, 4, 11, 3, '^')
    Hl(2, 3, 7, 8, 5)
    P(2, 3, 9, 7, '*')
    P(2, 3, 11, 11, BL)
    P(2, 3, 1, 11, '$')
    P(2, 3, 20, 11, TA)
    lights(2, 3, 'O', 'l')
    # (3,3) a laser eye; a fake doorway east
    P(3, 3, 20, 11, EY)
    Bx(3, 3, 10, 10, 2, 2)
    Hl(3, 3, 12, 7, 4)
    P(3, 3, 13, 6, '*')
    P(3, 3, 6, 11, '$')
    lights(3, 3)
    # (4,3) shaft up (east)
    Hl(4, 3, 4, 9, 5)
    P(4, 3, 6, 8, '*')
    P(4, 3, 10, 11, T)
    P(4, 3, 16, 11, BLA)
    P(4, 3, 1, 11, 'o')
    lights(4, 3, 'L', 'O')
    # (5,3) shaft up (west)
    Bx(5, 3, 12, 9, 3, 3)
    Hl(5, 3, 15, 6, 4)
    P(5, 3, 17, 5, '*')
    P(5, 3, 18, 11, TL)
    P(5, 3, 21, 11, '$')
    lights(5, 3)
    # (6,3) a checkpoint, shaft up (west)
    P(6, 3, 12, 11, 'C')
    Hl(6, 3, 14, 8, 4)
    P(6, 3, 16, 7, '*')
    P(6, 3, 21, 11, '&')
    lights(6, 3, 'O', 'l')
    # (7,3) the east pad to the archive
    P(7, 3, 22, 11, '3')
    P(7, 3, 19, 11, 'Y')
    Hl(7, 3, 6, 9, 4)
    Hl(7, 3, 10, 6, 4)
    P(7, 3, 12, 5, '*')
    P(7, 3, 8, 11, GL)
    P(7, 3, 3, 11, '+')
    P(7, 3, 14, 11, BLA)
    lights(7, 3, 'L', 'l')

    # secret 1: a fake floor plate in (1,3) drops into a vault under the maze; a girder leads back up
    Bx(1, 3, 15, 12, 2, 1, 'X')
    m.box(X0(1) + 8, 57, 14, 5, '?')
    m.hl(X0(1) + 15, 59, 2, '-')
    m.row(X0(1) + 9, 61, '$.$.c.$.$')
    # secret 2: a fake wall at the east end of (7,1), a vault in the east wall
    m.box(X0(7) + 24, Y0(1) + 9, 2, 3, 'X')
    m.box(210, Y0(1) + 6, 5, 6, '?')
    m.row(210, Y0(1) + 11, '$x$H')
    # secret 3: a fake floor plate in (5,3), another vault below
    Bx(5, 3, 8, 12, 2, 1, 'X')
    m.box(X0(5) + 2, 57, 14, 5, '?')
    m.hl(X0(5) + 8, 59, 2, '-')
    m.row(X0(5) + 3, 61, '$.$.p.$.$')
    for c, r, lx in ((3, 1, 2), (6, 2, 20), (4, 0, 2), (2, 3, 14)):
        assert m.get(X0(c) + lx, Y0(r) + 11) == '.'
        P(c, r, lx, 11, '&')
    # hanging bulkheads: the maze's ceilings drop in places (only over empty cells, never over pickups)
    def hang(c, r, lx, w, h):
        for yy in range(Y0(r), Y0(r) + h):
            for xx in range(X0(c) + lx, X0(c) + lx + w):
                if m.get(xx, yy) == '.':
                    m.put(xx, yy, '#')

    for c, r, lx, w, h in ((1, 0, 14, 3, 5), (2, 0, 2, 7, 4), (3, 0, 14, 9, 4), (4, 0, 1, 4, 5), (5, 0, 5, 8, 4),
                           (7, 0, 1, 9, 5), (7, 0, 16, 8, 4),
                           (0, 1, 2, 11, 4), (1, 1, 2, 8, 5), (2, 1, 16, 8, 5), (3, 1, 0, 6, 4), (4, 1, 2, 8, 5),
                           (5, 1, 16, 8, 5), (6, 1, 11, 6, 6), (7, 1, 9, 4, 5),
                           (0, 2, 12, 5, 6), (1, 2, 17, 7, 5), (2, 2, 17, 7, 4), (3, 2, 0, 6, 5), (3, 2, 16, 8, 4),
                           (4, 2, 13, 6, 5), (5, 2, 8, 5, 6), (6, 2, 1, 8, 5), (7, 2, 12, 5, 5),
                           (0, 3, 1, 4, 6), (1, 3, 1, 7, 4), (1, 3, 16, 7, 4), (2, 3, 0, 6, 4), (3, 3, 2, 7, 5),
                           (4, 3, 10, 5, 6), (5, 3, 20, 4, 5), (6, 3, 9, 4, 6), (7, 3, 16, 6, 5)):
        hang(c, r, lx, w, h)
    # the shaft girders last (they reach from the lower cell into the wall)
    for X, y0 in shafts:
        for i, dy in enumerate((9, 6, 3, 0)):
            m.hl(X + (0 if i % 2 == 0 else 3), y0 + dy, 2, '-')
    return m


if __name__ == '__main__':
    main(build, 'e4l6')
