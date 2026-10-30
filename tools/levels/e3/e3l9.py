"""e3l9 The Colossus / Der Koloss -- the boss level.

A short approach through the crystal vault (a few crystals, enemies, a secret, checkpoint, health, ammo) ends on a
ledge over the arena; dropping in locks the hero inside (allowed for boss arenas). The arena: 38 x 14 tiles (the
colossus is tall), a flat floor, two tiers of one-way platforms to dodge the shards and to jump the ice beam,
health and ammo in the corners, the boss on the far side, the exit in the middle (opens when it falls).
"""
from lvl import Lv, main

W, H = 106, 36


def build():
    L = Lv(W, H)
    L.legend.update({
        '!': 'boss colossus',
        'L': 'light cyan 6',
        'M': 'light violet 6',
    })

    # ---- the approach (floor 18) ---------------------------------------------------------------------------------
    L.runs(3, [(10, 12, 18), (8, 11, 18), (6, 13, 18), (10, 10, 18), (8, 12, 18), (10, 11, 18), (8, 12, 18)])
    L.set(5, 17, 'P')
    L.fill(26, 18, 5, 3, '.')                 # a pit, 3 deep
    L.set(28, 20, '*')
    L.put(14, 17, '$$')
    L.put(18, 15, '---')
    L.put(19, 14, '$*')
    L.fill(38, 12, 3, 3, '%')
    L.set(44, 17, '*')
    L.put(47, 15, '---')
    L.put(48, 14, '$$')
    L.set(22, 17, 'a')
    L.set(36, 14, 'O')
    L.set(42, 17, 'h')
    L.set(33, 17, '+')
    L.set(55, 17, 'C')
    for x, y, c in [(50, 17, 'n'), (52, 13, 'O'), (9, 17, '$'), (10, 17, '$'), (36, 17, '$'), (37, 17, '$')]:
        L.set(x, y, c)
    L.set(58, 17, 'H')
    L.set(59, 17, '&')
    # secret: a crystal cellar under the pit, through its fake wall
    L.col(31, 19, 'XX')
    L.fill(32, 19, 4, 2, '?')
    L.put(32, 20, '$I$p')
    for x, y, c in [(7, 13, 'L'), (20, 12, 'M'), (32, 13, 'L'), (45, 12, 'M'), (57, 14, 'L')]:
        L.set(x, y, c)

    # ---- the arena: x 63-100, rows 14-27, floor 28 -------------------------------------------------------------------
    L.fill(63, 14, 38, 14, ' ')
    L.fill(63, 18, 1, 10, '#')                # the wall below the ledge: no way back up
    for x, y, w in [(67, 25, 5), (78, 25, 6), (89, 25, 5), (73, 22, 4), (84, 22, 4)]:
        L.put(x, y, '-' * w)
    L.set(97, 27, '!')
    L.set(75, 27, 'E')
    L.set(64, 27, 'H')
    L.set(65, 27, '&')
    L.set(99, 27, 'H')
    L.set(98, 27, '&')
    for x, y, c in [(66, 16, 'L'), (76, 15, 'M'), (88, 15, 'L'), (98, 16, 'M')]:
        L.set(x, y, c)
    return L


META = [
    ('name', 'The Colossus'),
    ('name.de', 'Der Koloss'),
    ('theme', 'crystal'),
    ('tint', '0'),
    ('bg', 'crystal_a'),
    ('music', 'e3_crystal'),
    ('bossmusic', 'boss'),
    ('dark', '0.3'),
    ('par', '150'),
]

if __name__ == '__main__':
    main(build, 'e3l9', META)
