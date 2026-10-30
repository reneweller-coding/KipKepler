/**
 * @file WorldShots.cpp
 * @brief Kip's weapons, the shots of both sides, hits, explosions and what shots do to cells.
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

Color colourOf( unsigned rgb )
{
    return { (unsigned char)( rgb >> 16 ), (unsigned char)( rgb >> 8 ), (unsigned char)rgb, 255 };
}

bool inBox( float x, float y, float r, const Enemy &e )
{
    return x + r > e.left() && x - r < e.right() && y + r > e.top() && y - r < e.m_y;
}

}   // namespace

void World::fire()
{
    WeaponE          w = m_weapon;
    const WeaponDef &d = weapon( w );
    int              up = m_progress->m_upgrade[(int)w];
    if ( d.m_ammoMax > 0 && m_progress->m_ammo[(int)w] < d.m_ammoUse )
    {
        sfx( "no_ammo", 0.6f );
        popup( tr( "msg.no_ammo" ), m_hero.m_x, m_hero.top() - 8, { 255, 120, 100, 255 } );
        m_weapon = WeaponE::BLASTER;
        m_cool = 0.3f;
        return;
    }
    if ( d.m_ammoMax > 0 ) m_progress->m_ammo[(int)w] -= d.m_ammoUse;

    const Sheet &hs = assets().sheet( "hero" );
    Vector2      mz = m_aimUp ? hs.point( "muzzle_up", { 4, -54 } ) : hs.point( "muzzle", { 22, -26 } );
    float        mx = m_hero.m_x + mz.x * m_face, my = m_hero.m_y + mz.y;
    float        dx = m_aimUp ? 0.0f : (float)m_face, dy = m_aimUp ? -1.0f : 0.0f;
    float        dmg = d.m_damage * ( 1.0f + ( up >= 1 ? 0.25f : 0 ) + ( up >= 3 ? 0.25f : 0 ) ) * ( m_overdrive > 0 ? 1.5f : 1.0f );
    float        angle = m_aimUp ? -90.0f : ( m_face < 0 ? 180.0f : 0.0f );
    Color        col = colourOf( d.m_colour );
    m_shootPose = 0.3f;
    m_cool = d.m_cool * ( w == WeaponE::BLASTER && up >= 2 ? 0.75f : 1.0f );

    auto shot = [&]( const std::string &anim, float speed, float deg, float damage )
    {
        float a = ( angle + deg ) * DEG2RAD;
        Shot  s;
        s.m_weapon = w;
        s.m_anim = anim;
        s.m_x = mx, s.m_y = my;
        s.m_vx = std::cos( a ) * speed;
        s.m_vy = std::sin( a ) * speed;
        s.m_damage = damage;
        s.m_range = d.m_range;
        s.m_life = 4;
        m_shots.push_back( s );
        return &m_shots.back();
    };

    switch ( w )
    {
    case WeaponE::BLASTER:
        if ( m_charge >= 90 )
        {
            Shot *s = shot( "bolt_charged", 620, 0, dmg * 4.5f );
            s->m_pierce = true;
            s->m_charged = true;
            s->m_range = 640;
            m_cool = 0.35f;
            sfx( "shoot_charged" );
            m_shake = std::max( m_shake, 0.15f );
        }
        else
        {
            shot( "bolt", d.m_speed, 0, dmg );
            sfx( "shoot", 0.55f, 1.0f + GetRandomValue( -3, 3 ) * 0.01f );
        }
        break;
    case WeaponE::REPEATER:
    {
        Shot *s = shot( "bolt_rapid", d.m_speed, (float)GetRandomValue( -25, 25 ) * 0.1f, dmg );
        s->m_pierce = up >= 3;
        sfx( "shoot_repeater", 0.4f, 1.0f + GetRandomValue( -4, 4 ) * 0.01f );
        break;
    }
    case WeaponE::SCATTER:
    {
        int n = up >= 3 ? 7 : 5;
        for ( int i = 0; i < n; ++i )
        {
            float deg = -18.0f + 36.0f * i / ( n - 1 ) + GetRandomValue( -2, 2 );
            Shot *s = shot( "pellet", d.m_speed * ( 0.9f + GetRandomValue( 0, 20 ) * 0.01f ), deg, dmg );
            s->m_range = d.m_range * ( 0.85f + GetRandomValue( 0, 30 ) * 0.01f );
        }
        sfx( "shoot_scatter", 0.8f );
        m_hero.m_vx -= dx * 60;
        break;
    }
    case WeaponE::RICOCHET:
    {
        Shot *s = shot( "disc", d.m_speed, 0, dmg );
        s->m_bounces = up >= 3 ? 6 : 4;
        sfx( "shoot_ricochet", 0.7f );
        break;
    }
    case WeaponE::CRYO:
        shot( "cryo", d.m_speed, 0, dmg );
        sfx( "shoot_cryo", 0.7f );
        break;
    case WeaponE::LANCER:
    {
        // An instant beam through every enemy up to the next wall.
        float x = mx, y = my, len = 0;
        while ( len < d.m_range && !solid( (int)std::floor( ( x + dx * 4 ) / T ), (int)std::floor( ( y + dy * 4 ) / T ) ) )
            x += dx * 4, y += dy * 4, len += 4;
        float half = up >= 3 ? 9.0f : 5.0f;
        float l = std::min( mx, x ), r = std::max( mx, x ), t = std::min( my, y ), b = std::max( my, y );
        if ( dx != 0 ) t -= half, b += half;
        else
            l -= half, r += half;
        for ( size_t i = 0; i < m_enemies.size(); ++i )
        {
            Enemy &e = m_enemies[i];
            if ( !e.m_alive || e.m_hidden ) continue;
            if ( e.right() > l && e.left() < r && e.m_y > t && e.top() < b ) hurtEnemy( (int)i, dmg, mx, w, true );
        }
        hitCell( (int)std::floor( ( x + dx * 6 ) / T ), (int)std::floor( ( y + dy * 6 ) / T ), dmg );
        Beam bm;
        bm.m_points = { { mx, my }, { x, y } };
        bm.m_c = col;
        bm.m_life = 0.16f;
        m_beams.push_back( bm );
        effect( "spark", x, y );
        sfx( "shoot_lancer", 0.8f );
        break;
    }
    case WeaponE::MORTAR:
    {
        Shot *s = shot( "mortar", 0, 0, dmg );
        s->m_vx = m_aimUp ? m_face * 70.0f : m_face * 250.0f;
        s->m_vy = m_aimUp ? -640.0f : -430.0f;
        s->m_gravity = true;
        s->m_splash = up >= 3 ? 72.0f : 52.0f;
        s->m_range = 0;
        sfx( "shoot_mortar", 0.8f );
        break;
    }
    case WeaponE::ARC:
    {
        // Lightning to the nearest enemy in front, then on to its neighbours.
        int                  chain = up >= 3 ? 6 : 4;
        std::vector<int>     hit;
        std::vector<Vector2> pts = { { mx, my } };
        float                fx = mx, fy = my;
        for ( int k = 0; k < chain; ++k )
        {
            int   best = -1;
            float bestD = k == 0 ? d.m_range : 130.0f;
            for ( size_t i = 0; i < m_enemies.size(); ++i )
            {
                const Enemy &e = m_enemies[i];
                if ( !e.m_alive || e.m_hidden || std::find( hit.begin(), hit.end(), (int)i ) != hit.end() ) continue;
                float ex = e.m_x, ey = e.cy();
                if ( k == 0 && !m_aimUp && ( ex - mx ) * m_face < -8 ) continue;
                if ( k == 0 && m_aimUp && ey > my + 8 ) continue;
                float dd = std::hypot( ex - fx, ey - fy );
                if ( dd < bestD && lineOfSight( fx, fy, ex, ey ) ) best = (int)i, bestD = dd;
            }
            if ( best < 0 ) break;
            hit.push_back( best );
            fx = m_enemies[best].m_x, fy = m_enemies[best].cy();
            pts.push_back( { fx, fy } );
        }
        for ( size_t k = 0; k < hit.size(); ++k ) hurtEnemy( hit[k], dmg * ( k == 0 ? 1.0f : 0.8f ), mx, w, true );
        if ( hit.empty() ) pts.push_back( { mx + dx * 70, my + dy * 70 } );
        Beam bm;
        bm.m_points = pts;
        bm.m_c = col;
        bm.m_arc = true;
        bm.m_life = 0.14f;
        m_beams.push_back( bm );
        for ( size_t k = 1; k < pts.size(); ++k ) effect( "zap", pts[k].x, pts[k].y );
        sfx( "shoot_arc", 0.7f );
        break;
    }
    case WeaponE::SEEKER:
    {
        int n = up >= 3 ? 4 : 3;
        for ( int i = 0; i < n; ++i )
        {
            Shot *s = shot( "seeker", 160, -50.0f + 100.0f * i / ( n - 1 ), dmg );
            s->m_homing = true;
            s->m_range = d.m_range;
            s->m_life = 3.5f;
        }
        sfx( "shoot_seeker", 0.7f );
        break;
    }
    default: break;
    }
    effect( "muzzle", mx, my, m_face < 0, m_aimUp ? -90.0f * m_face : 0 );
}

void World::fireAlt()
{
    // Each weapon's second function: stronger, costlier, slower to come again.
    WeaponE          w = m_weapon;
    const WeaponDef &d = weapon( w );
    static const int cost[WeaponCount] = { 0, 8, 3, 3, 8, 3, 3, 10, 4 };
    if ( d.m_ammoMax > 0 && m_progress->m_ammo[(int)w] < cost[(int)w] )
    {
        sfx( "no_ammo", 0.6f );
        popup( tr( "msg.no_ammo" ), m_hero.m_x, m_hero.top() - 8, { 255, 120, 100, 255 } );
        m_cool = 0.3f;
        return;
    }
    if ( d.m_ammoMax > 0 ) m_progress->m_ammo[(int)w] -= cost[(int)w];
    int          up = m_progress->m_upgrade[(int)w];
    const Sheet &hs = assets().sheet( "hero" );
    Vector2      mz = m_aimUp ? hs.point( "muzzle_up", { 4, -54 } ) : hs.point( "muzzle", { 22, -26 } );
    float        mx = m_hero.m_x + mz.x * m_face, my = m_hero.m_y + mz.y;
    float        dmg = d.m_damage * ( 1.0f + ( up >= 1 ? 0.25f : 0 ) + ( up >= 3 ? 0.25f : 0 ) ) * ( m_overdrive > 0 ? 1.5f : 1.0f );
    float        angle = m_aimUp ? -90.0f : ( m_face < 0 ? 180.0f : 0.0f );
    Color        col = { (unsigned char)( d.m_colour >> 16 ), (unsigned char)( d.m_colour >> 8 ), (unsigned char)d.m_colour, 255 };
    m_shootPose = 0.35f;
    auto shot = [&]( const std::string &anim, float speed, float deg, float damage )
    {
        float a = ( angle + deg ) * DEG2RAD;
        Shot  s;
        s.m_weapon = w;
        s.m_anim = anim;
        s.m_x = mx, s.m_y = my;
        s.m_vx = std::cos( a ) * speed;
        s.m_vy = std::sin( a ) * speed;
        s.m_damage = damage;
        s.m_range = d.m_range;
        s.m_life = 4;
        m_shots.push_back( s );
        return &m_shots.back();
    };
    auto inRadius = [&]( float r, auto &&f )
    {
        for ( size_t i = 0; i < m_enemies.size(); ++i )
        {
            Enemy &e = m_enemies[i];
            if ( e.m_alive && !e.m_hidden && std::hypot( e.m_x - m_hero.m_x, e.cy() - ( m_hero.m_y - 22 ) ) < r ) f( (int)i );
        }
    };
    switch ( w )
    {
    case WeaponE::BLASTER:
        // A burst of three.
        for ( int k = 0; k < 3; ++k ) shot( "bolt", d.m_speed * ( 1.0f - k * 0.08f ), ( k - 1 ) * 4.0f, dmg );
        sfx( "shoot", 0.7f, 0.85f );
        m_cool = 0.9f;
        break;
    case WeaponE::REPEATER:
        for ( int k = 0; k < 8; ++k ) shot( "bolt_rapid", d.m_speed * ( 0.85f + k * 0.03f ), (float)GetRandomValue( -60, 60 ) * 0.1f, dmg )->m_pierce = true;
        sfx( "shoot_repeater", 0.8f, 0.8f );
        m_cool = 0.7f;
        break;
    case WeaponE::SCATTER:
    {
        // One heavy slug through everything in its way.
        Shot *s = shot( "bolt_charged", 700, 0, dmg * 5 );
        s->m_pierce = true;
        s->m_charged = true;
        sfx( "shoot_charged", 0.8f, 1.2f );
        m_hero.m_vx -= ( m_aimUp ? 0 : m_face ) * 160;
        m_cool = 0.9f;
        break;
    }
    case WeaponE::RICOCHET:
        for ( int k = -1; k <= 1; ++k ) shot( "disc", d.m_speed, k * 30.0f, dmg )->m_bounces = up >= 3 ? 6 : 4;
        sfx( "shoot_ricochet", 0.8f, 0.9f );
        m_cool = 0.8f;
        break;
    case WeaponE::CRYO:
        // A frost nova: everything near freezes.
        inRadius( 100, [&]( int i ) {
            Enemy &e = m_enemies[i];
            if ( e.m_boss ) return;
            e.m_frozen = up >= 3 ? 7.0f : 5.0f;
            effect( "freeze", e.m_x, e.cy() );
        } );
        burst( m_hero.m_x, m_hero.m_y - 22, 30, { 190, 240, 255, 255 }, 220, true, 0 );
        effect( "freeze", m_hero.m_x, m_hero.m_y - 22 );
        sfx( "freeze" );
        m_cool = 1.2f;
        break;
    case WeaponE::LANCER:
    {
        // A wide beam, twice the damage.
        float dx = m_aimUp ? 0.0f : (float)m_face, dy = m_aimUp ? -1.0f : 0.0f;
        float x = mx, y = my, len = 0;
        while ( len < d.m_range && !solid( (int)std::floor( ( x + dx * 4 ) / T ), (int)std::floor( ( y + dy * 4 ) / T ) ) )
            x += dx * 4, y += dy * 4, len += 4;
        float half = 16, l = std::min( mx, x ), r = std::max( mx, x ), t = std::min( my, y ), b = std::max( my, y );
        if ( dx != 0 ) t -= half, b += half;
        else
            l -= half, r += half;
        for ( size_t i = 0; i < m_enemies.size(); ++i )
        {
            Enemy &e = m_enemies[i];
            if ( e.m_alive && !e.m_hidden && e.right() > l && e.left() < r && e.m_y > t && e.top() < b ) hurtEnemy( (int)i, dmg * 2, mx, w, true );
        }
        Beam bm;
        bm.m_points = { { mx, my }, { x, y } };
        bm.m_c = col;
        bm.m_life = 0.3f;
        m_beams.push_back( bm );
        m_beams.push_back( bm );
        sfx( "shoot_lancer", 1.0f, 0.7f );
        m_shake = std::max( m_shake, 0.25f );
        m_cool = 1.2f;
        break;
    }
    case WeaponE::MORTAR:
        for ( int k = -1; k <= 1; ++k )
        {
            Shot *s = shot( "mortar", 0, 0, dmg );
            s->m_vx = ( m_aimUp ? 70.0f : 250.0f ) * m_face + k * 90;
            s->m_vy = ( m_aimUp ? -640.0f : -430.0f ) - std::abs( k ) * 40;
            s->m_gravity = true;
            s->m_splash = 44;
            s->m_range = 0;
        }
        sfx( "shoot_mortar", 0.9f, 0.85f );
        m_cool = 1.1f;
        break;
    case WeaponE::ARC:
    {
        // A storm: lightning to everything near.
        std::vector<Vector2> pts;
        inRadius( 150, [&]( int i ) {
            Enemy &e = m_enemies[i];
            Beam   bm;
            bm.m_points = { { m_hero.m_x, m_hero.m_y - 30 }, { e.m_x, e.cy() } };
            bm.m_c = col;
            bm.m_arc = true;
            bm.m_life = 0.2f;
            m_beams.push_back( bm );
            hurtEnemy( i, dmg * 1.2f, m_hero.m_x, w, true );
        } );
        burst( m_hero.m_x, m_hero.m_y - 30, 20, { 150, 200, 255, 255 }, 200, true, 0 );
        sfx( "shoot_arc", 1.0f, 0.8f );
        m_cool = 1.0f;
        break;
    }
    case WeaponE::SEEKER:
        for ( int k = 0; k < 6; ++k )
        {
            Shot *s = shot( "seeker", 160, -75.0f + 150.0f * k / 5, dmg );
            s->m_homing = true;
            s->m_life = 3.5f;
        }
        sfx( "shoot_seeker", 0.9f, 0.9f );
        m_cool = 1.0f;
        break;
    default: break;
    }
    effect( "muzzle", mx, my, m_face < 0, m_aimUp ? -90.0f * m_face : 0 );
}

void World::enemyShoot( Enemy &e, const std::string &kind, float x, float y, float vx, float vy )
{
    (void)e;
    Shot s;
    s.m_enemy = true;
    s.m_anim = kind;
    s.m_x = x, s.m_y = y, s.m_vx = vx, s.m_vy = vy;
    s.m_range = 900;
    s.m_life = 5;
    s.m_damage = 15;
    if ( kind == "acid" ) s.m_gravity = true;
    if ( kind == "shard" ) s.m_damage = 12;
    if ( kind == "missile" ) s.m_homing = true, s.m_damage = 20;
    if ( kind == "grenade" ) s.m_gravity = true, s.m_splash = 44, s.m_damage = 22;
    if ( kind == "spore" ) s.m_homing = true, s.m_damage = 10, s.m_life = 3;
    m_shots.push_back( s );
    float pan = 0.5f + std::clamp( ( x - m_hero.m_x ) / 640.0f, -0.5f, 0.5f );
    sfx( kind == "enemy_orb" ? "enemy_orb" : kind == "acid" ? "acid" : kind == "missile" ? "missile" : kind == "grenade" ? "grenade" : "enemy_shoot",
         0.5f, 1, pan );
}

void World::stepShots( float dt )
{
    for ( size_t si = 0; si < m_shots.size(); ++si )
    {
        Shot &s = m_shots[si];
        if ( s.m_dead ) continue;
        s.m_t += dt;
        s.m_life -= dt;
        if ( s.m_life <= 0 )
        {
            if ( s.m_splash > 0 ) explode( s.m_x, s.m_y, s.m_splash, s.m_damage, !s.m_enemy );
            s.m_dead = true;
            continue;
        }
        if ( s.m_homing )
        {
            float tx = 0, ty = 0;
            bool  has = false;
            if ( s.m_enemy )
            {
                tx = heroCx(), ty = heroCy(), has = !m_dead;
            }
            else
            {
                if ( s.m_target < 0 || !m_enemies[s.m_target].m_alive || m_enemies[s.m_target].m_hidden )
                {
                    s.m_target = -1;
                    float best = 360;
                    for ( size_t i = 0; i < m_enemies.size(); ++i )
                    {
                        const Enemy &e = m_enemies[i];
                        if ( !e.m_alive || e.m_hidden ) continue;
                        float dd = std::hypot( e.m_x - s.m_x, e.cy() - s.m_y );
                        if ( dd < best && lineOfSight( s.m_x, s.m_y, e.m_x, e.cy() ) ) best = dd, s.m_target = (int)i;
                    }
                }
                if ( s.m_target >= 0 ) tx = m_enemies[s.m_target].m_x, ty = m_enemies[s.m_target].cy(), has = true;
            }
            float speed = std::hypot( s.m_vx, s.m_vy );
            float want = s.m_enemy ? ( s.m_anim == "spore" ? 90.0f : 220.0f ) : std::min( 520.0f, speed + 900 * dt );
            if ( has && s.m_t > ( s.m_enemy ? 0.2f : 0.12f ) )
            {
                float a = std::atan2( s.m_vy, s.m_vx ), b = std::atan2( ty - s.m_y, tx - s.m_x );
                float diff = std::remainder( b - a, 2 * PI );
                float turn = ( s.m_enemy ? 2.2f : 7.0f ) * dt;
                a += std::clamp( diff, -turn, turn );
                s.m_vx = std::cos( a ) * want, s.m_vy = std::sin( a ) * want;
            }
            else if ( speed > 1 )
                s.m_vx *= want / speed, s.m_vy *= want / speed;
            if ( !s.m_enemy && GetRandomValue( 0, 2 ) == 0 )
                burst( s.m_x - s.m_vx * 0.02f, s.m_y - s.m_vy * 0.02f, 1, { 255, 160, 220, 255 }, 10, true, 0 );
        }
        if ( s.m_gravity ) s.m_vy += ( s.m_enemy ? 900.0f : 1000.0f ) * dt;
        float ox = s.m_x, oy = s.m_y;
        s.m_x += s.m_vx * dt;
        s.m_y += s.m_vy * dt;
        s.m_dist += std::hypot( s.m_vx, s.m_vy ) * dt;
        if ( s.m_range > 0 && s.m_dist > s.m_range )
        {
            s.m_dead = true;
            effect( "spark", s.m_x, s.m_y );
            continue;
        }
        int cx = (int)std::floor( s.m_x / T ), cy = (int)std::floor( s.m_y / T );
        if ( s.m_y > m_level.m_h * T + 64 )
        {
            s.m_dead = true;
            continue;
        }
        if ( solid( cx, cy ) )
        {
            if ( s.m_weapon == WeaponE::RICOCHET && !s.m_enemy && s.m_bounces > 0 )
            {
                // Mirror on the side it came through.
                bool hitX = solid( (int)std::floor( s.m_x / T ), (int)std::floor( oy / T ) );
                bool hitY = solid( (int)std::floor( ox / T ), (int)std::floor( s.m_y / T ) );
                if ( hitX || !hitY ) s.m_vx = -s.m_vx;
                if ( hitY || !hitX ) s.m_vy = -s.m_vy;
                s.m_x = ox, s.m_y = oy;
                --s.m_bounces;
                s.m_hit.clear();
                sfx( "disc_bounce", 0.4f, 1.0f + s.m_bounces * 0.05f );
                effect( "spark", s.m_x, s.m_y );
                hitCell( cx, cy, s.m_damage );
                continue;
            }
            if ( !s.m_enemy ) hitCell( cx, cy, s.m_damage * ( s.m_charged ? 2.0f : 1.0f ) );
            if ( s.m_splash > 0 ) explode( ox, oy, s.m_splash, s.m_damage, !s.m_enemy );
            else
            {
                effect( "spark", ox, oy, s.m_vx < 0 );
                if ( std::fabs( s.m_x - m_hero.m_x ) < 360 ) sfx( "hit_wall", 0.2f, 1.0f + GetRandomValue( -10, 10 ) * 0.01f );
            }
            s.m_dead = true;
            continue;
        }
        if ( s.m_enemy )
        {
            if ( !m_dead && m_exitT < 0 && s.m_x > m_hero.left() + 2 && s.m_x < m_hero.right() - 2 && s.m_y > m_hero.top() + 2 &&
                 s.m_y < m_hero.m_y - 1 )
            {
                if ( s.m_splash > 0 ) explode( s.m_x, s.m_y, s.m_splash, s.m_damage, false );
                else
                    hurtHero( s.m_damage, s.m_x - s.m_vx );
                if ( m_shield > 0 ) effect( "spark", s.m_x, s.m_y );
                s.m_dead = true;
            }
            continue;
        }
        // Switches can be shot.
        for ( Object &o : m_objects )
            if ( o.m_kind == "switch" && o.m_cx == cx && o.m_cy == cy && m_switchCool <= 0 && !o.m_args.empty() && !o.m_args[0].empty() )
            {
                flipGroup( ( o.m_args[0][0] - 'A' ) & 7 );
                m_switchCool = 0.6f;
                s.m_dead = true;
                effect( "spark", s.m_x, s.m_y );
            }
        if ( s.m_dead ) continue;
        float r = s.m_charged ? 9.0f : s.m_weapon == WeaponE::MORTAR ? 7.0f : 4.0f;
        for ( size_t i = 0; i < m_enemies.size() && !s.m_dead; ++i )
        {
            Enemy &e = m_enemies[i];
            if ( !e.m_alive || e.m_hidden || !inBox( s.m_x, s.m_y, r, e ) ) continue;
            if ( std::find( s.m_hit.begin(), s.m_hit.end(), (int)i ) != s.m_hit.end() ) continue;
            if ( s.m_splash > 0 )
            {
                explode( s.m_x, s.m_y, s.m_splash, s.m_damage, true );
                s.m_dead = true;
                break;
            }
            bool through = hurtEnemy( (int)i, s.m_damage, s.m_x - s.m_vx * 0.05f, s.m_weapon, s.m_charged );
            if ( s.m_weapon == WeaponE::CRYO && e.m_alive && !e.m_boss )
            {
                if ( e.m_frozen <= 0 ) effect( "freeze", e.m_x, e.cy() ), sfx( "freeze", 0.6f );
                e.m_frozen = m_progress->m_upgrade[(int)WeaponE::CRYO] >= 3 ? 7.0f : 5.0f;
            }
            if ( s.m_weapon == WeaponE::RICOCHET && ++s.m_hits >= 3 ) grant( AW_RICOCHET3 );
            if ( ( s.m_pierce || s.m_weapon == WeaponE::RICOCHET ) && through ) s.m_hit.push_back( (int)i );
            else
                s.m_dead = true;
        }
    }
    m_shots.erase( std::remove_if( m_shots.begin(), m_shots.end(), []( const Shot &s ) { return s.m_dead; } ), m_shots.end() );
}

bool World::hurtEnemy( int index, float damage, float fromX, WeaponE w, bool charged )
{
    Enemy &e = m_enemies[index];
    if ( !e.m_alive || e.m_hidden ) return true;
    float pan = 0.5f + std::clamp( ( e.m_x - m_hero.m_x ) / 640.0f, -0.5f, 0.5f );
    if ( e.m_frozen > 0 && !e.m_boss )
    {
        // An ice block shatters at any hit.
        effect( "shatter", e.m_x, e.cy() );
        sfx( "shatter", 0.8f, 1, pan );
        burst( e.m_x, e.cy(), 14, { 200, 240, 255, 255 }, 160, true, 500 );
        e.m_hp = 0;
        if ( ++m_progress->m_frozenKills >= 10 ) grant( AW_FROZEN10 );
        killEnemy( index );
        return true;
    }
    // Armour turns plain shots from the front.
    bool front = ( fromX - e.m_x ) * e.m_dir > 0;
    bool heavy = charged || w == WeaponE::LANCER || w == WeaponE::MORTAR || w == WeaponE::ARC;
    if ( e.m_shieldFront && front && !heavy && e.m_frozen <= 0 )
    {
        effect( "spark", fromX, e.cy() );
        sfx( "armour_ping", 0.6f, 1, pan );
        return false;
    }
    if ( w == WeaponE::CRYO && e.m_boss ) e.m_frozen = 0;
    e.m_hp -= damage;
    e.m_flash = 0.1f;
    if ( !e.m_boss && e.m_def->m_hp < 8 && e.m_def->m_brain != BrainE::TURRET && e.m_def->m_brain != BrainE::SPAWNER )
        e.m_vx += ( e.m_x > fromX ? 1 : -1 ) * 60.0f;
    sfx( e.m_boss ? "boss_hit" : "hit_enemy", 0.45f, 1.0f + GetRandomValue( -6, 6 ) * 0.01f, pan );
    burst( e.m_x, e.cy(), 3, { 255, 240, 200, 255 }, 90, true, 300 );
    if ( e.m_hp <= 0 ) killEnemy( index );
    return true;
}

void World::killEnemy( int index )
{
    Enemy &e = m_enemies[index];
    if ( !e.m_alive ) return;
    e.m_alive = false;
    e.m_frozen = 0;
    ++m_kills;
    m_score += e.m_def->m_score;
    popup( std::to_string( e.m_def->m_score ), e.m_x, e.top() - 4, { 255, 255, 255, 255 } );
    float pan = 0.5f + std::clamp( ( e.m_x - m_hero.m_x ) / 640.0f, -0.5f, 0.5f );
    static const char *die[] = { "robot_die", "creature_die", "ice_die", "gloam_die" };
    sfx( die[(int)e.m_def->m_family], 0.8f, 1.0f + GetRandomValue( -5, 5 ) * 0.01f, pan );
    bool  big = e.m_def->m_w * e.m_def->m_h > 1400;
    effect( big ? "explode_m" : "explode_s", e.m_x, e.cy() );
    static const Color debris[] = { { 160, 170, 190, 255 }, { 150, 220, 90, 255 }, { 190, 230, 255, 255 }, { 200, 90, 255, 255 } };
    burst( e.m_x, e.cy(), big ? 22 : 12, debris[(int)e.m_def->m_family], 170, false, 700 );
    if ( e.m_parent >= 0 && e.m_parent < (int)m_enemies.size() ) --m_enemies[e.m_parent].m_children;
    ++m_progress->m_kills;
    if ( m_progress->m_kills >= 100 ) grant( AW_KILLS100 );
    if ( m_progress->m_kills >= 500 ) grant( AW_KILLS500 );
    if ( m_progress->m_kills >= 1500 ) grant( AW_KILLS1500 );
    if ( e.m_elite )
    {
        m_score += e.m_def->m_score;
        if ( ++m_progress->m_eliteKills >= 25 ) grant( AW_ELITE25 );
        // A splitting elite falls apart into two small ones.
        if ( e.m_elite == 3 && !e.m_boss )
        {
            std::string id = e.m_def->m_id;
            float       x = e.m_x, y = e.m_y, hp = e.m_hpMax / 5;
            for ( int k = -1; k <= 1; k += 2 )
            {
                int c = spawnEnemy( id, x + k * 14, y, false );
                if ( c < 0 ) continue;
                m_enemies[c].m_hp = m_enemies[c].m_hpMax = std::max( 0.6f, hp );
                m_enemies[c].m_dir = k;
                m_enemies[c].m_vx = k * 120.0f;
                m_enemies[c].m_vy = -300;
                m_enemies[c].m_state = -1;
                ++m_enemiesTotal;
            }
        }
    }
    if ( e.m_boss )
    {
        m_shake = 1.2f;
        m_hitStop = 0.25f;
        sfx( "boss_die" );
        for ( int k = 0; k < 6; ++k )
            effect( "explode_l", e.m_x + GetRandomValue( -40, 40 ), e.cy() + GetRandomValue( -40, 40 ) );
        // The boss's minions go with it.
        for ( Enemy &o : m_enemies )
            if ( o.m_alive && !o.m_boss && o.m_parent == index ) o.m_hp = 0, o.m_alive = false;
        openExitIfDone();
        return;
    }
    m_shake = std::max( m_shake, big ? 0.3f : 0.12f );
    // Sometimes it leaves something behind.
    int roll = GetRandomValue( 0, 99 );
    if ( roll < 18 )
    {
        Pickup p;
        p.m_loose = true;
        p.m_life = 8;
        p.m_x = e.m_x, p.m_y = e.cy();
        p.m_vy = -220;
        bool ammoUseful = false;
        for ( int w = 1; w < WeaponCount; ++w ) ammoUseful |= m_progress->has( (WeaponE)w );
        if ( roll < 7 && ammoUseful ) p.m_kind = PickE::AMMO, p.m_anim = "ammo";
        else if ( roll < 12 )
            p.m_kind = PickE::HEALTH, p.m_anim = "health";
        else
            p.m_kind = PickE::TREASURE, p.m_anim = "gem", p.m_sub = 0;
        m_pickups.push_back( p );
    }
}

void World::explode( float x, float y, float radius, float damage, bool byHero )
{
    effect( radius > 60 ? "explode_l" : "explode_m", x, y );
    float pan = 0.5f + std::clamp( ( x - m_hero.m_x ) / 640.0f, -0.5f, 0.5f );
    sfx( radius > 60 ? "explode_l" : "explode_m", 0.8f, 1, pan );
    m_shake = std::max( m_shake, 0.3f );
    burst( x, y, 16, { 255, 190, 90, 255 }, 220, true, 400 );
    if ( byHero )
    {
        for ( size_t i = 0; i < m_enemies.size(); ++i )
        {
            Enemy &e = m_enemies[i];
            if ( !e.m_alive || e.m_hidden ) continue;
            float dx = std::max( { e.left() - x, 0.0f, x - e.right() } ), dy = std::max( { e.top() - y, 0.0f, y - e.m_y } );
            if ( dx * dx + dy * dy < radius * radius ) hurtEnemy( (int)i, damage, x, WeaponE::MORTAR, true );
        }
        int r = (int)std::ceil( radius / T );
        for ( int cy = (int)( y / T ) - r; cy <= (int)( y / T ) + r; ++cy )
            for ( int cx = (int)( x / T ) - r; cx <= (int)( x / T ) + r; ++cx )
                if ( std::hypot( cx * T + 16 - x, cy * T + 16 - y ) < radius + 8 ) hitCell( cx, cy, 2 );
    }
    else
    {
        float dx = std::max( { m_hero.left() - x, 0.0f, x - m_hero.right() } ), dy = std::max( { m_hero.top() - y, 0.0f, y - m_hero.m_y } );
        if ( dx * dx + dy * dy < radius * radius ) hurtHero( damage, x );
    }
}

void World::hitCell( int cx, int cy, float damage )
{
    if ( !m_level.inside( cx, cy ) ) return;
    size_t i = (size_t)cy * m_level.m_w + cx;
    if ( m_level.at( cx, cy ).m_kind != CellE::BREAKABLE || m_broken[i] >= 2 ) return;
    m_broken[i] = (uint8_t)std::min( 2, m_broken[i] + ( damage >= 2 ? 2 : 1 ) );
    float x = cx * T + 16, y = cy * T + 16;
    if ( m_broken[i] >= 2 )
    {
        sfx( "break", 0.8f );
        burst( x, y, 16, { 170, 150, 130, 255 }, 160, false, 800 );
        effect( "smoke", x, y );
        m_shake = std::max( m_shake, 0.15f );
    }
    else
    {
        sfx( "hit_wall", 0.4f, 0.8f );
        burst( x, y, 4, { 170, 150, 130, 255 }, 80, false, 600 );
    }
}

}   // namespace kepler
