"""e1s Zero-G Training Hall / Schwerelos-Trainingshalle -- the secret level of Episode 1 (station, gravity 0.55).

The Academy's old free-fall gym, forgotten behind a maintenance hatch. At 55 % gravity Kip jumps twice as high
(about 6 tiles, 8 across) and the bounce pads fling him 20 tiles up: crystals hang in the air above the pads.

  the airlock (start, sign, a pillar that only low gravity makes climbable)
  -> the training hall (80 x 37): bounce pads on the floor lift Kip through the one-way decks; floating islands
     climb to the upper left (secret 2, the cadets' hideout); a pad on the deck flings him to the top gallery;
     sweepers walk on the ceiling, drones fly.
     The left wall of the deck hides secret 1 (the instructor's locker).
  -> the gallery -> the Commandant's trophy room (the crown, an elite guard, the logbook page)
  -> the drop shaft (one-way covers, a pad halfway up: the lift back) -> the exit room, which also opens to the
     hall floor.
"""
from lvl import Lv, main

W, H = 140, 46
G = 40  # the hall floor row (the hero stands on row 39)


def build():
    L = Lv(W, H)
    L.legend.update({
        'a': 'enemy sweeper',
        'c': 'enemy sweeper ceiling',
        'b': 'enemy hoverdrone',
        'n': 'enemy hoverdrone ambush',
        'e': 'enemy sentry',
        'f': 'enemy sentry left',
        'j': 'enemy springbot',
        'J': 'enemy springbot elite',
        'g': 'enemy sentry left elite=shielded',
        't': 'enemy turret',
        'm': 'enemy sparkmine',
        's': 'spring',
        'I': 'treasure idol',
        'R': 'treasure crown',
        'o': 'power overdrive',
        'L': 'lore e1s_vault',
        '1': 'sign sign.e1s.gravity',
        '2': 'sign sign.e1s.pads',
        'l': 'light cyan 6',
        'y': 'light yellow 5',
        'w': 'light white 6',
    })

    # ==== the airlock (x 2-17, rows 28-39) ======================================================================
    L.fill(2, 28, 16, 12, '.')
    L.set(4, 39, 'P')
    L.set(7, 39, '1')
    L.fill(11, 35, 2, 5, '%')          # five tiles high: only low gravity makes it
    L.set(11, 30, '*')
    L.put(11, 34, '$$')
    L.fill(2, 33, 3, 1, '%')           # a shelf on the left wall
    L.put(2, 32, '$$')
    L.put(14, 39, '$')
    L.put(16, 39, '$')
    L.set(6, 30, 'l')

    # ==== the training hall (x 20-97, rows 3-39) ===============================================================
    L.fill(18, 34, 2, 6, '.')          # the doorway from the airlock
    L.fill(20, 3, 78, 37, '.')
    # windows to the gas giant in the back wall (top band) and two portholes low down
    for x0, x1 in ((28, 41), (50, 61)):
        L.rect(x0, 5, x1, 13, ' ')
    L.rect(74, 4, 89, 9, ' ')
    for x0, x1 in ((30, 37), (70, 77)):
        L.rect(x0, 28, x1, 32, ' ')
    # pads on the floor and a few crate stacks
    for x in (26, 46, 66, 86):
        L.set(x, G - 1, 's')
    L.set(22, G - 1, '2')
    L.fill(34, 37, 4, 3, '%')          # a crate stack (3 high)
    L.put(34, 36, '$$$$')
    L.fill(76, 37, 3, 3, '%')
    L.put(76, 36, '$$$')
    L.put(54, G - 1, '+')
    L.put(57, G - 1, 'C')
    L.put(91, G - 1, '^^^')            # a strip of training spikes before the exit room
    # the flight columns above the pads: trails of shards, a crystal at the top of each flight
    for y in (36, 33, 30, 27):
        L.set(46, y, '$')
    L.set(46, 19, '*')
    L.set(66, 36, '$')
    L.set(66, 32, '$')
    L.set(66, 28, '*')
    L.set(86, 35, '$')
    L.set(86, 30, '$')
    L.set(86, 21, '$')
    L.set(86, 18, '*')
    # training bars (one-way) for the climb without pads: 5 rows apart
    L.put(39, 34, '----')
    L.put(40, 33, '$$')
    L.put(51, 29, '----')
    L.put(52, 28, '$$')
    L.put(71, 34, '----')
    L.put(72, 33, '$$')
    L.put(80, 29, '----')
    L.put(81, 28, '$$')
    # the decks (one-way, row 24): the pads below lift Kip through them
    D = 24
    L.put(20, D, '-' * 14)            # x 20-33
    L.put(40, D, '-' * 13)            # x 40-52
    L.put(58, D, '-----%%%------')     # x 58-71, a block with the deck pad
    L.set(64, D - 1, 's')
    L.fill(63, D + 1, 3, 1, '%')
    L.put(78, D, '-' * 20)            # x 78-97
    L.put(28, D - 1, '$')
    L.put(31, D - 1, '*')
    L.put(48, D - 1, '$$$')
    L.put(81, D - 1, '$ $ $')
    L.set(94, D - 1, '*')
    # the floating islands: up the left side (5 rows apart), then the high traverse in front of the windows
    L.fill(25, 19, 4, 2, '%')          # top row 19
    L.put(25, 18, '$$')
    L.fill(33, 14, 4, 2, '%')          # top row 14
    L.set(35, 13, '*')
    L.fill(23, 9, 4, 2, '%')           # top row 9
    L.put(24, 8, '$$')
    L.fill(40, 9, 5, 2, '%')
    L.set(42, 8, '*')
    L.fill(50, 10, 4, 2, '%')
    L.put(51, 9, '$$')
    L.fill(57, 9, 4, 2, '%')
    L.set(59, 8, '*')
    L.fill(48, 16, 4, 2, '%')          # a stray island in the middle air
    L.put(49, 15, '$$')
    # the deck pad flings Kip to the gallery: a trail up its column, a shard under the ceiling
    for y in (19, 15, 11, 7):
        L.set(64, y, '$')
    L.set(64, 4, '$')
    # the top gallery (x 66-97, floor row 10)
    L.fill(66, 10, 32, 2, '#')
    L.put(70, 9, '$ $ $ $')
    L.set(90, 9, '*')
    # islands in the right half's air
    L.fill(74, 18, 4, 2, '%')
    L.put(75, 17, '$$')
    L.fill(92, 18, 4, 2, "%")
    L.put(93, 17, "$H")

    # ==== secret 1: the instructor's locker (above the airlock, entered through the deck's left wall) =========
    L.fill(6, 20, 12, 4, '?')
    L.col(18, 22, 'XX')
    L.col(19, 22, 'XX')
    L.put(8, 23, '$I$H$&')
    L.put(14, 23, '$$')

    # ==== secret 2: the cadets' hideout (upper left, from the top island) ======================================
    L.fill(10, 5, 8, 4, '?')
    L.col(18, 7, 'XX')
    L.col(19, 7, 'XX')
    L.put(11, 8, '$$I$$o')
    L.put(12, 7, ',,,,,')

    # ==== the trophy room (x 100-127, rows 3-9) and the drop shaft (x 128-135) ==================================
    L.fill(98, 5, 2, 5, '.')           # the gallery's door
    L.fill(100, 3, 36, 7, '.')
    L.fill(104, 7, 3, 3, '%')          # pedestals
    L.fill(112, 6, 4, 4, '%')
    L.fill(121, 7, 3, 3, '%')
    L.set(105, 6, 'I')
    L.set(113, 5, 'R')
    L.set(114, 5, '$')
    L.set(122, 6, 'L')                 # the logbook page on the last display case
    L.put(101, 9, '$$')
    L.put(108, 9, '$$$')
    L.put(117, 9, '$$$')
    L.set(125, 9, 'g')
    L.set(133, 4, '*')
    # the drop shaft: one-way covers, a pad halfway up on a block (the lift back up)
    L.fill(128, 10, 8, 20, '.')
    L.put(128, 10, '--------')
    L.put(128, 22, '-----%%-')
    L.set(133, 21, 's')
    L.set(129, 26, '$')
    L.set(134, 26, '$')
    L.set(130, 15, '*')

    # ==== the gyro room (x 101-126, rows 13-21), off the shaft's middle landing ===============================
    L.fill(101, 13, 26, 9, '.')
    L.fill(127, 18, 1, 4, '.')
    L.fill(103, 18, 3, 4, '%')         # a crate stack, four high
    L.set(104, 17, '*')
    L.put(108, 21, '^^^^^^')           # spikes under a floating island
    L.fill(109, 16, 4, 1, '%')
    L.put(109, 15, '$*$')
    L.fill(116, 19, 2, 3, '%')
    L.put(116, 18, '$$')
    L.put(120, 21, '$ $ $')
    L.set(102, 21, '+')

    # ==== the exit room (x 100-137, rows 30-39), open to the hall floor ======================================
    L.fill(98, 33, 2, 7, '.')
    L.fill(100, 30, 38, 10, '.')
    L.set(130, G - 1, 's')             # the pad up the shaft
    L.set(135, G - 1, 'E')
    L.put(103, G - 1, '$ $')
    L.fill(110, 36, 5, 4, '%')
    L.put(111, 35, '$*$')
    L.set(118, G - 1, '+')
    L.put(121, G - 1, '$ $')

    # ==== enemies =============================================================================================
    for x, y, c in [
        (40, 3, 'c'), (84, 3, 'c'), (114, 13, 'c'),      # sweepers on the ceiling
        (38, G - 1, 'a'), (72, G - 1, 'j'), (95, G - 1, 'a'),
        (44, 30, 'b'), (70, 16, 'b'), (30, 28, 'n'), (88, 28, 'n'),
        (50, D - 1, 'j'), (84, D - 1, 'e'),
        (94, 9, 'f'), (60, 5, 'm'),
        (106, G - 1, 'J'), (124, 34, 'b'), (121, 21, 'e'),
    ]:
        L.set(x, y, c)
    L.set(97, 14, 't')

    # ==== lights =============================================================================================
    for x, y, c in [(30, 34, 'l'), (52, 34, 'l'), (80, 34, 'l'), (92, 34, 'l'), (38, 20, 'y'), (68, 6, 'l'),
                    (110, 32, 'l'), (128, 32, 'y'), (12, 22, 'y'), (14, 6, 'y'), (108, 4, 'w'), (114, 14, 'l')]:
        L.set(x, y, c)
    return L


META = [
    ('name', 'Zero-G Training Hall'),
    ('name.de', 'Schwerelos-Trainingshalle'),
    ('theme', 'station'),
    ('tint', '1'),
    ('bg', 'station_a'),
    ('music', 'e1_station'),
    ('dark', '0.2'),
    ('par', '240'),
    ('gravity', '0.55'),
]

if __name__ == '__main__':
    main(build, 'e1s', META)
