"""e1l8 Security Core -- everything mixed: both keys, teleporters, fabricators, switches, lasers, crushers,
conveyors, crumble, springs, movers. The longest level of episode 1.

Route: security hall (start, the blue door already in view) -> west corridor -> the west shaft (a ladder of one-way
rungs, lasers across it) -> down: the coolant pits (crumbling floor over plasma, the BLUE KEY behind a laser fence)
-> up: the archive (a fabricator, crumble over spikes, a fake-wall secret) -> back through the blue door -> the
teleporter hub (pads on pedestals; one arrival pad for all returns) -> vault 1 (laser gauntlet, turrets), vault 2
(press belt, switch A), vault 3 (crumble, springs, a secret) -> bulkhead A opens -> east hall (two fabricators,
conveyors, crushers) -> the east shaft (rungs, springs) -> the key vault below (GOLD KEY, rammers) -> back up the
east shaft -> the gold door -> the core with the exit.
Teleporters: every sender pad leads to an arrival pad (a pad without a target) next to a sender back.
"""
import lvl

W, H = 200, 76
m = lvl.Map(W, H)


def ledge(x0, x1, s, ch='%'):
    """A ledge to stand on at row s (solid at s + 1)."""
    m.hline(x0, s + 1, x1 - x0 + 1, ch)


def ladder(xl, xr, top, bottom, width=5):
    """Zig-zag one-way rungs every 3 rows between two columns, from bottom (a stand row) up to top."""
    i = 0
    for s in range(bottom - 3, top - 1, -3):
        ledge(xl if i % 2 == 0 else xr, (xl if i % 2 == 0 else xr) + width - 1, s, '-')
        i += 1


# ---------------------------------------------------------------- R1 security hall (start), x 40..62, rows 36..47
m.rect(40, 36, 23, 12, '.')
m.put(43, 47, 'P')
m.put(46, 47, '7')                  # sign: keys
m.vline(63, 45, 3, 'd')             # the blue door, already in view
m.rect(39, 42, 1, 6, '.')           # west door
m.rect(50, 45, 4, 3, '%')           # security booth, stand 44
m.hline(55, 42, 5, '-')             # stand 41
m.put(57, 41, '*')
m.put(51, 44, '$$')
m.put(60, 47, '$')
m.put(48, 38, 'L')
m.put(58, 38, 'L')

# ---------------------------------------------------------------- R2 west corridor, x 20..38, rows 41..47
m.rect(20, 41, 19, 7, '.')
m.rect(26, 46, 2, 2, '%')
m.rect(32, 45, 3, 3, '%')           # stand 44
m.put(33, 44, '*')
m.put(23, 47, 'e')
m.put(30, 47, 'n')
m.put(29, 43, 'L')
m.put(36, 47, '+')

# ---------------------------------------------------------------- R3 west shaft, x 8..19, rows 8..71
m.rect(8, 8, 12, 64, '.')
ladder(15, 8, 20, 47)               # up to the archive
ladder(15, 8, 47, 71)               # down to the coolant pits
m.hline(15, 48, 5, '#')             # the landing at the corridor, stand 47
m.put(8, 30, 'h')                   # lasers across the shaft
m.put(8, 52, 'h')
m.put(10, 47, '*')
m.put(17, 26, '*')
m.put(13, 36, 'g')
m.put(12, 58, 'm')
m.put(11, 15, 'L')
m.put(11, 40, 'L')
m.put(11, 66, 'L')
m.put(18, 71, 'C')

# ---------------------------------------------------------------- R5 coolant pits, x 20..60, rows 58..71
m.rect(20, 58, 41, 14, '.')
for x0, x1 in ((25, 31), (38, 45)):
    m.hline(x0, 72, x1 - x0 + 1, '_')   # crumbling floor
    m.hline(x0, 73, x1 - x0 + 1, '~')   # plasma under it
