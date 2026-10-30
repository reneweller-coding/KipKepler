/**
 * @file EditorDoc.h
 * @brief The level editor's document: a level file exactly as written (keys, legend lines, the rows of the map),
 *        with a parsed view of its cells for drawing (docs/DESIGN.md "Level files").
 * @author Rene Weller
 */
#pragma once

#include "Level.h"

#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace kepler::edit
{

/** @brief A legend line: its character and the words after it ("enemy sweeper ambush"). */
struct LegendLine
{
    char        m_ch = 0;
    std::string m_text;
    bool        m_fromFile = false;   ///< read from the file: kept even when no cell uses it
};

/** @brief What the file holds (an undo step copies this). */
struct DocData
{
    std::vector<std::string>                         m_comments;   ///< the header's `#` lines, kept on top
    std::vector<std::pair<std::string, std::string>> m_keys;       ///< in the file's order
    std::vector<LegendLine>                          m_legend;     ///< in the file's order
    std::vector<std::string>                         m_rows;       ///< m_h rows of m_w characters
    int                                              m_w = 0, m_h = 0;
};

/** @brief The level being edited. */
class Doc : public DocData
{
public:
    /**
     * @brief Starts a new level: walls around, a floor, the start and the exit.
     * @param[in] w, h  the size in cells
     */
    void makeNew( int w, int h );

    /**
     * @brief Reads a level file's text (the same rules as Level::load, but keeping everything).
     * @param[in]  text   the file's contents
     * @param[out] error  why it failed
     * @return whether it was read
     */
    bool parse( const std::string &text, std::string &error );

    /** @brief The file's text: comments, keys, legend lines, `map` ... `end`. */
    std::string write() const;

    /** @brief A map character (`#` outside the map). */
    char at( int x, int y ) const;
    /** @brief Sets a map character; returns whether it changed. Call rebuild() afterwards. */
    bool set( int x, int y, char c );

    /** @brief A key's value or a fallback. */
    std::string key( const std::string &name, const std::string &fallback = "" ) const;
    /** @brief Sets a key (appended when new); an empty value removes it. */
    void setKey( const std::string &name, const std::string &value );

    /** @brief The legend line of a character (nullptr if none). */
    const LegendLine *legend( char c ) const;
    /** @brief What a character places: a legend kind, a fixed meaning (crystal, start ...), "" for plain cells,
     *         "?" when unknown. */
    std::string kindOf( char c ) const;
    /** @brief The words after the kind (legend arguments or the fixed meaning's: health small ...). */
    std::vector<std::string> argsOf( char c ) const;
    /**
     * @brief The character for a legend text: an identical line's, or a free character with a new line.
     * @param[in] text   the words after the character
     * @param[in] fresh  always a new character (teleport pads)
     * @return the character, 0 when none is left
     */
    char charFor( const std::string &text, bool fresh = false );
    /** @brief Whether any cell uses a character. */
    bool used( char c ) const;

    /** @brief Recomputes the view of the whole map. */
    void rebuild();
    /** @brief Recomputes the view around changed cells (inclusive bounds). */
    void rebuild( int x0, int y0, int x1, int y1 );

    /** @brief Whether a cell is solid when the level starts (doors shut, toggles off). */
    bool solidAt( int x, int y ) const;
    /** @brief Whether a cell is a one-way platform. */
    bool onewayAt( int x, int y ) const;

    /**
     * @brief Grows (positive) or shrinks (negative) the map at its edges; spawns keep their cells.
     * @param[in] left, right, top, bottom  columns or rows added at each edge
     */
    void resize( int left, int right, int top, int bottom );

    Level                m_view;      ///< the cells as the game reads them (masks, interior)
    std::vector<uint8_t> m_maskT;     ///< terrain mask per cell
    std::vector<uint8_t> m_maskB;     ///< back-wall mask per cell
    std::vector<uint8_t> m_variant;   ///< tile variant per cell
    std::string          m_id;        ///< the file name without folder and .txt

private:
    char freeChar();
};

/** @brief The game's cell hash (World.cpp): tile variants and the engine's own choices. */
uint32_t hashCell( int x, int y, uint32_t salt = 0 );
/** @brief The episode (1-4) a tile set belongs to. */
int episodeOf( const std::string &theme );
/** @brief Whether a map character has a fixed meaning (no legend needed). */
bool fixedChar( char c );
/** @brief Joins words with single spaces. */
std::string joinWords( const std::vector<std::string> &w, size_t from = 0 );

}   // namespace kepler::edit
