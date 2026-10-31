/**
 * @file Assets.h
 * @brief What the game reads from assets/: sprite sheets, tile sets, backgrounds, fonts and sounds (formats in
 *        docs/DESIGN.md). Anything missing is replaced by a plain stand-in so the game always runs.
 * @author Rene Weller
 */
#pragma once

#include <raylib.h>

#include <map>
#include <memory>
#include <string>
#include <vector>

namespace kepler
{

/** @brief The folder with the assets, with a slash at the end. */
const std::string &assetDir();

/** @brief One animation of a sheet. */
struct Anim
{
    std::vector<int> m_frames;
    float            m_fps = 10;
    bool             m_loop = true;
    /** @brief How long it lasts once through. */
    float length() const { return m_frames.size() / m_fps; }
};

/** @brief A sprite sheet: frames of one size in a grid, named animations and points. */
class Sheet
{
public:
    /**
     * @brief The frame of an animation at a time.
     * @param[in] anim  the animation's name (the first animation if unknown)
     * @param[in] t     seconds since it began
     * @return the frame index
     */
    int frame( const std::string &anim, float t ) const;
    /** @brief An animation (nullptr if the sheet has none of that name). */
    const Anim *anim( const std::string &name ) const;
    /** @brief Whether an animation has run through (once animations). */
    bool done( const std::string &name, float t ) const;
    /** @brief A named point relative to the anchor (facing right), or the fallback. */
    Vector2 point( const std::string &name, Vector2 fallback = { 0, 0 } ) const;

    /**
     * @brief Draws a frame with its anchor at (x, y).
     * @param[in] frame  the frame index
     * @param[in] x, y   where the anchor goes (pixels of the virtual screen)
     * @param[in] flip   facing left
     * @param[in] tint   colour multiplied in
     * @param[in] glow   draw the emissive mask instead (nothing if the sheet has none)
     * @param[in] angle  rotation about the anchor, degrees
     */
    void draw( int frame, float x, float y, bool flip = false, Color tint = WHITE, bool glow = false,
               float angle = 0 ) const;

    Texture2D                      m_tex = {};
    Texture2D                      m_glow = {};
    bool                           m_hasGlow = false;
    bool                           m_standIn = false;   ///< the file was missing
    int                            m_fw = 32, m_fh = 32;
    int                            m_ax = 16, m_ay = 16;
    int                            m_cols = 1;
    std::map<std::string, Anim>    m_anims;
    std::map<std::string, Vector2> m_points;
    std::string                    m_firstAnim;
};

/** @brief A decoration of a tile set (deco.txt). */
struct Deco
{
    std::string m_name;
    Rectangle   m_src;
    int         m_place = 0;   ///< 0 wall, 1 floor, 2 ceiling, 3 edge
    float       m_weight = 1;
    bool        m_glow = false;
    Color       m_light = { 150, 165, 190, 255 };   ///< the mean colour of its glowing pixels
};

/** @brief A theme's tiles. */
class TileSet
{
public:
    /** @brief How many variants a 256-mask sheet holds. */
    static int variants( const Texture2D &t ) { return t.height >= 32 * 16 ? t.height / ( 32 * 16 ) : 1; }

