"""e1l9 The Warden -- the boss of episode 1.

A short approach (lift lobby, a guarded corridor, a climbing hall; crystals, a secret, health and ammo, a
checkpoint at the arena's lip) and the arena: a flat floor 38 tiles wide and 14 high, three one-way platforms 3 rows
above the floor to dodge on, the WARDEN on the far side, health and ammo in both floor corners, the exit in the
middle of the floor. The arena is entered by dropping from the lip: once inside, the hero stays (the boss exception).
"""
import lvl

W, H = 110, 22
m = lvl.Map(W, H)

# ---------------------------------------------------------------- approach
m.rect(2, 9, 11, 8, '.')            # lift lobby
m.put(4, 16, 'P')
m.put(9, 16, '1')                   # sign: warning
m.put(7, 11, 'L')
m.rect(13, 10, 32, 7, '.')          # guarded corridor
m.rect(18, 15, 2, 2, '%')
m.rect(25, 14, 3, 3, '%')           # stand 13
m.hline(29, 12, 4, '-')             # stand 11
m.put(31, 11, '*')
m.put(26, 13, '$$')
m.rect(36, 15, 2, 2, '%')
m.put(28, 10, 't')                  # ceiling turret
m.put(34, 16, 'f')
m.put(42, 16, 'f')
m.put(22, 16, '$')
m.put(40, 16, '$')
m.put(20, 11, 'L')
m.put(35, 11, 'L')
m.rect(45, 3, 24, 14, '.')          # climbing hall
m.rect(50, 14, 3, 3, '%')           # stand 13
m.hline(54, 11, 4, '-')             # stand 10
m.rect(59, 8, 11, 1, '#')           # the arena's lip, stand 7
m.rect(69, 3, 1, 5, '.')            # open above the lip into the arena
m.put(47, 16, '*')
m.put(55, 10, '$')
m.hline(46, 6, 4, '-')              # a high perch, stand 5
m.put(47, 5, '*')
m.hline(51, 8, 2, '-')              # stand 7
m.put(57, 5, 'g')
m.put(48, 9, 'L')
m.put(62, 4, 'L')
m.put(61, 7, 'C')
m.put(63, 7, 'H')
m.put(64, 7, '&')
m.put(66, 7, '2')                   # sign: the arena
# Secret: a supply closet behind the hall's west wall, off the high perch.
m.rect(44, 4, 1, 2, 'X')
m.rect(38, 4, 6, 2, '?')
m.put(38, 5, '$i$H$?')

# ---------------------------------------------------------------- the arena (x 70..107, rows 3..16, floor 17)
m.rect(70, 3, 38, 14, '.')
for x0 in (75, 86, 97):
    m.hline(x0, 13, 6, '-')         # dodge platforms, stand 12
m.put(102, 16, '!')
m.put(88, 16, 'E')
m.put(70, 16, 'H')
m.put(71, 16, '&')
m.put(107, 16, 'H')
m.put(106, 16, '&')
for x in (74, 84, 94, 104):
    m.put(x, 4, 'R')
m.put(89, 9, 'R')

m.border()

header = [
    ('name', 'The Warden'),
    ('name.de', 'Der Wächter'),
    ('theme', 'station'),
    ('tint', '3'),
    ('bg', 'station_b'),
    ('music', 'e1_station'),
    ('bossmusic', 'boss'),
    ('dark', '0.3'),
    ('par', '180'),
]
legend = {
    'f': 'enemy sentry left',
    'g': 'enemy hoverdrone ambush',
    't': 'enemy turret',
    '!': 'boss warden',
    'i': 'treasure idol',
    'L': 'light cyan 6',
    'R': 'light red 7',
    '1': 'sign sign.e1l9.warning',
    '2': 'sign sign.e1l9.arena',
}

if __name__ == '__main__':
    lvl.write('e1l9', header, legend, m)
    lvl.check('e1l9')
