/**
 * @file AppExtras.cpp
 * @brief The second round around the levels: the Commodore's radio messages, medals and awards, the logbook, the
 *        high scores, secret levels, boss rush, time trial, New Game+, the demo and the assist settings.
 * @author Rene Weller
 */
#include "AppImpl.h"

#include "Assets.h"
#include "Audio.h"
#include "Input.h"
#include "Rumble.h"
#include "Text.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <ctime>
#include <fstream>

namespace kepler
{

namespace
{

/** @brief Episode and stage of a level id: e2l5 -> 2, 5; e3s -> 3, 10 (the secret level). */
void parseId( const std::string &id, int &episode, int &stage )
{
    episode = id.size() > 1 ? id[1] - '0' : 1;
    stage = id.size() > 2 && id[2] == 's' ? 10 : id.size() > 3 ? atoi( id.c_str() + 3 ) : 1;
}

/** @brief One line of the high scores. */
struct ScoreLine
{
    int         m_difficulty;
    long        m_score;
    int         m_episode;
    int         m_cycle;
    std::string m_date;
};

std::vector<ScoreLine> readScores()
{
    std::vector<ScoreLine> out;
    std::ifstream          in( userDir() + "highscores.txt" );
    std::string            line;
    while ( std::getline( in, line ) )
    {
        std::vector<std::string> w = words( line );
        if ( w.size() < 5 ) continue;
        out.push_back( { atoi( w[0].c_str() ), atol( w[1].c_str() ), atoi( w[2].c_str() ), atoi( w[3].c_str() ), w[4] } );
    }
    return out;
}

}   // namespace

std::vector<std::string> wrapText( const std::string &text, int width, bool big )
{
    const PixelFont         &f = big ? assets().font( true, true ) : assets().font();
    std::vector<std::string> lines;
    std::string              line, word;
    auto                     flush = [&]()
    {
        if ( word.empty() ) return;
        std::string t = line.empty() ? word : line + " " + word;
        if ( f.width( t ) > width && !line.empty() ) lines.push_back( line ), line = word;
        else
            line = t;
        word.clear();
    };
    for ( char ch : text )
    {
        if ( ch == ' ' ) flush();
        else if ( ch == '\n' )
            flush(), lines.push_back( line ), line.clear();
        else
            word += ch;
    }
    flush();
    if ( !line.empty() ) lines.push_back( line );
    return lines;
}

// ---------------------------------------------------------------------------------------------------- levels

bool App::startLevelId( const std::string &id, bool radio )
{
    // The Commodore says something first (not in time trials, boss rush, the demo or the autopilot's runs).
    if ( radio && !m_trial && !m_rush && !m_demo && !m_o.m_autoplay && hasText( "radio." + id ) )
    {
        m_pendingId = id;
        m_radioT = 0;
        m_radioVoice = voice( assetDir() + "voice/" + language() + "/radio_" + id + ".ogg" );
        go( StateE::RADIO );
        return true;
    }
    return loadLevelId( id );
}

bool App::loadLevelId( const std::string &id )
{
    stopVoice();
    std::string path = assetDir() + "levels/" + id + ".txt";
    if ( !FileExists( path.c_str() ) )
    {
        m_message = tr( "menu.missing_level" ) + " " + id;
        m_messageT = 3;
        return false;
    }
    int episode, stage;
    parseId( id, episode, stage );
    grantEpisodeWeapons( episode );
    // A challenge plays with a copy of what Kip carries (full ammo; only the blaster if so modified).
    if ( m_challenge >= 0 )
    {
        m_challengeProgress = m_progress;
        for ( int k = 1; k < WeaponCount; ++k )
            m_challengeProgress.m_ammo[k] = m_challengeProgress.ammoMax( (WeaponE)k );
        if ( m_challenge & 1 ) m_challengeProgress.m_weapons = 1;
    }
    // A level of the episodes begun afresh drops the place kept in another one.
    if ( !m_directLevel && !m_demo && !m_trial && !m_rush && m_challenge < 0 ) clearSuspend();
    auto world = std::make_unique<World>();
    world->setView( m_screen.m_w, m_screen.m_h );
    std::string error;
    if ( !world->load( path, m_challenge >= 0 ? m_challengeProgress : m_progress, error ) )
    {
        m_message = id + ": " + error;
        m_messageT = 6;
        TraceLog( LOG_ERROR, "%s", m_message.c_str() );
        return false;
    }
    m_world = std::move( world );
    m_world->m_trial = m_trial || m_challenge >= 0;
    if ( m_challenge >= 0 )
    {
        m_world->m_oneHit = ( m_challenge & 2 ) != 0;
        m_world->m_gravityMul = ( m_challenge & 4 ) ? 0.6f : 1.0f;
        if ( m_challenge & 8 ) m_world->m_dark = std::max( m_world->m_dark, 0.88f );
    }
    // A time trial records Kip's way; the best one so far runs beside him.
    if ( m_trial )
    {
        loadGhost( id );
        m_world->m_record = true;
        m_world->m_ghost = m_ghostTrack.empty() ? nullptr : &m_ghostTrack;
    }
    applyWorldSettings();
    if ( m_o.m_autoplay || m_demo )
    {
        m_bot = std::make_unique<Bot>();
        m_bot->m_realTime = true;
        m_bot->start( *m_world );
    }
    else
        m_bot.reset();
    // A new episode counts its knockouts afresh.
    if ( stage == 1 && !m_directLevel && !m_demo ) m_progress.m_episodeDeaths = 0;
    m_episode = episode, m_stage = stage;
    if ( !m_directLevel && !m_demo && stage <= 9 ) m_progress.m_episode = episode, m_progress.m_level = stage;
    go( StateE::PLAY );
    return true;
}

void App::nextAfterLevel( World &w, int &medals )
{
    Color medal = { 255, 210, 120, 255 };
    int   par = (int)w.m_level.num( "par", 0 );
    medals = 0;
    if ( par && w.m_time <= par ) medals |= MEDAL_TIME;
    if ( w.m_treasure == 0 || w.m_treasureTaken == w.m_treasure ) medals |= MEDAL_TREASURE;
    if ( w.m_hits == 0 ) medals |= MEDAL_UNHURT;
    if ( w.m_secrets == 0 || w.m_secretsFound == w.m_secrets ) medals |= MEDAL_SECRETS;
    std::string won;
    static const char *names[4] = { "medal.time", "medal.treasure", "medal.unhurt", "medal.secrets" };
    for ( int k = 0; k < 4; ++k )
        if ( medals & ( 1 << k ) ) won += ( won.empty() ? "" : ", " ) + tr( names[k] );
    m_tally.push_back( { tr( "tally.medals" ), won.empty() ? "-" : won, medal } );
    std::string id = w.m_level.m_id;
    if ( m_trial )
    {
        LevelBest &b = m_progress.m_best[id];
        bool       best = b.m_trial <= 0 || w.m_time < b.m_trial;
        if ( best ) b.m_trial = w.m_time, saveGhost( id, w.m_track );
        m_tally.push_back( { tr( best ? "tally.trial_best" : "tally.trial" ), fmtTime( w.m_time ) + "." + std::to_string( (int)( std::fmod( w.m_time, 1.0f ) * 10 ) ), medal } );
    }
    if ( m_challenge >= 0 )
    {
        finishChallenge( w );
        m_nextId.clear();
        return;
    }
    if ( m_demo || m_fromEditor )
    {
        if ( m_fromEditor ) grantApp( AW_EDITOR );
        m_nextId.clear();
        return;
    }
    if ( medals & MEDAL_TIME ) grantApp( AW_PAR_LEVEL );
    if ( w.m_treasure && ( medals & MEDAL_TREASURE ) ) grantApp( AW_TREASURE_LEVEL );
    if ( medals & MEDAL_UNHURT ) grantApp( AW_UNHURT_LEVEL );
    if ( w.m_secrets && ( medals & MEDAL_SECRETS ) ) grantApp( AW_SECRETS_LEVEL );
    m_progress.m_crystalsTotal += w.m_crystalsTaken;
    m_progress.m_episodeDeaths += w.m_deaths;
    int episode, stage;
    parseId( id, episode, stage );
    // The bosses and the episodes.
    if ( stage == 9 && !m_trial )
    {
        static const AwardE episodes[4] = { AW_EPISODE1, AW_EPISODE2, AW_EPISODE3, AW_EPISODE4 };
        static const AwardE clean[4] = { AW_WARDEN_CLEAN, AW_BROOD_CLEAN, AW_COLOSSUS_CLEAN, AW_GLOAM_CLEAN };
        if ( !m_rush ) grantApp( episodes[episode - 1] );
        if ( w.m_deaths == 0 ) grantApp( clean[episode - 1] );
        if ( !m_rush && !m_directLevel )
        {
            if ( m_progress.m_difficulty == 2 ) grantApp( AW_HARD_EPISODE );
            if ( m_progress.m_episodeDeaths == 0 ) grantApp( AW_NO_DEATH_EPISODE );
            addHighScore();
            if ( episode == 4 ) m_progress.m_finished = true;
        }
    }
    if ( stage == 10 )
    {
        static const AwardE secrets[4] = { AW_SECRET1, AW_SECRET2, AW_SECRET3, AW_SECRET4 };
        grantApp( secrets[episode - 1] );
    }
    // What comes next.
    if ( m_rush )
    {
        m_rushTime += w.m_time;
        if ( m_rush < 4 ) m_nextId = levelId( m_rush + 1, 9 );
        else
        {
            bool best = m_progress.m_bossRush <= 0 || m_rushTime < m_progress.m_bossRush;
            if ( best ) m_progress.m_bossRush = m_rushTime;
            grantApp( AW_BOSS_RUSH );
            m_tally.push_back( { tr( best ? "tally.rush_best" : "tally.rush" ), fmtTime( m_rushTime ), medal } );
            m_nextId.clear();
        }
        return;
    }
    if ( m_trial || m_directLevel )
    {
        m_nextId.clear();
        return;
    }
    if ( !w.m_warp.empty() )
    {
        m_afterSecret = stage < 9 ? levelId( episode, stage + 1 ) : "";
        m_nextId = w.m_warp;
    }
    else if ( stage == 10 )
        m_nextId = m_afterSecret.empty() ? "" : m_afterSecret;
    else if ( stage < 9 )
        m_nextId = levelId( episode, stage + 1 );
    else
        m_nextId = episode < 4 ? levelId( episode + 1, 1 ) : "";
}

// ---------------------------------------------------------------------------------------------------- awards

void App::grantApp( AwardE a )
{
    if ( m_progress.award( a ) ) return;
    m_progress.m_awards |= 1ull << (int)a;
    m_toasts.push_back( { tr( "msg.award" ) + " " + tr( awardKey( a ) ), 3.5f } );
    sfx( "extra", 0.8f );
}

void App::checkAwards()
{
    unsigned all = ( 1u << WeaponCount ) - 1;
    if ( ( m_progress.m_weapons & all ) == all ) grantApp( AW_ALL_WEAPONS );
    bool any3 = false, all3 = true;
    for ( int w = 0; w < WeaponCount; ++w )
    {
        if ( m_progress.m_upgrade[w] >= 3 ) any3 = true;
        if ( m_progress.m_upgrade[w] < 3 ) all3 = false;
    }
    if ( any3 ) grantApp( AW_FULL_UPGRADE );
    if ( all3 ) grantApp( AW_ALL_UPGRADES );
    if ( m_progress.m_armour >= 3 ) grantApp( AW_ARMOUR3 );
    if ( m_progress.m_creditsTotal >= 10000 ) grantApp( AW_RICH );
    if ( m_progress.m_crystalsTotal >= 250 ) grantApp( AW_CRYSTALS250 );
    if ( m_progress.m_crystalsTotal >= 750 ) grantApp( AW_CRYSTALS750 );
    int medals = 0;
    for ( const auto &[id, b] : m_progress.m_best )
        for ( int k = 0; k < 4; ++k ) medals += ( b.m_medals >> k ) & 1;
    if ( medals >= 10 ) grantApp( AW_MEDALS10 );
    if ( medals >= 40 ) grantApp( AW_MEDALS40 );
    if ( medals >= 160 ) grantApp( AW_MEDALS_ALL );
}

void App::addHighScore()
{
    std::vector<ScoreLine> all = readScores();
    char                   date[32];
    time_t                 now = time( nullptr );
    strftime( date, sizeof( date ), "%d.%m.%Y", localtime( &now ) );
    all.push_back( { m_progress.m_difficulty, m_progress.m_score, m_episode, m_progress.m_cycle, date } );
    std::sort( all.begin(), all.end(), []( const ScoreLine &a, const ScoreLine &b ) { return a.m_score > b.m_score; } );
    std::string text;
    int         kept[3] = { 0, 0, 0 };
    for ( const ScoreLine &l : all )
    {
        int d = std::clamp( l.m_difficulty, 0, 2 );
        if ( kept[d]++ >= 10 ) continue;
        text += std::to_string( d ) + " " + std::to_string( l.m_score ) + " " + std::to_string( l.m_episode ) + " " + std::to_string( l.m_cycle ) + " " +
                l.m_date + "\n";
    }
    std::ofstream out( userDir() + "highscores.txt", std::ios::binary );
    out << text;
}

// ------------------------------------------------------------------------------------------------ modes, demo

void App::startBossRush()
{
    m_rush = 1;
    m_rushTime = 0;
    m_directLevel = true;
    if ( !startLevelId( levelId( 1, 9 ), false ) ) m_rush = 0, m_directLevel = false;
}

void App::startDemo()
{
    // The autopilot plays one of the levels while nobody touches anything.
    std::vector<std::string> ids;
    for ( int e = 1; e <= 4; ++e )
        for ( int l = 1; l <= 8; ++l )
            if ( FileExists( ( assetDir() + "levels/" + levelId( e, l ) + ".txt" ).c_str() ) ) ids.push_back( levelId( e, l ) );
    if ( ids.empty() ) return;
    Progress keep = m_progress;
    m_demo = true;
    m_directLevel = true;
    m_progress.m_weapons = ( 1u << WeaponCount ) - 1;
    for ( int k = 1; k < WeaponCount; ++k ) m_progress.m_ammo[k] = m_progress.ammoMax( (WeaponE)k );
    if ( !loadLevelId( ids[GetRandomValue( 0, (int)ids.size() - 1 )] ) ) m_demo = false, m_directLevel = false;
    m_progress = keep;
    if ( m_world ) m_world->m_progress = &m_progress;
}

void App::applyAssist()
{
    static const int fps[5] = { 0, 144, 60, 40, 30 };
    int f = fps[std::clamp( m_settings.m_fps, 0, 4 )];
    SetTargetFPS( f ? f : std::max( 60, GetMonitorRefreshRate( GetCurrentMonitor() ) ) );
    rumble::stop();
}

// ------------------------------------------------------------------------------------------- extras: update

void App::updateExtras( StateE state, MenuKeys &k, float dt )
{
    (void)dt;
    auto moveCursor = [&]( int n )
    {
        if ( n <= 0 ) return;
        if ( k.m_up ) m_cursor = ( m_cursor + n - 1 ) % n, sfx( "menu_move", 0.5f );
        if ( k.m_down ) m_cursor = ( m_cursor + 1 ) % n, sfx( "menu_move", 0.5f );
    };
    switch ( state )
    {
    case StateE::RADIO:
        m_radioT += GetFrameTime();
        if ( k.m_ok || k.m_back )
        {
            size_t len = tr( "radio." + m_pendingId ).size();
            if ( m_radioT * 45 < len && !k.m_back ) m_radioT = 999;
            else if ( !loadLevelId( m_pendingId ) )
                go( StateE::MAIN );
        }
        break;

    case StateE::EXTRAS:
    {
        moveCursor( 7 );
        if ( k.m_back ) go( StateE::MAIN, 3 );
        // Left and right choose the editor's level slot.
        if ( m_cursor == 5 && ( k.m_left || k.m_right ) )
            m_editorSlot = ( m_editorSlot + ( k.m_right ? 1 : 7 ) ) % 9 + 1, sfx( "menu_move" );
        if ( !k.m_ok ) break;
        bool bosses = true;
        for ( int e = 1; e <= 4; ++e ) bosses &= m_progress.m_best.count( levelId( e, 9 ) ) && m_progress.m_best[levelId( e, 9 )].m_done;
        if ( m_cursor == 0 ) m_listTop = 0, go( StateE::LOGBOOK );
        else if ( m_cursor == 1 )
            m_listTop = 0, go( StateE::AWARDS );
        else if ( m_cursor == 2 )
            m_scoreDiff = m_progress.m_difficulty, go( StateE::SCORES );
        else if ( m_cursor == 3 )
            go( StateE::CHALLENGE );
        else if ( m_cursor == 4 )
        {
            if ( bosses ) startBossRush();
            else
                m_message = tr( "menu.rush_locked" ), m_messageT = 2.5f;
        }
        else if ( m_cursor == 5 )
            openEditor( userDir() + "levels/custom" + std::to_string( m_editorSlot ) + ".txt" );
        else
            go( StateE::MAIN, 3 );
        break;
    }

    case StateE::LOGBOOK:
    {
        // Left and right turn between the pages found and the bestiary.
        if ( k.m_left || k.m_right ) m_logTab ^= 1, m_cursor = 0, m_listTop = 0, sfx( "menu_move", 0.5f );
        size_t n = m_logTab ? bestiaryIds().size() : textKeys( "lore.", ".title" ).size();
        moveCursor( (int)std::max<size_t>( 1, n ) );
        if ( k.m_back || k.m_ok ) go( StateE::EXTRAS, 0 );
        break;
    }

    case StateE::AWARDS:
        moveCursor( AW_COUNT );
        if ( k.m_back || k.m_ok ) go( StateE::EXTRAS, 1 );
        break;

    case StateE::SCORES:
        if ( k.m_left ) m_scoreDiff = ( m_scoreDiff + 2 ) % 3, sfx( "menu_move", 0.5f );
        if ( k.m_right ) m_scoreDiff = ( m_scoreDiff + 1 ) % 3, sfx( "menu_move", 0.5f );
        if ( k.m_back || k.m_ok ) go( StateE::EXTRAS, 2 );
        break;

    default: break;
    }
}

// --------------------------------------------------------------------------------------------- extras: draw

void App::drawMedals( int medals, float x, float y, float size )
{
    // Clock, treasure, heart, secret: lit when won, a dim outline when not.
    const Sheet &hud = assets().sheetIn( "ui", "hud" );
    static const char *icons[4] = { "clock", "credits", "health", "secret" };
    for ( int k = 0; k < 4; ++k )
    {
        bool  on = ( medals >> k ) & 1;
        float x0 = x + k * ( size + 2 );
        if ( hud.m_standIn )
        {
            DrawRectangle( (int)x0, (int)y, (int)size, (int)size, on ? Color{ 255, 210, 90, 255 } : Color{ 60, 60, 80, 255 } );
            continue;
        }
        int       f = hud.frame( icons[k], 0 ), cols = std::max( 1, hud.m_tex.width / hud.m_fw );
        Rectangle src = { (float)( f % cols ) * hud.m_fw, (float)( f / cols ) * hud.m_fh, (float)hud.m_fw, (float)hud.m_fh };
        DrawTexturePro( hud.m_tex, src, { x0, y, size, size }, { 0, 0 }, 0, on ? WHITE : Color{ 60, 60, 80, 160 } );
    }
}

void App::drawToasts()
{
    // Awards slide in at the top, one after the other.
    float y = 34;
    for ( const Toast &t : m_toasts )
    {
        float a = std::clamp( std::min( t.m_t, 3.5f - t.m_t ) * 4, 0.0f, 1.0f );
        int   w = assets().font().width( t.m_text ) + 40;
        int   x = ( m_screen.m_w - w ) / 2;
        DrawRectangle( x, (int)y, w, 20, ColorAlpha( { 30, 20, 50, 255 }, 0.9f * a ) );
        DrawRectangleLines( x, (int)y, w, 20, ColorAlpha( { 255, 210, 90, 255 }, a ) );
        const Sheet &hud = assets().sheetIn( "ui", "hud" );
        if ( !hud.m_standIn ) hud.draw( hud.frame( "star", 0 ), x + 12.0f, y + 10, false, ColorAlpha( WHITE, a ) );
        assets().font().draw( t.m_text, x + 26.0f, y + 5, ColorAlpha( { 255, 235, 180, 255 }, a ) );
        y += 24;
    }
}

void App::drawRadio()
{
    // The bridge: the Commodore's portrait, her words appearing as if typed.
    m_screen.clear( WHITE );
    m_screen.begin( LayerE::BACKGROUND );
    drawBackdrop( "hull_a", (float)GetTime() );
    m_screen.end();
    m_screen.begin( LayerE::HUD );
    float            cx = m_screen.m_w * 0.5f;
    int              ep, st;
    parseId( m_pendingId, ep, st );
    std::string      title = hasText( "level." + m_pendingId ) ? tr( "level." + m_pendingId ) : m_pendingId;
    drawText( title, cx, 30, { 200, 235, 255, 255 }, true, true );
    drawPanel( 40, 80, m_screen.m_w - 80, 170 );
    std::string      text = glyphs( tr( "radio." + m_pendingId ), padInUse() );
    size_t           shown = std::min( text.size(), (size_t)( m_radioT * 45 ) );
    // Her mouth moves while she speaks (or, without a voice, while the text types).
    bool             talking = ( m_radioVoice ? voicePlaying() : shown < text.size() ) && (int)( m_radioT * 8 ) % 2 == 0;
    const Texture2D *face = assets().texture( talking ? "ui/portrait_commodore_talk.png" : "ui/portrait_commodore.png" );
    if ( !face ) face = assets().texture( "ui/portrait_commodore.png" );
    if ( face ) DrawTexturePro( *face, { 0, 0, (float)face->width, (float)face->height }, { 56, 96, 96, 96 }, { 0, 0 }, 0, WHITE );
    else
        DrawRectangle( 56, 96, 96, 96, { 40, 50, 90, 255 } );
    DrawRectangleLines( 55, 95, 98, 98, { 90, 190, 255, 255 } );
    drawText( tr( "radio.commodore" ), 104, 198, { 255, 210, 120, 255 }, false, true );
    // Cut the text at a character boundary (UTF-8).
    while ( shown < text.size() && ( (unsigned char)text[shown] & 0xC0 ) == 0x80 ) ++shown;
    float                    y = 100;
    bool                     big = m_settings.m_bigText;
    std::vector<std::string> lines = wrapText( text.substr( 0, shown ), m_screen.m_w - 230, big );
    if ( big && wrapText( text, m_screen.m_w - 230, true ).size() * ( assets().font( true, true ).height() + 2 ) > 140 )
        big = false, lines = wrapText( text.substr( 0, shown ), m_screen.m_w - 230 );
    for ( const std::string &l : lines )
        drawText( l, 170, y, { 225, 235, 255, 255 }, big ), y += big ? assets().font( true, true ).height() + 2 : 15;
    if ( shown >= text.size() && (int)( m_t * 2 ) % 2 == 0 ) drawText( tr( "menu.press_on" ), cx, 270, { 200, 210, 230, 255 }, false, true );
    drawToasts();
    m_screen.end();
}

void App::drawExtras( StateE state )
{
    float cx = m_screen.m_w * 0.5f;
    switch ( state )
    {
    case StateE::EXTRAS:
    {
        bool bosses = true;
        for ( int e = 1; e <= 4; ++e ) bosses &= m_progress.m_best.count( levelId( e, 9 ) ) && m_progress.m_best.at( levelId( e, 9 ) ).m_done;
        std::vector<bool> on = { true, true, true, bosses, true, true };
        std::string       rush = tr( "extras.rush" );
        bool              made = FileExists( ( userDir() + "levels/custom" + std::to_string( m_editorSlot ) + ".txt" ).c_str() );
        std::string       editorSlot = "  < " + tr( "extras.slot" ) + " " + std::to_string( m_editorSlot ) + ( made ? "" : " (" + tr( "extras.slot_new" ) + ")" ) + " >";
        if ( m_progress.m_bossRush > 0 ) rush += "  (" + fmtTime( m_progress.m_bossRush ) + ")";
        int got = 0;
        for ( int a = 0; a < AW_COUNT; ++a ) got += m_progress.award( (AwardE)a );
        on.insert( on.begin() + 3, true );
        drawMenu( tr( "menu.extras" ),
                  { tr( "extras.logbook" ) + "  (" + std::to_string( m_progress.m_lore.size() ) + ")",
                    tr( "extras.awards" ) + "  (" + std::to_string( got ) + "/" + std::to_string( (int)AW_COUNT ) + ")",
                    tr( "extras.scores" ), tr( "extras.challenges" ), rush, tr( "menu.editor" ) + editorSlot,
                    tr( "menu.back" ) },
                  m_screen.m_h / 2 - 56, &on );
        break;
    }
    case StateE::LOGBOOK:
    {
        // Two pages: the logbook's and the bestiary's, left and right between them.
        std::string tab = m_logTab ? tr( "extras.bestiary" ) + "  (" + std::to_string( m_progress.m_seen.size() ) +
                                         "/" + std::to_string( bestiaryIds().size() ) + ")"
                                   : tr( "extras.logbook" );
        drawText( "< " + tab + " >", cx, 14, { 200, 235, 255, 255 }, true, true );
        if ( m_logTab )
        {
            drawBestiary();
            break;
        }
        std::vector<std::string> keys = textKeys( "lore.", ".title" );
        drawPanel( 20, 50, 220, m_screen.m_h - 70 );
        drawPanel( 250, 50, m_screen.m_w - 270, m_screen.m_h - 70 );
        int rows = ( m_screen.m_h - 90 ) / 14;
        if ( m_cursor < m_listTop ) m_listTop = m_cursor;
        if ( m_cursor >= m_listTop + rows ) m_listTop = m_cursor - rows + 1;
        for ( int i = m_listTop; i < (int)keys.size() && i < m_listTop + rows; ++i )
        {
            std::string key = keys[i].substr( 5, keys[i].size() - 5 - 6 );
            bool        found = m_progress.m_lore.count( key ) > 0, sel = i == m_cursor;
            std::string t = found ? tr( keys[i] ) : "? ? ?";
            while ( assets().font().width( t ) > 196 && t.size() > 4 ) t = t.substr( 0, t.size() - 4 ) + "...";
            drawText( t, 32, 60.0f + ( i - m_listTop ) * 14, sel ? Color{ 255, 230, 120, 255 } : found ? Color{ 210, 220, 240, 255 } : Color{ 100, 105, 125, 255 } );
        }
        if ( m_cursor < (int)keys.size() )
        {
            std::string key = keys[m_cursor].substr( 5, keys[m_cursor].size() - 5 - 6 );
            if ( m_progress.m_lore.count( key ) )
            {
                drawText( tr( keys[m_cursor] ), 264, 62, { 255, 210, 120, 255 } );
                float y = 84;
                for ( const std::string &l : wrapText( tr( "lore." + key + ".text" ), m_screen.m_w - 300 ) )
                    drawText( l, 264, y, { 220, 230, 250, 255 } ), y += 14;
            }
            else
                drawText( tr( "extras.not_found" ), 264, 62, { 140, 150, 180, 255 } );
        }
        break;
    }
    case StateE::AWARDS:
    {
        drawText( tr( "extras.awards" ), cx, 14, { 200, 235, 255, 255 }, true, true );
        drawPanel( 30, 50, m_screen.m_w - 60, m_screen.m_h - 70 );
        int rows = ( m_screen.m_h - 90 ) / 22;
        if ( m_cursor < m_listTop ) m_listTop = m_cursor;
        if ( m_cursor >= m_listTop + rows ) m_listTop = m_cursor - rows + 1;
        const Sheet &hud = assets().sheetIn( "ui", "hud" );
        for ( int i = m_listTop; i < AW_COUNT && i < m_listTop + rows; ++i )
        {
            bool  got = m_progress.award( (AwardE)i ), sel = i == m_cursor;
            float y = 58.0f + ( i - m_listTop ) * 22;
            if ( !hud.m_standIn ) hud.draw( hud.frame( got ? "star" : "skull", 0 ), 52, y + 8, false, got ? WHITE : Color{ 70, 70, 90, 255 } );
            drawText( tr( awardKey( (AwardE)i ) ), 70, y, sel ? Color{ 255, 230, 120, 255 } : got ? Color{ 230, 235, 250, 255 } : Color{ 120, 125, 145, 255 } );
            drawText( tr( std::string( awardKey( (AwardE)i ) ) + ".about" ), 70, y + 10, { 140, 170, 210, 255 } );
        }
        break;
    }
    case StateE::SCORES:
    {
        drawText( tr( "extras.scores" ), cx, 14, { 200, 235, 255, 255 }, true, true );
        drawText( "< " + tr( "diff." + std::to_string( m_scoreDiff ) ) + " >", cx, 48, { 255, 220, 140, 255 }, false, true );
        drawPanel( (int)cx - 200, 66, 400, 10 * 20 + 16 );
        int row = 0;
        for ( const ScoreLine &l : readScores() )
        {
            if ( l.m_difficulty != m_scoreDiff || row >= 10 ) continue;
            float y = 76.0f + row * 20;
            drawText( std::to_string( row + 1 ) + ".", cx - 184, y, { 200, 210, 230, 255 } );
            drawText( std::to_string( l.m_score ), cx - 150, y, { 255, 230, 140, 255 } );
            drawText( tr( "episode." + std::to_string( l.m_episode ) ) + ( l.m_cycle ? "  +" + std::to_string( l.m_cycle ) : "" ), cx - 60, y, { 210, 220, 240, 255 } );
            drawText( l.m_date, cx + 110, y, { 150, 170, 200, 255 } );
            ++row;
        }
        if ( !row ) drawText( tr( "extras.no_scores" ), cx, 120, { 150, 160, 190, 255 }, false, true );
        break;
    }
    default: break;
    }
}

}   // namespace kepler
