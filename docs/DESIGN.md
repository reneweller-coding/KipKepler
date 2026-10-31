# KIP KEPLER -- design and contracts

An original 2D action platformer in HD pixel art, in the spirit of the early-90s shareware jump-and-runs (collect all
crystals to open the exit, keys and doors, power-ups, treasure, secrets, four episodes with a boss each), set in
science fiction. Own world, own characters, own levels. PC (Windows, Linux) and Steam Deck.

This file is the contract between the engine (src/, C++20 + raylib 5.5) and the asset generators (tools/, Python
3.12 + numpy + Pillow + scipy). Generators write into assets/; the game reads only assets/.

## Story (short)

The Beacon Corps keeps the great lighthouses of the Spiral lit: beacons whose prism cores guide every ship through
the dark between the stars. Kip Kepler is its most junior cadet, a repair tech who has never been off the Academy
ring. On the night of his graduation exam the Gloam -- a cold machine syndicate that wants the lanes dark and every
ship lost to it -- shatters the four sector beacons and scatters their prism shards across four sectors. The
Commodore sends the only cadet still on duty. Collect the shards (the crystals), relight the beacons, and maybe get
promoted.

Episodes (9 levels each, the 9th a boss level):

| Ep | Name (en / de)                         | Themes (tile sets)   | Boss          |
|----|----------------------------------------|----------------------|---------------|
| 1  | Academy Ring / Akademiering            | station, hull        | WARDEN (security mech gone rogue) |
| 2  | Verdant Moon Thessa / Grüner Mond Thessa | jungle, hive       | BROODMOTHER (hive queen) |
| 3  | Comet Mines of Ysk / Kometenminen von Ysk | ice, crystal      | COLOSSUS (crystal giant) |
| 4  | The Gloam Dreadnought / Das Gloam-Schlachtschiff | foundry, citadel | THE GLOAM (the syndicate's core, in a war frame) |

Humour is light and friendly (signs, the Commodore's messages between levels), never grim.

## Screen and pixels

* Virtual resolution 640 x 360 (16:9). On 16:10 screens (Steam Deck 1280 x 800) the view is 640 x 400. The game draws
  into that render target and scales it up by an integer factor (nearest neighbour), letterboxing the rest.
* Tile size 32 x 32 px. The view shows 20 x 11.25 tiles (20 x 12.5 on the Deck).
* Pixel art: no anti-aliasing, no semi-transparent edge pixels in sprites (alpha is 0 or 255), every colour from the
  shared palette (tools/common/palette.py). Light comes from the top left. Sprites have a 1 px dark outline
  (palette.OUTLINE or the darkest shade of the touching ramp); tiles have no outline but a bright top edge and darker
  lower edge.
* Modern effects are the engine's job: dynamic light, bloom on emissive pixels, particles, parallax, screen shake.
  Generators may supply an emissive mask: `<sheet>_glow.png`, same layout as the sheet, only the glowing pixels
  opaque (in their glowing colour), everything else transparent.

## Physics (the level designers and the checker rely on these numbers)

| Quantity                    | Value                     | In tiles |
|-----------------------------|---------------------------|----------|
| Hero box                    | 20 x 44 px                | 0.63 x 1.38 |
| Run speed                   | 210 px/s                  | 6.6 t/s |
| Gravity                     | 1900 px/s^2               |          |
| Jump speed                  | 640 px/s                  | apex 108 px = 3.37 t |
| Super jump (boots)          | 900 px/s                  | apex 213 px = 6.6 t |
| Fall speed cap              | 1000 px/s                 |          |
| Thrown out of a pool        | apex 136 px (`PoolLift`)  | 4.25 t |
| Releasing jump early        | vy *= 0.45                |          |
| Coyote time / jump buffer   | 0.08 s / 0.12 s           |          |

Consequences: a ledge 3 tiles higher can be reached, 4 cannot (without boots). Flat gaps up to 4 tiles can be jumped.
The hero needs 2 free tiles of headroom. One-way platforms (`-`) are landed on from above, jumped through from below,
and dropped through with down + jump.

Pools hurt instead of killing (as in the old games): each time the hero comes down into one, it costs health (20,
lava and plasma 30, then none for 1.1 s) and throws him out, about four tiles high, knocked back the way he came and
steerable. So a pool's surface lies at most 3 tiles below a bank, a ledge or a platform that leads on (4 would
just work with exact steering -- too tight). The checker throws the hero out of every spot of every pool's surface
(steering left, right, not at all; a little weaker than the game, 112 px, for that slack; moving platforms do not
count) and warns when getting out costs more than two hits ("WARN  pool: ..."; the summary counts "deep pool cells", which must be 0);
`tools/levels/raise_pools.py` raises such pools to three tiles below the lower bank (or `--to` a line).

## Weapons (science fiction, no magic)

Kip carries an arm cannon. Weapons are found in levels and kept for the rest of the game; LB/RB (Q/E, mouse
wheel) switch between the weapons he has. All but the blaster use ammo; ammo cells (`&`) refill a share of every
weapon's ammo, enemies sometimes drop small ones. Holding up aims upwards (standing and in the air). Credits from
treasure buy upgrades at the Quartermaster between levels (3 steps per weapon: damage, ammo, special; armour steps
for more health).

| Weapon (en / de)            | Found in | Behaviour |
|-----------------------------|----------|-----------|
| Pulse blaster / Pulsblaster | start    | bolts, infinite; hold fire to charge a piercing big shot (0.8 s) |
| Repeater / Repetierer       | Ep 1     | fast stream of small bolts |
| Scatter / Streuer           | Ep 1     | fan of 5 short-range pellets |
| Ricochet / Querschläger     | Ep 2     | discs that bounce off walls, floors and ceilings up to 4 times |
| Cryo projector / Kryowerfer | Ep 2     | freezes enemies into ice blocks for 5 s: they can be stood on; a hit shatters them |
| Lancer / Lanze              | Ep 3     | an instant beam through all enemies up to the next wall |
| Plasma mortar / Plasmamörser | Ep 3    | lobbed shell, explodes with splash (hits enemies below or above ledges) |
| Arc caster / Bogenwerfer    | Ep 4     | short-range lightning that jumps to up to 4 nearby enemies |
| Seeker / Sucher             | Ep 4     | three small homing missiles per shot |

Power-ups (timed): `overdrive` (double fire rate and damage, 15 s), `boots` (super jump, rest of the level),
`shield` (invulnerable, 12 s).

## Level files (assets/levels/e<N>l<M>.txt, e.g. e1l1.txt; bosses e1l9 ... e4l9)

Plain UTF-8 text. `#` at line start = comment. Keys first, then `map` ... `end`.

```
name      Docking Ring Delta
name.de   Andockring Delta
theme     station          # tile set folder in assets/tiles/
tint      0                # palette variant of the tile set, 0-3
bg        station_a        # background folder in assets/bg/
music     e1_a             # music cue (assets/music/<cue>.ogg)
dark      0.2              # 0 = fully lit, 0.8 = very dark (lights matter)
par       240              # par time in seconds
gravity   1.0              # optional, 0.6 = low gravity
legend a  enemy sweeper
legend b  enemy hoverdrone ambush
legend r  weapon repeater
legend 1  teleport 2
legend 2  teleport 1
legend s  switch A
legend A  toggle A solid
legend Z  toggle A empty
legend m  mover 0 -6 60
legend t  sign hint.jump
legend !  boss warden
map
<rows of characters>
end
```

Rows may differ in length; short rows are padded with `' '` (sky). Max 400 x 160 tiles. The map must be closed:
the hero may only leave it through the bottom (that is death).

### Fixed characters (no legend needed)

| Char | Meaning |
|------|---------|
| ` `  | empty, open sky (the parallax background shows) |
| `.`  | empty, interior (the theme's back wall shows) |
| `#`  | terrain A (main solid material of the theme) |
| `%`  | terrain B (secondary solid material; in theme `ice` it is slippery ice) |
| `-`  | one-way platform |
| `_`  | crumbling block: solid, falls 0.5 s after the hero stands on it, back after 4 s |
| `B`  | breakable block: solid, destroyed by 2 shots |
| `X`  | fake wall: looks like `#`, can be walked through (secret passages) |
| `^`  | spikes on the floor (point up) -- hurt 25 and bounce |
| `v`  | spikes on the ceiling (point down) |
| `<` `>` | spikes on a wall (pointing left / right) |
| `~`  | liquid (acid, lava, plasma, freezing brine -- by theme): hurts (20, lava and plasma 30) and throws the hero out, about four cells high (`phys::PoolLift`) -- a fall costs health, not a life |
| `*`  | crystal (prism shard). All must be collected to open the exit |
| `$`  | treasure, the kind picked by the engine (100-500 points) |
| `+`  | health, small (+20) |
| `H`  | health, big (+60) |
| `&`  | ammo cell (refills a share of every weapon) |
| `k` `K` | key card blue / gold |
| `d` `D` | door blue / gold: solid until the hero holds that colour's key. Stack 2-3 cells vertically for one door |
| `?`  | secret zone (invisible; drawn as interior). Touching it counts the secret once per connected group |
| `P`  | hero start (stands on the floor below) |
| `E`  | exit portal (stands on the floor below; 2 x 3 tiles). Opens when all crystals are taken |
| `C`  | checkpoint beacon (stands on the floor below) |

### Legend entries (per level; any free character)

| Legend                     | Meaning |
|----------------------------|---------|
| `enemy <type> [ambush] [left] [hp=N]` | an enemy (types below). `ambush`: invisible until the hero comes within 7 tiles, then it beams in |
| `weapon <kind>`            | a weapon pickup: `repeater`, `scatter`, `ricochet`, `cryo`, `lancer`, `mortar`, `arc`, `seeker` |
| `power <kind>`             | power-up: `overdrive`, `boots`, `shield` |
| `treasure <kind>`          | a specific treasure: `gem` 100, `chip` 200, `cube` 300, `idol` 500, `crown` 1000 |
| `teleport <char>`          | entering it puts the hero on the cell of `<char>` (one way; make two for both ways); a pad the hero arrives on fires only after he has stepped off it |
| `switch <group>`           | a lever (shoot or touch) that flips group `<group>` (letter A-H) |
| `toggle <group> solid`     | solid block while its group is off, gone while it is on |
| `toggle <group> empty`     | gone while its group is off, solid while it is on |
| `mover <dx> <dy> <speed> [wait]` | moving one-way platform; a horizontal run of the same char = one platform; travels dx, dy tiles and back, speed px/s, wait s at the ends (default 0.6) |
| `spring`                   | bounce pad: launches the hero about 11 tiles up (1180 px/s) |
| `conveyor <dir>`           | solid conveyor belt (dir -1 or 1), moves the hero 90 px/s |
| `laser <h|v> <on> <off> [phase]` | laser fence emitter on a wall (h) or floor/ceiling (v); the beam runs away from that wall to the next solid cell; on/off seconds, optional start phase in seconds |
| `crusher <tiles> <period> [phase]` | a ceiling crusher that slams down `<tiles>`; optional start phase in seconds |
| `sign <textkey>`           | a sign; text from assets/text/<lang>.txt |
| `light <colour> <radius>`  | a lamp (colour names from the palette ramps, radius in tiles) |
| `boss <type>`              | the boss (boss levels). The exit opens when it dies |

### Enemies (sprite sheet = type name; behaviour archetype in brackets)

Episode 1 (robots): `sweeper` (walker), `sentry` (shooter), `hoverdrone` (flier), `turret` (turret, on a wall or
ceiling), `sparkmine` (floater, homing, explodes), `rammer` (charger), `springbot` (hopper), `fabricator` (spawner of
hoverdrones), `mirrorbot` (mirror: walks at the hero behind a mirror that throws plain shots from the front back).
Boss `warden`.

Episode 2 (creatures): `beetle` (walker, armoured front), `spitter` (shooter: lobs acid arcs), `mothling` (flier),
`leaper` (hopper), `snapvine` (dropper from the ceiling), `sporepod` (floater, bursts into spores), `stalker`
(charger), `hivenest` (spawner of mothlings), `brineeel` (eel: placed in the cell above a pool, lurks under the
surface, leaps at the hero passing above, only hurt while out). Boss `broodmother`.

Episode 3 (ice and crystal): `crystalcrab` (walker), `icebat` (flier, swoops), `shardling` (hopper),
`cryoturret` (turret), `minerbot` (shooter), `burrower` (ambusher from the ground), `frostgolem` (charger, heavy),
`wisp` (floater, homing), `shardsniper` (sniper: aims about a second along a visible line, the last 0.3 s held
still, then one fast shard). Boss `colossus`.

Episode 4 (the Gloam): `trooper` (shooter), `shieldbot` (walker, blocks frontal shots), `jetpacker` (flier
shooter), `gloamhound` (charger), `lasereye` (turret, beam), `blinker` (teleports around), `brute` (heavy walker,
throws grenades), `riftgate` (spawner), `deckguard` (rider: placed in the cell above a moving platform, rides it --
asleep too --, walks to and fro on it and shoots). Final boss `gloam`.

The four of the third round come after the blocks of eight in the enemy table with their episode set
(`EnemyDef::m_episode`); `tools/levels/spread_enemies.py` spread the kinds over the levels once (4-6 kinds per level
by stage, conversions only within a movement class, no chargers or grenade throwers next to pits).

## Sprite sheets (assets/sprites/<sheet>.png + <sheet>.txt)

All frames of a sheet have one size, laid out row-major in a grid (columns = png width / frame width). Sprites face
RIGHT; the engine mirrors them for left.

```
frame 64 64            # frame width, height
anchor 32 60           # the point that sits on the entity's position (feet centre for walkers, centre for fliers)
point muzzle 22 -26    # optional named points, offsets from the anchor (facing right)
anim idle 8 loop 0 1 2 3 4 5
anim run 14 loop 6 7 8 9 10 11 12 13
anim die 12 once 40 41 42 43 44 45
```

`anim <name> <fps> <loop|once> <frame indices...>`. Optional `<sheet>_glow.png` (emissive mask, same layout).

Hero (`hero`, frames 64 x 64): idle, run, jump (rising), apex, fall, land, shoot (standing), run_shoot, jump_shoot,
fall_shoot, shoot_up (standing, cannon up), jump_shoot_up, hurt, die, teleport (beam out), appear (beam in),
victory, push (against a wall), look_up, skid. Muzzle points `muzzle` and `muzzle_up`.

Enemy sheets need at least: `idle` or `move` (fliers: `fly`), `attack` (where they attack), `hurt`; `die` optional
(the engine adds an explosion). Bosses as they need (documented in the sheet's .txt comments).

Items (`items`, 32 x 32): `crystal` (spinning, 8 frames), `gem`, `chip`, `cube`, `idol`, `crown`, `health`,
`health_big`, `key_blue`, `key_gold`, `ammo`, `power_overdrive`, `power_boots`, `power_shield`, and the weapon
pickups `weapon_repeater`, `weapon_scatter`, `weapon_ricochet`, `weapon_cryo`, `weapon_lancer`, `weapon_mortar`,
`weapon_arc`, `weapon_seeker`.

Objects (`objects`, 64 x 96): `exit_closed`, `exit_open`, `checkpoint_off`, `checkpoint_on`, `teleporter`,
`switch_off`, `switch_on`, `spring`, `spring_fire`, `sign`, `laser_emitter`.

Shots (`shots`, 32 x 32): `bolt`, `bolt_charged`, `bolt_rapid`, `pellet`, `disc`, `cryo`, `laser` (beam segment
that tiles), `mortar`, `arc` (lightning segment), `seeker`, `enemy_bolt`, `enemy_orb`, `acid`, `shard`, `missile`,
`grenade`, `spore`.

Effects (`fx`, 64 x 64): `muzzle`, `spark`, `explode_s`, `explode_m`, `explode_l` (96-px sheet `fx_big` if needed),
`beam_in`, `dust`, `sparkle`, `pickup`, `splash`, `smoke`, `charge` (gathering energy at the muzzle),
`freeze` (ice forming), `shatter`, `zap` (arc hit).

## Tile sets (assets/tiles/<theme>/, themes: station hull jungle hive ice crystal foundry citadel)

* `terrain_a.png`, `terrain_b.png`, `back.png`: 16 columns x 64 rows of 32 px tiles (512 x 2048). Tile index
  = variant * 256 + mask, variant 0-3, mask = 8 bits of the neighbours that are the same kind (solid for terrain:
  `#`, `%`, `X`, `B`, doors, map border; interior `.`/`?` and anything not sky for `back`):
  bit 0 N, 1 NE, 2 E, 3 SE, 4 S, 5 SW, 6 W, 7 NW. The engine picks the variant from a hash of the cell.
  Exposed edges get a lip/bevel, exposed top edges the theme's surface (rust, moss, frost ...).
* `platform.png`: 4 columns (single, left end, middle, right end) x 4 rows of variants.
* `blocks.png` (32 px tiles, one row each, 4 columns of animation or variants): row 0 breakable, row 1 crumble
  (intact, cracking 1, cracking 2, falling), row 2 door blue (closed, opening 1-3), row 3 door gold, row 4 toggle on,
  row 5 toggle off (ghost outline), row 6 conveyor (4 frames), row 7 spikes up/down/left/right.
* `liquid.png`: row 0 surface (4 frames), row 1 body (4 frames).
* `deco.png` + `deco.txt`: back-wall decorations scattered by the engine. Each line
  `<name> <x> <y> <w> <h> <place> <weight> [glow]`, place = `wall` (on the back wall), `floor` (stands on terrain),
  `ceiling` (hangs from terrain), `edge` (hangs over a ledge). `glow` = the deco gets a light.
* `tints.txt`: 4 lines, one per tint 0-3: `<tint> <r> <g> <b> <hue shift deg> <name>` (the engine's palette shift
  for the whole tile set).

## Backgrounds (assets/bg/<name>/)

`layer0.png` (farthest) ... `layer3.png` (nearest), each 640-1280 wide, 400 high, repeating horizontally, plus
`bg.txt`: one line per layer `layer<n> <parallax x> <parallax y> <y offset> [scroll px/s]`. Layer 0 is opaque; the
others have transparent sky. Names: `<theme>_a`, `<theme>_b` (two per theme).

## Fonts (assets/fonts/)

`small.png` (cells 8 x 12, cap height 7, baseline 9) and `big.png` (cells 16 x 24): 16 glyphs per row, plus
`<font>.txt`: `cell w h`, `baseline n`, then one line per glyph in sheet order: `<codepoint hex> <advance>`.
Characters: ASCII 32-126 plus Ä Ö Ü ä ö ü ß é è à ç ñ € © ° • … « » „ “ ” – — ’ and the button glyphs in the
private use area (E000 A, E001 B, E002 X, E003 Y, E004 LB, E005 RB, E006 dpad, E007 stick, E008 start, E009 select).

## Sounds (assets/sound/<name>.wav, 44.1 kHz 16 bit mono, peaks <= -1 dBFS)

jump, land, step, shoot, charge, charge_full, shoot_charged, shoot_repeater, shoot_scatter, shoot_ricochet,
disc_bounce, shoot_cryo, freeze, shatter, shoot_lancer, shoot_mortar, shoot_arc, shoot_seeker, weapon_switch,
ammo, no_ammo, buy, hit_wall, hit_enemy, armour_ping, hurt, die,
crystal, crystal_last, treasure, health, key, power, door, switch, teleport, checkpoint, exit_open, exit_enter,
break, crumble, spring, secret, enemy_shoot, enemy_orb, acid, missile, grenade, explode_s, explode_m, explode_l,
beam_in, robot_die, creature_die, ice_die, gloam_die, boss_roar, boss_hit, boss_die, laser_fence, crusher, splash,
menu_move, menu_ok, menu_back, score_tick, extra.

## Text (assets/text/en.txt, de.txt)

`key = text` lines. German source, English complete too.

## Extensions (second round)

### Secret levels (assets/levels/e<N>s.txt)
One bonus level per episode, reached through a hidden warp in a host level (legend `warp <levelid>`: an object
standing on the floor like the exit; touching it ends the host level as finished and plays the secret level next;
after it the game goes on with the level after the host). Same format and rules as the others (the checker must
say OK, 0 traps, 0 no-way-back). Text keys `level.e<N>s` in assets/text/<lang>/e<N>.txt.

### Logbook pages (lore)
Legend `lore <key>`: a collectable holo datapad (items sheet anim `lore`). Collected pages stay in the save and are
read in the menu (Logbuch / Logbook). Texts in assets/text/<lang>/lore.txt: `lore.<key>.title` and
`lore.<key>.text` (`|` breaks lines, up to ~8 lines of 60 characters). Keys like `e1_academy_founding`.

### Radio messages (between levels)
Before each level the Commodore radios Kip: `radio.<levelid>` in assets/text/<lang>/radio.txt (one to three
sentences, warm and wry; the last level of an episode leads into the boss). Optional voice:
assets/voice/<lang>/radio_<levelid>.ogg (tools/voices/make_voices.py: Qwen3-TTS locally, one designed voice per
language, a light suit-radio colour, -17 LUFS). Portraits (96x96, tools/sprites/portraits.py):
assets/ui/portrait_commodore.png, portrait_commodore_talk.png (mouth open, shown while her text types) and
portrait_commodore_glow.png (one emissive mask for both); the same three for portrait_kip.

### Story stills
A page `story.e1.intro.2` shows assets/story/e1_intro_2.png (320x180 pixel art, drawn at whole-pixel scale) above
its text when it exists. Made by tools/story/make_stills.py (FLUX locally in WSL, then pixelated to the palette).

### Music and ambience
Each level's piece (`music <cue>`) has a fight variant `<cue>_fight` (assets/music/<cue>_fight_t1.ogg ...): it fades
in while an awake enemy is within ~300 px or the hero is hit, and the calm piece comes back where it left off after
6 s without danger. Bosses have their own piece per episode (`bossmusic boss_e<N>`, falling back to `boss`).
Under the music each theme has an ambience bed, assets/ambience/<theme>.ogg (24 s seamless loop, -30 LUFS, played
with the effects volume while a level runs), made by tools/sfx/make_ambience.py.

GPU jobs (music, stills, voices) run through tools/gpu_queue.py, which waits for the shared flag
G:/Tools/Games/GPU_BELEGT.txt (and GPU_PAUSE.txt) to be gone and holds it while its jobs run.

### Sprites of the second round
items: `lore` (frames 128-135, a datapad with a hologram, the logbook page). objects: `warp` (frames 47-54, the
portal to the secret level, about 46x70 px; `point warp 0 -41` is the ring's centre).

### Foreground layer
assets/bg/<name>/fore.png (any width, 400 high, transparent except dark silhouettes at the top and bottom edges:
girders, leaves, stalactites, pipes) and in bg.txt a line `fore <parallax x> <parallax y> <y offset>` (parallax > 1:
it moves faster than the world). Drawn in front of the world, behind the HUD; it must never hide the middle of the
screen. Sideways it moves with `-camera x * parallax x` (repeating every 1280 px); up and down it stays with the
screen (its top row at the y offset on a 400 high view, 20 px higher on 360) and only sways by at most 10 px while
the camera catches up (`parallax y - 1` times the camera's lag). Made by tools/backgrounds/fore.py.

### Elite enemies
Legend flag `elite` (or `elite=<kind>` with kind armoured, swift, splitting, shielded, regenerating) on any enemy;
on Hard and in New Game+ some enemies become elite by themselves. Drawn with a coloured outline glow.

### Ceiling walkers
Legend flag `ceiling` on a walker (crystalcrab, beetle, sweeper): it walks upside down along the ceiling above its
cell (drawn flipped), turning at walls and ceiling edges.

## Extensions (third round)

Files in the player's folder (Save.h userDir()), all plain text but the ghosts:

| File | What |
|---|---|
| `deaths.txt` | one knockout per line: `<level id> <x> <y> <cause> <difficulty> <mode> <date>`; cause is an enemy kind, a shot's animation, `laser`, `crusher`, `liquid`, `spikes`, `fall`, `explosion` or `giveup`; mode `play`, `trial`, `challenge`, `rush`, `editor`. The autopilot's test writes the same lines into `deaths.txt` beside its report. The editor shows them (H), KeplerTool draws them (`deaths`). |
| `ghosts/<id>.ghost` | a time trial's best run: `KKG1`, a uint32 count, then per 1/30 s of the level's clock x, y (float), the hero sheet's frame (int16), facing (int8) |
| `suspend<slot>.txt` | a level left in the middle (pause, the window closed, the focus lost): `level <id>` and World::snapshot() -- counters, the hero (where he stood if firm, else the checkpoint), pickups taken and enemies beaten (by their index in the level), hurt enemies, broken blocks, open doors, secrets, the checkpoint, the explored cells as runs. Only the episodes' own run keeps one; finishing or restarting the level drops it. |
| `challenges.txt` | `<key> <seconds> <date>`, the five best per key; key `<id>+<mods>` or `daily<yyyymmdd>:<id>+<mods>` |
| `perf.txt` | with the performance display on: a line a second -- level, fps, average and longest frame, the fps setting, battery percent and watts (Linux / Steam Deck: /sys/class/power_supply/BAT1) |

Challenges: the mods are bits -- 1 blaster only, 2 one hit (any hit knocks out), 4 low gravity (x 0.6), 8 darkness
(the level's dark at least 0.88), 16 turbo (the game 1.3 times as fast). The daily challenge hashes the date: one of
the levels open to the player and two of the five. A challenge plays with a copy of the progress (full ammo) and
gives no score or credits; pages and enemy kinds found count.

Bestiary: `beast.<id>`, `beast.<id>.text`, `beast.<id>.weak` in `assets/text/<lang>/bestiary.txt` for every enemy
kind and the four bosses; a kind counts as seen once it was on the screen (Progress::m_seen, `seen` lines in the save).

Pause map: one pixel per cell, only cells that have been on the screen (World::m_explored); the crystals still missing
everywhere, keys, pages and checkpoints where explored, the exit, the hero.

Colour help: closed doors and keys get a square (blue) or a triangle (gold); laser fences and crushers draw yellow
warning stripes over what they hurt now (bright) and in the next 0.6 s (faint).
