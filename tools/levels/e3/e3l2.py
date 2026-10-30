"""e3l2 Frozen Shafts / Gefrorene Schaechte -- lancer weapon, icebats, long ice slides.

A big loop: the mine head (lancer, sign) -> a corridor of crabs in a line (what the lancer is for) -> shaft A down
(catwalks; optional pump room at its foot) -> slide 1 (sign) and slide 2, broken by a rock landing and a brine pit
-> the great ice cavern (brine lake with rock pillars, blue key, icebats under stalactites) -> the catwalks up its
east wall -> shaft B -> the upper gallery back west (ice floors, a dip, a fake floor) -> the blue door -> the exit
room above the mine head.
"""
from lvl import Lv, main

W, H = 200, 64


def build():
    L = Lv(W, H)
    L.legend.update({
        'W': 'weapon lancer',
        'i': 'sign sign.e3l2.lancer',
        'j': 'sign sign.e3l2.slide',
    })

    # ---- zone 1: the mine head and the crab corridor ------------------------------------------------------
    L.fill(6, 5, 20, 9, '.')                 # hall x 6-25, rows 5-13, floor 14
    L.fill(26, 10, 33, 4, '.')               # corridor to shaft A
    L.set(8, 13, 'P')
    L.set(12, 13, 'i')
    L.set(16, 13, 'W')
    L.put(18, 10, '-----')
    L.put(19, 9, '$*$')
    L.put(11, 11, '----')
    L.put(7, 8, '---')
    L.put(7, 7, '$$')
    L.set(24, 13, '&')
    # secret 1: behind the hall's west wall
    L.col(5, 12, 'XX')
    L.fill(1, 11, 4, 3, '?')
    L.put(1, 13, '$$+$')
    L.set(2, 12, '$')
    # the crabs come in a line: the lancer's beam goes through all of them
    for x in (42, 47, 52):
        L.set(x, 13, 'a')
    L.set(56, 13, '*')
    L.fill(30, 10, 3, 1, '#')                # ceiling beams
    L.fill(44, 10, 3, 1, '#')

    # ---- zone 2: shaft A and the pump room ------------------------------------------------------------------
    L.fill(59, 10, 8, 43, '.')               # x 59-66, rows 10-52, floor 53
    west, east = (59, 3), (64, 3)
    for y, side in [(17, west), (20, east), (23, west), (29, east), (32, west), (35, east), (38, west),
                    (41, east), (44, west), (47, east), (50, west)]:
        L.put(side[0], y, '-' * side[1])
    L.put(63, 26, '----')                    # the catwalk into slide 1
    L.set(60, 22, '*')
    L.set(65, 40, '*')
    L.put(65, 34, '$$')
    L.set(60, 31, '+')
    L.set(60, 49, '$')
    # pump room (optional, crystals): x 10-58, rows 45-52, floor 53
    L.fill(10, 45, 49, 8, '.')
    L.fill(10, 43, 14, 2, '.')               # a taller hall at its west end
    L.fill(30, 53, 4, 2, '~')                # brine channels in the floor
    L.fill(44, 53, 3, 2, '~')
    L.fill(36, 53, 6, 1, '%')                # ice between them, rock lips at both channels
    L.fill(36, 45, 2, 4, '#')                # a pump housing hanging from the ceiling
    L.put(12, 50, '----')
    L.put(16, 47, '----')
    L.put(17, 46, '*$')
    L.set(31, 50, '*')
    L.set(52, 52, '*')
    L.put(13, 49, '$$')
    L.set(20, 52, 'H')
    L.set(24, 52, '&')
    L.set(48, 52, 'n')
    L.set(27, 52, 'h')
    L.set(39, 49, 'b')
    # secret 2: a vault behind breakable blocks at the pump room's west end
    L.col(9, 51, 'BB')
    L.fill(4, 50, 5, 3, '?')
    L.put(4, 52, 'R$$&$')
    L.set(5, 51, '$')

    # ---- zone 3: the two slides ----------------------------------------------------------------------------
    # slide 1: steps 2 wide, 1 down, from x 67 (floor 26) to x 90 (floor 37); rock landing x 91-96 (floor 38)
    for j in range(12):
        x, fl = 67 + 2 * j, 26 + j
        L.fill(x, fl - 5, 2, 5, '.')
        L.fill(x, fl, 2, 1, '%')
    L.fill(91, 33, 6, 5, '.')
    L.fill(97, 33, 4, 9, '.')                # the brine pit
    L.fill(97, 42, 4, 3, '~')
    L.fill(101, 33, 3, 5, '.')               # rock landing on the far side
    # slide 2: steps 1 x 1 from x 104 (floor 39) to x 115 (floor 50); rock ledge x 116-121 (floor 50)
    for k in range(12):
        x, fl = 104 + k, 39 + k
        L.fill(x, fl - 6, 1, 6, '.')
        L.set(x, fl, '%')
    L.fill(116, 44, 6, 6, '.')
    L.set(65, 25, 'j')
    L.set(74, 27, '*')
    L.set(80, 30, '$')
    L.set(84, 32, '*')
    L.set(88, 34, '$')
    L.set(94, 37, '+')
    L.set(108, 41, '*')
    L.set(112, 45, '$')
    L.set(113, 46, '$')
    L.set(102, 37, '$')
    for x, y in [(77, 26), (89, 32), (110, 39)]:
        L.set(x, y, 'b')                     # icebats under the slide tunnels' ceilings
    L.set(118, 49, 'C')

    # ---- zone 4: the great cavern -----------------------------------------------------------------------------
    L.fill(122, 30, 61, 28, ' ')             # x 122-182, rows 30-57; shores at floor 58
    L.fill(135, 58, 33, 3, '~')              # the brine lake
    for x0, top in [(138, 55), (144, 53), (150, 51), (156, 53), (162, 55)]:
        L.fill(x0, top, 3, 61 - top, '#')
    L.set(151, 50, 'k')
    L.set(139, 54, '*')
    L.set(163, 54, '*')
    L.put(145, 52, '$')
    L.put(157, 52, '$')
    # stalactites with bats under them
    L.fill(141, 30, 7, 6, '#')
    L.fill(143, 36, 3, 8, '#')
    L.fill(153, 30, 7, 4, '#')
    L.fill(155, 34, 3, 9, '#')
    L.set(144, 44, 'b')
    L.set(156, 43, 'b')
    # west wall catwalks (from the slide ledge) up to a high niche
    for x, y, w in [(126, 55, 4), (122, 52, 4), (122, 47, 4), (127, 44, 4), (122, 41, 4), (127, 38, 5), (122, 35, 4)]:
        L.put(x, y, '-' * w)
    L.put(123, 40, '$*')
    L.put(128, 37, '$$')
    L.put(122, 32, '---')
    # secret 4: an alcove behind a fake wall at the top of the west catwalks
    L.fill(116, 30, 5, 2, '?')
    L.col(121, 30, 'XX')
    L.put(116, 31, '$Ip$$')
    L.set(124, 46, 'n')
    # shores
    L.set(126, 57, 'h')
    L.set(131, 57, '+')
    L.set(172, 57, 'n')
    L.set(178, 57, 'n')
    L.set(170, 57, '&')
    L.set(181, 57, 'H')
    # east wall catwalks up to shaft B
    for x, y, w in [(171, 55, 4), (176, 52, 5), (171, 49, 4), (176, 46, 5), (171, 43, 4), (176, 40, 5),
                    (171, 37, 4), (176, 34, 5), (180, 31, 3)]:
        L.put(x, y, '-' * w)
    L.set(178, 45, '*')
    L.put(172, 42, '$$')
    L.set(177, 33, '*')
    L.set(181, 39, 'b')
    L.set(172, 36, 'Q')

    # ---- shaft B: x 176-183, rows 9-29 ------------------------------------------------------------------------
    L.fill(176, 3, 8, 27, '.')
    for x, y in [(176, 28), (181, 25), (176, 22), (181, 19), (176, 16), (181, 13), (176, 10)]:
        L.put(x, y, '---')
    L.set(182, 18, '$')
    L.set(177, 21, '*')
    L.set(182, 12, '+')
    L.fill(184, 17, 5, 4, '.')               # a side room with treasure
    L.put(185, 20, '$$&')
    L.set(187, 19, 'N')

    # ---- zone 5: the upper gallery, x 50-175, rows 3-7, floor 8 ---------------------------------------------
    L.fill(50, 3, 126, 5, '.')
    L.set(170, 7, 'C')
    L.fill(146, 8, 18, 1, '%')               # an ice floor: a line of minerbots (lancer)
    for x in (150, 154, 158):
        L.set(x, 7, 'n')
    L.set(162, 7, '$')
    # a taller chamber with shelves and bats
    L.fill(132, 1, 16, 2, '.')
    L.put(134, 5, '----')
    L.put(141, 4, '----')
    L.put(135, 4, '$*$')
    L.put(142, 3, '$$')
    L.set(138, 2, 'b')
    L.set(146, 2, 'b')
    # the dip: ice steps down going west, a rock bottom, rock steps back up
    L.fill(110, 8, 22, 6, '#')
    for k in range(6):
        L.fill(130 - k, 3, 1, 6 + k, '.')
        L.set(130 - k, 9 + k, '%')
    L.fill(117, 3, 8, 11, '.')
    for k in range(6):
        L.fill(111 + k, 3, 1, 6 + k, '.')
    L.fill(117, 14, 8, 1, '#')
    for k in range(6):
        L.set(111 + k, 9 + k, '#')
    L.put(119, 13, '*$*')
    L.set(122, 13, 'a')
    # the fake floor (secret 3): a hidden store under the gallery
    L.put(96, 8, 'XXX')
    L.fill(92, 9, 12, 4, '?')
    L.put(92, 8, '--')
    L.put(92, 11, '----')
    L.put(97, 12, '$$H$$')
    L.set(102, 12, 'I')
    L.set(84, 7, 'a')
    L.set(104, 7, '*')
    # the pump channel: brine across the floor, rock lips both sides
    L.fill(74, 8, 4, 2, '~')
    L.fill(71, 1, 10, 2, '.')                # headroom for the jump
    L.put(73, 7, '#')
    L.put(78, 7, '#')
    L.set(75, 5, '$')
    L.set(76, 5, '$')
    L.set(66, 7, '*')
    L.set(62, 7, 'N')
    L.set(70, 7, '+')
    # the blue door and the exit room above the mine head
    L.col(49, 5, 'ddd')
    L.fill(26, 3, 23, 5, '.')               # (open to the mine head below: the start is never far)
    L.set(38, 7, 'E')
    L.put(44, 7, '$$')
    L.set(34, 7, 'N')
    # more enemies
    L.set(64, 10, 'b')
    L.set(93, 37, 'h')
    L.set(129, 57, 'a')
    L.set(100, 7, 'a')
    return L


META = [
    ('name', 'Frozen Shafts'),
    ('name.de', 'Gefrorene Schächte'),
    ('theme', 'ice'),
    ('tint', '2'),
    ('bg', 'ice_b'),
    ('music', 'e3_ice'),
    ('dark', '0.3'),
    ('par', '360'),
]

if __name__ == '__main__':
    main(build, 'e3l2', META)
