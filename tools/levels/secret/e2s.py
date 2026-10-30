"""e2s The Pod Garden / Der Schotengarten -- the secret level of Episode 2 (jungle, outdoors).

A walled garden of giant bounce pods that the colonists' botanists bred and forgot. Only leapers and mothlings
live here. Each pod flings Kip 11 tiles up and about 8 across: the garden is crossed by bouncing from pod to pod,
with crystals hanging at the tops of the arcs.

  the glade (start, sign, a practice pod with a column of shards)
  -> the acid pond: stumps three wide, five apart -- too far to jump, easy to bounce (a crystal over two hops)
  -> the terraces: pods up the cliff (secret 1, the root hollow, hides in the cliff foot)
  -> the botanists' lodge at the top (the crown, an elite leaper, the logbook page); the high garden leads
     back west over the pond to the overlook above the glade; secret 2 hides in the foot of the upper terrace
  -> the canopy run over the ravine: a vine bridge, a drifting seed basket (mover), pods on branch knots
  -> down to the exit lawn (a pod and a vine ledge lead back up).
"""
from lvl import Lv, main

W, H = 150, 50
G = 40  # the ground surface row (the hero stands on row 39)


def build():
    L = Lv(W, H, ' ')
    L.legend.update({
        'j': 'enemy leaper',
        'J': 'enemy leaper ambush',
        'q': 'enemy leaper elite',
        'm': 'enemy mothling',
        'M': 'enemy mothling ambush',
        'Q': 'enemy mothling elite=swift',
        's': 'spring',
        'I': 'treasure idol',
        'R': 'treasure crown',
        'p': 'power shield',
        'L': 'lore e2s_vault',
        '1': 'sign sign.e2s.pods',
        '2': 'sign sign.e2s.steer',
        'b': 'mover 7 0 60 1.0',
        'g': 'light green 6',
        'w': 'light warm 6',
    })
    # the garden walls (left and right) and the floor of the world
    L.fill(0, 0, 2, H, '#')
    L.fill(W - 2, 0, 2, H, '#')
    L.fill(0, G, W, H - G, '#')

    # ==== the glade (x 2-22) =================================================================================
    L.set(5, G - 1, 'P')
    L.set(9, G - 1, '1')
    L.set(16, G - 1, 's')              # the practice pod
    for y in (34, 32, 30):
        L.set(16, y, '$')
    L.set(16, 29, '*')
    L.put(12, G - 1, '$$')
    L.fill(2, 36, 3, 4, '%')           # an old garden wall
    L.put(2, 35, '$$$')

    # ==== the acid pond (x 23-64): stumps with pods, too far apart to jump =================================
    L.fill(23, G, 42, 2, ' ')
    L.fill(23, G + 2, 42, 4, '~')
    for cx in (28, 36, 44, 52, 60):
        L.fill(cx - 1, G + 1, 3, 5, '%')
        L.set(cx, G, 's')
    L.set(20, G - 1, '2')
    # the arcs: a crystal at the top of two hops, shards on the others
    L.set(32, 29, '*')
    L.set(48, 29, '*')
    L.set(40, 29, '*')
    L.put(56, 29, '$')
    for x in (30, 34, 46, 50):
        L.set(x, 32, '$')
    L.set(44, 30, '$')

    # ==== the terraces (x 65-99): pods up the cliff ===========================================================
    L.fill(74, 30, 26, 10, '#')        # T1: top row 30
    L.fill(84, 20, 16, 10, '#')        # T2: top row 20
    L.set(70, G - 1, 's')
    L.put(66, G - 1, '$$')
    L.set(78, 29, 's')
    L.put(75, 29, '$')
    L.put(81, 29, '$$')
    L.set(70, 29, '*')
    L.set(70, 33, '$')
    L.set(78, 22, '*')
    # secret 1: the root hollow in the cliff foot
    L.col(74, 37, 'XXX')
    L.col(75, 37, 'XXX')
    L.fill(76, 36, 8, 4, '?')
    L.put(77, 39, '$$I$H$')
    L.put(78, 36, ',,,')

    # ==== the high garden (rows 17-22): islands west over the pond, back to the overlook above the glade ======
    L.put(65, 20, '-' * 19)            # a vine bridge from the top terrace (x 65-83); the T1 pod lifts onto it
    L.fill(57, 20, 8, 3, '#')          # H1 (top 20)
    L.set(58, 19, 's')
    L.set(62, 19, '*')
    L.put(60, 19, '$')
    L.fill(45, 17, 7, 3, '#')          # H2 (top 17)
    L.set(46, 16, 's')
    L.put(48, 16, '*$')
    L.fill(28, 20, 9, 3, '#')          # H3 (top 20)
    L.set(29, 19, 's')
    L.put(32, 19, '$*$')
    L.fill(2, 22, 21, 2, '%')          # the overlook: the old garden wall's top
    L.put(4, 21, '*$$')
    L.put(14, 21, '$ $')
    for x, y in ((53, 13), (41, 11), (24, 14)):
        L.set(x, y, '$')

    # ==== the treehouse (x 92-105, rows 4-9, floor row 10) ===================================================
    L.set(87, 19, 's')
    L.put(85, 19, '$$')
    L.set(87, 14, '$')
    L.fill(91, 10, 16, 2, '%')         # the floor (top row 10)
    L.fill(91, 3, 16, 1, '%')          # the roof
    L.fill(105, 3, 2, 8, '%')          # the back wall
    L.fill(92, 4, 13, 6, '.')
    L.set(96, 9, '$')
    L.set(98, 9, 'R')
    L.set(99, 9, '$')
    L.fill(101, 8, 2, 2, '%')          # a shelf with the logbook page
    L.set(101, 7, 'L')
    L.set(102, 7, 'I')
    L.set(103, 9, 'q')
    L.set(94, 7, '*')
    # secret 2: the hollow in the tower (from the first terrace, through the second terrace's foot)
    L.col(84, 28, 'XX')
    L.col(85, 28, 'XX')
    L.fill(86, 26, 10, 4, '?')
    L.put(87, 29, '$$I$p$$')
    L.put(89, 26, ',,,')

    # ==== the canopy run (x 100-130) over the ravine ========================================================
    L.fill(100, G, 26, 2, ' ')
    L.fill(100, G + 2, 26, 4, '~')
    L.fill(100, G + 6, 26, 4, '#')
    for cx in (106, 114, 122):         # stumps in the ravine: a fall is not the end
        L.fill(cx - 1, G + 1, 3, 5, '%')
        L.set(cx, G, 's')
    L.set(110, 31, '$')
    L.set(118, 31, '$')
    L.put(103, 20, '----------')        # a vine bridge (x 103-112)
    L.put(105, 19, '$ $ $')
    L.set(111, 19, '*')
    L.set(114, 20, 'b')                # a drifting seed basket (x 114-116 -> 121-123)
    L.put(114, 20, 'bbb')
    L.set(118, 16, '*')
    L.fill(126, 20, 3, 2, '%')         # a branch knot with a pod
    L.set(127, 19, 's')
    L.set(127, 12, '$')
    L.set(127, 9, '*')

    # ==== the exit lawn (x 126-147) =========================================================================
    L.put(131, 30, '-------')           # a vine ledge (x 131-137) with a pod on a knot
    L.fill(134, 30, 2, 1, '%')
    L.set(134, 29, 's')
    L.set(129, G - 1, 's')
    L.put(132, 29, '$')
    L.put(137, 29, '$')
    L.set(129, 33, '$')
    L.set(140, 36, '*')
    L.fill(139, 37, 3, 3, '%')
    L.fill(133, 12, 7, 2, '#')         # a sky island off the knot pod
    L.put(134, 11, '$*$')
    L.put(136, G - 1, '$$')
    L.set(144, G - 1, 'E')

    # ==== enemies =============================================================================================
    for x, y, c in [
        (63, 19, 'j'), (36, 19, 'j'), (18, 21, 'J'), (112, 30, 'm'), (138, 7, 'M'),
        (30, 24, 'm'), (46, 22, 'm'), (58, 26, 'M'),
        (68, G - 1, 'j'), (72, 19, 'j'), (94, 19, 'J'),
        (110, 14, 'm'), (122, 24, 'Q'), (108, 19, 'j'),
        (133, G - 1, 'j'), (142, 28, 'M'),
    ]:
        L.set(x, y, c)

    # ==== health and ammo ====================================================================================
    for x, y, c in [(21, 21, '+'), (12, 21, '&'), (96, 19, '&'), (76, 29, '+'), (131, G - 1, '+'), (138, G - 1, '&')]:
        L.set(x, y, c)

    # ==== lights =============================================================================================
    for x, y, c in [(95, 5, 'w'), (90, 27, 'g'), (80, 38, 'g')]:
        L.set(x, y, c)
    return L


META = [
    ('name', 'The Pod Garden'),
    ('name.de', 'Der Schotengarten'),
    ('theme', 'jungle'),
    ('tint', '1'),
    ('bg', 'jungle_a'),
    ('music', 'e2_jungle'),
    ('dark', '0.1'),
    ('par', '260'),
]

if __name__ == '__main__':
    main(build, 'e2s', META)
