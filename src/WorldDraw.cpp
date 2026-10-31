/**
 * @file WorldDraw.cpp
 * @brief Drawing a level: parallax, tiles, decorations, objects, pickups, enemies, the hero, shots and effects into
 *        the screen's layers, the lights, and the HUD.
 * @author Rene Weller
 */
#include "Assets.h"
#include "Input.h"
#include "Screen.h"
#include "Text.h"
#include "World.h"

#include <algorithm>
#include <cmath>

namespace kepler
{

namespace
{

constexpr float T = (float)Tile;

void tileAt( const Texture2D &tex, int index, float x, float y, Color tint = WHITE, bool flipX = false )
{
    if ( !tex.id ) return;
    int cols = std::max( 1, tex.width / Tile );
    int rows = std::max( 1, tex.height / Tile );
    index %= cols * rows;
    Rectangle src = { (float)( index % cols ) * T, (float)( index / cols ) * T, flipX ? -T : T, T };
    DrawTextureRec( tex, src, { x, y }, tint );
}

Color colourOf( unsigned rgb, unsigned char a = 255 )
{
    return { (unsigned char)( rgb >> 16 ), (unsigned char)( rgb >> 8 ), (unsigned char)rgb, a };
}

/** @brief The light colour of a theme's liquid. */
Color liquidLight( const std::string &theme )
{
    if ( theme == "foundry" ) return { 255, 120, 40, 255 };
    if ( theme == "jungle" ) return { 120, 255, 90, 255 };
    if ( theme == "hive" ) return { 255, 180, 60, 255 };
    if ( theme == "ice" ) return { 120, 200, 255, 255 };
    if ( theme == "crystal" ) return { 190, 120, 255, 255 };
    if ( theme == "citadel" ) return { 230, 60, 255, 255 };
    return { 80, 220, 255, 255 };
}

}   // namespace

void World::drawBackground( Screen &s )
{
    using kepler::drawBackground;
    const Background &bg = assets().background( m_bgName );
    float             maxY = std::max( 0.0f, m_level.m_h * T - m_vh );
    DrawRectangleGradientV( 0, 0, s.m_w, s.m_h, bg.m_top, bg.m_bottom );
    if ( bg.m_standIn )
    {
        // Stars for a background that is not painted yet.
        for ( int i = 0; i < 160; ++i )
        {
            float x = std::fmod( i * 97.0f - m_camX * 0.05f + 4000, (float)s.m_w ), y = std::fmod( i * 53.0f - m_camY * 0.03f + 4000, (float)s.m_h );
            DrawPixel( (int)x, (int)y, i % 7 == 0 ? Color{ 255, 255, 255, 255 } : Color{ 120, 130, 170, 255 } );
        }
        return;
    }
    drawBackground( bg, s.m_w, s.m_h, m_camX, maxY - m_camY, m_clock, false );
}

void World::drawTiles( Screen &s, int layer )
{
    const TileSet &ts = assets().tiles( m_theme );
    const Level   &L = m_level;
    Color          tint = ts.m_tints[m_tint];
    int            x0 = std::max( 0, (int)std::floor( m_camX / T ) - 1 ), x1 = std::min( L.m_w - 1, (int)std::floor( ( m_camX + s.m_w ) / T ) + 1 );
    int            y0 = std::max( 0, (int)std::floor( m_camY / T ) - 1 ), y1 = std::min( L.m_h - 1, (int)std::floor( ( m_camY + s.m_h ) / T ) + 1 );
    int            cx0 = (int)std::floor( m_camX ), cy0 = (int)std::floor( m_camY );
    bool           glow = layer == 1;
    int            nA = TileSet::variants( ts.m_terrainA ), nB = TileSet::variants( ts.m_terrainB ), nBack = TileSet::variants( ts.m_back );

    // Back walls.
    const Texture2D &back = glow ? ts.m_backGlow : ts.m_back;
    for ( int y = y0; y <= y1; ++y )
        for ( int x = x0; x <= x1; ++x )
        {
            const Cell &c = L.at( x, y );
            if ( !c.m_interior ) continue;
            size_t i = (size_t)y * L.m_w + x;
            int    v = m_variant[i] % nBack;
            tileAt( back, v * 256 + m_maskBack[i], x * T - cx0, y * T - cy0, glow ? WHITE : ColorBrightness( tint, -0.05f ) );
        }
    // Decorations on the back walls.
    const Texture2D &deco = glow ? ts.m_decoGlow : ts.m_deco;
    if ( deco.id )
        for ( const DecoPlace &p : m_decoList )
        {
            const Deco &d = ts.m_decos[p.m_index];
            if ( p.m_x + d.m_src.width < m_camX || p.m_x > m_camX + s.m_w || p.m_y + d.m_src.height < m_camY || p.m_y > m_camY + s.m_h ) continue;
            DrawTextureRec( deco, d.m_src, { std::floor( p.m_x ) - cx0, std::floor( p.m_y ) - cy0 }, glow ? WHITE : tint );
        }
    // Terrain: all of A, then all of B (one texture at a time keeps the draw calls few, which the Deck's battery
    // likes).
    for ( int pass = 0; pass < 2; ++pass )
    {
        const Texture2D &tex = pass == 0 ? ( glow ? ts.m_terrainAGlow : ts.m_terrainA ) : ( glow ? ts.m_terrainBGlow : ts.m_terrainB );
        if ( !tex.id ) continue;
        int variants = pass == 0 ? nA : nB;
        for ( int y = y0; y <= y1; ++y )
            for ( int x = x0; x <= x1; ++x )
            {
                CellE  k = L.at( x, y ).m_kind;
                bool   mine = pass == 0 ? ( k == CellE::TERRAIN_A || k == CellE::FAKE ) : k == CellE::TERRAIN_B;
                if ( !mine ) continue;
                size_t i = (size_t)y * L.m_w + x;
                tileAt( tex, ( m_variant[i] % variants ) * 256 + m_maskTerrain[i], x * T - cx0, y * T - cy0, glow ? WHITE : tint );
            }
    }
    // Platforms, blocks, hazards, liquids.
    const Texture2D &blocks = glow ? ts.m_blocksGlow : ts.m_blocks;
    for ( int y = y0; y <= y1; ++y )
        for ( int x = x0; x <= x1; ++x )
        {
            const Cell &c = L.at( x, y );
            size_t      i = (size_t)y * L.m_w + x;
            float       px = x * T - cx0, py = y * T - cy0;
            int         row = -1, col = 0;
            bool        flip = false;
            switch ( c.m_kind )
            {
            case CellE::PLATFORM:
            {
                if ( glow ) break;
                bool l = L.at( x - 1, y ).m_kind == CellE::PLATFORM, r = L.at( x + 1, y ).m_kind == CellE::PLATFORM;
                int  piece = l && r ? 2 : l ? 3 : r ? 1 : 0;
                if ( ts.m_platform.id )
                    tileAt( ts.m_platform, ( m_variant[i] % std::max( 1, ts.m_platform.height / Tile ) ) * 4 + piece, px, py, tint );
                else
                    DrawRectangle( (int)px, (int)py, Tile, 8, { 200, 180, 90, 255 } );
                break;
            }
            case CellE::BREAKABLE:
                if ( m_broken[i] < 2 ) row = 0, col = m_broken[i];
                break;
            case CellE::CRUMBLE:
                if ( m_broken[i] == 0 ) row = 1, col = 0;
                else if ( m_broken[i] == 1 )
                    row = 1, col = m_crumbleT[i] > 0.25f ? 1 : 2;
                break;
            case CellE::DOOR_BLUE:
            case CellE::DOOR_GOLD:
                if ( !m_doorOpen[i] ) row = c.m_kind == CellE::DOOR_BLUE ? 2 : 3, col = 0;
                break;
            case CellE::TOGGLE: row = solid( x, y ) ? 4 : 5, col = (int)( m_clock * 8 ) % 4; break;
            case CellE::CONVEYOR:
                row = 6, col = (int)( m_clock * 10 ) % 4;
                flip = !c.m_aux;
                break;
            case CellE::SPIKE_UP: row = 7, col = 0; break;
            case CellE::SPIKE_DOWN: row = 7, col = 1; break;
            case CellE::SPIKE_LEFT: row = 7, col = 2; break;
            case CellE::SPIKE_RIGHT: row = 7, col = 3; break;
            case CellE::LIQUID:
            {
                const Texture2D &liq = glow ? ts.m_liquidGlow : ts.m_liquid;
                bool             surface = L.at( x, y - 1 ).m_kind != CellE::LIQUID;
                int              frame = (int)( m_clock * 6 + x * 0.5f ) % 4;
                if ( liq.id ) tileAt( liq, ( surface ? 0 : 4 ) + frame, px, py, glow ? WHITE : tint );
                else if ( !glow )
                    DrawRectangle( (int)px, (int)py + ( surface ? 6 : 0 ), Tile, Tile - ( surface ? 6 : 0 ), Fade( liquidLight( m_theme ), 0.8f ) );
                break;
            }
            default: break;
            }
            if ( row < 0 ) continue;
            if ( blocks.id ) tileAt( blocks, row * ( blocks.width / Tile ) + col, px, py, glow ? WHITE : tint, flip );
            else if ( !glow )
            {
                static const Color stand[8] = { { 170, 130, 90, 255 }, { 140, 110, 70, 255 }, { 50, 90, 240, 255 }, { 240, 190, 40, 255 },
                                                { 40, 210, 210, 255 }, { 40, 210, 210, 70 }, { 110, 110, 70, 255 }, { 220, 60, 60, 255 } };
                DrawRectangle( (int)px + 1, (int)py + 1, Tile - 2, Tile - 2, stand[row] );
            }
        }
}

void World::draw( Screen &s )
{
    float shakeX = m_shake > 0 ? GetRandomValue( -100, 100 ) * 0.01f * m_shake * 6 : 0;
    float shakeY = m_shake > 0 ? GetRandomValue( -100, 100 ) * 0.01f * m_shake * 6 : 0;
    float camX = m_camX, camY = m_camY;
    m_camX = std::floor( m_camX + shakeX );
    m_camY = std::floor( m_camY + shakeY );
    float amb = 1.0f - m_dark;
    Color ambient = { (unsigned char)( 255 * amb ), (unsigned char)( 255 * std::min( 1.0f, amb * 1.02f ) ), (unsigned char)( 255 * std::min( 1.0f, amb * 1.1f ) ), 255 };
    s.clear( ambient );
    int cx0 = (int)m_camX, cy0 = (int)m_camY;
    auto sx = [&]( float x ) { return std::floor( x ) - cx0; };
    auto sy = [&]( float y ) { return std::floor( y ) - cy0; };
    auto visible = [&]( float x, float y, float r ) { return x + r > m_camX && x - r < m_camX + s.m_w && y + r > m_camY && y - r < m_camY + s.m_h; };

    s.begin( LayerE::BACKGROUND );
    drawBackground( s );
    s.end();

    const Sheet &items = assets().sheet( "items" );
    const Sheet &objects = assets().sheet( "objects" );
    const Sheet &shots = assets().sheet( "shots" );
    const Sheet &fx = assets().sheet( "fx" );
    const Sheet &hero = assets().sheet( "hero" );

    // Both the world and the glow layer draw the same things: the glow uses the emissive masks.
    for ( int pass = 0; pass < 2; ++pass )
    {
        bool glow = pass == 1;
        s.begin( glow ? LayerE::GLOW : LayerE::WORLD );
        if ( glow )
        {
            // The background's lights glow too, gently.
            const Background &bg = assets().background( m_bgName );
            kepler::drawBackground( bg, s.m_w, s.m_h, m_camX, std::max( 0.0f, m_level.m_h * T - m_vh ) - m_camY, m_clock, true );
        }
        drawTiles( s, pass );
        // Movers.
        const TileSet &ts = assets().tiles( m_theme );
        for ( const Mover &m : m_movers )
        {
            if ( !visible( m.m_x + m.m_w * 16, m.m_y, m.m_w * 32 ) ) continue;
            for ( int k = 0; k < m.m_w; ++k )
            {
                int piece = m.m_w == 1 ? 0 : k == 0 ? 1 : k == m.m_w - 1 ? 3 : 2;
                if ( glow ) DrawRectangle( (int)sx( m.m_x + k * T ) + 4, (int)sy( m.m_y ) + 9, Tile - 8, 1, { 80, 200, 255, 255 } );
                else if ( ts.m_platform.id )
                    tileAt( ts.m_platform, piece, sx( m.m_x + k * T ), sy( m.m_y ), ts.m_tints[m_tint] );
                else
                    DrawRectangle( (int)sx( m.m_x + k * T ), (int)sy( m.m_y ), Tile, 10, { 200, 200, 120, 255 } );
            }
        }
        // Objects.
        for ( const Object &o : m_objects )
        {
            if ( !visible( o.m_x, o.m_y - 48, 96 ) ) continue;
            std::string anim;
            if ( o.m_kind == "exit" ) anim = m_exitOpen ? "exit_open" : "exit_closed";
            else if ( o.m_kind == "checkpoint" )
                anim = o.m_on ? "checkpoint_on" : "checkpoint_off";
            else if ( o.m_kind == "teleport" )
                anim = "teleporter";
            else if ( o.m_kind == "switch" )
                anim = o.m_on ? "switch_on" : "switch_off";
            else if ( o.m_kind == "spring" )
                anim = o.m_on ? "spring_fire" : "spring";
            else if ( o.m_kind == "sign" )
                anim = "sign";
            else if ( o.m_kind == "warp" )
                anim = assets().sheet( "objects" ).anim( "warp" ) ? "warp" : "exit_open";
            if ( o.m_kind == "laser" )
            {
                // Vertical emitters stand on the floor (or hang from the ceiling, turned over); horizontal ones sit
                // on the wall they fire away from.
                bool  vertical = !o.m_args.empty() && o.m_args[0] == "v";
                bool  ceiling = vertical && solid( o.m_cx, o.m_cy - 1 );
                bool  flip = !vertical && !solid( o.m_cx - 1, o.m_cy );
                float wallX = flip ? o.m_x + 16 : o.m_x - 16;
                std::string a = vertical ? ( o.m_on ? "laser_emitter" : "laser_emitter_off" ) : "laser_emitter_side";
                if ( vertical )
                    objects.draw( objects.frame( a, o.m_t ), sx( o.m_x ), sy( ceiling ? o.m_y - T : o.m_y ), false, WHITE, glow, ceiling ? 180.0f : 0 );
                else
                    objects.draw( objects.frame( a, o.m_t ), sx( wallX + ( flip ? -16 : 16 ) ), sy( o.m_y ), flip, WHITE, glow );
            }
            else if ( !anim.empty() )
                objects.draw( objects.frame( anim, o.m_t ), sx( o.m_x ), sy( o.m_y ), false, WHITE, glow );
            if ( o.m_kind == "laser" && o.m_on )
            {
                bool vertical = !o.m_args.empty() && o.m_args[0] == "v";
                int  dx = 0, dy = 0;
                if ( vertical ) dy = solid( o.m_cx, o.m_cy - 1 ) ? 1 : -1;
                else
                    dx = solid( o.m_cx - 1, o.m_cy ) ? 1 : -1;
                Vector2 a = { sx( o.m_cx * T + 16 ), sy( o.m_cy * T + 16 ) };
                Vector2 b = { a.x + dx * ( o.m_target + 0.5f ) * T, a.y + dy * ( o.m_target + 0.5f ) * T };
                float   flick = 0.7f + 0.3f * std::sin( m_clock * 40 );
                DrawLineEx( a, b, glow ? 5.0f : 3.0f, glow ? Color{ (unsigned char)( 255 * flick ), 40, 60, 255 } : Color{ 255, 90, 90, 255 } );
                DrawLineEx( a, b, 1.0f, { 255, 230, 230, 255 } );
            }
            if ( o.m_kind == "crusher" )
            {
                float reach = ( o.m_args.size() > 0 ? (float)atof( o.m_args[0].c_str() ) : 3 ) * T;
                float d = o.m_target / 1000.0f * reach;
                float l = sx( o.m_cx * T ), t = sy( o.m_cy * T );
                if ( !glow )
                {
                    DrawRectangle( (int)l + 12, (int)t, 8, (int)( d + 8 ), { 70, 74, 90, 255 } );
                    DrawRectangle( (int)l + 2, (int)( t + d ), Tile - 4, 22, { 120, 124, 140, 255 } );
                    DrawRectangle( (int)l + 2, (int)( t + d ), Tile - 4, 3, { 190, 196, 210, 255 } );
                    for ( int k = 0; k < 4; ++k ) DrawTriangle( { l + 3 + k * 7.0f, t + d + 22 }, { l + 6.5f + k * 7.0f, t + d + 29 }, { l + 10 + k * 7.0f, t + d + 22 }, { 200, 200, 215, 255 } );
                }
                else
                    DrawRectangle( (int)l + 4, (int)( t + d + 10 ), Tile - 8, 2, { 255, 120, 40, 255 } );
            }
        }
        // Pickups.
        for ( const Pickup &p : m_pickups )
        {
            if ( p.m_taken || !visible( p.m_x, p.m_y, 32 ) ) continue;
            if ( p.m_loose && p.m_life < 2 && (int)( p.m_life * 10 ) % 2 ) continue;
            float bob = p.m_loose ? 0 : std::sin( p.m_t * 3.0f ) * 2.0f;
            items.draw( items.frame( p.m_anim, p.m_t ), sx( p.m_x ), sy( p.m_y + bob ), false, WHITE, glow );
            if ( glow && !items.m_hasGlow && p.m_kind == PickE::CRYSTAL ) DrawCircle( (int)sx( p.m_x ), (int)sy( p.m_y + bob ), 3, { 100, 220, 255, 255 } );
        }
        // Enemies.
        for ( const Enemy &e : m_enemies )
        {
            if ( !e.m_alive || e.m_hidden || !visible( e.m_x, e.cy(), 160 ) ) continue;
            const Sheet &sh = assets().sheet( e.m_def->m_id );
            int          fr = sh.frame( e.m_anim, e.m_animT );
            bool         flip = e.m_dir < 0;
            bool         hung = e.m_upsideDown || ( e.m_ceiling && ( e.m_def->m_brain == BrainE::TURRET || e.m_def->m_brain == BrainE::BEAMER ) );
            float        y = hung ? e.top() : e.m_y, rot = hung ? 180.0f : 0.0f;
            if ( e.m_state == -1 && ( (int)( e.m_stateT * 20 ) % 2 ) ) continue;
            // A sniper's aim: a thin line from its muzzle, following the hero, then held (blinking) before the shot.
            if ( e.m_def->m_brain == BrainE::SNIPER && e.m_state == 1 )
            {
                Vector2 m = sh.point( "muzzle", { e.m_def->m_w * 0.5f, -e.m_def->m_h * 0.6f } );
                Vector2 a = { sx( e.m_x + m.x * e.m_dir ), sy( e.m_y + m.y ) }, b = { sx( e.m_aimX ), sy( e.m_aimY ) };
                bool    held = e.m_stateT >= 0.75f;
                if ( !held || (int)( e.m_stateT * 24 ) % 2 == 0 )
                    DrawLineEx( a, b, glow ? 2.0f : 1.0f,
                                glow   ? Color{ 255, 70, 70, 255 }
                                : held ? Color{ 255, 90, 90, 240 }
                                       : Color{ 255, 140, 140, 150 } );
            }
            if ( sh.m_standIn && !glow )
            {
                DrawRectangle( (int)sx( e.left() ), (int)sy( e.top() ), e.m_def->m_w, e.m_def->m_h, e.m_boss ? Color{ 200, 60, 200, 255 } : Color{ 220, 90, 60, 255 } );
                DrawRectangle( (int)sx( e.m_x + e.m_dir * e.m_def->m_w * 0.25f ) - 2, (int)sy( e.top() + 6 ), 4, 4, { 255, 255, 120, 255 } );
                continue;
            }
            if ( glow )
            {
                sh.draw( fr, sx( e.m_x ), sy( y ), flip, WHITE, true, rot );
                if ( e.m_elite )
                {
                    // Elites glow around their edge in the colour of their gift.
                    static const Color elite[6] = { {}, { 255, 200, 60, 255 }, { 80, 255, 140, 255 }, { 255, 80, 200, 255 }, { 80, 180, 255, 255 },
                                                    { 255, 90, 70, 255 } };
                    Color c = ColorAlpha( elite[e.m_elite], 0.55f + 0.25f * std::sin( m_clock * 6 ) );
                    for ( auto [ox, oy] : { std::pair{ -1, 0 }, { 1, 0 }, { 0, -1 }, { 0, 1 } } )
                        sh.draw( fr, sx( e.m_x ) + ox, sy( y ) + oy, flip, c, false, rot );
                }
                if ( e.m_flash > 0 ) sh.draw( fr, sx( e.m_x ), sy( y ), flip, { 180, 180, 180, 255 }, false, rot );
                if ( e.m_frozen > 0 )
                    DrawRectangleLines( (int)sx( e.left() ) - 2, (int)sy( e.top() ) - 2, e.m_def->m_w + 4, e.m_def->m_h + 4, { 120, 200, 255, 255 } );
                continue;
            }
            // A dropper away from its perch hangs on its vine.
            if ( e.m_def->m_brain == BrainE::DROPPER && e.m_y > e.m_homeY + 2 )
            {
                float top = e.m_homeY - e.m_def->m_h;
                DrawLineEx( { sx( e.m_x ), sy( top ) }, { sx( e.m_x ), sy( e.top() + 4 ) }, 2, { 40, 90, 50, 255 } );
                DrawLineEx( { sx( e.m_x ) - 1, sy( top ) }, { sx( e.m_x ) - 1, sy( e.top() + 4 ) }, 1, { 90, 160, 80, 255 } );
            }
            Color tint = e.m_frozen > 0 ? Color{ 150, 210, 255, 255 } : WHITE;
            sh.draw( fr, sx( e.m_x ), sy( y ), flip, tint, false, rot );
            if ( e.m_frozen > 0 )
                DrawRectangle( (int)sx( e.left() ) - 2, (int)sy( e.top() ) - 2, e.m_def->m_w + 4, e.m_def->m_h + 4, { 170, 230, 255, 110 } );
        }
        // The best run's ghost (time trials): the hero's frame where he was then, see-through.
        if ( m_ghost && !glow && !hero.m_standIn )
        {
            size_t gi = (size_t)( m_time * 30 );
            if ( gi < m_ghost->size() )
            {
                const TrackPoint &g = ( *m_ghost )[gi];
                if ( visible( g.m_x, g.m_y - 24, 48 ) )
                    hero.draw( g.m_frame, sx( g.m_x ), sy( g.m_y ), g.m_face < 0, { 150, 220, 255, 110 } );
            }
        }
        // The hero.
        bool blink = m_hurtT > 0 && !m_dead && ( (int)( m_hurtT * 16 ) % 2 );
        if ( !blink && !( m_exitT > 0.9f ) )
        {
            if ( hero.m_standIn && !glow )
            {
                DrawRectangle( (int)sx( m_hero.left() ), (int)sy( m_hero.top() ), (int)phys::HeroW, (int)phys::HeroH, { 240, 140, 40, 255 } );
                DrawRectangle( (int)sx( m_hero.m_x + m_face * 2 ) - 5, (int)sy( m_hero.top() + 6 ), 10, 8, { 90, 230, 255, 255 } );
            }
            else
                hero.draw( hero.frame( m_anim, m_animT ), sx( m_hero.m_x ), sy( m_hero.m_y ), m_face < 0, WHITE, glow );
            if ( m_weapon == WeaponE::BLASTER && m_charge > 0.25f )
            {
                // Energy gathers at the muzzle while the blaster charges.
                Vector2 mz = m_aimUp ? hero.point( "muzzle_up", { 4, -54 } ) : hero.point( "muzzle", { 22, -26 } );
                float   mx = sx( m_hero.m_x + mz.x * m_face ), my = sy( m_hero.m_y + mz.y );
                float   full = std::min( 1.0f, ( m_charge - 0.25f ) / 0.8f );
                if ( !fx.m_standIn ) fx.draw( fx.frame( "charge", m_charge ), mx, my, m_face < 0, glow ? WHITE : Color{ 255, 255, 255, 255 }, glow && fx.m_hasGlow );
                else if ( glow )
                    DrawCircle( (int)mx, (int)my, 2 + 4 * full, ColorAlpha( { 120, 230, 255, 255 }, 0.5f + 0.5f * std::sin( m_clock * 30 ) ) );
            }
        }
        if ( m_shield > 0 && glow && ( m_shield > 2 || (int)( m_shield * 8 ) % 2 ) )
            DrawCircleLines( (int)sx( m_hero.m_x ), (int)sy( m_hero.m_y - 22 ), 28 + std::sin( m_clock * 6 ), { 120, 220, 255, 255 } );
        // Shots.
        for ( const Shot &sh : m_shots )
        {
            if ( !visible( sh.m_x, sh.m_y, 32 ) ) continue;
            float ang = std::atan2( sh.m_vy, sh.m_vx ) * RAD2DEG;
            if ( sh.m_anim == "disc" || sh.m_anim == "mortar" || sh.m_anim == "grenade" || sh.m_anim == "acid" ) ang = 0;
            if ( shots.m_standIn )
            {
                Color c = sh.m_enemy ? Color{ 255, 80, 60, 255 } : colourOf( weapon( sh.m_weapon ).m_colour );
                DrawCircle( (int)sx( sh.m_x ), (int)sy( sh.m_y ), sh.m_charged ? 6.0f : 3.0f, c );
                continue;
            }
            int fr = shots.frame( sh.m_anim, sh.m_t );
            shots.draw( fr, sx( sh.m_x ), sy( sh.m_y ), false, WHITE, false, ang );
            if ( glow && !shots.m_hasGlow ) shots.draw( fr, sx( sh.m_x ), sy( sh.m_y ), false, { 160, 160, 160, 255 }, false, ang );
            else if ( glow )
                shots.draw( fr, sx( sh.m_x ), sy( sh.m_y ), false, WHITE, true, ang );
        }
        // Beams.
        for ( const Beam &b : m_beams )
        {
            float f = 1.0f - b.m_t / b.m_life;
            for ( size_t k = 1; k < b.m_points.size(); ++k )
            {
                Vector2 a = { sx( b.m_points[k - 1].x ), sy( b.m_points[k - 1].y ) }, c = { sx( b.m_points[k].x ), sy( b.m_points[k].y ) };
                if ( b.m_arc )
                {
                    // Jagged lightning: a few kinks across the segment.
                    Vector2 p = a;
                    int     n = std::max( 2, (int)( std::hypot( c.x - a.x, c.y - a.y ) / 10 ) );
                    for ( int j = 1; j <= n; ++j )
                    {
                        float   t = (float)j / n;
                        Vector2 q = { a.x + ( c.x - a.x ) * t + ( j < n ? GetRandomValue( -4, 4 ) : 0 ), a.y + ( c.y - a.y ) * t + ( j < n ? GetRandomValue( -4, 4 ) : 0 ) };
                        DrawLineEx( p, q, glow ? 3.0f : 1.0f, glow ? b.m_c : Color{ 230, 240, 255, 255 } );
                        p = q;
                    }
                }
                else
                {
                    DrawLineEx( a, c, ( glow ? 7.0f : 4.0f ) * f, glow ? b.m_c : ColorBrightness( b.m_c, 0.3f ) );
                    DrawLineEx( a, c, 2.0f * f, { 255, 255, 255, 255 } );
                }
            }
        }
        // Effects and particles.
        for ( const Effect &e : m_effects )
        {
            if ( !visible( e.m_x, e.m_y, 64 ) ) continue;
            if ( fx.m_standIn )
            {
                float r = 4 + e.m_t * 40;
                if ( glow ) DrawCircleLines( (int)sx( e.m_x ), (int)sy( e.m_y ), r, { 255, 200, 120, 255 } );
                continue;
            }
            int fr = fx.frame( e.m_anim, e.m_t );
            fx.draw( fr, sx( e.m_x ), sy( e.m_y ), e.m_flip, e.m_tint, false, e.m_angle );
            if ( glow ) fx.draw( fr, sx( e.m_x ), sy( e.m_y ), e.m_flip, fx.m_hasGlow ? WHITE : Color{ 150, 150, 150, 255 }, fx.m_hasGlow, e.m_angle );
        }
        for ( const Particle &p : m_particles )
        {
            if ( glow && !p.m_glow ) continue;
            Color c = p.m_c;
            if ( glow ) c = ColorBrightness( c, -0.2f );
            DrawRectangle( (int)sx( p.m_x ), (int)sy( p.m_y ), p.m_size, p.m_size, c );
        }
        // Colour help: shapes on keys and doors (blue a square, gold a triangle), warning stripes where laser fences
        // and crushers are about to hurt.
        if ( !glow && m_colourAssist )
        {
            auto shape = [&]( float x, float y, bool gold )
            {
                if ( gold )
                {
                    DrawTriangle( { x, y - 6 }, { x - 6, y + 5 }, { x + 6, y + 5 }, { 20, 16, 30, 255 } );
                    DrawTriangle( { x, y - 4 }, { x - 4, y + 3 }, { x + 4, y + 3 }, { 255, 255, 255, 255 } );
                }
                else
                {
                    DrawRectangle( (int)x - 5, (int)y - 5, 10, 10, { 20, 16, 30, 255 } );
                    DrawRectangle( (int)x - 3, (int)y - 3, 6, 6, { 255, 255, 255, 255 } );
                }
            };
            int c0 = std::max( 0, (int)std::floor( m_camX / T ) ),
                c1 = std::min( m_level.m_w - 1, (int)std::floor( ( m_camX + s.m_w ) / T ) );
            int r0 = std::max( 0, (int)std::floor( m_camY / T ) ),
                r1 = std::min( m_level.m_h - 1, (int)std::floor( ( m_camY + s.m_h ) / T ) );
            for ( int y = r0; y <= r1; ++y )
                for ( int x = c0; x <= c1; ++x )
                {
                    CellE k = m_level.at( x, y ).m_kind;
                    if ( ( k == CellE::DOOR_BLUE || k == CellE::DOOR_GOLD ) &&
                         !m_doorOpen[(size_t)y * m_level.m_w + x] )
                        shape( sx( x * T + T * 0.5f ), sy( y * T + T * 0.5f ), k == CellE::DOOR_GOLD );
                }
            for ( const Pickup &p : m_pickups )
                if ( !p.m_taken && ( p.m_kind == PickE::KEY_BLUE || p.m_kind == PickE::KEY_GOLD ) &&
                     visible( p.m_x, p.m_y, 32 ) )
                    shape( sx( p.m_x ), sy( p.m_y - 22 ), p.m_kind == PickE::KEY_GOLD );
            for ( const Object &o : m_objects )
            {
                if ( ( o.m_kind != "laser" && o.m_kind != "crusher" ) || !visible( o.m_x, o.m_y, 400 ) ) continue;
                float box[4];
                bool  now = hazard( o, o.m_t, box ), soon = !now && hazard( o, o.m_t + 0.6f, box );
                if ( !now && !soon ) continue;
                float l = sx( box[0] ), t = sy( box[1] ), w = box[2] - box[0], h = box[3] - box[1];
                BeginScissorMode( (int)l, (int)t, (int)std::ceil( w ), (int)std::ceil( h ) );
                for ( float d = -h; d < w; d += 12 )
                    DrawLineEx( { l + d, t + h }, { l + d + h, t }, 4,
                                now ? Color{ 255, 220, 40, 150 } : Color{ 255, 220, 40, 60 } );
                EndScissorMode();
                DrawRectangleLinesEx( { l, t, w, h }, 1,
                                      now ? Color{ 255, 230, 60, 255 } : Color{ 255, 230, 60, 140 } );
            }
        }
        // The foreground silhouettes, in front of everything (they hide their glow layer's light too).
        if ( !glow ) drawForeground( assets().background( m_bgName ), s.m_w, s.m_h, m_camX, m_camY - m_camYSmooth );
        s.end();
    }

    // Light.
    s.begin( LayerE::LIGHT );
    auto lamp = [&]( float x, float y, float r, Color c, float k ) { if ( visible( x, y, r ) ) s.light( sx( x ), sy( y ), r, c, k ); };
    lamp( m_hero.m_x, m_hero.m_y - 24, 120, { 255, 240, 220, 255 }, 0.55f + 0.5f * m_dark );
    for ( const Light &l : m_lights )
    {
        float k = 1.0f - ( l.m_flicker > 0 ? l.m_flicker * ( std::sin( m_clock * 23 + l.m_x ) > 0.7f ? 1.0f : 0.0f ) : 0 );
        lamp( l.m_x, l.m_y, l.m_r, l.m_c, k );
    }
    for ( const Shot &sh : m_shots )
        lamp( sh.m_x, sh.m_y, sh.m_charged ? 70.0f : 40.0f, sh.m_enemy ? Color{ 255, 90, 70, 255 } : colourOf( weapon( sh.m_weapon ).m_colour ), 0.8f );
    for ( const Pickup &p : m_pickups )
        if ( !p.m_taken && p.m_kind == PickE::CRYSTAL ) lamp( p.m_x, p.m_y, 44, { 120, 220, 255, 255 }, 0.6f );
    for ( const Effect &e : m_effects )
        if ( e.m_anim.rfind( "explode", 0 ) == 0 ) lamp( e.m_x, e.m_y, 110, { 255, 170, 80, 255 }, 1.4f * std::max( 0.0f, 1 - e.m_t * 1.5f ) );
    for ( const Beam &b : m_beams )
        for ( const Vector2 &p : b.m_points ) lamp( p.x, p.y, 70, b.m_c, 0.8f );
    for ( const Object &o : m_objects )
    {
        if ( o.m_kind == "exit" ) lamp( o.m_x, o.m_y - 48, m_exitOpen ? 120.0f : 60.0f, m_exitOpen ? Color{ 200, 140, 255, 255 } : Color{ 120, 120, 160, 255 }, 1 );
        if ( o.m_kind == "checkpoint" && o.m_on ) lamp( o.m_x, o.m_y - 70, 80, { 120, 255, 190, 255 }, 0.9f );
        if ( o.m_kind == "teleport" ) lamp( o.m_x, o.m_y - 20, 60, { 120, 200, 255, 255 }, 0.7f );
        if ( o.m_kind == "laser" && o.m_on ) lamp( o.m_x, o.m_y - 16, 70, { 255, 60, 60, 255 }, 0.8f );
    }
    {
        // Glowing liquids light their surroundings.
        Color lc = liquidLight( m_theme );
        int   x0 = std::max( 0, (int)( m_camX / T ) - 2 ), x1 = std::min( m_level.m_w - 1, (int)( ( m_camX + s.m_w ) / T ) + 2 );
        int   y0 = std::max( 0, (int)( m_camY / T ) - 2 ), y1 = std::min( m_level.m_h - 1, (int)( ( m_camY + s.m_h ) / T ) + 2 );
        // Every third surface cell, gently: the lamps add up along a long pool.
        for ( int y = y0; y <= y1; ++y )
            for ( int x = x0 - x0 % 3; x <= x1; x += 3 )
                if ( m_level.at( x, y ).m_kind == CellE::LIQUID && m_level.at( x, y - 1 ).m_kind != CellE::LIQUID )
                    lamp( x * T + 16, y * T + 4, 60, lc, 0.32f );
    }
    s.end();
    m_camX = camX, m_camY = camY;
}

void World::drawHud( Screen &s )
{
    s.begin( LayerE::HUD );
    const PixelFont &font = assets().font( false );
    const PixelFont &big = assets().font( true, true );
    const Sheet     &hud = assets().sheetIn( "ui", "hud" );
    auto             icon = [&]( const char *name, float x, float y, Color tint = WHITE )
    {
        if ( hud.m_standIn ) DrawRectangle( (int)x + 4, (int)y + 4, 8, 8, tint );
        else
            hud.draw( hud.frame( name, m_clock ), x + hud.m_ax, y + hud.m_ay, false, tint );
    };
    auto text = [&]( const std::string &t, float x, float y, Color c, bool shadow = true )
    {
        if ( shadow ) font.draw( t, x + 1, y + 1, { 10, 8, 20, 255 } );
        return font.draw( t, x, y, c );
    };

    // Crystals out of sight: the nearest few show at the screen's edge where they lie (all of them once only three
    // are left), so none has to be searched for long.
    if ( m_crystalsTaken < m_crystals && !m_dead )
    {
        const Sheet                                  &items = assets().sheet( "items" );
        float                                         hx = m_hero.m_x - m_camX, hy = m_hero.m_y - 22 - m_camY;
        bool                                          all = m_crystals - m_crystalsTaken <= 3;
        std::vector<std::pair<float, const Pickup *>> far;
        for ( const Pickup &p : m_pickups )
        {
            if ( p.m_taken || p.m_kind != PickE::CRYSTAL ) continue;
            float px = p.m_x - m_camX, py = p.m_y - m_camY;
            if ( px > -8 && px < s.m_w + 8 && py > -8 && py < s.m_h + 8 ) continue;
            float d = std::hypot( p.m_x - m_hero.m_x, p.m_y - m_hero.m_y );
            if ( all || d < s.m_w * 1.3f ) far.push_back( { d, &p } );
        }
        std::sort( far.begin(), far.end(), []( const auto &a, const auto &b ) { return a.first < b.first; } );
        if ( far.size() > 3 ) far.resize( 3 );
        for ( const auto &[d, p] : far )
        {
            // Where the line from Kip to the crystal leaves the screen, kept clear of the panel at the top left.
            float dx = p->m_x - m_camX - hx, dy = p->m_y - m_camY - hy, len = std::max( 1.0f, std::hypot( dx, dy ) );
            float ux = dx / len, uy = dy / len, m = 18;
            float k = std::min( ux > 0 ? ( s.m_w - m - hx ) / ux : ux < 0 ? ( m - hx ) / ux : 1e9f,
                                uy > 0 ? ( s.m_h - m - hy ) / uy : uy < 0 ? ( m - hy ) / uy : 1e9f );
            float x = hx + ux * k, y = hy + uy * k;
            if ( x < 150 && y < 112 )
            {
                if ( ux < 0 && std::fabs( ux ) > std::fabs( uy ) ) y = 112;
                else
                    x = 150;
            }
            // The crystal on a dark disc a little inside (it must stand out from any wall), a ring pulsing around it, an
            // arrow towards the edge.
            float pulse = 0.5f + 0.5f * std::sin( m_clock * 5 + d * 0.01f );
            float cx = std::floor( x - ux * 8 ), cy = std::floor( y - uy * 8 );
            Color ring = { (unsigned char)( 90 + 110 * pulse ), (unsigned char)( 210 + 45 * pulse ), 255, 255 };
            DrawCircle( (int)cx, (int)cy, 14, { 8, 10, 26, 170 } );
            DrawCircleLines( (int)cx, (int)cy, 14, ring );
            DrawCircleLines( (int)cx, (int)cy, 13, ring );
            items.draw( items.frame( "crystal", m_clock ), cx, cy );
            auto arrow = [&]( float r, float w, Color c )
            {
                Vector2 tip = { x + ux * ( 13 + r ), y + uy * ( 13 + r ) }, b1 = { x + ux * 7 - uy * w, y + uy * 7 + ux * w },
                        b2 = { x + ux * 7 + uy * w, y + uy * 7 - ux * w };
                if ( ( b1.x - tip.x ) * ( b2.y - tip.y ) - ( b1.y - tip.y ) * ( b2.x - tip.x ) > 0 ) std::swap( b1, b2 );
                DrawTriangle( tip, b1, b2, c );
            };
            arrow( 3, 7, { 8, 10, 26, 255 } );
            arrow( 0, 5, ring );
        }
    }

    // Health: the bar's frame and its fill (green, red when low), longer with armour.
    float hmax = (float)m_progress->healthMax();
    float frac = std::clamp( m_hp / hmax, 0.0f, 1.0f );
    icon( "health", 6, 4 );
    const Texture2D *frame = assets().texture( "ui/bar_frame.png" );
    const Texture2D *fill = assets().texture( frac > 0.35f ? "ui/bar_fill.png" : "ui/bar_fill_low.png" );
    if ( frame && fill )
    {
        int extra = 12 * m_progress->m_armour;
        NPatchInfo n = { { 0, 0, (float)frame->width, (float)frame->height }, 6, 0, 6, 0, NPATCH_THREE_PATCH_HORIZONTAL };
        DrawTextureNPatch( *frame, n, { 30, 13, (float)frame->width + extra, (float)frame->height }, { 0, 0 }, 0, WHITE );
        float fw = ( 92.0f + extra ) * frac;
        DrawTexturePro( *fill, { 0, 0, (float)fill->width * std::min( 1.0f, fw / fill->width ), (float)fill->height }, { 34, 16, std::floor( fw ), (float)fill->height }, { 0, 0 }, 0, WHITE );
    }
    else
    {
        int bw = 80 + 10 * m_progress->m_armour;
        DrawRectangle( 30, 11, bw + 4, 10, { 12, 10, 24, 255 } );
        DrawRectangle( 32, 13, (int)( bw * frac ), 6, frac > 0.35f ? Color{ 90, 220, 120, 255 } : Color{ 240, 80, 70, 255 } );
    }
    // Crystals.
    icon( "crystal", 6, 22 );
    text( std::to_string( m_crystalsTaken ) + "/" + std::to_string( m_crystals ), 32, 29, m_crystalsTaken >= m_crystals ? Color{ 140, 255, 200, 255 } : Color{ 160, 230, 255, 255 } );
    // Keys.
    float kx = 80;
    if ( m_keys[0] ) icon( "key_blue", kx, 24 ), kx += 22;
    if ( m_keys[1] ) icon( "key_gold", kx, 24 ), kx += 22;
    // Weapons: a slot per weapon Kip has, the one in hand lit, its ammo beside it.
    {
        const Texture2D *slot = assets().texture( "ui/weapon_slot.png" );
        const Texture2D *chosen = assets().texture( "ui/weapon_slot_selected.png" );
        float            x = 6;
        for ( int w = 0; w < WeaponCount; ++w )
        {
            if ( !m_progress->has( (WeaponE)w ) ) continue;
            bool on = (WeaponE)w == m_weapon;
            // The slots are half size; the one in hand full size.
            float size = on ? 36.0f : 24.0f, y = on ? 50.0f : 56.0f;
            const Texture2D *box = on ? chosen : slot;
            if ( box ) DrawTexturePro( *box, { 0, 0, (float)box->width, (float)box->height }, { x, y, size, size }, { 0, 0 }, 0, WHITE );
            std::string name = std::string( "weapon_" ) + weapon( (WeaponE)w ).m_id;
            if ( !hud.m_standIn )
            {
                int        f = hud.frame( name, 0 ), cols = std::max( 1, hud.m_tex.width / hud.m_fw );
                Rectangle  src = { (float)( f % cols ) * hud.m_fw, (float)( f / cols ) * hud.m_fh, (float)hud.m_fw, (float)hud.m_fh };
                float      inner = size * 0.8f;
                bool       dry = weapon( (WeaponE)w ).m_ammoMax && m_progress->m_ammo[w] <= 0;
                DrawTexturePro( hud.m_tex, src, { x + ( size - inner ) * 0.5f, y + ( size - inner ) * 0.5f, inner, inner }, { 0, 0 }, 0,
                                dry ? Color{ 90, 90, 110, 255 } : WHITE );
            }
            x += size + 2;
        }
        const WeaponDef &d = weapon( m_weapon );
        std::string      ammo = d.m_ammoMax ? std::to_string( m_progress->m_ammo[(int)m_weapon] ) : "";
        if ( !ammo.empty() ) text( ammo, x + 2, 63, colourOf( d.m_colour ) );
        float px = 6;
        if ( m_overdrive > 0 ) icon( "power_overdrive", px, 88 ), text( std::to_string( (int)std::ceil( m_overdrive ) ), px + 30, 98, { 255, 200, 120, 255 } ), px += 50;
        if ( m_shield > 0 ) icon( "power_shield", px, 88 ), text( std::to_string( (int)std::ceil( m_shield ) ), px + 30, 98, { 140, 220, 255, 255 } ), px += 50;
        if ( m_boots ) icon( "power_boots", px, 88 );
    }
    // Score and credits.
    {
        std::string sc = std::to_string( m_progress->m_score + m_score );
        int         w = font.width( sc );
        text( sc, s.m_w - 8 - w, 8, { 255, 255, 255, 255 } );
        std::string cr = std::to_string( m_progress->m_credits + m_credits );
        w = font.width( cr );
        text( cr, s.m_w - 8 - w, 28, { 255, 220, 100, 255 } );
        icon( "credits", s.m_w - 8 - w - 36, 18 );
    }
    // The boss's health.
    if ( m_boss && m_bossAwake && m_bossIndex >= 0 && m_enemies[m_bossIndex].m_alive )
    {
        const Enemy &b = m_enemies[m_bossIndex];
        int          w = 300, x = ( s.m_w - w ) / 2, y = s.m_h - 22;
        std::string  name = tr( std::string( "boss." ) + b.m_def->m_id );
        text( name, x, y - 12, { 255, 200, 230, 255 } );
        DrawRectangle( x - 2, y - 2, w + 4, 10, { 12, 10, 24, 255 } );
        DrawRectangle( x, y, (int)( w * std::max( 0.0f, b.m_hp / b.m_hpMax ) ), 6, { 230, 60, 120, 255 } );
    }
    // Popups in the world.
    for ( const Popup &p : m_popups )
    {
        float a = std::clamp( 1.6f - p.m_t * 1.5f, 0.0f, 1.0f );
        int   w = font.width( p.m_text );
        text( p.m_text, std::floor( p.m_x - m_camX - w * 0.5f ), std::floor( p.m_y - m_camY ), ColorAlpha( p.m_c, a ) );
    }
    // The banner.
    if ( m_bannerT > 0 && !m_banner.empty() )
    {
        float a = std::min( 1.0f, m_bannerT * 2 );
        int   w = big.width( m_banner );
        if ( w > s.m_w - 20 )
        {
            int fw = font.width( m_banner );
            text( m_banner, ( s.m_w - fw ) / 2, 74, ColorAlpha( { 255, 240, 200, 255 }, a ) );
        }
        else
            big.draw( m_banner, ( s.m_w - w ) / 2, 66, ColorAlpha( { 255, 240, 200, 255 }, a ) );
    }
    // A sign the hero reads.
    if ( m_signT > 0 && !m_sign.empty() )
    {
        // {jump}, {fire} ... become the pad's buttons or the keys, whichever was used last.
        const std::string t = glyphs( tr( m_sign ), padInUse() );
        // Up to three lines, broken at '\n'.
        std::vector<std::string> lines;
        size_t start = 0;
        while ( start <= t.size() )
        {
            size_t nl = t.find( '\n', start );
            lines.push_back( t.substr( start, nl == std::string::npos ? std::string::npos : nl - start ) );
            if ( nl == std::string::npos ) break;
            start = nl + 1;
        }
        // In the big font when asked for (and when it fits).
        const PixelFont *sf = m_bigText ? &big : &font;
        int              w = 0;
        for ( auto &l : lines ) w = std::max( w, sf->width( l ) );
        if ( sf == &big && w > s.m_w - 40 )
        {
            sf = &font, w = 0;
            for ( auto &l : lines ) w = std::max( w, font.width( l ) );
        }
        int h = (int)lines.size() * ( sf->height() + 2 ) + 10;
        int x = ( s.m_w - w ) / 2 - 8, y = s.m_h - h - 34;
        DrawRectangle( x, y, w + 16, h, { 14, 18, 40, 230 } );
        DrawRectangleLines( x, y, w + 16, h, { 90, 200, 255, 255 } );
        for ( size_t i = 0; i < lines.size(); ++i )
        {
            int ly = y + 6 + (int)i * ( sf->height() + 2 );
            sf->draw( lines[i], x + 9.0f, ly + 1.0f, { 10, 8, 20, 255 } );
            sf->draw( lines[i], (float)x + 8, (float)ly, { 220, 240, 255, 255 } );
        }
    }
    // The level's name at the start.
    if ( m_time < 3.0f && m_time > 0 )
    {
        float       a = std::clamp( ( 3.0f - m_time ) * 1.5f, 0.0f, 1.0f );
        std::string name = hasText( "level." + m_level.m_id ) ? tr( "level." + m_level.m_id )
                           : language() == "de"               ? m_level.key( "name.de", m_level.key( "name" ) )
                                                              : m_level.key( "name" );
        int         w = big.width( name );
        big.draw( name, ( s.m_w - w ) / 2, s.m_h / 2 - 50, ColorAlpha( { 200, 240, 255, 255 }, a ) );
    }
    s.end();
}

}   // namespace kepler
