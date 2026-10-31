/**
 * @file World.cpp
 * @brief One level in play: loading, the cells that change, the hero, pickups, objects, movers and the camera.
 *        Weapons and shots are in WorldShots.cpp, enemies in WorldEnemies.cpp, bosses in WorldBoss.cpp, drawing in
 *        WorldDraw.cpp.
 * @author Rene Weller
 */
#include "World.h"

#include "Assets.h"
#include "Audio.h"
#include "Rumble.h"
#include "Text.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <sstream>

namespace kepler
{

namespace
{

constexpr float T = (float)Tile;

uint32_t hashCell( int x, int y, uint32_t salt = 0 )
{
    uint32_t h = (uint32_t)x * 73856093u ^ (uint32_t)y * 19349663u ^ salt * 83492791u;
    h ^= h >> 13;
    h *= 0x5bd1e995u;
    h ^= h >> 15;
    return h;
}

bool overlaps( float l0, float t0, float r0, float b0, float l1, float t1, float r1, float b1 )
{
    return l0 < r1 && r0 > l1 && t0 < b1 && b0 > t1;
}

/** @brief How far a crusher is down at a moment of its clock (0 up .. 1 down): up slowly, slam down fast, rest. */
float crusherDrop( const Object &o, float at )
{
    float period = o.m_args.size() > 1 ? (float)atof( o.m_args[1].c_str() ) : 3;
    float ph = std::fmod( at, period ) / period;
    return ph < 0.55f ? 0 : ph < 0.62f ? ( ph - 0.55f ) / 0.07f : ph < 0.75f ? 1 : 1 - ( ph - 0.75f ) / 0.25f;
}

}   // namespace

// ------------------------------------------------------------------------------------------------------- loading

bool World::load( const std::string &path, Progress &progress, std::string &error )
{
    if ( !m_level.load( path, error ) ) return false;
    m_progress = &progress;
    const Level &L = m_level;
    m_theme = L.key( "theme", "station" );
    m_bgName = L.key( "bg", m_theme + "_a" );
    m_dark = std::clamp( L.num( "dark", 0.0f ), 0.0f, 0.9f );
    m_tint = std::clamp( (int)L.num( "tint", 0 ), 0, 3 );
    size_t n = (size_t)L.m_w * L.m_h;
    m_broken.assign( n, 0 );
    m_crumbleT.assign( n, 0 );
    m_explored.assign( n, 0 );
    m_deathLog.clear(), m_track.clear();
    m_doorOpen.assign( n, 0 );
    m_secretGroup.assign( n, 0 );
    m_maskTerrain.assign( n, 0 );
    m_maskBack.assign( n, 0 );
    m_variant.assign( n, 0 );
    m_pickups.clear(), m_shots.clear(), m_enemies.clear(), m_particles.clear(), m_effects.clear();
    m_movers.clear(), m_objects.clear(), m_lights.clear(), m_popups.clear();

    // Secret groups: connected '?' cells.
    int groups = 0;
    for ( int y = 0; y < L.m_h; ++y )
        for ( int x = 0; x < L.m_w; ++x )
        {
            if ( !L.at( x, y ).m_secret || m_secretGroup[(size_t)y * L.m_w + x] ) continue;
            ++groups;
            std::vector<int> stack = { y * L.m_w + x };
            m_secretGroup[(size_t)y * L.m_w + x] = groups;
            while ( !stack.empty() )
            {
                int c = stack.back();
                stack.pop_back();
                int cx = c % L.m_w, cy = c / L.m_w;
                const int d[4][2] = { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } };
                for ( auto &dd : d )
                {
                    int nx = cx + dd[0], ny = cy + dd[1];
                    if ( L.inside( nx, ny ) && L.at( nx, ny ).m_secret && !m_secretGroup[(size_t)ny * L.m_w + nx] )
                    {
                        m_secretGroup[(size_t)ny * L.m_w + nx] = groups;
                        stack.push_back( ny * L.m_w + nx );
                    }
                }
            }
        }
    m_secrets = groups;
    m_secretSeen.assign( groups + 1, false );

    // The tiles' neighbour masks (docs/DESIGN.md "Tile sets").
    for ( int y = 0; y < L.m_h; ++y )
        for ( int x = 0; x < L.m_w; ++x )
        {
            m_maskTerrain[(size_t)y * L.m_w + x] = L.terrainMask( x, y );
            m_maskBack[(size_t)y * L.m_w + x] = L.backMask( x, y );
            m_variant[(size_t)y * L.m_w + x] = (uint8_t)( hashCell( x, y ) >> 7 );
        }

    // What the map places.
    m_crystals = L.m_crystals;
    m_treasure = 0;
    m_enemiesTotal = 0;
    m_boss = false;
    m_bossIndex = -1;
    for ( const Spawn &s : L.m_spawns )
    {
        int   si = (int)( &s - L.m_spawns.data() );
        float cx = s.m_x * T + T * 0.5f, cy = s.m_y * T + T * 0.5f;
        auto  pick = [&]( PickE kind, const std::string &anim, int sub = 0 )
        {
            Pickup p;
            p.m_kind = kind;
            p.m_anim = anim;
            p.m_sub = sub;
            p.m_x = cx, p.m_y = cy;
            p.m_t = ( hashCell( s.m_x, s.m_y ) % 100 ) * 0.01f;
            p.m_spawn = si;
            m_pickups.push_back( p );
        };
        const std::string a0 = s.m_args.empty() ? "" : s.m_args[0];
        if ( s.m_kind == "crystal" ) pick( PickE::CRYSTAL, "crystal" );
        else if ( s.m_kind == "treasure" )
        {
            int k = 0;
            if ( !a0.empty() )
            {
                for ( size_t i = 0; i < treasures().size(); ++i )
                    if ( a0 == treasures()[i].m_id ) k = (int)i;
            }
            else
            {
                uint32_t h = hashCell( s.m_x, s.m_y, 7 ) % 100;
                k = h < 45 ? 0 : h < 75 ? 1 : h < 93 ? 2 : 3;
            }
            pick( PickE::TREASURE, treasures()[k].m_id, k );
            ++m_treasure;
        }
        else if ( s.m_kind == "health" ) pick( a0 == "big" ? PickE::HEALTH_BIG : PickE::HEALTH, a0 == "big" ? "health_big" : "health" );
        else if ( s.m_kind == "key" ) pick( a0 == "gold" ? PickE::KEY_GOLD : PickE::KEY_BLUE, a0 == "gold" ? "key_gold" : "key_blue" );
        else if ( s.m_kind == "ammo" ) pick( PickE::AMMO, "ammo" );
        else if ( s.m_kind == "weapon" )
        {
            WeaponE w = weaponOf( a0 );
            if ( w != WeaponE::COUNT ) pick( PickE::WEAPON, std::string( "weapon_" ) + weapon( w ).m_id, (int)w );
        }
        else if ( s.m_kind == "lore" )
        {
            // A page found in an earlier run is not there again.
            if ( !a0.empty() && !progress.m_lore.count( a0 ) )
            {
                pick( PickE::LORE, "lore" );
                m_pickups.back().m_key = a0;
            }
        }
        else if ( s.m_kind == "power" )
        {
            int k = a0 == "boots" ? 1 : a0 == "shield" ? 2 : 0;
            pick( PickE::POWER, k == 1 ? "power_boots" : k == 2 ? "power_shield" : "power_overdrive", k );
        }
        else if ( s.m_kind == "enemy" )
        {
            bool ambush = std::find( s.m_args.begin(), s.m_args.end(), "ambush" ) != s.m_args.end();
            int  i = spawnEnemy( a0, cx, ( s.m_y + 1 ) * T, ambush );
            if ( i >= 0 )
            {
                Enemy &e = m_enemies[i];
                int elite = 0;
                for ( const std::string &w : s.m_args )
                {
                    if ( w == "left" ) e.m_dir = -1;
                    if ( w == "right" ) e.m_dir = 1;
                    if ( w.rfind( "hp=", 0 ) == 0 ) e.m_hp = e.m_hpMax = (float)atof( w.c_str() + 3 );
                    if ( w == "elite" ) elite = 1 + (int)( hashCell( s.m_x, s.m_y, 5 ) % 5 );
                    if ( w.rfind( "elite=", 0 ) == 0 )
                    {
                        static const char *kinds[] = { "armoured", "swift", "splitting", "shielded", "regenerating" };
                        for ( int k = 0; k < 5; ++k )
                            if ( w.substr( 6 ) == kinds[k] ) elite = k + 1;
                    }
                    if ( w == "ceiling" && e.m_def->m_brain == BrainE::WALKER )
                    {
                        // Up to the ceiling above: it walks there upside down.
                        for ( int yy = s.m_y; yy >= 0; --yy )
                            if ( solid( s.m_x, yy ) )
                            {
                                e.m_y = ( yy + 1 ) * T + e.m_def->m_h;
                                break;
                            }
                        e.m_upsideDown = true;
                        e.m_homeY = e.m_y;
                    }
                }
                // On hard and in New Game+ some become elite by themselves.
                int chance = progress.m_cycle > 0 ? 15 : progress.m_difficulty == 2 ? 7 : 0;
                if ( !elite && chance && (int)( hashCell( s.m_x, s.m_y, 9 ) % 100 ) < chance && e.m_def->m_brain != BrainE::SPAWNER )
                    elite = 1 + (int)( hashCell( s.m_x, s.m_y, 5 ) % 5 );
                if ( elite )
                {
                    e.m_elite = elite;
                    if ( elite == 1 ) e.m_hp = e.m_hpMax = e.m_hpMax * 2.5f;
                    else
                        e.m_hp = e.m_hpMax = e.m_hpMax * 1.5f;
                    if ( elite == 2 ) e.m_speedMul = 1.5f;
                    if ( elite == 4 ) e.m_shieldFront = true;
                }
                ++m_enemiesTotal;
            }
        }
        else if ( s.m_kind == "boss" )
        {
            int i = spawnEnemy( a0, cx, ( s.m_y + 1 ) * T, false );
            if ( i >= 0 )
            {
                m_bossIndex = i;
                m_boss = true;
                ++m_enemiesTotal;
            }
        }
        else if ( s.m_kind == "mover" )
        {
            Mover m;
            m.m_x0 = s.m_x * T, m.m_y0 = s.m_y * T;
            m.m_dx = ( s.m_args.size() > 0 ? (float)atof( s.m_args[0].c_str() ) : 0 ) * T;
            m.m_dy = ( s.m_args.size() > 1 ? (float)atof( s.m_args[1].c_str() ) : 0 ) * T;
            m.m_speed = s.m_args.size() > 2 ? (float)atof( s.m_args[2].c_str() ) : 60;
            m.m_wait = s.m_args.size() > 3 ? (float)atof( s.m_args[3].c_str() ) : 0.6f;
            m.m_w = s.m_w;
            m.m_x = m.m_px = m.m_x0;
            m.m_y = m.m_py = m.m_y0;
            m_movers.push_back( m );
        }
        else if ( s.m_kind == "light" )
        {
            Light l;
            l.m_x = cx, l.m_y = cy;
            l.m_r = ( s.m_args.size() > 1 ? (float)atof( s.m_args[1].c_str() ) : 5 ) * T;
            static const std::pair<const char *, Color> named[] = {
                { "warm", { 255, 196, 120, 255 } }, { "cold", { 140, 200, 255, 255 } }, { "cyan", { 90, 230, 255, 255 } },
                { "green", { 120, 255, 150, 255 } }, { "red", { 255, 90, 80, 255 } }, { "orange", { 255, 150, 60, 255 } },
                { "violet", { 190, 120, 255, 255 } }, { "magenta", { 255, 90, 220, 255 } }, { "white", { 240, 240, 255, 255 } },
                { "yellow", { 255, 230, 110, 255 } }, { "blue", { 90, 140, 255, 255 } } };
            l.m_c = { 230, 230, 240, 255 };
            for ( auto &[name, c] : named )
                if ( a0 == name ) l.m_c = c;
            l.m_flicker = ( hashCell( s.m_x, s.m_y ) % 4 ) == 0 ? 0.15f : 0;
            m_lights.push_back( l );
        }
        else if ( s.m_kind != "start" )
        {
            Object o;
            o.m_kind = s.m_kind;
            o.m_cx = s.m_x, o.m_cy = s.m_y;
            o.m_x = cx, o.m_y = ( s.m_y + 1 ) * T;
            o.m_args = s.m_args;
            o.m_ch = s.m_ch;
            o.m_spawn = si;
            o.m_t = ( hashCell( s.m_x, s.m_y ) % 100 ) * 0.01f;
            // Lasers and crushers may set their phase (laser h|v on off PHASE, crusher tiles period PHASE).
            if ( s.m_kind == "laser" && s.m_args.size() > 3 ) o.m_t = (float)atof( s.m_args[3].c_str() );
            if ( s.m_kind == "crusher" && s.m_args.size() > 2 ) o.m_t = (float)atof( s.m_args[2].c_str() );
            m_objects.push_back( o );
        }
    }
    // Spawners add to the list while it is walked: room enough that it rarely moves.
    m_enemies.reserve( m_enemies.size() + 256 );
    for ( Object &o : m_objects )
        if ( o.m_kind == "teleport" && !o.m_args.empty() && !o.m_args[0].empty() )
            for ( size_t k = 0; k < m_objects.size(); ++k )
                if ( m_objects[k].m_ch == o.m_args[0][0] && &m_objects[k] != &o ) o.m_target = (int)k;

