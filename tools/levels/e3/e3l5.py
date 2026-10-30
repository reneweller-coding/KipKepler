"""e3l5 Brine Lake / Solesee -- a huge cavern over a lake of brine, crumbling ice bridges, shardlings.

West to east across the lake: the boathouse (start, a fake wall) -> a crumble bridge over a dry hollow (sign: keep
moving) -> island 1 -> a single crumble stone -> island 2 (checkpoint) -> a long crumble bridge with a rest
-> island 3 (spring up to the high route) -> island 4 with a cave inside (blue key, a vault behind breakable crystal)
-> a rail platform -> island 5 (spring) -> island 6 (checkpoint) -> stepping stones -> the east shore and the
gatehouse (blue door, exit). The high route along crystal ledges under the stalactites (icebats, cryoturrets)
holds crystals and treasure and a hidden niche; it can be left anywhere by dropping onto the islands.
"""
from lvl import Lv, main

W, H = 240, 58
S = 50   # the brine's surface row


def build():
    L = Lv(W, H)
    L.legend.update({
        'i': 'sign sign.e3l5.crumble',
        'x': 'mover 15 0 70 0.8',
        'L': 'light cyan 6',
    })

    # ---- the cavern and the lake --------------------------------------------------------------------------
    L.runs(22, [(12, 24, S), (20, 18, S), (16, 15, S), (20, 17, S), (20, 13, S), (32, 15, S), (20, 14, S),
                (22, 16, S), (22, 18, S), (10, 21, S), (24, 26, S)], ' ')
    L.fill(34, S, 181, 4, '~')
    # stalactites
    for x0, w, bottom in [(40, 3, 20), (60, 4, 18), (78, 3, 22), (96, 5, 16), (116, 3, 26), (130, 4, 22),
                          (146, 3, 24), (168, 4, 22), (190, 3, 23), (200, 4, 20)]:
        # tapered: one cell narrower every three rows, hanging from the ceiling
        for row in range(8, bottom + 1):
            cut = max(0, (row - (bottom - 3 * (w - 1) - 2)) // 3)
            ww = max(1, w - cut)
            L.fill(x0 + (w - ww + 1) // 2, row, ww, 1, '%')

    # ---- the boathouse and the west shore (floor 46) ------------------------------------------------------
    L.fill(4, 38, 18, 8, '.')
    L.set(6, 45, 'P')
    L.put(10, 43, '----')
    L.put(11, 42, '$$')
    L.set(16, 45, '&')
    L.set(19, 45, 'i')
    # secret 1: the boathouse's back room
    L.col(3, 44, 'XX')
    L.fill(0, 43, 3, 3, '?')
    L.put(0, 45, '$+$')
    L.fill(22, 46, 12, 8, '#')
    L.fill(22, 46, 6, 3, ' ')               # a dry hollow under the first crumble bridge (3 deep: climb out)
    L.put(22, 46, '______')
    L.set(25, 44, '*')
    L.put(29, 45, '$$')

    # ---- island 1 and the first real bridge ---------------------------------------------------------------
    L.put(34, 46, '________')
    L.put(36, 44, '$')
    L.put(39, 44, '$')
    L.fill(42, 46, 9, 8, '#')
    L.fill(48, 44, 2, 2, '%')
    L.set(45, 45, '*')
    L.set(44, 45, 'h')
    L.put(54, 46, '__')                      # a single crumble stone
    L.set(54, 44, '$')
    L.set(55, 44, '$')

    # ---- island 2 (checkpoint) ------------------------------------------------------------------------------
    L.fill(59, 44, 14, 10, '#')
    L.fill(64, 41, 3, 3, '%')
    L.set(65, 40, '*')
    L.set(61, 43, 'C')
    L.set(70, 43, '+')
    L.set(68, 43, 'h')
    L.set(71, 43, '*')

    # ---- the long bridge with a rest -------------------------------------------------------------------------
    L.put(73, 45, '_' * 10)
    L.put(83, 43, '----')
    L.put(87, 45, '_' * 6)
    L.set(78, 43, '$')
    L.set(84, 42, '*')
    L.set(90, 43, '$')

    # ---- island 3: a spring up to the high route -----------------------------------------------------------
    L.fill(93, 46, 8, 8, '#')
    L.set(97, 45, '@')
    L.set(94, 45, '$')
    L.set(100, 45, 'n')
    L.put(101, 47, '_' * 10)
    L.put(104, 45, '$$')
    L.put(108, 45, '*')

    # ---- island 4: the key cave ------------------------------------------------------------------------------
    L.fill(111, 43, 30, 11, '#')
    L.fill(116, 44, 22, 5, '.')
    L.put(118, 43, '..')
    L.put(134, 43, '..')
    L.put(117, 46, '----')
    L.put(133, 46, '----')
    L.set(126, 48, 'k')
    L.put(123, 48, '$$')
    L.set(129, 48, '*')
    L.set(131, 48, 'a')
    L.set(121, 48, 'a')
    L.set(125, 42, 'C')
    L.set(138, 42, 'h')
    L.set(114, 42, '+')
    L.set(122, 42, '*')
    L.set(126, 45, 'L')
    # secret 2: a vault behind breakable crystal at the cave's west end
    L.col(115, 47, 'BB')
    L.fill(112, 46, 3, 3, '?')
    L.put(112, 48, 'H$I')
    L.set(113, 47, '$')

    # ---- the rail platform to island 5 -----------------------------------------------------------------------
    L.put(141, 43, 'xxx')
    L.put(149, 40, '$*$')
    L.fill(159, 45, 10, 9, '#')
    L.set(160, 44, '@')
    L.set(162, 44, '$')
    L.set(167, 44, 'h')
    L.put(169, 46, '_' * 8)
    L.put(177, 44, '----')
    L.put(181, 46, '_' * 4)
    L.set(178, 43, '*')
    L.set(172, 44, '$')
    L.set(183, 44, '$')

    # ---- island 6 (checkpoint) and the stepping stones -------------------------------------------------------
    L.fill(185, 44, 8, 10, '#')
    L.set(187, 43, 'C')
    L.set(191, 43, '&')
    L.put(196, 45, '__')
    L.put(200, 43, '----')
    L.put(206, 45, '__')
    L.put(210, 44, '---')
    L.set(201, 42, '*')
    L.set(196, 43, '$')
    L.set(207, 43, '$')

    # ---- the east shore and the gatehouse -------------------------------------------------------------------
    L.fill(215, 46, 25, 8, '#')
    L.fill(221, 34, 19, 12, '#')
    L.fill(222, 37, 16, 9, '.')
    L.col(221, 43, 'ddd')
    L.set(234, 45, 'E')
    L.put(226, 45, '$$')
    L.put(224, 43, '---')
    L.put(225, 42, '$$')
    L.set(229, 45, 'H')
    L.set(218, 45, 'n')
    L.set(216, 45, '*')

    # ---- the high route: crystal ledges under the stalactites -----------------------------------------------
    for x, y, w, c, items in [
            (94, 35, 7, '-', '$.$.$'), (104, 33, 5, '%', '.*.'), (112, 31, 6, '%', '$$'), (121, 33, 5, '%', '$$'),
            (129, 31, 6, '%', '.*'), (138, 33, 5, '%', '$$'), (146, 35, 6, '%', '.*'), (155, 36, 8, '-', '$....$'),
            (166, 34, 5, '%', '.*'), (174, 32, 5, '%', '$$'), (182, 34, 5, '%', '.*'),
            (85, 33, 6, '%', '$$'), (76, 31, 6, '%', '.*'), (67, 33, 6, '%', '$$'), (58, 35, 6, '%', '$$$'),
            (54, 32, 3, '%', '')]:
        L.put(x, y, c * w)
        L.put(x + 1, y - 1, items, skip='.')
    for x, y in [(117, 27), (147, 25), (169, 23), (79, 23)]:
        L.set(x, y, 'b')
    L.set(131, 23, 'u')
    L.set(191, 24, 'u')
    L.set(61, 19, 'u')
    L.set(124, 32, 'a')
    L.set(177, 31, 'n')
    L.set(141, 32, 'h')
    L.set(62, 34, 'a')
    # secret 3: a niche in a crystal block above the westernmost ledges
    L.fill(48, 28, 6, 5, '%')
    L.fill(49, 29, 4, 3, '?')
    L.col(53, 30, 'XX')
    L.put(49, 31, 'p$$')
    # secret 4: under the east shore, a fake wall below the last stepping stone
    L.col(215, 48, 'XX')
    L.fill(216, 47, 4, 3, '?')
    L.put(216, 49, '$R$$')
    L.put(211, 50, '----')                    # a jetty to it, and a rest to climb back
    L.put(212, 47, '--')
    for x, y, c in [(43, 45, 'a'), (85, 42, 'h'), (132, 42, 'a'), (164, 44, 'a'), (116, 30, 'a'), (219, 45, 'h'),
                    (232, 45, 'A'), (202, 42, 'n'), (63, 43, '&'), (136, 48, '&'), (166, 44, '&'), (217, 45, '&'),
                    (95, 45, '+'), (183, 33, 'H'), (80, 43, '*'), (189, 43, '*')]:
        L.set(x, y, c)
    for x, y in [(28, 40), (46, 41), (66, 37), (86, 40), (106, 41), (126, 38), (150, 42), (172, 40), (194, 40),
                 (214, 40), (230, 39)]:
        L.set(x, y, 'L')
    return L


META = [
    ('name', 'Brine Lake'),
    ('name.de', 'Solesee'),
    ('theme', 'crystal'),
    ('tint', '1'),
    ('bg', 'crystal_b'),
    ('music', 'e3_crystal'),
    ('dark', '0.3'),
    ('par', '330'),
]

if __name__ == '__main__':
    main(build, 'e3l5', META)
