/**
 * @file App.h
 * @brief The game around the levels: title, menus, episodes and levels, the Quartermaster, the end-of-level tally,
 *        story cards, options, pause; and the test pictures.
 * @author Rene Weller
 */
#pragma once

#include <string>

namespace kepler
{

/** @brief The command line. */
struct Options
{
    std::string m_level;          ///< play this level file directly
    int         m_episode = 0, m_stage = 0;
    bool        m_mute = false;
    bool        m_windowed = false;
    int         m_w = 0, m_h = 0;
    std::string m_shot;           ///< write a picture and end
    bool        m_at = false;
    float       m_atX = 0, m_atY = 0;   ///< tiles
    float       m_warm = 0.5f;
    std::string m_hold;           ///< keys held during the warm-up: r l j f u (right left jump fire up)
    std::string m_lang;
    std::string m_menuShot;       ///< a menu to picture: title main episodes levels shop tally options story
    int         m_difficulty = -1;
    bool        m_allWeapons = false;
    std::string m_weapon;             ///< pictures: the weapon in hand
    std::string m_editor;             ///< start in the level editor with this file
    bool        m_autoplay = false;   ///< the autopilot plays (visible)
    std::string m_autotest;           ///< the autopilot plays headless and writes one line per level into this file
    float       m_limit = 900;        ///< autotest: game seconds per level before giving up
};

/** @brief Runs the game. */
int runApp( const Options &o );

}   // namespace kepler
