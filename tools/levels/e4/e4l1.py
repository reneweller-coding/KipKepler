"""e4l1 -- Boarding Breach / Enterbresche (foundry). Lava, troopers, gloamhounds.

Route: the pod's breach (A) -> intake deck (B: a lava channel taught, the first trooper, the first hound behind a
gap) -> slag yard (C: pillars over a lava river; the blue door is seen at the silo top) -> the chute down into the
smelter pits (D: the upper gallery west, the key vault above its west end, the shaft down, the lower basin back
east) -> the ore silo (E: climb) -> blue door -> kennels (F: three decks of hounds) -> exit hall (G).
Secrets: a niche in the breach's hull (fake wall), a store room east of the key vault (fake wall), a loft above the
first kennel deck (fake ceiling over a crate).
"""
from kit import Map, main


def build():
    m = Map(200, 62)
    m.key('name', 'Boarding Breach')
    m.key('name.de', 'Enterbresche')
    m.key('theme', 'foundry')
    m.key('tint', 0)
    m.key('bg', 'foundry_b')
    m.key('music', 'e4_foundry')
    m.key('dark', 0.25)
    m.key('par', 420)
    T = m.legend('a', 'enemy trooper')
    TL = m.legend('b', 'enemy trooper left')
    TA = m.legend('e', 'enemy trooper ambush')
    G = m.legend('g', 'enemy gloamhound')
    GL = m.legend('h', 'enemy gloamhound left')
    GA = m.legend('f', 'enemy gloamhound ambush')
    m.legend('t', 'sign sign.e4l1.lava')
    m.legend('u', 'sign sign.e4l1.hound')
    m.legend('L', 'light orange 7')
    m.legend('l', 'light warm 5')
    m.legend('o', 'power overdrive')
    m.legend('s', 'power shield')
    m.legend('c', 'treasure crown')
    m.legend('i', 'treasure idol')

    # ================================================================ A: the breach (x1-33, y1-16, floor 17)
    m.room(1, 1, 33, 16)
    for y, x0, x1 in ((1, 8, 24), (2, 4, 27), (3, 2, 27), (4, 1, 25), (5, 1, 25), (6, 1, 25), (7, 1, 25),
                      (8, 1, 24), (9, 1, 23), (10, 1, 21), (11, 1, 18), (12, 1, 14)):
        m.sky(x0, y, x1 - x0 + 1, 1)
    m.stamp(1, 1, """
#######
###
#
""")
    m.vl(14, 1, 2, '#')
    m.box(28, 1, 6, 3, '#')
    m.box(26, 4, 8, 8, '#')            # the hull's torn edge
    # secret 1: a fake plate beside the top girder, a niche in the hull
    m.box(26, 6, 2, 2, 'X')
    m.box(28, 5, 5, 3, '?')
    m.row(29, 7, '$&$')
    m.put(32, 7, 'i')
    # the pod (crashed): the hero starts on it
    m.box(1, 13, 8, 4, '%')
    m.box(9, 15, 2, 2, '%')
    m.put(4, 12, 'P')
    # girders in the breach
    m.hl(12, 14, 4, '-')
    m.hl(17, 11, 4, '-')
    m.put(18, 10, '*')
    m.hl(22, 8, 4, '-')
    m.row(22, 7, '$$')
    m.put(13, 13, '$')
    # the lava channel (taught): two wide, a crystal over it
    m.box(21, 17, 2, 2, '~')
    m.put(21, 14, '*')
    m.put(17, 16, 't')
    m.put(30, 13, 'L')

    # ================================================================ B: intake deck (x34-68)
    m.room(34, 10, 35, 7)              # main corridor y10-16, floor 17
    m.room(36, 4, 33, 4)               # upper corridor y4-7, floor 8
    m.room(45, 8, 4, 2)                # the shaft between them
    m.hl(45, 14, 4, '-')
    m.hl(45, 11, 4, '-')
    m.hl(45, 8, 4, '-')
    m.box(40, 17, 3, 2, '~')           # a second channel, crystal over it
    m.put(41, 13, '*')
    m.put(37, 13, 'l')
    m.box(51, 14, 3, 3, '%')           # cover crates, the first trooper beyond
    m.box(54, 15, 2, 2, '%')
    m.put(64, 16, TL)
    m.put(58, 16, '+')
    m.put(61, 13, 'l')
    m.row(38, 7, '$.$.$')              # upper corridor
    m.room(54, 8, 3, 2)                # a gap down into the main corridor: the first hound stops at its edge
    m.put(51, 7, 'u')
    m.put(62, 7, GL)
    m.put(66, 7, '*')
    m.put(58, 5, 'l')

    # ================================================================ C: slag yard (x69-122, y2-30)
    m.room(69, 2, 54, 29)
    m.sky(76, 3, 12, 6)                # windows onto the burning planet
    m.sky(96, 3, 8, 4)
    m.sky(111, 3, 9, 10)
    m.vl(81, 3, 5, '#')
    m.box(69, 28, 54, 3, '~')          # the lava river
    m.box(69, 2, 4, 2, '#')
    m.box(69, 8, 7, 1, '%')            # gantry from the upper corridor
    m.row(72, 7, '$$')
    m.box(69, 17, 6, 14, '#')          # entry ledge from the main corridor
    m.put(71, 16, '&')
    for x, top, w in ((78, 19, 4), (85, 18, 4), (92, 21, 3), (98, 19, 6)):
        m.box(x, top, w, 31 - top, '%')
    m.box(106, 20, 17, 11, '#')        # the east floor over the river
    m.room(109, 20, 2, 15)             # the chute down to the smelter pits
    m.put(80, 18, '$')
    m.put(87, 17, '$')
    m.put(86, 17, TL)
    m.put(93, 20, '*')
    m.put(101, 18, T)
    m.put(115, 19, TL)
    m.put(120, 19, '+')
    m.put(84, 14, 'L')
    m.put(104, 15, 'L')
    m.hl(85, 15, 4, '-')               # girders up to the high catwalk
    m.hl(90, 12, 4, '-')
    m.put(91, 11, '*')
    m.hl(95, 9, 6, '-')
    m.row(96, 8, '$$$$')
    m.box(101, 9, 22, 1, '%')          # the high catwalk
    m.put(107, 8, GL)
    m.put(117, 8, '*')
    m.put(121, 8, '$')
    m.put(108, 5, 'l')

    # ================================================================ E: ore silo (x124-139, y13-59)
    m.room(123, 17, 1, 3)              # passage from the slag yard
    m.room(124, 13, 16, 47)
    m.box(124, 57, 16, 3, '~')
    m.hl(124, 20, 2, '#')
    m.hl(126, 20, 12, '-')
    m.hl(138, 20, 2, '#')
    m.room(140, 17, 1, 3)
    m.vl(140, 17, 3, 'd')
    m.put(125, 19, 'C')
    m.put(131, 16, 'l')
    m.box(124, 54, 4, 6, '#')          # entry ledge from the basin
    for x, y, w, ch in ((130, 52, 4, '-'), (135, 50, 5, '%'), (129, 47, 4, '-'), (124, 45, 4, '%'),
                        (129, 42, 4, '-'), (135, 39, 5, '%'), (129, 36, 4, '-'), (124, 34, 4, '%'),
                        (129, 31, 4, '-'), (135, 28, 5, '%'), (130, 25, 4, '-'), (126, 23, 4, '-')):
        m.hl(x, y, w, ch)
    m.put(131, 51, '*')
    m.put(137, 49, T)
    m.put(131, 30, TA)
    m.put(125, 44, TL)
    m.put(137, 38, '*')
    m.put(125, 33, '$')
    m.put(137, 27, TA)
    m.put(131, 24, '*')
    m.put(127, 22, '&')
    m.put(133, 45, 'l')
    m.put(132, 33, 'l')

    # ================================================================ D: smelter pits
    # upper gallery (x10-122, y35-41, floor 42), entered by the chute at x109-110
    m.room(10, 35, 113, 7)
    m.put(113, 41, 'C')
    m.put(117, 37, 'L')
    m.box(102, 42, 3, 2, '~')
    m.box(94, 39, 3, 3, '%')
    m.put(88, 41, GL)
    m.put(84, 41, '$')
    m.box(78, 42, 3, 2, '~')
    m.put(79, 38, '*')
    m.box(70, 39, 4, 3, '%')
    m.put(72, 38, TL)
    m.put(66, 41, 'H')
    m.box(58, 42, 3, 2, '~')
    m.row(58, 38, '$$$')
    m.put(50, 41, GL)
    m.put(43, 39, T)
    m.box(42, 40, 3, 2, '%')
    m.put(38, 41, '&')
    m.box(30, 42, 3, 2, '~')
    m.put(31, 38, '*')
    m.put(25, 41, G)
    m.put(97, 37, 'l')
    m.put(76, 37, 'l')
    m.put(54, 37, 'L')
    m.put(36, 37, 'l')
    m.put(14, 37, 'l')
    # the casting hall above the gallery (x44-70, y20-34): girders up the west wall, a ledge, a bridge
    m.room(44, 20, 24, 15)
    for x, y in ((45, 39), (50, 36), (45, 33), (50, 30), (45, 27)):
        m.hl(x, y, 4, '-')
    m.box(50, 24, 7, 1, '%')
    m.hl(57, 24, 4, '-')
    m.box(61, 24, 7, 1, '%')
    m.box(61, 20, 7, 2, '%')           # the furnace hood
    m.put(52, 23, '*')
    m.row(54, 23, '$$')
    m.put(66, 23, TL)
    m.put(63, 23, '$')
    m.put(47, 22, 'L')
    m.put(58, 28, 'L')
    m.box(61, 25, 7, 3, '%')           # the furnace over the gallery
    m.box(62, 28, 5, 1, '%')
    # hanging pipes over the gallery
    m.box(86, 35, 2, 2, '#')
    m.box(97, 35, 3, 1, '#')
    m.box(118, 35, 2, 2, '#')
    # the climb into the key vault: girders stacked under the vault floor
    m.hl(18, 39, 4, '-')
    m.hl(18, 36, 4, '-')
    # the key vault (x9-31, y21-33, floor 34)
    m.room(9, 21, 23, 13)
    m.hl(18, 34, 4, '-')
    m.hl(19, 31, 4, '-')
    m.hl(14, 28, 4, '%')
    m.box(9, 25, 4, 1, '%')            # the key ledge
    m.put(10, 24, 'k')
    m.hl(24, 29, 4, '%')
    m.hl(27, 26, 4, '-')
    m.put(28, 25, '*')
    m.put(29, 33, TL)
    m.row(24, 33, '$$$')
    m.put(15, 27, '$')
    m.put(16, 22, 'l')
    m.put(26, 22, 'l')
    # secret 2: a store room behind the vault's east wall
    m.box(32, 31, 1, 3, 'X')
    m.box(33, 29, 10, 5, '?')
    m.row(34, 33, '$H$o$&')
    # the shaft down from the key ledge to the lower basin (one way)
    m.room(8, 22, 1, 3)
    m.room(4, 22, 4, 26)
    m.put(5, 30, 'l')
    # lower basin (x4-121, y45-59, lava 56-59), back east to the silo: four stretches
    m.room(4, 45, 118, 15)
    m.box(4, 56, 118, 4, '~')
    m.box(4, 48, 7, 12, '#')           # landing under the shaft
    m.put(6, 47, '+')
    # 1: open lava, a crumbling start
    m.hl(11, 51, 4, '_')
    for x, top, w in ((15, 51, 4), (22, 49, 5), (30, 51, 3)):
        m.box(x, top, w, 60 - top, '%')
    m.put(24, 48, T)
    m.put(16, 50, '$')
    m.put(31, 50, '$')
    m.put(20, 47, 'L')
    # 2: a slag wall with a tunnel through it
    m.box(36, 45, 6, 15, '#')
    m.room(36, 47, 6, 3)
    m.put(38, 49, '*')
    m.put(40, 49, '$')
    for x, top, w in ((45, 51, 4), (52, 52, 3), (58, 50, 6)):
        m.box(x, top, w, 60 - top, '%')
    m.put(61, 49, TL)
    m.put(53, 51, '$')
    m.put(50, 47, 'L')
    # 3: a low ceiling of hanging slag: short hops, crumbling plates
    m.box(64, 45, 27, 2, '#')
    m.box(70, 47, 3, 1, '#')
    m.box(80, 47, 2, 1, '#')
    m.hl(64, 51, 3, '_')
    for x, top, w in ((67, 52, 3), (72, 51, 4), (78, 53, 3)):
        m.box(x, top, w, 60 - top, '%')
    m.hl(81, 52, 3, '_')
    m.box(86, 51, 5, 9, '%')
    m.put(73, 50, T)
    m.put(79, 52, '*')
    m.put(68, 51, '$')
    m.put(88, 50, TA)
    m.put(76, 48, 'l')
    # 4: a high pillar and a girder bridge to the east landing
    m.box(92, 50, 3, 10, '%')
    m.box(97, 47, 4, 13, '%')
    m.put(98, 46, '*')
    m.hl(101, 47, 7, '-')
    m.row(102, 46, '$$$')
    m.box(103, 54, 3, 6, '%')
    m.put(104, 53, '&')
    m.box(108, 51, 14, 9, '#')         # east landing
    m.room(122, 48, 2, 3)              # passage into the silo
    m.put(117, 50, GL)
    m.put(110, 50, '+')
    m.put(95, 47, 'L')
    m.put(114, 47, 'l')

    # ================================================================ F: the kennels (x141-178)
    m.room(141, 15, 36, 5)             # deck 1, y15-19, floor 20
    m.room(143, 24, 36, 5)             # deck 2, y24-28, floor 29
    m.room(141, 33, 38, 6)             # deck 3, y33-38, floor 39
    m.room(172, 20, 6, 4)              # drop deck 1 -> 2, girders to climb back
    m.hl(172, 20, 3, '-')
    m.hl(175, 23, 3, '-')
    m.hl(172, 26, 3, '-')
    m.room(142, 29, 6, 4)              # drop deck 2 -> 3, girders to climb back
    m.hl(142, 36, 3, '-')
    m.hl(145, 33, 3, '-')
    m.hl(142, 30, 3, '-')
    # deck 1: a lava channel, hounds beyond it
    m.box(151, 20, 3, 2, '~')
    m.put(160, 19, GL)
    m.box(163, 17, 3, 3, '%')
    m.put(171, 19, GL)
    m.put(146, 18, '*')
    m.put(165, 16, '$')
    m.put(148, 16, 'l')
    m.put(168, 16, 'l')
    # secret 3: a fake ceiling over the crate, a loft above deck 1
    m.room(156, 10, 16, 4)
    m.box(156, 10, 16, 4, '?')
    m.box(163, 14, 2, 1, 'X')
    m.row(158, 13, '$.$.$')
    m.put(166, 13, 'c')
    m.put(169, 13, 's')
    # deck 2: westwards, cages
    m.box(169, 26, 2, 3, '%')
    m.put(164, 28, GL)
    m.put(157, 28, TL)
    m.put(150, 28, TA)
    m.box(153, 27, 3, 2, '%')
    m.put(148, 28, '+')
    m.put(160, 25, '*')
    m.put(175, 28, '$')
    m.put(172, 25, 'l')
    m.put(151, 25, 'l')
    # deck 3: eastwards to the exit hall
    m.box(152, 39, 3, 2, '~')
    m.put(160, 38, G)
    m.box(165, 36, 4, 3, '%')
    m.put(167, 35, T)
    m.put(175, 38, GA)
    m.put(146, 38, '&')
    m.put(172, 36, '*')
    m.row(157, 37, '$$')
    m.put(150, 35, 'l')
    m.put(171, 34, 'l')

    # ================================================================ G: exit hall (x179-197, y20-38)
    m.room(179, 20, 19, 19)
    m.sky(184, 21, 12, 10)
    m.hl(181, 36, 4, '-')
    m.box(186, 35, 4, 4, '%')
    m.box(190, 37, 1, 2, '%')
    m.put(188, 34, TL)
    m.put(184, 38, GA)
    m.hl(191, 32, 4, '-')
    m.hl(186, 29, 4, '-')
    m.hl(192, 26, 4, '-')
    m.put(194, 25, '*')
    m.put(182, 35, '$')
    m.put(187, 28, '$')
    m.put(195, 38, 'E')
    m.put(181, 23, 'L')
    m.put(193, 35, 'l')
    return m


if __name__ == '__main__':
    main(build, 'e4l1')
