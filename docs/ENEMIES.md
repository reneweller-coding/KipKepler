# KIP KEPLER -- enemy and boss sprites (brief for the sprite makers)

Sheets go to assets/sprites/<id>.png + <id>.txt (+ <id>_glow.png), built with the baker in tools/sprites (read
tools/sprites/README.md and docs/DESIGN.md "Sprite sheets"). One model file per enemy: tools/sprites/models/<id>.py,
registered in tools/sprites/build.py's MODELS.

## How the engine draws an enemy

* The enemy's position is the BOTTOM CENTRE of its hit box, for every kind (fliers too). The sheet's `anchor` must
  be that point: walkers stand on it, fliers hover with the bottom of their body there. The sprite should cover its
  box (it may stick out a few pixels; tails, wings and antennae may stick out more).
* Sprites face RIGHT; the engine mirrors them when the enemy walks left.
* Turrets (`turret`, `cryoturret`, `lasereye`) are drawn upright on floors (the base on the anchor line) and rotated
  by 180 degrees about the anchor when they hang from a ceiling: draw them standing on their base.
* Droppers and swoopers (`snapvine`, `icebat`) hang from a ceiling: their box top touches the ceiling. Draw them
  hanging (the anchor is still the bottom centre of the box; the art reaches up to the box top and a bit beyond for
  the stalk / the feet gripping the rock).
* Burrowers (`burrower`) are invisible while underground; their sheet only needs the above-ground animations.
* Animations used by the engine (missing ones fall back to the sheet's first animation):
  `move` (walkers, chargers, droppers climbing back), `idle` (standing, turrets, spawners, hoppers on the ground,
  hanging swoopers/droppers), `fly` (fliers, floaters, swoopers returning), `attack` (shooting, charging, a hopper in
  the air, a dropper falling, a swooper diving, a spawner beaming something in), `hurt` (a charger stunned after
  hitting a wall). Deaths are explosions drawn by the engine (no `die` needed).
* Shooters need a `point muzzle x y` (offset from the anchor, facing right) where their shots appear.
* Emissive bits (eyes, lights, energy) go into the glow mask: they glow in dark levels.
* Frame sizes: small and medium 64x64, heavy ones 96x96, bosses 128x128 to 192x192. Anchor e.g. (32, 60) in a 64
  frame (leave room for the outline below the feet like the hero does: see the README's ground line note).

## The enemies (id, box w x h, behaviour, look)

Colour worlds: episode 1 = the Academy ring's machines (steel, white, teal lights, hazard yellow; friendly
industrial designs gone haywire, red warning eyes); episode 2 = the jungle moon Thessa's creatures (greens, teal,
violet, amber; bioluminescent spots); episode 3 = the comet's ice and crystal life plus mining robots (icy blues,
white, cyan, violet crystal; the robots orange/yellow mining livery); episode 4 = the Gloam's machine army
(black-violet alloy, magenta/cyan neon, sharp angular shapes, cold menace).

Episode 1:
| id | box | behaviour | look |
|---|---|---|---|
| sweeper | 26 x 20 | walks back and forth | a floor-cleaning robot with brushes, one red eye, scuttling |
| sentry | 22 x 40 | patrols, stops, shoots straight ahead | a slim security robot with a blaster arm (muzzle) |
| hoverdrone | 26 x 18 | floats, chases | a round drone with a rotor and a lens eye (fly) |
| turret | 26 x 26 | fixed, aims and shoots | a wall/floor gun turret on a base, swivel barrel (muzzle) |
| sparkmine | 18 x 18 | drifts at the hero, explodes on touch | a spiky floating mine crackling with sparks (fly) |
| rammer | 34 x 28 | walks, revs, charges | a squat forklift/bulldozer bot with a ram plate (attack = charging, hurt = dazed with sparks) |
| springbot | 24 x 28 | hops at the hero | a robot on a big spring leg (idle = compressed, attack = in the air) |
| fabricator | 44 x 44 | beams in hoverdrones | a fabrication pod / machine block with a glowing hatch (attack = hatch open) |

