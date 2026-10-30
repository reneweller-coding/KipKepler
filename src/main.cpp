/**
 * @file main.cpp
 * @brief KIP KEPLER: the window, the main loop and the test options.
 *
 *        KipKepler [--level FILE] [--episode N --stage M] [--mute] [--windowed] [--w W --h H]
 *        Pictures for tests: --shot OUT.png [--at X,Y (tiles)] [--warm SECONDS] [--hold KEYS] (KEYS: r l j f u)
 *        The autopilot: --autoplay (watch it), --autotest REPORT.txt [--limit S] (headless, every level asked for:
 *        --level FILE, --episode N [--stage M], or all 36)
 * @author Rene Weller
 */
#include "App.h"
#include "Assets.h"
#include "Audio.h"
#include "Screen.h"
#include "Text.h"

#include <raylib.h>

#include <cstdlib>
#include <cstring>
#include <string>

using namespace kepler;

int main( int argc, char **argv )
{
    Options o;
    for ( int i = 1; i < argc; ++i )
    {
        std::string a = argv[i];
        auto        next = [&]() -> std::string { return i + 1 < argc ? argv[++i] : ""; };
        if ( a == "--level" ) o.m_level = next();
        else if ( a == "--episode" )
            o.m_episode = atoi( next().c_str() );
        else if ( a == "--stage" )
            o.m_stage = atoi( next().c_str() );
        else if ( a == "--mute" )
            o.m_mute = true;
        else if ( a == "--windowed" )
            o.m_windowed = true;
        else if ( a == "--w" )
            o.m_w = atoi( next().c_str() );
        else if ( a == "--h" )
            o.m_h = atoi( next().c_str() );
        else if ( a == "--shot" )
            o.m_shot = next();
        else if ( a == "--at" )
        {
            std::string v = next();
            o.m_atX = (float)atof( v.c_str() );
            size_t comma = v.find( ',' );
            o.m_atY = comma == std::string::npos ? 0 : (float)atof( v.c_str() + comma + 1 );
            o.m_at = true;
        }
        else if ( a == "--warm" )
            o.m_warm = (float)atof( next().c_str() );
        else if ( a == "--hold" )
            o.m_hold = next();
        else if ( a == "--lang" )
            o.m_lang = next();
        else if ( a == "--menu" )
            o.m_menuShot = next();
        else if ( a == "--difficulty" )
            o.m_difficulty = atoi( next().c_str() );
        else if ( a == "--weapons" )
            o.m_allWeapons = true;
        else if ( a == "--weapon" )
            o.m_weapon = next(), o.m_allWeapons = true;
        else if ( a == "--editor" )
            o.m_editor = next();
        else if ( a == "--autoplay" )
            o.m_autoplay = true;
        else if ( a == "--autotest" )
            o.m_autotest = next(), o.m_mute = true;
        else if ( a == "--limit" )
            o.m_limit = (float)atof( next().c_str() );
        else if ( a == "--perf" )
            o.m_perf = true;
        else if ( a == "--demo" )
            o.m_demoNow = true;
        else if ( a == "--help-look" )
            o.m_helpLook = true;
        else if ( a == "--seconds" )
            o.m_seconds = (float)atof( next().c_str() );
    }
    return runApp( o );
}
