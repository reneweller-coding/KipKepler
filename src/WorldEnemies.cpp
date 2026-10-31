/**
 * @file WorldEnemies.cpp
 * @brief The enemies' behaviour, one small state machine per brain (Content.h BrainE).
 * @author Rene Weller
 */
#include "Assets.h"
#include "Audio.h"
#include "World.h"

#include <algorithm>
#include <vector>
#include <cmath>

namespace kepler
{

namespace
{

constexpr float T = (float)Tile;

}   // namespace

void World::stepEnemies( float dt )
{
    // Fixed-size loop: spawners may add enemies while we go.
    size_t count = m_enemies.size();
    for ( size_t i = 0; i < count; ++i )
    {
        Enemy &e = m_enemies[i];
        if ( !e.m_alive ) continue;
        e.m_t += dt;
        e.m_animT += dt;
        if ( e.m_flash > 0 ) e.m_flash -= dt;
        // The animation clock starts again whenever the animation changes (attacks begin with their wind-up).
        struct AnimClock
        {
            std::vector<Enemy> &list;
            size_t              i;
            ~AnimClock()
            {
                Enemy &x = list[i];
                if ( x.m_attackT > 0 ) x.m_anim = "attack";
                if ( x.m_anim != x.m_animWas ) x.m_animT = 0, x.m_animWas = x.m_anim;
            }
        } clock{ m_enemies, i };
        if ( e.m_attackT > 0 ) e.m_attackT -= dt;
        if ( e.m_elite == 5 && e.m_hp < e.m_hpMax ) e.m_hp = std::min( e.m_hpMax, e.m_hp + 0.6f * dt );
        if ( e.m_boss )
        {
            stepBoss( e, (int)i, dt );
            continue;
        }
        // A rider goes where its platform goes, asleep or not.
        if ( e.m_def->m_brain == BrainE::RIDER && e.m_mover >= 0 && e.m_frozen <= 0 )
        {
            const Mover &m = m_movers[e.m_mover];
            e.m_x += m.m_x - m.m_px;
            e.m_y = m.m_y;
            e.m_vy = 0;
            e.m_ground = true;
        }
        // Far away things sleep.
        if ( std::fabs( e.m_x - m_hero.m_x ) > 900 || std::fabs( e.m_y - m_hero.m_y ) > 640 ) continue;
        if ( e.m_hidden )
        {
            bool near = std::hypot( e.m_x - heroCx(), e.cy() - heroCy() ) < 7 * T;
            if ( e.m_def->m_brain == BrainE::EEL )
            {
                // Under the surface until the hero passes above the pool, then out in an arc to where he will be at
                // its top (he keeps running).
                if ( e.m_shootT > 0 ) e.m_shootT -= dt;
                if ( !m_dead && e.m_shootT <= 0 && std::fabs( e.m_x - heroCx() ) < 150 && m_hero.m_y < e.m_y &&
                     e.m_y - m_hero.m_y < 260 )
                {
                    float h = std::clamp( e.m_y - heroCy() + 24, 70.0f, 230.0f );
                    e.m_hidden = false;
                    e.m_state = 1, e.m_stateT = 0;
                    e.m_vy = -std::sqrt( 2 * 1500 * h );
                    float up = -e.m_vy / 1500, aim = heroCx() + m_hero.m_vx * up;
                    e.m_dir = aim < e.m_x ? -1 : 1;
                    e.m_vx = std::clamp( ( aim - e.m_x ) / up, -170.0f, 170.0f );
                    effect( "splash", e.m_x, e.m_y - 8 );
                    burst( e.m_x, e.m_y - 8, 12, { 120, 230, 200, 255 }, 160 );
                    sfx( "splash", 0.7f, 1.3f );
                }
                continue;
            }
            if ( e.m_def->m_brain == BrainE::BURROWER )
            {
                // Under the ground until the hero is right there, then out with a leap.
                if ( !m_dead && std::fabs( e.m_x - heroCx() ) < 90 && std::fabs( e.cy() - heroCy() ) < 70 )
                {
                    e.m_hidden = false;
                    e.m_state = 1, e.m_stateT = 0;
                    e.m_vy = -460;
                    e.m_dir = heroCx() < e.m_x ? -1 : 1;
                    sfx( "break", 0.6f, 1.3f );
                    burst( e.m_x, e.m_y, 12, { 170, 200, 230, 255 }, 140, false, 700 );
                }
                continue;
            }
            if ( near && !m_dead )
            {
                e.m_hidden = false;
                e.m_state = -1;
                e.m_stateT = 0;
                effect( "beam_in", e.m_x, e.cy() );
                sfx( "beam_in", 0.6f, 1.1f );
            }
            continue;
        }
        if ( e.m_state == -1 )
        {
            // Just beamed in: a moment to materialise.
            e.m_stateT += dt;
            if ( e.m_stateT > 0.45f ) e.m_state = 0, e.m_stateT = 0;
            continue;
        }
        if ( e.m_frozen > 0 )
        {
            e.m_frozen -= dt;
            if ( e.m_frozen <= 0 ) sfx( "shatter", 0.3f, 1.5f );
            if ( !e.m_ceiling && e.m_def->m_brain != BrainE::FLIER && e.m_def->m_brain != BrainE::FLOATER &&
                 e.m_def->m_brain != BrainE::GUNSHIP && e.m_def->m_brain != BrainE::TURRET && e.m_def->m_brain != BrainE::BEAMER )
            {
                float vx = 0;
                bool  wall = false;
                e.m_vy = std::min( 900.0f, e.m_vy + 1500 * dt );
                moveBox( *this, e.m_x, e.m_y, (float)e.m_def->m_w, (float)e.m_def->m_h, vx, e.m_vy, dt, true, e.m_ground, wall );
            }
            continue;
        }
        stepEnemy( e, (int)i, dt );
        // (A spawner may have grown the list: the reference is not to be trusted after the step.)
        if ( m_enemies[i].m_y > m_level.m_h * T + 64 ) m_enemies[i].m_alive = false;
    }
}

void World::stepEnemy( Enemy &e, int index, float dt )
{
    const EnemyDef &d = *e.m_def;
    float           speed = d.m_speed * e.m_speedMul;
    float           hx = heroCx(), hy = heroCy();
    float           dx = hx - e.m_x, dy = hy - e.cy();
    float           dist = std::hypot( dx, dy );
    bool            heroUp = !m_dead && m_exitT < 0;
    float           w = (float)d.m_w, h = (float)d.m_h;
    e.m_stateT += dt;
    if ( e.m_shootT > 0 ) e.m_shootT -= dt;
    float pan = 0.5f + std::clamp( -dx / 640.0f, -0.5f, 0.5f );
    (void)pan;

    // Ground movement with gravity; turns at walls and (if asked) at edges.
    auto walk = [&]( float speed, bool turnAtEdge )
    {
        e.m_vx += ( e.m_dir * speed - e.m_vx ) * std::min( 1.0f, dt * 8 );
        e.m_vy = std::min( 900.0f, e.m_vy + 1500 * dt );
        bool wall = false;
        moveBox( *this, e.m_x, e.m_y, w, h, e.m_vx, e.m_vy, dt, true, e.m_ground, wall );
        if ( wall ) e.m_dir = -e.m_dir;
        if ( e.m_ground && turnAtEdge )
        {
            float ahead = e.m_x + e.m_dir * ( w * 0.5f + 2 );
            int   cx = (int)std::floor( ahead / T ), cy = (int)std::floor( ( e.m_y + 2 ) / T );
            bool  floor = solid( cx, cy ) || oneway( cx, cy );
            float top = 0;
            if ( !floor && platformTop( ahead - 1, ahead + 1, e.m_y - 1, e.m_y + 2, top ) ) floor = true;
            if ( !floor ) e.m_dir = -e.m_dir, e.m_vx = 0;
        }
        return wall;
    };
    auto sees = [&]( float range, float height )
    {
        return heroUp && std::fabs( dx ) < range && std::fabs( dy ) < height && lineOfSight( e.m_x, e.cy(), hx, hy );
    };
    auto face = [&]() { e.m_dir = dx < 0 ? -1 : 1; };
    auto muzzle = [&]( float &x, float &y )
    {
        Vector2 p = assets().sheet( d.m_id ).point( "muzzle", { w * 0.5f, -h * 0.6f } );
        x = e.m_x + p.x * e.m_dir;
        y = e.m_y + p.y;
    };

    switch ( d.m_brain )
    {
    case BrainE::WALKER:
        e.m_anim = "move";
        if ( e.m_upsideDown )
        {
            // Upside down along the ceiling: turns at walls and where the ceiling ends.
            float nx = e.m_x + e.m_dir * speed * dt;
            float ahead = nx + e.m_dir * ( w * 0.5f + 1 );
            int   cx = (int)std::floor( ahead / T ), above = (int)std::floor( ( e.top() - 2 ) / T );
            int   r0 = (int)std::floor( e.top() / T ), r1 = (int)std::floor( ( e.m_y - 1 ) / T );
            bool  wall = false;
            for ( int cy = r0; cy <= r1; ++cy ) wall |= solid( cx, cy );
            if ( wall || !solid( cx, above ) ) e.m_dir = -e.m_dir;
            else
                e.m_x = nx;
            break;
        }
        walk( speed, true );
        break;

    case BrainE::SHOOTER:
        if ( e.m_state == 0 )
        {
            e.m_anim = "move";
            walk( speed, true );
            if ( e.m_shootT <= 0 && sees( 300, 40 ) ) e.m_state = 1, e.m_stateT = 0;
        }
        else
        {
            face();
            e.m_anim = "attack";
            e.m_vx = 0;
            walk( 0, true );
            if ( e.m_state == 1 && e.m_stateT > 0.45f )
            {
                float x, y;
                muzzle( x, y );
                enemyShoot( e, d.m_shot, x, y, e.m_dir * 300.0f, 0 );
                e.m_state = 2, e.m_stateT = 0;
                e.m_shootT = 1.4f;
            }
            if ( e.m_state == 2 && e.m_stateT > 0.35f ) e.m_state = 0;
        }
        break;

    case BrainE::LOBBER:
        face();
        walk( 0, true );
        e.m_anim = e.m_state ? "attack" : "idle";
        if ( e.m_state == 0 && e.m_shootT <= 0 && heroUp && dist < 380 )
        {
            e.m_state = 1;
            e.m_stateT = 0;
        }
        if ( e.m_state == 1 && e.m_stateT > 0.4f )
        {
            float x, y, t = 0.85f, g = 900;
            muzzle( x, y );
            float vx = ( hx - x ) / t, vy = ( hy - y - 0.5f * g * t * t ) / t;
            enemyShoot( e, d.m_shot, x, y, std::clamp( vx, -380.0f, 380.0f ), std::max( vy, -700.0f ) );
            e.m_state = 0;
            e.m_shootT = 1.8f;
        }
        break;

    case BrainE::FLIER:
    case BrainE::GUNSHIP:
    {
        e.m_anim = "fly";
        float tx = e.m_homeX + std::sin( e.m_t * 0.9f ) * 48, ty = e.m_homeY + std::sin( e.m_t * 1.7f ) * 12;
        bool  chase = heroUp && dist < ( d.m_brain == BrainE::GUNSHIP ? 340.0f : 230.0f ) && lineOfSight( e.m_x, e.cy(), hx, hy );
        if ( chase )
        {
            if ( d.m_brain == BrainE::GUNSHIP )
            {
                // Keep a shooting distance at the hero's height.
                tx = hx - ( dx > 0 ? 1 : -1 ) * 170, ty = m_hero.m_y - 10 + std::sin( e.m_t * 2 ) * 10;
            }
            else
                tx = hx, ty = hy + h * 0.5f;
        }
        float vx = std::clamp( ( tx - e.m_x ) * 2.0f, -speed, speed );
        float vy = std::clamp( ( ty - e.m_y ) * 2.0f, -speed, speed );
        e.m_vx += ( vx - e.m_vx ) * std::min( 1.0f, dt * 3 );
        e.m_vy += ( vy - e.m_vy ) * std::min( 1.0f, dt * 3 );
        bool ground = false, wall = false;
        moveBox( *this, e.m_x, e.m_y, w, h, e.m_vx, e.m_vy, dt, false, ground, wall );
        if ( std::fabs( e.m_vx ) > 10 ) e.m_dir = e.m_vx < 0 ? -1 : 1;
        if ( d.m_brain == BrainE::GUNSHIP && chase )
        {
            face();
            if ( e.m_shootT <= 0 && std::fabs( dy ) < 60 )
            {
                float x, y;
                muzzle( x, y );
                enemyShoot( e, d.m_shot, x, y, e.m_dir * 300.0f, 0 );
                e.m_shootT = 1.6f;
                e.m_attackT = 0.3f;
            }
        }
        break;
    }

    case BrainE::SWOOPER:
        if ( e.m_state == 0 )
        {
            e.m_anim = "idle";
            if ( heroUp && std::fabs( dx ) < 170 && dy > 0 && dy < 260 && e.m_stateT > 1.0f && lineOfSight( e.m_x, e.cy(), hx, hy ) )
            {
                e.m_state = 1, e.m_stateT = 0;
                float n = std::max( 1.0f, dist );
                e.m_vx = dx / n * speed * 1.6f, e.m_vy = dy / n * speed * 1.6f;
                sfx( "jump", 0.3f, 1.8f );
            }
        }
        else if ( e.m_state == 1 )
        {
            e.m_anim = "attack";
            bool ground = false, wall = false;
            moveBox( *this, e.m_x, e.m_y, w, h, e.m_vx, e.m_vy, dt, false, ground, wall );
            if ( e.m_stateT > 0.8f || ground || wall ) e.m_state = 2, e.m_stateT = 0;
        }
        else
        {
            e.m_anim = "fly";
            float vx = std::clamp( ( e.m_homeX - e.m_x ) * 3.0f, -speed, speed );
            float vy = std::clamp( ( e.m_homeY - e.m_y ) * 3.0f, -speed, speed );
            e.m_x += vx * dt, e.m_y += vy * dt;
            if ( std::hypot( e.m_homeX - e.m_x, e.m_homeY - e.m_y ) < 3 || e.m_stateT > 3 )
                e.m_x = e.m_homeX, e.m_y = e.m_homeY, e.m_state = 0, e.m_stateT = 0;
        }
        if ( std::fabs( e.m_vx ) > 10 ) e.m_dir = e.m_vx < 0 ? -1 : 1;
        break;

    case BrainE::TURRET:
    {
        e.m_anim = "idle";
        bool canSee = heroUp && dist < 340 && lineOfSight( e.m_x, e.cy(), hx, hy ) && ( e.m_ceiling ? dy > -8 : dy < 8 );
        if ( canSee )
        {
            face();
            e.m_anim = "attack";
            if ( e.m_shootT <= 0 )
            {
                float n = std::max( 1.0f, dist );
                // From the barrel's height (on a ceiling the turret hangs upside down), a little towards the hero.
                Vector2 mz = assets().sheet( d.m_id ).point( "muzzle", { 0, -h * 0.5f } );
                float   y = e.m_ceiling ? e.top() - mz.y : e.m_y + mz.y;
                enemyShoot( e, d.m_shot, e.m_x + dx / n * 14, y + dy / n * 6, dx / n * 260, dy / n * 260 );
                e.m_shootT = 1.5f;
                e.m_attackT = 0.3f;
            }
        }
        break;
    }

    case BrainE::BEAMER:
    {
        face();
        bool lined = heroUp && std::fabs( dx ) < 420 && std::fabs( dy ) < 36 && lineOfSight( e.m_x, e.cy(), hx, e.cy() );
        if ( e.m_state == 0 )
        {
            e.m_anim = "idle";
            if ( lined && e.m_shootT <= 0 ) e.m_state = 1, e.m_stateT = 0, sfx( "charge", 0.4f, 0.7f );
        }
        else if ( e.m_state == 1 )
        {
            e.m_anim = "attack";
            if ( e.m_stateT > 0.9f ) e.m_state = 2, e.m_stateT = 0, sfx( "shoot_lancer", 0.6f, 0.7f );
        }
        else
        {
            // The beam: to the next wall in the facing direction.
            float x = e.m_x, y = e.cy(), len = 0;
            while ( len < 600 && !solid( (int)std::floor( ( x + e.m_dir * 4 ) / T ), (int)std::floor( y / T ) ) ) x += e.m_dir * 4, len += 4;
            if ( m_beams.empty() || m_beams.back().m_t > 0.05f )
            {
                Beam b;
                b.m_points = { { e.m_x + e.m_dir * 12, y }, { x, y } };
                b.m_c = { 255, 60, 200, 255 };
                b.m_life = 0.06f;
                m_beams.push_back( b );
            }
            float l = std::min( e.m_x, x ), r = std::max( e.m_x, x );
            if ( heroUp && m_hero.right() > l && m_hero.left() < r && m_hero.top() < y + 6 && m_hero.m_y > y - 6 )
                hurtHero( 25, e.m_x, e.m_def->m_id );
            if ( e.m_stateT > 0.45f ) e.m_state = 0, e.m_shootT = 2.0f;
        }
        break;
    }

    case BrainE::FLOATER:
    {
        e.m_anim = "fly";
        float tx = e.m_homeX + std::sin( e.m_t * 1.3f ) * 20, ty = e.m_homeY + std::cos( e.m_t * 1.1f ) * 14;
        if ( heroUp && dist < 260 && lineOfSight( e.m_x, e.cy(), hx, hy ) ) tx = hx, ty = hy + h * 0.5f;
        float n = std::max( 1.0f, std::hypot( tx - e.m_x, ty - e.m_y ) );
        float sp = std::min( speed, n * 2 );
        e.m_vx = ( tx - e.m_x ) / n * sp, e.m_vy = ( ty - e.m_y ) / n * sp;
        bool ground = false, wall = false;
        if ( std::string( d.m_id ) == "wisp" ) e.m_x += e.m_vx * dt, e.m_y += e.m_vy * dt;   // wisps pass through rock
        else
            moveBox( *this, e.m_x, e.m_y, w, h, e.m_vx, e.m_vy, dt, false, ground, wall );
        if ( std::fabs( e.m_vx ) > 5 ) e.m_dir = e.m_vx < 0 ? -1 : 1;
        if ( *d.m_shot && e.m_shootT <= 0 && heroUp && dist < 200 )
        {
            float x, y;
            muzzle( x, y );
            enemyShoot( e, d.m_shot, x, y, dx / std::max( 1.0f, dist ) * 80, dy / std::max( 1.0f, dist ) * 80 );
            e.m_shootT = 2.5f;
            e.m_attackT = 0.4f;
        }
        break;
    }

    case BrainE::CHARGER:
        if ( e.m_state == 0 )
        {
            e.m_anim = "move";
            walk( speed * 0.5f, true );
            if ( sees( 270, 34 ) && e.m_stateT > 0.6f ) face(), e.m_state = 1, e.m_stateT = 0;
        }
        else if ( e.m_state == 1 )
        {
            e.m_anim = "attack";
            walk( 0, true );
            if ( e.m_stateT > 0.5f ) e.m_state = 2, e.m_stateT = 0, sfx( "boss_roar", 0.25f, 1.8f );
        }
        else if ( e.m_state == 2 )
        {
            e.m_anim = "attack";
            int  before = e.m_dir;
            bool wall = walk( speed * 3.5f, true );
            if ( wall || e.m_dir != before || e.m_stateT > 1.6f )
            {
                e.m_dir = before;
                e.m_state = 3, e.m_stateT = 0;
                if ( wall ) m_shake = std::max( m_shake, 0.15f ), sfx( "crusher", 0.3f, 1.4f );
            }
        }
        else
        {
            e.m_anim = "hurt";
            e.m_vx = 0;
            walk( 0, false );
            if ( e.m_stateT > 0.9f ) e.m_state = 0, e.m_stateT = 0;
        }
        break;

    case BrainE::HOPPER:
    {
        e.m_vy = std::min( 900.0f, e.m_vy + 1500 * dt );
        bool wall = false;
        if ( e.m_ground ) e.m_vx *= 0.8f;
        moveBox( *this, e.m_x, e.m_y, w, h, e.m_vx, e.m_vy, dt, true, e.m_ground, wall );
        if ( wall ) e.m_dir = -e.m_dir, e.m_vx = -e.m_vx;
        e.m_anim = e.m_ground ? "idle" : "attack";
        if ( e.m_ground && e.m_stateT > 1.0f + ( index % 5 ) * 0.1f )
        {
            if ( heroUp && dist < 320 ) face();
            else if ( GetRandomValue( 0, 2 ) == 0 )
                e.m_dir = -e.m_dir;
            e.m_vy = -540;
            e.m_vx = e.m_dir * speed * ( heroUp && dist < 320 ? 1.6f : 0.8f );
            e.m_ground = false;
            e.m_stateT = 0;
        }
        break;
    }

    case BrainE::DROPPER:
        if ( e.m_state == 0 )
        {
            e.m_anim = "idle";
            if ( heroUp && std::fabs( dx ) < 26 && dy > 0 && dy < 260 ) e.m_state = 1, e.m_stateT = 0, e.m_vy = 0;
        }
        else if ( e.m_state == 1 )
        {
            e.m_anim = "attack";
            e.m_vy = std::min( 900.0f, e.m_vy + 1800 * dt );
            float vx = 0;
            bool  wall = false;
            moveBox( *this, e.m_x, e.m_y, w, h, vx, e.m_vy, dt, true, e.m_ground, wall );
            if ( e.m_ground || e.m_stateT > 0.9f ) e.m_state = 2, e.m_stateT = 0;
        }
        else if ( e.m_state == 2 )
        {
            e.m_anim = "idle";
            if ( e.m_stateT > 0.7f ) e.m_state = 3, e.m_stateT = 0;
        }
        else
        {
            e.m_anim = "move";
            e.m_y = std::max( e.m_homeY, e.m_y - 140 * dt );
            if ( e.m_y <= e.m_homeY ) e.m_state = 0, e.m_stateT = 0;
        }
        break;

    case BrainE::SPAWNER:
        e.m_anim = "idle";
        if ( heroUp && dist < 440 && e.m_children < 3 && e.m_shootT <= 0 )
        {
            e.m_anim = "attack";
            float sx = e.m_x + ( dx < 0 ? -1 : 1 ) * ( w * 0.5f + 20 ), sy = e.m_y - 4;
            const EnemyDef *cd = enemyDef( d.m_child );
            if ( cd && ( cd->m_brain == BrainE::FLIER || cd->m_brain == BrainE::GUNSHIP ) ) sy = e.top() - 10;
            int c = spawnEnemy( d.m_child, sx, sy, false );
            if ( c >= 0 )
            {
                Enemy &child = m_enemies[c];   // e may have moved with the vector
                child.m_parent = index;
                child.m_state = -1;
                child.m_dir = dx < 0 ? -1 : 1;
                ++m_enemies[index].m_children;
                ++m_enemiesTotal;
                effect( "beam_in", child.m_x, child.cy() );
                sfx( "beam_in", 0.5f );
                m_enemies[index].m_shootT = 3.5f;
                m_enemies[index].m_attackT = 0.6f;
            }
        }
        break;

    case BrainE::BLINKER:
        e.m_anim = e.m_state == 1 ? "attack" : "idle";
        if ( e.m_state == 0 && heroUp && dist < 420 && e.m_stateT > 2.4f )
        {
            // Pick a free spot on a floor 80-170 px from the hero.
            for ( int tries = 0; tries < 24; ++tries )
            {
                float side = GetRandomValue( 0, 1 ) ? 1.0f : -1.0f;
                float tx = m_hero.m_x + side * GetRandomValue( 80, 170 );
                int   cx = (int)std::floor( tx / T ), cy = (int)std::floor( ( m_hero.m_y - 1 ) / T );
                for ( int yy = cy - 2; yy <= cy + 3; ++yy )
                    if ( !solid( cx, yy - 1 ) && !solid( cx, yy - 2 ) && ( solid( cx, yy ) || oneway( cx, yy ) ) )
                    {
                        effect( "beam_in", e.m_x, e.cy() );
                        e.m_x = cx * T + T * 0.5f;
                        e.m_y = yy * T;
                        effect( "beam_in", e.m_x, e.cy() );
                        sfx( "teleport", 0.4f, 1.3f );
                        e.m_state = 1, e.m_stateT = 0;
                        tries = 99;
                        break;
                    }
            }
            if ( e.m_state == 0 ) e.m_stateT = 1.8f;
        }
        else if ( e.m_state == 1 && e.m_stateT > 0.5f )
        {
            face();
            float x, y;
            muzzle( x, y );
            float n = std::max( 1.0f, std::hypot( hx - x, hy - y ) );
            enemyShoot( e, d.m_shot, x, y, ( hx - x ) / n * 240, ( hy - y ) / n * 240 );
            e.m_state = 0, e.m_stateT = 0;
            e.m_attackT = 0.3f;
        }
        break;

    case BrainE::BURROWER:
        {
            e.m_anim = e.m_ground ? "move" : "attack";
            if ( e.m_ground && e.m_stateT > 1.2f ) face(), e.m_stateT = 0.6f;
            walk( speed, true );
        }
        break;

        case BrainE::MIRROR:
            // Behind its mirror, always turned to the hero once it sees him; slowly closer.
            e.m_anim = "move";
            if ( sees( 320, 60 ) )
            {
                face();
                walk( std::fabs( dx ) > 70 ? speed : 0, true );
            }
            else
                walk( speed * 0.6f, true );
            break;

        case BrainE::EEL:
            // In the air: a plain arc, back into its pool where it came from.
            e.m_anim = "attack";
            e.m_vy = std::min( 900.0f, e.m_vy + 1500 * dt );
            e.m_x += e.m_vx * dt;
            e.m_y += e.m_vy * dt;
            if ( e.m_vy > 0 && e.m_y >= e.m_homeY )
            {
                e.m_x = e.m_homeX, e.m_y = e.m_homeY;
                e.m_vx = e.m_vy = 0;
                e.m_hidden = true;
                e.m_state = 0;
                e.m_shootT = 1.6f;
                effect( "splash", e.m_x, e.m_y - 8 );
                sfx( "splash", 0.5f, 1.4f );
            }
            break;

        case BrainE::SNIPER:
            // Takes aim (the line follows the hero, then holds still a moment) and fires one fast shard.
            if ( e.m_state == 0 )
            {
                e.m_anim = "move";
                walk( speed, true );
                if ( e.m_shootT <= 0 && sees( 470, 170 ) ) e.m_state = 1, e.m_stateT = 0, face();
            }
            else if ( e.m_state == 1 )
            {
                e.m_anim = "attack";
                walk( 0, true );
                if ( e.m_stateT < 0.75f ) face(), e.m_aimX = hx, e.m_aimY = hy;
                if ( e.m_stateT > 1.05f )
                {
                    float x, y;
                    muzzle( x, y );
                    float ax = e.m_aimX - x, ay = e.m_aimY - y, n = std::max( 1.0f, std::hypot( ax, ay ) );
                    enemyShoot( e, d.m_shot, x, y, ax / n * 640, ay / n * 640 );
                    e.m_state = 2, e.m_stateT = 0;
                    e.m_shootT = 2.4f;
                }
            }
            else
            {
                e.m_anim = "attack";
                walk( 0, true );
                if ( e.m_stateT > 0.4f ) e.m_state = 0;
            }
            break;

        case BrainE::RIDER:
        {
            // Rides the platform it stands on (looked for once), walks to and fro on it and shoots along its height.
            // (Carried by its platform in stepEnemies; here it walks to and fro on it.)
            bool shooting = e.m_state != 0;
            if ( e.m_mover >= 0 )
            {
                const Mover &m = m_movers[e.m_mover];
                float        l = m.m_x + w * 0.5f + 2, r = m.m_x + m.m_w * T - w * 0.5f - 2;
                if ( !shooting )
                {
                    e.m_x += e.m_dir * speed * 0.5f * dt;
                    if ( e.m_x < l ) e.m_x = l, e.m_dir = 1;
                    if ( e.m_x > r ) e.m_x = r, e.m_dir = -1;
                }
                else
                    e.m_x = std::clamp( e.m_x, l, std::max( l, r ) );
            }
            else
                walk( shooting ? 0 : speed, true );
            e.m_anim = shooting ? "attack" : "move";
            if ( !shooting && e.m_shootT <= 0 && sees( 340, 50 ) ) e.m_state = 1, e.m_stateT = 0;
            if ( e.m_state == 1 )
            {
                face();
                if ( e.m_stateT > 0.4f )
                {
                    float x, y;
                    muzzle( x, y );
                    enemyShoot( e, d.m_shot, x, y, e.m_dir * 320.0f, 0 );
                    e.m_state = 2, e.m_stateT = 0;
                    e.m_shootT = 1.6f;
                }
            }
            else if ( e.m_state == 2 && e.m_stateT > 0.3f )
                e.m_state = 0;
            break;
        }

    case BrainE::HEAVY:
        if ( heroUp && dist < 300 && e.m_shootT <= 0 && lineOfSight( e.m_x, e.cy(), hx, hy ) )
        {
            face();
            e.m_anim = "attack";
            walk( 0, true );
            if ( e.m_stateT > 0.5f )
            {
                float x, y, t = 0.9f, g = 900;
                muzzle( x, y );
                enemyShoot( e, d.m_shot, x, y, std::clamp( ( hx - x ) / t, -320.0f, 320.0f ), std::max( ( hy - y - 0.5f * g * t * t ) / t, -650.0f ) );
                e.m_shootT = 2.2f;
                e.m_stateT = 0;
            }
        }
        else
        {
            e.m_anim = "move";
            e.m_stateT = 0;
            walk( speed, true );
        }
        break;
    }
}

}   // namespace kepler
