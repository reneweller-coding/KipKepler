/**
 * @file Physics.cpp
 * @brief The hero's movement against the tiles.
 * @author Rene Weller
 */
#include "Physics.h"

#include <algorithm>
#include <cmath>

namespace kepler
{

namespace
{

constexpr float T = 32.0f;
constexpr float Eps = 0.001f;

int cellOf( float p )
{
    return (int)std::floor( p / T );
}

/** @brief Moves along x; stops at solid cells. Returns whether it was blocked. */
bool moveX( const Collider &c, float &x, float y, float w, float h, float dx )
{
    if ( dx == 0 ) return false;
    float nx = x + dx;
    float top = y - h, bottom = y;
    int   r0 = cellOf( top + Eps ), r1 = cellOf( bottom - Eps );
    if ( dx > 0 )
    {
        float edge = nx + w * 0.5f;
        int   col = cellOf( edge - Eps );
        int   was = cellOf( x + w * 0.5f - Eps );
        for ( int cx = was + 1; cx <= col; ++cx )
            for ( int cy = r0; cy <= r1; ++cy )
                if ( c.solid( cx, cy ) )
                {
                    x = cx * T - w * 0.5f;
                    return true;
                }
    }
    else
    {
        float edge = nx - w * 0.5f;
        int   col = cellOf( edge );
        int   was = cellOf( x - w * 0.5f );
        for ( int cx = was - 1; cx >= col; --cx )
            for ( int cy = r0; cy <= r1; ++cy )
                if ( c.solid( cx, cy ) )
                {
                    x = ( cx + 1 ) * T + w * 0.5f;
                    return true;
                }
    }
    x = nx;
    return false;
}

/**
 * @brief Moves along y; lands on solid cells and (from above) one-way platforms. Returns -1 blocked above, 1 landed,
 *        0 free.
 */
int moveY( const Collider &c, float x, float &y, float w, float h, float dy, bool oneways )
{
    if ( dy == 0 ) return 0;
    float ny = y + dy;
    int   c0 = cellOf( x - w * 0.5f + Eps ), c1 = cellOf( x + w * 0.5f - Eps );
    if ( dy > 0 )
    {
        int was = cellOf( y - Eps ), row = cellOf( ny - Eps );
        for ( int cy = was + 1; cy <= row; ++cy )
            for ( int cx = c0; cx <= c1; ++cx )
                if ( c.solid( cx, cy ) || ( oneways && c.oneway( cx, cy ) && y <= cy * T + Eps ) )
                {
                    y = cy * T;
                    return 1;
                }
        float top = 0;
        if ( oneways && c.platformTop( x - w * 0.5f, x + w * 0.5f, y, ny, top ) )
        {
            y = top;
            return 1;
        }
    }
    else
    {
        float headWas = y - h, head = ny - h;
        int   was = cellOf( headWas ), row = cellOf( head );
        for ( int cy = was - 1; cy >= row; --cy )
            for ( int cx = c0; cx <= c1; ++cx )
                if ( c.solid( cx, cy ) )
                {
                    y = ( cy + 1 ) * T + h;
                    return -1;
                }
    }
    y = ny;
    return 0;
}

/** @brief Whether something carries a box standing at y (bottom) right now. */
bool supported( const Collider &c, float x, float y, float w, bool oneways, bool *icy = nullptr )
{
    int  c0 = cellOf( x - w * 0.5f + Eps ), c1 = cellOf( x + w * 0.5f - Eps );
    int  row = cellOf( y + 0.5f );
    bool aligned = std::fabs( y - row * T ) < 0.01f;
    bool any = false;
    if ( aligned )
        for ( int cx = c0; cx <= c1; ++cx )
            if ( c.solid( cx, row ) || ( oneways && c.oneway( cx, row ) ) )
            {
                any = true;
                if ( icy && c.icy( cx, row ) ) *icy = true;
            }
    if ( any ) return true;
    float top = 0;
    if ( oneways && c.platformTop( x - w * 0.5f, x + w * 0.5f, y - 0.5f, y + 0.5f, top ) ) return true;
    return false;
}

float approach( float v, float target, float rate )
{
    return v < target ? std::min( target, v + rate ) : std::max( target, v - rate );
}

}   // namespace

void stepHero( HeroBody &b, const HeroInput &in, const Collider &c, float dt )
{
    b.m_hitWall = b.m_hitHead = b.m_landed = b.m_jumped = false;
    if ( b.m_drop > 0 ) b.m_drop -= dt;
    bool oneways = b.m_drop <= 0;

    // Jump: buffered presses, coyote time, dropping through one-way platforms with down + jump.
    if ( in.m_jumpPressed ) b.m_buffer = phys::Buffer;
    else if ( b.m_buffer > 0 ) b.m_buffer -= dt;
    if ( b.m_ground ) b.m_coyote = phys::Coyote;
    else if ( b.m_coyote > 0 ) b.m_coyote -= dt;
    if ( b.m_buffer > 0 && ( b.m_ground || b.m_coyote > 0 ) )
    {
        bool onOneway = false;
        if ( b.m_ground && in.m_down )
        {
            int  c0 = cellOf( b.left() + Eps ), c1 = cellOf( b.right() - Eps ), row = cellOf( b.m_y + 0.5f );
            bool solidBelow = false;
            for ( int cx = c0; cx <= c1; ++cx )
            {
                if ( c.solid( cx, row ) ) solidBelow = true;
                if ( c.oneway( cx, row ) ) onOneway = true;
            }
            float top = 0;
            if ( c.platformTop( b.left(), b.right(), b.m_y - 0.5f, b.m_y + 0.5f, top ) ) onOneway = true;
            if ( solidBelow ) onOneway = false;
        }
        if ( onOneway )
        {
            b.m_drop = 0.22f;
            oneways = false;
            b.m_ground = false;
            b.m_y += 1.0f;
        }
        else
        {
            b.m_vy = -b.m_jumpSpeed;
            b.m_jumped = true;
            b.m_cut = false;
            b.m_noCut = false;
        }
        b.m_ground = false;
        b.m_coyote = 0;
        b.m_buffer = 0;
    }
    if ( !in.m_jump && b.m_vy < 0 && !b.m_cut && !b.m_noCut )
    {
        b.m_vy *= phys::Cut;
        b.m_cut = true;
    }

    // Running: quick on the ground, a little softer in the air, slow to change on ice.
    float target = in.m_dir * phys::Run;
    float rate;
    if ( b.m_ground && b.m_icy ) rate = ( in.m_dir == 0 ? phys::DecIce : phys::AccIce ) * dt;
    else if ( b.m_ground )
        rate = ( in.m_dir == 0 || in.m_dir * b.m_vx < 0 ? phys::DecGround : phys::AccGround ) * dt;
    else
        rate = phys::AccAir * dt;
    b.m_vx = approach( b.m_vx, target, rate );

    b.m_vy = std::min( phys::FallMax, b.m_vy + b.m_gravity * dt );

    float dx = ( b.m_vx + b.m_pushX ) * dt;
    float x0 = b.m_x;
    if ( moveX( c, b.m_x, b.m_y, phys::HeroW, phys::HeroH, dx ) )
    {
        // Ledge forgiveness: feet just below the top of what blocks them (a few pixels, after running over a narrow
        // gap or onto a low lip) step up onto it instead of stopping.
        float lift = b.m_y - std::floor( ( b.m_y - 0.001f ) / T ) * T;
        bool  stepped = false;
        if ( b.m_vy >= 0 && lift > 0.001f && lift <= 7.0f )
        {
            float y = b.m_y - lift, x = x0;
            bool  free = true;
            int   r0 = cellOf( y - phys::HeroH + Eps ), r1 = cellOf( y - Eps );
            int   c0 = cellOf( x0 + dx - phys::HeroW * 0.5f + Eps ), c1 = cellOf( x0 + dx + phys::HeroW * 0.5f - Eps );
            for ( int cy = r0; cy <= r1 && free; ++cy )
                for ( int cx = c0; cx <= c1 && free; ++cx )
                    if ( c.solid( cx, cy ) ) free = false;
            if ( free && !moveX( c, x, y, phys::HeroW, phys::HeroH, dx ) )
            {
                b.m_x = x, b.m_y = y;
                b.m_vy = 0;
                stepped = true;
            }
        }
        if ( !stepped )
        {
            b.m_hitWall = true;
            b.m_vx = 0;
        }
    }
    bool wasGround = b.m_ground;
    int  hit = moveY( c, b.m_x, b.m_y, phys::HeroW, phys::HeroH, b.m_vy * dt, oneways );
    if ( hit < 0 )
    {
        b.m_vy = 0;
        b.m_hitHead = true;
    }
    if ( hit > 0 ) b.m_vy = 0;
    b.m_icy = false;
    b.m_ground = b.m_vy >= 0 && supported( c, b.m_x, b.m_y, phys::HeroW, oneways, &b.m_icy );
    if ( b.m_ground ) b.m_vy = 0;
    b.m_landed = b.m_ground && !wasGround;
}

void moveBox( const Collider &c, float &x, float &y, float w, float h, float &vx, float &vy, float dt, bool oneways,
              bool &ground, bool &wall )
{
    wall = moveX( c, x, y, w, h, vx * dt );
    if ( wall ) vx = 0;
    int hit = moveY( c, x, y, w, h, vy * dt, oneways );
    if ( hit != 0 ) vy = 0;
    ground = vy >= 0 && supported( c, x, y, w, oneways );
}

}   // namespace kepler
