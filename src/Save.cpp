/**
 * @file Save.cpp
 * @brief Settings and save slots as plain text in the player's folder.
 * @author Rene Weller
 */
#include "Save.h"

#include "Level.h"

#include <raylib.h>

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>

namespace kepler
{

namespace fs = std::filesystem;

bool writeWhole( const std::string &path, const std::string &text )
{
    std::string tmp = path + ".tmp";
    {
        std::ofstream out( tmp, std::ios::binary );
        if ( !out ) return false;
        out << text;
        if ( !out.good() ) return false;
    }
    std::error_code e;
    if ( fs::exists( path, e ) ) fs::copy_file( path, path + ".bak", fs::copy_options::overwrite_existing, e );
    fs::rename( tmp, path, e );
    return !e;
}

namespace
{

std::string slotPath( int slot )
{
    return userDir() + "save" + ( slot ? std::to_string( slot + 1 ) : "" ) + ".txt";
}

}   // namespace

std::string userDir()
{
    static std::string dir;
    if ( !dir.empty() ) return dir;
#ifdef _WIN32
    const char *app = getenv( "APPDATA" );
    std::string root = app && *app ? app : GetApplicationDirectory();
#else
    const char *xdg = getenv( "XDG_DATA_HOME" ), *home = getenv( "HOME" );
    std::string root = xdg && *xdg ? xdg : ( home && *home ? std::string( home ) + "/.local/share" : GetApplicationDirectory() );
#endif
    dir = root + "/KipKepler/";
    std::error_code e;
    fs::create_directories( dir, e );
    if ( e ) dir = GetApplicationDirectory();
    return dir;
}

bool loadSettings( Settings &s )
{
    std::ifstream in( userDir() + "settings.txt" );
    if ( !in ) return false;
    std::string line;
    while ( std::getline( in, line ) )
    {
        std::vector<std::string> w = words( line );
        if ( w.size() < 2 ) continue;
        if ( w[0] == "fullscreen" ) s.m_fullscreen = atoi( w[1].c_str() ) != 0;
        else if ( w[0] == "master" )
            s.m_master = (float)atof( w[1].c_str() );
        else if ( w[0] == "music" )
            s.m_music = (float)atof( w[1].c_str() );
        else if ( w[0] == "effects" )
            s.m_effects = (float)atof( w[1].c_str() );
        else if ( w[0] == "lang" )
            s.m_lang = w[1];
        else if ( w[0] == "vsync" )
            s.m_vsync = atoi( w[1].c_str() ) != 0;
        else if ( w[0] == "slot" )
            s.m_slot = std::clamp( atoi( w[1].c_str() ), 0, 2 );
        else if ( w[0] == "shake" )
            s.m_shake = atoi( w[1].c_str() ) != 0;
        else if ( w[0] == "hints" )
            s.m_hints = atoi( w[1].c_str() ) != 0;
        else if ( w[0] == "rumble" )
            s.m_rumble = atoi( w[1].c_str() ) != 0;
        else if ( w[0] == "fps" )
            s.m_fps = std::clamp( atoi( w[1].c_str() ), 0, 4 );
        else if ( w[0] == "speed" )
            s.m_speed = std::clamp( atoi( w[1].c_str() ), 0, 3 );
        else if ( w[0] == "invulnerable" )
            s.m_invulnerable = atoi( w[1].c_str() ) != 0;
        else if ( w[0] == "infiniteammo" )
            s.m_infiniteAmmo = atoi( w[1].c_str() ) != 0;
        else if ( w[0] == "colourassist" )
            s.m_colourAssist = atoi( w[1].c_str() ) != 0;
        else if ( w[0] == "bigtext" )
            s.m_bigText = atoi( w[1].c_str() ) != 0;
        else if ( w[0] == "perf" )
            s.m_perf = atoi( w[1].c_str() ) != 0;
    }
    return true;
}

bool saveSettings( const Settings &s )
{
    char buf[512];
    snprintf( buf, sizeof( buf ), "fullscreen %d\nmaster %.2f\nmusic %.2f\neffects %.2f\nlang %s\nvsync %d\nslot %d\nshake %d\nhints %d\n",
              s.m_fullscreen ? 1 : 0, s.m_master, s.m_music, s.m_effects, s.m_lang.empty() ? "-" : s.m_lang.c_str(), s.m_vsync ? 1 : 0,
              s.m_slot, s.m_shake ? 1 : 0, s.m_hints ? 1 : 0 );
    std::string t = buf;
    snprintf( buf, sizeof( buf ),
              "rumble %d\nfps %d\nspeed %d\ninvulnerable %d\ninfiniteammo %d\ncolourassist %d\nbigtext %d\nperf %d\n",
              s.m_rumble ? 1 : 0, s.m_fps, s.m_speed, s.m_invulnerable ? 1 : 0, s.m_infiniteAmmo ? 1 : 0,
              s.m_colourAssist ? 1 : 0, s.m_bigText ? 1 : 0, s.m_perf ? 1 : 0 );
    t += buf;
    return writeWhole( userDir() + "settings.txt", t );
}

bool loadProgress( int slot, Progress &p )
{
    std::ifstream in( slotPath( slot ) );
    if ( !in ) return false;
    p = Progress();
    std::string line;
    while ( std::getline( in, line ) )
    {
        std::vector<std::string> w = words( line );
        if ( w.size() < 2 ) continue;
        auto n = [&]( size_t i ) { return i < w.size() ? atoi( w[i].c_str() ) : 0; };
        if ( w[0] == "difficulty" ) p.m_difficulty = std::clamp( n( 1 ), 0, 2 );
        else if ( w[0] == "weapons" )
            p.m_weapons = (unsigned)n( 1 ) | 1u;
        else if ( w[0] == "ammo" )
            for ( int k = 0; k < WeaponCount; ++k ) p.m_ammo[k] = n( k + 1 );
        else if ( w[0] == "upgrade" )
            for ( int k = 0; k < WeaponCount; ++k ) p.m_upgrade[k] = std::clamp( n( k + 1 ), 0, 3 );
        else if ( w[0] == "armour" )
            p.m_armour = std::clamp( n( 1 ), 0, 3 );
        else if ( w[0] == "credits" )
            p.m_credits = n( 1 );
        else if ( w[0] == "score" )
            p.m_score = atol( w[1].c_str() );
        else if ( w[0] == "episode" )
            p.m_episode = std::clamp( n( 1 ), 1, 4 );
        else if ( w[0] == "level" )
            p.m_level = std::clamp( n( 1 ), 1, 9 );
        else if ( w[0] == "deaths" )
            p.m_deaths = n( 1 );
        else if ( w[0] == "playtime" )
            p.m_playTime = (float)atof( w[1].c_str() );
        else if ( w[0] == "cycle" )
            p.m_cycle = n( 1 );
        else if ( w[0] == "awards" )
            p.m_awards = strtoull( w[1].c_str(), nullptr, 10 );
        else if ( w[0] == "lore" )
            p.m_lore[w[1]] = 1;
        else if ( w[0] == "seen" )
            p.m_seen[w[1]] = 1;
        else if ( w[0] == "stats" && w.size() >= 6 )
            p.m_kills = atol( w[1].c_str() ), p.m_crystalsTotal = atol( w[2].c_str() ), p.m_creditsTotal = atol( w[3].c_str() ),
            p.m_frozenKills = atol( w[4].c_str() ), p.m_eliteKills = atol( w[5].c_str() );
        else if ( w[0] == "bossrush" )
            p.m_bossRush = (float)atof( w[1].c_str() );
        else if ( w[0] == "episodedeaths" )
            p.m_episodeDeaths = n( 1 );
        else if ( w[0] == "finished" )
            p.m_finished = n( 1 ) != 0;
        else if ( w[0] == "medals" && w.size() >= 4 )
        {
            LevelBest &b = p.m_best[w[1]];
            b.m_medals = n( 2 );
            b.m_trial = (float)atof( w[3].c_str() );
        }
        else if ( w[0] == "best" && w.size() >= 9 )
        {
            LevelBest &b = p.m_best[w[1]];
            b.m_done = n( 2 ) != 0;
            b.m_score = n( 3 );
            b.m_time = (float)atof( w[4].c_str() );
            b.m_treasure = n( 5 );
            b.m_secrets = n( 6 );
            b.m_secretsMax = n( 7 );
            b.m_kills = n( 8 );
        }
    }
    return true;
}

bool saveProgress( int slot, const Progress &p )
{
    std::string t;
    char        buf[256];
    snprintf( buf, sizeof( buf ), "difficulty %d\nweapons %u\n", p.m_difficulty, p.m_weapons );
    t += buf;
    t += "ammo";
    for ( int k = 0; k < WeaponCount; ++k ) t += " " + std::to_string( p.m_ammo[k] );
    t += "\nupgrade";
    for ( int k = 0; k < WeaponCount; ++k ) t += " " + std::to_string( p.m_upgrade[k] );
    snprintf( buf, sizeof( buf ), "\narmour %d\ncredits %d\nscore %ld\nepisode %d\nlevel %d\ndeaths %d\nplaytime %.1f\n", p.m_armour,
              p.m_credits, p.m_score, p.m_episode, p.m_level, p.m_deaths, p.m_playTime );
    t += buf;
    for ( const auto &[id, b] : p.m_best )
    {
        snprintf( buf, sizeof( buf ), "best %s %d %d %.2f %d %d %d %d\nmedals %s %d %.2f\n", id.c_str(), b.m_done ? 1 : 0, b.m_score, b.m_time,
                  b.m_treasure, b.m_secrets, b.m_secretsMax, b.m_kills, id.c_str(), b.m_medals, b.m_trial );
        t += buf;
    }
    snprintf( buf, sizeof( buf ), "cycle %d\nawards %llu\nstats %ld %ld %ld %ld %ld\nbossrush %.2f\nepisodedeaths %d\nfinished %d\n", p.m_cycle,
              p.m_awards, p.m_kills, p.m_crystalsTotal, p.m_creditsTotal, p.m_frozenKills, p.m_eliteKills, p.m_bossRush, p.m_episodeDeaths,
              p.m_finished ? 1 : 0 );
    t += buf;
    for ( const auto &[key, v] : p.m_lore ) t += "lore " + key + "\n";
    for ( const auto &[id, v] : p.m_seen ) t += "seen " + id + "\n";
    return writeWhole( slotPath( slot ), t );
}

bool slotInfo( int slot, std::string &line )
{
    Progress p;
    if ( !loadProgress( slot, p ) ) return false;
    int done = 0;
    for ( const auto &[id, b] : p.m_best ) done += b.m_done;
    line = "E" + std::to_string( p.m_episode ) + "-" + std::to_string( p.m_level ) + "  " + std::to_string( done ) + "/36  " +
           std::to_string( p.m_score );
    return true;
}

void clearSlot( int slot )
{
    std::error_code e;
    fs::remove( slotPath( slot ), e );
}

}   // namespace kepler