m.rect(33, 69, 2, 3, '%')
m.put(33, 68, '*')
m.hline(46, 69, 5, '-')
m.put(48, 68, '*')
m.put(28, 68, '$`$`$')
m.put(41, 68, '$`$')
m.put(52, 58, 'V')                  # laser fence (from the ceiling) before the key
m.put(57, 71, 'k')
m.put(59, 71, '*')
m.put(36, 71, 'n')
m.put(50, 71, 'c')
m.put(30, 62, 'm')
m.put(43, 61, 'm')
m.put(24, 60, 'L')
m.put(40, 60, 'L')
m.put(55, 60, 'R')
# Secret 3: a breakable panel in the pits' east wall.
m.vline(61, 70, 2, 'B')
m.rect(62, 68, 3, 4, '?')
m.put(62, 71, '$H$')

# ---------------------------------------------------------------- R4 archive, x 20..44, rows 8..20
m.rect(20, 8, 25, 13, '.')
m.rect(25, 18, 3, 3, '%')           # shelves, stand 17
m.rect(31, 15, 3, 1, '%')           # stand 14
m.put(32, 14, '*')
m.hline(35, 21, 5, '_')             # crumble over a spike pit
m.rect(35, 22, 5, 2, '.')
m.hline(35, 23, 5, '^')
m.put(40, 20, 'F')                  # a fabricator guards the archive's end
m.put(43, 20, '*')
m.hline(37, 13, 6, '-')
m.put(39, 12, '*')
m.put(26, 17, '$$')
m.put(22, 20, '$')
m.put(29, 9, 't')
m.put(27, 10, 'L')
m.put(38, 10, 'L')
m.put(23, 20, '9')                  # sign: fabricators
# Secret 1: an archive stack behind the shaft's west wall, off a rung chain above the ladder.
ledge(8, 12, 17, '-')
ledge(14, 18, 14, '-')
ledge(8, 12, 11, '-')
m.rect(2, 10, 5, 2, '?')
m.rect(7, 10, 1, 2, 'X')
m.put(2, 11, '$io$')

# ---------------------------------------------------------------- R6 teleporter hub, x 64..90, rows 30..47
m.rect(64, 30, 27, 18, '.')
m.put(66, 47, '8')                  # sign: teleporters
for x, ch in ((70, '1'), (78, '2'), (86, '3')):
    m.rect(x - 1, 46, 3, 2, '%')    # pedestals, stand 45
    m.put(x, 45, ch)
m.rect(65, 41, 3, 1, '%')           # the arrival pad on a shelf, stand 40
m.put(66, 40, 'y')
m.put(74, 47, 'C')
m.put(82, 47, '$$')
m.hline(74, 43, 3, '%')             # stand 42, from a pedestal
m.hline(77, 40, 5, '%')             # stand 39
m.put(80, 39, 'f')
m.hline(72, 37, 5, '-')             # stand 36
m.put(74, 36, '*')
m.put(68, 32, 'L')
m.put(84, 32, 'L')
m.rect(91, 42, 1, 6, 'A')           # bulkhead A to the east hall

# ---------------------------------------------------------------- V1 laser vault (top), x 60..96, rows 8..20
m.rect(60, 8, 37, 13, '.')
m.put(62, 20, 'u')                  # arrival
m.put(94, 20, '4')                  # back to the hub
for x, ch in ((68, 'V'), (74, 'W'), (80, 'V'), (86, 'W')):
    m.put(x, 8, ch)
m.put(77, 20, '*')
m.rect(82, 18, 2, 3, '%')
m.hline(84, 16, 5, '-')
m.put(86, 15, '*')
m.put(71, 20, '$$')
m.put(89, 20, '$$')
m.put(65, 8, 't')
m.put(90, 8, 't')
m.put(63, 10, 'L')
m.put(77, 10, 'L')
m.put(92, 10, 'L')

# ---------------------------------------------------------------- V2 press vault (bottom), x 66..100, rows 58..71
m.rect(66, 58, 35, 14, '.')
m.put(68, 71, 'w')                  # arrival
m.put(98, 71, '5')                  # back to the hub
m.rect(72, 58, 22, 4, '#')          # press housing
m.hline(71, 72, 24, 'z')            # belt to the east
for x, ch in ((75, 'Y'), (81, 'U'), (87, 'Y')):
    m.put(x, 62, ch)
