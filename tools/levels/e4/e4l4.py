"""e4l4 -- The Long Barracks / Die langen Kasernen (citadel). Shieldbots, laser eyes, both keys.

Three decks west of an open courtyard and three decks east of it:
  M-west (start): gatehouse, dormitory, mess hall (first shieldbot), kitchen; stairwells S1 and S2 down to
  D-west: armory (blue key; a cellar under a fake floor plate), shooting range (laser eyes taught), workshop.
  The blue door at the east end of M-west opens onto the courtyard (sky): a tower with tunnels at three levels,
  girder climbs, a vault inside the tower (fake wall).
  U-west (only from the courtyard): officers' lounge, map room, quarters, the commandant's office (gold key; a
  stash over a fake ceiling plate).
  East: M-east briefing rooms, D-east brig, U-east command deck; stairwell S3 joins them. The gold door at the east
  end of the command deck leads to the exit.
"""
from kit import Map, main


def put_free(m, x, y, ch):
    assert m.get(x, y) == '.', (x, y, m.get(x, y))
    m.put(x, y, ch)


def stair(m, x, ys):
    """A stairwell: two-tile girders alternating left/right; the middle column stays open for falling."""
    for i, y in enumerate(ys):
        m.hl(x + (0 if i % 2 == 0 else 3), y, 2, '-')