    // Riders stand on the platform below their cell from the start (it carries them even while they sleep).
    for ( Enemy &e : m_enemies )
        if ( e.m_def->m_brain == BrainE::RIDER )
        {
            e.m_mover = -1;
            for ( size_t k = 0; k < m_movers.size(); ++k )
            {
                const Mover &m = m_movers[k];
                if ( std::fabs( m.m_y0 - e.m_y ) < T * 0.75f && e.m_x > m.m_x0 - 4 && e.m_x < m.m_x0 + m.m_w * T + 4 )
                    e.m_mover = (int)k;
            }
        }

    // The hero on the floor below the start.
    const Spawn *start = L.first( "start" );
    m_spawnX = start->m_x * T + T * 0.5f;
    m_spawnY = ( start->m_y + 1 ) * T;
    for ( int y = start->m_y + 1; y < L.m_h; ++y )
        if ( solid( start->m_x, y ) || oneway( start->m_x, y ) )
        {
            m_spawnY = y * T;
            break;
        }
    m_hp = (float)progress.healthMax();
    m_weapon = WeaponE::BLASTER;
    m_keys[0] = m_keys[1] = false;
    m_boots = false;
    m_overdrive = m_shield = 0;
    m_dead = false;
    m_exitT = -1;
    m_finished = false;
    m_time = 0;
    m_crystalsTaken = m_treasureTaken = m_secretsFound = m_kills = m_deaths = m_score = m_credits = 0;
    m_groups = 0;
    m_exitOpen = false;
    m_bossAwake = false;
    m_dangerT = m_calmT = 0;
    m_fightMusic = false;
    respawn();
    m_appearT = 0.6f;
    m_loadedPickups = (int)m_pickups.size(), m_loadedEnemies = (int)m_enemies.size();
    placeDecos();
    if ( m_crystals == 0 && !m_boss ) openExitIfDone();
    // The pictures the level needs, loaded now (behind the beam-in) rather than the moment they first come on screen:
    // that was a hitch of 100 ms and more in the middle of play. Without a window (the autopilot's test) nothing.
    if ( IsWindowReady() )
    {
        for ( const char *s : { "hero", "items", "objects", "shots", "fx" } ) assets().sheet( s );
        // The HUD's pictures (the low health bar only shows when it is low) and both fonts.
        assets().sheetIn( "ui", "hud" );
        for ( const char *t : { "ui/bar_frame.png", "ui/bar_fill.png", "ui/bar_fill_low.png", "ui/weapon_slot.png",
                                "ui/weapon_slot_selected.png" } )
            assets().texture( t );
        assets().font( false ), assets().font( true, true );
        assets().tiles( m_theme );
        assets().background( m_bgName );
        for ( const Enemy &e : m_enemies )
        {
            assets().sheet( e.m_def->m_id );
            if ( e.m_def->m_child && *e.m_def->m_child ) assets().sheet( e.m_def->m_child );
        }
        // What the bosses call in.
        if ( m_boss )
            for ( const char *s : { "hoverdrone", "mothling", "trooper" } ) assets().sheet( s );
    }
    // Two takes of each piece: the levels alternate them.
    std::string cue = L.key( "music", "" );
    if ( !cue.empty() ) music( cue + "_t" + std::to_string( 1 + ( L.m_id.empty() ? 0 : ( L.m_id.back() - '0' ) % 2 ) ) );
    return true;
}

int World::spawnEnemy( const std::string &type, float x, float y, bool ambush )
{
    const EnemyDef *d = enemyDef( type );
    int             boss = 0;
    if ( !d ) d = bossDef( type, boss );
    if ( !d ) return -1;
    Enemy e;
    e.m_def = d;
    e.m_boss = boss;
    e.m_hp = e.m_hpMax = d->m_hp * ( m_progress && m_progress->m_difficulty == 2 ? 1.3f : 1.0f ) *
                         ( m_progress ? 1.0f + 0.5f * m_progress->m_cycle : 1.0f );
    e.m_shieldFront = d->m_armour;
    e.m_x = x;
    e.m_y = y;
    e.m_hidden = ambush || d->m_brain == BrainE::BURROWER || d->m_brain == BrainE::EEL;
    e.m_t = ( hashCell( (int)x, (int)y ) % 100 ) * 0.01f;
    e.m_shootT = 1.0f + ( hashCell( (int)x, (int)y, 3 ) % 100 ) * 0.01f;
    // An eel lurks unseen anyway: ready at once, or a hero falling past the pool is gone before it leaps.
    if ( d->m_brain == BrainE::EEL ) e.m_shootT = 0.3f;
    int cx = (int)std::floor( x / T ), cy = (int)std::floor( ( y - 1 ) / T );
    switch ( d->m_brain )
    {
    case BrainE::FLIER:
    case BrainE::GUNSHIP:
    case BrainE::FLOATER:
        // Fliers hang in the middle of their cell.
        e.m_y = cy * T + T * 0.5f + d->m_h * 0.5f;
        break;
    case BrainE::EEL:
    case BrainE::RIDER:
        // Eels lurk at the bottom of their (liquid) cell; riders stand on the platform in the cell below.
        e.m_y = ( cy + 1 ) * T;
        break;
    case BrainE::SWOOPER:
    case BrainE::DROPPER:
        // They hang from the ceiling above.
        for ( int yy = cy; yy >= 0; --yy )
            if ( solid( cx, yy ) )
            {
                e.m_y = ( yy + 1 ) * T + d->m_h;
                break;
            }
        e.m_ceiling = true;
        break;
    case BrainE::TURRET:
    case BrainE::BEAMER:
        if ( !solid( cx, cy + 1 ) && solid( cx, cy - 1 ) )
        {
            e.m_ceiling = true;
            e.m_y = cy * T + d->m_h;
        }
        break;
    default:
        // Walkers stand on the floor below their cell.
        for ( int yy = cy + 1; yy < m_level.m_h; ++yy )
            if ( solid( cx, yy ) || oneway( cx, yy ) )
            {
                e.m_y = yy * T;
                break;
            }
        break;
    }
    e.m_homeX = e.m_x, e.m_homeY = e.m_y;
    m_enemies.push_back( e );
    return (int)m_enemies.size() - 1;
}

