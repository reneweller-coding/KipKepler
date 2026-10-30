"""e3l7 Avalanche Run / Lawinenlauf -- a long run east over the comet's surface; burrowers and frostgolems.

The start ridge (sign: burrowers, golems) -> a long ice stair down into the valley (checkpoint; burrowers under the
snow, a frostgolem on the long flat, catwalks to dodge it) -> the cliff ledges up to the plateau (a tunnel from a
ledge into the ice cave: the blue key) -> the plateau (an ice field, a hut, a crevasse with a lip) -> the avalanche
chute (a steep ice stair with a rock landing) -> the basin (a frozen lake, burrowers, a golem) -> the hills ->
the exit outcrop behind the blue door.
"""
from lvl import Lv, main

W, H = 260, 50


def build():
    L = Lv(W, H)
    L.legend.update({
        'i': 'sign sign.e3l7.burrowers',
        'L': 'light warm 5',
    })

    # ---- the surface profile -------------------------------------------------------------------------------------
    L.ground(0, [(3, 6), (20, 24)])
    for k in range(11):                       # the first descent: an ice stair, 2 wide steps
        x = 23 + 2 * k
        L.sky(x, 25 + k, 2)
        L.fill(x, 25 + k, 2, 1, '%')
    L.ground(45, [(56, 36)])                  # the valley, x 45-100
    L.ground(101, [(3, 21), (37, 21)])        # the plateau (its west face x 101-103 with ledges)
    for k in range(9):                        # the avalanche chute: 1 x 1 ice steps, a rock landing, more steps
        L.sky(141 + k, 22 + k, 1)
        L.set(141 + k, 22 + k, '%')
    L.ground(150, [(3, 30)])
    for k in range(9):
        L.sky(153 + k, 31 + k, 1)
        L.set(153 + k, 31 + k, '%')
    L.ground(162, [(40, 40), (8, 37), (8, 34), (6, 31), (4, 40), (32, 29)])
    L.fill(256, 4, 4, 25, '#')                # the right cliff

    # ---- the start ridge -----------------------------------------------------------------------------------------
    L.set(5, 23, 'P')
    L.set(10, 23, 'i')
    L.put(14, 23, '$$')
    L.put(8, 21, '%%%%')
    L.put(9, 20, '$*')
    L.set(18, 23, '&')
    L.set(30, 26, '*')                        # crystals over the stair: grab them on the slide
    L.set(38, 30, '$')
    L.set(42, 32, '*')

    # ---- the valley (floor 36) -----------------------------------------------------------------------------------
    L.set(47, 35, 'C')
    L.fill(56, 36, 10, 1, '%')
    for x in (60, 70, 82, 93):
        L.set(x, 35, 'w')                     # burrowers under the snow
    L.set(88, 35, 'g')                        # a frostgolem on the long flat
    for x, y, w in [(64, 33, 5), (75, 33, 5), (86, 33, 5)]:
        L.put(x, y, '-' * w)                  # catwalks to dodge its charge
    L.set(66, 32, '*')
    L.put(76, 32, '$*$')
    L.put(87, 32, '$$')
    L.set(53, 35, '$')
    L.set(97, 35, '+')
    L.set(72, 35, 'h')
    # secret 1: a fake wall at the foot of the cliff
    L.col(101, 34, 'XX')
    L.fill(102, 34, 2, 2, '?')
    L.put(102, 35, '$&')

    # ---- the cliff ledges and the ice cave (blue key) ------------------------------------------------------------
    for x, y in [(98, 33), (93, 30), (98, 27), (93, 24), (98, 21)]:
        L.put(x, y, '###')
    L.set(94, 29, '$')
    L.set(94, 23, '*')
    L.set(99, 20, '$')
    L.fill(101, 25, 4, 2, '.')                # the tunnel from the middle ledge into the cave
    L.fill(105, 25, 34, 10, '.')              # the ice cave, x 105-138, rows 25-34, floor 35
    L.put(105, 27, '-----')
    L.put(110, 30, '---')
    L.put(113, 32, '---')
    L.fill(118, 35, 12, 1, '%')
    L.fill(124, 25, 3, 4, '%')                # icicle columns
    L.fill(131, 25, 2, 3, '%')
    L.put(114, 31, '$$')
    L.set(130, 34, '&')
    L.set(122, 34, '*')
    L.set(137, 34, 'k')
    L.put(134, 34, '$$')
    L.set(116, 34, 'w')
    L.set(128, 34, 'w')
    L.set(132, 34, 'a')
    L.set(107, 26, 'L')
    L.set(120, 27, 'L')
    L.set(134, 27, 'L')
    L.set(111, 34, '+')
    # secret 2: a frozen store behind the cave's east wall
    L.col(139, 33, 'XX')
    L.fill(140, 32, 3, 3, '?')
    L.put(140, 34, 'R$H')

    # ---- the plateau (top 21) ------------------------------------------------------------------------------------
    L.set(106, 20, 'C')
    L.fill(110, 21, 14, 2, '%')
    L.fill(126, 21, 4, 3, '~')                # a crevasse of brine, rock lip before it
    L.fill(126, 24, 4, 1, '#')
    L.set(125, 20, '#')
    HUT = """
##########
#........#
#........#
..........
..........
"""
    L.paste(114, 16, HUT)
    L.put(116, 20, '$*$')
    L.set(121, 20, 'n')
    L.set(132, 20, 'g')
    L.set(137, 20, '*')
    L.put(108, 18, '--')
    L.put(109, 17, '$')
    # secret 3: an igloo in the sky, from the hut's roof
    L.fill(126, 10, 6, 4, '#')
    L.fill(127, 11, 4, 2, '?')
    L.col(126, 11, 'XX')
    L.put(124, 13, '--')
    L.put(127, 12, 'p$$I')

    # ---- the avalanche chute -------------------------------------------------------------------------------------
    L.set(144, 23, '$')
    L.set(147, 26, '*')
    L.set(151, 29, '+')
    L.set(155, 31, '$')
    L.set(158, 34, '*')
    L.set(146, 24, 'h')
    L.set(150, 29, 'a')

    # ---- the basin (top 40): a frozen lake --------------------------------------------------------------------------
    L.set(163, 39, 'C')
    L.fill(170, 40, 26, 2, '%')
    for x in (174, 186, 199):
        L.set(x, 39, 'w')
    L.set(192, 39, 'g')
    L.put(176, 37, '----')
    L.put(183, 34, '----')
    L.put(192, 37, '----')
    L.set(177, 36, '*')
    L.put(183, 33, '$*$')
    L.set(193, 36, '$')
    L.set(206, 36, '+')
    L.set(181, 39, 'h')
    L.set(168, 39, '&')
    L.set(197, 39, '$')

    # ---- the hills ---------------------------------------------------------------------------------------------------
    L.set(204, 36, 'n')
    L.set(207, 36, '*')
    L.set(212, 33, 'w')
    L.set(215, 33, '$')
    L.set(219, 30, 'a')
    L.set(220, 30, '*')
    L.fill(224, 37, 4, 3, '~')                # a brine crevasse (rock both sides)
    L.set(231, 28, 'g')

    # ---- the exit outcrop (top 26) -------------------------------------------------------------------------------------
    L.fill(238, 19, 7, 10, '#')
    L.fill(238, 26, 7, 3, '.')
    L.col(241, 26, 'ddd')
    L.put(232, 28, '$$')
    L.set(236, 28, '+')
    L.put(234, 25, '----')
    L.put(235, 24, '$*')
    L.set(250, 28, 'E')
    L.put(246, 28, '$$')
    # secret 4: breakable ice in the cliff behind the exit
    L.col(255, 27, 'BB')
    L.fill(256, 26, 3, 3, '?')
    L.put(256, 28, '$$H')
    # ---- sky rocks over the valley and the basin, more on the way -----------------------------------------------
    for x, y, rock, items in [(69, 30, '%%%', '$*'), (81, 30, '###', '$$'), (90, 30, '###', '.*'),
                              (178, 31, '%%%', '$$'), (188, 31, '###', '$*$'), (131, 18, '###', '.*')]:
        L.put(x, y, rock)
        L.put(x, y - 1, items, skip='.')
    L.set(107, 26, '*')
    for x, y, c in [(113, 20, 'w'), (138, 20, 'w'), (165, 39, 'a'), (196, 39, 'h'), (205, 36, 'w'), (214, 33, 'h'),
                    (234, 28, 'w'), (99, 35, 'n'), (34, 29, 'h'),
                    (58, 35, '$'), (61, 35, '$'), (209, 36, '$'), (217, 33, '$'), (243, 28, '$'), (142, 21, '$'),
                    (200, 39, '&'), (210, 33, '&')]:
        L.set(x, y, c)
    return L


META = [
    ('name', 'Avalanche Run'),
    ('name.de', 'Lawinenlauf'),
    ('theme', 'ice'),
    ('tint', '1'),
    ('bg', 'ice_a'),
    ('music', 'e3_ice'),
    ('dark', '0.15'),
    ('par', '360'),
]

if __name__ == '__main__':
    main(build, 'e3l7', META)
