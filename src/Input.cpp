/**
 * @file Input.cpp
 * @brief Keyboard and gamepad.
 * @author Rene Weller
 */
#include "Input.h"

#include <raylib.h>

#include <cmath>

namespace kepler
{

namespace
{

bool g_pad = false;

int pad()
{
    for ( int i = 0; i < 4; ++i )
        if ( IsGamepadAvailable( i ) ) return i;
    return -1;
}

bool down( std::initializer_list<int> keys )
{
    for ( int k : keys )
        if ( IsKeyDown( k ) ) return true;
    return false;
}

bool pressed( std::initializer_list<int> keys )
{
    for ( int k : keys )
        if ( IsKeyPressed( k ) ) return true;
    return false;
}

}   // namespace

bool padInUse()
{
    return g_pad;
}

Controls readControls()
{
    Controls c;
    c.m_left = down( { KEY_LEFT, KEY_A } );
    c.m_right = down( { KEY_RIGHT, KEY_D } );
    c.m_up = down( { KEY_UP, KEY_W } );
    c.m_down = down( { KEY_DOWN, KEY_S } );
    c.m_jump = down( { KEY_SPACE, KEY_K, KEY_Z } );
    c.m_jumpPressed = pressed( { KEY_SPACE, KEY_K, KEY_Z } );
    c.m_fire = down( { KEY_LEFT_CONTROL, KEY_RIGHT_CONTROL, KEY_J, KEY_X } ) || IsMouseButtonDown( MOUSE_BUTTON_LEFT );
    c.m_firePressed = pressed( { KEY_LEFT_CONTROL, KEY_RIGHT_CONTROL, KEY_J, KEY_X } ) || IsMouseButtonPressed( MOUSE_BUTTON_LEFT );
    c.m_alt = pressed( { KEY_L, KEY_C } ) || IsMouseButtonPressed( MOUSE_BUTTON_RIGHT );
    c.m_prevWeapon = pressed( { KEY_Q } ) || GetMouseWheelMove() < 0;
    c.m_nextWeapon = pressed( { KEY_E } ) || GetMouseWheelMove() > 0;
    c.m_pause = pressed( { KEY_ESCAPE, KEY_P } );
    if ( GetKeyPressed() ) g_pad = false;
    int p = pad();
    if ( p >= 0 )
    {
        float ax = GetGamepadAxisMovement( p, GAMEPAD_AXIS_LEFT_X ), ay = GetGamepadAxisMovement( p, GAMEPAD_AXIS_LEFT_Y );
        bool  dl = IsGamepadButtonDown( p, GAMEPAD_BUTTON_LEFT_FACE_LEFT ), dr = IsGamepadButtonDown( p, GAMEPAD_BUTTON_LEFT_FACE_RIGHT );
        bool  du = IsGamepadButtonDown( p, GAMEPAD_BUTTON_LEFT_FACE_UP ), dd = IsGamepadButtonDown( p, GAMEPAD_BUTTON_LEFT_FACE_DOWN );
        bool  any = false;
        auto  use = [&]( bool b ) { any |= b; return b; };
        c.m_left |= use( ax < -0.35f || dl );
        c.m_right |= use( ax > 0.35f || dr );
        c.m_up |= use( ay < -0.55f || du );
        c.m_down |= use( ay > 0.55f || dd );
        c.m_jump |= use( IsGamepadButtonDown( p, GAMEPAD_BUTTON_RIGHT_FACE_DOWN ) );
        c.m_jumpPressed |= use( IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_DOWN ) );
        c.m_fire |= use( IsGamepadButtonDown( p, GAMEPAD_BUTTON_RIGHT_FACE_LEFT ) || IsGamepadButtonDown( p, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT ) ||
                         IsGamepadButtonDown( p, GAMEPAD_BUTTON_RIGHT_TRIGGER_2 ) );
        c.m_firePressed |= use( IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_LEFT ) || IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT ) ||
                                IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_TRIGGER_2 ) );
        c.m_alt |= use( IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_UP ) || IsGamepadButtonPressed( p, GAMEPAD_BUTTON_LEFT_TRIGGER_2 ) );
        c.m_prevWeapon |= use( IsGamepadButtonPressed( p, GAMEPAD_BUTTON_LEFT_TRIGGER_1 ) );
        c.m_nextWeapon |= use( IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_TRIGGER_1 ) );
        c.m_pause |= use( IsGamepadButtonPressed( p, GAMEPAD_BUTTON_MIDDLE_RIGHT ) );
        if ( any ) g_pad = true;
    }
    return c;
}

MenuKeys readMenu( float dt )
{
    static float repeat = 0;
    static int   held = 0;
    MenuKeys     m;
    int          p = pad();
    bool         up = IsKeyDown( KEY_UP ) || IsKeyDown( KEY_W ), dn = IsKeyDown( KEY_DOWN ) || IsKeyDown( KEY_S );
    bool         lf = IsKeyDown( KEY_LEFT ) || IsKeyDown( KEY_A ), rt = IsKeyDown( KEY_RIGHT ) || IsKeyDown( KEY_D );
    m.m_ok = IsKeyPressed( KEY_ENTER ) || IsKeyPressed( KEY_SPACE ) || IsKeyPressed( KEY_KP_ENTER );
    m.m_back = IsKeyPressed( KEY_ESCAPE ) || IsKeyPressed( KEY_BACKSPACE );
    m.m_alt = IsKeyPressed( KEY_T );
    if ( p >= 0 )
    {
        float ax = GetGamepadAxisMovement( p, GAMEPAD_AXIS_LEFT_X ), ay = GetGamepadAxisMovement( p, GAMEPAD_AXIS_LEFT_Y );
        up |= ay < -0.6f || IsGamepadButtonDown( p, GAMEPAD_BUTTON_LEFT_FACE_UP );
        dn |= ay > 0.6f || IsGamepadButtonDown( p, GAMEPAD_BUTTON_LEFT_FACE_DOWN );
        lf |= ax < -0.6f || IsGamepadButtonDown( p, GAMEPAD_BUTTON_LEFT_FACE_LEFT );
        rt |= ax > 0.6f || IsGamepadButtonDown( p, GAMEPAD_BUTTON_LEFT_FACE_RIGHT );
        bool ok = IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_DOWN ) || IsGamepadButtonPressed( p, GAMEPAD_BUTTON_MIDDLE_RIGHT );
        bool back = IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT );
        if ( ok || back ) g_pad = true;
        m.m_ok |= ok;
        m.m_back |= back;
        m.m_alt |= IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_UP );
    }
    int now = up ? 1 : dn ? 2 : lf ? 3 : rt ? 4 : 0;
    bool fire = false;
    if ( now != held )
    {
        held = now;
        repeat = 0.35f;
        fire = now != 0;
    }
    else if ( now )
    {
        repeat -= dt;
        if ( repeat <= 0 )
        {
            repeat = 0.09f;
            fire = true;
        }
    }
    if ( fire )
    {
        m.m_up = now == 1, m.m_down = now == 2, m.m_left = now == 3, m.m_right = now == 4;
    }
    return m;
}

}   // namespace kepler
