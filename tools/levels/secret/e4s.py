"""e4s The Gloam's Treasury / Die Schatzkammer des Gloam -- the secret level of Episode 4 (citadel, a heist).

Everything the syndicate ever took from the lanes ends up here. A heist in four rooms:

  the service duct (start, sign)
  -> the laser gallery: two levels (floor and balcony) cut by five ceiling-to-floor laser fences that fire in a
     wave; the blue key waits at the balcony's far end
  -> (blue door) the crusher corridor: five crushers, a shard or a crystal under each (secret 1, the skimming
     cellar, under its floor)
  -> the sorting hall: a climb over belts that push the wrong way, jetpackers, the gold key at the top
     (secret 2, the petty cash, behind breakable blocks)
  -> the upper corridor back west: lasers and crushers again
  -> (gold door) the vault of crowns: shelves of loot under two sweeping laser beams, two crowns on the pedestal,
     an elite brute, the logbook page on the highest shelf, and the exit.
"""
from lvl import Lv, main

W, H = 150, 48


def build():
    L = Lv(W, H)
    L.legend.update({
        'a': 'enemy trooper',
        'A': 'enemy trooper left',
        'e': 'enemy trooper ambush',
        't': 'enemy shieldbot',
        'T': 'enemy shieldbot left',
        'j': 'enemy jetpacker',
        'J': 'enemy jetpacker ambush',
        'g': 'enemy gloamhound left',
        'z': 'enemy lasereye',
        'i': 'enemy blinker ambush elite=swift',
        'W': 'enemy brute elite=armoured',
        'I': 'treasure idol',
        'x': 'treasure cube',
        'h': 'enemy blinker',
        'R': 'treasure crown',
        'o': 'power overdrive',
        'p': 'power shield',
        'L': 'lore e4s_vault',
        '1': 'sign sign.e4s.treasury',
        '2': 'sign sign.e4s.vault',
        # laser fences in the gallery: a wave from west to east
        '3': 'laser v 1.4 1.6 0',
        '4': 'laser v 1.4 1.6 0.6',
        '5': 'laser v 1.4 1.6 1.2',
        '6': 'laser v 1.4 1.6 1.8',
        '7': 'laser v 1.4 1.6 2.4',
        # the upper corridor's fences
        '8': 'laser v 1.2 1.8 0',
        '9': 'laser v 1.2 1.8 1.0',
        # the vault's sweeping beams
        '(': 'laser h 1.5 2.0 0',
        ')': 'laser h 1.5 2.0 1.7',
        # crushers
        'G': 'crusher 4 2.6 0',
        'Q': 'crusher 4 2.6 0.65',
        'U': 'crusher 4 2.6 1.3',
        'V': 'crusher 4 2.6 1.95',
        'Y': 'crusher 4 3.0 0.5',
        'Z': 'crusher 4 3.0 2.0',
        # belts
        'r': 'conveyor 1',
        'l': 'conveyor -1',
        # lights
        'm': 'light magenta 6',
        'c': 'light cyan 6',
        'n': 'light violet 6',
        'y': 'light yellow 5',
    })

    # ==== the service duct (x 2-13, rows 38-41) ===============================================================
    L.fill(2, 38, 12, 4, '.')
    L.set(4, 41, 'P')
    L.set(8, 41, '1')
    L.put(10, 41, '$$')

    # ==== the laser gallery (x 14-60, rows 30-41) =============================================================
    L.fill(14, 30, 47, 12, '.')
    L.fill(15, 39, 3, 3, '%')          # crates up to the balcony
    L.put(15, 38, '$$$')
    L.put(18, 36, '-' * 41)            # the balcony (x 18-58), one-way: the beams pass through it
    for x in (33, 34, 47, 48):
        L.set(x, 36, '%')
    for x, c in ((24, '3'), (30, '4'), (38, '5'), (44, '6'), (52, '7')):
        L.set(x, 30, c)
    for x in (26, 27, 28, 34, 35, 41, 42, 48, 49, 55, 56):
        L.set(x, 41, '$')
    L.put(21, 35, '$$')
    L.put(40, 35, '$$')
    L.set(27, 35, '*')
    L.set(46, 33, '*')
    L.set(35, 41, '*')
    L.set(57, 41, '*')
    L.set(58, 35, 'k')
    L.set(54, 35, '+')
    # the blue door to the crusher corridor
    L.col(61, 39, 'ddd')

    # ==== the crusher corridor (x 62-100, rows 37-41) =========================================================
    L.fill(62, 37, 39, 5, '.')
    for x, c in ((68, 'G'), (74, 'Q'), (80, 'U'), (86, 'V'), (92, 'Q')):
        L.set(x, 37, c)
    L.set(68, 41, '$')
    L.set(74, 41, '*')
    L.set(80, 41, '$')
    L.set(86, 41, '*')
    L.set(92, 41, '$')
    L.put(70, 41, '$')
    L.put(77, 41, '$')
    L.put(89, 41, '$')
    L.set(64, 41, '&')
    L.set(97, 41, '*')
    # secret 1: the skimming cellar under the corridor floor
    L.put(83, 42, 'XX')
    L.fill(80, 43, 8, 2, '?')
    L.put(81, 44, '$I$H$&')

    # ==== the sorting hall (x 101-124, rows 9-41) =============================================================
    L.fill(101, 9, 24, 33, '.')
    L.fill(104, 39, 3, 3, '%')         # a crate stack up to the first step
    L.put(104, 38, '$$')
    L.put(109, 38, '------')           # x 109-114
    L.put(116, 35, 'rrrrrr')           # x 116-121, pushes east (into the wall)
    L.put(108, 32, '------')
    L.put(101, 29, 'llllll')           # x 101-106, pushes west (into the wall)
    L.put(108, 26, '------')
    L.put(116, 23, 'lllllllll')        # x 116-124, pushes west (off the edge)
    L.put(109, 20, '------')
    L.put(102, 17, 'rrrrrr')           # x 102-107, pushes east (off the edge)
    L.put(101, 14, '--------')         # x 101-108, one-way
    L.fill(109, 14, 16, 1, '#')        # the top floor (x 109-124)
    L.set(122, 13, 'K')
    L.put(117, 13, '$ $')
    L.put(110, 37, '$$')
    L.set(118, 34, '*')
    L.put(103, 28, '$$')
    L.set(110, 25, '*')
    L.put(111, 19, '$$')
    L.set(104, 16, '*')
    L.set(120, 22, '$')
    L.set(112, 31, '+')
    L.set(123, 41, '&')
    # secret 2: the petty cash behind breakable blocks off the west-pushing belt
    L.col(125, 21, 'BB')
    L.fill(126, 20, 5, 3, '?')
    L.put(126, 22, '$$p$$')

    # ==== the coin press (x 64-99, rows 21-29): the west-pushing belt of the sorting hall carries Kip in =======
    L.fill(64, 21, 37, 9, '.')
    L.put(66, 30, 'l' * 34)            # the press belt (x 66-99), pushing west
    for x, c in ((72, 'G'), (80, 'U'), (88, 'Q')):
        L.fill(x, 21, 1, 4, '#')       # the press heads' rams
        L.set(x, 25, c)
    for x in (68, 70, 74, 76, 78, 82, 84, 86, 90, 92, 94):
        L.set(x, 29, '$')
    L.set(80, 29, '*')
    L.set(88, 29, '*')
    L.fill(100, 21, 1, 4, '#')         # the doorway from the sorting hall (rows 25-29)
    L.set(64, 29, '*')
    L.set(65, 29, 'x')
    L.set(96, 29, 'h')

    # ==== the upper corridor (x 40-100, rows 9-13) ============================================================
    L.fill(39, 9, 62, 5, '.')
    for x, c in ((92, '8'), (84, '9'), (76, '8')):
        L.set(x, 9, c)
    for x, c in ((68, 'Y'), (60, 'Z'), (52, 'Y')):
        L.set(x, 9, c)
    for x in (95, 88, 80, 72, 64, 56):
        L.set(x, 13, '$')
    L.put(68, 13, '$')
    L.put(60, 13, '$')
    L.set(84, 13, '*')
    L.set(60, 12, '*')
    L.set(46, 13, '*')
    L.set(44, 13, '+')
    L.set(42, 13, '2')
    # the gold door to the vault
    L.col(38, 11, 'DDD')

    # ==== the vault of crowns (x 14-37, rows 5-25, floor 26) ==================================================
    L.fill(14, 5, 24, 21, '.')
    L.fill(30, 14, 8, 1, '%')          # the entry ledge (x 30-37)
    L.put(22, 17, '------')            # shelves, three rows apart
    L.put(30, 20, '------')
    L.put(22, 23, '------')
    L.put(14, 20, '-----')
    L.put(14, 14, '------')
    L.put(22, 11, '------')            # the top shelf
    L.put(22, 10, '$$$$$$')
    L.fill(30, 23, 4, 3, '%')          # the pedestal (x 30-33, top 23)
    L.set(31, 22, 'R')
    L.set(32, 22, 'R')
    L.set(30, 22, '$')
    L.set(33, 22, '$')
    L.set(15, 13, 'L')                 # the logbook page on the highest shelf
    L.put(17, 13, '$I$')
    L.put(15, 19, '$I$')
    L.put(23, 16, '$$$$')
    L.put(31, 19, '$$$$')
    L.put(23, 22, '$$$$')
    L.set(25, 16, '*')
    L.set(34, 19, '*')
    L.put(20, 25, '$ $ $ $ $')
    L.put(34, 25, '$$$')
    L.set(16, 25, 'E')
    L.set(14, 21, '(')                 # sweeping beams: from the west wall at row 21, from the east wall at 18
    L.set(37, 18, ')')

    # ==== enemies =============================================================================================
    for x, y, c in [
        (40, 41, 't'), (50, 35, 'A'), (29, 35, 'a'), (59, 31, 'z'),
        (96, 41, 'g'), (77, 40, ','),
        (113, 37, 'a'), (106, 28, 'T'), (118, 22, 'A'), (112, 30, 'j'), (106, 20, 'J'), (120, 12, 'i'),
        (88, 13, 'A'), (72, 13, 'e'), (56, 13, 'T'), (40, 9, 'z'),
        (24, 25, 'W'), (30, 8, 'j'),
    ]:
        if c != ',':
            L.set(x, y, c)

    # ==== lights =============================================================================================
    for x, y, c in [(6, 39, 'y'), (20, 31, 'm'), (34, 31, 'c'), (48, 31, 'm'), (58, 38, 'c'),
                    (65, 38, 'n'), (83, 38, 'n'), (98, 38, 'm'), (112, 40, 'c'), (104, 33, 'm'), (122, 27, 'c'),
                    (112, 18, 'm'), (118, 11, 'y'), (96, 10, 'n'), (80, 10, 'm'), (64, 10, 'n'), (48, 10, 'm'),
                    (26, 7, 'y'), (18, 12, 'm'), (35, 12, 'c'), (26, 21, 'n'), (16, 22, 'c'), (128, 21, 'y')]:
        L.set(x, y, c)
    return L


META = [
    ('name', "The Gloam's Treasury"),
    ('name.de', 'Die Schatzkammer des Gloam'),
    ('theme', 'citadel'),
    ('tint', '2'),
    ('bg', 'citadel_a'),
    ('music', 'e4_citadel'),
    ('dark', '0.4'),
    ('par', '330'),
]

if __name__ == '__main__':
    main(build, 'e4s', META)