void World::placeDecos()
{
    m_decoList.clear();
    const TileSet &ts = assets().tiles( m_theme );
    if ( ts.m_decos.empty() ) return;
    const Level      &L = m_level;
    std::vector<char> used( (size_t)L.m_w * L.m_h, 0 );
    for ( const Spawn &s : L.m_spawns )
        if ( L.inside( s.m_x, s.m_y ) ) used[(size_t)s.m_y * L.m_w + s.m_x] = 1;
    auto freeCell = [&]( int x, int y )
    {
        return L.inside( x, y ) && L.at( x, y ).m_kind == CellE::INTERIOR && !used[(size_t)y * L.m_w + x];
    };
    float total[4] = { 0, 0, 0, 0 };
    for ( const Deco &d : ts.m_decos ) total[d.m_place] += d.m_weight;
    for ( int y = 0; y < L.m_h; ++y )
        for ( int x = 0; x < L.m_w; ++x )
        {
            if ( !freeCell( x, y ) ) continue;
            uint32_t h = hashCell( x, y, 11 );
            int      place;
            if ( solid( x, y + 1 ) && h % 100 < 22 ) place = 1;
            else if ( solid( x, y - 1 ) && h % 100 < 16 )
                place = ( h >> 8 ) % 3 == 0 && total[3] > 0 ? 3 : 2;
            else if ( h % 1000 < 45 )
                place = 0;
            else
                continue;
            if ( total[place] <= 0 ) continue;
            float pickAt = ( ( h >> 12 ) % 10000 ) / 10000.0f * total[place];
            int   chosen = -1;
            for ( size_t i = 0; i < ts.m_decos.size(); ++i )
            {
                const Deco &d = ts.m_decos[i];
                if ( d.m_place != place ) continue;
                if ( pickAt < d.m_weight )
                {
                    chosen = (int)i;
                    break;
                }
                pickAt -= d.m_weight;
            }
            if ( chosen < 0 ) continue;
            const Deco &d = ts.m_decos[chosen];
            int         cw = (int)std::ceil( d.m_src.width / T ), ch = (int)std::ceil( d.m_src.height / T );
            // Floor decos rise from this cell, ceiling decos hang down from it, wall decos sit in it.
            int x0 = x, y0 = place == 1 ? y - ch + 1 : y;
            bool fits = true;
            for ( int yy = y0; yy < y0 + ch && fits; ++yy )
                for ( int xx = x0; xx < x0 + cw && fits; ++xx )
                    if ( !freeCell( xx, yy ) ) fits = false;
            if ( place == 1 )
                for ( int xx = x0; xx < x0 + cw && fits; ++xx )
                    if ( !solid( xx, y + 1 ) ) fits = false;
            if ( ( place == 2 || place == 3 ) )
                for ( int xx = x0; xx < x0 + cw && fits; ++xx )
                    if ( !solid( xx, y - 1 ) ) fits = false;
            if ( !fits ) continue;
            for ( int yy = y0; yy < y0 + ch; ++yy )
                for ( int xx = x0; xx < x0 + cw; ++xx ) used[(size_t)yy * L.m_w + xx] = 1;
            DecoPlace p;
            p.m_index = chosen;
            p.m_x = x0 * T + ( cw * T - d.m_src.width ) * 0.5f;
            p.m_y = place == 1 ? ( y + 1 ) * T - d.m_src.height : place == 0 ? y0 * T + ( ch * T - d.m_src.height ) * 0.5f : y * T;
            m_decoList.push_back( p );
            if ( d.m_glow )
            {
                Light l;
                l.m_x = p.m_x + d.m_src.width * 0.5f, l.m_y = p.m_y + d.m_src.height * 0.5f;
                l.m_r = 40 + std::max( d.m_src.width, d.m_src.height );
                l.m_c = ColorBrightness( d.m_light, -0.35f );
                l.m_flicker = 0;
                m_lights.push_back( l );
            }
        }
}

// --------------------------------------------------------------------------------------------------- collisions

bool World::solid( int cx, int cy ) const
{
    if ( cy >= m_level.m_h ) return false;
    if ( cx < 0 || cx >= m_level.m_w || cy < 0 ) return true;
    size_t      i = (size_t)cy * m_level.m_w + cx;
    const Cell &c = m_level.m_cells[i];
    switch ( c.m_kind )
    {
    case CellE::TERRAIN_A:
    case CellE::TERRAIN_B:
    case CellE::CONVEYOR: return true;
    case CellE::BREAKABLE: return m_broken[i] < 2;
    case CellE::CRUMBLE: return m_broken[i] < 2;
    case CellE::DOOR_BLUE:
    case CellE::DOOR_GOLD: return !m_doorOpen[i];
    case CellE::TOGGLE:
    {
        bool on = ( m_groups >> ( c.m_aux & 7 ) ) & 1;
        return on == ( ( c.m_aux & 8 ) != 0 );
    }
    default: return false;
    }
}

bool World::oneway( int cx, int cy ) const
{
    return m_level.inside( cx, cy ) && m_level.at( cx, cy ).m_kind == CellE::PLATFORM;
}

bool World::icy( int cx, int cy ) const
{
    return m_theme == "ice" && m_level.inside( cx, cy ) && m_level.at( cx, cy ).m_kind == CellE::TERRAIN_B;
}

bool World::platformTop( float x0, float x1, float before, float after, float &top ) const
{
    bool found = false;
    auto consider = [&]( float l, float r, float t )
    {
        if ( x1 > l && x0 < r && before <= t + 0.5f && after >= t && ( !found || t < top ) )
        {
            top = t;
            found = true;
        }
    };
    for ( const Mover &m : m_movers ) consider( m.m_x, m.m_x + m.m_w * T, m.m_y );
    for ( const Enemy &e : m_enemies )
        if ( e.m_alive && e.m_frozen > 0 ) consider( e.left() - 2, e.right() + 2, e.top() );
    return found;
}

bool World::hazard( const Object &o, float at, float box[4], int *beam ) const
{
    float l = o.m_cx * T, t = o.m_cy * T;
    if ( o.m_kind == "laser" )
    {
        float on = o.m_args.size() > 1 ? (float)atof( o.m_args[1].c_str() ) : 1.5f;
        float off = o.m_args.size() > 2 ? (float)atof( o.m_args[2].c_str() ) : 1.5f;
        if ( std::fmod( at, on + off ) >= on ) return false;
        bool vertical = !o.m_args.empty() && o.m_args[0] == "v";
        // The beam runs from the emitter to the next solid cell, away from the wall it sits on.
        int dx = 0, dy = 0;
        if ( vertical )
            dy = solid( o.m_cx, o.m_cy - 1 ) ? 1 : -1;
        else
            dx = solid( o.m_cx - 1, o.m_cy ) ? 1 : -1;
        int cx = o.m_cx, cy = o.m_cy, n = 0;
        while ( n < 40 && !solid( cx + dx, cy + dy ) ) cx += dx, cy += dy, ++n;
        box[0] = std::min( o.m_cx, cx ) * T, box[2] = ( std::max( o.m_cx, cx ) + 1 ) * T;
        box[1] = std::min( o.m_cy, cy ) * T, box[3] = ( std::max( o.m_cy, cy ) + 1 ) * T;
        if ( vertical )
            box[0] += 12, box[2] -= 12;
        else
            box[1] += 12, box[3] -= 12;
        if ( beam ) *beam = n;
        return true;
    }
    if ( o.m_kind == "crusher" )
    {
        float reach = ( o.m_args.size() > 0 ? (float)atof( o.m_args[0].c_str() ) : 3 ) * T, d = crusherDrop( o, at );
        if ( d <= 0.3f ) return false;
        box[0] = l + 2, box[1] = t, box[2] = l + T - 2, box[3] = t + T + reach * d;
        return true;
    }
    return false;
}

// ----------------------------------------------------------------------------------------- seen, quick save

void World::noteSeen()
{
    // The cells on the screen are explored (the pause map), the enemy kinds on it met (the bestiary).
    int c0 = std::max( 0, (int)std::floor( m_camX / T ) ),
        c1 = std::min( m_level.m_w - 1, (int)std::floor( ( m_camX + m_vw ) / T ) );
    int r0 = std::max( 0, (int)std::floor( m_camY / T ) ),
        r1 = std::min( m_level.m_h - 1, (int)std::floor( ( m_camY + m_vh ) / T ) );
    for ( int y = r0; y <= r1; ++y )
        for ( int x = c0; x <= c1; ++x ) m_explored[(size_t)y * m_level.m_w + x] = 1;
    for ( const Enemy &e : m_enemies )
        if ( e.m_alive && !e.m_hidden && e.m_x > m_camX && e.m_x < m_camX + m_vw && e.m_y > m_camY &&
             e.top() < m_camY + m_vh )
            m_progress->m_seen.emplace( e.m_def->m_id, 1 );
}

