/**
 * @file Tool.cpp
 * @brief KeplerTool, the console helper for level design (no window, no GPU):
 *          KeplerTool check <level.txt> [overview.png]      reachability report (exit code 1 when it cannot be finished)
 *          KeplerTool checkall <folder>                     every .txt level in the folder
 *          KeplerTool render <level.txt> <out.png> [scale]  the whole level with its real tiles and sprites
 *          KeplerTool render <level.txt> <out.png> x y w h  a part (in tiles), drawn twice as large
 *          KeplerTool deaths <level.txt> <deaths.txt> <out.png> [scale]   the level with its knockouts (the game's
 *                                                                          death records) as red circles
 * @author Rene Weller
 */
#include "../Checker.h"
#include "../Content.h"
#include "../Level.h"

#include <raylib.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <map>
#include <string>
#include <vector>

using namespace kepler;

namespace
{

std::string g_assets = KEPLER_ASSETS "/";

/** @brief A sprite sheet read into an Image (first frames only matter here). */
struct CpuSheet
{
    Image                      m_img = {};
    int                        m_fw = 32, m_fh = 32, m_ax = 16, m_ay = 16;
    std::map<std::string, int> m_first;   ///< animation -> its first frame
    bool                       ok() const { return m_img.data != nullptr; }
};

std::map<std::string, CpuSheet> g_sheets;

void label( Image &dst, const std::string &text, int x, int y, Color c );

const CpuSheet &sheet( const std::string &name )
{
    auto it = g_sheets.find( name );
    if ( it != g_sheets.end() ) return it->second;
    CpuSheet    s;
    std::string base = g_assets + "sprites/" + name;
    if ( FileExists( ( base + ".png" ).c_str() ) )
    {
        s.m_img = LoadImage( ( base + ".png" ).c_str() );
        ImageFormat( &s.m_img, PIXELFORMAT_UNCOMPRESSED_R8G8B8A8 );
        std::ifstream in( base + ".txt" );
        std::string   line;
        while ( std::getline( in, line ) )
        {
            std::vector<std::string> w = words( line );
            if ( w.size() >= 3 && w[0] == "frame" ) s.m_fw = atoi( w[1].c_str() ), s.m_fh = atoi( w[2].c_str() );
            if ( w.size() >= 3 && w[0] == "anchor" ) s.m_ax = atoi( w[1].c_str() ), s.m_ay = atoi( w[2].c_str() );
            if ( w.size() >= 5 && w[0] == "anim" ) s.m_first[w[1]] = atoi( w[4].c_str() );
        }
    }
    return g_sheets[name] = s;
}

Image loadImg( const std::string &path )
{
    if ( !FileExists( path.c_str() ) ) return {};
    Image img = LoadImage( path.c_str() );
    ImageFormat( &img, PIXELFORMAT_UNCOMPRESSED_R8G8B8A8 );
    return img;
}

void tile( Image &dst, const Image &src, int index, int x, int y, bool flip = false )
{
    if ( !src.data ) return;
    int cols = std::max( 1, src.width / Tile ), rows = std::max( 1, src.height / Tile );
    index %= cols * rows;
    Rectangle s = { (float)( index % cols ) * Tile, (float)( index / cols ) * Tile, (float)Tile, (float)Tile };
    if ( flip )
    {
        Image part = ImageFromImage( src, s );
        ImageFlipHorizontal( &part );
        ImageDraw( &dst, part, { 0, 0, (float)Tile, (float)Tile }, { (float)x, (float)y, (float)Tile, (float)Tile }, WHITE );
        UnloadImage( part );
        return;
    }
    ImageDraw( &dst, src, s, { (float)x, (float)y, (float)Tile, (float)Tile }, WHITE );
}

/** @brief Draws an animation's first frame with its anchor at (x, y); a labelled box when the sheet is missing. */
void sprite( Image &dst, const std::string &name, const std::string &anim, int x, int y, Color standIn, bool flip = false )
{
    const CpuSheet &s = sheet( name );
    if ( !s.ok() )
    {
        ImageDrawRectangle( &dst, x - 10, y - 24, 20, 24, standIn );
        label( dst, name.substr( 0, 2 ), x - 8, y - 18, BLACK );
        return;
    }
    int f = 0;
    for ( const std::string &a : { anim, std::string( "idle" ), std::string( "move" ), std::string( "fly" ) } )
    {
        auto it = s.m_first.find( a );
        if ( it != s.m_first.end() )
        {
            f = it->second;
            break;
        }
    }
    int   cols = std::max( 1, s.m_img.width / s.m_fw );
    Image part = ImageFromImage( s.m_img, { (float)( f % cols ) * s.m_fw, (float)( f / cols ) * s.m_fh, (float)s.m_fw, (float)s.m_fh } );
    int   ax = s.m_ax;
    if ( flip ) ImageFlipHorizontal( &part ), ax = s.m_fw - ax;
    ImageDraw( &dst, part, { 0, 0, (float)s.m_fw, (float)s.m_fh }, { (float)( x - ax ), (float)( y - s.m_ay ), (float)s.m_fw, (float)s.m_fh }, WHITE );
    UnloadImage( part );
}

/** @brief Tiny 3x5 letters for labels (raylib's text needs a window). */
void label( Image &dst, const std::string &text, int x, int y, Color c )
{
    static const std::map<char, const char *> glyphs = {
        { '0', "111101101101111" }, { '1', "010110010010111" }, { '2', "111001111100111" }, { '3', "111001111001111" },
        { '4', "101101111001001" }, { '5', "111100111001111" }, { '6', "111100111101111" }, { '7', "111001001001001" },
        { '8', "111101111101111" }, { '9', "111101111001111" }, { '>', "100010001010100" }, { '-', "000000111000000" } };
    for ( char ch : text )
    {
        char up = ch >= 'a' && ch <= 'z' ? ch - 32 : ch;
        auto it = glyphs.find( up );
        // Letters without a glyph: a filled box with a notch, still telling places apart by colour.
        const char *g = it != glyphs.end() ? it->second : "111101101101111";
        if ( it == glyphs.end() && up >= 'A' && up <= 'Z' )
        {
            static const char *letters[26] = {
                "010101111101101", "110101110101110", "011100100100011", "110101101101110", "111100110100111", "111100110100100",
                "011100101101011", "101101111101101", "111010010010111", "001001001101010", "101101110101101", "100100100100111",
                "101111111101101", "110101101101101", "010101101101010", "110101110100100", "010101101110011", "110101110101101",
                "011100010001110", "111010010010010", "101101101101111", "101101101101010", "101101111111101", "101101010101101",
                "101101010010010", "111001010100111" };
            g = letters[up - 'A'];
        }
        for ( int i = 0; i < 15; ++i )
            if ( g[i] == '1' ) ImageDrawRectangle( &dst, x + ( i % 3 ) * 2, y + ( i / 3 ) * 2, 2, 2, c );
        x += 8;
    }
}

uint32_t hashCell( int x, int y )
{
    uint32_t h = (uint32_t)x * 73856093u ^ (uint32_t)y * 19349663u;
    h ^= h >> 13;
    h *= 0x5bd1e995u;
    h ^= h >> 15;
    return h;
}

int render( const Level &L, const std::string &out, int x0, int y0, int w, int h, float scale,
            const std::string &deaths = "" )
{
    std::string theme = L.key( "theme", "station" ), tdir = g_assets + "tiles/" + theme + "/";
    Image       ta = loadImg( tdir + "terrain_a.png" ), tb = loadImg( tdir + "terrain_b.png" ), back = loadImg( tdir + "back.png" );
    Image       plat = loadImg( tdir + "platform.png" ), blocks = loadImg( tdir + "blocks.png" ), liquid = loadImg( tdir + "liquid.png" );
    if ( !tb.data ) tb = ta;
    Image img = GenImageColor( w * Tile, h * Tile, { 12, 14, 30, 255 } );
    // The sky: the background's layers side by side (no parallax).
    std::string bdir = g_assets + "bg/" + L.key( "bg", theme + "_a" ) + "/";
    for ( int n = 0; n < 4; ++n )
    {
        Image layer = loadImg( bdir + "layer" + std::to_string( n ) + ".png" );
        if ( !layer.data ) continue;
        for ( int ty = 0; ty < img.height; ty += layer.height )
            for ( int tx = 0; tx < img.width; tx += layer.width )
                ImageDraw( &img, layer, { 0, 0, (float)layer.width, (float)layer.height }, { (float)tx, (float)ty, (float)layer.width, (float)layer.height }, WHITE );
        UnloadImage( layer );
    }
    auto variants = []( const Image &i ) { return i.height >= 512 ? i.height / 512 : 1; };
    for ( int y = y0; y < y0 + h; ++y )
        for ( int x = x0; x < x0 + w; ++x )
        {
            if ( !L.inside( x, y ) ) continue;
            const Cell &c = L.at( x, y );
            int         px = ( x - x0 ) * Tile, py = ( y - y0 ) * Tile;
            int         v = (int)( ( hashCell( x, y ) >> 7 ) & 255 );
            if ( c.m_interior )
                tile( img, back, ( v % variants( back ) ) * 256 + L.backMask( x, y ), px, py );
            if ( !back.data && c.m_interior ) ImageDrawRectangle( &img, px, py, Tile, Tile, { 34, 38, 54, 255 } );
            int row = -1, col = 0;
            switch ( c.m_kind )
            {
            case CellE::TERRAIN_A:
            case CellE::FAKE: tile( img, ta, ( v % variants( ta ) ) * 256 + L.terrainMask( x, y ), px, py ); break;
            case CellE::TERRAIN_B: tile( img, tb, ( v % variants( tb ) ) * 256 + L.terrainMask( x, y ), px, py ); break;
            case CellE::PLATFORM:
            {
                bool l = L.at( x - 1, y ).m_kind == CellE::PLATFORM, r = L.at( x + 1, y ).m_kind == CellE::PLATFORM;
                if ( plat.data ) tile( img, plat, l && r ? 2 : l ? 3 : r ? 1 : 0, px, py );
                else
                    ImageDrawRectangle( &img, px, py, Tile, 8, { 200, 180, 90, 255 } );
                break;
            }
            case CellE::BREAKABLE: row = 0; break;
            case CellE::CRUMBLE: row = 1; break;
            case CellE::DOOR_BLUE: row = 2; break;
            case CellE::DOOR_GOLD: row = 3; break;
            case CellE::TOGGLE: row = ( c.m_aux & 8 ) ? 5 : 4; break;
            case CellE::CONVEYOR: row = 6; break;
            case CellE::SPIKE_UP: row = 7, col = 0; break;
            case CellE::SPIKE_DOWN: row = 7, col = 1; break;
            case CellE::SPIKE_LEFT: row = 7, col = 2; break;
            case CellE::SPIKE_RIGHT: row = 7, col = 3; break;
            case CellE::LIQUID:
                if ( liquid.data ) tile( img, liquid, L.at( x, y - 1 ).m_kind != CellE::LIQUID ? 0 : 4, px, py );
                else
                    ImageDrawRectangle( &img, px, py, Tile, Tile, { 140, 40, 200, 255 } );
                break;
            default: break;
            }
            if ( row >= 0 )
            {
                if ( blocks.data ) tile( img, blocks, row * ( blocks.width / Tile ) + col, px, py );
                else
                    ImageDrawRectangle( &img, px + 2, py + 2, Tile - 4, Tile - 4, { 200, 120, 60, 255 } );
            }
            if ( c.m_secret ) ImageDrawRectangleLines( &img, { (float)px + 1, (float)py + 1, Tile - 2.0f, Tile - 2.0f }, 1, { 230, 80, 230, 255 } );
            if ( c.m_kind == CellE::FAKE ) ImageDrawRectangleLines( &img, { (float)px + 3, (float)py + 3, Tile - 6.0f, Tile - 6.0f }, 1, { 230, 80, 230, 255 } );
        }
    // What the map places, at their places.
    for ( const Spawn &s : L.m_spawns )
    {
        if ( s.m_x < x0 - 3 || s.m_x >= x0 + w + 3 || s.m_y < y0 - 3 || s.m_y >= y0 + h + 3 ) continue;
        int         cx = ( s.m_x - x0 ) * Tile + Tile / 2, cy = ( s.m_y - y0 ) * Tile + Tile / 2, foot = ( s.m_y - y0 + 1 ) * Tile;
        std::string a0 = s.m_args.empty() ? "" : s.m_args[0];
        const std::string &k = s.m_kind;
        if ( k == "crystal" ) sprite( img, "items", "crystal", cx, cy, { 80, 230, 255, 255 } );
        else if ( k == "treasure" )
            sprite( img, "items", a0.empty() ? "gem" : a0, cx, cy, { 255, 220, 60, 255 } );
        else if ( k == "health" )
            sprite( img, "items", a0 == "big" ? "health_big" : "health", cx, cy, { 90, 255, 120, 255 } );
        else if ( k == "key" )
            sprite( img, "items", a0 == "gold" ? "key_gold" : "key_blue", cx, cy, { 60, 120, 255, 255 } );
        else if ( k == "ammo" )
            sprite( img, "items", "ammo", cx, cy, { 255, 160, 60, 255 } );
        else if ( k == "weapon" )
            sprite( img, "items", "weapon_" + a0, cx, cy, { 255, 120, 255, 255 } );
        else if ( k == "power" )
            sprite( img, "items", "power_" + a0, cx, cy, { 255, 120, 255, 255 } );
        else if ( k == "enemy" || k == "boss" )
        {
            const EnemyDef *d = enemyDef( a0 );
            int             kind = 0;
            if ( !d ) d = bossDef( a0, kind );
            bool air = d && ( d->m_brain == BrainE::FLIER || d->m_brain == BrainE::GUNSHIP || d->m_brain == BrainE::FLOATER );
            bool left = std::find( s.m_args.begin(), s.m_args.end(), "left" ) != s.m_args.end();
            sprite( img, a0, air ? "fly" : "move", cx, air ? cy + ( d ? d->m_h / 2 : 0 ) : foot, { 255, 110, 50, 255 }, left );
            if ( std::find( s.m_args.begin(), s.m_args.end(), "ambush" ) != s.m_args.end() )
                label( img, "A", cx - 3, cy - 30, { 255, 80, 80, 255 } );
        }
        else if ( k == "start" )
            sprite( img, "hero", "idle", cx, foot, { 240, 140, 40, 255 } );
        else if ( k == "exit" )
            sprite( img, "objects", "exit_closed", cx, foot, { 230, 60, 230, 255 } );
        else if ( k == "checkpoint" )
            sprite( img, "objects", "checkpoint_off", cx, foot, { 80, 255, 180, 255 } );
        else if ( k == "teleport" )
        {
            sprite( img, "objects", "teleporter", cx, foot, { 100, 180, 255, 255 } );
            label( img, std::string( 1, s.m_ch ) + ">" + a0, cx - 12, cy - 30, WHITE );
        }
        else if ( k == "switch" )
        {
            sprite( img, "objects", "switch_off", cx, foot, { 255, 255, 100, 255 } );
            label( img, a0, cx - 3, cy - 30, WHITE );
        }
        else if ( k == "spring" )
            sprite( img, "objects", "spring", cx, foot, { 120, 255, 120, 255 } );
        else if ( k == "sign" )
            sprite( img, "objects", "sign", cx, foot, { 200, 200, 255, 255 } );
        else if ( k == "laser" )
            sprite( img, "objects", "laser_emitter", cx, foot, { 255, 60, 60, 255 } );
        else if ( k == "mover" )
            for ( int i = 0; i < s.m_w; ++i )
            {
                int px = ( s.m_x + i - x0 ) * Tile, py = ( s.m_y - y0 ) * Tile;
                if ( plat.data ) tile( img, plat, s.m_w == 1 ? 0 : i == 0 ? 1 : i == s.m_w - 1 ? 3 : 2, px, py );
                if ( i == 0 ) label( img, "M", px + 2, py + 12, { 255, 255, 0, 255 } );
            }
        else if ( k == "light" )
            ImageDrawCircle( &img, cx, cy, 3, { 255, 240, 160, 255 } );
        else if ( k == "crusher" )
            ImageDrawRectangle( &img, cx - 14, cy - 16, 28, 26, { 120, 124, 140, 255 } );
    }
    // The knockouts of this level from a death record (level x y cause ...): a circle per cell, larger the more.
    if ( !deaths.empty() )
    {
        std::ifstream                              in( deaths );
        std::string                                line;
        std::map<std::pair<int, int>, int>         cells;
        std::map<std::pair<int, int>, std::string> cause;
        while ( std::getline( in, line ) )
        {
            char id[64] = {}, what[64] = {};
            int  x = 0, y = 0;
            if ( sscanf( line.c_str(), "%63s %d %d %63s", id, &x, &y, what ) < 4 || L.m_id != id ||
                 std::string( what ) == "giveup" )
                continue;
            std::pair<int, int> c = { x / Tile, ( y - 1 ) / Tile };
            ++cells[c];
            cause[c] = what;
        }
        for ( const auto &[c, n] : cells )
        {
            int px = ( c.first - x0 ) * Tile + Tile / 2, py = ( c.second - y0 ) * Tile + Tile / 2;
            int r = 8 + 3 * std::min( n, 8 );
            ImageDrawCircle( &img, px, py, r, { 255, 40, 40, 150 } );
            ImageDrawCircleLines( &img, px, py, r, { 255, 230, 230, 255 } );
            label( img, std::to_string( n ) + " " + cause[c], px + r + 2, py - 4, { 255, 220, 220, 255 } );
        }
    }
    if ( scale != 1.0f ) ImageResizeNN( &img, (int)( img.width * scale ), (int)( img.height * scale ) );
    bool ok = ExportImage( img, out.c_str() );
    UnloadImage( img );
    return ok ? 0 : 1;
}

}   // namespace

