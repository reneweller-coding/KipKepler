# KIP KEPLER -- the 36 levels

Read docs/DESIGN.md first (level file format, fixed characters, legend kinds, physics). This file is the plan per
level and the rules of good level design for this game.

## Tools

* `work\tool\KeplerTool.exe check assets\levels\e1l1.txt work\levels\e1l1_check.png` -- plays the hero's own
  physics from every standing place: reports unreachable crystals/keys/exit (ERROR), unreachable
  treasure/health/weapons/secrets/checkpoints (WARN) and traps (places from which neither the exit nor a death is
  reachable). The PNG is an overview (6 px per tile): green = places the hero stood/passed, red crosses = unreachable
  things, orange = traps. A level is done only with `OK` and no ERROR line.
* `work\tool\KeplerTool.exe render assets\levels\e1l1.txt work\levels\e1l1.png 0.5` -- the whole level with its real
  tiles and sprites (CPU only). `... render <level> <out.png> x y w h` -- a part (tiles), twice as large: use it to
  look at every area at the scale the player sees (the screen shows 20 x 11 tiles).
* `work\tool\KeplerTool.exe checkall assets\levels` -- all levels. Pools must be left with at most two hits
  (`deep pool cells 0`): see docs/DESIGN.md, Physics.
* Do NOT start KipKepler.exe yourself (it uses the GPU that other jobs share).

The checker's limits: breakable blocks `B` count as open, so put them only where the hero can shoot them (horizontal
shots fly at the row just above the floor he stands on; he can also shoot straight up); movers count as present at
every stop of their path; lasers and crushers are ignored (keep them avoidable); freezing enemies into platforms
(cryo) is never required; enemies are ignored.

## Rules of a good level here

* The heart of the genre: explore a big map, collect ALL crystals (`*`) to open the exit (`E`). Crystals lead the
  player through every part of the map; treasure (`$`) rewards side paths and trails of it show the way. Keys
  (`k`/`K`) and doors (`d`/`D`), switches with toggle blocks, teleporters and fake walls (`X`) give structure.
* Size: 120-260 tiles wide, 40-90 high (episode 1 smaller, then growing); boss levels smaller. 15-30 crystals,
  30-70 treasure, 2-4 secrets (`?` areas, often behind `X` walls or breakable `B` blocks, rewarding treasure, health,
  ammo or a power-up), 1-3 checkpoints (`C`) on long routes, health (`+`, `H`) every 40-60 tiles of route and before
  hard parts, ammo cells (`&`) from episode 2 on (once the hero owns ammo weapons).
* Readable play space: corridors at least 2 tiles high (the hero is 1.4 tiles), most rooms 3-8 tiles high, jumps of
  at most 3 tiles up and 4 tiles across (DESIGN.md "Physics"); leaps of faith only when treasure or a sign shows
  where to go. A gap the hero falls into must have a way out (or be deadly: liquid, spikes, the bottom).
* Variety in a level: a few distinct areas (a hall, a shaft, a cave, a bridge over a pit, a secret vault), a mix of
  horizontal and vertical movement, some optional branches, and backtracking only when it opens something new
  (a key opens the door you passed).
* Enemies: 25-50 per level (episode 1: 20-35), a mix of the episode's kinds, some `ambush` ones that beam in when
  the hero comes near. Shooters on ledges, fliers in big rooms, walkers on long floors; turrets on walls/ceilings.
  No enemy right at the start or right after a checkpoint. Give the player room to react.
* Each level introduces or features one or two mechanics (see the plan) and teaches it safely first.
* Terrain `#` is the theme's main material, `%` the secondary one (blocks, crates, ruins; on `ice` slippery ice):
  use both for visual variety. Interior rooms use `.` (back wall), open sky uses ` `. Mix both where it makes sense
  (outdoor levels mostly sky, station levels mostly interior with windows of sky).
* Signs (`legend t sign <key>`) only in the first levels and for new mechanics; their text goes into
  assets/text/de/e<N>.txt and assets/text/en/e<N>.txt (`sign.e1l1.jump = Springe mit LEERTASTE / A!`; `|` breaks a
  line; max ~45 characters per line, 3 lines). Use `{jump}`-free plain wording that works for keyboard and pad
  ("Springen: Leertaste / A").
