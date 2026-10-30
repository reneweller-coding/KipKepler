/**
 * @file Level.h
 * @brief A level as written in assets/levels/<name>.txt: the keys, the legend and the map of cells (docs/DESIGN.md
 *        "Level files"). Static data only; what changes in play (opened doors, broken blocks) lives in the World.
 * @author Rene Weller
 */
#pragma once

#include <cstdint>
#include <map>
#include <string>
#include <vector>

namespace kepler
{

/** @brief Pixels per tile. */
constexpr int Tile = 32;

/** @brief What a cell of the map is. */
enum class CellE : uint8_t
{
    SKY,          ///< empty, the parallax background shows
    INTERIOR,     ///< empty, the theme's back wall shows
    TERRAIN_A,    ///< `#`
    TERRAIN_B,    ///< `%`
    PLATFORM,     ///< `-` one way
    CRUMBLE,      ///< `_`
    BREAKABLE,    ///< `B`
    FAKE,         ///< `X` looks like terrain A, can be walked through
    SPIKE_UP,     ///< `^`
    SPIKE_DOWN,   ///< `v`
    SPIKE_LEFT,   ///< `<` (on a wall, pointing left)
    SPIKE_RIGHT,  ///< `>`
    LIQUID,       ///< `~`
    DOOR_BLUE,    ///< `d`
    DOOR_GOLD,    ///< `D`
    TOGGLE,       ///< legend `toggle <group> solid|empty` (group and polarity in Cell::m_aux)
    CONVEYOR      ///< legend `conveyor <dir>` (dir in Cell::m_aux: 0 left, 1 right)
};

/** @brief One cell of the map. */
struct Cell
{
    CellE   m_kind = CellE::SKY;
    uint8_t m_aux = 0;          ///< toggle: group (bits 0-2) + 8 when solid while the group is ON; conveyor: 1 = right
    bool    m_interior = false; ///< the back wall shows behind it (else the sky)
    bool    m_secret = false;   ///< `?`: touching it counts a secret
};

/** @brief Something placed by the map that is not a plain cell: pickups, enemies, objects. */
struct Spawn
{
    std::string              m_kind;   ///< crystal treasure health key power enemy start exit checkpoint teleport switch
                                       ///< mover spring laser crusher sign light boss
    std::vector<std::string> m_args;   ///< the legend's words after the kind (or the fixed character's meaning)
    int                      m_x = 0;  ///< cell column (for movers: the leftmost cell)
    int                      m_y = 0;  ///< cell row
    int                      m_w = 1;  ///< width in cells (movers)
    char                     m_ch = 0; ///< the map character
};

/** @brief A level file, parsed. */
class Level
{
public:
    /**
     * @brief Reads a level file.
     * @param[in]  path  the file
     * @param[out] error why it failed (empty when it worked)
     * @return whether it was read
     */
    bool load( const std::string &path, std::string &error );

    /** @brief Whether a cell lies inside the map. */
    bool inside( int x, int y ) const { return x >= 0 && y >= 0 && x < m_w && y < m_h; }

    /** @brief A cell (outside the map: terrain at the sides and the top, sky below). */
    const Cell &at( int x, int y ) const;

    /**
     * @brief Whether a box (pixels) touches the hurting part of a spike or a liquid.
     * @param[in]  l, t, r, b  the box
     * @param[out] liquid      whether it was a liquid (deadly) rather than spikes
     * @return whether it touches one
     */
    bool hurts( float l, float t, float r, float b, bool &liquid ) const;

    /** @brief The 8-bit neighbour mask of a cell for the terrain sheets (docs/DESIGN.md "Tile sets"). */
    uint8_t terrainMask( int x, int y ) const;
    /** @brief The 8-bit neighbour mask of a cell for the back-wall sheet. */
    uint8_t backMask( int x, int y ) const;

    /** @brief The first spawn of a kind (nullptr if none). */
    const Spawn *first( const std::string &kind ) const;

    /** @brief A key's value, or a fallback. */
    std::string key( const std::string &name, const std::string &fallback = "" ) const;
    /** @brief A key's value as a number, or a fallback. */
    float num( const std::string &name, float fallback ) const;

    std::string                        m_path;   ///< where it was read from
    std::string                        m_id;     ///< the file name without folder and .txt (e1l1)
    int                                m_w = 0;  ///< columns
    int                                m_h = 0;  ///< rows
    std::vector<Cell>                  m_cells;  ///< row-major
    std::vector<Spawn>                 m_spawns; ///< in map order (row by row)
    std::map<std::string, std::string> m_keys;   ///< name, theme, bg, music, dark, par, gravity, tint ...
    int                                m_crystals = 0; ///< how many crystals the map has
};

/** @brief Splits a line into words at spaces and tabs. */
std::vector<std::string> words( const std::string &line );

}   // namespace kepler
