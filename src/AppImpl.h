/**
 * @file AppImpl.h
 * @brief The App class behind runApp (App.cpp: start, menus, flow; AppExtras.cpp: the second round -- radio,
 *        medals, awards, logbook, high scores, boss rush, time trial, New Game+, demo, assist; AppMore.cpp: the third
 *        -- death records, ghosts, challenges, bestiary, pause map, quick save, performance display).
 * @author Rene Weller
 */
#pragma once

#include "App.h"
#include "Audio.h"
#include "Bot.h"
#include "Content.h"
#include "Editor.h"
#include "Save.h"
#include "Screen.h"
#include "World.h"

#include <raylib.h>

#include <cstdio>
#include <memory>
#include <string>
#include <vector>

namespace kepler
{

struct MenuKeys;

enum class StateE
{
    TITLE,
    MAIN,
    DIFFICULTY,
    EPISODES,
    LEVELS,
    PLAY,
    PAUSE,
    TALLY,
    SHOP,
    STORY,
    OPTIONS,
    CONFIRM,
    CONTROLS,
    EDITOR,
    RADIO,   ///< the Commodore's message before a level
    EXTRAS,
    LOGBOOK,
    AWARDS,
    SCORES,
    CHALLENGE,   ///< the challenges: today's, or a level with modifiers
    MAP          ///< the pause menu's map of the level
};

inline const char *EpisodeBg[5] = { "", "station_a", "jungle_a", "ice_a", "citadel_a" };

/** @brief Wraps a text into lines that fit a width (in the small or the big font). */
std::vector<std::string> wrapText( const std::string &text, int width, bool big = false );

inline std::string fmtTime( float t )
{
    int s = (int)t;
    char buf[32];
    snprintf( buf, sizeof( buf ), "%d:%02d", s / 60, s % 60 );
    return buf;
}

/** @brief A line of the tally. */
struct TallyLine
{
    std::string m_label, m_value;
    Color       m_c;
};

class App
{
public:
    explicit App( const Options &o ) : m_o( o ) {}
    int run();

private:
    void openWindow();
    void applyVolumes() { setVolumes( m_settings.m_master, m_settings.m_music, m_settings.m_effects ); }
    bool startLevel( int episode, int stage );
    void finishLevel();
    void grantEpisodeWeapons( int episode );
    void showStory( const std::string &prefix, StateE after );
    void go( StateE s, int cursor = 0 );

    void update( float dt );
    void draw();
    void drawBackdrop( const std::string &bg, float t );
    void drawPanel( int x, int y, int w, int h );
    int  drawText( const std::string &t, float x, float y, Color c, bool big = false, bool centre = false );
    void drawMenu( const std::string &title, const std::vector<std::string> &items, int y, const std::vector<bool> *enabled = nullptr );
    std::vector<std::string> mainItems() const;

    Options                m_o;
    Settings               m_settings;
    Progress               m_progress;
    bool                   m_hasSave = false;
    Screen                 m_screen;
    std::unique_ptr<World> m_world;
    StateE                 m_state = StateE::TITLE;
    StateE                 m_back = StateE::MAIN;
    int                    m_cursor = 0;
    float                  m_t = 0;
    int                    m_episode = 1, m_stage = 1;
    int                    m_pickEpisode = 1;
    std::vector<std::string> m_pages;
    int                    m_page = 0;
    StateE                 m_afterStory = StateE::MAIN;
    std::string            m_storyBg;
    std::vector<TallyLine> m_tally;
    std::string            m_message;
    float                  m_messageT = 0;
    std::string            m_confirm;
    int                    m_confirmAction = 0;
    bool                   m_quit = false;
    bool                   m_directLevel = false;
    float                  m_fade = 0;
    std::unique_ptr<Bot>   m_bot;
    std::unique_ptr<Editor> m_editor;
    bool                   m_fromEditor = false;   ///< the level in play is the editor's test
    void openEditor( const std::string &path );
    void playEditorLevel();
    int  autotest();

