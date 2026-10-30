/**
 * @file EditorView.h
 * @brief The level editor's picture of a level: drawn as the game draws it (back walls, terrain with its masks,
 *        platforms, blocks, liquids, decorations, objects, pickups, enemies in their first frames, the hero), with a
 *        camera that pans and zooms; and the sprite helpers the palette's icons use.
 * @author Rene Weller
 */
#pragma once

#include "EditorDoc.h"

#include <raylib.h>

#include <string>
#include <vector>

namespace kepler
{
class Screen;
class TileSet;
class Sheet;
}   // namespace kepler

namespace kepler::edit
{

/** @brief Where the editor looks: the top left of the view in world pixels and the zoom. */
struct Camera
{
    float m_x = 0, m_y = 0;
    float m_zoom = 1;
    /** @brief A world point on the virtual screen. */
    Vector2 toScreen( float x, float y ) const { return { ( x - m_x ) * m_zoom, ( y - m_y ) * m_zoom }; }
    /** @brief A virtual screen point in the world. */
    Vector2 toWorld( float x, float y ) const { return { m_x + x / m_zoom, m_y + y / m_zoom }; }
};

/** @brief What a map character places, worked out once per frame. */
struct CharInfo
{
    std::string              m_kind;   ///< "" plain cell, "?" unknown, else the spawn kind
    std::vector<std::string> m_args;
};

/** @brief Every character's meaning in a document. */
struct CharTable
{
    CharInfo m_info[256];
    void     build( const Doc &doc );
    const CharInfo &operator[]( char c ) const { return m_info[(unsigned char)c]; }
};

/** @brief A back-wall decoration (as the game scatters them). */
struct DecoSpot
{
    int   m_index = 0;
    float m_x = 0, m_y = 0;
};

/** @brief How the level is drawn. */
struct DrawOptions
{
    bool  m_decos = true;    ///< the back-wall decorations
    bool  m_light = false;   ///< the level's darkness and lamps (else fully lit)
    float m_clock = 0;       ///< seconds, for animations
};

/** @brief Scatters the back-wall decorations as World::placeDecos does. */
std::vector<DecoSpot> placeDecos( const Doc &doc );

/**
 * @brief Draws the level into the screen's background, world, glow and light layers.
 * @param[in] s      the screen
 * @param[in] doc    the level
 * @param[in] chars  its characters' meanings
 * @param[in] cam    the camera
 * @param[in] decos  the decorations (placeDecos)
 * @param[in] o      options
 */
void drawLevel( Screen &s, const Doc &doc, const CharTable &chars, const Camera &cam, const std::vector<DecoSpot> &decos,
                const DrawOptions &o );

/**
 * @brief Draws what a spawn looks like on its cell, in world pixels (inside BeginMode2D).
 * @param[in] doc    the level (where things stand)
 * @param[in] info   what it is
 * @param[in] x, y   its cell
 * @param[in] ch     its map character (movers: the run)
 * @param[in] clock  seconds
 * @param[in] glow   the emissive pass
 * @param[in] alpha  0..1
 */
void drawSpawn( const Doc &doc, const CharInfo &info, int x, int y, char ch, float clock, bool glow, float alpha = 1 );

/**
 * @brief Where a spawn's sprite stands: walkers on the floor below their cell, fliers in the middle, turrets on the
 *        ceiling; the hero on the floor below the start.
 * @param[in]  doc   the level
 * @param[in]  info  what it is
 * @param[in]  x, y  its cell
 * @param[out] upside  drawn turned over (hanging from the ceiling)
 * @return the anchor in world pixels
 */
Vector2 standPoint( const Doc &doc, const CharInfo &info, int x, int y, bool &upside );

/** @brief A tile of a 32 px sheet at world or screen pixels. */
void tileAt( const Texture2D &tex, int index, float x, float y, Color tint = WHITE, bool flipX = false );

/**
 * @brief Draws a cell's look alone (palette icons, brush ghosts): terrain as a lone block, back walls whole.
 * @param[in] ts       the tile set
 * @param[in] tint     its tint
 * @param[in] c        the map character (' ' sky ... `D`), or 't'/'T' toggle solid/empty, '{'/'}' conveyor left/right
 * @param[in] x, y     top left
 * @param[in] size     the drawn size (32 = as in the game)
 * @param[in] clock    seconds
 */
void drawCellLook( const TileSet &ts, Color tint, char c, float x, float y, float size, float clock );

/**
 * @brief Draws a frame of a sheet so its opaque part fits a box (palette icons).
 * @param[in] sheet  the sheet's name (assets/sprites/<sheet>.png)
 * @param[in] anim   the animation (its first frame), "" for the sheet's first
 * @param[in] dst    the box
 * @param[in] tint   colour multiplied in
 * @param[in] flip   mirrored
 */
void drawFit( const std::string &sheet, const std::string &anim, Rectangle dst, Color tint = WHITE, bool flip = false );

/** @brief The colour of a light's colour name (as the game reads `light <colour> <radius>`). */
Color lightColour( const std::string &name );

/** @brief The animation an enemy is shown in: idle, move or fly, whichever its sheet has. */
std::string restAnim( const Sheet &sh );

}   // namespace kepler::edit
