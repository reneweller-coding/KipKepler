"""e3l6 Prism Halls / Prismenhallen -- plasma mortar, switches with toggle blocks, teleporters.

The vestibule (start, the mortar, sign; a sunken pit of crabs and a minerbot on a shelf: what the mortar is for)
-> the prism atrium (hub): a tall open hall of catwalks; its top leads to the exit behind three crystal gates
(groups A, B, C; sign). From the atrium:
  teleporter 1 -> the mirror halls (NW wing, three halls stacked; switch A at the top; A also builds a bridge),
  the doorway on the east catwalk -> the lens works (E wing; switch B before a brine pit, B builds its bridge),
  teleporter 3 -> the prism vaults (SE wing; mortar fights, switch C, C raises steps to a vault).
Every wing has a pad back to the atrium. Teleporters land on invisible 'arrive' markers beside the pads, so the
hero never lands on a pad (which would send him straight back).
"""
from lvl import Lv, main

W, H = 196, 66


def build():
    L = Lv(W, H)
    L.legend.update({
        'W': 'weapon mortar',
        'i': 'sign sign.e3l6.mortar',
        'j': 'sign sign.e3l6.gates',
        '1': 'teleport 5',
        '2': 'teleport 6',
        '3': 'teleport 7',
        '4': 'teleport 8',
        '5': 'arrive',
        '6': 'arrive',
        '7': 'arrive',
        '8': 'arrive',
        '9': 'teleport 6',
        'S': 'switch A',
        'T': 'switch B',
        'Y': 'switch C',
        '[': 'toggle A solid',
        ']': 'toggle A empty',
        '{': 'toggle B solid',
        '}': 'toggle B empty',
        '(': 'toggle C solid',
        ')': 'toggle C empty',
        'L': 'light violet 6',
        'M': 'light cyan 6',
    })

    # ==== the vestibule (x 2-81, floor 56) =====================================================================
    L.fill(2, 46, 80, 10, '.')
    L.fill(14, 42, 20, 4, '.')
    L.set(4, 55, 'P')
    L.set(8, 55, 'i')
    L.set(12, 55, 'W')
    L.put(16, 53, '-----')
    L.set(18, 52, '*')
    L.put(15, 50, '---')
    L.put(15, 49, '$$')
    # the mortar's first lesson: crabs down in a pit, a minerbot up on a shelf
    L.fill(24, 56, 15, 3, '.')
    L.put(30, 50, '%%%%%%%%')
    L.put(39, 53, '---')
    L.set(34, 49, 'n')
    L.put(31, 49, '$$')
    L.set(28, 58, 'a')
    L.set(34, 58, 'a')
    L.set(31, 58, '*')
    L.put(36, 58, '$$')
    # secret 1: a cellar behind the pit's east wall
    L.col(39, 57, 'XX')
    L.fill(40, 57, 5, 2, '?')
    L.put(41, 58, '$&$$')
    L.fill(46, 46, 2, 5, '%')
    L.fill(60, 46, 2, 4, '%')
    L.put(64, 53, '----')
    L.set(66, 52, '*')
    L.set(44, 55, '*')
    L.put(52, 55, '$$')
    L.set(50, 55, 'a')
    L.set(57, 55, 'h')
    L.set(72, 55, 'n')
    L.set(77, 55, '+')
    L.set(69, 55, '&')
    for x, y, c in [(6, 48, 'L'), (20, 44, 'M'), (34, 45, 'L'), (48, 47, 'M'), (62, 48, 'L'), (76, 48, 'M')]:
        L.set(x, y, c)

    # ==== the prism atrium (hub, x 82-111, rows 18-55, floor 56) =============================================
    L.fill(82, 18, 30, 38, ' ')
    L.set(85, 55, '1')
    L.set(88, 55, '6')
    L.set(108, 55, '3')
    L.set(105, 55, '8')
    L.set(96, 55, 'j')
    L.set(92, 55, 'C')
    L.set(160, 56, '+')
    L.set(100, 55, '&')
    for y in (53, 47, 41, 35, 29, 23):
        L.put(84, y, '-' * 6)
        L.put(104, y, '-' * 6)
    for y in (50, 44, 38, 32, 26):
        L.put(92, y, '-' * 10)
    L.put(104, 35, '-' * 8)                  # the east catwalk reaches the doorway
    L.put(82, 41, '--')                      # and the west one the hidden alcove
    L.put(96, 20, '-' * 16)                  # the top catwalk, to the gates
    L.set(87, 46, '*')
    L.set(97, 43, '*')
    L.set(106, 28, '*')
    L.set(88, 22, '*')
    L.set(100, 31, '*')
    for x, y in [(94, 49), (99, 49), (106, 52), (86, 34), (95, 37), (101, 25), (98, 19)]:
        L.set(x, y, '$')
    L.set(96, 43, 'a')
    L.set(98, 31, 'a')
    L.set(90, 19, 'b')
    L.set(106, 19, 'b')
    for x, y, c in [(84, 50, 'L'), (109, 44, 'M'), (84, 32, 'M'), (109, 26, 'L'), (96, 22, 'M')]:
        L.set(x, y, c)
    # secret 4: an alcove behind the atrium's west wall
    L.col(81, 39, 'XX')
    L.fill(77, 38, 4, 3, '?')
    L.put(77, 40, 'IH$p')
    # the gates and the exit room
    L.fill(112, 17, 7, 3, '.')
    L.col(113, 17, '[[[')
    L.col(115, 17, '{{{')
    L.col(117, 17, '(((')
    L.fill(119, 14, 12, 6, '.')
    L.set(126, 19, 'E')
    L.put(121, 19, '$$')
    L.put(129, 19, '$')
    L.set(124, 15, 'L')

    # ==== the lens works (E wing, rows 22-38) ==================================================================
    L.fill(112, 32, 14, 3, '.')              # the doorway corridor (floor 35)
    L.runs(126, [(12, 26, 35), (12, 24, 35), (11, 25, 35)])     # hall E2, x 126-160
    L.fill(132, 24, 2, 4, '%')
    L.fill(146, 22, 3, 4, '%')
    L.put(128, 32, '----')
    L.put(136, 29, '%%%%%')
    L.put(143, 32, '----')
    L.put(150, 29, '%%%%%')
    L.put(137, 28, '$*$')
    L.put(151, 28, '$*$')
    L.set(140, 28, 'n')
    L.set(156, 34, 'a')
    L.set(129, 34, '+')
    L.set(147, 26, 'b')
    # hall E3, x 161-194: switch B, a brine pit that B bridges
    L.runs(161, [(8, 25, 37), (16, 22, 37), (9, 26, 37)])
    L.fill(169, 37, 12, 2, '~')
    L.put(169, 37, '}' * 12)                 # B's bridge over the brine
    L.set(164, 36, 'T')
    L.set(186, 36, '*')
    L.put(188, 36, '$$$')
    L.set(183, 36, 'h')
    L.set(176, 33, '$')
    L.set(174, 33, '$')
    L.set(175, 32, '*')
    L.put(173, 34, '----')
    L.set(191, 36, 'H')
    # secret 3: a store behind the lens hall's south wall... reached from the east end
    L.col(194, 35, 'XX')
    L.fill(195, 34, 1, 3, '?')
    L.set(195, 36, 'R')
    for x, y, c in [(118, 33, 'M'), (130, 28, 'L'), (142, 26, 'M'), (156, 28, 'L'), (166, 30, 'M'), (178, 26, 'L'),
                    (190, 30, 'M')]:
        L.set(x, y, c)

    # ==== the prism vaults (SE wing, rows 42-62) ==============================================================
    L.runs(114, [(27, 48, 57)])              # V1, x 114-140
    L.set(115, 56, '4')
    L.set(118, 56, '7')
    L.set(123, 56, '+')
    L.put(128, 54, '---')
    L.put(129, 53, '$$')
    L.set(134, 56, 'a')
    L.set(138, 56, '*')
    # V2, x 141-170: a mortar arena (shelves above, a sunken floor below)
    L.runs(141, [(30, 42, 57)])
    L.fill(148, 57, 16, 3, '.')
    L.put(142, 54, '----')
    L.put(146, 51, '-----')
    L.put(153, 48, '----')
    L.put(160, 49, '-----')
    L.set(148, 50, 'n')
    L.set(162, 48, 'n')
    L.set(154, 47, '*')
    L.put(164, 48, '$')
    L.set(152, 59, 'a')
    L.set(158, 59, 'h')
    L.set(155, 59, '*')
    L.put(149, 59, '$$')
    L.set(166, 56, '&')
    # V3, x 171-194: switch C, and C's steps up to a vault
    L.runs(171, [(24, 44, 59)])
    L.set(190, 58, 'Y')
    L.put(175, 56, ')))')
    L.put(178, 53, ')))')
    L.put(181, 50, ')))')
    L.fill(184, 44, 11, 5, '#')
    L.fill(184, 45, 10, 3, '.')
    L.put(186, 47, '$*$$I')
    L.set(176, 58, 'a')
    L.set(186, 58, 'N')
    L.set(181, 58, '*')
    L.set(173, 58, '$')
    for x, y, c in [(120, 50, 'L'), (132, 50, 'M'), (146, 45, 'L'), (158, 44, 'M'), (168, 47, 'L'), (176, 48, 'M'),
                    (190, 52, 'L')]:
        L.set(x, y, c)

    # ==== the mirror halls (NW wing, x 2-78) ==================================================================
    # N1: rows 29-35, floor 36 (arrival, the pad back)
    L.fill(2, 29, 77, 7, '.')
    L.set(4, 35, '2')
    L.set(7, 35, '5')
    L.fill(30, 36, 4, 2, '~')
    L.set(29, 35, '#')
    L.set(34, 35, '#')
    L.put(30, 33, '$*')
    L.set(20, 35, 'a')
    L.set(45, 35, 'n')
    L.set(58, 35, 'h')
    L.set(52, 35, '*')
    L.put(40, 32, '----')
    L.put(41, 31, '$$')
    L.set(66, 35, '&')
    # up into N2 at the east end
    L.fill(72, 27, 6, 2, '.')
    L.put(70, 33, '---')
    L.put(74, 30, '----')
    # N2: rows 19-26, floor 27 (walk west)
    L.fill(2, 19, 77, 8, '.')
    L.fill(44, 27, 4, 2, '~')
    L.set(43, 26, '#')
    L.set(48, 26, '#')
    L.set(46, 23, '*')
    L.fill(16, 24, 3, 3, '%')               # crystal blocks
    L.fill(24, 19, 2, 4, '%')
    L.put(16, 23, '$*$')
    L.set(54, 26, 'a')
    L.set(69, 26, 'C')
    L.set(38, 26, '+')
    L.set(33, 26, 'h')
    L.set(55, 22, 'b')
    L.set(10, 26, '+')
    # up into N3 at the west end
    L.fill(3, 16, 6, 3, '.')
    L.put(8, 24, '---')
    L.put(4, 21, '----')
    L.put(6, 18, '---')
    # N3: rows 6-15, floor 16 (walk east): switch A at the east end
    L.fill(2, 8, 77, 8, '.')
    L.fill(20, 5, 30, 3, '.')
    L.put(24, 13, '%%%')
    L.put(30, 10, '%%%')
    L.put(25, 12, '$')
    L.set(31, 9, '*')
    L.set(30, 15, 'n')
    L.set(50, 15, 'a')
    L.set(40, 6, 'b')
    L.set(58, 15, '*')
    L.put(55, 15, '$$')
    L.set(64, 15, 'S')
    L.fill(67, 16, 8, 3, '~')               # brine that only A's blocks bridge
    L.put(67, 16, ']' * 8)
    L.set(70, 13, '$')
    L.set(72, 13, '$')
    L.set(77, 15, '9')                       # a pad back to the atrium
    # secret 2: breakable crystal at N3's east end
    L.col(79, 14, 'BB')
    L.fill(80, 13, 2, 3, '?')
    L.set(80, 15, '$')
    L.set(81, 15, '$')
    for x, y, c in [(12, 31, 'L'), (26, 31, 'M'), (40, 30, 'L'), (54, 31, 'M'), (68, 31, 'L'), (66, 21, 'M'),
                    (52, 21, 'L'), (38, 21, 'M'), (24, 21, 'L'), (10, 21, 'M'), (10, 10, 'L'), (24, 7, 'M'),
                    (38, 8, 'L'), (52, 10, 'M'), (66, 10, 'L')]:
        L.set(x, y, c)
    return L


META = [
    ('name', 'Prism Halls'),
    ('name.de', 'Prismenhallen'),
    ('theme', 'crystal'),
    ('tint', '2'),
    ('bg', 'crystal_a'),
    ('music', 'e3_crystal'),
    ('dark', '0.3'),
    ('par', '420'),
]

if __name__ == '__main__':
    main(build, 'e3l6', META)
