/**
 * @file EditorView.cpp
 * @brief The level editor's picture of a level, drawn with the game's tiles and sprites (as WorldDraw.cpp does, for
 *        a level that has not started: doors shut, blocks whole, toggles off).
 * @author Rene Weller
 */
#include "EditorView.h"

#include "Assets.h"
#include "Content.h"
#include "Screen.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <map>

namespace kepler::edit
{

namespace
{

constexpr float T = (float)Tile;

/** @brief A tile of a 32 px sheet scaled into a box. */
void tileTo( const Texture2D &tex, int index, Rectangle dst, Color tint = WHITE, bool flipX = false )
{
    if ( !tex.id ) return;
    int cols = std::max( 1, tex.width / Tile ), rows = std::max( 1, tex.height / Tile );
    index %= cols * rows;
    Rectangle src = { (float)( index % cols ) * T, (float)( index / cols ) * T, flipX ? -T : T, T };
    DrawTexturePro( tex, src, dst, { 0, 0 }, 0, tint );
}

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

bool has( const std::vector<std::string> &w, const char *word )
{
    return std::find( w.begin(), w.end(), word ) != w.end();
}

/** @brief The pickup animation in the items sheet of an item spawn ("" if it is not one). */
std::string itemAnim( const CharInfo &info, int x, int y )
{
    const std::string &k = info.m_kind;
    std::string        a0 = info.m_args.empty() ? "" : info.m_args[0];
    if ( k == "crystal" ) return "crystal";
    if ( k == "treasure" )
    {
        for ( const TreasureDef &t : treasures() )
            if ( a0 == t.m_id ) return a0;
        uint32_t h = hashCell( x, y, 7 ) % 100;
        int      i = h < 45 ? 0 : h < 75 ? 1 : h < 93 ? 2 : 3;
        return treasures()[i].m_id;
    }
    if ( k == "health" ) return a0 == "big" ? "health_big" : "health";
    if ( k == "key" ) return a0 == "gold" ? "key_gold" : "key_blue";
    if ( k == "ammo" ) return "ammo";
    if ( k == "weapon" ) return weaponOf( a0 ) != WeaponE::COUNT ? "weapon_" + a0 : "";
    if ( k == "power" ) return a0 == "boots" ? "power_boots" : a0 == "shield" ? "power_shield" : "power_overdrive";
    if ( k == "lore" ) return "lore";
    return "";
}

/** @brief The opaque part of every frame of a sheet (texture pixels), read once from its png. */
const std::vector<Rectangle> &opaqueBoxes( const std::string &name, const Sheet &sh )
{
    static std::map<std::string, std::vector<Rectangle>> cache;
    auto it = cache.find( name );
    if ( it != cache.end() ) return it->second;
    std::vector<Rectangle> boxes;
    int                    cols = std::max( 1, sh.m_cols ), rows = std::max( 1, sh.m_tex.height / std::max( 1, sh.m_fh ) );
    Image                  img = LoadImage( ( assetDir() + "sprites/" + name + ".png" ).c_str() );
    Color                 *px = img.data ? LoadImageColors( img ) : nullptr;
    for ( int f = 0; f < cols * rows; ++f )
    {
        int fx = ( f % cols ) * sh.m_fw, fy = ( f / cols ) * sh.m_fh;
        int l = sh.m_fw, t = sh.m_fh, r = -1, b = -1;
        if ( px )
            for ( int y = 0; y < sh.m_fh && fy + y < img.height; ++y )
                for ( int x = 0; x < sh.m_fw && fx + x < img.width; ++x )
                    if ( px[( fy + y ) * img.width + fx + x].a > 0 )
                        l = std::min( l, x ), r = std::max( r, x ), t = std::min( t, y ), b = std::max( b, y );
        if ( r < 0 ) boxes.push_back( { (float)fx, (float)fy, (float)sh.m_fw, (float)sh.m_fh } );
        else
            boxes.push_back( { (float)( fx + l ), (float)( fy + t ), (float)( r - l + 1 ), (float)( b - t + 1 ) } );
    }
    if ( px ) UnloadImageColors( px );
    if ( img.data ) UnloadImage( img );
    return cache.emplace( name, std::move( boxes ) ).first->second;
}

}   // namespace

// ---------------------------------------------------------------------------------------------------- helpers

void CharTable::build( const Doc &doc )
{
    for ( CharInfo &i : m_info ) i = CharInfo();
    for ( int c = 33; c < 127; ++c )
    {
        std::string kind = doc.kindOf( (char)c );
        if ( kind.empty() ) continue;
        m_info[c].m_kind = kind;
        m_info[c].m_args = doc.argsOf( (char)c );
    }
}

void tileAt( const Texture2D &tex, int index, float x, float y, Color tint, bool flipX )
{
    tileTo( tex, index, { x, y, T, T }, tint, flipX );
}

Color lightColour( const std::string &name )
{
    static const std::pair<const char *, Color> named[] = {
        { "warm", { 255, 196, 120, 255 } }, { "cold", { 140, 200, 255, 255 } },  { "cyan", { 90, 230, 255, 255 } },
        { "green", { 120, 255, 150, 255 } }, { "red", { 255, 90, 80, 255 } },     { "orange", { 255, 150, 60, 255 } },
        { "violet", { 190, 120, 255, 255 } }, { "magenta", { 255, 90, 220, 255 } }, { "white", { 240, 240, 255, 255 } },
        { "yellow", { 255, 230, 110, 255 } }, { "blue", { 90, 140, 255, 255 } } };
    for ( auto &[n, c] : named )
        if ( name == n ) return c;
    return { 230, 230, 240, 255 };
}

std::string restAnim( const Sheet &sh )
{
    for ( const char *a : { "idle", "move", "fly" } )
        if ( sh.anim( a ) ) return a;
    return sh.m_firstAnim;
}

void drawFit( const std::string &sheet, const std::string &anim, Rectangle dst, Color tint, bool flip )
{
    const Sheet &sh = assets().sheet( sheet );
    if ( sh.m_standIn || !sh.m_tex.id )
    {
        DrawRectangle( (int)dst.x + 4, (int)dst.y + 4, (int)dst.width - 8, (int)dst.height - 8, ColorAlpha( { 220, 90, 60, 255 }, tint.a / 255.0f ) );
        return;
    }
    int                           fr = sh.frame( anim.empty() ? sh.m_firstAnim : anim, 0 );
    const std::vector<Rectangle> &boxes = opaqueBoxes( sheet, sh );
    Rectangle box = fr >= 0 && fr < (int)boxes.size() ? boxes[fr] : Rectangle{ 0, 0, (float)sh.m_fw, (float)sh.m_fh };
    float     sc = std::min( dst.width / box.width, dst.height / box.height );
    sc = sc >= 2 ? std::floor( std::min( sc, 2.0f ) ) : sc >= 1 ? 1 : sc;
    float w = box.width * sc, h = box.height * sc;
    Rectangle out = { std::floor( dst.x + ( dst.width - w ) / 2 ), std::floor( dst.y + ( dst.height - h ) / 2 ), w, h };
    Rectangle src = box;
    if ( flip ) src.width = -src.width;
    DrawTexturePro( sh.m_tex, src, out, { 0, 0 }, 0, tint );
}

void drawCellLook( const TileSet &ts, Color tint, char c, float x, float y, float size, float clock )
{
    Rectangle dst = { x, y, size, size };
    auto block = [&]( int row, int col, bool flip, Color stand )
    {
        if ( ts.m_blocks.id ) tileTo( ts.m_blocks, row * ( ts.m_blocks.width / Tile ) + col, dst, tint, flip );
        else
            DrawRectangleRec( { x + 1, y + 1, size - 2, size - 2 }, stand );
    };
    switch ( c )
    {
    case ' ':
        DrawRectangleGradientV( (int)x, (int)y, (int)size, (int)size, { 24, 30, 70, 255 }, { 8, 8, 20, 255 } );
        for ( int i = 0; i < 6; ++i )
            DrawPixel( (int)( x + 3 + ( i * 37 ) % (int)( size - 6 ) ), (int)( y + 3 + ( i * 23 ) % (int)( size - 6 ) ), { 200, 210, 255, 255 } );
        break;
    case '.':
    case '?':
        if ( ts.m_back.id ) tileTo( ts.m_back, 255, dst, ColorBrightness( tint, -0.05f ) );
        else
            DrawRectangleRec( dst, { 40, 44, 60, 255 } );
        if ( c == '?' ) DrawRectangleRec( dst, { 170, 90, 255, 90 } );
        break;
    case '#':
    case 'X':
        if ( ts.m_terrainA.id ) tileTo( ts.m_terrainA, 0, dst, tint );
        else
            DrawRectangleRec( dst, { 110, 110, 130, 255 } );
        break;
    case '%':
        if ( ts.m_terrainB.id ) tileTo( ts.m_terrainB, 0, dst, tint );
        else
            DrawRectangleRec( dst, { 90, 120, 140, 255 } );
        break;
    case '-':
        if ( ts.m_platform.id ) tileTo( ts.m_platform, 0, dst, tint );
        else
            DrawRectangleRec( { x, y, size, size / 4 }, { 200, 180, 90, 255 } );
        break;
    case 'B': block( 0, 0, false, { 170, 130, 90, 255 } ); break;
    case '_': block( 1, 0, false, { 140, 110, 70, 255 } ); break;
    case 'd': block( 2, 0, false, { 50, 90, 240, 255 } ); break;
    case 'D': block( 3, 0, false, { 240, 190, 40, 255 } ); break;
    case 't': block( 4, (int)( clock * 8 ) % 4, false, { 40, 210, 210, 255 } ); break;
    case 'T': block( 5, (int)( clock * 8 ) % 4, false, { 40, 210, 210, 70 } ); break;
    case '{': block( 6, (int)( clock * 10 ) % 4, true, { 110, 110, 70, 255 } ); break;
    case '}': block( 6, (int)( clock * 10 ) % 4, false, { 110, 110, 70, 255 } ); break;
    case '^': block( 7, 0, false, { 220, 60, 60, 255 } ); break;
    case 'v': block( 7, 1, false, { 220, 60, 60, 255 } ); break;
    case '<': block( 7, 2, false, { 220, 60, 60, 255 } ); break;
    case '>': block( 7, 3, false, { 220, 60, 60, 255 } ); break;
    case '~':
        if ( ts.m_liquid.id ) tileTo( ts.m_liquid, (int)( clock * 6 ) % 4, dst, tint );
        else
            DrawRectangleRec( { x, y + size / 5, size, size * 4 / 5 }, Fade( liquidLight( ts.m_theme ), 0.8f ) );
        break;
    default: break;
    }
}

// --------------------------------------------------------------------------------------------------- placement

Vector2 standPoint( const Doc &doc, const CharInfo &info, int x, int y, bool &upside )
{
    upside = false;
    float cx = x * T + T * 0.5f;
    auto  floorBelow = [&]( int from, float fallback )
    {
        for ( int yy = from; yy < doc.m_h; ++yy )
            if ( doc.solidAt( x, yy ) || doc.onewayAt( x, yy ) ) return yy * T;
        return fallback;
    };
    if ( info.m_kind == "start" ) return { cx, floorBelow( y + 1, ( y + 1 ) * T ) };
    if ( info.m_kind != "enemy" && info.m_kind != "boss" ) return { cx, ( y + 1 ) * T };
    std::string     id = info.m_args.empty() ? "" : info.m_args[0];
    int             boss = 0;
    const EnemyDef *d = enemyDef( id );
    if ( !d ) d = bossDef( id, boss );
    if ( !d ) return { cx, ( y + 1 ) * T };
    float ey = ( y + 1 ) * T;
    switch ( d->m_brain )
    {
    case BrainE::FLIER:
    case BrainE::GUNSHIP:
    case BrainE::FLOATER: ey = y * T + T * 0.5f + d->m_h * 0.5f; break;
    case BrainE::SWOOPER:
    case BrainE::DROPPER:
        for ( int yy = y; yy >= 0; --yy )
            if ( doc.solidAt( x, yy ) )
            {
                ey = ( yy + 1 ) * T + d->m_h;
                break;
            }
        break;
    case BrainE::TURRET:
    case BrainE::BEAMER:
        if ( !doc.solidAt( x, y + 1 ) && doc.solidAt( x, y - 1 ) ) upside = true, ey = y * T + d->m_h;
        break;
    default: ey = floorBelow( y + 1, ey ); break;
    }
    if ( d->m_brain == BrainE::WALKER && has( info.m_args, "ceiling" ) && info.m_kind == "enemy" )
    {
        for ( int yy = y; yy >= 0; --yy )
            if ( doc.solidAt( x, yy ) )
            {
                ey = ( yy + 1 ) * T + d->m_h;
                break;
            }
        upside = true;
    }
    return { cx, ey };
}

// -------------------------------------------------------------------------------------------------------- spawns

void drawSpawn( const Doc &doc, const CharInfo &info, int x, int y, char ch, float clock, bool glow, float alpha )
{
    const std::string &k = info.m_kind;
    Color              tint = ColorAlpha( WHITE, alpha );
    float              cx = x * T + T * 0.5f, cy = y * T + T * 0.5f;
    float              phase = ( hashCell( x, y ) % 100 ) * 0.01f;
    std::string        a0 = info.m_args.empty() ? "" : info.m_args[0];

    std::string item = itemAnim( info, x, y );
    if ( !item.empty() )
    {
        const Sheet &items = assets().sheet( "items" );
        if ( items.anim( item ) ) items.draw( items.frame( item, clock + phase ), cx, cy, false, tint, glow );
        else if ( !glow )
        {
            // A datapad stand-in (lore pages before the sheet has them).
            DrawRectangle( (int)cx - 7, (int)cy - 9, 14, 18, ColorAlpha( { 40, 60, 90, 255 }, alpha ) );
            DrawRectangle( (int)cx - 5, (int)cy - 7, 10, 12, ColorAlpha( { 120, 230, 255, 255 }, alpha ) );
        }
        if ( glow && k == "crystal" && !items.m_hasGlow ) DrawCircle( (int)cx, (int)cy, 3, { 100, 220, 255, 255 } );
        return;
    }
    if ( k == "enemy" || k == "boss" )
    {
        int             boss = 0;
        const EnemyDef *d = enemyDef( a0 );
        if ( !d ) d = bossDef( a0, boss );
        if ( !d ) return;
        bool         upside = false;
        Vector2      p = standPoint( doc, info, x, y, upside );
        bool         flip = has( info.m_args, "left" );
        const Sheet &sh = assets().sheet( a0 );
        if ( has( info.m_args, "ambush" ) ) tint = ColorAlpha( WHITE, alpha * 0.55f );
        if ( sh.m_standIn )
        {
            if ( !glow )
                DrawRectangle( (int)( p.x - d->m_w * 0.5f ), (int)( p.y - d->m_h ), d->m_w, d->m_h,
                               ColorAlpha( k == "boss" ? Color{ 200, 60, 200, 255 } : Color{ 220, 90, 60, 255 }, tint.a / 255.0f ) );
            return;
        }
        int fr = sh.frame( restAnim( sh ), 0 );
        if ( upside ) sh.draw( fr, p.x, p.y - d->m_h, flip, tint, glow, 180 );
        else
            sh.draw( fr, p.x, p.y, flip, tint, glow );
        return;
    }
    if ( k == "start" )
    {
        bool         upside = false;
        Vector2      p = standPoint( doc, info, x, y, upside );
        const Sheet &hero = assets().sheet( "hero" );
        if ( hero.m_standIn )
        {
            if ( !glow ) DrawRectangle( (int)p.x - 10, (int)p.y - 44, 20, 44, ColorAlpha( { 240, 140, 40, 255 }, alpha ) );
        }
        else
            hero.draw( hero.frame( "idle", 0 ), p.x, p.y, false, tint, glow );
        return;
    }
    if ( k == "mover" )
    {
        const TileSet &ts = assets().tiles( doc.key( "theme", "station" ) );
        bool           l = doc.at( x - 1, y ) == ch, r = doc.at( x + 1, y ) == ch;
        int            piece = l && r ? 2 : l ? 3 : r ? 1 : 0;
        float          px = x * T, py = y * T;
        int            tintI = std::clamp( atoi( doc.key( "tint", "0" ).c_str() ), 0, 3 );
        if ( glow ) DrawRectangle( (int)px + 4, (int)py + 9, Tile - 8, 1, { 80, 200, 255, 255 } );
        else if ( ts.m_platform.id )
            tileAt( ts.m_platform, piece, px, py, ColorAlpha( ts.m_tints[tintI], alpha ) );
        else
            DrawRectangle( (int)px, (int)py, Tile, 10, ColorAlpha( { 200, 200, 120, 255 }, alpha ) );
        return;
    }
    const Sheet &objects = assets().sheet( "objects" );
    float        oy = ( y + 1 ) * T;
    std::string  anim;
    if ( k == "exit" ) anim = "exit_closed";
    else if ( k == "checkpoint" )
        anim = "checkpoint_off";
    else if ( k == "teleport" )
        anim = "teleporter";
    else if ( k == "switch" )
        anim = "switch_off";
    else if ( k == "spring" )
        anim = "spring";
    else if ( k == "sign" )
        anim = "sign";
    else if ( k == "warp" )
        anim = objects.anim( "warp" ) ? "warp" : "exit_open";
    if ( !anim.empty() )
    {
        Color t = k == "warp" && !objects.anim( "warp" ) ? ColorAlpha( { 220, 150, 255, 255 }, alpha ) : tint;
        if ( objects.m_standIn )
        {
            if ( !glow ) DrawRectangle( (int)cx - 12, (int)oy - 28, 24, 28, ColorAlpha( { 120, 200, 255, 255 }, alpha ) );
        }
        else
            objects.draw( objects.frame( anim, clock + phase ), cx, oy, false, t, glow );
        return;
    }
    if ( k == "laser" )
    {
        bool  vertical = a0 == "v";
        bool  ceiling = vertical && doc.solidAt( x, y - 1 );
        bool  flip = !vertical && !doc.solidAt( x - 1, y );
        float wallX = flip ? cx + 16 : cx - 16;
        if ( vertical )
            objects.draw( objects.frame( "laser_emitter", clock + phase ), cx, ceiling ? oy - T : oy, false, tint, glow, ceiling ? 180.0f : 0 );
        else
            objects.draw( objects.frame( "laser_emitter_side", clock + phase ), wallX + ( flip ? -16 : 16 ), oy, flip, tint, glow );
        int dx = 0, dy = 0;
        if ( vertical ) dy = doc.solidAt( x, y - 1 ) ? 1 : -1;
        else
            dx = doc.solidAt( x - 1, y ) ? 1 : -1;
        int bx = x, by = y, n = 0;
        while ( n < 40 && !doc.solidAt( bx + dx, by + dy ) ) bx += dx, by += dy, ++n;
        Vector2 a = { cx, cy }, b = { cx + dx * ( n + 0.5f ) * T, cy + dy * ( n + 0.5f ) * T };
        DrawLineEx( a, b, glow ? 5.0f : 3.0f, glow ? Color{ 200, 40, 60, 255 } : ColorAlpha( { 255, 90, 90, 255 }, alpha * 0.7f ) );
        DrawLineEx( a, b, 1.0f, ColorAlpha( { 255, 230, 230, 255 }, alpha ) );
        return;
    }
    if ( k == "crusher" )
    {
        float l = x * T, t = y * T;
        if ( !glow )
        {
            DrawRectangle( (int)l + 12, (int)t, 8, 8, ColorAlpha( { 70, 74, 90, 255 }, alpha ) );
            DrawRectangle( (int)l + 2, (int)t, Tile - 4, 22, ColorAlpha( { 120, 124, 140, 255 }, alpha ) );
            DrawRectangle( (int)l + 2, (int)t, Tile - 4, 3, ColorAlpha( { 190, 196, 210, 255 }, alpha ) );
            for ( int i = 0; i < 4; ++i )
                DrawTriangle( { l + 3 + i * 7.0f, t + 22 }, { l + 6.5f + i * 7.0f, t + 29 }, { l + 10 + i * 7.0f, t + 22 }, ColorAlpha( { 200, 200, 215, 255 }, alpha ) );
        }
        else
            DrawRectangle( (int)l + 4, (int)t + 10, Tile - 8, 2, { 255, 120, 40, 255 } );
        return;
    }
}

// -------------------------------------------------------------------------------------------------------- decos

std::vector<DecoSpot> placeDecos( const Doc &doc )
{
    std::vector<DecoSpot> out;
    const TileSet        &ts = assets().tiles( doc.key( "theme", "station" ) );
    if ( ts.m_decos.empty() || doc.m_w <= 0 ) return out;
    const Level      &L = doc.m_view;
    std::vector<char> used( (size_t)L.m_w * L.m_h, 0 );
    bool              spawn[256] = {};
    for ( int c = 33; c < 127; ++c )
    {
        std::string k = doc.kindOf( (char)c );
        spawn[c] = !k.empty() && k != "?";
    }
    for ( int y = 0; y < doc.m_h; ++y )
        for ( int x = 0; x < doc.m_w; ++x )
            if ( spawn[(unsigned char)doc.m_rows[y][x]] ) used[(size_t)y * L.m_w + x] = 1;
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
            if ( doc.solidAt( x, y + 1 ) && h % 100 < 22 ) place = 1;
            else if ( doc.solidAt( x, y - 1 ) && h % 100 < 16 )
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
            int         x0 = x, y0 = place == 1 ? y - ch + 1 : y;
            bool        fits = true;
            for ( int yy = y0; yy < y0 + ch && fits; ++yy )
                for ( int xx = x0; xx < x0 + cw && fits; ++xx )
                    if ( !freeCell( xx, yy ) ) fits = false;
            if ( place == 1 )
                for ( int xx = x0; xx < x0 + cw && fits; ++xx )
                    if ( !doc.solidAt( xx, y + 1 ) ) fits = false;
            if ( place == 2 || place == 3 )
                for ( int xx = x0; xx < x0 + cw && fits; ++xx )
                    if ( !doc.solidAt( xx, y - 1 ) ) fits = false;
            if ( !fits ) continue;
            for ( int yy = y0; yy < y0 + ch; ++yy )
                for ( int xx = x0; xx < x0 + cw; ++xx ) used[(size_t)yy * L.m_w + xx] = 1;
            DecoSpot p;
            p.m_index = chosen;
            p.m_x = x0 * T + ( cw * T - d.m_src.width ) * 0.5f;
            p.m_y = place == 1 ? ( y + 1 ) * T - d.m_src.height : place == 0 ? y0 * T + ( ch * T - d.m_src.height ) * 0.5f : y * T;
            out.push_back( p );
        }
    return out;
}