* Also in those text files: the level names `level.e1l1 = Kadettenquartiere` (de) / `level.e1l1 = Cadet Quarters`
  (en).
* Lights (`legend L light warm 6`) in dark levels (`dark 0.4`+): a lamp every 10-15 tiles of route, coloured to the
  theme. Normal levels `dark 0.1`-`0.3`.
* Weapons are placed where the plan says, early in that level, in a spot where the next fight shows what it is good
  for. Power-ups: 1-2 per level (`overdrive`, `shield`; `boots` only where super jumps open optional heights).
* Keys: `music` per the plan, `bg` `<theme>_a` or `<theme>_b`, `par` = a good first run in seconds (roughly 1 s
  per 1.2 tiles of route plus fights), `tint` 0-3 to vary the look between levels of one theme.

## Boss levels (e<N>l9)

A short approach (40-80 tiles, a checkpoint, health, ammo) into an arena: a flat floor 30-40 tiles wide and 10-14
tiles high, a few one-way platforms (`-`) 3 tiles above the floor to dodge on, the boss (`legend ! boss <type>`) on
the far side of the arena, standing on the floor, and the exit `E` in the arena (it opens when the boss dies). Health
`H` x2 and ammo `&` x2 in the arena's corners. No crystals required in the arena (a few in the approach are fine;
the exit needs all of them AND the boss dead). The arena must be closed (the hero cannot leave it once inside, or
can only go back to the approach).

## The plan

Music cues: e1_station e1_hull e2_jungle e2_hive e3_ice e3_crystal e4_foundry e4_citadel (bossmusic: boss).

### Episode 1 -- The Academy Ring (themes station, hull)
Enemies: sweeper (walker), sentry (shooter), hoverdrone (flier), turret, sparkmine (homing mine), rammer (charger),
springbot (hopper), fabricator (spawner of hoverdrones), mirrorbot (mirror, from e1l3). Weapons: repeater in e1l3,
scatter in e1l6.

| Level | Name (en / de) | Theme / bg | Features |
|---|---|---|---|
| e1l1 | Cadet Quarters / Kadettenquartiere | station / station_a | tutorial: run, jump, shoot, crystals, one checkpoint, one easy secret (fake wall), signs; small (~110x40); sweepers, hoverdrones |
| e1l2 | Maintenance Deck / Wartungsdeck | station / station_a | one-way platforms, blue key + door, crumble blocks (`_`), sentries |
| e1l3 | Hangar Bay 7 / Hangar 7 | station / station_b | movers across a hangar, repeater weapon, turrets, spikes |
| e1l4 | Outer Hull / Außenhülle | hull / hull_a | outdoors in space (mostly sky), springs, sparkmines, ambushes, plasma pits |
| e1l5 | Reactor Spine / Reaktorrückgrat | station / station_a, dark 0.45 | laser fences, switches + toggles, gold key, lights |
| e1l6 | Cargo Conveyors / Frachtbänder | station / station_b | conveyors, crushers, rammers, scatter weapon |
| e1l7 | Antenna Field / Antennenfeld | hull / hull_b | a vertical climb, movers, springbots, `gravity 0.8` |
| e1l8 | Security Core / Sicherheitskern | station / station_a, dark 0.35 | everything mixed, fabricators, teleporters, both keys; the longest of ep 1 |
| e1l9 | The Warden / Der Wächter | station / station_b | boss `warden` |

### Episode 2 -- Verdant Moon Thessa (themes jungle, hive)
Enemies: beetle (armoured walker), spitter (acid lobber), mothling (flier), leaper (hopper), snapvine (drops from the
ceiling), sporepod (floater), stalker (charger), hivenest (spawner of mothlings), brineeel (leaps from the pools).
Weapons: ricochet in e2l2, cryo in e2l5.