Episode 2:
| id | box | behaviour | look |
|---|---|---|---|
| beetle | 30 x 22 | walks; its front shell blocks shots | an armoured beetle with a big front shell plate |
| spitter | 26 x 34 | stands, lobs acid arcs | a carnivorous plant bulb with a spitting mouth (muzzle) |
| mothling | 26 x 20 | flies, chases | a glowing moth with patterned wings (fly) |
| leaper | 26 x 24 | hops at the hero | a frog-like alien hopper |
| snapvine | 24 x 30 | hangs from the ceiling, drops, snaps, climbs back | a vine-pod with jaws hanging from a stalk |
| sporepod | 22 x 22 | drifts at the hero, puffs spores | a floating spore balloon with tendrils (fly) |
| stalker | 36 x 30 | walks, charges | a lean raptor-like predator |
| hivenest | 48 x 48 | beams in mothlings | a pulsing hive mound with openings |

Episode 3:
| id | box | behaviour | look |
|---|---|---|---|
| crystalcrab | 30 x 20 | walks | a crab with crystal growths on its shell |
| icebat | 26 x 20 | hangs from the ceiling, dives at the hero, flies back | an icy bat (idle = hanging upside down, attack = diving, fly) |
| shardling | 24 x 26 | hops at the hero | a small living crystal creature |
| cryoturret | 26 x 26 | fixed, aims and shoots ice shards | a frosted turret (muzzle) |
| minerbot | 26 x 38 | patrols, shoots | a mining robot with a drill arm and a gun (muzzle) |
| burrower | 30 x 24 | bursts out of the ground, then walks | an ice worm / burrowing beast |
| frostgolem | 40 x 46 | walks heavy, charges | a hulking ice golem (96 frame) |
| wisp | 20 x 20 | drifts through rock at the hero | a cold ghost light (fly; mostly glow) |

Episode 4:
| id | box | behaviour | look |
|---|---|---|---|
| trooper | 24 x 42 | patrols, shoots | a Gloam soldier android with a rifle (muzzle) |
| shieldbot | 30 x 36 | walks; its front shield blocks shots | a robot carrying a big energy shield |
| jetpacker | 26 x 36 | flies at shooting distance, shoots | a Gloam trooper with a jetpack (fly, attack; muzzle) |
| gloamhound | 36 x 26 | walks, charges | a robotic hound |
| lasereye | 28 x 28 | fixed, charges a beam | a floating/mounted eye emitter on a base (attack = charging glow) |
| blinker | 24 x 36 | teleports near the hero and shoots | a phasing assassin android (idle, attack; muzzle) |
| brute | 40 x 50 | walks heavy, throws grenades | a hulking heavy android (96 frame; muzzle = throwing hand) |
| riftgate | 48 x 64 | beams in troopers | a portal frame with a swirling rift (96 frame) |

## The bosses (one sheet each)

| id | box | frame | behaviour (animations) |
|---|---|---|---|
| warden | 60 x 78 | 128 or 160 | the Academy's security mech gone rogue: walks at the hero (move), fires missiles from shoulder pods (attack), jumps and stomps (jump), calls drones (attack), idle; white/steel armour, hazard stripes, red visor; muzzle at the pods |
| broodmother | 84 x 60 | 160 | the hive queen: flies in a figure eight (fly), spits acid (attack), dives (attack), idle; huge insect with translucent wings, glowing abdomen |
| colossus | 76 x 108 | 160 or 192 | a crystal giant: slow steps (move), slams the ground / fires an ice beam (attack), idle; ice and violet crystal, glowing core |
| gloam | 68 x 84 | 128 or 160 | the Gloam's core in a floating war frame: hovers (fly), attacks (attack: rings of orbs, beams), idle; black-violet angular frame around a cold magenta/white core, the final boss -- make it imposing |
