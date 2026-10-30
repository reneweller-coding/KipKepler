"""e3l1 Drill Camp / Bohrlager -- the comet's surface (sky), low gravity, minerbots, slippery ice intro.

Route: landing pad (sign: low gravity) -> ice field (sign: slippery ice) -> the drill camp (barracks, workshop,
sky rocks, the rig) -> down the rig's shaft into the upper gallery -> west to a hole -> the ice stair -> lower
gallery east past brine pools -> blue key -> the lift shaft up -> the ice ridges -> the gatehouse (blue door) -> exit.
Secrets: barracks store room (fake wall), the rig's locker (fake wall), a vault behind breakable blocks (upper
gallery, east end), a grotto behind a fake wall beside the ice stair.
"""
from lvl import Lv, main

W, H = 200, 56
G = 28   # the surface (ground top row)


def build():
    L = Lv(W, H)
    L.legend.update({
        'i': 'sign sign.e3l1.gravity',
        'j': 'sign sign.e3l1.ice',
        'f': 'sign sign.e3l1.door',
    })

    # ---- the surface profile ------------------------------------------------------------------------------
    L.ground(0, [(3, 9), (10, 27), (3, G), (3, 25), (3, G), (5, 31), (4, G)])   # landing, pillar, crater
    L.ground(31, [(31, G), (2, 27), (64, G)])                                     # ice field, lip, the camp
    L.ground(128, [(4, 26), (2, 24), (1, 23), (4, 34), (5, 26), (7, G), (4, 25), (4, 34), (41, G)])
    L.fill(194, 8, 6, 20, '#')                                                    # the right cliff

    # ---- A: landing pad -----------------------------------------------------------------------------------
    L.put(3, 27, '##########')
    L.put(8, 22, '####')                     # a floating rock: only the low-gravity leap from the pillar gets there
    L.put(9, 21, '$*$')
    L.set(17, 22, '*')
    L.put(23, 30, '$$$')
    L.set(26, 30, '+')
    L.set(6, 26, 'P')
    L.set(12, 26, 'i')

    # ---- B: the ice field ---------------------------------------------------------------------------------
    L.fill(33, G, 26, 2, '%')
    L.set(31, 27, 'j')
    L.put(38, 25, '#####')
    L.put(46, 22, '#####')
    L.set(40, 24, '*')
    L.put(47, 21, '$*$')
    L.set(36, 27, '*')
    L.put(43, 27, '$$')
    L.set(56, 27, '*')
    L.set(53, 27, 'a')                      # the first enemy, on the ice

    # ---- C: the drill camp --------------------------------------------------------------------------------
    BARRACKS = """
##################
#............#####
#............X???#
#............X???#
####---###########
#................#
#................#
.....---..........
..................
..................
"""
    L.paste(64, 18, BARRACKS)
    L.col(64, 20, '..')                      # a window: the way out of the upper room
    L.put(66, 21, '$.*..')
    L.set(75, 21, 'n')
    L.put(78, 21, 'R$&')                     # secret 1: the barracks' store room (fake wall)
    L.set(65, 27, '&')
    L.set(79, 27, '+')
    L.set(72, 27, 'a')

    L.fill(84, 26, 2, 2, '#')                # crates
    L.set(86, 27, '#')
    L.set(85, 25, '$')

    WORKSHOP = """
####---#######
#............#
#..-----.....#
#............#
#............#
#######---####
#............#
#............#
......-----...
..............
..............
"""
    L.paste(89, 17, WORKSHOP)
    L.set(94, 18, '*')
    L.put(97, 18, '$')
    L.set(100, 21, '*')
    L.put(92, 21, '$$')
    L.set(90, 21, 'n')
    L.set(91, 27, '&')
    L.set(100, 24, '$')

    # sky rocks above the camp (from the workshop roof)
    L.put(96, 14, '%%%%%')
    L.set(98, 13, '*')
    L.put(89, 11, '####')
    L.put(90, 10, '$$')
    L.put(82, 9, '###')
    L.set(83, 8, 'I')

    # the rig: cabin with a hidden locker, two legs, a zigzag of catwalks, the shaft into the mine
    L.fill(104, 3, 19, 5, '#')
    L.fill(109, 4, 13, 3, '.')
    L.fill(105, 4, 3, 3, '?')
    L.col(108, 5, 'XX')
    L.col(122, 5, '..')                      # the cabin's door out onto the leg
    L.put(112, 7, '---')
    L.put(110, 6, '$*')
    L.put(116, 6, '$.$')
    L.put(105, 6, 'p$$')                     # secret 2: the drill master's locker
    L.fill(106, 8, 1, 17, '#')
    L.fill(122, 8, 1, 17, '#')
    for x, y, w in [(107, 25, 5), (115, 22, 7), (109, 19, 6), (116, 16, 6), (107, 13, 6), (111, 10, 7)]:
        L.put(x, y, '-' * w)
    L.set(119, 21, '*')
    L.put(111, 18, '$$')
    L.set(109, 12, '*')
    L.put(118, 15, '$$')
    L.fill(112, G, 4, 5, '.')                # the drill shaft
    L.set(103, 27, 'a')

    # ---- D: the mine ----------------------------------------------------------------------------------------
    # upper gallery
    L.fill(62, 33, 72, 4, '.')
    L.fill(84, 31, 17, 2, '.')              # a higher chamber
    L.fill(76, 37, 8, 1, '%')
    L.fill(116, 37, 9, 1, '%')
    L.put(92, 36, '##')
    L.set(93, 35, '#')
    L.put(92, 32, '$*$')
    L.set(99, 34, '&')
    L.set(74, 36, 'n')
    L.set(97, 36, 'a')
    L.set(122, 36, 'n')
    L.set(126, 36, '*')
    L.set(119, 36, '$')
    L.set(104, 36, '+')
    L.set(66, 36, '$')
    # secret 3: behind breakable blocks at the east end
    L.fill(128, 33, 6, 4, '#')
    L.fill(129, 34, 4, 3, '?')
    L.col(128, 35, 'BB')
    L.put(130, 36, 'H$$')
    L.set(130, 35, '$')

    # the hole at the west end and the ice stair below it, down to the lower gallery
    L.fill(62, 37, 3, 1, '.')
    for k in range(7):
        x = 62 + k
        L.fill(x, 38, 1, 4 + k, '.')
        L.set(x, 42 + k, '%')
    # secret 4: a grotto behind a fake wall beside the stair
    L.col(61, 40, 'XX')
    L.fill(57, 39, 4, 3, '?')
    L.put(57, 41, '$$&$')
    L.set(58, 40, '$')

    # lower gallery
    L.fill(69, 43, 99, 6, '.')
    for x0, w in [(78, 4), (98, 4), (121, 3), (140, 4)]:
        L.fill(x0, 49, w, 2, '~')
    L.fill(84, 49, 9, 1, '%')                # ice run-up, rock before the next pool
    L.fill(128, 49, 7, 1, '%')
    for x0 in (79, 99, 141):
        L.put(x0, 46, '--')
        L.put(x0, 45, '$$')
    L.set(100, 45, '*')
    L.set(142, 45, '*')
    L.set(72, 48, 'C')
    L.set(75, 48, '+')
    L.set(76, 48, '*')
    L.set(110, 48, '*')
    L.set(89, 48, 'n')
    L.set(94, 48, 'a')
    L.set(108, 48, 'h')
    L.set(116, 48, 'n')
    L.set(132, 48, 'a')
    L.set(150, 48, 'N')
    L.set(156, 48, 'k')
    L.put(153, 48, '$&')
    L.set(126, 48, 'Q')
    L.set(137, 48, '$')
    L.set(160, 48, 'H')

    # the lift shaft up to the ridges
    L.fill(162, G + 1, 6, 20, '.')
    for y, x in [(46, 162), (43, 165), (40, 162), (37, 165), (34, 162), (31, 165)]:
        L.put(x, y, '---')
    L.put(162, G, '------')
    L.set(163, 45, '$')
    L.set(166, 36, '$')
    L.set(163, 33, '+')

    # ---- E: the ice ridges ----------------------------------------------------------------------------------
    L.fill(132, 24, 2, 2, '%')
    L.fill(132, 26, 2, 1, '#')
    for x0 in (135, 155):
        L.fill(x0, 34, 4, 3, '~')
    L.fill(144, G, 7, 2, '%')               # an ice pond
    L.put(140, 23, '%%%%%')                  # a floating ice slab
    L.set(142, 22, '*')
    L.put(143, 22, '$')
    L.set(147, 27, '*')
    L.set(153, 24, '*')
    L.put(129, 25, '$$')
    L.set(130, 25, 'h')
    L.set(141, 25, 'a')
    L.set(159, 27, 'C')

    # ---- F: the gatehouse and the exit ----------------------------------------------------------------------
    L.fill(173, 14, 7, 14, '#')
    L.fill(173, 25, 7, 3, '.')
    L.col(176, 25, 'ddd')
    L.set(171, 27, 'f')
    L.put(182, 27, '$.$')
    L.set(190, 27, 'E')
    L.put(186, 24, '---')
    L.put(186, 23, 'H$$')

    # more enemies on the surface (none at the start or after a checkpoint)
    L.set(60, 27, 'n')
    L.set(126, 27, 'n')
    L.set(167, 27, 'N')
    L.set(170, 27, 'h')
    L.set(50, 21, 'h')
    L.set(84, 36, 'N')
    L.set(110, 36, 'h')
    L.set(104, 48, 'a')
    L.set(146, 48, 'h')
    L.set(149, 27, 'a')
    L.set(185, 27, 'N')
    L.set(68, 27, 'h')
    return L


META = [
    ('name', 'Drill Camp'),
    ('name.de', 'Bohrlager'),
    ('theme', 'ice'),
    ('tint', '0'),
    ('bg', 'ice_a'),
    ('music', 'e3_ice'),
    ('dark', '0.15'),
    ('par', '330'),
    ('gravity', '0.85'),
]

if __name__ == '__main__':
    main(build, 'e3l1', META)
