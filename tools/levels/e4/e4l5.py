"""e4l5 -- Engine Cathedral / Maschinenkathedrale (foundry). Movers over lava, the seeker, jetpackers.

The nave (x60-140, y4-84) is a great hall over a lava floor, crossed three times on movers between engine
pistons (bottom) and floating engine pods (middle, top).
  Crypt (start, bottom west): tombs, the first mover over a lava pit (taught), the seeker on an altar, the first
  jetpackers in the crypt's tall east hall.
  Bottom crossing (row 77) west -> east into the east aisle: a long floor, a lift and a girder climb to its gallery.
  Middle crossing (row 52) east -> west into the west aisle: chapels below, a climb to the blue key at the top.
  Top crossing (row 26) west -> east into the spire: the blue door, the exit hall.
Secrets: a chapel behind a fake wall (west aisle), a crawlway behind a fake wall over the crypt hall, a chamber
inside the second piston (fake plate in its side, reached from the mover).
"""
from kit import Map, main


def put_free(m, x, y, ch):
    assert m.get(x, y) == '.', (x, y, m.get(x, y))
    m.put(x, y, ch)


def build():
    m = Map(200, 88)
    m.key('name', 'Engine Cathedral')
    m.key('name.de', 'Maschinenkathedrale')
    m.key('theme', 'foundry')
    m.key('tint', 3)
    m.key('bg', 'foundry_b')
    m.key('music', 'e4_foundry')
    m.key('dark', 0.3)
    m.key('par', 560)
    T = m.legend('a', 'enemy trooper')
    TL = m.legend('b', 'enemy trooper left')
    TA = m.legend('e', 'enemy trooper ambush')
    G = m.legend('g', 'enemy gloamhound')
    GL = m.legend('h', 'enemy gloamhound left')
    J = m.legend('j', 'enemy jetpacker')
    JA = m.legend('y', 'enemy jetpacker ambush')
    BR = m.legend('q', 'enemy brute')
    SB = m.legend('r', 'enemy shieldbot')
    m.legend('w', 'weapon seeker')
    m.legend('n', 'sign sign.e4l5.mover')
    m.legend('t', 'sign sign.e4l5.seeker')
    m.legend('L', 'light orange 8')
    m.legend('l', 'light warm 5')
    m.legend('o', 'power overdrive')
    m.legend('p', 'power shield')
    m.legend('i', 'treasure idol')
    m.legend('x', 'treasure cube')
    mv = {}
    for ch, spec in (('1', '6 0 50 1.0'),             # the taught one in the crypt
                     ('2', '8 0 70'), ('3', '9 0 70'), ('4', '8 0 75'), ('5', '8 0 75'),
                     ('6', '0 -25 80 1.0'),           # the east aisle lift
                     ('7', '10 0 80'), ('8', '12 -4 80'), ('9', '9 0 80'), ('A', '13 0 85'),
                     ('G', '6 0 80'), ('I', '12 0 85'), ('J', '12 -4 85'), ('M', '14 0 90')):
        mv[ch] = m.legend(ch, 'mover ' + spec)

    # ================================================================ all rooms first (details are drawn into them)
    m.room(2, 72, 58, 12)
    m.room(44, 64, 16, 8)                  # the tall east hall
    m.room(142, 30, 56, 47)
    m.room(141, 73, 1, 4)                  # doorway from the bottom crossing
    m.room(141, 48, 1, 4)                  # doorway from the middle crossing
    m.room(2, 6, 57, 55)
    m.room(59, 48, 1, 4)                   # doorway to the middle crossing
    m.room(59, 22, 1, 4)                   # doorway to the top crossing
    m.room(142, 2, 56, 24)
    m.room(141, 21, 1, 3)                  # doorway from the top crossing
    # ================================================================ the nave (x60-140, y4-84), lava below
    m.room(60, 4, 81, 81)
    m.sky(64, 5, 18, 12)                   # rose windows onto the burning planet
    m.sky(90, 5, 22, 10)
    m.sky(120, 5, 18, 12)
    m.vl(100, 5, 10, '#')
    m.box(60, 81, 81, 4, '~')
    # the great engine core hanging in the nave between the top and the middle crossing, turbines lower down,
    # buttresses on the walls (scenery: out of every jump's reach)
    m.stamp(90, 31, '''
,,,,%%%%%%%%%%,,,,
,,%%%%%%%%%%%%%%,,
%%%%%%~~~~~~%%%%%%
%%%%%~~~~~~~~%%%%%
%%%%%%~~~~~~%%%%%%
,,%%%%%%%%%%%%%%,,
,,,,%%%%%%%%%%,,,,
''')
    m.vl(98, 38, 3, '%')
    m.vl(99, 38, 3, '%')
    for x in (66, 128):
        m.box(x, 60, 6, 2, '%')
        m.box(x + 1, 62, 4, 3, '%')
        m.box(x + 2, 65, 2, 2, '#')
    for y in (33, 62):
        m.box(60, y, 3, 2, '#')
        m.box(60, y + 2, 2, 2, '#')
        m.box(138, y, 3, 2, '#')
        m.box(139, y + 2, 2, 2, '#')
    m.put(99, 42, 'L')
    # bottom crossing (platform row 77): pistons rising from the lava
    m.box(56, 77, 5, 8, '#')               # the crypt's ledge
    m.put(58, 76, 'C')
    m.hl(62, 77, 3, mv['2'])               # -> x70-72
    m.box(74, 77, 4, 8, '#')               # piston 1
    m.hl(79, 77, 3, mv['3'])               # -> x88-90
    m.box(92, 74, 4, 11, '#')              # piston 2
    m.hl(97, 74, 3, mv['4'])               # -> x105-107
    m.box(109, 74, 4, 11, '#')             # piston 3
    m.hl(114, 77, 3, mv['5'])              # -> x122-124
    m.box(126, 77, 6, 8, '#')              # piston 4
    m.box(135, 77, 6, 8, '#')              # the east aisle's ledge
    m.put(76, 72, '*')
    m.put(101, 70, '*')
    m.put(120, 73, '*')
    m.put(110, 73, '$')
    m.put(129, 76, '$')
    m.row(65, 74, '$.$')
    m.row(83, 74, '$.$')
    m.row(117, 74, '$.$')
    m.put(138, 76, '+')
    m.put(84, 66, J)
    m.put(118, 64, J)
    m.put(76, 76, 'l')
    m.put(110, 69, 'L')
    m.put(130, 70, 'l')
    # secret 3: a chamber inside piston 2, a fake plate in its side (hop in from the mover)
    m.box(92, 75, 1, 2, 'X')
    m.box(93, 75, 3, 2, '?')
    m.row(93, 76, 'x$o')
    # middle crossing (platform row 52): floating engine pods
    m.box(122, 50, 5, 4, '%')              # pod M1 (top 50)
    m.hl(128, 52, 3, mv['7'])              # -> x138-140, beside the east gallery
    m.box(100, 54, 5, 4, '%')              # pod M2 (top 54)
    m.hl(106, 54, 3, mv['8'])              # diagonal -> x118-120, row 50
    m.box(80, 50, 5, 4, '%')               # pod M3 (top 50)
    m.hl(86, 52, 3, mv['9'])               # -> x95-97
    m.hl(63, 52, 3, mv['A'])               # -> x76-78
    m.box(55, 52, 6, 1, '%')               # west ledge
    m.put(124, 49, '*')
    m.put(92, 47, '*')
    m.put(70, 48, '*')
    m.put(102, 53, '$')
    m.put(82, 49, '$')
    m.row(66, 49, '$.$')
    m.row(89, 49, '$.$')
    m.row(130, 49, '$.$')
    m.put(110, 44, J)
    m.put(74, 42, JA)
    m.put(124, 46, 'L')
    m.put(82, 46, 'L')
    # top crossing (platform row 26), west -> east
    m.box(54, 26, 7, 1, '%')               # west ledge
    m.hl(62, 26, 3, mv['G'])               # -> x68-70
    m.box(72, 24, 4, 3, '%')               # pod T1 (top 24)
    m.hl(77, 26, 3, mv['I'])               # -> x89-91
    m.box(93, 28, 4, 3, '%')               # pod T2 (top 28)
    m.hl(98, 28, 3, mv['J'])               # diagonal -> x110-112, row 24
    m.box(114, 24, 4, 3, '%')              # pod T3 (top 24)
    m.hl(119, 24, 3, mv['M'])              # -> x133-135
    m.box(136, 24, 5, 1, '%')              # east ledge
    m.put(73, 23, '*')
    m.put(84, 21, '*')
    m.put(115, 23, '*')
    m.put(95, 27, '$')
    m.put(104, 22, '$')
    m.row(64, 23, '$.$')
    m.row(80, 23, '$.$')
    m.row(124, 21, '$.$.$')
    m.put(88, 18, J)
    m.put(126, 19, J)
    m.put(94, 25, 'L')
    m.put(116, 20, 'l')

    # ================================================================ crypt (start; x2-59, y72-83, floor 84)
    m.put(4, 83, 'P')
    m.box(10, 81, 4, 3, '%')               # tombs
    m.put(11, 80, '$')
    m.box(17, 82, 3, 2, '%')
    m.put(18, 81, '*')
    m.put(23, 83, 'n')
    m.box(26, 84, 10, 2, '~')              # the lava pit with the first mover
    m.hl(27, 84, 3, mv['1'])               # -> x33-35
    m.put(31, 80, '*')
    m.put(38, 83, 't')
    m.put(40, 83, '%')
    m.put(40, 82, 'w')
    m.put(7, 76, 'l')
    m.put(24, 76, 'L')
    m.put(40, 77, 'l')
    # the tall east hall: jetpackers, girders up, steps to the nave ledge
    m.put(49, 67, J)
    m.put(48, 70, J)
    m.box(48, 81, 3, 3, '%')
    m.box(51, 79, 5, 5, '%')
    m.put(53, 78, '&')
    m.put(46, 83, '+')
    for x, y, w in ((44, 78, 4), (49, 75, 4), (44, 72, 4), (49, 69, 4), (44, 66, 5)):
        m.hl(x, y, w, '-')
    m.put(51, 68, '*')
    m.put(46, 71, '$')
    m.put(56, 66, 'L')
    # secret 2: a crawlway behind a fake wall at the top of the hall
    m.box(43, 64, 1, 2, 'X')
    m.box(30, 64, 13, 2, '?')
    m.row(31, 65, '$.$.H.$.i.$')

    # ================================================================ east aisle (x142-197, y30-76, floor 77)
    m.sky(170, 32, 24, 10)
    m.box(142, 52, 50, 1, '%')             # the gallery floor
    m.hl(192, 77, 3, mv['6'])              # the lift from the floor to the gallery
    m.put(145, 76, '+')
    m.put(154, 76, GL)
    m.put(166, 76, T)
    m.put(179, 76, BR)
    m.put(181, 76, GL)
    m.box(158, 74, 4, 3, '%')
    m.put(160, 73, '*')
    m.box(172, 74, 5, 3, '%')
    m.put(174, 72, '$')
    m.box(185, 75, 3, 2, '%')
    m.put(189, 76, '&')
    m.put(162, 64, J)
    # a girder climb on the west side of the aisle as well
    for x, y in ((142, 74), (147, 71), (142, 68), (147, 65), (142, 62), (147, 59), (142, 57), (147, 55)):
        m.hl(x, y, 4, '-')
    m.hl(147, 52, 4, '-')                  # the gap in the gallery floor over the climb
    m.put(149, 58, '$')
    m.put(144, 67, '*')
    m.put(152, 70, 'l')
    m.put(165, 69, 'L')
    m.put(186, 70, 'L')
    # the gallery (rows 30-51 over the shelf at row 52)
    m.put(143, 51, 'C')
    m.put(162, 51, TL)
    m.box(170, 49, 6, 3, '%')
    m.put(172, 48, '*')
    m.hl(178, 47, 4, '-')
    m.hl(183, 44, 4, '-')
    m.put(185, 43, '$')
    m.row(150, 51, '$.$')
    m.put(190, 51, T)
    m.put(188, 51, SB)
    m.put(180, 38, J)
    m.put(155, 45, 'L')
    m.put(178, 44, 'l')

    # ================================================================ west aisle (x2-58, y6-60, floor 61)
    m.sky(8, 8, 16, 8)
    m.box(28, 52, 31, 1, '%')              # the middle gallery
    m.put(56, 51, 'C')
    m.put(44, 51, TL)
    m.box(36, 49, 4, 3, '%')
    m.put(37, 48, '$')
    # below the gallery: chapels
    m.box(2, 52, 1, 9, '#')
    m.box(3, 54, 14, 7, '#')
    m.box(16, 58, 1, 3, 'X')               # secret 1: the chapel behind a fake wall
    m.box(4, 57, 12, 4, '?')
    m.row(5, 60, '$.i.$.p.$')
    m.box(20, 58, 8, 3, '%')
    m.put(23, 57, '*')
    m.put(33, 60, BR)
    m.put(48, 60, '+')
    m.put(42, 60, G)
    m.put(40, 56, J)
    m.hl(30, 58, 3, '-')
    m.hl(32, 55, 3, '-')
    m.room(28, 52, 6, 1)                   # a gap in the gallery floor over the girders
    m.hl(28, 52, 3, '-')
    m.put(10, 50, 'L')
    m.put(45, 56, 'l')
    # the climb from the gallery to the upper floor (row 37) and the top floor (row 26)
    m.box(3, 52, 25, 1, '%')
    m.hl(3, 52, 6, '-')
    m.hl(3, 49, 4, '-')
    m.hl(8, 46, 4, '-')
    m.hl(3, 43, 4, '-')
    m.hl(8, 40, 4, '-')
    m.hl(3, 37, 25, '-')                   # the upper floor (girders over the west part)
    m.box(28, 37, 31, 1, '%')
    m.put(12, 36, TL)
    m.put(56, 36, '$')
    m.row(30, 36, '$.$')
    m.put(36, 36, G)
    m.put(40, 31, J)
    m.put(24, 36, '&')
    m.put(5, 48, '*')
    m.hl(51, 34, 3, '-')
    m.hl(47, 31, 3, '-')
    m.hl(51, 28, 3, '-')
    m.put(48, 30, '*')
    # the top floor (row 26) and the key gallery above it
    m.box(3, 26, 43, 1, '%')
    m.hl(46, 26, 8, '-')
    m.hl(40, 23, 4, '-')
    m.hl(35, 20, 4, '-')
    m.hl(30, 17, 4, '-')
    m.box(3, 17, 20, 1, '%')
    m.hl(23, 17, 4, '-')
    m.put(6, 16, 'k')
    m.put(10, 16, '$')
    m.put(18, 16, TL)
    m.put(8, 25, GL)
    m.put(15, 25, '*')
    m.put(28, 25, SB)
    m.put(38, 25, '+')
    m.put(20, 12, J)
    m.put(30, 21, 'L')
    m.put(12, 21, 'l')
    m.put(40, 12, 'l')
    m.put(20, 32, 'l')

    # ================================================================ the spire (x142-197, y2-25, floor 26)
    m.put(144, 25, 'C')
    m.box(150, 23, 4, 3, '%')
    m.put(182, 25, TA)
    m.hl(156, 22, 4, '-')
    m.put(158, 21, '*')
    m.put(147, 25, '&')
    m.vl(162, 2, 21, '#')
    m.vl(162, 23, 3, 'd')                  # the blue door
    m.sky(166, 4, 28, 14)
    m.box(170, 23, 6, 3, '%')
    m.put(172, 22, TL)
    m.hl(178, 19, 4, '-')
    m.put(180, 18, '*')
    m.put(166, 25, '$')
    m.put(186, 25, '$')
    m.put(196, 25, BR)
    m.row(178, 18, '$')
    m.put(179, 18, '$')
    m.put(191, 25, 'E')
    m.put(184, 10, J)
    m.put(146, 10, 'L')
    m.put(156, 12, 'l')
    m.put(184, 21, 'l')
    # extra ammo cells
    put_free(m, 148, 76, '&')
    put_free(m, 50, 51, '&')
    put_free(m, 156, 25, '&')
    return m


if __name__ == '__main__':
    main(build, 'e4l5')
