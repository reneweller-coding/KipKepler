/**
 * @file Editor.h
 * @brief The level editor: paints a level in the format of docs/DESIGN.md (cells, pickups, enemies, objects with
 *        their legend), checks it with the checker, saves it and hands it to the game for a test.
 * @author Rene Weller
 */
#pragma once

#include <memory>
#include <string>

namespace kepler
{

class Screen;

class Editor
{
public:
    Editor();
    ~Editor();

    /**
     * @brief Opens a level file (a new one when it does not exist yet).
     * @param[in] path  the file
     * @return whether it could be read or started
     */
    bool open( const std::string &path );

    /** @brief What the editor wants after an update. */
    enum class ResultE
    {
        STAY,   ///< go on editing
        LEAVE,  ///< back to the menu
        PLAY    ///< test the level (it was saved to path())
    };

    /**
     * @brief Runs a frame: input (mouse, keyboard, pad) and editing.
     * @param[in] dt  seconds since the last frame
     * @return what the app should do next
     */
    ResultE update( float dt );

    /** @brief Draws the editor into the screen's layers (world and HUD). */
    void draw( Screen &s );

    /** @brief The file being edited. */
    const std::string &path() const;

private:
    struct Impl;
    std::unique_ptr<Impl> m_impl;
};

}   // namespace kepler
