"""e1l3 Hangar Bay 7 -- movers across the hangar, the repeater, turrets, spikes.

Route (a serpentine): crew deck (start) -> armory: the REPEATER -> launch tube full of drones (what it is for) ->
hangar deck west to east: a safe first mover over a trench, checkpoint, two movers over a spike pit, the docked
shuttle (cabin and roof) -> the paternoster lifts at the east wall -> gantries east to west in front of the open
hangar door (turrets, drones, movers between gantry sections) -> control room above the crew deck (hidden office) ->
down the crew shaft into the service tunnels (checkpoint) -> tunnels west to east (spikes, ceiling turrets, a
breakable wall, crate store, a mover over a spike trench) -> exit room past the lift base (a closet secret).
"""
import lvl

W, H = 140, 50
m = lvl.Map(W, H)

# ---------------------------------------------------------------- crew deck (rows 21..30, floor 31..34)
m.rect(2, 26, 11, 5, '.')           # start room
m.rect(2, 14, 4, 31, '.')           # crew shaft x 2..5 from the control room down to the tunnels
m.put(8, 30, 'P')
m.put(11, 30, '$')
m.rect(13, 21, 12, 10, '.')         # armory
m.rect(13, 21, 1, 5, '#')           # bulkhead, doorway rows 26..30
m.put(18, 30, '%%%')                # pedestal
m.put(19, 29, 'r')
m.put(14, 30, '1')                  # sign: new weapon / switching
m.rect(16, 28, 2, 3, '%')           # crates, stand 27
m.rect(14, 25, 2, 1, '%')           # shelf, stand 24
m.put(22, 30, '$`')
m.rect(22, 28, 2, 1, '%')
m.put(22, 27, '$$')
# Secret 1: weapons locker behind a fake wall above the shelf.
m.rect(13, 23, 1, 2, 'X')
m.rect(7, 22, 6, 3, '?')
m.put(7, 24, '?&$o$?')
m.rect(25, 21, 20, 10, '.')         # launch tube
m.rect(25, 21, 1, 4, '#')
m.rect(30, 29, 2, 2, '%')
m.rect(36, 28, 3, 3, '%')
m.put(37, 27, '*')
m.put(30, 28, '$$')
m.put(41, 30, '$`$')
m.put(29, 24, 'b')
m.put(34, 23, 'g')
m.put(40, 24, 'b')
m.put(43, 26, 'g')
m.put(33, 30, '+')

# ---------------------------------------------------------------- hangar (x 46..119, rows 2..30)
m.rect(46, 2, 74, 29, '.')
m.rect(46, 2, 74, 14, ' ')          # the open hangar door: space behind a force field (rows 2..15)
for px in (61, 84, 104):
    m.rect(px, 1, 1, 3, '#')        # door frame struts
m.rect(45, 23, 1, 8, '.')           # crew deck opening
# deck pads and gaps (deck surface row 31, stand row 30)
m.rect(56, 31, 6, 2, '.')           # gap 1: a safe trench, floor row 33
m.put(56, 31, 'mmm')
m.put(53, 30, '2')                  # sign: movers
m.put(64, 30, 'C')
m.rect(69, 28, 3, 3, '%')           # kiosk, stand 27
m.put(70, 27, '*')
m.put(66, 30, '$$')
m.rect(74, 31, 16, 2, '.')          # gap 2: spike pit
m.hline(74, 33, 16, '^')
m.put(79, 33, '%%')                 # islands
m.put(85, 33, '%')
m.put(74, 31, 'ppp')
m.put(82, 31, 'qqq')
m.put(82, 27, '*')                  # over the pit, taken from the second mover
m.put(77, 28, '$`$')
m.put(87, 28, '$`$')
m.put(80, 22, 'b')
# the shuttle on pad 3 (x 90..111)
m.stamp(91, 21, """
`````%%%%%`````````
```%%%%%%%%%%%`````
`%%%%%%%%%%%%%%%%``
%%%%%%%%%%%%%%%%%%`
%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%
%.................%
...................
...................
...................
""")
m.put(98, 20, '*')                  # on the roof
m.put(102, 21, 'f')                 # sentry on the hull
m.put(104, 30, '*')                 # in the cabin
m.put(96, 30, '$`$`$')
m.put(94, 30, 'a')
m.hline(110, 28, 2, '-')            # boarding step, stand 27 (then the hull steps up)
m.put(109, 24, '$')
m.put(107, 22, '$')

# cargo containers hanging in the hangar (reached by dropping from the gantries)
m.rect(50, 20, 5, 2, '%')
m.put(51, 19, '$$$')
m.rect(75, 21, 4, 2, '%')
m.put(76, 20, '$i')
m.put(66, 22, 'b')

# paternoster lifts at the east wall (x 112..115 up, x 116..119 down), tunnels <-> deck <-> gantries
m.rect(112, 14, 8, 32, '.')
m.rect(112, 14, 8, 2, ' ')
m.put(112, 45, 'LLLL')
m.put(116, 14, 'MMMM')