// --------------------------------------------------------------------------------------------------------- level

void drawLevel( Screen &s, const Doc &doc, const CharTable &chars, const Camera &cam, const std::vector<DecoSpot> &decos,
                const DrawOptions &o )
{
    const std::string theme = doc.key( "theme", "station" );
    const TileSet    &ts = assets().tiles( theme );
    const Level      &L = doc.m_view;
    int               tintI = std::clamp( atoi( doc.key( "tint", "0" ).c_str() ), 0, 3 );
    Color             tint = ts.m_tints[tintI];
    float             dark = std::clamp( (float)atof( doc.key( "dark", "0" ).c_str() ), 0.0f, 0.9f );
    float             amb = o.m_light ? 1.0f - dark : 1.0f;
    Color ambient = { (unsigned char)( 255 * amb ), (unsigned char)( 255 * std::min( 1.0f, amb * 1.02f ) ), (unsigned char)( 255 * std::min( 1.0f, amb * 1.1f ) ), 255 };
    s.clear( ambient );

    float viewW = s.m_w / cam.m_zoom, viewH = s.m_h / cam.m_zoom;
    float rise = std::max( 0.0f, std::max( 0.0f, L.m_h * T - viewH ) - cam.m_y );
    const Background &bg = assets().background( doc.key( "bg", theme + "_a" ) );

    s.begin( LayerE::BACKGROUND );
    DrawRectangleGradientV( 0, 0, s.m_w, s.m_h, bg.m_top, bg.m_bottom );
    if ( bg.m_standIn )
        for ( int i = 0; i < 160; ++i )
        {
            float x = std::fmod( i * 97.0f - cam.m_x * 0.05f + 40000, (float)s.m_w ), y = std::fmod( i * 53.0f - cam.m_y * 0.03f + 40000, (float)s.m_h );
            DrawPixel( (int)x, (int)y, i % 7 == 0 ? Color{ 255, 255, 255, 255 } : Color{ 120, 130, 170, 255 } );
        }
    else
        drawBackground( bg, s.m_w, s.m_h, cam.m_x, rise, o.m_clock, false );
    s.end();

    int x0 = std::max( 0, (int)std::floor( cam.m_x / T ) - 1 ), x1 = std::min( L.m_w - 1, (int)std::floor( ( cam.m_x + viewW ) / T ) + 1 );
    int y0 = std::max( 0, (int)std::floor( cam.m_y / T ) - 1 ), y1 = std::min( L.m_h - 1, (int)std::floor( ( cam.m_y + viewH ) / T ) + 1 );
    int nA = TileSet::variants( ts.m_terrainA ), nB = TileSet::variants( ts.m_terrainB ), nBack = TileSet::variants( ts.m_back );
    Camera2D c2 = {};
    c2.target = { cam.m_x, cam.m_y };
    c2.zoom = cam.m_zoom;
    if ( cam.m_zoom >= 1 ) c2.target = { std::floor( cam.m_x ), std::floor( cam.m_y ) };

    for ( int pass = 0; pass < 2; ++pass )
    {
        bool glow = pass == 1;
        s.begin( glow ? LayerE::GLOW : LayerE::WORLD );
        // (The background's own glow is left out: in the editor it would shine over the walls being painted.)
        BeginMode2D( c2 );
        // Back walls.
        const Texture2D &back = glow ? ts.m_backGlow : ts.m_back;
        for ( int y = y0; y <= y1; ++y )
            for ( int x = x0; x <= x1; ++x )
            {
                size_t i = (size_t)y * L.m_w + x;
                if ( !L.m_cells[i].m_interior ) continue;
                if ( back.id ) tileAt( back, ( doc.m_variant[i] % nBack ) * 256 + doc.m_maskB[i], x * T, y * T, glow ? WHITE : ColorBrightness( tint, -0.05f ) );
                else if ( !glow )
                    DrawRectangle( x * Tile, y * Tile, Tile, Tile, { 34, 38, 54, 255 } );
            }
        // Decorations.
        const Texture2D &deco = glow ? ts.m_decoGlow : ts.m_deco;
        if ( o.m_decos && deco.id )
            for ( const DecoSpot &p : decos )
            {
                if ( p.m_index < 0 || p.m_index >= (int)ts.m_decos.size() ) continue;
                const Deco &d = ts.m_decos[p.m_index];
                if ( p.m_x + d.m_src.width < cam.m_x || p.m_x > cam.m_x + viewW || p.m_y + d.m_src.height < cam.m_y || p.m_y > cam.m_y + viewH ) continue;
                DrawTextureRec( deco, d.m_src, { std::floor( p.m_x ), std::floor( p.m_y ) }, glow ? WHITE : tint );
            }
        // Terrain.
        for ( int y = y0; y <= y1; ++y )
            for ( int x = x0; x <= x1; ++x )
            {
                size_t      i = (size_t)y * L.m_w + x;
                const Cell &c = L.m_cells[i];
                if ( c.m_kind == CellE::TERRAIN_A || c.m_kind == CellE::FAKE )
                {
                    const Texture2D &t = glow ? ts.m_terrainAGlow : ts.m_terrainA;
                    if ( t.id ) tileAt( t, ( doc.m_variant[i] % nA ) * 256 + doc.m_maskT[i], x * T, y * T, glow ? WHITE : tint );
                    else if ( !glow )
                        DrawRectangle( x * Tile, y * Tile, Tile, Tile, { 110, 110, 130, 255 } );
                }
                else if ( c.m_kind == CellE::TERRAIN_B )
                {
                    const Texture2D &t = glow ? ts.m_terrainBGlow : ts.m_terrainB;
                    if ( t.id ) tileAt( t, ( doc.m_variant[i] % nB ) * 256 + doc.m_maskT[i], x * T, y * T, glow ? WHITE : tint );
                    else if ( !glow )
                        DrawRectangle( x * Tile, y * Tile, Tile, Tile, { 90, 120, 140, 255 } );
                }
            }
        // Platforms, blocks, hazards, liquids.
        const Texture2D &blocks = glow ? ts.m_blocksGlow : ts.m_blocks;
        for ( int y = y0; y <= y1; ++y )
            for ( int x = x0; x <= x1; ++x )
            {
                size_t      i = (size_t)y * L.m_w + x;
                const Cell &c = L.m_cells[i];
                float       px = x * T, py = y * T;
                int         row = -1, col = 0;
                bool        flip = false;
                switch ( c.m_kind )
                {
                case CellE::PLATFORM:
                {
                    if ( glow ) break;
                    bool l = L.at( x - 1, y ).m_kind == CellE::PLATFORM, r = L.at( x + 1, y ).m_kind == CellE::PLATFORM;
                    int  piece = l && r ? 2 : l ? 3 : r ? 1 : 0;
                    if ( ts.m_platform.id ) tileAt( ts.m_platform, ( doc.m_variant[i] % std::max( 1, ts.m_platform.height / Tile ) ) * 4 + piece, px, py, tint );
                    else
                        DrawRectangle( (int)px, (int)py, Tile, 8, { 200, 180, 90, 255 } );
                    break;
                }
                case CellE::BREAKABLE: row = 0; break;
                case CellE::CRUMBLE: row = 1; break;
                case CellE::DOOR_BLUE: row = 2; break;
                case CellE::DOOR_GOLD: row = 3; break;
                case CellE::TOGGLE: row = ( c.m_aux & 8 ) == 0 ? 4 : 5, col = (int)( o.m_clock * 8 ) % 4; break;
                case CellE::CONVEYOR:
                    row = 6, col = (int)( o.m_clock * 10 ) % 4;
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
                    int              frame = (int)( o.m_clock * 6 + x * 0.5f ) % 4;
                    if ( liq.id ) tileAt( liq, ( surface ? 0 : 4 ) + frame, px, py, glow ? WHITE : tint );
                    else if ( !glow )
                        DrawRectangle( (int)px, (int)py + ( surface ? 6 : 0 ), Tile, Tile - ( surface ? 6 : 0 ), Fade( liquidLight( theme ), 0.8f ) );
                    break;
                }
                default: break;
                }
                if ( row < 0 ) continue;
                if ( blocks.id ) tileAt( blocks, row * ( blocks.width / Tile ) + col, px, py, glow ? WHITE : tint, flip );
                else if ( !glow )
                {
                    static const Color stand[8] = { { 170, 130, 90, 255 }, { 140, 110, 70, 255 }, { 50, 90, 240, 255 }, { 240, 190, 40, 255 },
                                                    { 40, 210, 210, 255 }, { 40, 210, 210, 70 },   { 110, 110, 70, 255 }, { 220, 60, 60, 255 } };
                    DrawRectangle( (int)px + 1, (int)py + 1, Tile - 2, Tile - 2, stand[row] );
                }
            }
        // What the map places: objects first, then pickups, enemies and the hero on top (their sprites reach over
        // their cells, so a margin of cells around the view is looked at).
        int sx0 = std::max( 0, x0 - 3 ), sx1 = std::min( L.m_w - 1, x1 + 3 ), sy0 = std::max( 0, y0 - 4 ), sy1 = std::min( L.m_h - 1, y1 + 4 );
        for ( int layer = 0; layer < 3; ++layer )
            for ( int y = sy0; y <= sy1; ++y )
                for ( int x = sx0; x <= sx1; ++x )
                {
                    char            ch = doc.m_rows[y][x];
                    const CharInfo &info = chars[ch];
                    if ( info.m_kind.empty() || info.m_kind == "?" || info.m_kind == "toggle" || info.m_kind == "conveyor" ) continue;
                    bool actor = info.m_kind == "enemy" || info.m_kind == "boss" || info.m_kind == "start";
                    bool item = !itemAnim( info, x, y ).empty();
                    int  want = actor ? 2 : item ? 1 : 0;
                    if ( want != layer ) continue;
                    drawSpawn( doc, info, x, y, ch, o.m_clock, glow );
                }
        EndMode2D();
        s.end();
    }

    if ( !o.m_light ) return;
    s.begin( LayerE::LIGHT );
    auto lamp = [&]( float x, float y, float r, Color c, float k )
    {
        Vector2 p = cam.toScreen( x, y );
        float   rr = r * cam.m_zoom;
        if ( p.x + rr < 0 || p.y + rr < 0 || p.x - rr > s.m_w || p.y - rr > s.m_h ) return;
        s.light( p.x, p.y, rr, c, k );
    };
    for ( int y = 0; y < doc.m_h; ++y )
        for ( int x = 0; x < doc.m_w; ++x )
        {
            const CharInfo &info = chars[doc.m_rows[y][x]];
            if ( info.m_kind.empty() ) continue;
            float cx = x * T + T * 0.5f, cy = y * T + T * 0.5f, oy = ( y + 1 ) * T;
            if ( info.m_kind == "start" )
            {
                bool    up = false;
                Vector2 p = standPoint( doc, info, x, y, up );
                lamp( p.x, p.y - 24, 120, { 255, 240, 220, 255 }, 0.55f + 0.5f * dark );
            }
            else if ( info.m_kind == "light" )
            {
                float r = ( info.m_args.size() > 1 ? (float)atof( info.m_args[1].c_str() ) : 5 ) * T;
                lamp( cx, cy, r, lightColour( info.m_args.empty() ? "" : info.m_args[0] ), 1 );
            }
            else if ( info.m_kind == "crystal" )
                lamp( cx, cy, 44, { 120, 220, 255, 255 }, 0.6f );
            else if ( info.m_kind == "exit" )
                lamp( cx, oy - 48, 60, { 120, 120, 160, 255 }, 1 );
            else if ( info.m_kind == "teleport" )
                lamp( cx, oy - 20, 60, { 120, 200, 255, 255 }, 0.7f );
            else if ( info.m_kind == "laser" )
                lamp( cx, oy - 16, 70, { 255, 60, 60, 255 }, 0.8f );
        }
    if ( o.m_decos )
        for ( const DecoSpot &p : decos )
        {
            if ( p.m_index < 0 || p.m_index >= (int)ts.m_decos.size() ) continue;
            const Deco &d = ts.m_decos[p.m_index];
            if ( d.m_glow ) lamp( p.m_x + d.m_src.width * 0.5f, p.m_y + d.m_src.height * 0.5f, 40 + std::max( d.m_src.width, d.m_src.height ), ColorBrightness( d.m_light, -0.35f ), 1 );
        }
    Color lc = liquidLight( theme );
    for ( int y = y0; y <= y1; ++y )
        for ( int x = x0 - x0 % 3; x <= x1; x += 3 )
            if ( L.at( x, y ).m_kind == CellE::LIQUID && L.at( x, y - 1 ).m_kind != CellE::LIQUID ) lamp( x * T + 16, y * T + 4, 60, lc, 0.32f );
    s.end();
}

}   // namespace kepler::edit