std::string World::snapshot() const
{
    // One line per thing. The hero stays where he stands if that is firm ground, else he goes back to the checkpoint.
    std::ostringstream o;
    bool               firm = m_hero.m_ground && !m_dead && m_hurtT <= 0 && m_exitT < 0 && m_appearT <= 0;
    o << "time " << m_time << "\n";
    o << "stats " << m_deaths << " " << m_score << " " << m_credits << " " << m_crystalsTaken << " " << m_treasureTaken
      << " " << m_secretsFound << " " << m_kills << " " << m_hits << "\n";
    o << "hero " << ( firm ? m_hero.m_x : m_spawnX ) << " " << ( firm ? m_hero.m_y : m_spawnY ) << " "
      << std::max( 1.0f, m_hp ) << " " << (int)m_weapon << " " << m_face << "\n";
    o << "spawn " << m_spawnX << " " << m_spawnY << "\n";
    o << "keys " << m_keys[0] << " " << m_keys[1] << " " << m_boots << "\n";
    o << "groups " << m_groups << "\nexit " << m_exitOpen << "\n";
    o << "taken";
    for ( int i = 0; i < m_loadedPickups; ++i )
        if ( m_pickups[i].m_taken ) o << " " << i;
    o << "\nbeaten";
    for ( int i = 0; i < m_loadedEnemies; ++i )
        if ( !m_enemies[i].m_alive ) o << " " << i;
    o << "\nhurt";
    for ( int i = 0; i < m_loadedEnemies; ++i )
        if ( m_enemies[i].m_alive && m_enemies[i].m_hp < m_enemies[i].m_hpMax )
            o << " " << i << ":" << m_enemies[i].m_hp;
    o << "\nbroken";
    for ( size_t i = 0; i < m_broken.size(); ++i )
        if ( m_broken[i] == 2 && m_level.m_cells[i].m_kind == CellE::BREAKABLE ) o << " " << i;
    o << "\ndoors";
    for ( size_t i = 0; i < m_doorOpen.size(); ++i )
        if ( m_doorOpen[i] ) o << " " << i;
    o << "\nsecrets";
    for ( size_t g = 0; g < m_secretSeen.size(); ++g )
        if ( m_secretSeen[g] ) o << " " << g;
    o << "\ncheckpoint";
    for ( size_t k = 0; k < m_objects.size(); ++k )
        if ( m_objects[k].m_kind == "checkpoint" && m_objects[k].m_on ) o << " " << k;
    // The explored cells as runs: start, length.
    o << "\nexplored";
    for ( size_t i = 0; i < m_explored.size(); )
    {
        if ( !m_explored[i] )
        {
            ++i;
            continue;
        }
        size_t j = i;
        while ( j < m_explored.size() && m_explored[j] ) ++j;
        o << " " << i << ":" << j - i;
        i = j;
    }
    o << "\n";
    return o.str();
}

bool World::restore( const std::string &text )
{
    std::istringstream in( text );
    std::string        line;
    size_t             cells = m_broken.size();
    while ( std::getline( in, line ) )
    {
        std::istringstream l( line );
        std::string        key;
        l >> key;
        if ( key == "time" )
            l >> m_time;
        else if ( key == "stats" )
            l >> m_deaths >> m_score >> m_credits >> m_crystalsTaken >> m_treasureTaken >> m_secretsFound >> m_kills >>
                m_hits;
        else if ( key == "hero" )
        {
            int w = 0;
            l >> m_hero.m_x >> m_hero.m_y >> m_hp >> w >> m_face;
            if ( w >= 0 && w < WeaponCount && m_progress->has( (WeaponE)w ) ) m_weapon = (WeaponE)w;
            m_hero.m_vx = m_hero.m_vy = 0;
            m_hero.m_ground = true;
        }
        else if ( key == "spawn" )
            l >> m_spawnX >> m_spawnY;
        else if ( key == "keys" )
            l >> m_keys[0] >> m_keys[1] >> m_boots;
        else if ( key == "groups" )
            l >> m_groups;
        else if ( key == "exit" )
            l >> m_exitOpen;
        else if ( key == "taken" )
            for ( int i; l >> i; )
            {
                if ( i >= 0 && i < m_loadedPickups ) m_pickups[i].m_taken = true;
            }
        else if ( key == "beaten" )
            for ( int i; l >> i; )
            {
                if ( i >= 0 && i < m_loadedEnemies ) m_enemies[i].m_alive = false;
            }
        else if ( key == "hurt" )
            for ( std::string w; l >> w; )
            {
                int i = atoi( w.c_str() );
                if ( i >= 0 && i < m_loadedEnemies && w.find( ':' ) != std::string::npos )
                    m_enemies[i].m_hp = (float)atof( w.c_str() + w.find( ':' ) + 1 );
            }
        else if ( key == "broken" )
            for ( size_t i; l >> i; )
            {
                if ( i < cells ) m_broken[i] = 2;
            }
        else if ( key == "doors" )
            for ( size_t i; l >> i; )
            {
                if ( i < cells ) m_doorOpen[i] = 1;
            }
        else if ( key == "secrets" )
            for ( size_t g; l >> g; )
            {
                if ( g < m_secretSeen.size() ) m_secretSeen[g] = true;
            }
        else if ( key == "checkpoint" )
            for ( size_t k; l >> k; )
            {
                if ( k < m_objects.size() ) m_objects[k].m_on = true;
            }
        else if ( key == "explored" )
            for ( std::string w; l >> w; )
            {
                size_t a = (size_t)atoll( w.c_str() ),
                       n = w.find( ':' ) != std::string::npos ? (size_t)atoll( w.c_str() + w.find( ':' ) + 1 ) : 0;
                for ( size_t i = a; i < a + n && i < cells; ++i ) m_explored[i] = 1;
            }
    }
    m_hp = std::clamp( m_hp, 1.0f, (float)m_progress->healthMax() );
    m_appearT = 0.6f;
    m_hurtT = 1.2f;
    stepCamera( 0, true );
    return true;
}

bool World::lineOfSight( float x0, float y0, float x1, float y1 ) const
{
    float d = std::hypot( x1 - x0, y1 - y0 );
    int   n = std::max( 1, (int)( d / 12 ) );
    for ( int i = 1; i < n; ++i )
    {
        float f = (float)i / n;
        if ( solid( (int)std::floor( ( x0 + ( x1 - x0 ) * f ) / T ), (int)std::floor( ( y0 + ( y1 - y0 ) * f ) / T ) ) ) return false;
    }
    return true;
}

// ---------------------------------------------------------------------------------------------------- the frame

void World::update( float dt, const Controls &c )
{
    dt = std::min( dt, 0.1f );
    m_acc += dt;
    Controls once = c;
    while ( m_acc >= phys::Step - 1e-6f )
    {
        step( phys::Step, once );
        // A press counts in the first step only.
        once.m_jumpPressed = once.m_firePressed = once.m_prevWeapon = once.m_nextWeapon = once.m_alt = false;
        m_acc -= phys::Step;
    }
}