int main( int argc, char **argv )
{
    SetTraceLogLevel( LOG_WARNING );
    if ( argc < 3 )
    {
        printf( "usage: KeplerTool check <level.txt> [overview.png]\n       KeplerTool checkall <folder>\n"
                "       KeplerTool render <level.txt> <out.png> [scale | x y w h]\n"
                "       KeplerTool deaths <level.txt> <deaths.txt> <out.png> [scale]\n" );
        return 2;
    }
    if ( const char *a = getenv( "KEPLER_ASSETS_DIR" ) ) g_assets = std::string( a ) + "/";
    std::string cmd = argv[1];
    if ( cmd == "deaths" )
    {
        if ( argc < 5 ) return 2;
        Level       level;
        std::string error;
        if ( !level.load( argv[2], error ) )
        {
            printf( "FAIL  %s: %s\n", argv[2], error.c_str() );
            return 1;
        }
        return render( level, argv[4], 0, 0, level.m_w, level.m_h, argc >= 6 ? (float)atof( argv[5] ) : 0.5f, argv[3] );
    }
    if ( cmd == "render" )
    {
        if ( argc < 4 ) return 2;
        Level       level;
        std::string error;
        if ( !level.load( argv[2], error ) )
        {
            printf( "FAIL  %s: %s\n", argv[2], error.c_str() );
            return 1;
        }
        if ( argc >= 8 )
            return render( level, argv[3], atoi( argv[4] ), atoi( argv[5] ), atoi( argv[6] ), atoi( argv[7] ), 2.0f );
        return render( level, argv[3], 0, 0, level.m_w, level.m_h, argc >= 5 ? (float)atof( argv[4] ) : 0.5f );
    }
    std::vector<std::string> files;
    if ( cmd == "check" ) files.push_back( argv[2] );
    else if ( cmd == "checkall" )
    {
        for ( const auto &e : std::filesystem::directory_iterator( argv[2] ) )
            if ( e.path().extension() == ".txt" ) files.push_back( e.path().string() );
        std::sort( files.begin(), files.end() );
    }
    else
    {
        printf( "unknown command %s\n", cmd.c_str() );
        return 2;
    }
    bool all = true;
    for ( const std::string &f : files )
    {
        Level       level;
        std::string error;
        if ( !level.load( f, error ) )
        {
            printf( "FAIL  %s: %s\n", f.c_str(), error.c_str() );
            all = false;
            continue;
        }
        std::string report;
        bool        ok = checkLevel( level, cmd == "check" && argc > 3 ? argv[3] : "", report );
        printf( "%s", report.c_str() );
        fflush( stdout );
        all = all && ok;
    }
    return all ? 0 : 1;
}
