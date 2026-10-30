/**
 * @file Content.h
 * @brief The game's tables: weapons, enemy kinds, treasures; and the player's progress carried between levels.
 * @author Rene Weller
 */
#pragma once

#include <array>
#include <map>
#include <string>
#include <vector>

namespace kepler
{

/** @brief Kip's weapons (docs/DESIGN.md "Weapons"). */
enum class WeaponE : int
{
    BLASTER,
    REPEATER,
    SCATTER,
    RICOCHET,
    CRYO,
    LANCER,
    MORTAR,
    ARC,
    SEEKER,
    COUNT
};
constexpr int WeaponCount = (int)WeaponE::COUNT;

/** @brief What a weapon does. */
struct WeaponDef
{
    const char *m_id;       ///< file names: weapon_<id>, shoot_<id>
    const char *m_shot;     ///< the shot's animation in the "shots" sheet
    float       m_cool;     ///< seconds between shots
    float       m_damage;   ///< per hit
    float       m_speed;    ///< px/s
    float       m_range;    ///< px a shot flies
    int         m_ammoMax;  ///< 0 = infinite
    int         m_ammoUse;  ///< per shot
    unsigned    m_colour;   ///< the glow colour 0xRRGGBB
    int         m_price;    ///< first upgrade (the next ones x2, x3)
};

/** @brief The weapon table, indexed by WeaponE. */
const WeaponDef &weapon( WeaponE w );
/** @brief A weapon by its id ("repeater"), COUNT if unknown. */
WeaponE weaponOf( const std::string &id );

/** @brief How an enemy behaves. */
enum class BrainE : int
{
    WALKER,    ///< patrols, turns at walls and edges
    SHOOTER,   ///< patrols slowly, stops and shoots when it sees the hero
    LOBBER,    ///< throws arcs at the hero
    FLIER,     ///< floats on a sine path, drifts towards the hero
    SWOOPER,   ///< hangs, then dives at the hero and returns
    GUNSHIP,   ///< flies and shoots
    TURRET,    ///< fixed, aims and shoots
    BEAMER,    ///< fixed, charges and fires a beam
    FLOATER,   ///< drifts at the hero, explodes on touch
    CHARGER,   ///< walks, revs up and charges when it sees the hero
    HOPPER,    ///< jumps at the hero
    DROPPER,   ///< waits on the ceiling, drops on the hero, climbs back
    SPAWNER,   ///< beams in others
    BLINKER,   ///< teleports near the hero and shoots
    BURROWER,  ///< hides in the ground, bursts out when the hero is near
    HEAVY      ///< slow walker that throws grenades
};

/** @brief How an enemy dies (sound and debris). */
enum class FamilyE : int
{
    ROBOT,
    CREATURE,
    ICE,
    GLOAM
};

/** @brief An enemy kind. */
struct EnemyDef
{
    const char *m_id;      ///< sprite sheet and level legend name
    BrainE      m_brain;
    FamilyE     m_family;
    float       m_hp;
    float       m_speed;   ///< px/s
    int         m_damage;  ///< on touch
    int         m_w, m_h;  ///< box
    int         m_score;
    const char *m_shot;    ///< its shot ("enemy_bolt"), or "" for none
    const char *m_child;   ///< spawners: what it beams in
    bool        m_armour;  ///< blocks shots from the front
};

/** @brief The enemy table entry of a kind (nullptr if unknown). */
const EnemyDef *enemyDef( const std::string &id );
/** @brief A boss (warden, broodmother, colossus, gloam): its table entry and kind 1-4, nullptr if unknown. */
const EnemyDef *bossDef( const std::string &id, int &kind );
/** @brief All enemy kinds. */
const std::vector<EnemyDef> &enemyDefs();

/** @brief A treasure kind and its value. */
struct TreasureDef
{
    const char *m_id;
    int         m_value;
};
const std::vector<TreasureDef> &treasures();

/** @brief What one level's best run was. */
struct LevelBest
{
    bool  m_done = false;
    int   m_score = 0;
    float m_time = 0;         ///< seconds, 0 = none
    int   m_treasure = 0;     ///< percent
    int   m_secrets = 0, m_secretsMax = 0;
    int   m_kills = 0;        ///< percent
    int   m_medals = 0;       ///< MedalE bits won so far
    float m_trial = 0;        ///< best time trial, seconds (0 = none)
};

/** @brief The four medals of a level. */
enum MedalE : int
{
    MEDAL_TIME = 1,       ///< finished within the par time
    MEDAL_TREASURE = 2,   ///< every treasure
    MEDAL_UNHURT = 4,     ///< never hit
    MEDAL_SECRETS = 8     ///< every secret
};

/** @brief The awards (achievements); the order is the save's bit order, so new ones go at the end. */
enum AwardE : int
{
    AW_FIRST_CRYSTAL,
    AW_EPISODE1,
    AW_EPISODE2,
    AW_EPISODE3,
    AW_EPISODE4,
    AW_WARDEN_CLEAN,       ///< a boss without a knockout in its level
    AW_BROOD_CLEAN,
    AW_COLOSSUS_CLEAN,
    AW_GLOAM_CLEAN,
    AW_SECRET1,            ///< secret levels found
    AW_SECRET2,
    AW_SECRET3,
    AW_SECRET4,
    AW_KILLS100,
    AW_KILLS500,
    AW_KILLS1500,
    AW_CRYSTALS250,
    AW_CRYSTALS750,
    AW_TREASURE_LEVEL,     ///< every treasure in a level
    AW_UNHURT_LEVEL,       ///< a level without being hit
    AW_SECRETS_LEVEL,      ///< every secret in a level
    AW_PAR_LEVEL,          ///< a level within par
    AW_MEDALS10,
    AW_MEDALS40,
    AW_MEDALS_ALL,
    AW_ALL_WEAPONS,
    AW_FULL_UPGRADE,       ///< a weapon at step 3
    AW_ALL_UPGRADES,
    AW_ARMOUR3,
    AW_LORE10,
    AW_LORE_ALL,
    AW_RICH,               ///< 10000 credits earned
    AW_FROZEN10,           ///< enemies shattered while frozen
    AW_RICOCHET3,          ///< one disc, three hits
    AW_ELITE25,            ///< elite enemies beaten
    AW_BOSS_RUSH,
    AW_NEW_GAME_PLUS,
    AW_HARD_EPISODE,       ///< an episode on hard
    AW_NO_DEATH_EPISODE,   ///< an episode without a knockout
    AW_EDITOR,             ///< a level of one's own played to its end
    AW_COUNT
};

/** @brief The award's text key ("award.first_crystal"). */
const char *awardKey( AwardE a );

/** @brief What the player carries through the game (one save slot). */
struct Progress
{
    int                             m_difficulty = 1;   ///< 0 easy, 1 normal, 2 hard
    unsigned                        m_weapons = 1;      ///< bit per WeaponE (the blaster always)
    std::array<int, WeaponCount>    m_ammo = {};
    std::array<int, WeaponCount>    m_upgrade = {};     ///< 0-3
    int                             m_armour = 0;       ///< 0-3: +20 health each
    int                             m_credits = 0;
    long                            m_score = 0;
    int                             m_episode = 1;      ///< where the player is
    int                             m_level = 1;
    int                             m_deaths = 0;
    float                           m_playTime = 0;
    std::map<std::string, LevelBest> m_best;            ///< by level id (e1l1)
    int                             m_cycle = 0;        ///< New Game+ round (0: the first run)
    unsigned long long              m_awards = 0;       ///< AwardE bits
    std::map<std::string, int>      m_lore;             ///< logbook pages found (key -> 1)
    std::map<std::string, int>       m_seen;             ///< enemy kinds met (the bestiary: id -> 1)
    long                            m_kills = 0, m_crystalsTotal = 0, m_creditsTotal = 0, m_frozenKills = 0, m_eliteKills = 0;
    float                           m_bossRush = 0;     ///< best boss rush, seconds (0 = none)
    int                             m_episodeDeaths = 0; ///< knockouts in the episode so far
    bool                            m_finished = false; ///< the Gloam has been beaten once (New Game+ open)

    bool award( AwardE a ) const { return ( m_awards >> (int)a ) & 1ull; }

    bool has( WeaponE w ) const { return ( m_weapons >> (int)w ) & 1; }
    /** @brief The most ammo a weapon can hold with its upgrades. */
    int ammoMax( WeaponE w ) const;
    /** @brief The hero's health with the armour. */
    int healthMax() const { return 100 + 20 * m_armour; }
    /** @brief Whether a level may be played (the first of each unlocked episode, or after the one before). */
    bool unlocked( int episode, int level ) const;
};

/** @brief "e<episode>l<level>". */
std::string levelId( int episode, int level );

}   // namespace kepler
