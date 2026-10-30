"""e3l4 Ore Elevators / Erzaufzuege -- big vertical movers (ore lifts), crushers, cryoturrets.

A zigzag up through four galleries of an ore mine, each joined to the next by a 19-tile ore lift:
G0 the loading dock (start; a rail platform over a harmless pit teaches movers, sign; first cryoturret) -> lift E1
(a fake wall half-way up) -> G1 the crusher line, going west (sign at the first crushers) -> lift E2 -> G2 the
turret hall, going east (a rail platform over brine, a hole down to the key chamber, the blue door) -> lift E3 ->
G3 the upper works, going west (more crushers, an optional lift to a high stash) -> lift E4 -> the exit room.
"""
from lvl import Lv, main

W, H = 160, 90
X0, X1 = 6, 150          # galleries span x 6-150


def gallery(L, floor, x0=X0, x1=X1):
    L.fill(x0, floor - 6, x1 - x0 + 1, 6, '.')


def build():
    L = Lv(W, H)
    L.legend.update({
        'm': 'mover 0 -19 80 1.0',
        'q': 'mover 0 -19 80 1.0',
        'r': 'mover 0 -19 80 1.0',
        's': 'mover 0 -13 70 1.0',
        't': 'mover 7 0 60 0.8',
        'x': 'mover 7 0 70 0.6',
        'y': 'mover 0 -9 60 1.0',
        'V': 'crusher 2 2.6',
        'F': 'crusher 2 3.2',
        'i': 'sign sign.e3l4.lift',
        'j': 'sign sign.e3l4.crusher',
    })

    # ==== G0: the loading dock (floor 84) =======================================================================
    gallery(L, 84)
    L.set(8, 83, 'P')
    L.set(25, 83, 'i')
    L.fill(30, 84, 10, 3, '.')               # a harmless pit (3 deep): the first rail platform
    L.put(30, 83, 'ttt')
    L.set(35, 80, '*')
    L.put(33, 81, '$')
    L.put(38, 81, '$')
    L.fill(44, 75, 27, 3, '.')               # a tall hall
    L.fill(50, 84, 16, 1, '%')               # an ice floor
    L.put(52, 81, '----')
    L.put(58, 78, '----')
    L.put(59, 77, '*$')
    L.put(53, 80, '$$')
    L.set(75, 78, 'u')                       # the first cryoturret, on the ceiling
    L.fill(84, 82, 2, 2, '#')                # ore heaps
    L.set(86, 83, '#')
    L.put(84, 81, '$$')
    L.set(95, 83, '*')
    L.fill(100, 82, 3, 2, '#')
    L.fill(128, 82, 3, 2, '#')
    L.set(129, 81, '*')
    L.put(112, 83, '&')
    L.set(118, 83, '$')
    L.set(122, 83, '$')
    L.set(134, 83, '+')
    L.set(70, 83, 'a')
    L.set(91, 83, 'n')
    L.set(108, 83, 'a')
    L.set(120, 83, 'n')
    L.set(65, 83, 'h')
    # lift E1 (x 140-144) up to G1
    L.fill(140, 64, 5, 14, '.')
    L.put(141, 83, 'mmm')
    L.set(142, 58, 'b')                      # a bat waits at the top of the lift
    # secret 1: a fake wall half-way up the lift shaft (a gem shows the spot)
    L.col(145, 70, 'XX')
    L.fill(146, 69, 4, 3, '?')
    L.put(146, 71, '$R$H')
    L.set(144, 69, '$')

    # ==== G1: the crusher line, going west (floor 64) ===========================================================
    gallery(L, 64)
    L.set(136, 63, 'C')
    L.set(131, 63, 'j')
    L.fill(112, 58, 17, 3, '#')              # crusher corridor A, rows 61-63
    for x in (115, 120, 125):
        L.set(x, 61, 'V')
    L.put(116, 63, '$')
    L.put(121, 63, '$')
    L.fill(90, 52, 21, 6, '.')               # a hall with a high ceiling
    L.put(93, 61, '----')
    L.put(99, 58, '----')
    L.put(105, 55, '----')
    L.put(100, 57, '$*')
    L.put(106, 54, '$$')
    L.set(96, 52, 'u')
    L.set(104, 63, '*')
    L.set(92, 63, 'n')
    L.fill(70, 64, 18, 1, '%')               # ice floor with minerbots
    L.set(76, 63, 'n')
    L.set(84, 63, 'N')
    L.set(80, 62, '*')
    L.set(68, 63, '&')
    L.fill(40, 58, 21, 3, '#')               # crusher corridor B, rows 61-63
    for x, c in ((43, 'F'), (48, 'V'), (53, 'F'), (58, 'V')):
        L.set(x, 61, c)
    L.set(50, 63, '$')
    L.set(56, 63, '$')
    L.set(62, 63, '+')
    L.fill(24, 64, 4, 2, '~')                # an ore bin of brine, rock lips
    L.set(23, 63, '#')
    L.set(28, 63, '#')
    L.put(25, 61, '$*')
    L.set(33, 63, 'a')
    L.set(18, 63, 'h')
    # lift E2 (x 8-12) up to G2
    L.fill(8, 44, 5, 14, '.')
    L.put(9, 63, 'qqq')
    # secret 2: breakable blocks west of the lift
    L.col(5, 62, 'BB')
    L.fill(1, 61, 4, 3, '?')
    L.put(1, 63, '$$&$')
    L.set(2, 62, 'p')

    # ==== G2: the turret hall, going east (floor 44) ============================================================
    gallery(L, 44, X0, 144)
    L.set(15, 43, 'C')
    L.fill(18, 33, 24, 5, '.')               # the turret hall: high ceiling
    L.set(24, 33, 'u')
    L.set(36, 33, 'u')
    L.put(22, 41, '----')
    L.put(28, 38, '----')
    L.put(34, 41, '----')
    L.put(29, 37, '$*$')
    L.put(23, 40, '$')
    L.put(35, 40, '$')
    L.set(40, 43, 'a')
    L.fill(46, 44, 10, 3, '~')               # brine: ride the rail platform across
    L.put(46, 43, 'xxx')
    L.put(48, 40, '$')
    L.put(52, 40, '*')
    L.set(45, 43, '#')
    L.set(56, 43, '#')
    L.set(63, 43, 'n')
    L.set(60, 43, '+')
    # the hole down to the key chamber, and catwalks back up
    L.fill(70, 44, 4, 5, '.')
    L.fill(58, 49, 30, 6, '.')               # key chamber, rows 49-54, floor 55
    L.put(70, 52, '--')                      # staggered: fall past them, climb back on them
    L.put(72, 49, '--')
    L.put(70, 46, '--')
    L.set(84, 54, 'k')
    L.put(80, 54, '$$')
    L.set(61, 54, '*')
    L.put(62, 54, '$$')
    L.set(66, 50, 'u')
    L.set(77, 54, 'a')
    L.set(64, 54, 'a')
    L.set(86, 54, '+')
    L.fill(90, 44, 14, 1, '%')               # ice floor
    L.set(98, 43, '*')
    L.set(96, 43, 'h')
    L.fill(110, 41, 3, 3, '#')               # ore heaps
    L.put(110, 40, '$$')
    L.fill(120, 42, 2, 2, '#')
    L.set(121, 41, '*')
    L.set(115, 43, 'n')
    L.set(127, 43, 'N')
    L.set(118, 39, 'u')
    L.set(125, 43, '&')
    L.col(133, 41, 'ddd')                    # the blue door before lift E3
    L.set(131, 43, 'H')
    # lift E3 (x 140-144) up to G3
    L.fill(140, 24, 5, 14, '.')
    L.put(141, 43, 'rrr')
    # secret 3: a fake wall east of the lift
    L.col(145, 42, 'XX')
    L.fill(146, 41, 4, 3, '?')
    L.put(146, 43, 'I$$$')

    # ==== G3: the upper works, going west (floor 24) ============================================================
    gallery(L, 24)
    L.set(137, 23, 'C')
    L.fill(110, 10, 26, 8, '.')              # a tall hall (rows 10-23)
    L.put(126, 23, 'yyy')                    # an optional lift to a high stash
    L.put(129, 14, '----')
    L.put(130, 13, '$$')
    L.set(131, 13, '*')
    L.put(112, 19, '----')
    L.put(117, 16, '----')
    L.put(113, 18, '$$')
    L.put(118, 15, '$*')
    L.set(122, 10, 'u')
    L.set(110, 15, 'u')
    L.set(121, 23, 'a')
    # secret 4: the stash's fake wall
    L.col(136, 12, 'XX')
    L.fill(137, 11, 4, 3, '?')
    L.put(137, 13, 'Q$$$')
    L.fill(82, 18, 25, 3, '#')               # crusher corridor C, rows 21-23
    for x, c in ((85, 'V'), (90, 'F'), (95, 'V'), (100, 'F'), (105, 'V')):
        L.set(x, 21, c)
    L.set(88, 23, '$')
    L.set(98, 23, '$')
    L.set(108, 23, '+')
    L.fill(50, 24, 26, 1, '%')               # ice with shardlings
    L.fill(60, 24, 4, 2, '~')                # brine in the ice (rock lips both sides)
    L.put(58, 24, '##')
    L.put(64, 24, '##')
    L.set(59, 23, '#')
    L.set(64, 23, '#')
    L.set(61, 20, '*')
    L.set(70, 23, 'h')
    L.set(54, 23, 'h')
    L.set(74, 23, '$')
    L.fill(26, 14, 22, 4, '.')               # a hall
    L.put(30, 21, '----')
    L.put(36, 18, '----')
    L.put(42, 21, '----')
    L.put(37, 17, '$*$')
    L.set(31, 20, '$')
    L.set(43, 20, '$')
    L.set(28, 14, 'u')
    L.set(46, 23, 'n')
    L.set(34, 23, 'a')
    L.set(25, 23, '*')
    L.set(23, 23, '&')
    # lift E4 (x 16-20) up to the exit room
    L.fill(16, 10, 5, 8, '.')
    L.put(17, 23, 'sss')
    L.set(10, 23, '*')
    L.set(78, 23, '+')
    L.set(12, 63, '+')

    # ==== the exit room (floor 10) ============================================================================
    L.fill(4, 4, 41, 6, '.')
    L.set(40, 9, 'E')
    L.put(26, 9, '$$$')
    L.put(8, 9, '$$')
    L.set(32, 9, 'N')
    return L


META = [
    ('name', 'Ore Elevators'),
    ('name.de', 'Erzaufzüge'),
    ('theme', 'ice'),
    ('tint', '3'),
    ('bg', 'ice_b'),
    ('music', 'e3_ice'),
    ('dark', '0.3'),
    ('par', '400'),
]

if __name__ == '__main__':
    main(build, 'e3l4', META)
