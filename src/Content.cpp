/**
 * @file Content.cpp
 * @brief The weapon, enemy and treasure tables.
 * @author Rene Weller
 */
#include "Content.h"

namespace kepler
{

namespace
{

// id, shot, cooldown, damage, speed, range, ammo max, ammo per shot, glow colour, first upgrade price
const WeaponDef Weapons[WeaponCount] = {
    { "blaster", "bolt", 0.26f, 1.0f, 560, 420, 0, 0, 0x40E0FF, 300 },
    { "repeater", "bolt_rapid", 0.085f, 0.55f, 660, 380, 300, 1, 0xFF9030, 400 },
    { "scatter", "pellet", 0.5f, 0.8f, 520, 200, 60, 1, 0xFFE040, 400 },
    { "ricochet", "disc", 0.34f, 1.3f, 430, 1100, 80, 1, 0x60FF80, 500 },
    { "cryo", "cryo", 0.4f, 0.3f, 380, 300, 60, 1, 0xA0F0FF, 500 },
    { "lancer", "laser", 0.6f, 2.6f, 0, 640, 40, 1, 0xFF4050, 600 },
    { "mortar", "mortar", 0.7f, 3.5f, 380, 0, 30, 1, 0xB060FF, 600 },
    { "arc", "arc", 0.3f, 1.4f, 0, 160, 120, 2, 0x60A0FF, 700 },
    { "seeker", "seeker", 0.65f, 1.3f, 300, 800, 45, 1, 0xFF50D0, 700 },
};

// id, brain (unused for bosses), family, hp, speed, touch damage, box, score, shot, child, armour
const EnemyDef Bosses[] = {
    { "warden", BrainE::HEAVY, FamilyE::ROBOT, 70, 80, 25, 60, 78, 5000, "missile", "hoverdrone", false },
    { "broodmother", BrainE::FLIER, FamilyE::CREATURE, 85, 110, 25, 84, 60, 6000, "acid", "mothling", false },
    { "colossus", BrainE::CHARGER, FamilyE::ICE, 120, 55, 30, 76, 108, 8000, "shard", "", false },
    { "gloam", BrainE::GUNSHIP, FamilyE::GLOAM, 160, 130, 30, 68, 84, 12000, "enemy_orb", "trooper", false },
};

}   // namespace

const EnemyDef *bossDef( const std::string &id, int &kind )
{
    for ( int i = 0; i < 4; ++i )
        if ( id == Bosses[i].m_id )
        {
            kind = i + 1;
            return &Bosses[i];
        }
    return nullptr;
}

const WeaponDef &weapon( WeaponE w )
{
    int i = (int)w;
    return Weapons[i >= 0 && i < WeaponCount ? i : 0];
}

WeaponE weaponOf( const std::string &id )
{
    for ( int i = 0; i < WeaponCount; ++i )
        if ( id == Weapons[i].m_id ) return (WeaponE)i;
    return WeaponE::COUNT;
}

const std::vector<EnemyDef> &enemyDefs()
{
    using B = BrainE;
    using F = FamilyE;
    static const std::vector<EnemyDef> defs = {
        // Episode 1: the Academy ring's machines gone wrong.
        { "sweeper", B::WALKER, F::ROBOT, 2, 55, 12, 26, 20, 100, "", "", false },
        { "sentry", B::SHOOTER, F::ROBOT, 3, 40, 15, 22, 40, 150, "enemy_bolt", "", false },
        { "hoverdrone", B::FLIER, F::ROBOT, 2, 70, 12, 26, 18, 120, "", "", false },
        { "turret", B::TURRET, F::ROBOT, 4, 0, 10, 26, 26, 200, "enemy_bolt", "", false },
        { "sparkmine", B::FLOATER, F::ROBOT, 1, 45, 25, 18, 18, 80, "", "", false },
        { "rammer", B::CHARGER, F::ROBOT, 5, 60, 20, 34, 28, 250, "", "", false },
        { "springbot", B::HOPPER, F::ROBOT, 3, 90, 15, 24, 28, 150, "", "", false },
        { "fabricator", B::SPAWNER, F::ROBOT, 12, 0, 15, 44, 44, 600, "", "hoverdrone", false },
        // Episode 2: Thessa's wildlife.
        { "beetle", B::WALKER, F::CREATURE, 4, 50, 15, 30, 22, 150, "", "", true },
        { "spitter", B::LOBBER, F::CREATURE, 4, 0, 15, 26, 34, 200, "acid", "", false },
        { "mothling", B::FLIER, F::CREATURE, 2, 85, 12, 26, 20, 120, "", "", false },
        { "leaper", B::HOPPER, F::CREATURE, 3, 110, 15, 26, 24, 150, "", "", false },
        { "snapvine", B::DROPPER, F::CREATURE, 3, 0, 20, 24, 30, 180, "", "", false },
        { "sporepod", B::FLOATER, F::CREATURE, 1, 35, 20, 22, 22, 100, "spore", "", false },
        { "stalker", B::CHARGER, F::CREATURE, 5, 80, 20, 36, 30, 250, "", "", false },
        { "hivenest", B::SPAWNER, F::CREATURE, 14, 0, 15, 48, 48, 700, "", "mothling", false },
        // Episode 3: the comet's ice and crystal life, and the mine's machines.
        { "crystalcrab", B::WALKER, F::ICE, 4, 65, 15, 30, 20, 150, "", "", false },
        { "icebat", B::SWOOPER, F::ICE, 2, 170, 15, 26, 20, 150, "", "", false },
        { "shardling", B::HOPPER, F::ICE, 3, 100, 15, 24, 26, 160, "", "", false },
        { "cryoturret", B::TURRET, F::ICE, 5, 0, 12, 26, 26, 220, "shard", "", false },
        { "minerbot", B::SHOOTER, F::ROBOT, 5, 45, 15, 26, 38, 220, "enemy_bolt", "", false },
        { "burrower", B::BURROWER, F::ICE, 4, 70, 20, 30, 24, 200, "", "", false },
        { "frostgolem", B::CHARGER, F::ICE, 10, 50, 25, 40, 46, 400, "", "", false },
        { "wisp", B::FLOATER, F::ICE, 2, 55, 18, 20, 20, 150, "", "", false },
        // Episode 4: the Gloam's army.
        { "trooper", B::SHOOTER, F::GLOAM, 5, 55, 15, 24, 42, 250, "enemy_bolt", "", false },
        { "shieldbot", B::WALKER, F::GLOAM, 6, 45, 18, 30, 36, 300, "", "", true },
        { "jetpacker", B::GUNSHIP, F::GLOAM, 4, 90, 15, 26, 36, 300, "enemy_bolt", "", false },
        { "gloamhound", B::CHARGER, F::GLOAM, 5, 95, 20, 36, 26, 280, "", "", false },
        { "lasereye", B::BEAMER, F::GLOAM, 6, 0, 15, 28, 28, 350, "", "", false },
        { "blinker", B::BLINKER, F::GLOAM, 4, 0, 15, 24, 36, 350, "enemy_orb", "", false },
        { "brute", B::HEAVY, F::GLOAM, 12, 35, 25, 40, 50, 500, "grenade", "", false },
        { "riftgate", B::SPAWNER, F::GLOAM, 18, 0, 15, 48, 64, 900, "", "trooper", false },
    };
    return defs;
}

const EnemyDef *enemyDef( const std::string &id )
{
    for ( const EnemyDef &d : enemyDefs() )
        if ( id == d.m_id ) return &d;
    return nullptr;
}

const std::vector<TreasureDef> &treasures()
{
    static const std::vector<TreasureDef> t = {
        { "gem", 100 }, { "chip", 200 }, { "cube", 300 }, { "idol", 500 }, { "crown", 1000 } };
    return t;
}

int Progress::ammoMax( WeaponE w ) const
{
    int base = weapon( w ).m_ammoMax;
    return m_upgrade[(int)w] >= 2 ? base * 3 / 2 : base;
}

bool Progress::unlocked( int episode, int level ) const
{
    if ( level <= 1 ) return true;
    auto it = m_best.find( levelId( episode, level - 1 ) );
    return it != m_best.end() && it->second.m_done;
}

const char *awardKey( AwardE a )
{
    static const char *keys[AW_COUNT] = {
        "award.first_crystal", "award.episode1", "award.episode2", "award.episode3", "award.episode4",
        "award.warden_clean", "award.brood_clean", "award.colossus_clean", "award.gloam_clean", "award.secret1",
        "award.secret2", "award.secret3", "award.secret4", "award.kills100", "award.kills500", "award.kills1500",
        "award.crystals250", "award.crystals750", "award.treasure_level", "award.unhurt_level", "award.secrets_level",
        "award.par_level", "award.medals10", "award.medals40", "award.medals_all", "award.all_weapons",
        "award.full_upgrade", "award.all_upgrades", "award.armour3", "award.lore10", "award.lore_all", "award.rich",
        "award.frozen10", "award.ricochet3", "award.elite25", "award.boss_rush", "award.new_game_plus",
        "award.hard_episode", "award.no_death_episode", "award.editor" };
    int i = (int)a;
    return i >= 0 && i < AW_COUNT ? keys[i] : "award.?";
}

std::string levelId( int episode, int level )
{
    return "e" + std::to_string( episode ) + "l" + std::to_string( level );
}

}   // namespace kepler
