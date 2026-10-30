/**
 * @file App.cpp
 * @brief The game around the levels: title, menus, episodes, the Quartermaster, the tally, story, options, pause.
 * @author Rene Weller
 */
#include "AppImpl.h"

#include "Assets.h"
#include "Audio.h"
#include "Bot.h"
#include "Editor.h"
#include "Input.h"
#include "Rumble.h"
#include "Save.h"
#include "Screen.h"
#include "Text.h"
#include "World.h"

#include <raylib.h>

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <memory>
#include <vector>

namespace kepler
{

// ----------------------------------------------------------------------------------------------------- startup

void App::openWindow()
{
    bool deck = getenv( "SteamDeck" ) && atoi( getenv( "SteamDeck" ) ) == 1;
    bool shot = !m_o.m_shot.empty() || !m_o.m_autotest.empty();
    unsigned flags = FLAG_WINDOW_RESIZABLE | ( m_settings.m_vsync && !shot ? FLAG_VSYNC_HINT : 0 ) | ( shot ? FLAG_WINDOW_HIDDEN : 0 );
    SetConfigFlags( flags );
    int w = m_o.m_w ? m_o.m_w : 1280, h = m_o.m_h ? m_o.m_h : 720;
    SetTraceLogLevel( LOG_WARNING );
    InitWindow( w, h, "KIP KEPLER" );
    SetExitKey( 0 );
    if ( !shot && !m_o.m_w )
    {
        int mon = GetCurrentMonitor(), mw = GetMonitorWidth( mon ), mh = GetMonitorHeight( mon );
        if ( deck ) w = 1280, h = 800;
        else
        {
            int s = std::max( 1, std::min( (int)( mw * 0.85f ) / 640, (int)( mh * 0.85f ) / 360 ) );
            w = 640 * s, h = 360 * s;
        }
        SetWindowSize( w, h );
        SetWindowPosition( std::max( 0, ( mw - w ) / 2 ), std::max( 0, ( mh - h ) / 2 ) );
        if ( ( m_settings.m_fullscreen || deck ) && !m_o.m_windowed ) ToggleBorderlessWindowed();
    }
    if ( !m_settings.m_vsync ) SetTargetFPS( 144 );
    SetTargetFPS( std::max( 60, GetMonitorRefreshRate( GetCurrentMonitor() ) ) );
    HideCursor();
    m_screen.init();
}

int App::run()
{
    loadSettings( m_settings );
    openWindow();
    audioInit( m_o.m_mute || !m_o.m_shot.empty() || !m_o.m_autotest.empty() );
    applyVolumes();
    setLanguage( !m_o.m_lang.empty() ? m_o.m_lang : !m_settings.m_lang.empty() && m_settings.m_lang != "-" ? m_settings.m_lang : systemLanguage() );
    m_hasSave = loadProgress( m_settings.m_slot, m_progress );
    if ( m_o.m_shot.empty() && m_o.m_autotest.empty() ) applyAssist();
    if ( m_o.m_difficulty >= 0 ) m_progress.m_difficulty = m_o.m_difficulty;

    if ( !m_o.m_autotest.empty() ) return autotest();
    if ( !m_o.m_editor.empty() ) openEditor( m_o.m_editor );

    // Test pictures.
    if ( !m_o.m_shot.empty() )
    {
        if ( m_o.m_allWeapons )
        {
            m_progress.m_weapons = ( 1u << WeaponCount ) - 1;
            for ( int k = 1; k < WeaponCount; ++k ) m_progress.m_ammo[k] = m_progress.ammoMax( (WeaponE)k );
        }
        bool ok = true;
        if ( !m_o.m_editor.empty() )
        {
            for ( int i = 0; i < 30; ++i ) update( 1.0f / 30 );
        }
        else if ( !m_o.m_menuShot.empty() )
        {
            static const std::pair<const char *, StateE> names[] = {
                { "title", StateE::TITLE }, { "main", StateE::MAIN }, { "episodes", StateE::EPISODES }, { "levels", StateE::LEVELS },
                { "shop", StateE::SHOP }, { "options", StateE::OPTIONS }, { "difficulty", StateE::DIFFICULTY },
                { "extras", StateE::EXTRAS }, { "awards", StateE::AWARDS }, { "logbook", StateE::LOGBOOK } };
            for ( auto &[n, s] : names )
                if ( m_o.m_menuShot == n ) m_state = s;
            if ( m_o.m_menuShot == "radio" ) m_pendingId = "e1l2", m_radioT = 10, m_state = StateE::RADIO;
            if ( m_o.m_menuShot == "story" ) showStory( "story.e1.intro", StateE::MAIN );
            if ( m_o.m_menuShot == "tally" || m_o.m_menuShot == "pause" )
            {
                ok = startLevel( m_o.m_episode ? m_o.m_episode : 1, m_o.m_stage ? m_o.m_stage : 1 );
                if ( ok && m_o.m_menuShot == "tally" ) finishLevel();
                if ( ok && m_o.m_menuShot == "pause" ) m_state = StateE::PAUSE;
            }
            for ( int i = 0; i < 30; ++i ) update( 1.0f / 30 );
        }
        else
        {
            if ( !m_o.m_level.empty() )
            {
                m_world = std::make_unique<World>();
                m_world->setView( m_screen.m_w, m_screen.m_h );
                std::string error;
                ok = m_world->load( m_o.m_level, m_progress, error );
                if ( !ok ) TraceLog( LOG_ERROR, "%s", error.c_str() );
                m_state = StateE::PLAY;
            }
            else
                ok = startLevel( m_o.m_episode ? m_o.m_episode : 1, m_o.m_stage ? m_o.m_stage : 1 );
            if ( ok )
            {
                if ( m_o.m_at ) m_world->place( m_o.m_atX * Tile + Tile * 0.5f, ( m_o.m_atY + 1 ) * Tile );
                if ( !m_o.m_weapon.empty() && weaponOf( m_o.m_weapon ) != WeaponE::COUNT ) m_world->m_weapon = weaponOf( m_o.m_weapon );
                Controls c;
                c.m_right = m_o.m_hold.find( 'r' ) != std::string::npos;
                c.m_left = m_o.m_hold.find( 'l' ) != std::string::npos;
                c.m_jump = m_o.m_hold.find( 'j' ) != std::string::npos;
                c.m_fire = m_o.m_hold.find( 'f' ) != std::string::npos;
                c.m_up = m_o.m_hold.find( 'u' ) != std::string::npos;
                int steps = (int)( m_o.m_warm * 60 );
                for ( int i = 0; i < steps; ++i )
                {
                    Controls k = c;
                    k.m_jumpPressed = c.m_jump && i % 50 == 0;
                    k.m_firePressed = c.m_fire && i % 12 == 0;
                    m_world->update( 1.0f / 60, k );
                }
            }
        }
        if ( ok )
        {
            BeginDrawing();
            draw();
            EndDrawing();
            Image img = m_screen.capture();
            ImageResizeNN( &img, img.width * 2, img.height * 2 );
            ExportImage( img, m_o.m_shot.c_str() );
            UnloadImage( img );
        }
        assets().unload();
        m_screen.unload();
        CloseWindow();
        return ok ? 0 : 1;
    }

    if ( !m_o.m_level.empty() || m_o.m_episode )
    {
        if ( !m_o.m_level.empty() )
        {
            m_world = std::make_unique<World>();
            m_world->setView( m_screen.m_w, m_screen.m_h );
            std::string error;
            if ( m_world->load( m_o.m_level, m_progress, error ) )
            {
                m_state = StateE::PLAY, m_directLevel = true;
                if ( m_o.m_autoplay ) m_bot = std::make_unique<Bot>(), m_bot->start( *m_world );
            }
            else
                m_message = error, m_messageT = 5;
        }
        else
            startLevel( m_o.m_episode, std::max( 1, m_o.m_stage ) );
    }
    if ( m_state == StateE::TITLE ) music( "title" );

    while ( !WindowShouldClose() && !m_quit )
    {
        float dt = std::min( GetFrameTime(), 0.1f );
        if ( IsWindowResized() ) m_screen.resize();
        if ( IsKeyPressed( KEY_F11 ) || ( IsKeyPressed( KEY_ENTER ) && ( IsKeyDown( KEY_LEFT_ALT ) || IsKeyDown( KEY_RIGHT_ALT ) ) ) )
        {
            ToggleBorderlessWindowed();
            m_settings.m_fullscreen = !m_settings.m_fullscreen;
            saveSettings( m_settings );
            m_screen.resize();
        }
        update( dt );
        // The level's ambience bed plays while the level does (and under the pause menu).
        bool playing = m_world && ( m_state == StateE::PLAY || m_state == StateE::PAUSE );
        ambience( playing ? m_world->m_level.key( "theme", "" ) : "" );
        audioUpdate( dt );
        BeginDrawing();
        draw();
        EndDrawing();
    }
    if ( m_state == StateE::PLAY || m_state == StateE::PAUSE ) m_progress.m_playTime += 0;
    audioClose();
    assets().unload();
    m_screen.unload();
    CloseWindow();
    return 0;
}

// ----------------------------------------------------------------------------------------------------- editor

void App::openEditor( const std::string &path )
{
    if ( !m_editor ) m_editor = std::make_unique<Editor>();
    if ( !m_editor->open( path ) )
    {
        m_message = tr( "editor.cannot_open" ) + " " + path;
        m_messageT = 3;
        return;
    }
    music( "shop" );
    go( StateE::EDITOR );
}

void App::playEditorLevel()
{
    auto        world = std::make_unique<World>();
    std::string error;
    world->setView( m_screen.m_w, m_screen.m_h );
    if ( !world->load( m_editor->path(), m_progress, error ) )
    {
        m_message = error;
        m_messageT = 4;
        return;
    }
    m_world = std::move( world );
    m_fromEditor = true;
    m_directLevel = true;
    go( StateE::PLAY );
}

// --------------------------------------------------------------------------------------------------- autotest

int App::autotest()
{
    // Which levels: one file, one stage, one episode or all of them; the hero carries his progress through them.
    std::vector<std::pair<std::string, std::string>> levels;   // path, id
    if ( !m_o.m_level.empty() ) levels.push_back( { m_o.m_level, "" } );
    else
        for ( int e = m_o.m_episode ? m_o.m_episode : 1; e <= ( m_o.m_episode ? m_o.m_episode : 4 ); ++e )
            for ( int l = m_o.m_stage ? m_o.m_stage : 1; l <= ( m_o.m_stage ? m_o.m_stage : 9 ); ++l )
                levels.push_back( { assetDir() + "levels/" + levelId( e, l ) + ".txt", levelId( e, l ) } );
    FILE *out = fopen( m_o.m_autotest.c_str(), "a" );
    if ( !out ) return 1;
    m_progress = Progress();
    m_progress.m_difficulty = m_o.m_difficulty >= 0 ? m_o.m_difficulty : 1;
    int failures = 0;
    for ( auto &[path, id] : levels )
    {
        if ( !FileExists( path.c_str() ) ) continue;
        if ( !id.empty() ) grantEpisodeWeapons( id[1] - '0' );
        if ( m_o.m_allWeapons )
        {
            m_progress.m_weapons = ( 1u << WeaponCount ) - 1;
            for ( int k = 1; k < WeaponCount; ++k ) m_progress.m_ammo[k] = m_progress.ammoMax( (WeaponE)k );
        }
        World       w;
        std::string error;
        w.setView( 640, 360 );
        if ( !w.load( path, m_progress, error ) )
        {
            fprintf( out, "%s load-error %s\n", id.c_str(), error.c_str() );
            ++failures;
            continue;
        }
        Bot bot;
        bot.start( w );
        if ( getenv( "KEPLER_TRACE" ) ) bot.m_trace = fopen( ( std::string( getenv( "KEPLER_TRACE" ) ) + w.m_level.m_id + ".txt" ).c_str(), "w" );
        double wall = GetTime();
        while ( !w.m_finished && w.m_time < m_o.m_limit )
        {
            Controls c = bot.think( w );
            w.update( phys::Step, c );
        }
        if ( w.m_finished ) m_progress.m_credits += w.m_credits, m_progress.m_score += w.m_score;
        else
            ++failures;
        fprintf( out, "%s finished=%d time=%.1f deaths=%d crystals=%d/%d treasure=%d/%d secrets=%d/%d kills=%d/%d stalls=%d(lost %d noway %d) hp=%.0f wall=%.1fs %s\n",
                 w.m_level.m_id.c_str(), w.m_finished ? 1 : 0, w.m_time, w.m_deaths, w.m_crystalsTaken, w.m_crystals, w.m_treasureTaken,
                 w.m_treasure, w.m_secretsFound, w.m_secrets, w.m_kills, w.m_enemiesTotal, bot.m_stalls, bot.m_lost, bot.m_noWay, w.m_hp, GetTime() - wall,
                 ( bot.m_stallLog + ( w.m_finished ? "" : " last: " + bot.m_status ) ).c_str() );
        fflush( out );
        if ( bot.m_trace ) fclose( bot.m_trace );
    }
    fclose( out );
    assets().unload();
    m_screen.unload();
    CloseWindow();
    return failures ? 1 : 0;
}

// ------------------------------------------------------------------------------------------------------- flow

void App::go( StateE s, int cursor )
{
    if ( s != StateE::PLAY ) rumble::stop();
    m_state = s;
    m_cursor = cursor;
    m_t = 0;
    // The menus' music; levels choose their own when they load.
    switch ( s )
    {
    case StateE::TITLE:
    case StateE::MAIN:
    case StateE::EPISODES:
    case StateE::LEVELS:
    case StateE::DIFFICULTY: music( "title" ); break;
    case StateE::SHOP: music( "shop" ); break;
    case StateE::STORY: music( m_afterStory == StateE::MAIN && m_episode == 4 ? "ending" : "story" ); break;
    case StateE::TALLY: music( "tally", false ); break;
    default: break;
    }
}

void App::grantEpisodeWeapons( int episode )
{
    // Starting a later episode, Kip has what the earlier ones gave him.
    static const WeaponE got[5][2] = { {}, {}, { WeaponE::REPEATER, WeaponE::SCATTER }, { WeaponE::RICOCHET, WeaponE::CRYO }, { WeaponE::LANCER, WeaponE::MORTAR } };
    for ( int e = 2; e <= episode; ++e )
        for ( WeaponE w : got[e] )
            if ( !m_progress.has( w ) )
            {
                m_progress.m_weapons |= 1u << (int)w;
                m_progress.m_ammo[(int)w] = m_progress.ammoMax( w );
            }
}

bool App::startLevel( int episode, int stage )
{
    return startLevelId( levelId( episode, stage ) );
}

void App::finishLevel()
{
    World &w = *m_world;
    m_tally.clear();
    Color plain = { 220, 230, 255, 255 }, good = { 140, 255, 180, 255 }, gold = { 255, 220, 100, 255 };
    int   score = w.m_score, credits = w.m_credits;
    auto  pct = []( int a, int b ) { return b ? a * 100 / b : 100; };
    m_tally.push_back( { tr( "tally.crystals" ), std::to_string( w.m_crystalsTaken ) + "/" + std::to_string( w.m_crystals ), plain } );
    m_tally.push_back( { tr( "tally.treasure" ), std::to_string( w.m_treasureTaken ) + "/" + std::to_string( w.m_treasure ) + "  (" + std::to_string( pct( w.m_treasureTaken, w.m_treasure ) ) + "%)", plain } );
    m_tally.push_back( { tr( "tally.secrets" ), std::to_string( w.m_secretsFound ) + "/" + std::to_string( w.m_secrets ), plain } );
    m_tally.push_back( { tr( "tally.kills" ), std::to_string( w.m_kills ) + "/" + std::to_string( w.m_enemiesTotal ), plain } );
    int par = (int)w.m_level.num( "par", 0 );
    m_tally.push_back( { tr( "tally.time" ), fmtTime( w.m_time ) + ( par ? "  (" + tr( "tally.par" ) + " " + fmtTime( (float)par ) + ")" : "" ), plain } );
    m_tally.push_back( { tr( "tally.deaths" ), std::to_string( w.m_deaths ), plain } );
    auto bonus = [&]( const std::string &key, int points, int cr )
    {
        score += points, credits += cr;
        m_tally.push_back( { tr( key ), "+" + std::to_string( points ) + "  +" + std::to_string( cr ) + " " + tr( "tally.cr" ), good } );
    };
    if ( w.m_treasure && w.m_treasureTaken == w.m_treasure ) bonus( "tally.bonus_treasure", 2000, 300 );
    if ( w.m_secrets && w.m_secretsFound == w.m_secrets ) bonus( "tally.bonus_secrets", 1500, 250 );
    if ( w.m_enemiesTotal && w.m_kills * 10 >= w.m_enemiesTotal * 9 ) bonus( "tally.bonus_kills", 1000, 150 );
    if ( par && w.m_time <= par ) bonus( "tally.bonus_time", 1000, 150 );
    if ( w.m_deaths == 0 ) bonus( "tally.bonus_deaths", 1000, 150 );
    int medals = 0;
    nextAfterLevel( w, medals );
    if ( m_trial ) score = credits = 0;
    m_tally.push_back( { tr( "tally.score" ), std::to_string( score ), gold } );
    m_tally.push_back( { tr( "tally.credits" ), "+" + std::to_string( credits ), gold } );
    if ( m_demo || m_trial || m_rush ) score = 0, credits = 0;

    m_progress.m_score += score;
    m_progress.m_credits += credits;
    m_progress.m_playTime += w.m_time;
    std::string id = w.m_level.m_id;
    LevelBest  &b = m_progress.m_best[m_demo || m_fromEditor ? std::string( "demo" ) : id];
    b.m_done = true;
    b.m_score = std::max( b.m_score, score );
    b.m_time = b.m_time > 0 ? std::min( b.m_time, w.m_time ) : w.m_time;
    b.m_treasure = std::max( b.m_treasure, pct( w.m_treasureTaken, w.m_treasure ) );
    b.m_secrets = std::max( b.m_secrets, w.m_secretsFound );
    b.m_secretsMax = w.m_secrets;
    b.m_kills = std::max( b.m_kills, pct( w.m_kills, w.m_enemiesTotal ) );
    b.m_medals |= medals;
    m_progress.m_creditsTotal += credits;
    checkAwards();
    if ( !m_directLevel && !m_demo && !m_trial && !m_rush && !m_nextId.empty() && m_nextId.find( 's' ) == std::string::npos )
    {
        m_progress.m_episode = m_nextId[1] - '0';
        m_progress.m_level = atoi( m_nextId.c_str() + 3 );
    }
    if ( !m_demo && ( !m_directLevel || m_trial || m_rush ) )
    {
        saveProgress( m_settings.m_slot, m_progress );
        m_hasSave = true;
    }
    go( StateE::TALLY );
}

void App::showStory( const std::string &prefix, StateE after )
{
    m_pages.clear();
    for ( int i = 1; i < 12; ++i )
    {
        std::string k = prefix + "." + std::to_string( i );
        if ( !hasText( k ) ) break;
        m_pages.push_back( tr( k ) );
    }
    m_page = 0;
    m_afterStory = after;
    if ( m_pages.empty() )
    {
        go( after );
        return;
    }
    m_storyPrefix = prefix;
    int ep = prefix.size() > 7 && prefix[7] >= '1' && prefix[7] <= '4' ? prefix[7] - '0' : m_episode;
    m_storyBg = EpisodeBg[std::clamp( ep, 1, 4 )];
    go( StateE::STORY );
}

std::vector<std::string> App::mainItems() const
{
    std::vector<std::string> items;
    if ( m_hasSave ) items.push_back( tr( "menu.continue" ) );
    items.push_back( tr( "menu.new" ) );
    if ( m_progress.m_finished ) items.push_back( tr( "menu.new_plus" ) );
    items.push_back( tr( "menu.episodes" ) );
    items.push_back( tr( "menu.extras" ) );
    items.push_back( tr( "menu.options" ) );
    items.push_back( tr( "menu.quit" ) );
    return items;
}

// ----------------------------------------------------------------------------------------------------- update

void App::update( float dt )
{
    m_t += dt;
    if ( m_messageT > 0 ) m_messageT -= dt;
    for ( Toast &t : m_toasts ) t.m_t -= dt;
    while ( !m_toasts.empty() && m_toasts.front().m_t <= 0 ) m_toasts.erase( m_toasts.begin() );
    if ( m_state == StateE::PLAY )
    {
        Controls c = readControls();
        if ( c.m_pause )
        {
            sfx( "menu_ok", 0.6f );
            go( StateE::PAUSE );
            return;
        }
        if ( m_demo && ( GetKeyPressed() || GetGamepadButtonPressed() > 0 || m_world->m_time > 75 ) )
        {
            m_demo = false;
            m_bot.reset();
            m_directLevel = false;
            go( StateE::TITLE );
            return;
        }
        static const float speeds[4] = { 1.0f, 0.9f, 0.8f, 0.7f };
        float              play = dt * ( m_demo ? 1.0f : speeds[std::clamp( m_settings.m_speed, 0, 3 )] );
        m_world->m_assistInvulnerable = m_settings.m_invulnerable && !m_demo;
        m_world->m_assistAmmo = m_settings.m_infiniteAmmo && !m_demo;
        m_world->m_rumbleOn = m_settings.m_rumble && !m_demo;
        if ( m_bot )
        {
            int n = std::max( 1, (int)std::lround( dt / phys::Step ) );
            for ( int i = 0; i < n && !m_world->m_finished; ++i ) m_world->update( phys::Step, m_bot->think( *m_world ) );
        }
        else
            m_world->update( play, c );
        for ( int a : m_world->m_awardQueue ) m_toasts.push_back( { tr( "msg.award" ) + " " + tr( awardKey( (AwardE)a ) ), 3.5f } );
        m_world->m_awardQueue.clear();
        if ( m_world->m_restart )
        {
            m_world->m_restart = false;
        }
        if ( m_world->m_finished ) finishLevel();
        return;
    }
    if ( m_state == StateE::EDITOR )
    {
        Editor::ResultE r = m_editor->update( dt );
        if ( r == Editor::ResultE::LEAVE ) go( StateE::MAIN );
        if ( r == Editor::ResultE::PLAY ) playEditorLevel();
        return;
    }
    MenuKeys k = readMenu( dt );
    auto     moveCursor = [&]( int n )
    {
        if ( n <= 0 ) return;
        if ( k.m_up ) m_cursor = ( m_cursor + n - 1 ) % n, sfx( "menu_move", 0.5f );
        if ( k.m_down ) m_cursor = ( m_cursor + 1 ) % n, sfx( "menu_move", 0.5f );
    };
    if ( k.m_ok ) sfx( "menu_ok", 0.6f );
    if ( k.m_back ) sfx( "menu_back", 0.6f );

    switch ( m_state )
    {
    case StateE::TITLE:
        if ( k.m_ok || ( m_t > 0.5f && GetKeyPressed() ) ) go( StateE::MAIN );
        else if ( m_t > 25 )
            startDemo();
        break;

    case StateE::MAIN:
    {
        std::vector<std::string> items = mainItems();
        moveCursor( (int)items.size() );
        if ( k.m_back ) go( StateE::TITLE );
        if ( !k.m_ok ) break;
        int i = m_cursor - ( m_hasSave ? 1 : 0 );
        // Without New Game+ the rows after "new game" move up by one.
        if ( i >= 1 && !m_progress.m_finished ) ++i;
        if ( i < 0 )
        {
            if ( !startLevel( m_progress.m_episode, m_progress.m_level ) ) {}
        }
        else if ( i == 0 )
            go( StateE::DIFFICULTY, 1 );
        else if ( i == 1 )
        {
            // New Game+: everything stays, the Spiral fights back harder.
            ++m_progress.m_cycle;
            m_progress.m_episode = 1, m_progress.m_level = 1;
            m_progress.m_episodeDeaths = 0;
            grantApp( AW_NEW_GAME_PLUS );
            saveProgress( m_settings.m_slot, m_progress );
            m_episode = 1, m_stage = 1;
            showStory( "story.e1.intro", StateE::PLAY );
        }
        else if ( i == 2 )
            go( StateE::EPISODES, std::clamp( m_progress.m_episode - 1, 0, 3 ) );
        else if ( i == 3 )
            go( StateE::EXTRAS );
        else if ( i == 4 )
            m_back = StateE::MAIN, go( StateE::OPTIONS );
        else
            m_quit = true;
        break;
    }

    case StateE::DIFFICULTY:
        moveCursor( 3 );
        if ( k.m_back ) go( StateE::MAIN );
        if ( k.m_ok )
        {
            if ( m_hasSave && m_confirmAction == 0 )
            {
                m_confirm = tr( "menu.overwrite" );
                m_confirmAction = 1 + m_cursor;
                go( StateE::CONFIRM, 1 );
                break;
            }
            int diff = m_confirmAction ? m_confirmAction - 1 : m_cursor;
            m_confirmAction = 0;
            m_progress = Progress();
            m_progress.m_difficulty = diff;
            saveProgress( m_settings.m_slot, m_progress );
            m_hasSave = true;
            m_episode = 1, m_stage = 1;
            showStory( "story.e1.intro", StateE::PLAY );
        }
        break;

    case StateE::CONFIRM:
        moveCursor( 2 );
        if ( k.m_back ) m_confirmAction = 0, go( StateE::MAIN );
        if ( k.m_ok )
        {
            if ( m_cursor == 0 )
            {
                m_state = StateE::DIFFICULTY;
                m_cursor = m_confirmAction - 1;
                // Run the difficulty choice again with the confirmation given.
                int diff = m_confirmAction - 1;
                m_confirmAction = 0;
                m_progress = Progress();
                m_progress.m_difficulty = diff;
                saveProgress( m_settings.m_slot, m_progress );
                m_hasSave = true;
                m_episode = 1, m_stage = 1;
                showStory( "story.e1.intro", StateE::PLAY );
            }
            else
                m_confirmAction = 0, go( StateE::MAIN );
        }
        break;

    case StateE::EPISODES:
        moveCursor( 4 );
        if ( k.m_left ) m_cursor = ( m_cursor + 3 ) % 4;
        if ( k.m_right ) m_cursor = ( m_cursor + 1 ) % 4;
        if ( k.m_back ) go( StateE::MAIN );
        if ( k.m_ok )
        {
            m_pickEpisode = m_cursor + 1;
            int first = 0;
            for ( int l = 1; l <= 9; ++l )
                if ( m_progress.unlocked( m_pickEpisode, l ) ) first = l - 1;
            go( StateE::LEVELS, first );
        }
        break;

    case StateE::LEVELS:
    {
        std::string secret = "e" + std::to_string( m_pickEpisode ) + "s";
        bool        hasSecret = m_progress.m_best.count( secret ) > 0;
        moveCursor( hasSecret ? 10 : 9 );
        if ( k.m_back ) go( StateE::EPISODES, m_pickEpisode - 1 );
        std::string id = m_cursor == 9 ? secret : levelId( m_pickEpisode, m_cursor + 1 );
        if ( k.m_alt )
        {
            // A time trial of a level already finished.
            if ( m_progress.m_best.count( id ) && m_progress.m_best[id].m_done )
            {
                m_trial = true;
                m_directLevel = true;
                if ( !startLevelId( id, false ) ) m_trial = false;
            }
            else
                m_message = tr( "menu.trial_locked" ), m_messageT = 2;
            break;
        }
        if ( k.m_ok && m_cursor == 9 )
        {
            m_directLevel = true;
            startLevelId( secret, false );
            break;
        }
        if ( k.m_ok )
        {
            if ( !m_progress.unlocked( m_pickEpisode, m_cursor + 1 ) )
            {
                m_message = tr( "menu.locked" );
                m_messageT = 2;
            }
            else if ( m_cursor == 0 && !m_progress.m_best.count( levelId( m_pickEpisode, 1 ) ) )
            {
                m_episode = m_pickEpisode, m_stage = 1;
                showStory( "story.e" + std::to_string( m_pickEpisode ) + ".intro", StateE::PLAY );
            }
            else
                startLevel( m_pickEpisode, m_cursor + 1 );
        }
        break;
    }

    case StateE::PAUSE:
    {
        Controls c = readControls();
        moveCursor( 5 );
        if ( k.m_back || ( c.m_pause && m_t > 0.1f ) ) go( StateE::PLAY );
        if ( k.m_ok )
        {
            if ( m_cursor == 0 ) go( StateE::PLAY );
            else if ( m_cursor == 1 )
            {
                // Back to the last checkpoint (a way out of any spot).
                m_world->giveUp();
                go( StateE::PLAY );
            }
            else if ( m_cursor == 2 )
                loadLevelId( m_world->m_level.m_id );
            else if ( m_cursor == 3 )
                m_back = StateE::PAUSE, go( StateE::OPTIONS );
            else if ( m_fromEditor )
            {
                m_fromEditor = false;
                go( StateE::EDITOR );
            }
            else
            {
                saveProgress( m_settings.m_slot, m_progress );
                music( "title" );
                go( StateE::MAIN );
            }
        }
        break;
    }

    case StateE::TALLY:
        if ( k.m_ok && m_t > 0.4f )
        {
            if ( m_t < 0.35f * m_tally.size() + 0.4f )
            {
                m_t = 99;
                break;
            }
            if ( m_fromEditor )
            {
                m_fromEditor = false;
                go( StateE::EDITOR );
                break;
            }
            if ( m_demo )
            {
                m_demo = false;
                m_bot.reset();
                go( StateE::TITLE );
                break;
            }
            if ( m_trial )
            {
                m_trial = false;
                m_directLevel = false;
                go( StateE::LEVELS, m_stage == 10 ? 9 : m_stage - 1 );
                break;
            }
            if ( m_rush )
            {
                if ( m_nextId.empty() ) m_rush = 0, m_directLevel = false, go( StateE::EXTRAS, 3 );
                else
                    ++m_rush, startLevelId( m_nextId, false );
                break;
            }
            if ( m_directLevel )
            {
                m_quit = !m_o.m_level.empty();
                m_directLevel = false;
                go( StateE::MAIN );
                break;
            }
            if ( m_stage == 9 )
            {
                std::string outro = "story.e" + std::to_string( m_episode ) + ".outro";
                if ( m_episode == 4 ) showStory( outro, StateE::MAIN );
                else
                    showStory( outro, StateE::SHOP );
            }
            else
                go( StateE::SHOP );
        }
        break;

    case StateE::SHOP:
    {
        // Owned weapons' upgrades, armour, ammo, then on.
        std::vector<int> rows;
        for ( int w = 0; w < WeaponCount; ++w )
            if ( m_progress.has( (WeaponE)w ) ) rows.push_back( w );
        rows.push_back( 100 );   // armour
        rows.push_back( 101 );   // ammo
        rows.push_back( 102 );   // on
        moveCursor( (int)rows.size() );
        if ( k.m_back ) m_cursor = (int)rows.size() - 1;
        if ( k.m_ok )
        {
            int r = rows[m_cursor];
            if ( r == 102 )
            {
                saveProgress( m_settings.m_slot, m_progress );
                checkAwards();
                if ( m_nextId.empty() ) go( StateE::MAIN );
                else if ( m_nextId.size() > 3 && m_nextId[2] == 'l' && atoi( m_nextId.c_str() + 3 ) == 1 )
                {
                    // A new episode begins with its story.
                    m_episode = m_nextId[1] - '0';
                    showStory( "story.e" + std::to_string( m_episode ) + ".intro", StateE::PLAY );
                }
                else if ( !startLevelId( m_nextId ) )
                    go( StateE::MAIN );
                break;
            }
            int price = 0, *level = nullptr;
            if ( r < 100 ) level = &m_progress.m_upgrade[r], price = weapon( (WeaponE)r ).m_price * ( *level + 1 );
            else if ( r == 100 )
                level = &m_progress.m_armour, price = 500 * ( *level + 1 );
            else
                price = 150;
            bool full = level && *level >= 3;
            if ( r == 101 )
            {
                full = true;
                for ( int w = 1; w < WeaponCount; ++w )
                    if ( m_progress.has( (WeaponE)w ) && m_progress.m_ammo[w] < m_progress.ammoMax( (WeaponE)w ) ) full = false;
            }
            if ( full ) m_message = tr( "shop.full" ), m_messageT = 1.5f, sfx( "no_ammo", 0.5f );
            else if ( m_progress.m_credits < price )
                m_message = tr( "shop.poor" ), m_messageT = 1.5f, sfx( "no_ammo", 0.5f );
            else
            {
                m_progress.m_credits -= price;
                if ( level ) ++*level;
                if ( r == 101 || ( r < 100 && *level == 2 ) )
                    for ( int w = 1; w < WeaponCount; ++w )
                        if ( m_progress.has( (WeaponE)w ) && ( r == 101 || w == r ) ) m_progress.m_ammo[w] = m_progress.ammoMax( (WeaponE)w );
                sfx( "buy" );
            }
        }
        break;
    }

    case StateE::STORY:
        if ( k.m_ok || k.m_back )
        {
            if ( ++m_page >= (int)m_pages.size() || k.m_back )
            {
                if ( m_afterStory == StateE::PLAY )
                {
                    if ( !startLevel( m_episode, 1 ) ) go( StateE::MAIN );
                }
                else if ( m_afterStory == StateE::SHOP )
                    go( StateE::SHOP );
                else
                {
                    music( "title" );
                    go( m_afterStory );
                }
            }
        }
        break;

    case StateE::OPTIONS:
    {
        moveCursor( 13 );
        int dir = k.m_left ? -1 : k.m_right ? 1 : 0;
        auto vol = [&]( float &v )
        {
            if ( dir ) v = std::clamp( std::round( ( v + dir * 0.1f ) * 10 ) / 10, 0.0f, 1.0f ), applyVolumes(), sfx( "menu_move", 0.6f );
        };
        if ( m_cursor == 0 && ( dir || k.m_ok ) )
        {
            m_settings.m_fullscreen = !m_settings.m_fullscreen;
            ToggleBorderlessWindowed();
            m_screen.resize();
        }
        if ( m_cursor == 1 ) vol( m_settings.m_master );
        if ( m_cursor == 2 ) vol( m_settings.m_music );
        if ( m_cursor == 3 ) vol( m_settings.m_effects );
        if ( m_cursor == 4 && ( dir || k.m_ok ) )
        {
            m_settings.m_lang = language() == "de" ? "en" : "de";
            setLanguage( m_settings.m_lang );
        }
        if ( m_cursor == 5 && ( dir || k.m_ok ) ) m_settings.m_shake = !m_settings.m_shake;
        if ( m_cursor == 6 && ( dir || k.m_ok ) ) m_settings.m_rumble = !m_settings.m_rumble;
        if ( m_cursor == 7 && ( dir || k.m_ok ) )
        {
            m_settings.m_fps = ( m_settings.m_fps + ( dir < 0 ? 4 : 1 ) ) % 5;
            applyAssist();
        }
        if ( m_cursor == 8 && ( dir || k.m_ok ) ) m_settings.m_speed = ( m_settings.m_speed + ( dir < 0 ? 3 : 1 ) ) % 4;
        if ( m_cursor == 9 && ( dir || k.m_ok ) ) m_settings.m_invulnerable = !m_settings.m_invulnerable;
        if ( m_cursor == 10 && ( dir || k.m_ok ) ) m_settings.m_infiniteAmmo = !m_settings.m_infiniteAmmo;
        if ( m_cursor == 11 && k.m_ok ) go( StateE::CONTROLS );
        else if ( k.m_back || ( m_cursor == 12 && k.m_ok ) )
        {
            saveSettings( m_settings );
            applyAssist();
            go( m_back, m_back == StateE::PAUSE ? 3 : 0 );
        }
        break;
    }

    case StateE::CONTROLS:
        if ( k.m_ok || k.m_back ) go( StateE::OPTIONS, 11 );
        break;

    case StateE::RADIO:
    case StateE::EXTRAS:
    case StateE::LOGBOOK:
    case StateE::AWARDS:
    case StateE::SCORES: updateExtras( m_state, k, dt ); break;

    default: break;
    }
}

// ------------------------------------------------------------------------------------------------------- draw

void App::drawBackdrop( const std::string &name, float t )
{
    const Background &bg = assets().background( name );
    drawBackground( bg, m_screen.m_w, m_screen.m_h, t * 40, 0, t, false );
    if ( bg.m_standIn )
        for ( int i = 0; i < 200; ++i )
        {
            float x = std::fmod( i * 97.0f + t * ( 5 + i % 7 * 3 ), (float)m_screen.m_w ), y = std::fmod( i * 53.0f, (float)m_screen.m_h );
            DrawPixel( (int)x, (int)y, i % 9 == 0 ? Color{ 255, 255, 255, 255 } : Color{ 110, 120, 170, 255 } );
        }
}

void App::drawPanel( int x, int y, int w, int h )
{
    const Texture2D *p = assets().texture( "ui/panel.png" );
    if ( p )
    {
        NPatchInfo n = { { 0, 0, (float)p->width, (float)p->height }, 16, 16, 16, 16, NPATCH_NINE_PATCH };
        DrawTextureNPatch( *p, n, { (float)x, (float)y, (float)w, (float)h }, { 0, 0 }, 0, WHITE );
        return;
    }
    DrawRectangle( x, y, w, h, { 12, 16, 38, 225 } );
    DrawRectangleLines( x, y, w, h, { 90, 190, 255, 255 } );
    DrawRectangleLines( x + 2, y + 2, w - 4, h - 4, { 40, 70, 130, 255 } );
}

int App::drawText( const std::string &t, float x, float y, Color c, bool big, bool centre )
{
    const PixelFont &f = assets().font( big, big );
    if ( centre ) x = std::floor( x - f.width( t ) * 0.5f );
    if ( !big ) f.draw( t, x + 1, y + 1, { 8, 6, 18, 255 } );
    return f.draw( t, x, y, c );
}

void App::drawMenu( const std::string &title, const std::vector<std::string> &items, int y, const std::vector<bool> *enabled )
{
    float cx = m_screen.m_w * 0.5f;
    if ( !title.empty() ) drawText( title, cx, (float)y - 34, { 200, 235, 255, 255 }, true, true );
    int w = 0;
    for ( const std::string &s : items ) w = std::max( w, assets().font().width( s ) );
    drawPanel( (int)cx - w / 2 - 28, y - 10, w + 56, (int)items.size() * 18 + 16 );
    for ( size_t i = 0; i < items.size(); ++i )
    {
        bool  sel = (int)i == m_cursor;
        bool  on = !enabled || ( *enabled )[i];
        Color c = !on ? Color{ 110, 110, 130, 255 } : sel ? Color{ 255, 230, 120, 255 } : Color{ 210, 220, 240, 255 };
        drawText( items[i], cx, (float)y + i * 18, c, false, true );
        if ( sel )
        {
            float bounce = std::sin( m_t * 8 ) * 2;
            int   iw = assets().font().width( items[i] );
            drawText( ">", cx - iw / 2 - 14 + bounce, (float)y + i * 18, { 255, 200, 90, 255 } );
        }
    }
}

void App::draw()
{
    if ( m_state == StateE::EDITOR )
    {
        m_editor->draw( m_screen );
        m_screen.present( 0.5f );
        return;
    }
    if ( m_state == StateE::RADIO )
    {
        drawRadio();
        m_screen.present( 0.6f );
        return;
    }
    if ( m_state == StateE::PLAY || m_state == StateE::PAUSE )
    {
        m_world->setView( m_screen.m_w, m_screen.m_h );
        m_world->draw( m_screen );
        m_world->drawHud( m_screen );
        if ( m_state == StateE::PAUSE )
        {
            m_screen.begin( LayerE::HUD );
            DrawRectangle( 0, 0, m_screen.m_w, m_screen.m_h, { 0, 0, 10, 150 } );
            drawMenu( tr( "pause.title" ), { tr( "pause.resume" ), tr( "pause.checkpoint" ), tr( "pause.restart" ), tr( "menu.options" ), tr( "pause.quit" ) },
                      m_screen.m_h / 2 - 30 );
            m_screen.end();
        }
        m_screen.begin( LayerE::HUD );
        drawToasts();
        if ( m_trial )
        {
            std::string t = fmtTime( m_world->m_time ) + "." + std::to_string( (int)( std::fmod( m_world->m_time, 1.0f ) * 10 ) );
            drawText( t, m_screen.m_w * 0.5f, 8, { 255, 230, 140, 255 }, true, true );
        }
        if ( m_demo && (int)( m_t * 2 ) % 2 == 0 ) drawText( tr( "title.demo" ), m_screen.m_w * 0.5f, m_screen.m_h - 20.0f, { 230, 240, 255, 255 }, false, true );
        m_screen.end();
        // Fade in at the start of the level.
        float fade = std::max( 0.0f, 1.0f - m_world->m_time * 2.5f );
        m_screen.present( 0.8f, m_world->m_time < 0.4f ? fade : 0 );
        return;
    }
    // Menus: a backdrop and the HUD layer.
    m_screen.clear( WHITE );
    m_screen.begin( LayerE::BACKGROUND );
    std::string bg = m_state == StateE::STORY ? m_storyBg : m_state == StateE::LEVELS ? EpisodeBg[m_pickEpisode]
                     : m_state == StateE::EPISODES                                    ? EpisodeBg[m_cursor + 1]
                                                                                      : "hull_a";
    drawBackdrop( bg, (float)GetTime() );
    m_screen.end();
    m_screen.begin( LayerE::HUD );
    float cx = m_screen.m_w * 0.5f;
    switch ( m_state )
    {
    case StateE::TITLE:
    case StateE::MAIN:
    {
        const Texture2D *logo = assets().texture( "ui/logo.png" );
        float            ly = m_state == StateE::TITLE ? 70.0f : 34.0f;
        if ( logo ) DrawTexture( *logo, (int)( cx - logo->width / 2 ), (int)ly, WHITE );
        else
            drawText( "KIP KEPLER", cx, ly + 30, { 255, 200, 90, 255 }, true, true );
        if ( m_state == StateE::TITLE )
        {
            if ( (int)( m_t * 2 ) % 2 == 0 ) drawText( tr( padInUse() ? "title.press_pad" : "title.press" ), cx, m_screen.m_h - 90.0f, { 230, 240, 255, 255 }, false, true );
            drawText( tr( "title.sub" ), cx, ly + 120, { 150, 210, 255, 255 }, false, true );
        }
        else
            drawMenu( "", mainItems(), m_screen.m_h / 2 + 10 );
        drawText( "v" KEPLER_VERSION, 6, m_screen.m_h - 14.0f, { 120, 130, 160, 255 } );
        break;
    }
    case StateE::DIFFICULTY:
        drawMenu( tr( "menu.difficulty" ), { tr( "diff.0" ), tr( "diff.1" ), tr( "diff.2" ) }, m_screen.m_h / 2 - 20 );
        drawText( tr( "diff.about." + std::to_string( m_cursor ) ), cx, m_screen.m_h / 2 + 50.0f, { 170, 200, 230, 255 }, false, true );
        break;
    case StateE::CONFIRM:
        drawMenu( m_confirm, { tr( "menu.yes" ), tr( "menu.no" ) }, m_screen.m_h / 2 );
        break;
    case StateE::EPISODES:
    {
        drawText( tr( "menu.episodes" ), cx, 20, { 200, 235, 255, 255 }, true, true );
        int cw = 140, gap = 12, x0 = (int)cx - ( 4 * cw + 3 * gap ) / 2;
        for ( int e = 0; e < 4; ++e )
        {
            int  x = x0 + e * ( cw + gap ), y = 80;
            bool sel = e == m_cursor;
            drawPanel( x - 4, y - 4 - ( sel ? 6 : 0 ), cw + 8, 190 );
            const Texture2D *card = assets().texture( "ui/ep" + std::to_string( e + 1 ) + ".png" );
            if ( card ) DrawTexturePro( *card, { 0, 0, (float)card->width, (float)card->height }, { (float)x, (float)y - ( sel ? 6 : 0 ), (float)cw, (float)cw * card->height / card->width }, { 0, 0 }, 0, WHITE );
            int done = 0;
            for ( int l = 1; l <= 9; ++l ) done += m_progress.m_best.count( levelId( e + 1, l ) ) && m_progress.m_best.at( levelId( e + 1, l ) ).m_done;
            drawText( tr( "episode." + std::to_string( e + 1 ) ), x + cw / 2.0f, y + 100.0f - ( sel ? 6 : 0 ), sel ? Color{ 255, 230, 120, 255 } : Color{ 210, 220, 240, 255 }, false, true );
            drawText( std::to_string( done ) + "/9", x + cw / 2.0f, y + 150.0f - ( sel ? 6 : 0 ), { 150, 200, 255, 255 }, false, true );
        }
        drawText( tr( "episode.about." + std::to_string( m_cursor + 1 ) ), cx, 290, { 180, 210, 240, 255 }, false, true );
        break;
    }
    case StateE::LEVELS:
    {
        drawText( tr( "episode." + std::to_string( m_pickEpisode ) ), cx, 16, { 200, 235, 255, 255 }, true, true );
        drawPanel( (int)cx - 230, 54, 460, 9 * 26 + 14 );
        for ( int l = 0; l < 9; ++l )
        {
            std::string id = levelId( m_pickEpisode, l + 1 );
            bool        open = m_progress.unlocked( m_pickEpisode, l + 1 );
            bool        sel = l == m_cursor;
            Color       c = !open ? Color{ 100, 105, 125, 255 } : sel ? Color{ 255, 230, 120, 255 } : Color{ 210, 220, 240, 255 };
            float       y = 62.0f + l * 26;
            std::string name = open ? tr( "level." + id ) : "? ? ?";
            drawText( std::to_string( l + 1 ) + ( l == 8 ? "  " + tr( "menu.boss" ) : "" ), cx - 214, y, c );
            drawText( name, cx - 150, y, c );
            auto it = m_progress.m_best.find( id );
            if ( it != m_progress.m_best.end() && it->second.m_done )
                drawText( std::to_string( it->second.m_treasure ) + "%  " + std::to_string( it->second.m_secrets ) + "/" + std::to_string( it->second.m_secretsMax ) + "  " + fmtTime( it->second.m_time ),
                          cx + 100, y, { 150, 220, 170, 255 } );
            if ( it != m_progress.m_best.end() ) drawMedals( it->second.m_medals, cx + 178, y - 1, 11 );
            if ( sel ) drawText( ">", cx - 226 + std::sin( m_t * 8 ) * 2, y, { 255, 200, 90, 255 } );
        }
        std::string secret = "e" + std::to_string( m_pickEpisode ) + "s";
        auto        sit = m_progress.m_best.find( secret );
        if ( sit != m_progress.m_best.end() )
        {
            float y = 62.0f + 9 * 26;
            bool  sel = m_cursor == 9;
            drawText( "*  " + tr( "level." + secret ), cx - 214, y, sel ? Color{ 255, 230, 120, 255 } : Color{ 230, 170, 255, 255 } );
            drawMedals( sit->second.m_medals, cx + 178, y - 1, 11 );
            if ( sel ) drawText( ">", cx - 226 + std::sin( m_t * 8 ) * 2, y, { 255, 200, 90, 255 } );
        }
        drawText( tr( "menu.trial_hint" ), cx, m_screen.m_h - 22.0f, { 150, 180, 220, 255 }, false, true );
        break;
    }
    case StateE::TALLY:
    {
        World &w = *m_world;
        std::string name = hasText( "level." + w.m_level.m_id ) ? tr( "level." + w.m_level.m_id )
                           : language() == "de"                 ? w.m_level.key( "name.de", w.m_level.key( "name" ) )
                                                                : w.m_level.key( "name" );
        drawText( tr( "tally.title" ), cx, 18, { 140, 255, 200, 255 }, true, true );
        drawText( name, cx, 50, { 200, 230, 255, 255 }, false, true );
        drawPanel( (int)cx - 200, 70, 400, (int)m_tally.size() * 17 + 16 );
        int shown = std::min( (int)m_tally.size(), (int)( m_t / 0.35f ) + 1 );
        for ( int i = 0; i < shown; ++i )
        {
            float y = 78.0f + i * 17;
            drawText( m_tally[i].m_label, cx - 184, y, m_tally[i].m_c );
            int vw = assets().font().width( m_tally[i].m_value );
            drawText( m_tally[i].m_value, cx + 184 - vw, y, m_tally[i].m_c );
        }
        if ( shown >= (int)m_tally.size() && (int)( m_t * 2 ) % 2 == 0 ) drawText( tr( "menu.press_on" ), cx, m_screen.m_h - 24.0f, { 200, 210, 230, 255 }, false, true );
        break;
    }
    case StateE::SHOP:
    {
        drawText( tr( "shop.title" ), cx, 14, { 255, 210, 120, 255 }, true, true );
        drawText( tr( "shop.credits" ) + " " + std::to_string( m_progress.m_credits ), cx, 46, { 255, 220, 100, 255 }, false, true );
        std::vector<int> rows;
        for ( int w = 0; w < WeaponCount; ++w )
            if ( m_progress.has( (WeaponE)w ) ) rows.push_back( w );
        rows.push_back( 100 ), rows.push_back( 101 ), rows.push_back( 102 );
        drawPanel( (int)cx - 260, 62, 520, (int)rows.size() * 20 + 14 );
        const Sheet &hud = assets().sheetIn( "ui", "hud" );
        for ( size_t i = 0; i < rows.size(); ++i )
        {
            int         r = rows[i];
            float       y = 70.0f + i * 20;
            bool        sel = (int)i == m_cursor;
            Color       c = sel ? Color{ 255, 230, 120, 255 } : Color{ 210, 220, 240, 255 };
            std::string label, value, about;
            if ( r < 100 )
            {
                int lv = m_progress.m_upgrade[r];
                label = tr( std::string( "weapon." ) + weapon( (WeaponE)r ).m_id );
                value = lv >= 3 ? tr( "shop.max" ) : std::to_string( weapon( (WeaponE)r ).m_price * ( lv + 1 ) ) + " " + tr( "tally.cr" );
                about = std::string( "|" ) + std::string( lv, '#' ) + std::string( 3 - lv, '-' ) + "|";
                if ( !hud.m_standIn ) hud.draw( hud.frame( std::string( "weapon_" ) + weapon( (WeaponE)r ).m_id, 0 ), cx - 240 + hud.m_ax * 0.5f, y + 4 + hud.m_ay * 0.5f - 8 );
            }
            else if ( r == 100 )
            {
                int lv = m_progress.m_armour;
                label = tr( "shop.armour" );
                value = lv >= 3 ? tr( "shop.max" ) : std::to_string( 500 * ( lv + 1 ) ) + " " + tr( "tally.cr" );
                about = std::string( "|" ) + std::string( lv, '#' ) + std::string( 3 - lv, '-' ) + "|";
            }
            else if ( r == 101 )
                label = tr( "shop.ammo" ), value = "150 " + tr( "tally.cr" );
            else
                label = tr( "shop.leave" );
            drawText( label, cx - 210, y, c );
            drawText( about, cx + 20, y, { 140, 200, 255, 255 } );
            int vw = assets().font().width( value );
            drawText( value, cx + 240 - vw, y, c );
            if ( sel ) drawText( ">", cx - 252 + std::sin( m_t * 8 ) * 2, y, { 255, 200, 90, 255 } );
        }
        if ( m_cursor < (int)rows.size() )
        {
            int         r = rows[m_cursor];
            std::string about;
            if ( r < 100 ) about = tr( std::string( "shop.up." ) + weapon( (WeaponE)r ).m_id + "." + std::to_string( std::min( 3, m_progress.m_upgrade[r] + 1 ) ) );
            else if ( r == 100 )
                about = tr( "shop.armour.about" );
            else if ( r == 101 )
                about = tr( "shop.ammo.about" );
            if ( !about.empty() ) drawText( about, cx, m_screen.m_h - 40.0f, { 180, 215, 245, 255 }, false, true );
        }
        break;
    }
    case StateE::STORY:
    {
        // A still above the text when there is one (assets/story/<prefix with _>_<page>.png).
        std::string still = m_storyPrefix.size() > 6 ? m_storyPrefix.substr( 6 ) : m_storyPrefix;
        for ( char &ch : still )
            if ( ch == '.' ) ch = '_';
        const Texture2D *img = assets().texture( "story/" + still + "_" + std::to_string( m_page + 1 ) + ".png" );
        if ( img )
        {
            // Whole pixels only (the stills are pixel art): 1x on the 640 x 360 screen.
            float sc = std::max( 1.0f, std::floor( std::min( ( m_screen.m_w - 120.0f ) / img->width, 180.0f / img->height ) ) );
            float iw = img->width * sc, ih = img->height * sc;
            float ix = std::floor( cx - iw / 2 );
            DrawRectangle( (int)ix - 3, 9, (int)iw + 6, (int)ih + 6, { 8, 8, 20, 255 } );
            DrawTexturePro( *img, { 0, 0, (float)img->width, (float)img->height }, { ix, 12, iw, ih }, { 0, 0 }, 0, WHITE );
            drawPanel( 40, 201, m_screen.m_w - 80, m_screen.m_h - 213 );
        }
        else
            drawPanel( 40, 40, m_screen.m_w - 80, m_screen.m_h - 80 );
        const std::string &page = m_page < (int)m_pages.size() ? m_pages[m_page] : "";
        // Wrap the page into lines that fit.
        const PixelFont &f = assets().font();
        std::vector<std::string> lines;
        std::string              line, word;
        auto                     flush = [&]()
        {
            if ( !word.empty() )
            {
                std::string t = line.empty() ? word : line + " " + word;
                if ( f.width( t ) > m_screen.m_w - 130 ) lines.push_back( line ), line = word;
                else
                    line = t;
                word.clear();
            }
        };
        for ( char ch : page )
        {
            if ( ch == ' ' ) flush();
            else if ( ch == '\n' )
                flush(), lines.push_back( line ), line.clear();
            else
                word += ch;
        }
        flush();
        if ( !line.empty() ) lines.push_back( line );
        float y = img ? 213.0f : 62.0f;
        for ( const std::string &l : lines ) drawText( l, 64, y, { 225, 235, 255, 255 } ), y += img ? 14.0f : 16.0f;
        drawText( std::to_string( m_page + 1 ) + "/" + std::to_string( m_pages.size() ), m_screen.m_w - 80.0f, m_screen.m_h - 60.0f, { 140, 160, 200, 255 } );
        if ( (int)( m_t * 2 ) % 2 == 0 ) drawText( tr( "menu.press_on" ), cx, m_screen.m_h - 60.0f, { 200, 210, 230, 255 }, false, true );
        break;
    }
    case StateE::OPTIONS:
    {
        auto pctOf = []( float v ) { return std::to_string( (int)std::round( v * 100 ) ) + "%"; };
        drawMenu( tr( "menu.options" ),
                  { tr( "opt.fullscreen" ) + ": " + tr( m_settings.m_fullscreen ? "opt.on" : "opt.off" ), tr( "opt.master" ) + ": " + pctOf( m_settings.m_master ),
                    tr( "opt.music" ) + ": " + pctOf( m_settings.m_music ), tr( "opt.effects" ) + ": " + pctOf( m_settings.m_effects ),
                    tr( "opt.language" ) + ": " + tr( "opt.lang_name" ), tr( "opt.shake" ) + ": " + tr( m_settings.m_shake ? "opt.on" : "opt.off" ),
                    tr( "opt.rumble" ) + ": " + tr( m_settings.m_rumble ? "opt.on" : "opt.off" ),
                    tr( "opt.fps" ) + ": " + tr( "opt.fps." + std::to_string( m_settings.m_fps ) ),
                    tr( "opt.speed" ) + ": " + std::to_string( 100 - 10 * m_settings.m_speed ) + "%",
                    tr( "opt.invulnerable" ) + ": " + tr( m_settings.m_invulnerable ? "opt.on" : "opt.off" ),
                    tr( "opt.infinite_ammo" ) + ": " + tr( m_settings.m_infiniteAmmo ? "opt.on" : "opt.off" ), tr( "opt.controls" ), tr( "menu.back" ) },
                  48 );
        break;
    }
    case StateE::CONTROLS:
    {
        drawText( tr( "opt.controls" ), cx, 20, { 200, 235, 255, 255 }, true, true );
        drawPanel( (int)cx - 250, 56, 500, 250 );
        static const char *rows[] = { "run", "aim", "jump", "drop", "fire", "charge", "switch", "pause", "fullscreen" };
        drawText( tr( "ctl.keyboard" ), cx - 40, 66, { 150, 200, 255, 255 } );
        drawText( tr( "ctl.pad" ), cx + 120, 66, { 150, 200, 255, 255 } );
        for ( int i = 0; i < 9; ++i )
        {
            float y = 88.0f + i * 22;
            std::string k = std::string( "ctl." ) + rows[i];
            drawText( tr( k ), cx - 232, y, { 255, 230, 160, 255 } );
            drawText( tr( k + ".key" ), cx - 40, y, { 220, 230, 250, 255 } );
            drawText( tr( k + ".pad" ), cx + 120, y, { 220, 230, 250, 255 } );
        }
        break;
    }
    case StateE::EXTRAS:
    case StateE::LOGBOOK:
    case StateE::AWARDS:
    case StateE::SCORES: drawExtras( m_state ); break;
    default: break;
    }
    drawToasts();
    if ( m_messageT > 0 ) drawText( m_message, cx, m_screen.m_h - 20.0f, { 255, 160, 140, 255 }, false, true );
    m_screen.end();
    m_screen.present( 0.6f );
}

int runApp( const Options &o )
{
    App app( o );
    return app.run();
}

}   // namespace kepler
