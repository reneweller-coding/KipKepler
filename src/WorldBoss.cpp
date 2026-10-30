/**
 * @file WorldBoss.cpp
 * @brief The four bosses: the WARDEN (security mech), the BROODMOTHER (hive queen), the COLOSSUS (crystal giant)
 *        and THE GLOAM (the syndicate's core in a war frame). Each wakes when the hero comes near and fights in
 *        phases by its health.
 * @author Rene Weller
 */
#include "Assets.h"
#include "Audio.h"
#include "Text.h"
#include "World.h"

#include <algorithm>
#include <cmath>

namespace kepler
{

namespace
{

constexpr float T = (float)Tile;

}   // namespace

void World::stepBoss( Enemy &e, int index, float dt )
{
    const EnemyDef &d = *e.m_def;
    float           hx = heroCx(), hy = heroCy();
    float           dx = hx - e.m_x, dy = hy - e.cy();
    float           dist = std::hypot( dx, dy );
    bool            heroUp = !m_dead && m_exitT < 0;
    float           w = (float)d.m_w, h = (float)d.m_h;
    float           frac = e.m_hp / e.m_hpMax;
    int             phase = frac > 0.66f ? 0 : frac > 0.33f ? 1 : 2;
    // The shot timer runs down (99 marks "done in this attack" and stays).
    if ( e.m_shootT > 0 && e.m_shootT < 50 ) e.m_shootT -= dt;

    if ( !m_bossAwake )
    {
        e.m_anim = "idle";
        if ( heroUp && dist < 380 )
        {
            m_bossAwake = true;
            banner( tr( std::string( "boss." ) + d.m_id ), 3 );
            sfx( "boss_roar" );
            m_shake = 0.6f;
            music( m_level.key( "bossmusic", "boss" ) );
            e.m_state = 0, e.m_stateT = -1.0f;
        }
        else
        {
            if ( e.m_boss != 2 && e.m_boss != 4 )
            {
                float vx = 0;
                bool  wall = false;
                e.m_vy = std::min( 900.0f, e.m_vy + 1500 * dt );
                moveBox( *this, e.m_x, e.m_y, w, h, vx, e.m_vy, dt, true, e.m_ground, wall );
            }
            return;
        }
    }
    if ( phase != e.m_phase )
    {
        e.m_phase = phase;
        sfx( "boss_roar", 0.8f, 1.0f + phase * 0.1f );
        m_shake = std::max( m_shake, 0.5f );
    }
    e.m_stateT += dt;
    if ( e.m_frozen > 0 ) e.m_frozen = 0;
    auto face = [&]() { e.m_dir = dx < 0 ? -1 : 1; };
    auto gravityWalk = [&]( float speed )
    {
        e.m_vx += ( e.m_dir * speed - e.m_vx ) * std::min( 1.0f, dt * 6 );
        e.m_vy = std::min( 900.0f, e.m_vy + 1500 * dt );
        bool wall = false, was = e.m_ground;
        moveBox( *this, e.m_x, e.m_y, w, h, e.m_vx, e.m_vy, dt, true, e.m_ground, wall );
        if ( wall ) e.m_dir = -e.m_dir;
        return !was && e.m_ground;
    };
    auto minions = [&]()
    {
        int n = 0;
        for ( const Enemy &o : m_enemies )
            if ( o.m_alive && !o.m_boss && o.m_parent == index ) ++n;
        return n;
    };
    auto summon = [&]( const char *type, float x, float y )
    {
        int c = spawnEnemy( type, x, y, false );
        if ( c < 0 ) return;
        m_enemies[c].m_parent = index;
        m_enemies[c].m_state = -1;
        ++m_enemiesTotal;
        effect( "beam_in", m_enemies[c].m_x, m_enemies[c].cy() );
        sfx( "beam_in", 0.6f );
    };
    // Shockwaves along the floor: low orbs that only a jump clears.
    auto shockwave = [&]( float x, float floorY )
    {
        for ( int s : { -1, 1 } )
        {
            enemyShoot( e, "enemy_orb", x + s * w * 0.5f, floorY - 10, s * 270.0f, 0 );
            m_shots.back().m_damage = 20;
            m_shots.back().m_range = 700;
        }
    };

    switch ( e.m_boss )
    {
    case 1:   // WARDEN: walks at the hero, missiles, jump-stomps with shockwaves, calls drones.
    {
        Enemy &me = e;
        if ( me.m_state == 0 )
        {
            me.m_anim = "move";
            face();
            gravityWalk( d.m_speed * ( 1 + 0.25f * phase ) );
            if ( me.m_stateT > 1.8f - 0.3f * phase )
            {
                int pick = GetRandomValue( 0, phase >= 1 ? 2 : 1 );
                if ( pick == 2 && minions() >= 2 ) pick = 0;
                me.m_state = 1 + pick, me.m_stateT = 0;
            }
        }
        else if ( me.m_state == 1 )
        {
            // Missiles.
            me.m_anim = "attack";
            gravityWalk( 0 );
            if ( me.m_stateT > 0.5f && me.m_shootT <= 0 )
            {
                int n = 2 + phase;
                const Sheet &sh = assets().sheet( d.m_id );
                for ( int k = 0; k < n; ++k )
                {
                    float   a = ( -90.0f + ( k - ( n - 1 ) * 0.5f ) * 35.0f ) * DEG2RAD;
                    Vector2 mz = sh.point( k % 2 ? "muzzle2" : "muzzle", { 0, -66 } );
                    enemyShoot( m_enemies[index], "missile", me.m_x + mz.x * me.m_dir, me.m_y + mz.y, std::cos( a ) * 220, std::sin( a ) * 220 );
                }
                me.m_shootT = 99;
            }
            if ( me.m_stateT > 1.4f ) me.m_state = 0, me.m_stateT = 0, me.m_shootT = 0;
        }
        else if ( me.m_state == 2 )
        {
            // Jump and stomp.
            if ( me.m_stateT < dt * 1.5f )
            {
                face();
                me.m_vy = -680;
                me.m_vx = std::clamp( dx * 1.1f, -260.0f, 260.0f );
                me.m_ground = false;
                sfx( "jump", 0.8f, 0.5f );
            }
            me.m_anim = "jump";
            me.m_vy = std::min( 900.0f, me.m_vy + 1500 * dt );
            bool wall = false, was = me.m_ground;
            moveBox( *this, me.m_x, me.m_y, w, h, me.m_vx, me.m_vy, dt, true, me.m_ground, wall );
            if ( !was && me.m_ground && me.m_stateT > 0.2f )
            {
                me.m_vx = 0;
                m_shake = 0.6f;
                sfx( "crusher" );
                burst( me.m_x, me.m_y, 20, { 200, 200, 210, 255 }, 160, false, 400 );
                shockwave( me.m_x, me.m_y );
                me.m_state = 4, me.m_stateT = 0;
            }
        }
        else if ( me.m_state == 3 )
        {
            // Calls drones.
            me.m_anim = "summon";
            gravityWalk( 0 );
            if ( me.m_stateT > 0.6f && me.m_shootT <= 0 )
            {
                summon( "hoverdrone", me.m_x - 90, me.top() - 30 );
                summon( "hoverdrone", m_enemies[index].m_x + 90, m_enemies[index].top() - 30 );
                m_enemies[index].m_shootT = 99;
            }
            if ( m_enemies[index].m_stateT > 1.2f ) m_enemies[index].m_state = 0, m_enemies[index].m_stateT = 0, m_enemies[index].m_shootT = 0;
        }
        else
        {
            me.m_anim = "land";
            gravityWalk( 0 );
            if ( me.m_stateT > 0.7f ) me.m_state = 0, me.m_stateT = 0;
        }
        break;
    }

    case 2:   // BROODMOTHER: hovers in an eight, spits acid, lays mothlings, dives later.
    {
        if ( e.m_state == 0 )
        {
            e.m_anim = "fly";
            float tx = e.m_homeX + std::sin( e.m_t * 0.7f ) * 170, ty = e.m_homeY - 40 + std::sin( e.m_t * 1.4f ) * 50;
            e.m_x += std::clamp( ( tx - e.m_x ) * 2.0f, -d.m_speed, d.m_speed ) * dt;
            e.m_y += std::clamp( ( ty - e.m_y ) * 2.0f, -d.m_speed, d.m_speed ) * dt;
            face();
            // Spitting: she rears back (the "spit" animation), the acid leaves a quarter second in.
            if ( e.m_shootT <= 0.25f && e.m_shootT > 0 && heroUp ) e.m_anim = "spit";
            if ( e.m_shootT <= 0 && heroUp )
            {
                Vector2 mz = assets().sheet( d.m_id ).point( "muzzle", { 0, -20 } );
                float   mx = e.m_x + mz.x * e.m_dir, my = e.m_y + mz.y;
                for ( int k = -1; k <= 1; ++k )
                {
                    float t = 0.9f, g = 900;
                    float vx = ( hx + k * 50 - mx ) / t, vy = ( hy - my - 0.5f * g * t * t ) / t;
                    enemyShoot( m_enemies[index], "acid", mx, my, std::clamp( vx, -420.0f, 420.0f ), std::max( vy, -600.0f ) );
                }
                m_enemies[index].m_shootT = 2.4f - 0.4f * phase;
                m_enemies[index].m_attackT = 0;
                m_enemies[index].m_anim = "spit";
            }
            if ( m_enemies[index].m_shootT > 2.0f - 0.4f * phase ) m_enemies[index].m_anim = "spit";
            if ( e.m_stateT > 6.0f - phase && minions() < 3 )
            {
                summon( "mothling", e.m_x, e.cy() + 30 );
                m_enemies[index].m_stateT = 0;
            }
            if ( phase >= 1 && m_enemies[index].m_stateT > 4.0f && GetRandomValue( 0, 60 ) == 0 )
                m_enemies[index].m_state = 1, m_enemies[index].m_stateT = 0;
        }
        else if ( e.m_state == 1 )
        {
            // Dive: down to the hero's height and across the arena.
            e.m_anim = "attack";
            if ( e.m_stateT < dt * 1.5f )
            {
                face();
                sfx( "boss_roar", 0.6f, 1.3f );
            }
            float ty = m_hero.m_y - 6;
            e.m_y += std::clamp( ( ty - e.m_y ) * 4.0f, -300.0f, 300.0f ) * dt;
            if ( e.m_stateT > 0.6f ) e.m_x += e.m_dir * 380 * dt;
            int cx = (int)std::floor( ( e.m_x + e.m_dir * w * 0.5f ) / T );
            if ( solid( cx, (int)std::floor( e.cy() / T ) ) || e.m_stateT > 2.6f ) e.m_state = 2, e.m_stateT = 0;
        }
        else
        {
            e.m_anim = "fly";
            float tx = e.m_homeX, ty = e.m_homeY - 40;
            e.m_x += std::clamp( ( tx - e.m_x ) * 2.0f, -d.m_speed, d.m_speed ) * dt;
            e.m_y += std::clamp( ( ty - e.m_y ) * 2.0f, -d.m_speed, d.m_speed ) * dt;
            if ( e.m_stateT > 1.6f ) e.m_state = 0, e.m_stateT = 0;
        }
        break;
    }

    case 3:   // COLOSSUS: slow steps, ground slams that bring down shards, a low ice beam, charges when hurt.
    {
        if ( e.m_state == 0 )
        {
            e.m_anim = "move";
            face();
            gravityWalk( d.m_speed );
            if ( e.m_stateT > 2.2f - 0.4f * phase ) e.m_state = 1 + GetRandomValue( 0, phase >= 1 ? 2 : 1 ), e.m_stateT = 0;
        }
        else if ( e.m_state == 1 )
        {
            // Slam: shards fall from the ceiling over the hero.
            e.m_anim = "attack";
            gravityWalk( 0 );
            if ( e.m_stateT > 0.7f && e.m_shootT <= 0 )
            {
                m_shake = 0.7f;
                sfx( "crusher" );
                int n = 5 + 2 * phase;
                for ( int k = 0; k < n; ++k )
                {
                    float x = hx + GetRandomValue( -220, 220 );
                    enemyShoot( e, "shard", x, m_camY - 8 - GetRandomValue( 0, 120 ), 0, 260 );
                    m_shots.back().m_range = 1400;
                }
                e.m_shootT = 99;
            }
            if ( e.m_stateT > 1.5f ) e.m_state = 0, e.m_stateT = 0, e.m_shootT = 0;
        }
        else if ( e.m_state == 2 )
        {
            // The ice beam, low over the floor: jump it.
            gravityWalk( 0 );
            face();
            e.m_anim = "attack";
            if ( e.m_stateT > 0.2f && e.m_stateT < 0.3f ) sfx( "charge", 0.6f, 0.6f );
            float y = e.m_y - 20;
            if ( e.m_stateT > 1.0f && e.m_stateT < 1.6f )
            {
                float x = e.m_x, len = 0;
                while ( len < 700 && !solid( (int)std::floor( ( x + e.m_dir * 4 ) / T ), (int)std::floor( y / T ) ) ) x += e.m_dir * 4, len += 4;
                Beam b;
                b.m_points = { { e.m_x + e.m_dir * w * 0.4f, y }, { x, y } };
                b.m_c = { 150, 230, 255, 255 };
                b.m_life = 0.05f;
                m_beams.push_back( b );
                float l = std::min( e.m_x, x ), r = std::max( e.m_x, x );
                if ( heroUp && m_hero.right() > l && m_hero.left() < r && m_hero.top() < y + 7 && m_hero.m_y > y - 7 )
                    hurtHero( 25, e.m_x, e.m_def->m_id );
            }
            if ( e.m_stateT > 1.0f && e.m_stateT < 1.0f + dt * 1.5f ) sfx( "shoot_lancer", 0.8f, 0.5f );
            if ( e.m_stateT > 2.0f ) e.m_state = 0, e.m_stateT = 0;
        }
        else
        {
            // Charge.
            e.m_anim = e.m_stateT < 0.5f ? "idle" : "charge";
            if ( e.m_stateT < 0.5f ) gravityWalk( 0 ), face();
            else
            {
                int dir = e.m_dir;
                gravityWalk( d.m_speed * 4.5f );
                if ( e.m_dir != dir || e.m_stateT > 2.4f )
                {
                    m_shake = 0.5f;
                    sfx( "crusher", 0.8f, 0.8f );
                    e.m_state = 0, e.m_stateT = 0;
                }
            }
        }
        break;
    }

    case 4:   // THE GLOAM: blinks between anchor points, rings of orbs, beams, troopers, seekers.
    {
        float ax[3] = { e.m_homeX - 220, e.m_homeX, e.m_homeX + 220 };
        float ay[3] = { e.m_homeY, e.m_homeY - 70, e.m_homeY };
        if ( e.m_state == 0 )
        {
            e.m_anim = "fly";
            face();
            int   at = e.m_phase >= 0 ? ( (int)e.m_shootT ) : 0;
            (void)at;
            e.m_y += std::sin( e.m_t * 2.0f ) * 12 * dt;
            if ( e.m_stateT > 3.2f - 0.6f * phase )
            {
                // Attack, then blink elsewhere.
                e.m_anim = "attack";
                int pick = GetRandomValue( 0, 1 + phase );
                if ( pick == 0 || pick == 3 )
                {
                    int n = 8 + 4 * phase;
                    for ( int k = 0; k < n; ++k )
                    {
                        float a = ( 360.0f * k / n + e.m_t * 40 ) * DEG2RAD;
                        enemyShoot( e, "enemy_orb", e.m_x, e.cy(), std::cos( a ) * 170, std::sin( a ) * 170 );
                    }
                }
                else if ( pick == 1 )
                {
                    for ( int k = -1; k <= 1; ++k )
                    {
                        float a = std::atan2( dy, dx ) + k * 0.2f;
                        enemyShoot( e, "enemy_bolt", e.m_x, e.cy(), std::cos( a ) * 300, std::sin( a ) * 300 );
                    }
                }
                else if ( pick == 2 )
                {
                    if ( minions() < 2 )
                    {
                        summon( "trooper", ax[0], m_hero.m_y );
                        summon( "trooper", ax[2], m_hero.m_y );
                    }
                    else
                        for ( int k = 0; k < 3; ++k )
                            enemyShoot( m_enemies[index], "missile", m_enemies[index].m_x, m_enemies[index].top(), ( k - 1 ) * 160.0f, -200 );
                }
                Enemy &me = m_enemies[index];
                me.m_state = 1, me.m_stateT = 0;
            }
        }
        else
        {
            e.m_anim = "attack";
            if ( e.m_stateT > 0.6f )
            {
                int k = GetRandomValue( 0, 2 );
                effect( "beam_in", e.m_x, e.cy() );
                e.m_x = ax[k], e.m_y = ay[k];
                effect( "beam_in", e.m_x, e.cy() );
                sfx( "teleport", 0.6f, 0.7f );
                e.m_state = 0, e.m_stateT = 0;
            }
        }
        break;
    }
    }
}

}   // namespace kepler