def build():
    m = Map(270, 56)
    m.key('name', 'The Long Barracks')
    m.key('name.de', 'Die langen Kasernen')
    m.key('theme', 'citadel')
    m.key('tint', 0)
    m.key('bg', 'citadel_a')
    m.key('music', 'e4_citadel')
    m.key('dark', 0.25)
    m.key('par', 540)
    T = m.legend('a', 'enemy trooper')
    TL = m.legend('b', 'enemy trooper left')
    TA = m.legend('e', 'enemy trooper ambush')
    G = m.legend('g', 'enemy gloamhound')
    GL = m.legend('h', 'enemy gloamhound left')
    BRL = m.legend('w', 'enemy brute left')
    S = m.legend('r', 'enemy shieldbot')
    SL = m.legend('t', 'enemy shieldbot left')
    EY = m.legend('z', 'enemy lasereye')
    m.legend('n', 'sign sign.e4l4.lasereye')
    m.legend('j', 'sign sign.e4l4.shieldbot')
    m.legend('L', 'light violet 7')
    m.legend('l', 'light cyan 5')
    m.legend('o', 'power overdrive')
    m.legend('p', 'power shield')
    m.legend('c', 'treasure crown')
    m.legend('i', 'treasure idol')
    m.legend('x', 'treasure cube')

    def walls(y0, xs, h=7):
        for x in xs:
            m.vl(x, y0, h, '#')

    # ================================================================ M-west (x3-140, y19-28, floor 29)
    m.room(3, 19, 138, 10)
    walls(19, (23, 59, 67, 113, 132))
    m.box(139, 19, 2, 7, '#')
    m.vl(140, 26, 3, 'd')                  # the blue door onto the courtyard
    # gatehouse (start)
    m.put(5, 28, 'P')
    m.sky(4, 20, 7, 3)
    m.box(13, 26, 4, 3, '%')               # the guard booth
    m.put(14, 25, '*')
    m.put(19, 28, '$')
    m.put(8, 24, 'L')
    # dormitory: bunks under a lower ceiling
    m.box(24, 19, 35, 2, '#')
    for x in (27, 36, 45, 53):
        m.hl(x, 26, 5, '-')
        m.hl(x, 23, 5, '-')
    m.put(47, 22, '*')
    m.put(29, 22, '$')
    m.put(38, 22, '$')
    m.put(55, 22, 'i')
    m.put(34, 28, TL)
    m.put(51, 28, TL)
    m.put(42, 21, 'l')
    m.put(56, 28, '+')
    # S1 (x60-66): down to D-west
    m.room(61, 29, 5, 5)
    # mess hall: tables, the first shieldbots between them
    m.put(70, 28, 'j')
    for x in (73, 84, 95, 106):
        m.box(x, 28, 6, 1, '%')
    m.put(81, 28, S)
    m.put(92, 28, SL)
    m.put(97, 25, '*')
    m.row(85, 27, '$.$')
    m.put(108, 27, '$')
    m.put(78, 21, 'L')
    m.put(100, 21, 'L')
    # kitchen: plasma vats
    m.box(118, 29, 2, 2, '~')
    m.box(125, 29, 2, 2, '~')
    m.hl(120, 26, 4, '-')
    m.put(122, 25, '*')
    m.put(129, 28, GL)
    m.put(116, 28, '&')
    m.put(122, 21, 'l')
    # S2 (x133-137): down to D-west
    m.room(133, 29, 5, 5)
    m.put(138, 28, '$')

    # ================================================================ D-west (x3-139, y34-43, floor 44)
    m.room(3, 34, 137, 10)
    walls(34, (35, 101))
    # armory: racks, the blue key
    m.hl(11, 41, 4, '-')
    m.box(5, 38, 6, 1, '%')
    m.put(6, 37, 'k')
    m.put(9, 37, '$')
    m.box(20, 40, 6, 1, '%')
    m.put(23, 39, '*')
    m.put(16, 43, S)
    m.put(29, 43, SL)
    m.put(26, 36, 'L')
    m.put(8, 35, 'l')
    # secret 1: a fake floor plate drops into the cellar; a girder leads back up through it
    m.box(18, 44, 2, 1, 'X')
    m.box(8, 45, 23, 5, '?')
    m.hl(18, 47, 2, '-')
    m.row(10, 49, '$.$.H')
    m.row(22, 49, '$.p.$.c')
    # shooting range: cover blocks, laser eyes at the far end and on the ceiling
    m.put(38, 43, 'n')
    m.box(40, 42, 4, 2, '%')
    for x in (48, 60, 72, 84):
        m.box(x, 42, 2, 2, '%')
    m.put(98, 43, EY)
    m.put(66, 34, EY)
    m.put(55, 43, TL)
    m.put(79, 43, TL)
    m.put(66, 41, '*')
    m.hl(88, 41, 5, '-')
    m.put(90, 40, '*')
    m.row(53, 43, '$')
    m.row(77, 43, '$')
    m.put(92, 43, '+')
    m.put(54, 36, 'l')
    m.put(78, 36, 'l')
    m.put(95, 36, 'L')
    # workshop
    m.box(106, 43, 5, 1, '%')
    m.box(120, 43, 5, 1, '%')
    m.hl(119, 40, 5, '-')
    m.put(121, 39, '*')
    m.put(115, 43, BRL)
    m.put(108, 42, '&')
    m.put(112, 36, 'L')
    m.put(128, 37, 'l')

    # ================================================================ the courtyard (x141-195, y2-49): open sky
    m.sky(141, 2, 55, 48)
    m.box(141, 47, 55, 3, '~')
    m.box(163, 8, 11, 39, '#')             # the tower
    m.room(163, 11, 11, 3)                 # tunnels through it at three levels
    m.room(163, 26, 11, 3)
    m.room(163, 41, 11, 3)
    # ledges at the west wall (U-west mouth, the blue door) and the east wall (three decks)
    m.box(141, 14, 6, 1, '#')
    m.box(141, 29, 8, 1, '#')
    m.put(143, 28, 'C')
    m.box(189, 14, 7, 1, '#')
    m.box(187, 29, 9, 1, '#')
    m.box(187, 44, 9, 1, '#')
    # walkways
    m.hl(150, 14, 11, '-')
    m.hl(152, 29, 9, '-')
    m.hl(176, 14, 11, '-')
    m.hl(176, 29, 9, '-')
    m.hl(176, 44, 9, '-')
    m.hl(150, 44, 13, '-')
    # climbs: west M -> U, east D -> M, the tower top
    for x, y in ((153, 26), (157, 23), (153, 20), (157, 17)):
        m.hl(x, y, 4, '-')
    for x, y in ((176, 41), (180, 38), (176, 35), (180, 32)):
        m.hl(x, y, 4, '-')
    m.hl(159, 11, 4, '-')
    m.put(168, 7, '*')
    m.put(171, 7, TL)
    m.put(155, 19, '*')
    m.put(152, 43, '*')
    m.put(181, 37, '*')
    m.put(159, 28, EY)
    m.put(185, 13, EY)
    m.put(184, 43, SL)
    m.put(178, 28, TL)
    m.put(156, 13, TA)
    m.row(178, 13, '$$')
    m.row(154, 43, '$.$')
    m.put(193, 28, '+')
    m.put(193, 43, '&')
    m.put(168, 27, 'L')
    m.put(168, 12, 'l')
    m.put(168, 42, 'l')
    # secret 2: a vault inside the tower, through a fake wall from the west climb
    m.hl(161, 23, 2, '-')
    m.box(163, 21, 2, 2, 'X')
    m.box(165, 19, 7, 4, '?')
    m.row(166, 22, '$x$o')

    # ================================================================ U-west (x3-140, y4-13, floor 14), from the courtyard
    m.room(3, 4, 138, 10)
    walls(4, (34, 69, 104))
    m.vl(140, 4, 6, '#')
    # officers' lounge
    m.box(110, 13, 4, 1, '%')
    m.box(126, 13, 4, 1, '%')
    m.put(107, 13, EY)
    m.hl(118, 11, 4, '-')
    m.put(120, 10, '*')
    m.put(133, 13, SL)
    m.put(124, 7, 'L')
    # map room: the great table
    m.box(80, 11, 14, 3, '%')
    m.put(86, 10, '*')
    m.row(82, 10, '$')
    m.row(91, 10, '$')
    m.put(75, 13, S)
    m.put(98, 13, SL)
    m.put(86, 6, 'L')
    # quarters: beds and shelves
    m.box(40, 13, 5, 1, '%')
    m.box(52, 13, 5, 1, '%')
    m.hl(46, 10, 4, '-')
    m.hl(50, 7, 4, '-')
    m.put(51, 6, '*')
    m.put(47, 9, '$')
    m.put(60, 13, TL)
    m.put(38, 13, G)
    m.put(64, 13, '+')
    m.put(55, 6, 'l')
    # the commandant's office: gold key on the desk, a stash above the ceiling
    m.box(8, 11, 5, 3, '%')
    m.put(10, 10, 'K')
    m.hl(3, 9, 4, '-')
    m.put(4, 8, '*')
    m.box(28, 13, 1, 1, '%')
    m.put(28, 12, EY)
    m.put(24, 13, TL)
    m.hl(14, 9, 4, '-')
    m.hl(14, 6, 5, '-')
    m.box(15, 3, 2, 1, 'X')
    m.box(12, 1, 13, 2, '?')
    m.row(13, 2, '$.$.i')
    m.row(19, 2, '$.$')
    m.put(20, 7, 'L')

    # ================================================================ M-east (x196-266, y19-28, floor 29)
    m.room(196, 19, 71, 10)
    walls(19, (226, 237))
    m.vl(196, 19, 6, '#')
    m.box(197, 19, 29, 2, '#')
    for x in (200, 207, 214):
        m.box(x, 28, 4, 1, '%')
    m.put(212, 28, S)
    m.put(221, 28, TL)
    m.put(215, 25, '*')
    m.put(203, 27, '$')
    m.put(210, 22, 'L')
    m.box(258, 26, 5, 3, '%')              # the podium
    m.put(260, 25, '*')
    m.put(248, 28, SL)
    m.put(242, 28, T)
    m.put(265, 28, 'H')
    m.put(252, 21, 'L')
    # S3 (x231-235): from D-east through M-east to U-east
    m.room(231, 14, 5, 20)

    # ================================================================ D-east (x196-266, y34-43, floor 44): the brig
    m.room(196, 34, 71, 10)
    m.vl(196, 34, 6, '#')
    for x in (200, 203, 226, 260, 263):
        m.vl(x, 34, 4, '%')
    for x in (205, 218, 244, 255):
        m.box(x, 42, 2, 2, '%')
    m.hl(210, 40, 13, '-')
    m.hl(238, 40, 13, '-')
    m.put(215, 39, '*')
    m.put(245, 39, '*')
    m.row(212, 39, '$')
    m.row(248, 39, '$')
    m.put(226, 43, EY)
    m.put(252, 43, EY)
    m.put(211, 43, GL)
    m.put(240, 43, GL)
    m.put(261, 43, BRL)
    m.put(199, 43, '+')
    m.put(264, 43, '&')
    m.put(203, 36, 'l')
    m.put(222, 36, 'L')
    m.put(240, 36, 'l')
    m.put(258, 36, 'L')

    # ================================================================ U-east (x196-253, y4-13, floor 14): command deck
    m.room(196, 4, 58, 10)
    m.vl(196, 4, 6, '#')
    m.put(199, 13, 'C')
    m.box(205, 13, 6, 1, '%')
    m.box(222, 13, 6, 1, '%')
    m.put(224, 12, '*')
    m.put(215, 13, TL)
    m.box(240, 12, 11, 2, '%')             # the dais
    m.hl(243, 9, 5, '-')
    m.put(245, 8, '*')
    m.put(238, 13, SL)
    m.put(250, 11, EY)
    m.put(228, 13, TA)
    m.put(207, 12, '$')
    m.put(242, 11, '$')
    m.put(212, 7, 'L')
    m.put(236, 7, 'L')
    # the gold door and the exit
    m.vl(254, 11, 3, 'D')
    m.room(255, 4, 12, 10)
    m.sky(256, 5, 10, 5)
    m.put(262, 13, 'E')
    m.put(258, 13, '$')
    m.put(265, 13, '$')
    # the stairwells (drawn last: they reach into the decks above and below)
    stair(m, 61, (29, 32, 35, 38, 41))
    m.put(63, 37, '*')
    stair(m, 133, (29, 32, 35, 38, 41))
    stair(m, 231, (41, 38, 35, 32, 29, 26, 23, 20, 17, 14))
    m.put(233, 24, '*')
    m.put(233, 36, 'l')
    # extra ammo cells
    put_free(m, 245, 28, '&')
    put_free(m, 95, 13, '&')
    put_free(m, 207, 43, '&')
    return m


if __name__ == '__main__':
    main(build, 'e4l4')