m.put(78, 71, '*')
m.put(84, 71, '*')
m.put(93, 66, 'a')                  # switch A, shoot it from below
m.put(91, 71, 'r')
m.put(96, 64, 'L')
m.put(70, 62, 'L')

# ---------------------------------------------------------------- V3 spring vault (top), x 100..138, rows 8..20
m.rect(100, 8, 39, 13, '.')
m.put(102, 20, 'x')                 # arrival
m.put(136, 20, '6')                 # back to the hub
m.rect(108, 21, 6, 2, '.')
m.hline(108, 22, 6, '^')
m.put(107, 20, 'S')                 # spring over the spikes
m.hline(110, 12, 6, '-')
m.put(112, 11, '*')
m.hline(117, 21, 8, '_')            # crumble over a spike pit
m.rect(117, 22, 8, 2, '.')
m.hline(117, 23, 8, '^')
m.put(128, 20, 'S')
m.hline(126, 10, 6, '-')
m.put(129, 9, '*')
m.put(120, 16, '$`$`$')
m.put(115, 20, 'j')
m.put(132, 20, 'j')
m.put(104, 10, 'L')
m.put(120, 10, 'L')
m.put(134, 10, 'L')
# Secret 2: a cache in V3's ceiling, off the high catwalk.
m.rect(132, 8, 7, 3, '#')
m.rect(133, 8, 5, 2, '?')
m.rect(132, 8, 1, 2, 'X')
m.put(133, 9, '$H$&')

# ---------------------------------------------------------------- R7 east hall, x 92..140, rows 30..47
m.rect(92, 30, 49, 18, '.')
m.put(95, 41, 'a')                  # switch A (east side), shoot from below
m.put(110, 47, 'F')
m.put(128, 47, 'F')
m.hline(100, 48, 8, 'z')
m.hline(114, 48, 10, 'q')
m.rect(118, 30, 6, 3, '#')
m.put(120, 33, 'G')
m.rect(102, 45, 3, 3, '%')
m.hline(105, 42, 5, '-')
m.put(107, 41, '*')
m.rect(130, 45, 2, 3, '%')
m.hline(124, 42, 6, '-')
m.put(126, 41, '*')
m.put(134, 47, '*')
m.put(115, 47, '$$')
m.put(100, 47, 'e')
m.rect(135, 45, 5, 3, '%')
m.put(137, 44, 'f')
m.put(98, 33, 'L')
m.put(112, 33, 'L')
m.put(130, 33, 'L')

# ---------------------------------------------------------------- R8 east shaft, x 141..152, rows 6..71
m.rect(141, 6, 12, 66, '.')
ladder(148, 141, 20, 47)
ladder(148, 141, 47, 71)
m.put(146, 47, 'C')
m.hline(141, 48, 4, '#')
m.put(141, 24, 'h')
m.put(141, 52, 'h')
m.put(150, 63, '*')
m.put(146, 28, 'g')
m.put(145, 60, 'm')
m.put(146, 12, 'L')
m.put(146, 38, 'L')
m.put(146, 66, 'L')

# ---------------------------------------------------------------- R11 server farm, x 155..196, rows 28..44
# Off the east shaft's rung at stand 44; racks, catwalks, a laser, a teleporter shortcut back to the hub.
m.rect(153, 43, 2, 2, '.')
m.rect(155, 28, 42, 17, '.')
for x in (160, 168, 176, 184):
    m.rect(x, 42, 2, 3, '%')        # server racks, stand 41
for x0 in (162, 170, 178):
    m.hline(x0, 39, 6, '-')         # catwalks beside the racks, stand 38