# ---------------------------------------------------------------- gantries (stand row 13, in front of space)
m.hline(100, 14, 12, '%')           # G1
m.put(105, 15, 't')                 # turret under G1 (fires at the deck)
m.put(95, 14, 'uuu')                # mover G1 -> G2
m.hline(78, 14, 11, '%')            # G2
m.put(83, 15, 't')
m.put(86, 13, 't')                  # turret on top of G2
m.put(74, 14, 'www')                # mover G2 -> G3
m.hline(54, 14, 13, '-')            # G3
m.hline(46, 14, 5, '%')             # G4 at the control room door
m.put(108, 13, '*')
m.put(80, 13, '*$$')
m.put(58, 13, '*')
m.put(60, 13, '$$$')
m.rect(69, 11, 3, 1, '%')           # a floating block in the door, stand 10
m.put(70, 10, '*')
m.rect(92, 11, 3, 1, '%')
m.put(93, 10, '$')
m.put(96, 7, 'b')
m.put(66, 6, 'b')
m.put(51, 9, 'g')

# ---------------------------------------------------------------- control room (x 6..44, rows 3..17)
m.rect(6, 3, 39, 15, '.')
m.rect(45, 11, 1, 3, '.')           # door from G4
m.rect(6, 3, 1, 11, '#')            # wall to the crew shaft, open rows 14..17
m.rect(36, 15, 4, 3, '%')           # console bank A, stand 14
m.hline(30, 12, 14, '-')            # mezzanine east, stand 11
m.rect(20, 15, 5, 3, '%')           # console bank B, stand 14
m.hline(12, 12, 10, '-')            # mezzanine west, stand 11
m.put(22, 14, '*')
m.put(14, 11, '*')
m.put(37, 14, '$$')
m.put(32, 11, '$`$`$')
m.put(10, 17, '+')
m.put(32, 17, 'a')
m.put(41, 11, 'f')
m.put(18, 3, 't')                   # ceiling turret
# Secret 2: the commander's office between the mezzanines, behind a fake wall.
m.rect(25, 3, 5, 10, '#')
m.rect(26, 8, 3, 4, '?')
m.rect(29, 10, 1, 2, 'X')
m.put(26, 11, 'iH$')

# ---------------------------------------------------------------- service tunnels (rows 35..44, floor 45)
m.rect(2, 35, 118, 10, '.')
m.put(8, 44, 'C')
m.rect(2, 45, 4, 1, '%')            # the old crew lift cabin at the bottom of the shaft
m.hline(14, 42, 8, '-')             # stand 41
m.put(17, 41, '*')
m.put(15, 41, '$$')
m.put(24, 44, 'c')
m.put(28, 44, 'a')
m.rect(30, 43, 2, 2, '%')
# spikes with stepping stones (x 33..43)
m.hline(33, 44, 11, '^')
m.hline(34, 42, 3, '-')
m.hline(40, 42, 3, '-')
m.put(35, 41, '$')
m.put(41, 41, '$')
# turret alley (x 46..60)
m.put(49, 35, 't')
m.put(58, 35, 't')
m.rect(52, 42, 4, 3, '%')           # stand 41
m.put(53, 41, '*$')
m.put(47, 44, '&')
# breakable wall across the tunnel at x 62
m.vline(62, 41, 4, 'B')
m.rect(62, 35, 1, 6, '#')
# crate store (x 63..100)
m.rect(72, 42, 3, 3, '%')           # stand 41
m.rect(76, 40, 3, 1, '%')           # stand 39
m.rect(80, 37, 4, 1, '%')           # stand 36
m.put(81, 36, '*')
m.put(77, 39, '$$')
m.put(73, 41, '$')
m.put(66, 44, '$$')
m.put(86, 44, 'c')
m.put(92, 44, 'a')
m.rect(95, 42, 3, 3, '%')           # stand 41
m.put(96, 41, '*')
m.put(89, 39, 'b')
m.put(99, 44, '+')
# a mover over a spike trench (x 101..110)
m.rect(101, 45, 10, 1, '.')
m.hline(101, 46, 10, '^')
m.put(101, 45, 'nnn')
m.put(104, 41, '$`$`$')

# exit room (x 121..133, rows 35..44) and Secret 3, a closet behind its east wall
m.rect(120, 38, 1, 7, '.')
m.rect(121, 35, 13, 10, '.')
m.put(129, 44, 'E')
m.rect(123, 42, 3, 3, '%')
m.put(124, 41, '*')
m.put(122, 44, '$')
m.put(132, 44, '$')
m.rect(134, 43, 1, 2, 'X')
m.rect(135, 41, 4, 4, '?')
m.put(135, 44, '$$H&')

m.border()

header = [
    ('name', 'Hangar Bay 7'),
    ('name.de', 'Hangar 7'),
    ('theme', 'station'),
    ('tint', '2'),
    ('bg', 'station_b'),
    ('music', 'e1_station'),
    ('dark', '0.2'),
    ('par', '330'),
]
legend = {
    'a': 'enemy sweeper',
    'c': 'enemy sweeper left',
    'b': 'enemy hoverdrone',
    'g': 'enemy hoverdrone ambush',
    'f': 'enemy sentry left',
    't': 'enemy turret',
    'r': 'weapon repeater',
    'o': 'power overdrive',
    'i': 'treasure idol',
    'm': 'mover 3 0 50',
    'n': 'mover 7 0 60',
    'p': 'mover 5 0 60',
    'q': 'mover 5 0 60',
    'u': 'mover -6 0 60',
    'w': 'mover -7 0 60',
    'L': 'mover 0 -31 110 1.2',
    'M': 'mover 0 31 110 1.2',
    '1': 'sign sign.e1l3.repeater',
    '2': 'sign sign.e1l3.mover',
}

if __name__ == '__main__':
    lvl.write('e1l3', header, legend, m)
    lvl.check('e1l3')