void World::step( float dt, const Controls &c )
{
    m_clock += dt;
    if ( m_hitStop > 0 )
    {
        m_hitStop -= dt;
        return;
    }
    if ( !m_dead && m_exitT < 0 ) m_time += dt;
    stepMovers( dt );
    stepHero( dt, c );
    stepShots( dt );
    stepEnemies( dt );
    stepPickups( dt );
    stepObjects( dt );
    for ( Particle &p : m_particles )
    {
        p.m_vy += p.m_grav * dt;
        p.m_x += p.m_vx * dt;
        p.m_y += p.m_vy * dt;
        p.m_life -= dt;
    }
    m_particles.erase( std::remove_if( m_particles.begin(), m_particles.end(), []( const Particle &p ) { return p.m_life <= 0; } ),
                       m_particles.end() );
    for ( Effect &e : m_effects )
    {
        e.m_t += dt;
        const Sheet &s = assets().sheet( e.m_sheet );
        if ( s.done( e.m_anim, e.m_t ) || e.m_t > 3 ) e.m_dead = true;
    }
    m_effects.erase( std::remove_if( m_effects.begin(), m_effects.end(), []( const Effect &e ) { return e.m_dead; } ), m_effects.end() );
    for ( Popup &p : m_popups ) p.m_t += dt, p.m_y -= 24 * dt;
    for ( Beam &b : m_beams ) b.m_t += dt;
    m_beams.erase( std::remove_if( m_beams.begin(), m_beams.end(), []( const Beam &b ) { return b.m_t > b.m_life; } ), m_beams.end() );
    m_popups.erase( std::remove_if( m_popups.begin(), m_popups.end(), []( const Popup &p ) { return p.m_t > 1.1f; } ), m_popups.end() );
    if ( m_bannerT > 0 ) m_bannerT -= dt;
    if ( m_signT > 0 ) m_signT -= dt;
    if ( m_shake > 0 ) m_shake = std::max( 0.0f, m_shake - dt * 3 );
    if ( m_toggleFlash > 0 ) m_toggleFlash -= dt;
    if ( m_teleCool > 0 ) m_teleCool -= dt;
    if ( m_switchCool > 0 ) m_switchCool -= dt;
    // Crumbling blocks fall and come back.
    for ( size_t i = 0; i < m_crumbleT.size(); ++i )
    {
        if ( m_crumbleT[i] <= 0 ) continue;
        m_crumbleT[i] -= dt;
        if ( m_broken[i] == 1 && m_crumbleT[i] <= 0 )
        {
            m_broken[i] = 2;
            m_crumbleT[i] = 4.0f;
            float x = ( i % m_level.m_w ) * T + T * 0.5f, y = ( i / m_level.m_w ) * T + T * 0.5f;
            burst( x, y, 10, { 150, 130, 110, 255 }, 80, false, 600 );
            sfx( "crumble", 0.6f );
        }
        else if ( m_broken[i] == 2 && m_crumbleT[i] <= 0 )
        {
            // Back, unless the hero stands inside it or below it nearby (a gap he fell through stays open while he
            // climbs out).
            int   cx = (int)( i % m_level.m_w ), cy = (int)( i / m_level.m_w );
            float l = cx * T, t = cy * T;
            bool  below = m_hero.right() > l - 64 && m_hero.left() < l + T + 64 && m_hero.top() > t && m_hero.m_y < t + 10 * T;
            if ( below || overlaps( m_hero.left(), m_hero.top(), m_hero.right(), m_hero.m_y, l, t, l + T, t + T ) ) m_crumbleT[i] = 0.5f;
            else
                m_broken[i] = 0;
        }
    }
    stepCamera( dt );
    // What the App keeps: the cells and enemy kinds seen, the hero's way.
    if ( ++m_noteN >= 8 ) m_noteN = 0, noteSeen();
    if ( m_record && m_track.size() <= (size_t)( m_time * 30 ) )
    {
        const Sheet &hs = assets().sheet( "hero" );
        m_track.push_back(
            { m_hero.m_x, m_hero.m_y, (int16_t)( hs.m_standIn ? 0 : hs.frame( m_anim, m_animT ) ), (int8_t)m_face } );
    }
    // The music gets denser while enemies are close or the hero is hit, and calms down a while after the last one.
    bool danger = !m_dead && !m_bossAwake && m_hurtT > 0.9f;
    for ( size_t i = 0; i < m_enemies.size() && !danger && !m_dead && !m_bossAwake; ++i )
    {
        const Enemy &e = m_enemies[i];
        danger = e.m_alive && !e.m_hidden && !e.m_boss && e.m_frozen <= 0 && std::abs( e.m_x - m_hero.m_x ) < 300 &&
                 std::abs( e.cy() - m_hero.m_y ) < 200;
    }
    m_dangerT = danger ? m_dangerT + dt : 0;
    m_calmT = danger ? 0 : m_calmT + dt;
    if ( !m_fightMusic && m_dangerT > 0.4f ) m_fightMusic = true, musicFight( true );
    else if ( m_fightMusic && ( m_calmT > 6 || m_bossAwake ) ) m_fightMusic = false, musicFight( false );
    // The pad's motors follow the screen's shake (and a jolt when the hero is hit).
    if ( m_rumbleOn )
        rumble::set( std::min( 1.0f, m_shake * 1.4f ), std::min( 1.0f, m_shake + ( m_hurtT > 0.95f && !m_dead ? 0.6f : 0.0f ) ) );
}

// --------------------------------------------------------------------------------------------------------- hero

