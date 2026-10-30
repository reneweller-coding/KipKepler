"""e4l7 -- Hangar of Shadows / Hangar der Schatten (citadel). Open spaces, jetpackers, springs.

Three hangars joined by service corridors; the hangar roofs are open force fields onto space.
  H1 arrival hangar (start): springs taught (a bounce onto the west catwalk), a parked dropship, catwalks up to
  the corridor C1. H2 main hangar: three dropships at three heights (on struts, on a landing tower, docked under
  the roof); springs carry the hero from roof to roof up to the blue key on the highest ship.
  C2 at floor level leads to H3, the launch bay: rails stick out into space, springs between them, the blue door
  and the exit capsule on the top rail.
Springs launch about 11 tiles high: every spring target here is 9-10 tiles up.
Secrets: a vault behind H1's east wall (fake wall from a high ledge), a cabin inside the low dropship of H2
(fake hull plate), a vault behind the launch bay's west wall (fake wall from rail 2).
"""
from kit import Map, main

SHIP = """
,,,,%%%%%%%%%%%%%%%%,,,,
,,%%%%%%%%%%%%%%%%%%%%,,
%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%
,,%%%%%%%%%%%%%%%%%%%%,,
,,,,,%%%%%%%%%%%%%%,,,,,
"""


def build():
    m = Map(260, 68)
    m.key('name', 'Hangar of Shadows')
    m.key('name.de', 'Hangar der Schatten')
    m.key('theme', 'citadel')
    m.key('tint', 2)
    m.key('bg', 'citadel_a')
    m.key('music', 'e4_citadel')
    m.key('dark', 0.3)
    m.key('par', 560)
    T = m.legend('a', 'enemy trooper')
    TL = m.legend('b', 'enemy trooper left')
    TA = m.legend('e', 'enemy trooper ambush')
    G = m.legend('g', 'enemy gloamhound')
    GL = m.legend('h', 'enemy gloamhound left')
    J = m.legend('j', 'enemy jetpacker')
    JA = m.legend('y', 'enemy jetpacker ambush')
    SB = m.legend('r', 'enemy shieldbot')
    EY = m.legend('z', 'enemy lasereye')
    BR = m.legend('w', 'enemy brute')
    BL = m.legend('i', 'enemy blinker')
    S = m.legend('S', 'spring')
    m.legend('n', 'sign sign.e4l7.spring')
    m.legend('L', 'light violet 8')
    m.legend('l', 'light cyan 6')
    m.legend('o', 'power overdrive')
    m.legend('p', 'power shield')
    m.legend('c', 'treasure crown')
    m.legend('x', 'treasure cube')
    m.legend('u', 'treasure idol')

    def ship(x, y, floor=None):
        """A parked dropship, roof at row y (x+4..x+19); struts down to the floor leave a walkway under it."""
        m.stamp(x, y, SHIP)
        pass

    # ================================================================ rooms
    m.room(2, 6, 79, 56)                   # H1 x2-80, floor 62
    m.room(81, 37, 20, 4)                  # C1 x81-100, floor 41
    m.room(101, 4, 80, 60)                 # H2 x101-180, floor 64
    m.room(181, 59, 20, 5)                 # C2 x181-200, floor 64
    m.room(201, 6, 56, 58)                 # H3 x201-256, floor 64

    # ================================================================ H1 arrival hangar
    m.sky(8, 7, 66, 16)
    m.box(2, 62, 79, 2, '#')
    m.put(5, 61, 'P')
    m.put(11, 61, 'n')
    m.put(15, 61, S)                       # the first spring: onto the west catwalk
    m.box(2, 52, 10, 1, '%')
    m.put(4, 51, '*')
    m.row(7, 51, '$.$')
    m.put(8, 55, 'l')
    # the parked dropship
    m.put(21, 61, S)
    ship(24, 52, 62)
    m.put(35, 51, '*')
    m.put(36, 61, '*')
    m.put(33, 61, '$')
    m.put(39, 61, '$')
    m.put(42, 51, S)                       # roof spring up to the middle catwalk
    m.box(49, 42, 14, 1, '%')
    m.put(55, 41, '*')
    m.put(58, 41, T)
    m.put(52, 61, GL)
    m.put(66, 61, G)
    m.put(60, 61, '&')
    m.put(64, 61, '+')
    m.box(70, 59, 4, 3, '%')               # crates
    m.box(74, 60, 3, 2, '%')
    # the high catwalk over the ship, from a spring on the middle catwalk
    m.put(50, 41, S)
    m.hl(26, 32, 18, '-')
    m.put(30, 31, '*')
    m.row(34, 31, '$.$.$')
    m.put(40, 31, TL)
    # east catwalk to the corridor
    m.box(66, 41, 15, 1, '%')
    m.hl(63, 41, 3, '-')
    m.put(68, 40, TL)
    m.put(70, 40, S)                       # a spring to the high east ledge (secret)
    m.box(74, 31, 7, 1, '%')
    m.put(76, 30, '$')
    m.box(81, 29, 1, 2, 'X')
    m.box(82, 27, 12, 4, '?')
    m.row(83, 30, '$.$.c.$.H')
    # jetpackers in the open
    m.put(24, 40, J)
    m.put(45, 24, J)
    m.put(62, 30, J)
    m.put(14, 30, JA)
    m.put(30, 45, 'L')
    m.put(60, 50, 'L')
    m.put(20, 27, 'l')
    m.put(70, 34, 'l')

    # ================================================================ C1 corridor (x81-100, y37-40, floor 41)
    m.put(84, 40, 'C')
    m.put(93, 40, TL)
    m.put(99, 40, EY)
    m.row(88, 40, '$$')
    m.put(90, 37, 'l')

    # ================================================================ H2 main hangar (x101-180, y4-63, floor 64)
    m.sky(104, 5, 74, 14)
    m.box(101, 41, 8, 1, '%')              # west ledge (C1)
    m.box(134, 64, 4, 1, '~')
    m.box(158, 64, 4, 1, '~')
    # D2 on struts, low
    m.put(108, 63, S)
    ship(112, 54, 64)
    m.put(123, 53, '*')
    m.put(124, 63, '*')
    m.put(121, 63, '$')
    m.put(127, 63, '$')
    m.put(118, 63, BR)
    # secret 2: a cabin inside D2, through a fake hull plate at its stern
    m.box(112, 56, 1, 2, 'X')
    m.box(113, 56, 7, 2, '?')
    m.row(114, 57, '$x$p')
    m.hl(110, 58, 3, '%')
    # D3 on the landing tower
    m.box(140, 40, 12, 24, '#')
    ship(134, 34)
    m.put(131, 53, S)                      # D2's roof spring up to the catwalk
    m.hl(124, 44, 12, '-')
    m.hl(117, 42, 5, '-')
    m.put(132, 43, TL)
    m.put(127, 43, S)                      # catwalk spring up to a girder beside D3
    m.hl(129, 34, 5, '-')
    m.put(145, 33, '*')
    m.put(149, 33, SB)
    m.put(138, 33, '$')
    m.put(152, 33, S)                      # D3's roof spring up to the hanging catwalk
    m.hl(150, 24, 10, '-')
    m.put(155, 23, '*')
    m.put(152, 23, S)                      # catwalk spring up beside D4
    # D4 docked under the roof gantry
    m.box(166, 4, 5, 10, '#')
    ship(156, 14)
    m.put(162, 13, 'k')
    m.put(164, 13, '$')
    # the floor of H2
    m.put(146, 63, G)
    m.put(166, 63, GL)
    m.put(175, 63, '+')
    m.put(178, 63, '&')
    m.box(170, 61, 3, 3, '%')
    m.put(171, 60, '$')
    # the east floor's springs back up to D3 (the landing tower splits the floor)
    m.put(162, 63, S)
    m.hl(158, 54, 9, '-')
    m.put(164, 53, S)
    m.hl(156, 44, 9, '-')
    m.put(162, 43, S)
    m.put(160, 53, '$')
    m.put(158, 43, T)
    m.hl(111, 41, 6, '-')
    m.put(113, 40, '*')
    m.put(120, 30, J)
    m.put(140, 22, J)
    m.put(170, 32, J)
    m.put(110, 20, JA)
    m.put(168, 48, J)
    m.put(118, 45, 'L')
    m.put(146, 45, 'L')
    m.put(164, 40, 'L')
    m.put(132, 25, 'l')
    m.put(174, 55, 'l')

    # ================================================================ C2 corridor (x181-200, y59-63, floor 64)
    m.put(184, 63, 'C')
    m.put(195, 63, TL)
    m.put(191, 63, '$')
    m.put(190, 60, 'l')

    # ================================================================ H3 launch bay (x201-256, y6-63, floor 64)
    m.sky(226, 7, 30, 52)                  # the bay opens onto space
    m.box(201, 64, 56, 4, '#')
    # rails sticking out into space; springs between them
    m.box(214, 54, 34, 1, '%')             # rail 1
    m.box(201, 44, 33, 1, '%')             # rail 2
    m.box(220, 34, 34, 1, '%')             # rail 3
    m.box(205, 24, 28, 1, '%')             # rail 4 (the exit rail, west part)
    m.put(212, 63, S)                      # floor -> rail 1
    m.put(244, 53, S)                      # rail 1 -> rail 2 ... from its east end
    m.hl(236, 47, 4, '-')
    m.put(217, 43, S)                      # rail 2 -> rail 3
    m.put(250, 33, S)                      # rail 3 -> rail 4 (east), a girder bridge back west
    m.hl(234, 24, 22, '-')
    m.put(208, 63, G)
    m.put(222, 63, GL)
    m.put(234, 63, '&')
    m.put(218, 63, '*')
    m.put(230, 53, '*')
    m.put(240, 53, TL)
    m.put(210, 43, '*')
    m.put(226, 43, TL)
    m.put(238, 33, '*')
    m.put(232, 33, SB)
    m.put(246, 46, '$')
    m.put(254, 32, '$')
    m.put(216, 53, '+')
    m.put(240, 40, J)
    m.put(250, 15, J)
    m.put(236, 18, JA)
    m.put(212, 30, BL)
    # the blue door and the exit capsule on rail 4
    m.vl(212, 21, 3, 'd')
    m.box(212, 6, 1, 15, '#')
    m.put(207, 23, 'E')
    m.put(210, 23, '$')
    m.put(224, 23, '*')
    m.put(228, 23, TL)
    # secret 3: behind the bay's west wall from rail 2
    m.box(200, 41, 1, 3, 'X')
    m.box(188, 41, 12, 3, '?')
    m.row(189, 43, '$.$.u.$.o')
    m.put(216, 58, 'L')
    m.put(208, 48, 'L')
    m.put(222, 38, 'l')
    m.put(216, 28, 'L')
    m.put(244, 58, 'l')
    # more crystals on the spring arcs, treasure, supplies, ambushes
    m.put(15, 51, '*')
    m.put(70, 36, '*')
    m.put(95, 40, '*')
    m.put(164, 48, '*')
    m.put(244, 45, '*')
    m.put(250, 27, '*')
    m.row(72, 40, '$$$')
    m.row(125, 43, '$$')
    m.row(220, 53, '$$$')
    m.row(226, 33, '$$')
    m.row(104, 63, '$$')
    m.row(8, 61, '$$')
    m.row(176, 63, '$')
    m.put(82, 40, '+')
    m.put(246, 53, 'H')
    m.put(103, 40, '+')
    m.put(45, 61, '&')
    m.put(106, 40, '&')
    m.put(227, 53, '&')
    m.put(241, 33, TA)
    m.put(62, 61, TA)
    m.put(230, 63, TA)
    m.put(103, 63, G)
    return m


if __name__ == '__main__':
    main(build, 'e4l7')
