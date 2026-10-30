/**
 * @file AppMore.cpp
 * @brief The third round around the levels: the death map's records, the time trial's ghost, challenges (modifiers,
 *        the daily one, best times), the bestiary, the pause map, the quick save in the middle of a level and the
 *        performance display (frame times and the battery, for the Steam Deck).
 * @author Rene Weller
 */
#include "AppImpl.h"

#include "Assets.h"
#include "Audio.h"
#include "Input.h"
#include "Text.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <sstream>

#ifdef _WIN32
extern "C"
{
    struct KeplerPowerStatus
    {
        unsigned char m_acLine, m_flag, m_percent, m_saver;
        unsigned long m_life, m_full;
    };
    __declspec( dllimport ) int __stdcall GetSystemPowerStatus( KeplerPowerStatus *status );
}
#endif

namespace kepler
{

namespace
{

namespace fs = std::filesystem;

/** @brief The local date (or date and time) as text. */
std::string stamp( const char *format )
{
    char   buf[40];
    time_t now = time( nullptr );
    strftime( buf, sizeof( buf ), format, localtime( &now ) );
    return buf;
}

uint32_t hashOf( const std::string &s )
{
    uint32_t h = 2166136261u;
    for ( unsigned char c : s ) h = ( h ^ c ) * 16777619u;
    return h;
}

/** @brief The challenges' modifiers (bits of the mods number). */
constexpr int     ModCount = 5;
const char *const ModKeys[ModCount] = { "chal.mod.blaster", "chal.mod.onehit", "chal.mod.gravity", "chal.mod.dark",
                                        "chal.mod.fast" };

/** @brief A best time of a challenge. */
struct ChallengeTime
{
    std::string m_key;
    float       m_time;
    std::string m_date;
};

std::vector<ChallengeTime> readChallengeTimes()
{
    std::vector<ChallengeTime> out;
    std::ifstream              in( userDir() + "challenges.txt" );
    std::string                line;
    while ( std::getline( in, line ) )
    {
        std::vector<std::string> w = words( line );
        if ( w.size() >= 3 ) out.push_back( { w[0], (float)atof( w[1].c_str() ), w[2] } );
    }
    return out;
}

std::string timeText( float t )
{
    return fmtTime( t ) + "." + std::to_string( (int)( std::fmod( t, 1.0f ) * 10 ) );
}

/** @brief The battery: percent and watts drawn (false without one; watts < 0 when unknown). */
bool battery( int &percent, float &watts )
{
    watts = -1;
#ifdef _WIN32
    KeplerPowerStatus s = {};
    if ( !GetSystemPowerStatus( &s ) || s.m_percent > 100 ) return false;
    percent = s.m_percent;
    return true;
#else
    for ( const char *dir : { "/sys/class/power_supply/BAT1/", "/sys/class/power_supply/BAT0/" } )
    {
        std::ifstream cap( std::string( dir ) + "capacity" );
        if ( !( cap >> percent ) ) continue;
        long          p = 0, i = 0, v = 0;
        std::ifstream pw( std::string( dir ) + "power_now" );
        if ( pw >> p )
            watts = p / 1e6f;
        else
        {
            std::ifstream cur( std::string( dir ) + "current_now" ), vol( std::string( dir ) + "voltage_now" );
            if ( ( cur >> i ) && ( vol >> v ) ) watts = (float)( (double)i * v / 1e12 );
        }
        return true;
    }
    return false;
#endif
}

}   // namespace

// ------------------------------------------------------------------------------------------- the death map

void App::recordDeaths( World &w, const std::string &file, const char *mode )
{
    // One line per knockout: level, where, by what, the difficulty, how it was played, when.
    if ( w.m_deathLog.empty() ) return;
    std::ofstream out( file, std::ios::app | std::ios::binary );
    for ( const World::Death &d : w.m_deathLog )
        out << ( w.m_level.m_id.empty() ? std::string( "level" ) : w.m_level.m_id ) << " " << (int)d.m_x << " "
            << (int)d.m_y << " " << ( d.m_cause.empty() ? std::string( "-" ) : d.m_cause ) << " "
            << m_progress.m_difficulty << " " << mode << " " << stamp( "%Y-%m-%dT%H:%M" ) << "\n";
    w.m_deathLog.clear();
}

void App::recordPlayDeaths()
{
    if ( !m_world ) return;
    if ( m_demo )
        m_world->m_deathLog.clear();
    else
        recordDeaths( *m_world, userDir() + "deaths.txt",
                      m_fromEditor       ? "editor"
                      : m_trial          ? "trial"
                      : m_challenge >= 0 ? "challenge"
                      : m_rush           ? "rush"
                      : m_bot            ? "autopilot"
                                         : "play" );
}

// -------------------------------------------------------------------------------------------------- ghosts

std::string App::ghostPath( const std::string &id ) const
{
    return userDir() + "ghosts/" + id + ".ghost";
}

void App::loadGhost( const std::string &id )
{
    // KKG1, the count, then x, y (floats), frame (int16), face (int8) per point.
    m_ghostTrack.clear();
    std::ifstream in( ghostPath( id ), std::ios::binary );
    char          magic[4] = {};
    uint32_t      n = 0;
    if ( !in.read( magic, 4 ) || std::string( magic, 4 ) != "KKG1" || !in.read( (char *)&n, 4 ) || n > 30 * 3600 )
        return;
    m_ghostTrack.resize( n );
    for ( World::TrackPoint &p : m_ghostTrack )
    {
        in.read( (char *)&p.m_x, 4 ), in.read( (char *)&p.m_y, 4 ), in.read( (char *)&p.m_frame, 2 ),
            in.read( (char *)&p.m_face, 1 );
        if ( !in ) return m_ghostTrack.clear();
    }
}

void App::saveGhost( const std::string &id, const std::vector<World::TrackPoint> &track )
{
    std::error_code e;
    fs::create_directories( userDir() + "ghosts", e );
    std::ofstream out( ghostPath( id ), std::ios::binary );
    uint32_t      n = (uint32_t)track.size();
    out.write( "KKG1", 4 ).write( (const char *)&n, 4 );
    for ( const World::TrackPoint &p : track )
        out.write( (const char *)&p.m_x, 4 )
            .write( (const char *)&p.m_y, 4 )
            .write( (const char *)&p.m_frame, 2 )
            .write( (const char *)&p.m_face, 1 );
}

// ------------------------------------------------------------------------------------------------ challenges

std::vector<std::string> App::challengeLevels() const
{
    // The levels open to the player (the first always), the secret ones once found.
    std::vector<std::string> ids;
    for ( int e = 1; e <= 4; ++e )
    {
        for ( int l = 1; l <= 9; ++l )
            if ( ( e == 1 && l == 1 ) || m_progress.unlocked( e, l ) ) ids.push_back( levelId( e, l ) );
        std::string secret = "e" + std::to_string( e ) + "s";
        if ( m_progress.m_best.count( secret ) ) ids.push_back( secret );
    }
    return ids;
}

void App::dailyChallenge( std::string &id, int &mods ) const
{
    // Today's level and two modifiers, the same all day.
    std::vector<std::string> ids = challengeLevels();
    uint32_t                 h = hashOf( "kepler" + stamp( "%Y%m%d" ) );
    id = ids[h % ids.size()];
    int a = ( h >> 8 ) % ModCount, b = ( h >> 16 ) % ( ModCount - 1 );
    if ( b >= a ) ++b;
    mods = ( 1 << a ) | ( 1 << b );
}

std::string App::challengeKey( const std::string &id, int mods, bool daily ) const
{
    return ( daily ? "daily" + stamp( "%Y%m%d" ) + ":" : std::string() ) + id + "+" + std::to_string( mods );
}

std::string App::modsText( int mods ) const
{
    std::string t;
    for ( int k = 0; k < ModCount; ++k )
        if ( mods & ( 1 << k ) ) t += ( t.empty() ? "" : ", " ) + tr( ModKeys[k] );
    return t.empty() ? tr( "chal.mod.none" ) : t;
}

bool App::startChallenge( const std::string &id, int mods, const std::string &key )
{
    m_challenge = mods;
    m_challengeKey = key;
    m_directLevel = true;
    if ( startLevelId( id, false ) ) return true;
    m_challenge = -1;
    m_directLevel = false;
    return false;
}

void App::finishChallenge( World &w )
{
    // The time goes into the best times (the five best of each challenge are kept).
    std::vector<ChallengeTime> all = readChallengeTimes();
    float                      best = 0;
    for ( const ChallengeTime &c : all )
        if ( c.m_key == m_challengeKey && ( best <= 0 || c.m_time < best ) ) best = c.m_time;
    all.push_back( { m_challengeKey, w.m_time, stamp( "%d.%m.%Y" ) } );
    std::stable_sort( all.begin(), all.end(), []( const ChallengeTime &a, const ChallengeTime &b )
                      { return a.m_key != b.m_key ? a.m_key < b.m_key : a.m_time < b.m_time; } );
    std::string text;
    int         kept = 0;
    for ( size_t i = 0; i < all.size(); ++i )
    {
        kept = i && all[i].m_key == all[i - 1].m_key ? kept + 1 : 0;
        if ( kept < 5 ) text += all[i].m_key + " " + std::to_string( all[i].m_time ) + " " + all[i].m_date + "\n";
    }
    writeWhole( userDir() + "challenges.txt", text );
    bool record = best <= 0 || w.m_time < best;
    m_tally.push_back(
        { tr( record ? "chal.tally_best" : "chal.tally" ), timeText( w.m_time ), { 255, 210, 120, 255 } } );
    // Pages and enemy kinds found count for the game too.
    m_progress.m_lore.insert( m_challengeProgress.m_lore.begin(), m_challengeProgress.m_lore.end() );
    m_progress.m_seen.insert( m_challengeProgress.m_seen.begin(), m_challengeProgress.m_seen.end() );
}

void App::updateChallenge( MenuKeys &k )
{
    // Rows: today's challenge, the level, the five modifiers, start, back.
    std::vector<std::string> ids = challengeLevels();
    int                      rows = 3 + ModCount + 1;
    if ( k.m_up ) m_cursor = ( m_cursor + rows - 1 ) % rows, sfx( "menu_move", 0.5f );
    if ( k.m_down ) m_cursor = ( m_cursor + 1 ) % rows, sfx( "menu_move", 0.5f );
    m_challengePick = std::clamp( m_challengePick, 0, (int)ids.size() - 1 );
    if ( m_cursor == 1 && ( k.m_left || k.m_right ) )
        m_challengePick = ( m_challengePick + ( k.m_right ? 1 : (int)ids.size() - 1 ) ) % (int)ids.size(),
        sfx( "menu_move", 0.5f );
    int mod = m_cursor - 2;
    if ( mod >= 0 && mod < ModCount && ( k.m_ok || k.m_left || k.m_right ) )
        m_challengeMods ^= 1 << mod, sfx( "menu_move", 0.6f );
    if ( k.m_back || ( k.m_ok && m_cursor == rows - 1 ) )
    {
        go( StateE::EXTRAS, 3 );
        return;
    }
    if ( !k.m_ok ) return;
    if ( m_cursor == 0 )
    {
        std::string id;
        int         mods = 0;
        dailyChallenge( id, mods );
        startChallenge( id, mods, challengeKey( id, mods, true ) );
    }
    else if ( m_cursor == 1 || m_cursor == 2 + ModCount )
        startChallenge( ids[m_challengePick], m_challengeMods,
                        challengeKey( ids[m_challengePick], m_challengeMods, false ) );
}

void App::drawChallenge()
{
    float cx = m_screen.m_w * 0.5f;
    drawText( tr( "chal.title" ), cx, 14, { 200, 235, 255, 255 }, true, true );
    std::vector<std::string> ids = challengeLevels();
    int                      pick = std::clamp( m_challengePick, 0, (int)ids.size() - 1 );
    std::string              dailyId;
    int                      dailyMods = 0;
    dailyChallenge( dailyId, dailyMods );
    auto levelName = [&]( const std::string &id ) { return hasText( "level." + id ) ? tr( "level." + id ) : id; };
    std::vector<std::string> rows = { tr( "chal.daily" ) + ": " + levelName( dailyId ),
                                      tr( "chal.level" ) + ":  < " + levelName( ids[pick] ) + " >" };
    for ( int m = 0; m < ModCount; ++m )
        rows.push_back( "[" + std::string( ( m_challengeMods >> m ) & 1 ? "x" : " " ) + "] " + tr( ModKeys[m] ) );
    rows.push_back( tr( "chal.start" ) );
    rows.push_back( tr( "menu.back" ) );
    drawPanel( 20, 48, 330, (int)rows.size() * 18 + 20 );
    for ( size_t i = 0; i < rows.size(); ++i )
    {
        bool        sel = (int)i == m_cursor;
        float       y = 58.0f + i * 18 + ( i >= 2 ? 6 : 0 ) + ( i >= 2 + ModCount ? 6 : 0 );
        std::string t = rows[i];
        while ( assets().font().width( t ) > 290 && t.size() > 6 ) t = t.substr( 0, t.size() - 4 ) + "...";
        drawText( t, 44, y,
                  sel      ? Color{ 255, 230, 120, 255 }
                  : i == 0 ? Color{ 150, 230, 255, 255 }
                           : Color{ 210, 220, 240, 255 } );
        if ( sel ) drawText( ">", 30 + std::sin( m_t * 8 ) * 2, y, { 255, 200, 90, 255 } );
    }
    // On the right: what the row means and its best times.
    bool        daily = m_cursor == 0;
    std::string key =
        daily ? challengeKey( dailyId, dailyMods, true ) : challengeKey( ids[pick], m_challengeMods, false );
    drawPanel( 362, 48, m_screen.m_w - 382, 250 );
    drawText( daily ? tr( "chal.daily" ) + "  " + stamp( "%d.%m.%Y" ) : tr( "chal.own" ), 376, 58,
              { 255, 210, 120, 255 } );
    drawText( levelName( daily ? dailyId : ids[pick] ), 376, 76, { 220, 230, 250, 255 } );
    drawText( modsText( daily ? dailyMods : m_challengeMods ), 376, 92, { 150, 200, 255, 255 } );
    drawText( tr( "chal.best" ), 376, 118, { 200, 235, 255, 255 } );
    int row = 0;
    for ( const ChallengeTime &c : readChallengeTimes() )
        if ( c.m_key == key && row < 5 )
        {
            drawText( std::to_string( row + 1 ) + ".  " + timeText( c.m_time ), 380, 136.0f + row * 16,
                      { 255, 230, 140, 255 } );
            drawText( c.m_date, 500, 136.0f + row * 16, { 150, 170, 200, 255 } );
            ++row;
        }
    if ( !row ) drawText( tr( "chal.no_times" ), 380, 136, { 140, 150, 180, 255 } );
    if ( m_cursor >= 2 && m_cursor < 2 + ModCount )
        drawText( tr( std::string( ModKeys[m_cursor - 2] ) + ".about" ), cx, m_screen.m_h - 40.0f,
                  { 180, 215, 245, 255 }, false, true );
    else
        drawText( tr( "chal.about" ), cx, m_screen.m_h - 40.0f, { 180, 215, 245, 255 }, false, true );
}

// -------------------------------------------------------------------------------------------------- bestiary

std::vector<std::string> App::bestiaryIds() const
{
    std::vector<std::string> ids;
    for ( const EnemyDef &d : enemyDefs() ) ids.push_back( d.m_id );
    for ( const char *b : { "warden", "broodmother", "colossus", "gloam" } ) ids.push_back( b );
    return ids;
}

void App::drawBestiary()
{
    std::vector<std::string> ids = bestiaryIds();
    drawPanel( 20, 50, 220, m_screen.m_h - 70 );
    drawPanel( 250, 50, m_screen.m_w - 270, m_screen.m_h - 70 );
    int rows = ( m_screen.m_h - 90 ) / 14;
    if ( m_cursor < m_listTop ) m_listTop = m_cursor;
    if ( m_cursor >= m_listTop + rows ) m_listTop = m_cursor - rows + 1;
    for ( int i = m_listTop; i < (int)ids.size() && i < m_listTop + rows; ++i )
    {
        bool seen = m_progress.m_seen.count( ids[i] ) > 0, sel = i == m_cursor;
        drawText( seen ? tr( "beast." + ids[i] ) : "? ? ?", 32, 60.0f + ( i - m_listTop ) * 14,
                  sel    ? Color{ 255, 230, 120, 255 }
                  : seen ? Color{ 210, 220, 240, 255 }
                         : Color{ 100, 105, 125, 255 } );
    }
    if ( m_cursor >= (int)ids.size() ) return;
    const std::string &id = ids[m_cursor];
    if ( !m_progress.m_seen.count( id ) )
    {
        drawText( tr( "beast.unknown" ), 264, 62, { 140, 150, 180, 255 } );
        return;
    }
    // The creature itself (its first frame, whole pixels, at most 96 high), its name, what it does, how to beat it.
    const Sheet &sh = assets().sheet( id );
    float        top = 62;
    if ( !sh.m_standIn && sh.m_tex.id )
    {
        std::string anim = sh.anim( "move" ) ? "move" : sh.anim( "idle" ) ? "idle" : sh.m_firstAnim;
        int         f = sh.frame( anim, (float)GetTime() ), cols = std::max( 1, sh.m_tex.width / sh.m_fw );
        float       sc = std::max( 1.0f, std::floor( std::min( 96.0f / sh.m_fh, 200.0f / sh.m_fw ) ) );
        Rectangle   src = { (float)( f % cols ) * sh.m_fw, (float)( f / cols ) * sh.m_fh, (float)sh.m_fw,
                            (float)sh.m_fh };
        float       w = sh.m_fw * sc, h = sh.m_fh * sc;
        DrawTexturePro( sh.m_tex, src, { std::floor( 250 + ( m_screen.m_w - 270 - w ) * 0.5f ), top, w, h }, { 0, 0 },
                        0, WHITE );
        top += h + 8;
    }
    drawText( tr( "beast." + id ), 264, top, { 255, 210, 120, 255 } );
    float y = top + 18;
    for ( const std::string &l : wrapText( glyphs( tr( "beast." + id + ".text" ), padInUse() ), m_screen.m_w - 300 ) )
        drawText( l, 264, y, { 220, 230, 250, 255 } ), y += 13;
    y += 4;
    for ( const std::string &l : wrapText(
              tr( "beast.weak" ) + " " + glyphs( tr( "beast." + id + ".weak" ), padInUse() ), m_screen.m_w - 300 ) )
        drawText( l, 264, y, { 150, 230, 170, 255 } ), y += 13;
}

// ------------------------------------------------------------------------------------------------ pause map

void App::buildMap()
{
    // One pixel per cell: what has been on the screen, the rest dark.
    if ( m_mapTex.id ) UnloadTexture( m_mapTex );
    m_mapTex = {};
    if ( !m_world ) return;
    const World &w = *m_world;
    const Level &L = w.m_level;
    Image        img = GenImageColor( L.m_w, L.m_h, { 6, 8, 16, 255 } );
    for ( int y = 0; y < L.m_h; ++y )
        for ( int x = 0; x < L.m_w; ++x )
        {
            size_t i = (size_t)y * L.m_w + x;
            if ( !w.m_explored[i] ) continue;
            CellE k = L.at( x, y ).m_kind;
            Color c = { 26, 30, 52, 255 };
            if ( k == CellE::LIQUID )
                c = { 40, 150, 140, 255 };
            else if ( k == CellE::SPIKE_UP || k == CellE::SPIKE_DOWN || k == CellE::SPIKE_LEFT ||
                      k == CellE::SPIKE_RIGHT )
                c = { 210, 70, 70, 255 };
            else if ( k == CellE::DOOR_BLUE && !w.m_doorOpen[i] )
                c = { 80, 140, 255, 255 };
            else if ( k == CellE::DOOR_GOLD && !w.m_doorOpen[i] )
                c = { 240, 200, 70, 255 };
            else if ( k == CellE::PLATFORM )
                c = { 170, 190, 220, 255 };
            else if ( k == CellE::CRUMBLE )
                c = { 160, 130, 100, 255 };
            else if ( w.solid( x, y ) )
                c = { 110, 125, 160, 255 };
            ImageDrawPixel( &img, x, y, c );
        }
    m_mapTex = LoadTextureFromImage( img );
    UnloadImage( img );
}

void App::drawMap()
{
    if ( !m_world ) return;
    const World &w = *m_world;
    const Level &L = w.m_level;
    float        cx = m_screen.m_w * 0.5f;
    DrawRectangle( 0, 0, m_screen.m_w, m_screen.m_h, { 0, 0, 10, 210 } );
    drawText( tr( "map.title" ), cx, 8, { 200, 235, 255, 255 }, true, true );
    float sc = std::min( ( m_screen.m_w - 40.0f ) / L.m_w, ( m_screen.m_h - 84.0f ) / L.m_h );
    if ( sc >= 1 ) sc = std::floor( sc );
    float mw = L.m_w * sc, mh = L.m_h * sc, ox = std::floor( cx - mw * 0.5f ),
          oy = std::floor( 40 + ( m_screen.m_h - 84 - mh ) * 0.5f );
    DrawRectangleLines( (int)ox - 2, (int)oy - 2, (int)mw + 4, (int)mh + 4, { 90, 190, 255, 255 } );
    if ( m_mapTex.id )
        DrawTexturePro( m_mapTex, { 0, 0, (float)L.m_w, (float)L.m_h }, { ox, oy, mw, mh }, { 0, 0 }, 0, WHITE );
    auto dot = [&]( float px, float py, float r, Color c )
    { DrawCircleV( { ox + px / Tile * sc, oy + py / Tile * sc }, std::max( 1.5f, r * sc ), c ); };
    auto seen = [&]( float px, float py )
    {
        int x = (int)( px / Tile ), y = (int)( py / Tile );
        return x >= 0 && y >= 0 && x < L.m_w && y < L.m_h && w.m_explored[(size_t)y * L.m_w + x];
    };
    // The crystals still missing (all of them: the map is there to find the last ones), keys, pages, the exit,
    // the checkpoints, the hero.
    int missing = 0;
    for ( const Pickup &p : w.m_pickups )
    {
        if ( p.m_taken ) continue;
        if ( p.m_kind == PickE::CRYSTAL )
            dot( p.m_x, p.m_y, 0.45f, { 120, 230, 255, 255 } ), ++missing;
        else if ( ( p.m_kind == PickE::KEY_BLUE || p.m_kind == PickE::KEY_GOLD ) && seen( p.m_x, p.m_y ) )
            dot( p.m_x, p.m_y, 0.6f,
                 p.m_kind == PickE::KEY_BLUE ? Color{ 80, 140, 255, 255 } : Color{ 255, 210, 70, 255 } );
        else if ( p.m_kind == PickE::LORE && seen( p.m_x, p.m_y ) )
            dot( p.m_x, p.m_y, 0.45f, { 240, 240, 255, 255 } );
    }
    for ( const Object &o : w.m_objects )
    {
        if ( o.m_kind == "exit" )
            dot( o.m_x, o.m_y - 20, 0.8f, w.m_exitOpen ? Color{ 120, 255, 150, 255 } : Color{ 120, 130, 140, 255 } );
        else if ( o.m_kind == "checkpoint" && seen( o.m_x, o.m_y - 10 ) )
            dot( o.m_x, o.m_y - 10, 0.5f, o.m_on ? Color{ 120, 255, 200, 255 } : Color{ 90, 140, 130, 255 } );
    }
    // Kip always, a ring pulsing around him.
    dot( w.m_hero.m_x, w.m_hero.m_y - 20, 0.8f, { 255, 220, 80, 255 } );
    DrawCircleLines( (int)( ox + w.m_hero.m_x / Tile * sc ), (int)( oy + ( w.m_hero.m_y - 20 ) / Tile * sc ),
                     std::max( 3.0f, sc * ( 1.4f + 0.6f * std::sin( m_t * 6 ) ) ), { 255, 220, 80, 200 } );
    // The key below.
    std::string legend = tr( "map.crystals" ) + " " + std::to_string( missing ) + "   " + tr( "map.secrets" ) + " " +
                         std::to_string( w.m_secretsFound ) + "/" + std::to_string( w.m_secrets ) + "   " +
                         tr( "map.legend" );
    drawText( legend, cx, m_screen.m_h - 34.0f, { 180, 210, 240, 255 }, false, true );
    drawText( tr( "map.back" ), cx, m_screen.m_h - 18.0f, { 140, 160, 200, 255 }, false, true );
}

// ------------------------------------------------------------------------------------- quick save in a level

std::string App::suspendPath() const
{
    return userDir() + "suspend" + std::to_string( m_settings.m_slot + 1 ) + ".txt";
}

bool App::canSuspend() const
{
    // Only the game's own run through the episodes keeps its place (not trials, challenges, rush, tests, the demo).
    return m_world && !m_directLevel && !m_demo && !m_trial && !m_rush && !m_fromEditor && m_challenge < 0 && !m_bot &&
           m_world->m_exitT < 0 && !m_world->m_finished && !m_world->m_dead;
}

void App::saveSuspend()
{
    if ( !canSuspend() ) return;
    writeWhole( suspendPath(), "level " + m_world->m_level.m_id + "\n" + m_world->snapshot() );
    saveProgress( m_settings.m_slot, m_progress );
    m_hasSave = true;
}

void App::clearSuspend()
{
    std::error_code e;
    fs::remove( suspendPath(), e );
}

bool App::hasSuspend() const
{
    std::error_code e;
    return fs::exists( suspendPath(), e );
}

bool App::resumeSuspend()
{
    std::ifstream in( suspendPath(), std::ios::binary );
    std::string   first, id;
    if ( !std::getline( in, first ) || first.rfind( "level ", 0 ) != 0 ) return false;
    id = first.substr( 6 );
    std::stringstream rest;
    rest << in.rdbuf();
    if ( !loadLevelId( id ) ) return false;
    m_world->restore( rest.str() );
    m_toasts.push_back( { tr( "msg.resumed" ), 2.5f } );
    return true;
}

// ------------------------------------------------------------------------------------------ the performance

void App::updatePerf( float frame )
{
    // A line a second: frames, their average and longest time, the battery; written down while the display is on.
    if ( !perfOn() ) return;
    ++m_perfN, m_perfSum += frame, m_perfMax = std::max( m_perfMax, frame );
    if ( m_perfSum < 1.0f ) return;
    int   pct = 0;
    float watts = -1;
    bool  bat = battery( pct, watts );
    char  buf[160];
    snprintf( buf, sizeof( buf ), "%.0f fps  %.1f ms  (max %.1f)", m_perfN / m_perfSum, 1000 * m_perfSum / m_perfN,
              1000 * m_perfMax );
    m_perfLine = buf;
    if ( bat )
    {
        snprintf( buf, sizeof( buf ), "  %s %d%%", tr( "perf.battery" ).c_str(), pct );
        m_perfLine += buf;
        if ( watts >= 0 ) snprintf( buf, sizeof( buf ), "  %.1f W", watts ), m_perfLine += buf;
    }
    static const char *fpsNames[5] = { "screen", "144", "60", "40", "30" };
    std::ofstream      out( userDir() + "perf.txt", std::ios::app | std::ios::binary );
    out << stamp( "%Y-%m-%dT%H:%M:%S" ) << " "
        << ( m_world && ( m_state == StateE::PLAY || m_state == StateE::PAUSE ) ? m_world->m_level.m_id
                                                                                : std::string( "menu" ) )
        << " fps=" << m_perfN / m_perfSum << " avg_ms=" << 1000 * m_perfSum / m_perfN << " max_ms=" << 1000 * m_perfMax
        << " target=" << fpsNames[std::clamp( m_settings.m_fps, 0, 4 )]
        << " battery=" << ( bat ? std::to_string( pct ) : std::string( "-" ) )
        << " watts=" << ( watts >= 0 ? std::to_string( watts ) : std::string( "-" ) ) << "\n";
    m_perfN = 0, m_perfSum = 0, m_perfMax = 0;
}

void App::drawPerf()
{
    if ( !perfOn() || m_perfLine.empty() ) return;
    int w = assets().font().width( m_perfLine );
    DrawRectangle( ( m_screen.m_w - w ) / 2 - 4, m_screen.m_h - 15, w + 8, 13, { 0, 0, 0, 170 } );
    drawText( m_perfLine, m_screen.m_w * 0.5f, m_screen.m_h - 14.0f, { 160, 255, 170, 255 }, false, true );
}

}   // namespace kepler