void World::stepHero( float dt, const Controls &c )
{
    if ( m_appearT > 0 ) m_appearT -= dt;
    if ( m_hurtT > 0 ) m_hurtT -= dt;
    if ( m_overdrive > 0 ) m_overdrive -= dt;
    if ( m_shield > 0 ) m_shield -= dt;
    if ( m_shootPose > 0 ) m_shootPose -= dt;
    m_animT += dt;
    auto setAnim = [&]( const std::string &a )
    {
        if ( a == m_anim ) return;
        // The shooting run keeps the run's phase (same frames, see the hero sheet).
        bool keep = ( a == "run" && m_anim == "run_shoot" ) || ( a == "run_shoot" && m_anim == "run" );
        m_anim = a;
        if ( !keep ) m_animT = 0;
    };
    if ( m_dead )
    {
        m_deadT += dt;
        setAnim( "die" );
        m_hero.m_vx *= 0.9f;
        HeroInput none;
        kepler::stepHero( m_hero, none, *this, dt );
        if ( m_deadT > 1.8f ) respawn();
        return;
    }
    if ( m_exitT >= 0 )
    {
        m_exitT += dt;
        setAnim( "teleport" );
        if ( m_exitT > 1.1f ) m_finished = true;
        return;
    }

    HeroInput in;
    in.m_dir = ( c.m_right ? 1 : 0 ) - ( c.m_left ? 1 : 0 );
    if ( m_appearT > 0.2f ) in.m_dir = 0;
    in.m_jump = c.m_jump;
    in.m_jumpPressed = c.m_jumpPressed;
    in.m_down = c.m_down;
    m_hero.m_jumpSpeed = m_boots ? phys::BootsJump : phys::Jump;
    m_hero.m_gravity = phys::Gravity * m_level.num( "gravity", 1.0f ) * m_gravityMul;
    // Conveyors push what stands on them.
    m_hero.m_pushX = 0;
    if ( m_hero.m_ground )
    {
        int row = (int)std::floor( ( m_hero.m_y + 1 ) / T );
        for ( int cx : { (int)std::floor( m_hero.left() / T ), (int)std::floor( ( m_hero.right() - 1 ) / T ) } )
            if ( m_level.inside( cx, row ) && m_level.at( cx, row ).m_kind == CellE::CONVEYOR )
                m_hero.m_pushX = m_level.at( cx, row ).m_aux ? 90.0f : -90.0f;
    }
    float vyBefore = m_hero.m_vy;
    kepler::stepHero( m_hero, in, *this, dt );
    if ( in.m_dir ) m_face = in.m_dir;
    if ( m_hero.m_jumped ) sfx( "jump", 0.55f, 1.0f + GetRandomValue( -4, 4 ) * 0.01f );
    if ( m_hero.m_landed && vyBefore > 250 )
    {
        sfx( "land", std::min( 1.0f, vyBefore / 900 ) * 0.7f );
        effect( "dust", m_hero.m_x, m_hero.m_y );
        if ( vyBefore > 700 ) m_shake = std::max( m_shake, 0.25f );
    }
    // Footsteps.
    if ( m_hero.m_ground && std::fabs( m_hero.m_vx ) > 60 )
    {
        m_stepT -= dt;
        if ( m_stepT <= 0 )
        {
            m_stepT = 0.28f;
            sfx( "step", 0.25f, 0.9f + GetRandomValue( 0, 20 ) * 0.01f );
        }
    }

    // Weapons.
    if ( c.m_prevWeapon || c.m_nextWeapon )
    {
        int dir = c.m_nextWeapon ? 1 : -1, w = (int)m_weapon;
        for ( int k = 0; k < WeaponCount; ++k )
        {
            w = ( w + dir + WeaponCount ) % WeaponCount;
            if ( m_progress->has( (WeaponE)w ) ) break;
        }
        if ( w != (int)m_weapon )
        {
            m_weapon = (WeaponE)w;
            m_charge = 0;
            sfx( "weapon_switch", 0.6f );
            popup( tr( std::string( "weapon." ) + weapon( m_weapon ).m_id ), m_hero.m_x, m_hero.top() - 6, { 220, 240, 255, 255 } );
        }
    }
    m_aimUp = c.m_up;
    if ( m_cool > 0 ) m_cool -= dt * ( m_overdrive > 0 ? 2.0f : 1.0f );
    if ( m_weapon == WeaponE::BLASTER )
    {
        // The blaster fires on the press; held, it charges a big piercing shot let go on release.
        if ( c.m_firePressed && m_cool <= 0 ) fire();
        if ( c.m_fire )
        {
            float before = m_charge;
            m_charge += dt;
            if ( before < 0.25f && m_charge >= 0.25f ) sfx( "charge", 0.5f );
            float full = m_progress->m_upgrade[0] >= 3 ? 0.6f : 0.8f;
            if ( before < full + 0.25f && m_charge >= full + 0.25f ) sfx( "charge_full", 0.7f );
            // Held at full charge it hums on (the loop is 0.5 s long and seamless).
            if ( m_charge >= full + 0.25f && std::fmod( before - full - 0.25f, 0.5f ) > std::fmod( m_charge - full - 0.25f, 0.5f ) )
                sfx( "charge_loop", 0.3f );
        }
        else
        {
            float full = m_progress->m_upgrade[0] >= 3 ? 0.6f : 0.8f;
            if ( m_charge >= full + 0.25f )
            {
                m_charge = 99;
                fire();
            }
            m_charge = 0;
        }
    }
    else if ( c.m_fire && m_cool <= 0 )
        fire();
    if ( c.m_alt && m_cool <= 0 ) fireAlt();

    // Hazards.
    bool liquid = false;
    if ( m_level.hurts( m_hero.left() + 2, m_hero.top() + 2, m_hero.right() - 2, m_hero.m_y, liquid ) )
    {
        if ( liquid )
        {
            // A pool costs health, not a life: each time Kip comes down into it, it throws him out again (about four
            // tiles, steerable), knocked back the way he came. Lava and plasma burn more than acid, resin and brine.
            if ( m_hero.m_vy >= 0 )
            {
                effect( "splash", m_hero.m_x, std::floor( ( m_hero.m_y - 8 ) / T ) * T + 8 );
                burst( m_hero.m_x, m_hero.m_y - 8, 16, { 160, 255, 120, 255 }, 160 );
                sfx( "splash" );
                bool  hot = m_theme == "foundry" || m_theme == "station" || m_theme == "hull" || m_theme == "citadel";
                float ahead = m_hero.m_vx != 0 ? ( m_hero.m_vx > 0 ? 1.0f : -1.0f ) : (float)m_face;
                hurtHero( hot ? 30.0f : 20.0f, m_hero.m_x + ahead * 10, "liquid" );
                if ( m_dead ) return;
                m_hero.m_vy = -std::sqrt( 2 * m_hero.m_gravity * phys::PoolLift );
                m_hero.m_noCut = true;
                m_hero.m_ground = false;
            }
        }
        else if ( m_hurtT <= 0 && m_shield <= 0 )
        {
            hurtHero( 25, m_hero.m_x - m_face * 10, "spikes" );
            m_hero.m_vy = -460;
            m_hero.m_ground = false;
        }
    }
    if ( m_hero.top() > m_level.m_h * T + 64 )
    {
        killHero( "fall" );
        return;
    }

    // Crumbling blocks under the feet start to go.
    if ( m_hero.m_ground )
    {
        int row = (int)std::floor( ( m_hero.m_y + 1 ) / T );
        for ( int cx = (int)std::floor( m_hero.left() / T ); cx <= (int)std::floor( ( m_hero.right() - 1 ) / T ); ++cx )
            if ( m_level.inside( cx, row ) && m_level.at( cx, row ).m_kind == CellE::CRUMBLE )
            {
                size_t i = (size_t)row * m_level.m_w + cx;
                if ( m_broken[i] == 0 )
                {
                    m_broken[i] = 1;
                    m_crumbleT[i] = 0.5f;
                    sfx( "crumble", 0.35f, 1.3f );
                }
            }
    }

    // Doors open to their key at a touch.
    for ( int k = 0; k < 2; ++k )
    {
        if ( !m_keys[k] ) continue;
        CellE door = k ? CellE::DOOR_GOLD : CellE::DOOR_BLUE;
        int   c0 = (int)std::floor( ( m_hero.left() - 3 ) / T ), c1 = (int)std::floor( ( m_hero.right() + 3 ) / T );
        int   r0 = (int)std::floor( m_hero.top() / T ), r1 = (int)std::floor( ( m_hero.m_y - 1 ) / T );
        for ( int cy = r0; cy <= r1; ++cy )
            for ( int cx = c0; cx <= c1; ++cx )
            {
                if ( !m_level.inside( cx, cy ) || m_level.at( cx, cy ).m_kind != door ) continue;
                size_t i = (size_t)cy * m_level.m_w + cx;
                if ( m_doorOpen[i] ) continue;
                // The whole door (connected cells of that colour) opens.
                std::vector<int> stack = { (int)i };
                m_doorOpen[i] = 1;
                while ( !stack.empty() )
                {
                    int c2 = stack.back();
                    stack.pop_back();
                    int x2 = c2 % m_level.m_w, y2 = c2 / m_level.m_w;
                    const int d[4][2] = { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } };
                    for ( auto &dd : d )
                    {
                        int nx = x2 + dd[0], ny = y2 + dd[1];
                        if ( m_level.inside( nx, ny ) && m_level.at( nx, ny ).m_kind == door &&
                             !m_doorOpen[(size_t)ny * m_level.m_w + nx] )
                        {
                            m_doorOpen[(size_t)ny * m_level.m_w + nx] = 1;
                            stack.push_back( ny * m_level.m_w + nx );
                        }
                    }
                }
                sfx( "door" );
                burst( cx * T + 16, cy * T + 16, 10, k ? Color{ 255, 210, 80, 255 } : Color{ 90, 150, 255, 255 }, 90 );
            }
    }

    // Secrets.
    {
        int c0 = (int)std::floor( m_hero.left() / T ), c1 = (int)std::floor( ( m_hero.right() - 1 ) / T );
        int r0 = (int)std::floor( m_hero.top() / T ), r1 = (int)std::floor( ( m_hero.m_y - 1 ) / T );
        for ( int cy = r0; cy <= r1; ++cy )
            for ( int cx = c0; cx <= c1; ++cx )
            {
                if ( !m_level.inside( cx, cy ) ) continue;
                int g = m_secretGroup[(size_t)cy * m_level.m_w + cx];
                if ( g && !m_secretSeen[g] )
                {
                    m_secretSeen[g] = true;
                    ++m_secretsFound;
                    m_score += 500;
                    sfx( "secret" );
                    banner( tr( "msg.secret" ), 2.5f );
                    popup( "+500", m_hero.m_x, m_hero.top() - 10, { 255, 160, 255, 255 } );
                }
            }
    }

    // Touching enemies.
    if ( m_hurtT <= 0 && m_shield <= 0 )
        for ( Enemy &e : m_enemies )
        {
            if ( !e.m_alive || e.m_hidden || e.m_frozen > 0 ) continue;
            if ( overlaps( m_hero.left() + 3, m_hero.top() + 4, m_hero.right() - 3, m_hero.m_y - 2, e.left(), e.top(), e.right(), e.m_y ) )
            {
                hurtHero( (float)e.m_def->m_damage, e.m_x, e.m_def->m_id );
                if ( e.m_def->m_brain == BrainE::FLOATER && !e.m_boss )
                {
                    e.m_hp = 0;
                    killEnemy( (int)( &e - m_enemies.data() ) );
                }
                break;
            }
        }
    if ( m_dead ) return;

    // Assist mode: the ammo never runs out.
    if ( m_assistAmmo )
        for ( int w = 1; w < WeaponCount; ++w )
            if ( m_progress->has( (WeaponE)w ) ) m_progress->m_ammo[w] = m_progress->ammoMax( (WeaponE)w );
    // The animation.
    bool shooting = m_shootPose > 0 || ( m_weapon != WeaponE::BLASTER && c.m_fire );
    if ( m_appearT > 0 ) setAnim( "appear" );
    else if ( m_hurtT > 0.8f )
        setAnim( "hurt" );
    else if ( !m_hero.m_ground )
    {
        if ( shooting && m_aimUp ) setAnim( "jump_shoot_up" );
        else if ( m_hero.m_vy < -80 )
            setAnim( shooting ? "jump_shoot" : "jump" );
        else if ( m_hero.m_vy < 80 && !shooting )
            setAnim( "apex" );
        else
            setAnim( shooting ? "fall_shoot" : "fall" );
    }
    else if ( std::fabs( m_hero.m_vx ) > 20 && in.m_dir )
    {
        if ( in.m_dir * m_hero.m_vx < 0 && std::fabs( m_hero.m_vx ) > 120 ) setAnim( "skid" );
        else
            setAnim( shooting && !m_aimUp ? "run_shoot" : "run" );
    }
    else if ( m_hero.m_hitWall && in.m_dir )
        setAnim( "push" );
    else if ( shooting )
        setAnim( m_aimUp ? "shoot_up" : "shoot" );
    else if ( m_aimUp )
        setAnim( "look_up" );
    else if ( m_hero.m_landed || ( m_anim == "land" && m_animT < 0.15f ) )
        setAnim( "land" );
    else
        setAnim( "idle" );
}

void World::hurtHero( float amount, float fromX, const std::string &cause )
{
    if ( m_dead || m_hurtT > 0 || m_shield > 0 || m_exitT >= 0 ) return;
    static const float scale[3] = { 0.6f, 1.0f, 1.5f };
    if ( m_assistInvulnerable ) return;
    m_hp -= m_oneHit
                ? m_hp
                : amount * scale[std::clamp( m_progress->m_difficulty, 0, 2 )] * ( 1.0f + 0.25f * m_progress->m_cycle );
    ++m_hits;
    m_hurtT = 1.1f;
    m_hero.m_vx = ( m_hero.m_x < fromX ? -1 : 1 ) * 200.0f;
    m_hero.m_vy = std::min( m_hero.m_vy, -260.0f );
    m_hero.m_ground = false;
    m_shake = std::max( m_shake, 0.35f );
    m_hitStop = 0.04f;
    sfx( "hurt" );
    burst( m_hero.m_x, m_hero.m_y - 24, 8, { 255, 220, 160, 255 }, 140 );
    if ( m_hp <= 0 ) killHero( cause );
}

void World::killHero( const std::string &cause )
{
    if ( m_dead ) return;
    m_deathLog.push_back( { m_hero.m_x, m_hero.m_y, cause } );
    m_hp = 0;
    m_dead = true;
    m_deadT = 0;
    ++m_deaths;
    ++m_progress->m_deaths;
    m_hero.m_vy = -300;
    m_shake = 0.6f;
    sfx( "die" );
    burst( m_hero.m_x, m_hero.m_y - 24, 24, { 255, 180, 80, 255 }, 200 );
}

void World::respawn()
{
    m_hero = HeroBody();
    m_hero.m_x = m_spawnX;
    m_hero.m_y = m_spawnY;
    m_hero.m_ground = true;
    m_hp = (float)m_progress->healthMax();
    m_dead = false;
    m_hurtT = 1.2f;
    m_overdrive = m_shield = 0;
    m_charge = 0;
    m_appearT = 0.5f;
    m_anim = "appear";
    m_animT = 0;
    m_face = 1;
    // The ammo never runs dry for good: what is below a quarter comes back to a quarter.
    for ( int w = 1; w < WeaponCount; ++w )
        if ( m_progress->has( (WeaponE)w ) )
            m_progress->m_ammo[w] = std::max( m_progress->m_ammo[w], m_progress->ammoMax( (WeaponE)w ) / 4 );
    stepCamera( 0, true );
    sfx( "beam_in", 0.7f );
}

// ------------------------------------------------------------------------------------------------------ pickups

