/**
 * @file Screen.cpp
 * @brief The virtual pixel screen and its layers.
 * @author Rene Weller
 */
#include "Screen.h"

#include <rlgl.h>

#include <algorithm>
#include <cmath>

namespace kepler
{

namespace
{

// The light map holds half the light, so lamps can brighten up to twice (the lit shader doubles it again).
const char *LitFs = R"(#version 330
in vec2 fragTexCoord;
in vec4 fragColor;
uniform sampler2D texture0;
uniform sampler2D lightMap;
out vec4 finalColor;
void main()
{
    vec4 c = texture( texture0, fragTexCoord );
    vec3 l = texture( lightMap, fragTexCoord ).rgb * 2.0;
    finalColor = vec4( c.rgb * l, c.a ) * fragColor;
}
)";

const char *BlurFs = R"(#version 330
in vec2 fragTexCoord;
in vec4 fragColor;
uniform sampler2D texture0;
uniform vec2 dir;
uniform vec2 size;
out vec4 finalColor;
void main()
{
    vec2 px = dir / size;
    vec3 c = texture( texture0, fragTexCoord ).rgb * 0.227;
    c += texture( texture0, fragTexCoord + px * 1.38 ).rgb * 0.316;
    c += texture( texture0, fragTexCoord - px * 1.38 ).rgb * 0.316;
    c += texture( texture0, fragTexCoord + px * 3.23 ).rgb * 0.070;
    c += texture( texture0, fragTexCoord - px * 3.23 ).rgb * 0.070;
    finalColor = vec4( c, 1.0 );
}
)";

void drawRt( const RenderTexture2D &rt, Rectangle dst, Color tint = WHITE )
{
    DrawTexturePro( rt.texture, { 0, 0, (float)rt.texture.width, -(float)rt.texture.height }, dst, { 0, 0 }, 0, tint );
}

RenderTexture2D target( int w, int h, bool smooth = false )
{
    RenderTexture2D rt = LoadRenderTexture( w, h );
    SetTextureFilter( rt.texture, smooth ? TEXTURE_FILTER_BILINEAR : TEXTURE_FILTER_POINT );
    return rt;
}

}   // namespace

void Screen::init()
{
    if ( m_open ) unload();
    int   ww = std::max( 1, GetRenderWidth() ), wh = std::max( 1, GetRenderHeight() );
    float aspect = (float)ww / wh;
    m_w = 640;
    m_h = aspect < 1.7f ? 400 : 360;
    m_scale = std::max( 1, std::min( ww / m_w, wh / m_h ) );
    m_bg = target( m_w, m_h );
    m_world = target( m_w, m_h );
    m_light = target( m_w, m_h, true );
    m_glow = target( m_w, m_h );
    m_hud = target( m_w, m_h );
    m_out = target( m_w, m_h );
    m_blurA = target( m_w / 2, m_h / 2, true );
    m_blurB = target( m_w / 2, m_h / 2, true );
    if ( !m_lit.id )
    {
        m_lit = LoadShaderFromMemory( nullptr, LitFs );
        m_litLight = GetShaderLocation( m_lit, "lightMap" );
        m_blur = LoadShaderFromMemory( nullptr, BlurFs );
        m_blurDir = GetShaderLocation( m_blur, "dir" );
        m_blurSize = GetShaderLocation( m_blur, "size" );
        // A lamp: a round light falling off in a few hard steps, as pixel art lights do.
        const int N = 128;
        Image     img = GenImageColor( N, N, BLANK );
        for ( int y = 0; y < N; ++y )
            for ( int x = 0; x < N; ++x )
            {
                float d = std::sqrt( ( x - N / 2 + 0.5f ) * ( x - N / 2 + 0.5f ) + ( y - N / 2 + 0.5f ) * ( y - N / 2 + 0.5f ) ) / ( N / 2 );
                float v = std::max( 0.0f, 1.0f - d );
                v = v * v * ( 3 - 2 * v );
                v = std::floor( v * 6.0f + 0.5f ) / 6.0f;
                unsigned char b = (unsigned char)( v * 255 );
                ImageDrawPixel( &img, x, y, { b, b, b, 255 } );
            }
        m_lamp = LoadTextureFromImage( img );
        UnloadImage( img );
        SetTextureFilter( m_lamp, TEXTURE_FILTER_BILINEAR );
    }
    m_open = true;
}

void Screen::resize()
{
    int   ww = std::max( 1, GetRenderWidth() ), wh = std::max( 1, GetRenderHeight() );
    int   h = (float)ww / wh < 1.7f ? 400 : 360;
    if ( h != m_h ) init();
    m_scale = std::max( 1, std::min( ww / m_w, wh / m_h ) );
}

void Screen::unload()
{
    for ( RenderTexture2D *rt : { &m_bg, &m_world, &m_light, &m_glow, &m_hud, &m_out, &m_blurA, &m_blurB } )
        if ( rt->id ) UnloadRenderTexture( *rt ), *rt = {};
    m_open = false;
}

