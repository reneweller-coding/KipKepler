/**
 * @file Save.h
 * @brief The player's folder (%APPDATA%/KipKepler, or $XDG_DATA_HOME / ~/.local/share/KipKepler), the settings and
 *        the three save slots, written whole or not at all.
 * @author Rene Weller
 */
#pragma once

#include "Content.h"

#include <string>

namespace kepler
{

/** @brief What the options menu sets. */
struct Settings
{
    bool        m_fullscreen = true;
    float       m_master = 0.8f, m_music = 0.6f, m_effects = 0.8f;
    std::string m_lang;          ///< empty: the system's
    bool        m_vsync = true;
    int         m_slot = 0;      ///< the save slot in use
    bool        m_shake = true;
    bool        m_hints = true;  ///< button hints in the HUD
    bool        m_rumble = true;
    int         m_fps = 0;       ///< 0 the screen's rate, 1 144, 2 60, 3 40, 4 30
    int         m_speed = 0;     ///< assist: game speed 0 100 %, 1 90 %, 2 80 %, 3 70 %
    bool        m_invulnerable = false;   ///< assist
    bool        m_infiniteAmmo = false;   ///< assist
};

/** @brief The player's folder, with a slash at the end (made if missing). */
std::string userDir();

bool loadSettings( Settings &s );
bool saveSettings( const Settings &s );
/** @brief Reads a save slot (0-2); false when there is none. */
bool loadProgress( int slot, Progress &p );
bool saveProgress( int slot, const Progress &p );
/** @brief Whether a slot has a save, and a short line about it. */
bool slotInfo( int slot, std::string &line );
/** @brief Deletes a slot's save. */
void clearSlot( int slot );

}   // namespace kepler
