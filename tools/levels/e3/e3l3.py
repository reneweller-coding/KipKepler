"""e3l3 Glittering Grotto / Glitzergrotte -- dark crystal caves lit by crystal lights, crystalcrabs, many secrets.

Areas: A the entrance gallery (sign) -> B the geode (a big open bowl with catwalks and a crystal island) -> C the
crystal halls (crabs, a fake floor) -> the crack down into F, the prism bridges over a brine chasm -> E the hub
(a pool, a hole down) -> H the two-level crystal maze (blue key) -> the blue door -> I the exit cave.
G (lower west) and the crack D tie the loop together: D climbs from G past E back up to A.
Secrets: A (fake wall west of the start), B (fake wall low in the geode's east wall), C (a fake floor that drops
into a pocket and out into the crack), G (a vault behind breakable crystal).
"""
from lvl import Lv, main

W, H = 212, 70


def build():
    L = Lv(W, H)
    L.legend.update({
        'i': 'sign sign.e3l3.secrets',
        'L': 'light cyan 7',
        'M': 'light violet 6',
        'Y': 'light magenta 6',
        'Z': 'enemy crystalcrab left',
    })

    # ---- A: the entrance gallery (floor 18-20) ----------------------------------------------------------------
    L.runs(2, [(8, 11, 19), (6, 10, 19), (5, 9, 18), (6, 10, 18), (4, 12, 18), (7, 10, 21), (6, 9, 20),
               (5, 8, 19), (6, 9, 18), (6, 10, 18)])
    L.set(4, 18, 'P')
    L.set(8, 18, 'i')
    L.put(34, 20, '%%')
    L.set(34, 19, '%')
    L.put(23, 10, '%%%')
    L.set(24, 11, '%')
    L.put(43, 9, '%%')
    L.put(38, 17, '----')
    L.put(39, 16, '$$')
    L.set(13, 18, '*')
    L.set(35, 18, '*')
    L.set(52, 17, '*')
    L.put(18, 17, '$$')
    L.put(45, 18, '$$')
    L.set(29, 17, 'a')
    L.set(47, 18, 'Z')
    for x, y, c in [(6, 12, 'L'), (21, 11, 'M'), (36, 11, 'L'), (50, 10, 'Y'), (58, 11, 'L')]:
        L.set(x, y, c)
    # secret 1: under the gallery floor, behind the dip's west wall
    L.col(30, 19, 'XX')
    L.fill(26, 19, 4, 2, '?')
    L.put(26, 20, '$&$+')

    # ---- B: the geode (open bowl, x 67-108) -----------------------------------------------------------------
    L.fill(61, 14, 6, 4, '.')                # passage from A (floor 18)
    L.runs(67, [(4, 8, 26), (5, 5, 28), (5, 4, 30), (8, 3, 31), (6, 4, 30), (5, 5, 28), (4, 7, 26),
                (4, 9, 24)], ' ')
    L.fill(108, 11, 1, 4, '.')
    L.put(67, 18, '----')
    for x, y, w in [(76, 27, 5), (83, 24, 5), (89, 21, 5), (83, 18, 5), (77, 15, 5), (101, 21, 4), (97, 18, 4),
                    (104, 15, 4)]:
        L.put(x, y, '-' * w)
    L.put(84, 12, '%%%%')                    # the crystal island
    L.put(85, 11, '*$')
    L.set(84, 11, '$')
    L.set(79, 14, '*')
    L.put(80, 14, '$$')
    L.set(91, 20, '*')
    L.set(86, 30, '*')
    L.put(84, 30, '$$')
    L.put(98, 17, '$$')
    L.set(85, 23, 'a')
    L.set(80, 29, 'a')
    L.set(93, 29, 'Z')
    L.set(102, 23, 'h')
    L.set(103, 25, '+')
    for x, y, c in [(70, 12, 'L'), (86, 6, 'M'), (100, 10, 'Y'), (78, 24, 'L'), (94, 26, 'M')]:
        L.set(x, y, c)
    # secret 2: a pocket behind the geode's east wall, low down
    L.col(108, 22, 'XX')
    L.fill(109, 21, 5, 3, '?')
    L.put(109, 23, '$&$H')

    # ---- C: the crystal halls (x 109-205, rows 6-24) --------------------------------------------------------
    L.fill(109, 11, 6, 4, '.')               # passage from the geode (floor 15)
    L.runs(115, [(6, 10, 15), (8, 8, 17), (6, 7, 16), (6, 9, 15)])
    L.runs(141, [(30, 6, 18)])
    L.fill(148, 6, 2, 8, '%')               # a crystal column hanging from the ceiling
    L.fill(160, 15, 2, 3, '%')              # a crystal block on the floor
    L.runs(171, [(6, 9, 17), (8, 8, 16), (6, 10, 17), (9, 9, 18), (6, 9, 40)])
    L.set(124, 16, '*')
    L.set(155, 17, '*')
    L.set(166, 17, '*')
    L.set(180, 15, '*')
    L.put(160, 14, '$$')
    L.put(130, 15, '$$')
    L.put(143, 17, '$')
    L.put(177, 15, '$$')
    L.put(142, 15, '---')
    L.put(143, 14, '$')
    L.set(185, 16, '&')
    L.set(126, 16, 'a')
    L.set(146, 17, 'a')
    L.set(157, 17, 'h')
    L.set(168, 17, 'Z')
    L.set(188, 16, 'a')
    L.set(153, 17, '+')
    for x, y, c in [(118, 11, 'L'), (131, 9, 'M'), (144, 8, 'L'), (156, 7, 'Y'), (168, 8, 'L'), (181, 10, 'M'),
                    (194, 10, 'L')]:
        L.set(x, y, c)
    # secret 3: a fake floor drops into a pocket that opens into the crack
    L.put(194, 18, 'XX')
    L.fill(192, 19, 7, 3, '?')
    L.col(199, 20, 'XX')
    L.put(192, 21, 'I$')
    L.put(196, 21, '$$')
    L.set(193, 20, 'p')

    # ---- F: the prism bridges (x 148-205, rows 28-46) -------------------------------------------------------
    L.fill(150, 28, 50, 16, ' ')            # x 150-199, rows 28-43
    L.fill(156, 44, 40, 3, '~')             # brine at the bottom (rows 44-46), floor 47
    L.fill(150, 40, 6, 4, '#')              # west shore (floor 40)
    L.fill(196, 40, 4, 4, '#')              # east shore under the crack
    L.fill(200, 40, 6, 7, '#')
    L.fill(192, 41, 1, 6, '%')
    L.fill(184, 41, 1, 6, '%')
    L.put(184, 40, '-' * 9)                 # bridge 1, x 184-192
    L.fill(177, 37, 4, 10, '%')             # a crystal pillar
    L.fill(165, 40, 1, 7, '%')
    L.fill(173, 40, 1, 7, '%')
    L.put(165, 39, '-' * 9)                 # bridge 2, x 165-173
    L.fill(158, 36, 4, 11, '%')             # another pillar
    L.fill(168, 28, 5, 4, '%')              # a stalactite with a bat under it
    L.set(170, 32, 'b')
    L.fill(186, 28, 4, 5, '%')
    L.set(187, 33, 'b')
    L.set(178, 36, '*')
    L.set(159, 35, '*')
    L.put(194, 37, '$')
    L.put(182, 36, '$')
    L.put(163, 35, '$')
    L.put(188, 39, '$*$')
    L.set(198, 39, 'H')
    L.set(186, 39, 'a')
    L.set(168, 38, 'Z')
    L.set(152, 39, 'n')
    for x, y, c in [(197, 33, 'L'), (182, 30, 'M'), (174, 34, 'Y'), (162, 30, 'L'), (152, 33, 'M')]:
        L.set(x, y, c)
    L.set(203, 39, 'C')

    # ---- E: the hub (x 70-149, rows 30-44) -------------------------------------------------------------------
    L.runs(70, [(10, 34, 44), (12, 32, 42), (10, 31, 43), (12, 30, 41), (10, 32, 42), (12, 33, 40),
                (14, 34, 40)])
    L.fill(95, 43, 4, 2, '~')               # a brine pool in the floor
    L.fill(94, 42, 1, 1, '#')
    L.fill(99, 42, 1, 1, '#')
    L.fill(72, 44, 4, 8, '.')               # the hole down into the maze
    L.fill(104, 30, 2, 5, '%')
    L.fill(116, 32, 2, 4, '%')
    L.put(126, 37, '----')
    L.put(127, 36, '$*$')
    L.put(108, 38, '----')
    L.put(109, 37, '$$')
    L.set(85, 41, '*')
    L.set(96, 40, '*')
    L.set(141, 39, '*')
    L.put(118, 41, '$&')
    L.set(88, 41, 'a')
    L.set(112, 40, 'n')
    L.set(122, 41, 'Z')
    L.set(135, 39, 'h')
    L.set(145, 39, 'a')
    L.set(80, 41, '+')
    for x, y, c in [(144, 35, 'L'), (132, 34, 'M'), (120, 33, 'L'), (108, 32, 'Y'), (96, 33, 'L'), (84, 33, 'M'),
                    (74, 36, 'L')]:
        L.set(x, y, c)

    # ---- D: the crack from G up past E to A (x 50-55) --------------------------------------------------------
    L.fill(50, 19, 6, 33, '.')              # rows 19-51
    L.put(50, 18, '------')                 # A's floor over it: walk over, drop through (down + jump)
    for y, x in [(21, 50), (24, 53), (27, 50), (30, 53), (33, 50), (36, 53), (39, 50), (42, 53), (45, 50),
                 (48, 53), (51, 50)]:
        L.put(x, y, '---')
    L.fill(56, 38, 14, 4, '.')              # passage to E (floor 42)
    L.set(54, 41, '*')
    L.put(51, 26, '$$')
    L.set(54, 35, '+')
    L.set(51, 44, '$')
    L.set(52, 22, 'M')
    L.set(53, 32, 'L')
    L.set(52, 46, 'Y')
    L.set(62, 39, 'L')

    # ---- G: the lower west cave (x 4-69, rows 50-63) ---------------------------------------------------------
    L.runs(8, [(8, 54, 62), (10, 52, 63), (12, 51, 61), (10, 50, 62), (8, 52, 60), (12, 51, 60)])
    L.fill(20, 63, 4, 2, '~')
    L.put(19, 62, '#')
    L.put(24, 62, '#')
    L.put(30, 58, '----')
    L.put(31, 57, '$*')
    L.put(14, 59, '---')
    L.put(15, 58, '$$')
    L.set(12, 61, '*')
    L.set(44, 61, '*')
    L.set(60, 59, '*')
    L.set(36, 60, 'a')
    L.set(48, 59, 'h')
    L.set(58, 59, 'Z')
    L.set(40, 61, '&')
    L.set(26, 60, '+')
    for x, y, c in [(12, 56, 'L'), (24, 54, 'M'), (36, 53, 'L'), (48, 53, 'Y'), (60, 55, 'L')]:
        L.set(x, y, c)
    # secret 4: a vault behind breakable crystal at the west end
    L.col(7, 60, 'BB')
    L.fill(2, 59, 5, 3, '?')
    L.put(2, 61, '$R$$+')
    L.set(3, 60, '$')
    L.put(53, 54, '---')                     # the crack's lowest catwalks (after G is carved)
    L.put(50, 57, '---')
    # the passage from G to the maze
    L.fill(68, 57, 2, 3, '.')

    # ---- H: the crystal maze (x 70-150, two tunnels) ---------------------------------------------------------
    L.runs(70, [(14, 52, 56), (10, 51, 56), (12, 52, 56), (10, 50, 56), (14, 52, 56), (10, 51, 56), (10, 52, 56)])
    L.runs(70, [(20, 58, 62), (14, 57, 62), (16, 58, 62), (14, 57, 62), (16, 58, 62)])
    for x0 in (90, 112, 134):                # cracks between the tunnels
        L.fill(x0, 56, 3, 2, '.')
    for x0 in (90, 112, 134):                # one-way ledges under the cracks, up from the lower tunnel
        L.put(x0, 59, '---')
    L.fill(84, 51, 1, 2, '%')
    L.fill(104, 54, 2, 2, '%')
    L.fill(128, 52, 1, 2, '%')
    L.fill(96, 60, 2, 2, '%')
    L.fill(118, 58, 1, 2, '%')
    L.set(147, 61, 'k')
    L.put(143, 61, '$$')
    L.set(86, 55, '*')
    L.set(108, 61, '*')
    L.set(125, 55, '*')
    L.set(138, 61, '*')
    L.put(95, 55, '$$')
    L.put(116, 55, '$$')
    L.put(131, 61, '$$')
    L.set(78, 55, 'C')
    L.set(92, 55, 'a')
    L.set(110, 55, 'Z')
    L.set(132, 55, 'a')
    L.set(103, 61, 'a')
    L.set(125, 61, 'h')
    L.set(140, 61, 'Z')
    L.set(118, 61, 'H')
    for x, y, c in [(80, 53, 'L'), (93, 52, 'M'), (106, 52, 'L'), (119, 53, 'Y'), (132, 53, 'L'), (145, 53, 'M'),
                    (88, 59, 'Y'), (100, 59, 'L'), (113, 58, 'M'), (128, 59, 'L'), (141, 59, 'Y')]:
        L.set(x, y, c)

    # ---- I: the blue door and the exit cave ------------------------------------------------------------------
    L.col(150, 59, 'ddd')
    L.runs(151, [(10, 57, 62), (12, 55, 63), (14, 53, 62), (12, 55, 61), (10, 56, 62)])
    L.put(166, 60, '----')
    L.put(167, 59, '$$')
    L.set(160, 61, '$')
    L.set(174, 61, '$')
    L.set(172, 61, 'A')
    L.set(183, 60, 'A')
    L.set(194, 60, 'E')
    for x, y, c in [(156, 58, 'L'), (168, 55, 'M'), (180, 55, 'L'), (192, 57, 'Y')]:
        L.set(x, y, c)
    return L


META = [
    ('name', 'Glittering Grotto'),
    ('name.de', 'Glitzergrotte'),
    ('theme', 'crystal'),
    ('tint', '0'),
    ('bg', 'crystal_a'),
    ('music', 'e3_crystal'),
    ('dark', '0.5'),
    ('par', '380'),
]

if __name__ == '__main__':
    main(build, 'e3l3', META)