void World::take( Pickup &p )
{
    float  x = p.m_x, y = p.m_y;
    switch ( p.m_kind )
    {
    case PickE::CRYSTAL:
        ++m_crystalsTaken;
        grant( AW_FIRST_CRYSTAL );
        m_score += 50;
        sfx( m_crystalsTaken == m_crystals ? "crystal_last" : "crystal", 0.8f, 1.0f + 0.02f * ( m_crystalsTaken % 8 ) );
        popup( std::to_string( m_crystalsTaken ) + "/" + std::to_string( m_crystals ), x, y - 16, { 140, 240, 255, 255 } );
        openExitIfDone();
        break;
    case PickE::TREASURE:
    {
        int v = treasures()[p.m_sub].m_value;
        ++m_treasureTaken;
        m_score += v;
        m_credits += v;
        sfx( "treasure", 0.7f, 1.0f + 0.1f * p.m_sub );
        popup( "+" + std::to_string( v ), x, y - 16, { 255, 220, 90, 255 } );
        break;
    }
    case PickE::HEALTH:
    case PickE::HEALTH_BIG:
        m_hp = std::min( (float)m_progress->healthMax(), m_hp + ( p.m_kind == PickE::HEALTH ? 20.0f : 60.0f ) );
        sfx( "health", 0.8f );
        popup( p.m_kind == PickE::HEALTH ? "+20" : "+60", x, y - 16, { 120, 255, 140, 255 } );
        break;
    case PickE::KEY_BLUE:
    case PickE::KEY_GOLD:
    {
        int k = p.m_kind == PickE::KEY_GOLD;
        m_keys[k] = true;
        sfx( "key" );
        banner( tr( k ? "msg.key_gold" : "msg.key_blue" ), 2.5f );
        break;
    }
    case PickE::AMMO:
        for ( int w = 1; w < WeaponCount; ++w )
            if ( m_progress->has( (WeaponE)w ) )
            {
                int mx = m_progress->ammoMax( (WeaponE)w );
                m_progress->m_ammo[w] = std::min( mx, m_progress->m_ammo[w] + std::max( 1, mx / 4 ) );
            }
        m_score += 25;
        sfx( "ammo", 0.8f );
        popup( tr( "msg.ammo" ), x, y - 16, { 255, 200, 120, 255 } );
        break;
    case PickE::WEAPON:
    {
        WeaponE w = (WeaponE)p.m_sub;
        bool    fresh = !m_progress->has( w );
        m_progress->m_weapons |= 1u << p.m_sub;
        m_progress->m_ammo[p.m_sub] = std::max( m_progress->m_ammo[p.m_sub], m_progress->ammoMax( w ) );
        m_weapon = w;
        m_score += 250;
        sfx( "power" );
        banner( ( fresh ? tr( "msg.new_weapon" ) : tr( "msg.weapon_ammo" ) ) + " " + tr( std::string( "weapon." ) + weapon( w ).m_id ), 3 );
        break;
    }
    case PickE::LORE:
        m_progress->m_lore[p.m_key] = 1;
        m_score += 300;
        sfx( "secret", 0.7f, 1.2f );
        banner( tr( "msg.lore" ) + " " + tr( "lore." + p.m_key + ".title" ), 3 );
        if ( m_progress->m_lore.size() >= 10 ) grant( AW_LORE10 );
        if ( m_progress->m_lore.size() >= 40 ) grant( AW_LORE_ALL );
        break;
    case PickE::POWER:
        if ( p.m_sub == 0 ) m_overdrive = 15;
        if ( p.m_sub == 1 ) m_boots = true;
        if ( p.m_sub == 2 ) m_shield = 12;
        m_score += 100;
        sfx( "power" );
        banner( tr( p.m_sub == 0 ? "msg.overdrive" : p.m_sub == 1 ? "msg.boots" : "msg.shield" ), 2.5f );
        break;
    }
    p.m_taken = true;
    effect( "pickup", x, y );
    burst( x, y, 6, p.m_kind == PickE::CRYSTAL ? Color{ 140, 240, 255, 255 } : Color{ 255, 230, 140, 255 }, 70, true, 0 );
}

void World::stepPickups( float dt )
{
    for ( Pickup &p : m_pickups )
    {
        if ( p.m_taken ) continue;
        p.m_t += dt;
        if ( p.m_loose )
        {
            p.m_life -= dt;
            if ( p.m_life <= 0 )
            {
                p.m_taken = true;
                continue;
            }
            p.m_vy = std::min( 600.0f, p.m_vy + 1200 * dt );
            float vx = 0, x = p.m_x, y = p.m_y + 8;
            bool  ground = false, wall = false;
            moveBox( *this, x, y, 12, 12, vx, p.m_vy, dt, true, ground, wall );
            p.m_y = y - 8;
        }
        if ( m_dead || m_exitT >= 0 ) continue;
        if ( ( p.m_kind == PickE::HEALTH || p.m_kind == PickE::HEALTH_BIG ) && m_hp >= m_progress->healthMax() ) continue;
        // The whole cell counts, as for the checker (generous pickups feel right in this genre).
        if ( overlaps( m_hero.left(), m_hero.top(), m_hero.right(), m_hero.m_y, p.m_x - 16, p.m_y - 16, p.m_x + 16, p.m_y + 16 ) )
            take( p );
    }
}

void World::openExitIfDone()
{
    if ( m_exitOpen ) return;
    if ( m_crystalsTaken < m_crystals ) return;
    if ( m_boss && m_bossIndex >= 0 && m_enemies[m_bossIndex].m_alive ) return;
    m_exitOpen = true;
    sfx( "exit_open" );
    banner( tr( m_crystals ? "msg.exit_open" : "msg.exit_open_boss" ), 3 );
    for ( Object &o : m_objects )
        if ( o.m_kind == "exit" ) o.m_t = 0;
}

// ------------------------------------------------------------------------------------------------------ objects

void World::flipGroup( int group )
{
    m_groups ^= 1u << ( group & 7 );
    m_toggleFlash = 0.4f;
    for ( Object &o : m_objects )
        if ( o.m_kind == "switch" && !o.m_args.empty() && !o.m_args[0].empty() && ( ( o.m_args[0][0] - 'A' ) & 7 ) == group )
            o.m_on = ( m_groups >> group ) & 1;
    // A block that appears around the hero puts him at the nearest free spot: beside it, or on top of it.
    auto fits = [&]( float x, float y )
    {
        for ( int cy = (int)std::floor( ( y - phys::HeroH ) / T ); cy <= (int)std::floor( ( y - 1 ) / T ); ++cy )
            for ( int cx = (int)std::floor( ( x - phys::HeroW * 0.5f ) / T ); cx <= (int)std::floor( ( x + phys::HeroW * 0.5f - 1 ) / T ); ++cx )
                if ( solid( cx, cy ) ) return false;
        return true;
    };
    if ( !fits( m_hero.m_x, m_hero.m_y ) )
    {
        const float tries[][2] = { { -T, 0 }, { T, 0 }, { 0, -T }, { -2 * T, 0 }, { 2 * T, 0 }, { 0, -2 * T }, { 0, -3 * T } };
        for ( auto &d : tries )
        {
            float x = std::floor( ( m_hero.m_x + d[0] ) / T ) * T + T * 0.5f, y = d[1] ? std::floor( ( m_hero.m_y + d[1] ) / T ) * T + T : m_hero.m_y;
            if ( fits( x, y ) )
            {
                m_hero.m_x = x, m_hero.m_y = y;
                break;
            }
        }
    }
    sfx( "switch" );
}

