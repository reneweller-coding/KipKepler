/**
 * @file Assets.cpp
 * @brief Loading sprite sheets, tile sets, backgrounds and fonts, with stand-ins for what is missing.
 * @author Rene Weller
 */
#include "Assets.h"

#include "Level.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>

namespace kepler
{

namespace fs = std::filesystem;

const std::string &assetDir()
{
    static std::string dir;
    if ( dir.empty() )
    {
        std::string beside = std::string( GetApplicationDirectory() ) + "assets/";
        std::error_code e;
        if ( fs::is_directory( fs::path( beside ), e ) ) dir = beside;
        else
            dir = std::string( KEPLER_ASSETS ) + "/";
    }
    return dir;
}

int nextCodepoint( const std::string &s, size_t &i )
{
    unsigned char c = (unsigned char)s[i++];
    if ( c < 0x80 ) return c;
    int n = c >= 0xF0 ? 3 : c >= 0xE0 ? 2 : 1;
    int cp = c & ( 0x3F >> n );
    for ( int k = 0; k < n && i < s.size(); ++k ) cp = ( cp << 6 ) | ( (unsigned char)s[i++] & 0x3F );
    return cp;
}

// ---------------------------------------------------------------------------------------------------------- Sheet

const Anim *Sheet::anim( const std::string &name ) const
{
    auto it = m_anims.find( name );
    return it == m_anims.end() ? nullptr : &it->second;
}

int Sheet::frame( const std::string &name, float t ) const
{
    const Anim *a = anim( name );
    if ( !a ) a = anim( m_firstAnim );
    if ( !a || a->m_frames.empty() ) return 0;
    int i = (int)( t * a->m_fps );
    int n = (int)a->m_frames.size();
    i = a->m_loop ? ( ( i % n ) + n ) % n : std::min( std::max( i, 0 ), n - 1 );
    return a->m_frames[i];
}

bool Sheet::done( const std::string &name, float t ) const
{
    const Anim *a = anim( name );
    return !a || t >= a->length();
}

Vector2 Sheet::point( const std::string &name, Vector2 fallback ) const
{
    auto it = m_points.find( name );
    return it == m_points.end() ? fallback : it->second;
}

void Sheet::draw( int frame, float x, float y, bool flip, Color tint, bool glow, float angle ) const
{
    const Texture2D &t = glow ? m_glow : m_tex;
    if ( glow && !m_hasGlow ) return;
    if ( t.id == 0 ) return;
    int       fx = ( frame % m_cols ) * m_fw, fy = ( frame / m_cols ) * m_fh;
    Rectangle src = { (float)fx, (float)fy, (float)( flip ? -m_fw : m_fw ), (float)m_fh };
    float     ax = flip ? m_fw - m_ax : m_ax;
    Rectangle dst = { std::floor( x ), std::floor( y ), (float)m_fw, (float)m_fh };
    DrawTexturePro( t, src, dst, { ax, (float)m_ay }, angle, tint );
}

namespace
{

Texture2D loadTex( const std::string &path )
{
    if ( !FileExists( path.c_str() ) ) return {};
    if ( !IsWindowReady() )
    {
        // Without a window (the autopilot test runs without the graphics card): only the size, nothing uploaded.
        Image     img = LoadImage( path.c_str() );
        Texture2D t = {};
        t.width = img.width, t.height = img.height;
        UnloadImage( img );
        return t;
    }
    Texture2D t = LoadTexture( path.c_str() );
    SetTextureFilter( t, TEXTURE_FILTER_POINT );
    SetTextureWrap( t, TEXTURE_WRAP_CLAMP );
    return t;
}

/** @brief A magenta-and-dark checker box: a frame for what has no picture yet. */
Texture2D standInTex( int w, int h, Color a, Color b )
{
    if ( !IsWindowReady() ) return {};
    Image img = GenImageChecked( w, h, std::max( 2, w / 4 ), std::max( 2, h / 4 ), a, b );
    ImageDrawRectangleLines( &img, { 0, 0, (float)w, (float)h }, 1, BLACK );
    Texture2D t = LoadTextureFromImage( img );
    UnloadImage( img );
    SetTextureFilter( t, TEXTURE_FILTER_POINT );
    return t;
}

void readSheetText( Sheet &s, const std::string &path )
{
    std::ifstream in( path );
    std::string   line;
    while ( std::getline( in, line ) )
    {
        if ( line.empty() || line[0] == '#' ) continue;
        std::vector<std::string> w = words( line );
        if ( w.empty() ) continue;
        if ( w[0] == "frame" && w.size() >= 3 ) s.m_fw = atoi( w[1].c_str() ), s.m_fh = atoi( w[2].c_str() );
        else if ( w[0] == "anchor" && w.size() >= 3 )
            s.m_ax = atoi( w[1].c_str() ), s.m_ay = atoi( w[2].c_str() );
        else if ( w[0] == "point" && w.size() >= 4 )
            s.m_points[w[1]] = { (float)atof( w[2].c_str() ), (float)atof( w[3].c_str() ) };
        else if ( w[0] == "anim" && w.size() >= 5 )
        {
            Anim a;
            a.m_fps = (float)atof( w[2].c_str() );
            if ( a.m_fps <= 0 ) a.m_fps = 10;
            a.m_loop = w[3] != "once";
            for ( size_t i = 4; i < w.size(); ++i )
                if ( w[i][0] != '#' ) a.m_frames.push_back( atoi( w[i].c_str() ) );
                else
                    break;
            if ( s.m_firstAnim.empty() ) s.m_firstAnim = w[1];
            s.m_anims[w[1]] = a;
        }
    }
}

/** @brief A stand-in terrain sheet: one variant of all 256 masks, lit edges where a side is open. */
Texture2D standInTerrain( Color base, bool back )
{
    if ( !IsWindowReady() ) return {};
    Image img = GenImageColor( 512, 512, BLANK );
    for ( int m = 0; m < 256; ++m )
    {
        int x = ( m % 16 ) * 32, y = ( m / 16 ) * 32;
        ImageDrawRectangle( &img, x, y, 32, 32, base );
        Color hi = ColorBrightness( base, 0.35f ), lo = ColorBrightness( base, -0.45f );
        if ( back )
        {
            ImageDrawRectangle( &img, x + 2, y + 2, 28, 28, ColorBrightness( base, 0.06f ) );
            if ( !( m & 1 ) ) ImageDrawRectangle( &img, x, y, 32, 3, lo );
            if ( !( m & 16 ) ) ImageDrawRectangle( &img, x, y + 29, 32, 3, lo );
            if ( !( m & 4 ) ) ImageDrawRectangle( &img, x + 29, y, 3, 32, lo );
            if ( !( m & 64 ) ) ImageDrawRectangle( &img, x, y, 3, 32, lo );
            continue;
        }
        ImageDrawRectangle( &img, x + 6, y + 6, 20, 20, ColorBrightness( base, -0.08f ) );
        if ( !( m & 1 ) ) ImageDrawRectangle( &img, x, y, 32, 4, hi );
        if ( !( m & 16 ) ) ImageDrawRectangle( &img, x, y + 28, 32, 4, lo );
        if ( !( m & 4 ) ) ImageDrawRectangle( &img, x + 29, y, 3, 32, lo );
        if ( !( m & 64 ) ) ImageDrawRectangle( &img, x, y, 3, 32, hi );
    }
    Texture2D t = LoadTextureFromImage( img );
    UnloadImage( img );
    SetTextureFilter( t, TEXTURE_FILTER_POINT );
    return t;
}

}   // namespace

// --------------------------------------------------------------------------------------------------------- Assets

Assets &assets()
{
    static Assets a;
    return a;
}

const Sheet &Assets::sheet( const std::string &name )
{
    return sheetIn( "sprites", name );
}

const Sheet &Assets::sheetIn( const std::string &folder, const std::string &name )
{
    std::string key = folder + "/" + name;
    auto        it = m_sheets.find( key );
    if ( it != m_sheets.end() ) return *it->second;
    auto        s = std::make_unique<Sheet>();
    std::string base = assetDir() + folder + "/" + name;
    s->m_tex = loadTex( base + ".png" );
    if ( s->m_tex.width > 0 )
    {
        readSheetText( *s, base + ".txt" );
        s->m_glow = loadTex( base + "_glow.png" );
        s->m_hasGlow = s->m_glow.id != 0;
        if ( s->m_fw <= 0 ) s->m_fw = s->m_tex.width;
        if ( s->m_fh <= 0 ) s->m_fh = s->m_tex.height;
        s->m_cols = std::max( 1, s->m_tex.width / s->m_fw );
    }
    else
    {
        s->m_standIn = true;
        s->m_fw = s->m_fh = 24;
        s->m_ax = 12, s->m_ay = 24;
        s->m_tex = standInTex( 24, 24, { 220, 40, 200, 255 }, { 60, 10, 60, 255 } );
        s->m_cols = 1;
    }
    m_sheets[key] = std::move( s );
    return *m_sheets[key];
}

const TileSet &Assets::tiles( const std::string &theme )
{
    auto it = m_tiles.find( theme );
    if ( it != m_tiles.end() ) return *it->second;
    auto        t = std::make_unique<TileSet>();
    std::string dir = assetDir() + "tiles/" + theme + "/";
    t->m_theme = theme;
    auto both = [&]( const char *name, Texture2D &tex, Texture2D &glow )
    {
        tex = loadTex( dir + name + ".png" );
        glow = loadTex( dir + name + "_glow.png" );
    };
    both( "terrain_a", t->m_terrainA, t->m_terrainAGlow );
    both( "terrain_b", t->m_terrainB, t->m_terrainBGlow );
    both( "back", t->m_back, t->m_backGlow );
    both( "blocks", t->m_blocks, t->m_blocksGlow );
    both( "liquid", t->m_liquid, t->m_liquidGlow );
    both( "deco", t->m_deco, t->m_decoGlow );
    t->m_platform = loadTex( dir + "platform.png" );
    if ( !t->m_terrainA.id )
    {
        t->m_standIn = true;
        t->m_terrainA = standInTerrain( { 92, 110, 140, 255 }, false );
        t->m_terrainB = standInTerrain( { 110, 90, 76, 255 }, false );
        t->m_back = standInTerrain( { 30, 34, 50, 255 }, true );
    }
    if ( !t->m_terrainB.id ) t->m_terrainB = t->m_terrainA;
    if ( !t->m_back.id ) t->m_back = standInTerrain( { 30, 34, 50, 255 }, true );
    std::ifstream in( dir + "deco.txt" );
    std::string   line;
    while ( std::getline( in, line ) )
    {
        std::vector<std::string> w = words( line );
        if ( w.size() < 7 || w[0][0] == '#' ) continue;
        Deco d;
        d.m_name = w[0];
        d.m_src = { (float)atof( w[1].c_str() ), (float)atof( w[2].c_str() ), (float)atof( w[3].c_str() ),
                    (float)atof( w[4].c_str() ) };
        d.m_place = w[5] == "floor" ? 1 : w[5] == "ceiling" ? 2 : w[5] == "edge" ? 3 : 0;
        d.m_weight = (float)atof( w[6].c_str() );
        d.m_glow = w.size() > 7 && w[7] == "glow";
        t->m_decos.push_back( d );
    }
    // The light a glowing decoration casts takes the colour of its glow.
    if ( FileExists( ( dir + "deco_glow.png" ).c_str() ) )
    {
        Image glow = LoadImage( ( dir + "deco_glow.png" ).c_str() );
        ImageFormat( &glow, PIXELFORMAT_UNCOMPRESSED_R8G8B8A8 );
        const unsigned char *px = (const unsigned char *)glow.data;
        for ( Deco &d : t->m_decos )
        {
            long r = 0, g = 0, b = 0, n = 0;
            for ( int y = (int)d.m_src.y; y < (int)( d.m_src.y + d.m_src.height ) && y < glow.height; ++y )
                for ( int x = (int)d.m_src.x; x < (int)( d.m_src.x + d.m_src.width ) && x < glow.width; ++x )
                {
                    const unsigned char *p = px + ( (size_t)y * glow.width + x ) * 4;
                    if ( p[3] < 128 ) continue;
                    r += p[0], g += p[1], b += p[2], ++n;
                }
            if ( n > 0 )
            {
                // Brighten the mean to full value: a light, not a surface.
                float m = (float)std::max( { r, g, b } ) / n;
                float k = m > 1 ? 230.0f / m : 1.0f;
                d.m_light = { (unsigned char)std::min( 255.0f, r / n * k ), (unsigned char)std::min( 255.0f, g / n * k ),
                              (unsigned char)std::min( 255.0f, b / n * k ), 255 };
            }
        }
        UnloadImage( glow );
    }
    std::ifstream tin( dir + "tints.txt" );
    while ( std::getline( tin, line ) )
    {
        std::vector<std::string> w = words( line );
        if ( w.size() < 4 || w[0][0] == '#' ) continue;
        int i = atoi( w[0].c_str() );
        if ( i >= 0 && i < 4 )
            t->m_tints[i] = { (unsigned char)atoi( w[1].c_str() ), (unsigned char)atoi( w[2].c_str() ),
                              (unsigned char)atoi( w[3].c_str() ), 255 };
    }
    m_tiles[theme] = std::move( t );
    return *m_tiles[theme];
}

const Background &Assets::background( const std::string &name )
{
    auto it = m_backgrounds.find( name );
    if ( it != m_backgrounds.end() ) return *it->second;
    auto        b = std::make_unique<Background>();
    std::string dir = assetDir() + "bg/" + name + "/";
    std::ifstream in( dir + "bg.txt" );
    std::string   line;
    std::map<int, BgLayer> layers;
    while ( std::getline( in, line ) )
    {
        std::vector<std::string> w = words( line );
        if ( w.empty() || w[0][0] == '#' ) continue;
        if ( w[0] == "fill" && w.size() >= 7 )
        {
            b->m_top = { (unsigned char)atoi( w[1].c_str() ), (unsigned char)atoi( w[2].c_str() ),
                         (unsigned char)atoi( w[3].c_str() ), 255 };
            b->m_bottom = { (unsigned char)atoi( w[4].c_str() ), (unsigned char)atoi( w[5].c_str() ),
                            (unsigned char)atoi( w[6].c_str() ), 255 };
        }
        else if ( w[0] == "fore" && w.size() >= 4 )
        {
            b->m_fore.m_px = (float)atof( w[1].c_str() );
            b->m_fore.m_py = (float)atof( w[2].c_str() );
            b->m_fore.m_yoff = (float)atof( w[3].c_str() );
        }
        else if ( w[0].rfind( "layer", 0 ) == 0 && w.size() >= 4 )
        {
            int     n = atoi( w[0].c_str() + 5 );
            BgLayer l;
            l.m_px = (float)atof( w[1].c_str() );
            l.m_py = (float)atof( w[2].c_str() );
            l.m_yoff = (float)atof( w[3].c_str() );
            l.m_scroll = w.size() > 4 && w[4][0] != '#' ? (float)atof( w[4].c_str() ) : 0;
            layers[n] = l;
        }
    }
    for ( int n = 0; n < 6; ++n )
    {
        Texture2D t = loadTex( dir + "layer" + std::to_string( n ) + ".png" );
        if ( !t.id ) continue;
        SetTextureWrap( t, TEXTURE_WRAP_REPEAT );
        BgLayer l;
        if ( layers.count( n ) ) l = layers[n];
        else
            l.m_px = 0.05f + 0.15f * n, l.m_py = 0.03f + 0.08f * n;
        l.m_tex = t;
        l.m_glow = loadTex( dir + "layer" + std::to_string( n ) + "_glow.png" );
        b->m_layers.push_back( l );
    }
    if ( b->m_layers.empty() ) b->m_standIn = true;
    b->m_fore.m_tex = loadTex( dir + "fore.png" );
    if ( b->m_fore.m_tex.id ) SetTextureWrap( b->m_fore.m_tex, TEXTURE_WRAP_REPEAT );
    m_backgrounds[name] = std::move( b );
    return *m_backgrounds[name];
}

const Texture2D *Assets::texture( const std::string &path )
{
    auto it = m_textures.find( path );
    if ( it == m_textures.end() ) it = m_textures.emplace( path, loadTex( assetDir() + path ) ).first;
    return it->second.id ? &it->second : nullptr;
}

const PixelFont &Assets::font( bool big, bool outline )
{
    int i = big ? ( outline ? 2 : 1 ) : 0;
    if ( m_fonts[i] ) return *m_fonts[i];
    auto        f = std::make_unique<PixelFont>();
    std::string base = assetDir() + "fonts/" + ( big ? ( outline ? "big_outline" : "big" ) : "small" );
    f->m_tex = loadTex( base + ".png" );
    if ( !f->m_tex.id && outline ) f->m_tex = loadTex( assetDir() + "fonts/big.png" ), base = assetDir() + "fonts/big";
    if ( f->m_tex.id )
    {
        f->m_standIn = false;
        // The outlined font shares the plain one's layout when it has no list of its own.
        std::string list = base + ".txt";
        if ( !FileExists( list.c_str() ) ) list = assetDir() + "fonts/big.txt";
        std::ifstream in( list );
        std::string   line;
        int           index = 0;
        while ( std::getline( in, line ) )
        {
            std::vector<std::string> w = words( line );
            if ( w.empty() || w[0][0] == '#' ) continue;
            if ( w[0] == "cell" && w.size() >= 3 ) f->m_cw = atoi( w[1].c_str() ), f->m_ch = atoi( w[2].c_str() );
            else if ( w[0] == "baseline" && w.size() >= 2 )
                f->m_base = atoi( w[1].c_str() );
            else if ( w.size() >= 2 )
            {
                int cp = (int)strtol( w[0].c_str(), nullptr, 16 );
                f->m_index[cp] = index++;
                f->m_advance[cp] = atoi( w[1].c_str() );
            }
        }
    }
    else
    {
        f->m_standIn = true;
        f->m_scale = big ? 2 : 1;
        f->m_ch = big ? 20 : 10;
    }
    m_fonts[i] = std::move( f );
    return *m_fonts[i];
}

void Assets::unload()
{
    for ( auto &[k, s] : m_sheets )
    {
        if ( s->m_tex.id ) UnloadTexture( s->m_tex );
        if ( s->m_glow.id ) UnloadTexture( s->m_glow );
    }
    m_sheets.clear();
    m_tiles.clear();
    m_backgrounds.clear();
    for ( auto &[k, t] : m_textures )
        if ( t.id ) UnloadTexture( t );
    m_textures.clear();
}

void drawBackground( const Background &bg, int w, int h, float camX, float rise, float clock, bool glow )
{
    if ( !glow ) DrawRectangleGradientV( 0, 0, w, h, bg.m_top, bg.m_bottom );
    for ( size_t i = 0; i < bg.m_layers.size(); ++i )
    {
        const BgLayer   &l = bg.m_layers[i];
        const Texture2D &t = glow ? l.m_glow : l.m_tex;
        if ( !t.id ) continue;
        float tw = (float)t.width, th = (float)t.height;
        float ox = std::fmod( -camX * l.m_px + l.m_scroll * clock, tw );
        if ( ox > 0 ) ox -= tw;
        float y = std::floor( l.m_yoff + rise * l.m_py );
        Color tint = glow ? Color{ 110, 110, 110, 255 } : WHITE;
        for ( float x = std::floor( ox ); x < w; x += tw )
        {
            DrawTexture( t, (int)x, (int)y, tint );
            // The first row continues upwards, the last downwards.
            if ( y > 0 ) DrawTexturePro( t, { 0, 0, tw, 1 }, { x, 0, tw, y }, { 0, 0 }, 0, tint );
            if ( y + th < h ) DrawTexturePro( t, { 0, th - 1, tw, 1 }, { x, y + th, tw, h - ( y + th ) }, { 0, 0 }, 0, tint );
        }
    }
}

void drawForeground( const Background &bg, int w, int h, float camX, float lag )
{
    const BgLayer &l = bg.m_fore;
    if ( !l.m_tex.id ) return;
    float tw = (float)l.m_tex.width, th = (float)l.m_tex.height;
    float ox = std::fmod( -camX * ( l.m_px > 0 ? l.m_px : 1.3f ), tw );
    if ( ox > 0 ) ox -= tw;
    // The top row at the y offset on a 400 high view (20 px higher on 360), plus a bounded sway.
    float sway = std::clamp( -lag * std::max( 0.1f, l.m_py - 1 ), -10.0f, 10.0f );
    float y = std::floor( l.m_yoff + ( h - th ) * 0.5f + sway );
    for ( float x = std::floor( ox ); x < w; x += tw ) DrawTexture( l.m_tex, (int)x, (int)y, WHITE );
}

// ----------------------------------------------------------------------------------------------------- PixelFont

int PixelFont::draw( const std::string &text, float x, float y, Color tint ) const
{
    if ( m_standIn )
    {
        Font f = GetFontDefault();
        DrawTextEx( f, text.c_str(), { std::floor( x ), std::floor( y ) }, 10.0f * m_scale, (float)m_scale, tint );
        return (int)MeasureTextEx( f, text.c_str(), 10.0f * m_scale, (float)m_scale ).x;
    }
    int    cols = std::max( 1, m_tex.width / m_cw );
    float  px = std::floor( x );
    size_t i = 0;
    while ( i < text.size() )
    {
        int  cp = nextCodepoint( text, i );
        auto it = m_index.find( cp );
        if ( it == m_index.end() ) it = m_index.find( '?' );
        if ( it == m_index.end() ) continue;
        int g = it->second;
        DrawTextureRec( m_tex, { (float)( g % cols ) * m_cw, (float)( g / cols ) * m_ch, (float)m_cw, (float)m_ch },
                        { px, std::floor( y ) }, tint );
        auto a = m_advance.find( cp );
        px += a == m_advance.end() ? m_cw : a->second;
    }
    return (int)( px - std::floor( x ) );
}

int PixelFont::width( const std::string &text ) const
{
    if ( m_standIn ) return (int)MeasureTextEx( GetFontDefault(), text.c_str(), 10.0f * m_scale, (float)m_scale ).x;
    int    w = 0;
    size_t i = 0;
    while ( i < text.size() )
    {
        int  cp = nextCodepoint( text, i );
        auto a = m_advance.find( cp );
        w += a == m_advance.end() ? m_cw : a->second;
    }
    return w;
}

}   // namespace kepler