    std::string       m_theme;
    Texture2D         m_terrainA = {}, m_terrainB = {}, m_back = {}, m_platform = {}, m_blocks = {}, m_liquid = {},
              m_deco = {};
    Texture2D         m_terrainAGlow = {}, m_terrainBGlow = {}, m_backGlow = {}, m_blocksGlow = {}, m_liquidGlow = {},
              m_decoGlow = {};
    std::vector<Deco> m_decos;
    Color             m_tints[4] = { WHITE, WHITE, WHITE, WHITE };
    bool              m_standIn = false;
};

/** @brief One parallax layer. */
struct BgLayer
{
    Texture2D m_tex = {};
    Texture2D m_glow = {};                 ///< its emissive pixels (none: id 0)
    float     m_px = 0.1f, m_py = 0.05f;   ///< how much it moves with the camera
    float     m_yoff = 0;                  ///< vertical offset
    float     m_scroll = 0;                ///< drifts by itself, px/s
};

/** @brief A background: up to four layers and the colours above and below them. */
class Background
{
public:
    std::vector<BgLayer> m_layers;
    BgLayer              m_fore;           ///< silhouettes in front of the world (m_fore.m_tex.id 0: none)
    Color                m_top = { 10, 12, 30, 255 }, m_bottom = { 6, 6, 14, 255 };
    bool                 m_standIn = false;
};

/**
 * @brief Draws a background's layers: each repeats sideways, its top row sits at `y offset + rise * parallax y`,
 *        and its first and last rows continue above and below it (the layers are painted for that).
 * @param[in] bg     the background
 * @param[in] w, h   the view in virtual pixels
 * @param[in] camX   the camera's x
 * @param[in] rise   how far the camera is above its lowest place in the level (>= 0)
 * @param[in] clock  seconds, for layers that drift by themselves
 * @param[in] glow   draw the layers' emissive masks instead (dimmed: the foreground must stay readable)
 */
void drawBackground( const Background &bg, int w, int h, float camX, float rise, float clock, bool glow );

/**
 * @brief Draws a background's foreground silhouettes (in front of the world): they move faster than the world
 *        sideways and stay with the screen up and down, swaying a little while the camera catches up.
 * @param[in] lag  how far the camera is ahead of its smoothed self vertically (px)
 */
void drawForeground( const Background &bg, int w, int h, float camX, float lag );

/** @brief A pixel font (DESIGN.md "Fonts"), or raylib's own when missing. */
class PixelFont
{
public:
    /**
     * @brief Draws text.
     * @param[in] text   UTF-8
     * @param[in] x, y   top left
     * @param[in] tint   colour
     * @return the width drawn
     */
    int draw( const std::string &text, float x, float y, Color tint ) const;
    /** @brief The width of a text. */
    int width( const std::string &text ) const;
    /** @brief The line height. */
    int height() const { return m_ch; }

    Texture2D               m_tex = {};
    int                     m_cw = 8, m_ch = 12, m_base = 9;
    std::map<int, int>      m_index;    ///< codepoint -> glyph index
    std::map<int, int>      m_advance;  ///< codepoint -> advance
    bool                    m_standIn = true;
    int                     m_scale = 1;
};

/** @brief Loads things once and keeps them. */
class Assets
{
public:
    /** @brief A sprite sheet (assets/sprites/<name>), a stand-in when missing. */
    const Sheet &sheet( const std::string &name );
    /** @brief A sheet from another folder (assets/<folder>/<name>). */
    const Sheet &sheetIn( const std::string &folder, const std::string &name );
    /** @brief A tile set (assets/tiles/<theme>/). */
    const TileSet &tiles( const std::string &theme );
    /** @brief A background (assets/bg/<name>/). */
    const Background &background( const std::string &name );
    /** @brief A plain texture (assets/<path>), nullptr if missing. */
    const Texture2D *texture( const std::string &path );
    /** @brief The small and the big font. */
    const PixelFont &font( bool big = false, bool outline = false );
    /** @brief Frees everything (before the window closes). */
    void unload();
    /** @brief The pictures loaded since the last call, with their time ("path 12.3ms", for the performance log). */
    std::string takeLoads();

private:
    std::map<std::string, std::unique_ptr<Sheet>>      m_sheets;
    std::map<std::string, std::unique_ptr<TileSet>>    m_tiles;
    std::map<std::string, std::unique_ptr<Background>> m_backgrounds;
    std::map<std::string, Texture2D>                   m_textures;
    std::unique_ptr<PixelFont>                         m_fonts[3];
};

/** @brief The game's assets. */
Assets &assets();

/** @brief Decodes the next UTF-8 code point and advances i. */
int nextCodepoint( const std::string &s, size_t &i );

}   // namespace kepler