| Level | Name (en / de) | Theme / bg | Features |
|---|---|---|---|
| e2l1 | Landing Glade / Landelichtung | jungle / jungle_a | outdoors, acid pools, beetles, leapers, big sky |
| e2l2 | Root Caverns / Wurzelhöhlen | jungle / jungle_b | caves, crumble blocks, snapvines, ricochet weapon (corners) |
| e2l3 | Canopy Bridges / Kronenbrücken | jungle / jungle_a | high up: one-way bridges, springs (bounce pods), mothlings, deadly fall |
| e2l4 | The Sunken Temple / Der versunkene Tempel | jungle / jungle_b, dark 0.4 | ruins (`%`), switch puzzles, teleporters, many secrets |
| e2l5 | Hive Outskirts / Rand des Stocks | hive / hive_a | cryo weapon, spitters, resin pools |
| e2l6 | Spore Marsh / Sporensumpf | jungle / jungle_b, dark 0.3 | sporepods, acid, crumble, stalkers |
| e2l7 | Amber Tunnels / Bernsteintunnel | hive / hive_b | vertical shafts, movers, snapvines |
| e2l8 | The Nursery / Die Brutkammern | hive / hive_a, dark 0.5 | hivenests, stalkers, ambushes, gold key |
| e2l9 | Broodmother / Brutmutter | hive / hive_b | boss `broodmother` (flies: give the arena 12-14 tiles of height) |

### Episode 3 -- The Comet Mines of Ysk (themes ice, crystal)
Enemies: crystalcrab (walker), icebat (swoops from the ceiling), shardling (hopper), cryoturret, minerbot (shooter),
burrower (bursts from the ground), frostgolem (heavy charger), wisp (homing, passes rock), shardsniper (aims, then one
fast shot, from e3l2). Weapons: lancer in e3l2, mortar in e3l6. `%` on ice is slippery.

| Level | Name (en / de) | Theme / bg | Features |
|---|---|---|---|
| e3l1 | Drill Camp / Bohrlager | ice / ice_a | comet surface (sky), `gravity 0.85`, minerbots, slippery ice intro |
| e3l2 | Frozen Shafts / Gefrorene Schächte | ice / ice_b | lancer weapon, icebats, long ice slides |
| e3l3 | Glittering Grotto / Glitzergrotte | crystal / crystal_a, dark 0.5 | crystal lights, crystalcrabs, secrets |
| e3l4 | Ore Elevators / Erzaufzüge | ice / ice_b | big vertical movers, crushers, cryoturrets |
| e3l5 | Brine Lake / Solesee | crystal / crystal_b | liquid lake with crumble-ice bridges, shardlings |
| e3l6 | Prism Halls / Prismenhallen | crystal / crystal_a | mortar weapon, switches, teleporters |
| e3l7 | Avalanche Run / Lawinenlauf | ice / ice_a | long horizontal run, burrowers, frostgolems |
| e3l8 | Heart of the Comet / Herz des Kometen | crystal / crystal_b, dark 0.55 | everything, wisps, both keys |
| e3l9 | The Colossus / Der Koloss | crystal / crystal_a | boss `colossus` (tall: 13-14 tiles of arena height) |

### Episode 4 -- The Gloam Dreadnought (themes foundry, citadel)
Enemies: trooper (shooter), shieldbot (armoured walker), jetpacker (flying gunner), gloamhound (charger), lasereye
(beam turret), blinker (teleports and shoots), brute (heavy, grenades), riftgate (spawner of troopers), deckguard
(rides the movers). Weapons: arc in e4l2, seeker in e4l5.

| Level | Name (en / de) | Theme / bg | Features |
|---|---|---|---|
| e4l1 | Boarding Breach / Enterbresche | foundry / foundry_b | lava, troopers, gloamhounds |
| e4l2 | Forge Decks / Schmiededecks | foundry / foundry_a | conveyors, crushers, arc weapon |
| e4l3 | Coolant Ducts / Kühlschächte | foundry / foundry_a, dark 0.5 | tight ducts, lasers, brutes |
| e4l4 | The Long Barracks / Die langen Kasernen | citadel / citadel_a | shieldbots, lasereyes, both keys |
| e4l5 | Engine Cathedral / Maschinenkathedrale | foundry / foundry_b | movers over lava, seeker weapon, jetpackers |
| e4l6 | Neon Labyrinth / Neonlabyrinth | citadel / citadel_b, dark 0.45 | teleporters, toggles, blinkers |
| e4l7 | Hangar of Shadows / Hangar der Schatten | citadel / citadel_a | open spaces, jetpackers, springs |
| e4l8 | Core Approach / Kernzugang | citadel / citadel_b, dark 0.4 | everything, riftgates, the hardest level |
| e4l9 | The Gloam / Das Gloam | citadel / citadel_b | final boss `gloam` (floats, teleports: a wide arena) |
