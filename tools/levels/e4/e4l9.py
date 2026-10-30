"""e4l9 -- The Gloam / Das Gloam (citadel). The final boss.

A short approach along the core's rim (windows onto the core, a checkpoint, health and ammo, no crystals),
then a shaft drops into the arena (no way back): 42 x 13 tiles, flat floor, two one-way platforms 3 tiles up,
health and ammo in the corners, the exit on the east side. THE GLOAM floats in the arena's middle, 3 tiles above
the floor, and blinks between its spawn and points 220 px left/right (and 70 px up).
"""
from kit import Map, main


def build():
    m = Map(106, 36)
    m.key('name', 'The Gloam')
    m.key('name.de', 'Das Gloam')
    m.key('theme', 'citadel')
    m.key('tint', 3)
    m.key('bg', 'citadel_b')
    m.key('music', 'e4_citadel')
    m.key('bossmusic', 'boss')
    m.key('dark', 0.35)
    m.key('par', 240)
    TL = m.legend('b', 'enemy trooper left')
    BL = m.legend('i', 'enemy blinker')
    EY = m.legend('z', 'enemy lasereye')
    J = m.legend('j', 'enemy jetpacker')
    m.legend('!', 'boss gloam')
    m.legend('n', 'sign sign.e4l9.core')
    m.legend('L', 'light magenta 7')
    m.legend('l', 'light violet 6')
    m.legend('o', 'power overdrive')

    # ================================================================ the approach (x2-66, y6-17, floor 18)
    m.room(2, 6, 65, 12)
    m.sky(8, 7, 22, 5)                     # windows onto the core
    m.sky(36, 7, 18, 4)
    m.put(4, 17, 'P')
    m.hl(12, 15, 5, '-')
    m.put(14, 14, '$')
    m.put(20, 17, '+')
    m.put(22, 17, '&')
    m.box(27, 16, 3, 2, '%')
    m.put(31, 17, EY)
    m.hl(33, 15, 5, '-')
    m.put(35, 14, '$')
    m.put(40, 17, TL)
    m.hl(44, 15, 5, '-')
    m.put(46, 14, '$')
    m.put(46, 11, J)
    m.put(44, 17, BL)
    m.row(36, 17, '$.$')
    m.row(45, 17, '$.$')
    m.put(53, 17, 'n')
    m.put(55, 17, 'C')
    m.put(57, 17, 'H')
    m.put(59, 17, '&')
    m.put(61, 17, 'o')
    m.put(10, 13, 'L')
    m.put(24, 13, 'l')
    m.put(42, 13, 'L')
    m.put(58, 12, 'l')
    # the shaft down into the arena
    m.room(63, 18, 3, 1)

    # ================================================================ the arena (x62-103, y19-31, floor 32)
    m.room(62, 19, 42, 13)
    m.hl(66, 29, 5, '-')
    m.hl(90, 29, 5, '-')
    m.put(82, 28, '!')
    m.put(62, 31, 'H')
    m.put(64, 31, '&')
    m.put(103, 31, 'H')
    m.put(101, 31, '&')
    m.put(99, 31, 'E')
    m.put(68, 21, 'L')
    m.put(82, 20, 'l')
    m.put(96, 21, 'L')
    return m


if __name__ == '__main__':
    main(build, 'e4l9')
