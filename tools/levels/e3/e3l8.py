"""e3l8 Heart of the Comet / Herz des Kometen -- everything, wisps, both keys; dark, lit by crystal lamps.

A the entry tunnel (start; sign: wisps drift through rock) -> a crystal stair down -> the Heart: a vast open
chamber around a floating diamond of crystal, the exit shrine on its top behind two gold doors; two ore lifts up
the diamond's flanks, cryoturrets under it, wisps around it.
From the Heart: teleporter 1 -> C, the old drill works in the north (crushers, a lift, the blue key; a pad back);
the east passage -> E, the labyrinth (switch A opens the upper gallery's gate; switch B a vault; a teleporter
back down); the hole in the floor -> D, the brine caverns in the south (crumble bridges, rail platforms, springs)
-> the blue door -> the gold key -> back up to the shrine.
A shaft from the entry tunnel also drops into D's west end (catwalks lead back up).
"""
from lvl import Lv, main

W, H = 236, 80


def build():
    L = Lv(W, H)
    L.legend.update({
        'i': 'sign sign.e3l8.wisps',
        'm': 'mover 0 -23 90 1.0',
        'q': 'mover 0 -16 80 1.0',
        'x': 'mover 8 0 70 0.8',
        'y': 'mover 8 0 70 0.8',
        'V': 'crusher 2 2.8',
        'F': 'crusher 2 3.4',
        '1': 'teleport 5',
        '2': 'teleport 6',
        '3': 'teleport 7',
        '4': 'teleport 8',
        '5': 'arrive',
        '6': 'arrive',
        '7': 'arrive',
        '8': 'arrive',
        'S': 'switch A',
        'T': 'switch B',
        '[': 'toggle A solid',
        '{': 'toggle B solid',
        'L': 'light cyan 7',
        'M': 'light magenta 6',
        'Z': 'light violet 6',
    })

    def lamps(points):
        cycle = 'LMZ'
        for n, (x, y) in enumerate(points):
            L.set(x, y, cycle[n % 3])

    # ==== A: the entry tunnel ====================================================================================
    L.fill(5, 34, 37, 8, '.')                 # A1, x 5-41, floor 42
    L.set(7, 41, 'P')
    L.set(11, 41, 'i')
    L.put(14, 39, '---')
    L.put(15, 38, '$$')
    L.set(30, 41, '*')
    L.put(34, 41, '$$')
    L.set(36, 36, 'O')
    L.set(38, 41, 'a')
    for k in range(10):                       # A2: a stair of crystal down to A3
        x, fl = 42 + 2 * k, 43 + k
        L.fill(x, fl - 5, 2, 5, '.')
        L.fill(x, fl, 2, 1, '%')
    L.set(47, 42, '$')
    L.set(53, 44, '*')
    L.set(58, 47, '$')
    L.fill(62, 47, 30, 6, '.')                # A3, floor 53
    L.put(66, 52, '$$')
    L.set(74, 52, 'h')
    L.set(80, 52, '*')
    L.set(84, 49, 'O')
    L.set(70, 52, '+')
    L.set(88, 52, 'n')
    # the shaft from A1 down into D's west end (catwalks to climb back; walk over its top)
    L.fill(20, 42, 4, 21, '.')
    L.put(20, 42, '----')
    for y, x in [(45, 20), (48, 22), (51, 20), (54, 22), (57, 20), (60, 22)]:
        L.put(x, y, '--')
    L.set(21, 56, '$')
    lamps([(8, 36), (18, 36), (32, 37), (46, 40), (56, 45), (66, 49), (78, 49), (89, 49), (22, 50), (22, 66)])
    # secret 1: behind the entry's west wall
    L.col(4, 40, 'XX')
    L.fill(1, 39, 3, 3, '?')
    L.put(1, 41, '$$&')

    # ==== the Heart: x 92-146, rows 6-59, floor 60 =================================================================
    L.fill(92, 6, 55, 54, ' ')
    for r in range(26, 47):                   # the floating diamond
        hw = 4 + min(r - 26, 46 - r)
        L.fill(119 - hw, r, 2 * hw + 1, 1, '%')
    L.fill(113, 20, 13, 6, '#')               # the shrine on its top
    L.fill(114, 21, 11, 5, '.')
    L.fill(113, 26, 13, 1, '%')
    L.col(113, 23, 'DDD')
    L.col(125, 23, 'DDD')
    L.set(119, 25, 'E')
    L.put(116, 25, '$')
    L.put(122, 25, '$')
    L.put(109, 26, '----')                    # landings at the gold doors (jump up through them)
    L.put(126, 26, '----')
    L.put(101, 59, 'mmm')                     # the lifts up the flanks (to row 36)
    L.put(135, 59, 'mmm')
    L.put(92, 57, '----')                     # catwalks back up to A3
    L.put(92, 54, '---')
    for x, y in [(108, 32), (130, 32), (105, 35), (112, 28), (119, 59)]:
        L.set(x, y, '*')
    for x, y in [(126, 28), (133, 35), (110, 31), (128, 31), (116, 59), (122, 59)]:
        L.set(x, y, '$')
    L.set(110, 42, 'u')                       # cryoturrets under the diamond
    L.set(128, 42, 'u')
    for x, y in [(100, 28), (139, 28), (119, 52), (97, 44), (142, 44)]:
        L.set(x, y, 'O')
    L.set(108, 59, 'a')
    L.set(131, 59, 'a')
    L.set(95, 59, '1')                        # to the drill works
    L.set(98, 59, '6')
    L.set(105, 59, 'H')
    L.set(113, 59, '&')
    L.set(126, 59, 'C')
    L.fill(140, 60, 4, 3, '.')                # the hole down to the brine caverns
    lamps([(96, 50), (106, 48), (119, 55), (132, 48), (143, 50), (98, 30), (140, 30), (119, 14), (104, 18), (134, 18)])

    # ==== C: the drill works (north), reached by teleporter ========================================================
    L.fill(50, 22, 41, 8, '.')                # C1, x 50-90, floor 30
    L.set(86, 29, '5')
    L.set(89, 29, '2')
    L.set(80, 29, '+')
    L.put(70, 26, '----')
    L.put(71, 25, '$*$')
    L.set(62, 29, 'n')
    L.set(56, 24, 'O')
    L.fill(20, 27, 30, 3, '.')                # C2: the crusher corridor, rows 27-29
    for x, c in [(24, 'V'), (29, 'F'), (34, 'V'), (39, 'F'), (44, 'V')]:
        L.set(x, 27, c)
    L.put(31, 29, '$')
    L.put(41, 29, '$')
    L.fill(3, 10, 17, 20, '.')                # C3: the lift hall, x 3-19, rows 10-29
    L.put(8, 29, 'qqq')                       # up to row 13
    L.set(14, 29, '*')
    L.put(12, 22, '---')
    L.put(13, 21, '$$')
    L.set(16, 29, 'a')
    L.set(5, 11, 'b')
    L.fill(20, 6, 41, 7, '.')                 # C4: the upper hall, x 20-60, rows 6-12, floor 13
    L.fill(11, 13, 9, 1, '%')                # the walk from the lift's top into the upper hall
    L.put(28, 12, '%%')
    L.set(28, 11, '*')
    L.set(36, 12, 'h')
    L.set(44, 12, 'n')
    L.put(48, 9, '----')
    L.put(49, 8, '$$')
    L.set(58, 12, 'k')
    L.put(55, 12, '$$')
    L.set(52, 7, 'u')
    lamps([(84, 24), (72, 23), (60, 24), (46, 28), (34, 28), (22, 28), (10, 14), (14, 25), (26, 8), (40, 8),
           (54, 8)])
    # secret 2: a store behind the upper hall's east wall
    L.col(61, 11, 'XX')
    L.fill(62, 10, 4, 3, '?')
    L.put(62, 12, 'R$p$')

    # ==== E: the labyrinth (east) ==================================================================================
    L.fill(147, 56, 4, 4, '.')                # the east passage
    L.fill(151, 52, 50, 8, '.')               # E1, x 151-200, floor 60
    L.set(190, 59, 'S')                       # switch A (opens the gallery's gate)
    L.set(160, 59, 'n')
    L.set(172, 59, 'w')
    L.set(178, 59, 'a')
    L.set(166, 55, 'O')
    L.put(176, 56, '----')
    L.put(177, 55, '$*')
    L.set(156, 59, '7')                       # arrival from the gallery's teleporter
    L.set(195, 59, '+')
    L.fill(201, 10, 32, 50, '.')              # E2, the tall hall, x 201-232, rows 10-59
    for y, x in [(57, 228), (54, 224), (51, 228), (48, 224), (45, 228), (42, 224), (39, 228), (36, 224), (33, 228),
                 (30, 224), (27, 228), (24, 224), (21, 228), (18, 224)]:
        L.put(x, y, '----')
    for x, y, w in [(203, 50, 6), (210, 44, 6), (203, 38, 6), (210, 32, 6), (203, 26, 6)]:
        L.put(x, y, '%' * w)
    L.put(209, 29, '---')
    L.put(217, 50, '---')
    L.put(217, 38, '---')
    L.put(217, 26, '---')
    L.set(205, 49, '*')
    L.put(211, 43, '$$')
    L.set(205, 37, '*')
    L.put(212, 31, '$$')
    L.set(205, 25, '$')
    L.set(230, 44, '&')
    L.set(213, 43, 'a')
    L.set(207, 37, 'n')
    L.set(226, 11, 'b')
    L.set(209, 11, 'b')
    L.set(220, 30, 'O')
    L.set(215, 52, 'O')
    # E3: the upper gallery, x 150-200, rows 12-18, floor 19 (from E2's top catwalk)
    L.fill(150, 12, 51, 7, '.')
    L.fill(201, 19, 23, 1, '%')               # the walk from E2's top catwalk into the gallery
    L.fill(201, 44, 6, 1, '%')                # a ledge to B's vault
    L.set(212, 18, '&')
    L.col(185, 16, '[[[')                     # the gate (switch A)
    L.set(196, 18, '*')
    L.put(190, 18, '$$')
    L.set(180, 18, 'n')
    L.set(170, 18, '*')
    L.put(164, 18, '$$')
    L.set(160, 18, 'T')                       # switch B
    L.set(154, 18, '3')                       # a teleporter back down to E1
    L.set(157, 18, '8')
    L.set(175, 13, 'u')
    L.set(166, 14, 'O')
    # B's vault in E2's wall
    L.fill(195, 40, 6, 4, '.')
    L.col(200, 41, '{{{')
    L.put(196, 43, 'I$H$')
    L.set(196, 42, '*')
    L.put(197, 44, '##')
    lamps([(155, 54), (168, 53), (182, 54), (196, 54), (206, 56), (226, 50), (206, 44), (226, 38), (206, 32),
           (226, 26), (206, 20), (226, 14), (194, 14), (180, 14), (168, 15), (156, 14), (197, 41)])

    # ==== D: the brine caverns (south), rows 63-77, floor 78 =======================================================
    L.fill(2, 63, 196, 15, ' ')               # x 2-197
    L.fill(30, 75, 166, 3, '~')               # the lake (rows 75-77), shores and islands below
    L.fill(2, 75, 28, 3, '#')                 # west shore x 2-29 (top 75)
    for x0, w, top in [(44, 6, 72), (66, 8, 73), (90, 6, 72), (112, 6, 73), (138, 8, 72), (164, 6, 73),
                       (184, 14, 75)]:
        L.fill(x0, top, w, 78 - top, '#')
    L.put(30, 74, '_' * 14)                   # crumble bridge to island 1
    L.put(50, 74, '_' * 4)
    L.put(56, 72, 'xxx')                      # rail platform x 56 -> 64
    L.put(74, 74, '_' * 4)
    L.put(80, 72, '----')
    L.put(84, 74, '_' * 6)
    L.put(96, 72, 'yyy')                      # rail platform x 96 -> 104
    L.put(118, 74, '_' * 8)
    L.put(126, 71, '----')
    L.put(130, 74, '_' * 8)
    L.put(146, 74, '_' * 6)
    L.put(152, 71, '----')
    L.put(156, 74, '_' * 8)
    L.put(170, 74, '_' * 14)
    for x, y in [(46, 71), (114, 72), (166, 72)]:
        L.set(x, y, '@')                      # springs up to the high ledges
    for x, y, w in [(40, 66, 6), (108, 65, 7), (162, 66, 6)]:
        L.put(x, y, '%' * w)
    L.put(41, 65, '$*$')
    L.put(109, 64, '$$*$$')
    L.put(163, 65, '$*$')
    for y, x in [(63, 20), (66, 22), (69, 20), (72, 22)]:
        L.put(x, y, '--')                     # the shaft's lower catwalks (after D is carved)
    # catwalks below the Heart's hole (x 140-143) to climb back
    for y, x in [(70, 140), (67, 142), (64, 140)]:
        L.put(x, y, '--')
    L.set(68, 72, '*')
    L.set(92, 71, '*')
    L.set(140, 71, '+')
    L.put(76, 72, '$$')
    L.put(132, 72, '$$')
    L.put(176, 72, '$$$')
    L.set(10, 74, 'C')
    L.set(186, 74, 'C')
    for x, y, c in [(70, 72, 'h'), (93, 71, 'a'), (142, 71, 'a'), (167, 72, 'h'), (60, 66, 'O'), (128, 66, 'O'),
                    (176, 66, 'O'), (190, 74, 'n'), (26, 74, '&'), (194, 74, '+'), (112, 64, '&'),
                    (88, 52, '&')]:
        L.set(x, y, c)
    # the blue door and the gold key's vault, x 199-232
    L.col(198, 72, 'ddd')
    L.fill(199, 66, 34, 9, '.')
    L.set(229, 74, 'K')
    L.put(224, 74, '$$')
    L.put(214, 71, '----')
    L.put(215, 70, '$*$')
    L.set(208, 74, 'G')
    L.set(220, 74, 'a')
    L.set(226, 68, 'O')
    L.set(203, 74, 'H')
    lamps([(8, 66), (36, 68), (56, 66), (78, 68), (100, 66), (122, 68), (146, 66), (170, 68), (192, 66), (206, 68),
           (220, 68)])
    # secret 3: under the west shore
    L.col(2, 73, 'XX')
    L.fill(0, 72, 2, 3, '?')
    L.put(0, 74, '$$')
    # secret 4: a hollow in the Heart's diamond, entered from the lift's top (fake crystal)
    L.col(104, 34, 'XX')
    L.fill(105, 33, 3, 2, '?')
    L.put(105, 34, '$I')
    return L


META = [
    ('name', 'Heart of the Comet'),
    ('name.de', 'Herz des Kometen'),
    ('theme', 'crystal'),
    ('tint', '3'),
    ('bg', 'crystal_b'),
    ('music', 'e3_crystal'),
    ('dark', '0.55'),
    ('par', '540'),
]

if __name__ == '__main__':
    main(build, 'e3l8', META)