    // The second round (AppExtras.cpp).
    bool startLevelId( const std::string &id, bool radio = true );
    bool loadLevelId( const std::string &id );
    void nextAfterLevel( World &w, int &medals );
    void grantApp( AwardE a );
    void checkAwards();
    void addHighScore();
    void startBossRush();
    void startDemo();
    void applyAssist();
    void updateExtras( StateE state, struct MenuKeys &k, float dt );
    void drawExtras( StateE state );
    void drawRadio();
    void drawToasts();
    void drawMedals( int medals, float x, float y, float size );

    std::string m_nextId;        ///< the level after the tally and the shop ("" = none)
    std::string m_afterSecret;   ///< the level after a secret level
    std::string m_pendingId;     ///< the level the radio message leads into
    std::string m_storyPrefix;   ///< the story's key prefix (its stills)
    bool        m_trial = false; ///< a time trial runs
    int         m_rush = 0;      ///< boss rush: the boss now (1-4), 0 = none
    float       m_rushTime = 0;
    bool        m_demo = false;  ///< the attract mode plays
    float       m_idleT = 0;
    float       m_radioT = 0;
    int         m_scoreDiff = 1; ///< the high score page shows this difficulty
    bool        m_radioVoice = false; ///< the radio message has its voice playing
    int         m_editorSlot = 1; ///< the level editor opens custom<slot>.txt (1..9)
    int         m_listTop = 0;   ///< the first row of a scrolled list
    struct Toast
    {
        std::string m_text;
        float       m_t;
    };
    std::vector<Toast> m_toasts;

    // The third round (AppMore.cpp).
    void recordDeaths( World &w, const std::string &file, const char *mode );
    void recordPlayDeaths();
    std::string ghostPath( const std::string &id ) const;
    void loadGhost( const std::string &id );
    void saveGhost( const std::string &id, const std::vector<World::TrackPoint> &track );
    std::vector<std::string> challengeLevels() const;
    void dailyChallenge( std::string &id, int &mods ) const;
    std::string challengeKey( const std::string &id, int mods, bool daily ) const;
    std::string modsText( int mods ) const;
    bool startChallenge( const std::string &id, int mods, const std::string &key );
    void finishChallenge( World &w );
    void updateChallenge( struct MenuKeys &k );
    void drawChallenge();
    std::vector<std::string> bestiaryIds() const;
    void drawBestiary();
    void buildMap();
    void drawMap();
    std::string suspendPath() const;
    bool canSuspend() const;
    void saveSuspend();
    void clearSuspend();
    bool hasSuspend() const;
    bool resumeSuspend();
    bool perfOn() const { return m_settings.m_perf || m_o.m_perf; }
    void updatePerf( float frame );
    void drawPerf();
    /** @brief The settings the level in play follows (colour help, big text). */
    void applyWorldSettings()
    {
        if ( m_world ) m_world->m_colourAssist = m_settings.m_colourAssist, m_world->m_bigText = m_settings.m_bigText;
    }

    std::vector<World::TrackPoint> m_ghostTrack;       ///< the time trial's best run
    int                            m_challenge = -1;   ///< a challenge runs: its modifiers (bits), -1 none
    std::string                    m_challengeKey;
    int                            m_challengeMods = 0, m_challengePick = 0;
    Progress    m_challengeProgress;   ///< what Kip carries in a challenge (the game's progress stays)
    int         m_logTab = 0;          ///< the logbook's page: 0 the pages found, 1 the bestiary
    Texture2D   m_mapTex = {};
    int         m_perfN = 0;
    float       m_perfSum = 0, m_perfMax = 0;
    std::string m_perfLine;
    double                         m_perfPart[3] = {};      ///< the frame just shown: update, draw, swap (seconds)
    double                         m_perfMaxPart[3] = {};   ///< the same for the second's longest frame
    bool        m_focused = true;
};


}   // namespace kepler