void Screen::begin( LayerE layer )
{
    switch ( layer )
    {
    case LayerE::BACKGROUND: BeginTextureMode( m_bg ); break;
    case LayerE::WORLD: BeginTextureMode( m_world ); break;
    case LayerE::LIGHT:
        BeginTextureMode( m_light );
        BeginBlendMode( BLEND_ADDITIVE );
        break;
    case LayerE::GLOW:
        BeginTextureMode( m_glow );
        BeginBlendMode( BLEND_ADDITIVE );
        break;
    case LayerE::HUD: BeginTextureMode( m_hud ); break;
    }
}

void Screen::end()
{
    EndBlendMode();
    EndTextureMode();
}

void Screen::clear( Color ambient )
{
    BeginTextureMode( m_bg );
    ClearBackground( BLACK );
    EndTextureMode();
    BeginTextureMode( m_world );
    ClearBackground( BLANK );
    EndTextureMode();
    BeginTextureMode( m_light );
    ClearBackground( { (unsigned char)( ambient.r / 2 ), (unsigned char)( ambient.g / 2 ), (unsigned char)( ambient.b / 2 ), 255 } );
    EndTextureMode();
    BeginTextureMode( m_glow );
    ClearBackground( BLACK );
    EndTextureMode();
    BeginTextureMode( m_hud );
    ClearBackground( BLANK );
    EndTextureMode();
}

void Screen::light( float x, float y, float radius, Color c, float strength )
{
    Color t = { (unsigned char)std::min( 255.0f, c.r * strength * 0.5f ), (unsigned char)std::min( 255.0f, c.g * strength * 0.5f ),
                (unsigned char)std::min( 255.0f, c.b * strength * 0.5f ), 255 };
    DrawTexturePro( m_lamp, { 0, 0, (float)m_lamp.width, (float)m_lamp.height },
                    { std::floor( x - radius ), std::floor( y - radius ), radius * 2, radius * 2 }, { 0, 0 }, 0, t );
}

void Screen::compose( float bloom )
{
    Rectangle full = { 0, 0, (float)m_w, (float)m_h };
    Rectangle half = { 0, 0, (float)m_w / 2, (float)m_h / 2 };
    // Bloom: the glow layer halved and blurred both ways.
    if ( bloom > 0 )
    {
        float size[2] = { (float)m_w / 2, (float)m_h / 2 };
        BeginTextureMode( m_blurA );
        ClearBackground( BLACK );
        BeginShaderMode( m_blur );
        float dx[2] = { 1, 0 };
        SetShaderValue( m_blur, m_blurDir, dx, SHADER_UNIFORM_VEC2 );
        SetShaderValue( m_blur, m_blurSize, size, SHADER_UNIFORM_VEC2 );
        drawRt( m_glow, half );
        EndShaderMode();
        EndTextureMode();
        BeginTextureMode( m_blurB );
        ClearBackground( BLACK );
        BeginShaderMode( m_blur );
        float dy[2] = { 0, 1 };
        SetShaderValue( m_blur, m_blurDir, dy, SHADER_UNIFORM_VEC2 );
        SetShaderValue( m_blur, m_blurSize, size, SHADER_UNIFORM_VEC2 );
        drawRt( m_blurA, half );
        EndShaderMode();
        EndTextureMode();
    }
    BeginTextureMode( m_out );
    ClearBackground( BLACK );
    drawRt( m_bg, full );
    BeginShaderMode( m_lit );
    SetShaderValueTexture( m_lit, m_litLight, m_light.texture );
    drawRt( m_world, full );
    EndShaderMode();
    BeginBlendMode( BLEND_ADDITIVE );
    drawRt( m_glow, full );
    if ( bloom > 0 )
    {
        unsigned char b = (unsigned char)std::min( 255.0f, 255 * bloom );
        drawRt( m_blurB, full, { b, b, b, 255 } );
    }
    EndBlendMode();
    drawRt( m_hud, full );
    EndTextureMode();
}

void Screen::present( float bloom, float fade )
{
    compose( bloom );
    int   ww = GetRenderWidth(), wh = GetRenderHeight();
    float s = (float)m_scale;
    if ( ww < m_w || wh < m_h ) s = std::min( (float)ww / m_w, (float)wh / m_h );
    float w = m_w * s, h = m_h * s;
    ClearBackground( BLACK );
    drawRt( m_out, { std::floor( ( ww - w ) / 2 ), std::floor( ( wh - h ) / 2 ), w, h } );
    if ( fade > 0 ) DrawRectangle( 0, 0, ww, wh, { 0, 0, 0, (unsigned char)( std::min( 1.0f, fade ) * 255 ) } );
}

Image Screen::capture( float bloom )
{
    compose( bloom );
    Image img = LoadImageFromTexture( m_out.texture );
    ImageFlipVertical( &img );
    return img;
}

}   // namespace kepler