m.hline(186, 36, 6, '-')
m.put(188, 35, '*')
m.put(173, 38, '*')
m.put(164, 38, '$$')
m.put(180, 38, '$$')
m.put(172, 28, 'V')
m.put(192, 44, 'F')
m.put(165, 44, 'n')
m.put(181, 44, 'c')
m.put(158, 30, 'L')
m.put(174, 30, 'L')
m.put(190, 30, 'L')
m.rect(194, 43, 3, 2, '%')
m.put(195, 42, '0')                 # teleporter back to the hub
m.put(157, 44, '+')

# ---------------------------------------------------------------- R9 key vault (bottom east), x 153..197, rows 56..71
m.rect(153, 56, 45, 16, '.')
m.put(160, 71, 'r')
m.put(178, 71, 'r')
m.put(186, 71, 'F')
m.rect(165, 69, 3, 3, '%')          # stand 68
m.hline(168, 66, 5, '-')
m.put(170, 65, '*')
m.rect(172, 56, 8, 3, '#')
m.put(175, 59, 'Q')
m.rect(180, 69, 2, 3, '%')
m.hline(182, 66, 5, '-')
m.put(184, 65, '*')
m.rect(193, 69, 3, 3, '%')
m.put(194, 68, 'K')
m.put(196, 71, '$$')
m.put(158, 60, 'L')
m.put(170, 60, 'L')
m.put(188, 60, 'L')
m.put(190, 71, '+')

# ---------------------------------------------------------------- R10 the core (top east), x 153..197, rows 6..20
m.vline(153, 18, 3, 'D')
m.rect(153, 6, 1, 12, '#')
m.rect(154, 6, 44, 15, '.')
m.put(186, 20, 'E')
m.put(166, 20, '*')
m.rect(168, 18, 2, 3, '%')
m.hline(170, 16, 6, '-')
m.put(172, 15, '$$$')
m.put(160, 6, 't')
m.put(180, 6, 't')
m.put(158, 9, 'L')
m.put(174, 9, 'L')
m.put(188, 9, 'L')
m.put(190, 20, '$$')
# Secret 4: a closet behind the core's east wall.
m.rect(194, 6, 1, 13, '#')
m.rect(194, 19, 1, 2, 'X')
m.rect(195, 6, 3, 15, '#')
m.rect(195, 18, 3, 3, '?')
m.put(195, 20, '$H$')

m.border()

header = [
    ('name', 'Security Core'),
    ('name.de', 'Sicherheitskern'),
    ('theme', 'station'),
    ('tint', '2'),
    ('bg', 'station_a'),
    ('music', 'e1_station'),
    ('dark', '0.35'),
    ('par', '600'),
]
legend = {
    'e': 'enemy sentry',
    'f': 'enemy sentry left',
    'n': 'enemy sweeper',
    'c': 'enemy sweeper left',
    'g': 'enemy hoverdrone ambush',
    'm': 'enemy sparkmine',
    't': 'enemy turret',
    'r': 'enemy rammer',
    'j': 'enemy springbot',
    'F': 'enemy fabricator',
    'S': 'spring',
    'h': 'laser h 1.4 1.6',
    'V': 'laser v 1.5 1.5',
    'W': 'laser v 1.0 2.0',
    'Y': 'crusher 9 3.0',
    'U': 'crusher 9 2.4',
    'G': 'crusher 14 3.0',
    'Q': 'crusher 12 2.8',
    'z': 'conveyor 1',
    'q': 'conveyor -1',
    'a': 'switch A',
    'A': 'toggle A solid',
    '1': 'teleport u',
    '2': 'teleport w',
    '3': 'teleport x',
    '4': 'teleport y',
    '5': 'teleport y',
    '6': 'teleport y',
    '0': 'teleport y',
    'u': 'teleport -',
    'w': 'teleport -',
    'x': 'teleport -',
    'y': 'teleport -',
    'i': 'treasure idol',
    'o': 'power overdrive',
    'L': 'light cyan 6',
    'R': 'light red 4',
    '7': 'sign sign.e1l8.keys',
    '8': 'sign sign.e1l8.teleport',
    '9': 'sign sign.e1l8.fabricator',
}

if __name__ == '__main__':
    lvl.write('e1l8', header, legend, m)
    lvl.check('e1l8')
