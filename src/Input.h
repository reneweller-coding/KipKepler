/**
 * @file Input.h
 * @brief Keyboard and gamepad read into Controls (play) and menu presses. Keyboard: arrows/WASD move, Space/K/Z
 *        jump, Ctrl/J/X fire, Q/E switch weapons, Esc/P pause. Pad (Steam Deck): stick/d-pad move, A jump, X or B
 *        fire, LB/RB switch weapons, Start pause.
 * @author Rene Weller
 */
#pragma once

#include "World.h"

namespace kepler
{

/** @brief What the menus need. */
struct MenuKeys
{
    bool m_up = false, m_down = false, m_left = false, m_right = false;
    bool m_ok = false, m_back = false;
    bool m_alt = false;   ///< the second action (T / pad Y): time trial in the level list
};

/** @brief Reads the play controls for this frame. */
Controls readControls();
/** @brief Reads the menu presses for this frame (with key repeat on held directions). */
MenuKeys readMenu( float dt );
/** @brief Whether the last input came from a gamepad (for button hints). */
bool padInUse();

}   // namespace kepler