void World::stepObjects( float dt )
{
    bool heroFree = !m_dead && m_exitT < 0 && m_appearT <= 0;
    float hl = m_hero.left(), ht = m_hero.top(), hr = m_hero.right(), hb = m_hero.m_y;
    m_sign.clear();
    for ( size_t i = 0; i < m_objects.size(); ++i )
    {
        Object &o = m_objects[i];
        o.m_t += dt;
        float l = o.m_cx * T, t = o.m_cy * T;
        bool  touch = heroFree && overlaps( hl, ht, hr, hb, l, t, l + T, t + T );
        if ( o.m_kind == "warp" )
        {
            if ( heroFree && !o.m_args.empty() && overlaps( hl, ht, hr, hb, l - 8, t - 32, l + T + 8, t + T ) )
            {
                m_warp = o.m_args[0];
                m_exitT = 0;
                m_hero.m_vx = m_hero.m_vy = 0;
                m_hero.m_x = o.m_x;
                sfx( "secret" );
                sfx( "exit_enter" );
                effect( "beam_in", o.m_x, o.m_y - 40 );
                banner( tr( "msg.warp" ), 2 );
            }
        }
        else if ( o.m_kind == "exit" )
        {
            if ( m_exitOpen && heroFree && overlaps( hl, ht, hr, hb, l - 8, t - 32, l + T + 8, t + T ) )
            {
                m_exitT = 0;
                m_hero.m_vx = m_hero.m_vy = 0;
                m_hero.m_x = o.m_x;
                sfx( "exit_enter" );
                effect( "beam_in", o.m_x, o.m_y - 40 );
            }
        }
        else if ( o.m_kind == "checkpoint" )
        {
            if ( touch && !o.m_on )
            {
                for ( Object &k : m_objects )
                    if ( k.m_kind == "checkpoint" ) k.m_on = false;
                o.m_on = true;
                o.m_t = 0;
                m_spawnX = o.m_x;
                m_spawnY = o.m_y;
                sfx( "checkpoint" );
                banner( tr( "msg.checkpoint" ), 2 );
                burst( o.m_x, o.m_y - 60, 14, { 120, 255, 200, 255 }, 120 );
            }
        }
        else if ( o.m_kind == "teleport" )
        {
            if ( (int)i == m_teleLock )
            {
                if ( !overlaps( hl, ht, hr, hb, l, t, l + T, t + T ) ) m_teleLock = -1;
                continue;
            }
            if ( touch && m_teleCool <= 0 && o.m_target >= 0 )
            {
                const Object &to = m_objects[o.m_target];
                m_teleLock = o.m_target;
                effect( "beam_in", m_hero.m_x, m_hero.m_y - 24 );
                m_hero.m_x = to.m_x;
                m_hero.m_y = to.m_y;
                m_hero.m_vx = m_hero.m_vy = 0;
                m_teleCool = 0.8f;
                m_appearT = 0.3f;
                sfx( "teleport" );
                effect( "beam_in", m_hero.m_x, m_hero.m_y - 24 );
                stepCamera( 0, true );
            }
        }
        else if ( o.m_kind == "switch" )
        {
            // A lever flips when touched anew, not again while the hero stays at it.
            if ( touch && !o.m_held && m_switchCool <= 0 && !o.m_args.empty() && !o.m_args[0].empty() )
            {
                flipGroup( ( o.m_args[0][0] - 'A' ) & 7 );
                m_switchCool = 0.5f;
            }
            o.m_held = touch;
        }
        else if ( o.m_kind == "spring" )
        {
            // The whole cell, as for the checker.
            if ( heroFree && m_hero.m_vy >= 0 && m_hero.m_y >= t + 8 && overlaps( hl, ht, hr, hb, l, t, l + T, t + T ) )
            {
                m_hero.m_vy = -phys::SpringJump;
                m_hero.m_noCut = true;
                m_hero.m_ground = false;
                o.m_on = true;
                o.m_t = 0;
                sfx( "spring" );
            }
            if ( o.m_on && o.m_t > 0.3f ) o.m_on = false;
        }
        else if ( o.m_kind == "sign" )
        {
            if ( heroFree && overlaps( hl, ht, hr, hb, l - 16, t - 32, l + T + 16, t + T ) && !o.m_args.empty() )
            {
                // A text key, or (in levels of one's own) the words themselves.
                m_sign = o.m_args[0];
                for ( size_t k = 1; k < o.m_args.size(); ++k ) m_sign += " " + o.m_args[k];
            }
        }
        else if ( o.m_kind == "laser" )
        {
            float on = o.m_args.size() > 1 ? (float)atof( o.m_args[1].c_str() ) : 1.5f;
            float off = o.m_args.size() > 2 ? (float)atof( o.m_args[2].c_str() ) : 1.5f;
            bool  was = o.m_on;
            o.m_on = std::fmod( o.m_t, on + off ) < on;
            if ( o.m_on && !was && std::fabs( o.m_x - m_hero.m_x ) < 400 ) sfx( "laser_fence", 0.4f );
            float box[4];
            if ( !o.m_on || !hazard( o, o.m_t, box, &o.m_target ) || !heroFree ) continue;
            if ( overlaps( hl, ht, hr, hb, box[0], box[1], box[2], box[3] ) )
                hurtHero( 30, m_hero.m_x - m_face, "laser" );
        }
        else if ( o.m_kind == "crusher" )
        {
            float d = crusherDrop( o, o.m_t ), was = o.m_target / 1000.0f;
            o.m_target = (int)( d * 1000 );
            if ( d >= 1 && was < 1 && std::fabs( o.m_x - m_hero.m_x ) < 360 )
            {
                sfx( "crusher", 0.7f );
                m_shake = std::max( m_shake, 0.2f );
            }
            float box[4];
            if ( heroFree && hazard( o, o.m_t, box ) && overlaps( hl, ht, hr, hb, box[0], box[1], box[2], box[3] ) )
                hurtHero( 40, o.m_x, "crusher" );
        }
    }
    if ( !m_sign.empty() ) m_signT = 0.2f;
}

void advanceMover( Mover &m, float dt )
{
    m.m_px = m.m_x, m.m_py = m.m_y;
    float len = std::hypot( m.m_dx, m.m_dy );
    if ( len < 1 ) return;
    if ( m.m_hold > 0 )
        m.m_hold -= dt;
    else
    {
        float before = m.m_s;
        m.m_s += m.m_speed * dt / len;
        if ( before < 1 && m.m_s >= 1 ) m.m_s = 1, m.m_hold = m.m_wait;
        if ( m.m_s >= 2 ) m.m_s = 0, m.m_hold = m.m_wait;
    }
    float f = m.m_s <= 1 ? m.m_s : 2 - m.m_s;
    f = f * f * ( 3 - 2 * f ) * 0.35f + f * 0.65f;
    m.m_x = m.m_x0 + m.m_dx * f;
    m.m_y = m.m_y0 + m.m_dy * f;
}

void World::stepMovers( float dt )
{
    for ( Mover &m : m_movers )
    {
        advanceMover( m, dt );
        // Carry the hero when he stands on it.
        if ( m_hero.m_ground && m_hero.right() > m.m_px && m_hero.left() < m.m_px + m.m_w * T && std::fabs( m_hero.m_y - m.m_py ) < 1.0f )
        {
            float dx = m.m_x - m.m_px, vx = dx / dt, vy = 0;
            float x = m_hero.m_x, y = m_hero.m_y;
            bool  g = false, w = false;
            moveBox( *this, x, y, phys::HeroW, phys::HeroH, vx, vy, dt, false, g, w );
            m_hero.m_x = x;
            m_hero.m_y = m.m_y;
        }
    }
}

// ------------------------------------------------------------------------------------------------------- camera

void World::stepCamera( float dt, bool snap )
{
    float want = m_face * 56.0f;
    m_lookAhead += ( want - m_lookAhead ) * std::min( 1.0f, dt * 2.5f );
    if ( snap ) m_lookAhead = want;
    float tx = m_hero.m_x + m_lookAhead - m_vw * 0.5f;
    float ty = m_hero.m_y - 24 - m_vh * 0.55f;
    if ( snap )
    {
        m_camX = tx, m_camY = ty;
    }
    else
    {
        m_camX += ( tx - m_camX ) * std::min( 1.0f, dt * 6.0f );
        float rate = m_hero.m_ground ? 5.0f : 2.5f;
        m_camY += ( ty - m_camY ) * std::min( 1.0f, dt * rate );
        // Never let the hero leave the middle band.
        float sy = m_hero.m_y - m_camY;
        if ( sy > m_vh * 0.8f ) m_camY = m_hero.m_y - m_vh * 0.8f;
        if ( sy < m_vh * 0.3f ) m_camY = m_hero.m_y - m_vh * 0.3f;
    }
    float maxX = m_level.m_w * T - m_vw, maxY = m_level.m_h * T - m_vh;
    m_camX = maxX < 0 ? maxX * 0.5f : std::clamp( m_camX, 0.0f, maxX );
    m_camY = maxY < 0 ? maxY * 0.5f : std::clamp( m_camY, 0.0f, maxY );
    m_camYSmooth = snap ? m_camY : m_camYSmooth + ( m_camY - m_camYSmooth ) * std::min( 1.0f, dt * 2.0f );
}

void World::lookAt( float x, float y )
{
    m_camX = x - m_vw * 0.5f;
    m_camY = y - m_vh * 0.5f;
    float maxX = m_level.m_w * T - m_vw, maxY = m_level.m_h * T - m_vh;
    m_camX = maxX < 0 ? maxX * 0.5f : std::clamp( m_camX, 0.0f, maxX );
    m_camY = maxY < 0 ? maxY * 0.5f : std::clamp( m_camY, 0.0f, maxY );
}

void World::place( float x, float y )
{
    m_hero.m_x = x;
    m_hero.m_y = y;
    m_spawnX = x, m_spawnY = y;
    stepCamera( 0, true );
}

// ------------------------------------------------------------------------------------------------------ helpers

void World::burst( float x, float y, int n, Color c, float speed, bool glow, float grav )
{
    for ( int i = 0; i < n; ++i )
    {
        float    a = GetRandomValue( 0, 628 ) * 0.01f, s = speed * ( 0.3f + GetRandomValue( 0, 70 ) * 0.01f );
        Particle p;
        p.m_x = x, p.m_y = y;
        p.m_vx = std::cos( a ) * s;
        p.m_vy = std::sin( a ) * s - speed * 0.3f;
        p.m_max = p.m_life = 0.35f + GetRandomValue( 0, 40 ) * 0.01f;
        p.m_c = c;
        p.m_size = GetRandomValue( 0, 3 ) == 0 ? 2 : 1;
        p.m_glow = glow;
        p.m_grav = grav;
        m_particles.push_back( p );
    }
}

void World::effect( const std::string &anim, float x, float y, bool flip, float angle )
{
    Effect e;
    e.m_anim = anim;
    e.m_x = x, e.m_y = y;
    e.m_flip = flip;
    e.m_angle = angle;
    m_effects.push_back( e );
}

void World::popup( const std::string &text, float x, float y, Color c )
{
    m_popups.push_back( { text, x, y, 0, c } );
}

void World::grant( int award )
{
    if ( award < 0 || award >= AW_COUNT || m_progress->award( (AwardE)award ) ) return;
    m_progress->m_awards |= 1ull << award;
    m_awardQueue.push_back( award );
    sfx( "extra", 0.8f );
}

void World::banner( const std::string &text, float seconds )
{
    m_banner = text;
    m_bannerT = seconds;
}

}   // namespace kepler
