/**
 * @file Editor.cpp
 * @brief The level editor: paints a level with the game's own tiles and sprites (EditorView.cpp) in the file format
 *        of docs/DESIGN.md (EditorDoc.cpp), with a palette of cells, pickups, enemies, objects and bosses, undo and
 *        redo, copy and paste, the level's settings, the checker in the background and a test run.
 *
 *        Mouse and keyboard: left button paints (drag: a line, Shift+drag: a rectangle, Alt+click: pick, Ctrl+drag:
 *        select), right click erases (drag: pans, Shift+drag: erases a rectangle), wheel zooms; arrows/WASD pan,
 *        Tab palette, F1 help, F2 settings, F5 check, F9 test, Esc menu, Ctrl+Z/Y undo/redo, Ctrl+C/X/V copy, cut,
 *        paste, G grid, C characters, Z zoom, Q pick, F fill, Delete erase, F3 decorations, F4 lighting.
 *        Pad: stick/d-pad move the cursor, A paints, B erases, X/Y palette, LB/RB brush, LT/RT zoom, right stick
 *        pans, Start menu, Select check.
 * @author Rene Weller
 */
#include "Editor.h"

#include "Assets.h"
#include "Checker.h"
#include "Content.h"
#include "EditorDoc.h"
#include "EditorView.h"
#include "Level.h"
#include "Save.h"
#include "Screen.h"
#include "Text.h"

#include <raylib.h>

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <functional>
#include <map>
#include <set>
#include <sstream>
#include <thread>

namespace kepler
{

using namespace edit;
namespace fs = std::filesystem;

namespace
{

constexpr float T = (float)Tile;
constexpr int   BarH = 13;     ///< the top and bottom bars
constexpr int   PalW = 216;    ///< the palette's width
constexpr int   UndoMax = 100; ///< undo steps kept
constexpr int   ReportH = 112;

const char *const Themes[8] = { "station", "hull", "jungle", "hive", "ice", "crystal", "foundry", "citadel" };
const char *const CatKeys[5] = { "editor.cat.cells", "editor.cat.items", "editor.cat.enemies", "editor.cat.objects", "editor.cat.boss" };

// The pad's button glyphs in the fonts (docs/DESIGN.md "Fonts").
const std::string PadA = "\xEE\x80\x80", PadB = "\xEE\x80\x81", PadX = "\xEE\x80\x82";
const std::string PadLB = "\xEE\x80\x84", PadRB = "\xEE\x80\x85", PadStart = "\xEE\x80\x88", PadSelect = "\xEE\x80\x89";

const Color Ink = { 220, 236, 255, 255 }, Dim = { 140, 160, 190, 255 }, Gold = { 255, 220, 110, 255 };
const Color Bad = { 255, 110, 100, 255 }, Good = { 130, 240, 160, 255 }, Warn = { 255, 210, 90, 255 };
const Color PanelFill = { 12, 16, 36, 255 }, PanelEdge = { 80, 170, 230, 255 };

enum class ToolE
{
    PAINT,
    TELE_PAIR,    ///< two pads that lead to each other
    TELE_ONEWAY   ///< a pad and the place it leads to
};

/** @brief A palette entry: a fixed map character or a legend line. */
struct Item
{
    std::string              m_id;          ///< what it is (icons)
    std::string              m_name;        ///< a text key, or the name itself when m_literal
    bool                     m_literal = false;
    char                     m_ch = 0;      ///< a fixed map character (0: a legend line)
    std::string              m_kind;        ///< the legend kind
    std::string              m_fixed;       ///< words after the kind that stay (weapon, enemy, laser h|v)
    std::string              m_args;        ///< words the user may change
    std::vector<std::string> m_presets;     ///< suggestions for m_args
    std::string              m_argsHint;    ///< a text key: what the words mean
    bool                     m_group = false;   ///< takes the switch group letter
    std::string              m_groupTail;       ///< after the group (toggle: solid|empty)
    bool                     m_enemy = false;   ///< takes the enemy flags
    bool                     m_stamp = false;   ///< one per click (no lines, no rectangles)
    bool                     m_unique = false;  ///< one in the level: placing it moves it
    bool                     m_ask = false;     ///< ask for the words when picked
    ToolE                    m_tool = ToolE::PAINT;
    char                     m_look = 0;        ///< drawn as this cell
    std::string              m_sheet, m_anim;   ///< drawn as this sprite
};

/** @brief A line of the checker's report. */
struct ReportLine
{
    std::string m_text;
    Color       m_c = Ink;
    int         m_x = -1, m_y = -1;   ///< the cell it names (0-based), -1 none
};

/** @brief Copied cells: their characters and the legend lines they need. */
struct Clip
{
    int                        m_w = 0, m_h = 0;
    std::string                m_cells;
    std::map<char, std::string> m_legend;
};

std::string utf8( int cp )
{
    std::string s;
    if ( cp < 0x80 ) s += (char)cp;
    else if ( cp < 0x800 )
        s += (char)( 0xC0 | ( cp >> 6 ) ), s += (char)( 0x80 | ( cp & 0x3F ) );
    else if ( cp < 0x10000 )
        s += (char)( 0xE0 | ( cp >> 12 ) ), s += (char)( 0x80 | ( ( cp >> 6 ) & 0x3F ) ), s += (char)( 0x80 | ( cp & 0x3F ) );
    else
        s += (char)( 0xF0 | ( cp >> 18 ) ), s += (char)( 0x80 | ( ( cp >> 12 ) & 0x3F ) ), s += (char)( 0x80 | ( ( cp >> 6 ) & 0x3F ) ),
            s += (char)( 0x80 | ( cp & 0x3F ) );
    return s;
}

void popUtf8( std::string &s )
{
    if ( s.empty() ) return;
    size_t i = s.size() - 1;
    while ( i > 0 && ( (unsigned char)s[i] & 0xC0 ) == 0x80 ) --i;
    s.resize( i );
}

std::string fmtNum( float v )
{
    char buf[32];
    snprintf( buf, sizeof( buf ), "%.2f", v );
    std::string s = buf;
    while ( s.size() > 3 && s.back() == '0' && s[s.size() - 2] != '.' ) s.pop_back();
    return s;
}

int txt( const std::string &t, float x, float y, Color c, bool shadow = true )
{
    const PixelFont &f = assets().font();
    if ( shadow ) f.draw( t, std::floor( x ) + 1, std::floor( y ) + 1, { 6, 6, 16, 255 } );
    return f.draw( t, std::floor( x ), std::floor( y ), c );
}

int txtW( const std::string &t )
{
    return assets().font().width( t );
}

/** @brief A text cut to a width (with an ellipsis). */
std::string fit( std::string t, int w )
{
    if ( txtW( t ) <= w ) return t;
    const std::string dots = "\xE2\x80\xA6";
    while ( !t.empty() && txtW( t + dots ) > w ) popUtf8( t );
    return t + dots;
}

void panel( Rectangle r, Color fill = PanelFill, Color edge = PanelEdge )
{
    DrawRectangleRec( r, fill );
    DrawRectangleLinesEx( r, 1, edge );
}

bool inRect( Vector2 p, Rectangle r )
{
    return CheckCollisionPointRec( p, r );
}

/** @brief Keys from the English text files that start (and end) so: sign keys, lore pages. */
std::vector<std::string> listTextKeys( const std::string &prefix, const std::string &suffix, bool strip )
{
    std::set<std::string>    keys;
    std::vector<std::string> files = { assetDir() + "text/en.txt" };
    std::error_code          e;
    for ( const auto &f : fs::directory_iterator( assetDir() + "text/en", e ) )
        if ( f.path().extension() == ".txt" ) files.push_back( f.path().string() );
    for ( const std::string &path : files )
    {
        std::ifstream in( path, std::ios::binary );
        std::string   line;
        while ( std::getline( in, line ) )
        {
            size_t eq = line.find( '=' );
            if ( eq == std::string::npos || line.empty() || line[0] == '#' ) continue;
            std::string k = line.substr( 0, eq );
            while ( !k.empty() && ( k.back() == ' ' || k.back() == '\t' ) ) k.pop_back();
            if ( k.size() <= prefix.size() + suffix.size() || k.rfind( prefix, 0 ) != 0 ) continue;
            if ( !suffix.empty() && k.compare( k.size() - suffix.size(), suffix.size(), suffix ) != 0 ) continue;
            keys.insert( strip ? k.substr( prefix.size(), k.size() - prefix.size() - suffix.size() ) : k );
        }
    }
    return { keys.begin(), keys.end() };
}

/** @brief The palette: cells, pickups, enemies (the episode's first), objects, bosses. */
std::vector<std::vector<Item>> makeItems( int episode, const std::vector<std::string> &signs, const std::vector<std::string> &lores )
{
    std::vector<std::vector<Item>> cats( 5 );
    auto cell = [&]( const char *id, char ch )
    {
        Item i;
        i.m_id = id;
        i.m_name = std::string( "editor.item." ) + id;
        i.m_ch = ch;
        i.m_look = ch;
        cats[0].push_back( i );
    };
    cell( "sky", ' ' );
    cell( "interior", '.' );
    cell( "terrain_a", '#' );
    cell( "terrain_b", '%' );
    cell( "platform", '-' );
    cell( "crumble", '_' );
    cell( "breakable", 'B' );
    cell( "fake", 'X' );
    cell( "spike_up", '^' );
    cell( "spike_down", 'v' );
    cell( "spike_left", '<' );
    cell( "spike_right", '>' );
    cell( "liquid", '~' );
    cell( "door_blue", 'd' );
    cell( "door_gold", 'D' );
    cell( "secret", '?' );
    for ( int dir = 0; dir < 2; ++dir )
    {
        Item i;
        i.m_id = dir ? "conveyor_right" : "conveyor_left";
        i.m_name = "editor.item." + i.m_id;
        i.m_kind = "conveyor";
        i.m_fixed = dir ? "1" : "-1";
        i.m_look = dir ? '}' : '{';
        cats[0].push_back( i );
    }

    auto pickup = [&]( const std::string &id, char ch, const std::string &anim, const std::string &kind = "", const std::string &fixed = "" )
    {
        Item i;
        i.m_id = id;
        i.m_name = "editor.item." + id;
        i.m_ch = ch;
        i.m_kind = kind;
        i.m_fixed = fixed;
        i.m_sheet = "items";
        i.m_anim = anim;
        cats[1].push_back( i );
        return &cats[1].back();
    };
    pickup( "crystal", '*', "crystal" );
    pickup( "treasure", '$', "gem" );
    for ( const TreasureDef &t : treasures() ) pickup( std::string( "treasure_" ) + t.m_id, 0, t.m_id, "treasure", t.m_id );
    pickup( "health", '+', "health" );
    pickup( "health_big", 'H', "health_big" );
    pickup( "ammo", '&', "ammo" );
    pickup( "key_blue", 'k', "key_blue" );
    pickup( "key_gold", 'K', "key_gold" );
    for ( int w = 1; w < WeaponCount; ++w )
    {
        std::string id = weapon( (WeaponE)w ).m_id;
        Item       *i = pickup( "weapon_" + id, 0, "weapon_" + id, "weapon", id );
        i->m_name = "weapon." + id;
    }
    for ( const char *p : { "overdrive", "boots", "shield" } ) pickup( std::string( "power_" ) + p, 0, std::string( "power_" ) + p, "power", p );
    {
        Item *i = pickup( "lore", 0, "lore", "lore" );
        i->m_presets = lores.empty() ? std::vector<std::string>{ "e1_academy_founding" } : lores;
        i->m_args = i->m_presets[0];
        i->m_argsHint = "editor.args.lore";
        i->m_ask = true;
        i->m_stamp = true;
    }

    // Enemies: the episode's eight first.
    std::vector<const EnemyDef *> order;
    const std::vector<EnemyDef>  &defs = enemyDefs();
    for ( size_t k = 0; k < defs.size(); ++k )
        if ( (int)k / 8 + 1 == episode ) order.push_back( &defs[k] );
    for ( size_t k = 0; k < defs.size(); ++k )
        if ( (int)k / 8 + 1 != episode ) order.push_back( &defs[k] );
    for ( const EnemyDef *d : order )
    {
        Item i;
        i.m_id = d->m_id;
        i.m_name = d->m_id;
        i.m_literal = true;
        i.m_kind = "enemy";
        i.m_fixed = d->m_id;
        i.m_enemy = true;
        i.m_stamp = true;
        i.m_sheet = d->m_id;
        cats[2].push_back( i );
    }

    auto object = [&]( const std::string &id, const std::string &kind, char ch, const std::string &sheet, const std::string &anim )
    {
        Item i;
        i.m_id = id;
        i.m_name = "editor.item." + id;
        i.m_kind = kind;
        i.m_ch = ch;
        i.m_sheet = sheet;
        i.m_anim = anim;
        i.m_stamp = true;
        cats[3].push_back( i );
        return &cats[3].back();
    };
    object( "start", "", 'P', "hero", "idle" )->m_unique = true;
    object( "exit", "", 'E', "objects", "exit_closed" )->m_unique = true;
    object( "checkpoint", "", 'C', "objects", "checkpoint_off" );
    object( "spring", "spring", 0, "objects", "spring" );
    {
        Item *i = object( "sign", "sign", 0, "objects", "sign" );
        i->m_presets = signs.empty() ? std::vector<std::string>{ "sign.e1l1.run" } : signs;
        i->m_args = i->m_presets[0];
        i->m_argsHint = "editor.args.sign";
        i->m_ask = true;
    }
    for ( int v = 0; v < 2; ++v )
    {
        Item *i = object( v ? "laser_v" : "laser_h", "laser", 0, "objects", v ? "laser_emitter" : "laser_emitter_side" );
        i->m_fixed = v ? "v" : "h";
        i->m_args = "1.5 1.5";
        i->m_presets = { "1.5 1.5", "1.2 1.8", "2.0 1.2", "1.0 1.0", "1.5 1.5 0.75" };
        i->m_argsHint = "editor.args.laser";
    }
    {
        Item *i = object( "crusher", "crusher", 0, "", "" );
        i->m_args = "3 3.0";
        i->m_presets = { "2 2.6", "3 3.0", "4 3.2", "6 2.4", "3 3.0 1.5" };
        i->m_argsHint = "editor.args.crusher";
    }
    {
        Item *i = object( "light", "light", 0, "", "" );
        i->m_args = "warm 6";
        i->m_presets = { "warm 6", "cold 6", "cyan 6", "green 5", "red 5", "orange 6", "violet 6", "magenta 6", "white 7", "yellow 6", "blue 6" };
        i->m_argsHint = "editor.args.light";
    }
    object( "teleport_pair", "", 0, "objects", "teleporter" )->m_tool = ToolE::TELE_PAIR;
    object( "teleport_oneway", "", 0, "objects", "teleporter" )->m_tool = ToolE::TELE_ONEWAY;
    object( "switch", "switch", 0, "objects", "switch_off" )->m_group = true;
    for ( int e = 0; e < 2; ++e )
    {
        Item *i = object( e ? "toggle_empty" : "toggle_solid", "toggle", 0, "", "" );
        i->m_group = true;
        i->m_groupTail = e ? "empty" : "solid";
        i->m_look = e ? 'T' : 't';
        i->m_stamp = false;
    }
    for ( int v = 0; v < 2; ++v )
    {
        Item *i = object( v ? "mover_v" : "mover_h", "mover", 0, "", "" );
        i->m_args = v ? "0 -6 60" : "6 0 60";
        i->m_presets = v ? std::vector<std::string>{ "0 -4 60", "0 -6 60", "0 -10 80 1.0", "0 6 60" }
                         : std::vector<std::string>{ "4 0 60", "6 0 60", "8 0 70", "12 0 85", "-6 0 60" };
        i->m_argsHint = "editor.args.mover";
        i->m_ask = true;
        i->m_stamp = false;
    }
    {
        Item *i = object( "warp", "warp", 0, "objects", "exit_open" );
        i->m_args = "e1s";
        i->m_presets = { "e1s", "e2s", "e3s", "e4s" };
        i->m_argsHint = "editor.args.warp";
        i->m_ask = true;
    }

    for ( const char *b : { "warden", "broodmother", "colossus", "gloam" } )
    {
        Item i;
        i.m_id = b;
        i.m_name = std::string( "boss." ) + b;
        i.m_kind = "boss";
        i.m_fixed = b;
        i.m_stamp = true;
        i.m_unique = true;
        i.m_sheet = b;
        cats[4].push_back( i );
    }
    return cats;
}

/** @brief Whether the editor knows a spawn kind (unknown ones are kept and marked on the map). */
bool knownKind( const std::string &k )
{
    static const std::set<std::string> known = { "crystal", "treasure", "health", "ammo",   "key",     "start", "exit",   "checkpoint",
                                                 "enemy",   "boss",     "weapon", "power",  "lore",    "teleport", "arrive", "switch",
                                                 "toggle",  "mover",    "spring", "conveyor", "laser", "crusher",  "sign",   "light",
                                                 "warp" };
    return k.empty() || known.count( k ) > 0;
}

bool walkerKind( const std::string &id )
{
    const EnemyDef *d = enemyDef( id );
    return d && d->m_brain == BrainE::WALKER;
}

}   // namespace

// ============================================================================================================ Impl

struct Editor::Impl
{
    enum class ModeE
    {
        EDIT,
        MENU,
        SETTINGS,
        FIELD,
        HELP
    };
    enum class DragE
    {
        NONE,
        PAINT,        ///< left button: a line of the brush
        RECT,         ///< Shift + left: a rectangle of the brush
        SELECT,       ///< Ctrl + left: a selection
        RIGHT,        ///< right button: a click erases, a drag pans
        ERASE_RECT,   ///< Shift + right: a rectangle erased
        PAN,          ///< middle button
        PAD_PAINT,    ///< pad A held
        PAD_ERASE     ///< pad B held
    };
    enum class HoverE
    {
        MAP,
        BAR,
        PALETTE,
        REPORT,
        DIALOG
    };
    /** @brief A control below the palette's grid. */
    struct Ctl
    {
        int       m_kind;   ///< 0-3 enemy flags, 4 group, 5 words
        int       m_row;
        Rectangle m_r;
    };

    // The document.
    Doc                  m_doc;
    std::string          m_path;
    bool                 m_dirty = false;
    std::vector<DocData> m_undo, m_redo;
    DocData              m_pending;
    bool                 m_hasPending = false;

    // The view.
    Camera                m_cam;
    int                   m_zoomI = 0;
    bool                  m_grid = true, m_showChars = false, m_decos = true, m_light = false;
    float                 m_clock = 0;
    std::vector<DecoSpot> m_decoSpots;
    bool                  m_decosDirty = true;
    CharTable             m_table;
    int                   m_vw = 640, m_vh = 360;

    // Input.
    Vector2 m_mouse = { -100, -100 }, m_delta = { 0, 0 };
    bool    m_pad = false;
    int     m_curX = 0, m_curY = 0;
    bool    m_curOn = false;
    int     m_heldDir = 4;
    float   m_repeatT = 0;
    DragE   m_drag = DragE::NONE;
    int     m_dragX = 0, m_dragY = 0, m_lastX = 0, m_lastY = 0;
    Vector2 m_rightAt = { 0, 0 };
    bool    m_rightPanned = false;
    char    m_strokeChar = 0;

    // The palette and the brush.
    bool                           m_palette = true;
    int                            m_cat = 0;                     ///< the page shown
    int                            m_brushCat = 0;                ///< the page the brush is from
    int                            m_sel[5] = { 2, 0, 0, 0, 0 };  ///< the chosen entry of each page
    int                            m_padSel = 0;                  ///< pad: the entry under the pad's focus
    bool                           m_padWas = false;              ///< the pad was in use the frame before
    int                            m_palFocus = -1;   ///< pad: -1 the grid, else a control
    std::vector<std::vector<Item>> m_items;
    Item                           m_raw;             ///< a picked character the palette has no entry for
    bool                           m_useRaw = false;
    bool                           m_ambush = false, m_left = false, m_elite = false, m_ceiling = false;
    int                            m_group = 0;
    char                           m_telePending = 0; ///< the second pad still to place
    int                            m_teleX = -1, m_teleY = -1;

    // Selection and clipboard.
    bool m_hasSel = false;
    int  m_sx0 = 0, m_sy0 = 0, m_sx1 = 0, m_sy1 = 0;
    Clip m_clip;
    bool m_pasting = false;

    // Dialogs.
    ModeE                                    m_mode = ModeE::EDIT;
    int                                      m_menuI = 0, m_setI = 0;
    ModeE                                    m_fieldBack = ModeE::EDIT;
    std::string                              m_fieldTitle, m_fieldText;
    std::vector<std::string>                 m_fieldPresets;
    int                                      m_fieldPreset = -1;
    std::function<void( const std::string & )> m_fieldOk;

    // The checker.
    bool                    m_report = false;
    int                     m_reportScroll = 0;
    std::vector<ReportLine> m_lines;
    std::thread             m_thread;
    std::atomic<bool>       m_checking{ false }, m_checked{ false };
    std::string             m_checkOut;
    std::vector<std::pair<int, int>> m_reach, m_reachOut;   ///< standing places the check reached (column, floor row)
    bool                             m_showReach = true;
    // The death map: knockouts in the player's games of this level, per cell.
    struct DeathMark
    {
        int m_x, m_y, m_n;
    };
    std::vector<DeathMark>  m_deathMarks;
    bool                    m_showDeaths = false;
    int                     m_flashX = -1, m_flashY = -1;
    float                   m_flashT = 0;

    // A message in the top bar.
    std::string m_msg;
    float       m_msgT = 0;
    Color       m_msgC = Ink;

    // Choices for the settings.
    std::vector<std::string> m_bgs, m_music;
    std::string              m_demo;   ///< KEPLER_EDITOR_SHOT: states for test pictures, applied once

    ~Impl()
    {
        if ( m_thread.joinable() ) m_thread.join();
    }

    // ------------------------------------------------------------------------------------------------ basics

    void message( const std::string &t, Color c = Ink, float seconds = 3.5f )
    {
        m_msg = t, m_msgC = c, m_msgT = seconds;
    }

    Item &brush()
    {
        if ( m_useRaw ) return m_raw;
        std::vector<Item> &list = m_items[m_brushCat];
        m_sel[m_brushCat] = std::clamp( m_sel[m_brushCat], 0, (int)list.size() - 1 );
        return list[m_sel[m_brushCat]];
    }

    std::string nameOf( const Item &it ) const
    {
        return it.m_literal ? it.m_name : tr( it.m_name );
    }

    /** @brief The legend words a palette entry writes. */
    std::string legendText( const Item &it ) const
    {
        std::string t = it.m_kind;
        auto        add = [&]( const std::string &w )
        {
            if ( !w.empty() ) t += " " + w;
        };
        add( it.m_fixed );
        if ( it.m_group )
        {
            add( std::string( 1, (char)( 'A' + m_group ) ) );
            add( it.m_groupTail );
        }
        add( joinWords( words( it.m_args ) ) );
        if ( it.m_enemy )
        {
            if ( m_ambush ) add( "ambush" );
            if ( m_left ) add( "left" );
            if ( m_elite ) add( "elite" );
            if ( m_ceiling && walkerKind( it.m_fixed ) ) add( "ceiling" );
        }
        return t;
    }

    /** @brief What a palette entry places, as the drawing wants it. */
    CharInfo infoOf( const Item &it ) const
    {
        CharInfo i;
        if ( it.m_ch )
        {
            i.m_kind = m_doc.kindOf( it.m_ch );
            i.m_args = m_doc.argsOf( it.m_ch );
            return i;
        }
        if ( it.m_tool != ToolE::PAINT )
        {
            i.m_kind = "teleport";
            return i;
        }
        std::vector<std::string> w = words( legendText( it ) );
        if ( !w.empty() ) i.m_kind = w[0], i.m_args.assign( w.begin() + 1, w.end() );
        return i;
    }

    /** @brief The map character of the brush (a legend line is made when needed); 0 if none is left. */
    char brushChar()
    {
        Item &b = brush();
        if ( b.m_ch ) return b.m_ch;
        char c = m_doc.charFor( legendText( b ) );
        if ( !c ) message( tr( "editor.msg.no_chars" ), Bad );
        return c;
    }

    // ------------------------------------------------------------------------------------------------- undo

    /** @brief Remembers the document before a change (kept once the change happens). */
    void begin()
    {
        m_pending = m_doc;
        m_hasPending = true;
    }

    void commit()
    {
        if ( !m_hasPending ) return;
        m_undo.push_back( std::move( m_pending ) );
        if ( (int)m_undo.size() > UndoMax ) m_undo.erase( m_undo.begin() );
        m_redo.clear();
        m_hasPending = false;
        m_dirty = true;
    }

    void snapshot()
    {
        begin();
        commit();
    }

    void afterBigChange()
    {
        m_doc.rebuild();
        m_decosDirty = true;
        m_dirty = true;
        m_telePending = 0;
        m_hasSel = false;
        m_hasPending = false;
    }

    void undo( bool back )
    {
        std::vector<DocData> &from = back ? m_undo : m_redo, &to = back ? m_redo : m_undo;
        if ( from.empty() )
        {
            message( tr( back ? "editor.msg.undo_empty" : "editor.msg.redo_empty" ), Dim );
            return;
        }
        to.push_back( m_doc );
        static_cast<DocData &>( m_doc ) = std::move( from.back() );
        from.pop_back();
        afterBigChange();
        message( tr( back ? "editor.msg.undone" : "editor.msg.redone" ), Dim, 1.5f );
    }

    // ---------------------------------------------------------------------------------------------- editing

    bool inside( int x, int y ) const
    {
        return x >= 0 && y >= 0 && x < m_doc.m_w && y < m_doc.m_h;
    }

    /** @brief Sets a cell (the first change of an action keeps its undo step). */
    bool put( int x, int y, char c )
    {
        if ( !c || !inside( x, y ) || m_doc.at( x, y ) == c ) return false;
        commit();
        m_doc.set( x, y, c );
        m_doc.rebuild( x, y, x, y );
        m_dirty = true;
        m_decosDirty = true;
        return true;
    }

    /** @brief What an erased cell becomes: interior or sky, as around it; a second erase flips that. */
    char eraseChar( int x, int y, bool flip ) const
    {
        char now = m_doc.at( x, y );
        if ( flip && now == '.' ) return ' ';
        if ( flip && now == ' ' ) return '.';
        return m_doc.m_view.at( x, y ).m_interior ? '.' : ' ';
    }

    void line( int x0, int y0, int x1, int y1, bool erase )
    {
        int dx = std::abs( x1 - x0 ), dy = -std::abs( y1 - y0 ), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1, err = dx + dy;
        for ( int guard = 0; guard < 2000; ++guard )
        {
            put( x0, y0, erase ? eraseChar( x0, y0, false ) : m_strokeChar );
            if ( x0 == x1 && y0 == y1 ) break;
            int e2 = 2 * err;
            if ( e2 >= dy ) err += dy, x0 += sx;
            if ( e2 <= dx ) err += dx, y0 += sy;
        }
    }

    void fillRect( int x0, int y0, int x1, int y1, bool erase )
    {
        if ( x0 > x1 ) std::swap( x0, x1 );
        if ( y0 > y1 ) std::swap( y0, y1 );
        x0 = std::max( 0, x0 ), y0 = std::max( 0, y0 ), x1 = std::min( m_doc.m_w - 1, x1 ), y1 = std::min( m_doc.m_h - 1, y1 );
        char c = erase ? 0 : brushChar();
        if ( !erase && !c ) return;
        bool any = false;
        for ( int y = y0; y <= y1; ++y )
            for ( int x = x0; x <= x1; ++x )
            {
                char to = erase ? eraseChar( x, y, false ) : c;
                if ( m_doc.at( x, y ) == to ) continue;
                commit();
                m_doc.set( x, y, to );
                any = true;
            }
        if ( any ) m_doc.rebuild( x0, y0, x1, y1 ), m_dirty = true, m_decosDirty = true;
    }

    /** @brief Removes every other placement of a unique kind (the start, the exit, the boss). */
    void removeOthers( const std::string &kind, int keepX, int keepY )
    {
        for ( int y = 0; y < m_doc.m_h; ++y )
            for ( int x = 0; x < m_doc.m_w; ++x )
                if ( ( x != keepX || y != keepY ) && m_doc.kindOf( m_doc.at( x, y ) ) == kind ) put( x, y, eraseChar( x, y, false ) );
    }

    /** @brief One click of a stamp brush (enemies, objects, teleport pads). */
    void stamp( int x, int y )
    {
        if ( !inside( x, y ) ) return;
        Item &b = brush();
        if ( b.m_tool != ToolE::PAINT )
        {
            if ( m_telePending )
            {
                if ( x == m_teleX && y == m_teleY ) return;
                put( x, y, m_telePending );
                m_telePending = 0;
                message( tr( "editor.msg.tele_done" ), Good );
                return;
            }
            char a = m_doc.charFor( "teleport ?", true );
            char other = a ? m_doc.charFor( b.m_tool == ToolE::TELE_PAIR ? std::string( "teleport " ) + a : "arrive", true ) : 0;
            if ( !a || !other )
            {
                message( tr( "editor.msg.no_chars" ), Bad );
                return;
            }
            for ( LegendLine &l : m_doc.m_legend )
                if ( l.m_ch == a ) l.m_text = std::string( "teleport " ) + other;
            put( x, y, a );
            m_telePending = other, m_teleX = x, m_teleY = y;
            message( tr( b.m_tool == ToolE::TELE_PAIR ? "editor.msg.tele_second" : "editor.msg.tele_target" ), Gold, 6 );
            return;
        }
        char c = brushChar();
        if ( !c ) return;
        if ( b.m_unique ) removeOthers( m_doc.kindOf( c ), x, y );
        put( x, y, c );
    }

    void flood( int x, int y )
    {
        if ( !inside( x, y ) ) return;
        if ( brush().m_stamp || brush().m_tool != ToolE::PAINT )
        {
            message( tr( "editor.msg.no_fill" ), Dim );
            return;
        }
        begin();
        char c = brushChar(), from = m_doc.at( x, y );
        if ( !c || c == from ) return;
        std::vector<int> stack = { y * m_doc.m_w + x };
        int              x0 = x, y0 = y, x1 = x, y1 = y, n = 0;
        while ( !stack.empty() )
        {
            int i = stack.back();
            stack.pop_back();
            int cx = i % m_doc.m_w, cy = i / m_doc.m_w;
            if ( m_doc.at( cx, cy ) != from ) continue;
            commit();
            m_doc.set( cx, cy, c );
            ++n;
            x0 = std::min( x0, cx ), y0 = std::min( y0, cy ), x1 = std::max( x1, cx ), y1 = std::max( y1, cy );
            const int d[4][2] = { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } };
            for ( auto &dd : d )
                if ( inside( cx + dd[0], cy + dd[1] ) && m_doc.at( cx + dd[0], cy + dd[1] ) == from ) stack.push_back( ( cy + dd[1] ) * m_doc.m_w + cx + dd[0] );
        }
        m_doc.rebuild( x0, y0, x1, y1 );
        m_decosDirty = true;
        message( tr( "editor.msg.filled" ) + " " + std::to_string( n ), Dim, 2 );
    }

    /** @brief Takes the brush from a cell: its palette entry when there is one, else the character itself. */
    void pick( int x, int y )
    {
        if ( !inside( x, y ) ) return;
        char                     c = m_doc.at( x, y );
        std::string              kind = m_doc.kindOf( c );
        std::vector<std::string> args = m_doc.argsOf( c );
        const LegendLine        *l = m_doc.legend( c );
        auto choose = [&]( int cat, int i )
        {
            m_cat = m_brushCat = cat, m_sel[cat] = i, m_useRaw = false;
            message( tr( "editor.msg.picked" ) + " " + nameOf( m_items[cat][i] ), Dim, 2 );
        };
        if ( !l || c == ' ' || c == '.' )
        {
            for ( int cat = 0; cat < 5; ++cat )
                for ( size_t i = 0; i < m_items[cat].size(); ++i )
                    if ( m_items[cat][i].m_ch == c ) return choose( cat, (int)i );
        }
        else
        {
            std::string a0 = args.empty() ? "" : args[0];
            for ( int cat = 0; cat < 5; ++cat )
                for ( size_t i = 0; i < m_items[cat].size(); ++i )
                {
                    Item &it = m_items[cat][i];
                    if ( it.m_ch || it.m_kind != kind || it.m_tool != ToolE::PAINT ) continue;
                    if ( kind == "enemy" || kind == "boss" || kind == "weapon" || kind == "power" || kind == "treasure" || kind == "laser" )
                    {
                        if ( it.m_fixed != a0 ) continue;
                        if ( kind == "enemy" )
                        {
                            auto has = [&]( const char *w ) { return std::find( args.begin(), args.end(), w ) != args.end(); };
                            m_ambush = has( "ambush" ), m_left = has( "left" ), m_elite = has( "elite" ), m_ceiling = has( "ceiling" );
                        }
                        if ( kind == "laser" ) it.m_args = joinWords( args, 1 );
                    }
                    else if ( kind == "conveyor" )
                    {
                        if ( ( atoi( a0.c_str() ) > 0 ) != ( it.m_fixed == "1" ) ) continue;
                    }
                    else if ( kind == "toggle" || kind == "switch" )
                    {
                        if ( kind == "toggle" && ( args.size() < 2 || args[1] != it.m_groupTail ) ) continue;
                        if ( !a0.empty() ) m_group = std::clamp( a0[0] - 'A', 0, 7 );
                    }
                    else if ( kind == "mover" )
                    {
                        bool vertical = args.size() > 1 && atof( args[1].c_str() ) != 0 && atof( a0.c_str() ) == 0;
                        if ( vertical != ( it.m_id == "mover_v" ) ) continue;
                        it.m_args = joinWords( args );
                    }
                    else
                        it.m_args = joinWords( args );
                    return choose( cat, (int)i );
                }
        }
        // No entry: paint this very character.
        m_raw = Item();
        m_raw.m_id = "raw";
        m_raw.m_name = std::string( "'" ) + c + "' " + ( l ? l->m_text : kind );
        m_raw.m_literal = true;
        m_raw.m_ch = c;
        m_useRaw = true;
        message( tr( "editor.msg.picked" ) + " " + m_raw.m_name, Dim, 2 );
    }

    // ---------------------------------------------------------------------------------------- copy and paste

    void normaliseSel()
    {
        if ( m_sx0 > m_sx1 ) std::swap( m_sx0, m_sx1 );
        if ( m_sy0 > m_sy1 ) std::swap( m_sy0, m_sy1 );
        m_sx0 = std::clamp( m_sx0, 0, m_doc.m_w - 1 ), m_sx1 = std::clamp( m_sx1, 0, m_doc.m_w - 1 );
        m_sy0 = std::clamp( m_sy0, 0, m_doc.m_h - 1 ), m_sy1 = std::clamp( m_sy1, 0, m_doc.m_h - 1 );
    }

    void copy( bool cut )
    {
        if ( !m_hasSel )
        {
            message( tr( "editor.msg.no_selection" ), Dim );
            return;
        }
        normaliseSel();
        m_clip = Clip();
        m_clip.m_w = m_sx1 - m_sx0 + 1, m_clip.m_h = m_sy1 - m_sy0 + 1;
        for ( int y = m_sy0; y <= m_sy1; ++y )
            for ( int x = m_sx0; x <= m_sx1; ++x )
            {
                char c = m_doc.at( x, y );
                m_clip.m_cells += c;
                if ( c != ' ' && c != '.' )
                    if ( const LegendLine *l = m_doc.legend( c ) ) m_clip.m_legend[c] = l->m_text;
            }
        if ( cut )
        {
            begin();
            fillRect( m_sx0, m_sy0, m_sx1, m_sy1, true );
        }
        message( tr( cut ? "editor.msg.cut" : "editor.msg.copied" ) + " " + std::to_string( m_clip.m_w ) + "x" + std::to_string( m_clip.m_h ), Good, 2 );
    }

    void pasteAt( int x0, int y0 )
    {
        if ( m_clip.m_w <= 0 ) return;
        begin();
        std::map<char, char> mapped;
        for ( const auto &[c, text] : m_clip.m_legend )
        {
            // Teleport pads keep their pair only when the very same lines are still there.
            const LegendLine *l = m_doc.legend( c );
            mapped[c] = l && l->m_text == text ? c : m_doc.charFor( text );
        }
        bool any = false;
        for ( int y = 0; y < m_clip.m_h; ++y )
            for ( int x = 0; x < m_clip.m_w; ++x )
            {
                char c = m_clip.m_cells[(size_t)y * m_clip.m_w + x];
                auto it = mapped.find( c );
                if ( it != mapped.end() ) c = it->second ? it->second : '.';
                if ( !inside( x0 + x, y0 + y ) || m_doc.at( x0 + x, y0 + y ) == c ) continue;
                commit();
                m_doc.set( x0 + x, y0 + y, c );
                any = true;
            }
        if ( !any ) return;
        m_doc.rebuild( x0, y0, x0 + m_clip.m_w - 1, y0 + m_clip.m_h - 1 );
        // A start, exit or boss pasted moves it.
        for ( const char *kind : { "start", "exit", "boss" } )
            for ( int y = 0; y < m_clip.m_h; ++y )
                for ( int x = 0; x < m_clip.m_w; ++x )
                    if ( inside( x0 + x, y0 + y ) && m_doc.kindOf( m_doc.at( x0 + x, y0 + y ) ) == kind )
                    {
                        for ( int yy = 0; yy < m_doc.m_h; ++yy )
                            for ( int xx = 0; xx < m_doc.m_w; ++xx )
                                if ( ( xx < x0 || yy < y0 || xx >= x0 + m_clip.m_w || yy >= y0 + m_clip.m_h ) && m_doc.kindOf( m_doc.at( xx, yy ) ) == kind )
                                    put( xx, yy, eraseChar( xx, yy, false ) );
                        y = m_clip.m_h;
                        break;
                    }
        m_dirty = true;
        m_decosDirty = true;
    }

    // --------------------------------------------------------------------------------------------- files

    bool open( const std::string &path )
    {
        if ( m_thread.joinable() ) m_thread.join();
        m_checking = false;
        m_path = path;
        m_undo.clear(), m_redo.clear();
        m_hasPending = false;
        m_lines.clear();
        m_report = false;
        m_mode = ModeE::EDIT;
        m_drag = DragE::NONE;
        m_hasSel = m_pasting = false;
        m_telePending = 0;
        m_useRaw = false;
        size_t slash = path.find_last_of( "/\\" );
        m_doc.m_id = path.substr( slash == std::string::npos ? 0 : slash + 1 );
        if ( m_doc.m_id.size() > 4 && m_doc.m_id.substr( m_doc.m_id.size() - 4 ) == ".txt" ) m_doc.m_id.resize( m_doc.m_id.size() - 4 );

        std::ifstream in( path, std::ios::binary );
        if ( in )
        {
            std::stringstream ss;
            ss << in.rdbuf();
            std::string error;
            if ( !m_doc.parse( ss.str(), error ) )
            {
                TraceLog( LOG_WARNING, "editor: %s: %s", path.c_str(), error.c_str() );
                return false;
            }
            m_dirty = false;
            Level       check;
            std::string problem;
            if ( !check.load( path, problem ) ) message( tr( "editor.msg.file_problem" ) + " " + problem, Warn, 8 );
            else
                message( tr( "editor.msg.opened" ) + " " + m_doc.m_id, Good );
        }
        else
        {
            m_doc.makeNew( 120, 40 );
            m_dirty = true;
            message( tr( "editor.msg.new_level" ) + " " + m_doc.m_id, Good, 5 );
        }

        // The settings' choices.
        m_bgs.clear(), m_music.clear();
        std::error_code e;
        for ( const auto &f : fs::directory_iterator( assetDir() + "bg", e ) )
            if ( f.is_directory( e ) ) m_bgs.push_back( f.path().filename().string() );
        std::sort( m_bgs.begin(), m_bgs.end() );
        std::set<std::string> cues;
        for ( const auto &f : fs::directory_iterator( assetDir() + "music", e ) )
        {
            std::string n = f.path().stem().string();
            if ( f.path().extension() != ".ogg" ) continue;
            if ( n.size() > 3 && ( n.substr( n.size() - 3 ) == "_t1" || n.substr( n.size() - 3 ) == "_t2" ) ) n.resize( n.size() - 3 );
            cues.insert( n );
        }
        m_music.push_back( "" );
        m_music.insert( m_music.end(), cues.begin(), cues.end() );

        m_items = makeItems( episodeOf( m_doc.key( "theme", "station" ) ), listTextKeys( "sign.", "", false ), listTextKeys( "lore.", ".title", true ) );
        m_decosDirty = true;
        m_cat = m_brushCat = 0;
        m_padSel = m_sel[0];
        m_zoomI = 0;
        m_cam.m_zoom = 1;
        // Look at the start.
        int px = m_doc.m_w / 2, py = m_doc.m_h / 2;
        for ( int y = 0; y < m_doc.m_h; ++y )
            for ( int x = 0; x < m_doc.m_w; ++x )
                if ( m_doc.at( x, y ) == 'P' ) px = x, py = y;
        m_curX = px, m_curY = py;
        centreOn( px * T + T / 2, py * T );
        const char *demo = getenv( "KEPLER_EDITOR_SHOT" );
        m_demo = demo ? demo : "";
        // Pictures of the death map: KEPLER_EDITOR_DEATHS=<deaths file> checks the level and shows both overlays.
        if ( const char *deaths = getenv( "KEPLER_EDITOR_DEATHS" ) )
        {
            startCheck( true );
            m_showDeaths = false;
            toggleDeaths( deaths );
        }
        return true;
    }

    bool save()
    {
        std::error_code e;
        fs::path        p( m_path );
        if ( p.has_parent_path() ) fs::create_directories( p.parent_path(), e );
        std::string tmp = m_path + ".tmp";
        {
            std::ofstream out( tmp, std::ios::binary );
            if ( out ) out << m_doc.write();
            if ( !out || !out.good() )
            {
                message( tr( "editor.msg.save_failed" ) + " " + m_path, Bad, 6 );
                return false;
            }
        }
        if ( fs::exists( m_path, e ) ) fs::copy_file( m_path, m_path + ".bak", fs::copy_options::overwrite_existing, e );
        e.clear();
        fs::rename( tmp, m_path, e );
        if ( e )
        {
            message( tr( "editor.msg.save_failed" ) + " " + m_path, Bad, 6 );
            return false;
        }
        m_dirty = false;
        message( tr( "editor.msg.saved" ) + " " + p.filename().string(), Good );
        return true;
    }

    Editor::ResultE testPlay()
    {
        if ( !save() ) return ResultE::STAY;
        Level       check;
        std::string error;
        if ( !check.load( m_path, error ) )
        {
            message( tr( "editor.msg.cannot_test" ) + " " + error, Bad, 6 );
            return ResultE::STAY;
        }
        m_drag = DragE::NONE;
        m_mode = ModeE::EDIT;
        return ResultE::PLAY;
    }

    // ------------------------------------------------------------------------------------------- the checker

    void startCheck( bool wait = false )
    {
        if ( m_checking ) return;
        if ( m_thread.joinable() ) m_thread.join();
        std::error_code e;
        fs::path        dir = fs::temp_directory_path( e ) / "KipKepler-editor";
        fs::create_directories( dir, e );
        std::string tmp = ( dir / ( ( m_doc.m_id.empty() ? std::string( "level" ) : m_doc.m_id ) + ".txt" ) ).string();
        {
            std::ofstream out( tmp, std::ios::binary );
            out << m_doc.write();
        }
        m_report = true;
        m_reportScroll = 0;
        m_lines.clear();
        m_checking = true;
        m_checked = false;
        auto job = [this, tmp]()
        {
            Level       level;
            std::string error, report;
            std::vector<std::pair<int, int>> reach;
            if ( !level.load( tmp, error ) ) report = "ERROR " + error + "\n";
            else
            {
                checkLevel( level, "", report );
                // The places the hero can stand on (whatever keys and switches), for the overlay.
                ReachGraph graph;
                buildGraph( level, graph );
                std::set<std::pair<int, int>> cells;
                for ( const ReachNode &n : graph.m_nodes ) cells.insert( { n.m_fx, n.m_fy } );
                reach.assign( cells.begin(), cells.end() );
            }
            m_checkOut = report;
            m_reachOut = std::move( reach );
            m_checked = true;
        };
        if ( wait ) job();
        else
            m_thread = std::thread( job );
        pollCheck();
    }

    void pollCheck()
    {
        if ( !m_checking || !m_checked ) return;
        if ( m_thread.joinable() ) m_thread.join();
        m_checking = false;
        m_lines.clear();
        m_reach = std::move( m_reachOut );
        std::istringstream in( m_checkOut );
        std::string        l;
        while ( std::getline( in, l ) )
        {
            if ( l.empty() ) continue;
            ReportLine r;
            r.m_text = l;
            r.m_c = l.rfind( "ERROR", 0 ) == 0 || l.rfind( "FAIL", 0 ) == 0 ? Bad : l.rfind( "WARN", 0 ) == 0 ? Warn : l.rfind( "OK", 0 ) == 0 ? Good : Ink;
            size_t col = l.find( "column " ), row = l.find( ", row " );
            if ( col != std::string::npos && row != std::string::npos )
            {
                r.m_x = atoi( l.c_str() + col + 7 ) - 1;
                r.m_y = atoi( l.c_str() + row + 6 ) - 1;
            }
            m_lines.push_back( r );
        }
        // The summary first.
        std::stable_sort( m_lines.begin(), m_lines.end(), []( const ReportLine &a, const ReportLine &b )
                          { return ( a.m_text.rfind( "OK", 0 ) == 0 || a.m_text.rfind( "FAIL", 0 ) == 0 ) > ( b.m_text.rfind( "OK", 0 ) == 0 || b.m_text.rfind( "FAIL", 0 ) == 0 ); } );
        m_report = true;
        bool ok = !m_lines.empty() && m_lines[0].m_text.rfind( "OK", 0 ) == 0;
        message( tr( ok ? "editor.msg.check_ok" : "editor.msg.check_fail" ), ok ? Good : Bad );
    }

    // ----------------------------------------------------------------------------------------- the death map

    void toggleDeaths( const std::string &file = "" )
    {
        // The player's knockouts in this level (deaths.txt in the player's folder: level x y cause ...), per cell; the
        // view goes to the cell with the most.
        m_showDeaths = !m_showDeaths;
        m_deathMarks.clear();
        if ( !m_showDeaths )
        {
            message( tr( "editor.msg.deaths_off" ), Dim, 2 );
            return;
        }
        std::ifstream              in( file.empty() ? userDir() + "deaths.txt" : file );
        std::string                line;
        std::map<long, int>        cells;
        std::map<std::string, int> causes;
        int                        total = 0;
        while ( std::getline( in, line ) )
        {
            std::istringstream l( line );
            std::string        id, cause;
            int                x = 0, y = 0;
            if ( !( l >> id >> x >> y >> cause ) || id != m_doc.m_id || cause == "giveup" ) continue;
            int cx = (int)std::floor( x / T ), cy = (int)std::floor( ( y - 1 ) / T );
            ++cells[(long)cy * 100000 + cx], ++causes[cause], ++total;
        }
        for ( const auto &[k, n] : cells ) m_deathMarks.push_back( { (int)( k % 100000 ), (int)( k / 100000 ), n } );
        if ( !total )
        {
            message( tr( "editor.msg.deaths_none" ), Dim, 3 );
            return;
        }
        const DeathMark &worst =
            *std::max_element( m_deathMarks.begin(), m_deathMarks.end(),
                               []( const DeathMark &a, const DeathMark &b ) { return a.m_n < b.m_n; } );
        centreOn( worst.m_x * T + T / 2, worst.m_y * T + T / 2 );
        // The three most frequent causes.
        std::vector<std::pair<int, std::string>> top;
        for ( const auto &[c, n] : causes ) top.push_back( { n, c } );
        std::sort( top.rbegin(), top.rend() );
        std::string most;
        for ( size_t i = 0; i < top.size() && i < 3; ++i )
            most += ( i ? ", " : "" ) + top[i].second + " " + std::to_string( top[i].first );
        char buf[256];
        snprintf( buf, sizeof( buf ), tr( "editor.msg.deaths" ).c_str(), total, most.c_str() );
        message( buf, Warn, 5 );
    }

    // -------------------------------------------------------------------------------------------- the camera

    Rectangle mapArea() const
    {
        float w = (float)m_vw - ( m_palette ? PalW : 0 );
        float h = (float)m_vh - 2 * BarH - ( m_report ? ReportH + 4 : 0 );
        return { 0, (float)BarH, w, h };
    }

    void clampCamera()
    {
        float vw = m_vw / m_cam.m_zoom, vh = m_vh / m_cam.m_zoom;
        float lw = m_doc.m_w * T, lh = m_doc.m_h * T, margin = 3 * T;
        float right = margin + ( m_palette ? PalW / m_cam.m_zoom : 0 ), bottom = margin + ( m_report ? ( ReportH + 4 ) / m_cam.m_zoom : 0 );
        float top = margin + BarH / m_cam.m_zoom;
        if ( lw + margin + right <= vw ) m_cam.m_x = ( lw - vw + right - margin ) * 0.5f;
        else
            m_cam.m_x = std::clamp( m_cam.m_x, -margin, lw + right - vw );
        if ( lh + top + bottom <= vh ) m_cam.m_y = ( lh - vh + bottom - top ) * 0.5f;
        else
            m_cam.m_y = std::clamp( m_cam.m_y, -top, lh + bottom - vh );
    }

    void centreOn( float x, float y )
    {
        Rectangle a = mapArea();
        m_cam.m_x = x - ( a.x + a.width * 0.5f ) / m_cam.m_zoom;
        m_cam.m_y = y - ( a.y + a.height * 0.5f ) / m_cam.m_zoom;
        clampCamera();
    }

    void setZoom( int i, Vector2 at )
    {
        static const float zooms[3] = { 1.0f, 0.5f, 0.25f };
        i = std::clamp( i, 0, 2 );
        if ( i == m_zoomI ) return;
        Vector2 w = m_cam.toWorld( at.x, at.y );
        m_zoomI = i;
        m_cam.m_zoom = zooms[i];
        m_cam.m_x = w.x - at.x / m_cam.m_zoom;
        m_cam.m_y = w.y - at.y / m_cam.m_zoom;
        clampCamera();
    }

    Vector2 viewCentre() const
    {
        Rectangle a = mapArea();
        return { a.x + a.width * 0.5f, a.y + a.height * 0.5f };
    }

    /** @brief Pans so the pad's cursor stays two cells inside the view. */
    void keepCursorInView()
    {
        Rectangle a = mapArea();
        float     m = 2 * T * m_cam.m_zoom;
        Vector2   p = m_cam.toScreen( m_curX * T, m_curY * T );
        float     s = T * m_cam.m_zoom;
        if ( p.x < a.x + m ) m_cam.m_x -= ( a.x + m - p.x ) / m_cam.m_zoom;
        if ( p.x + s > a.x + a.width - m ) m_cam.m_x += ( p.x + s - ( a.x + a.width - m ) ) / m_cam.m_zoom;
        if ( p.y < a.y + m ) m_cam.m_y -= ( a.y + m - p.y ) / m_cam.m_zoom;
        if ( p.y + s > a.y + a.height - m ) m_cam.m_y += ( p.y + s - ( a.y + a.height - m ) ) / m_cam.m_zoom;
        clampCamera();
    }

    // ------------------------------------------------------------------------------------------------ layout

    Rectangle paletteRect() const { return { (float)m_vw - PalW, (float)BarH + 1, (float)PalW, (float)m_vh - 2 * BarH - 2 }; }
    Rectangle tabRect( int i ) const
    {
        // As wide as their names, the room left shared out.
        Rectangle p = paletteRect();
        float     w[5], sum = 0;
        for ( int k = 0; k < 5; ++k ) w[k] = (float)txtW( tr( CatKeys[k] ) ) + 6, sum += w[k];
        float extra = std::max( 0.0f, ( p.width - 8 - 4 * 2 - sum ) / 5 ), x = p.x + 4;
        for ( int k = 0; k < i; ++k ) x += w[k] + extra + 2;
        return { std::floor( x ), p.y + 4, std::floor( w[i] + extra ), 14 };
    }
    Rectangle cellRect( int i ) const
    {
        Rectangle p = paletteRect();
        return { p.x + 6 + ( i % 6 ) * 34.0f, p.y + 22 + ( i / 6 ) * 34.0f, 32, 32 };
    }
    float infoTop() const
    {
        int rows = ( (int)m_items[m_cat].size() + 5 ) / 6;
        return paletteRect().y + 22 + rows * 34.0f + 2;
    }
    Rectangle reportRect() const
    {
        float w = (float)m_vw - 8 - ( m_palette ? PalW : 0 );
        return { 4, (float)m_vh - BarH - 4 - ReportH, w, (float)ReportH };
    }
    Rectangle menuRect() const
    {
        float h = 7 * 16.0f + 34;
        return { m_vw * 0.5f - 120, std::floor( m_vh * 0.5f - h * 0.5f ), 240, h };
    }
    Rectangle settingsRect() const
    {
        float h = 14 * 15.0f + 40;
        return { m_vw * 0.5f - 190, std::floor( m_vh * 0.5f - h * 0.5f ), 380, h };
    }
    Rectangle settingsRow( int r ) const
    {
        Rectangle d = settingsRect();
        return { d.x + 6, d.y + 24 + r * 15.0f, d.width - 12, 14 };
    }
    Rectangle fieldRect() const { return { m_vw * 0.5f - 200, std::floor( m_vh * 0.5f - 44 ), 400, 88 }; }
    /** @brief The field's OK and Cancel buttons (as wide as their words). */
    void fieldButtons( Rectangle &ok, Rectangle &no ) const
    {
        Rectangle f = fieldRect();
        float     wn = std::max( 54.0f, (float)txtW( tr( "editor.field.cancel" ) ) + 12 ), wo = std::max( 54.0f, (float)txtW( tr( "editor.field.ok" ) ) + 12 );
        no = { f.x + f.width - 8 - wn, f.y + f.height - 20, wn, 14 };
        ok = { no.x - 4 - wo, no.y, wo, 14 };
    }

    /** @brief The controls under the palette's grid for the chosen entry. */
    std::vector<Ctl> controls() const
    {
        std::vector<Ctl> out;
        if ( m_useRaw || m_items.empty() ) return out;
        const Item &it = m_items[m_brushCat][std::clamp( m_sel[m_brushCat], 0, (int)m_items[m_brushCat].size() - 1 )];
        Rectangle   p = paletteRect();
        float       y = infoTop() + 26;
        int         row = 0;
        if ( it.m_enemy )
        {
            float x = p.x + 6;
            for ( int k = 0; k < 4; ++k )
            {
                static const char *keys[4] = { "editor.flag.ambush", "editor.flag.left", "editor.flag.elite", "editor.flag.ceiling" };
                if ( k == 3 && !walkerKind( it.m_fixed ) ) continue;
                float w = (float)txtW( tr( keys[k] ) ) + 10;
                if ( x + w > p.x + p.width - 4 ) x = p.x + 6, y += 15, ++row;
                out.push_back( { k, row, { x, y, w, 13 } } );
                x += w + 3;
            }
            y += 15, ++row;
        }
        if ( it.m_group )
        {
            out.push_back( { 4, row, { p.x + 6, y, p.width - 12, 13 } } );
            y += 15, ++row;
        }
        if ( !it.m_kind.empty() && ( !it.m_args.empty() || !it.m_presets.empty() || !it.m_argsHint.empty() ) )
            out.push_back( { 5, row, { p.x + 6, y, p.width - 12, 13 } } );
        return out;
    }

    HoverE hoverAt( Vector2 p ) const
    {
        if ( m_mode != ModeE::EDIT ) return HoverE::DIALOG;
        if ( p.y < BarH || p.y >= m_vh - BarH ) return HoverE::BAR;
        if ( m_palette && inRect( p, paletteRect() ) ) return HoverE::PALETTE;
        if ( m_report && inRect( p, reportRect() ) ) return HoverE::REPORT;
        return HoverE::MAP;
    }

    // ----------------------------------------------------------------------------------------- the palette

    void selectItem( int cat, int i, bool ask = true )
    {
        m_cat = m_brushCat = cat;
        m_sel[cat] = std::clamp( i, 0, (int)m_items[cat].size() - 1 );
        m_padSel = m_sel[cat];
        m_useRaw = false;
        m_telePending = 0;
        m_pasting = false;
        Item &it = m_items[cat][m_sel[cat]];
        if ( it.m_ask && ask ) askArgs( cat, m_sel[cat] );
    }

    void askArgs( int cat, int i )
    {
        Item &it = m_items[cat][i];
        openField( nameOf( it ) + ": " + tr( it.m_argsHint ), it.m_args, it.m_presets,
                   [this, cat, i]( const std::string &s ) { m_items[cat][i].m_args = joinWords( words( s ) ); } );
    }

    void cyclePreset( Item &it, int dir )
    {
        if ( it.m_presets.empty() ) return;
        auto at = std::find( it.m_presets.begin(), it.m_presets.end(), it.m_args );
        int  i = at == it.m_presets.end() ? ( dir > 0 ? -1 : 0 ) : (int)( at - it.m_presets.begin() );
        i = ( i + dir + (int)it.m_presets.size() ) % (int)it.m_presets.size();
        it.m_args = it.m_presets[i];
    }

    /** @brief A control clicked or pressed: flags flip, the group and the words change. */
    void activate( const Ctl &c, int dir, bool edit )
    {
        Item &it = brush();
        switch ( c.m_kind )
        {
        case 0: m_ambush = !m_ambush; break;
        case 1: m_left = !m_left; break;
        case 2: m_elite = !m_elite; break;
        case 3: m_ceiling = !m_ceiling; break;
        case 4: m_group = ( m_group + ( dir ? dir : 1 ) + 8 ) % 8; break;
        case 5:
            if ( edit ) askArgs( m_brushCat, m_sel[m_brushCat] );
            else
                cyclePreset( it, dir ? dir : 1 );
            break;
        default: break;
        }
    }

    void paletteClick()
    {
        for ( int i = 0; i < 5; ++i )
            if ( inRect( m_mouse, tabRect( i ) ) )
            {
                m_cat = i;
                return;
            }
        for ( int i = 0; i < (int)m_items[m_cat].size(); ++i )
            if ( inRect( m_mouse, cellRect( i ) ) )
            {
                selectItem( m_cat, i );
                return;
            }
        for ( const Ctl &c : controls() )
            if ( inRect( m_mouse, c.m_r ) )
            {
                if ( c.m_kind == 4 ) activate( c, m_mouse.x < c.m_r.x + c.m_r.width * 0.5f ? -1 : 1, false );
                else if ( c.m_kind == 5 )
                {
                    bool arrows = !brush().m_presets.empty() && m_mouse.x > c.m_r.x + c.m_r.width - 26;
                    activate( c, m_mouse.x > c.m_r.x + c.m_r.width - 13 ? 1 : -1, !arrows );
                }
                else
                    activate( c, 0, false );
                return;
            }
    }

    // ------------------------------------------------------------------------------------------------- input

    int pad() const
    {
        for ( int i = 0; i < 4; ++i )
            if ( IsGamepadAvailable( i ) ) return i;
        return -1;
    }

    /** @brief The pad's direction this frame with key repeat (stick or d-pad): -1, 0, 1 each. */
    void padDir( float dt, int &dx, int &dy )
    {
        dx = dy = 0;
        int p = pad();
        if ( p < 0 ) return;
        float ax = GetGamepadAxisMovement( p, GAMEPAD_AXIS_LEFT_X ), ay = GetGamepadAxisMovement( p, GAMEPAD_AXIS_LEFT_Y );
        int   hx = ( ax < -0.5f || IsGamepadButtonDown( p, GAMEPAD_BUTTON_LEFT_FACE_LEFT ) ) ? -1 : ( ax > 0.5f || IsGamepadButtonDown( p, GAMEPAD_BUTTON_LEFT_FACE_RIGHT ) ) ? 1 : 0;
        int   hy = ( ay < -0.5f || IsGamepadButtonDown( p, GAMEPAD_BUTTON_LEFT_FACE_UP ) ) ? -1 : ( ay > 0.5f || IsGamepadButtonDown( p, GAMEPAD_BUTTON_LEFT_FACE_DOWN ) ) ? 1 : 0;
        int   dir = ( hx + 1 ) * 3 + hy + 1;
        bool  fire = false;
        if ( dir != m_heldDir )
        {
            m_heldDir = dir;
            m_repeatT = 0.28f;
            fire = dir != 4;
        }
        else if ( dir != 4 )
        {
            m_repeatT -= dt;
            if ( m_repeatT <= 0 )
            {
                m_repeatT = std::max( std::fabs( ax ), std::fabs( ay ) ) > 0.95f ? 0.035f : 0.07f;
                fire = true;
            }
        }
        if ( fire ) dx = hx, dy = hy, m_pad = true;
    }

    /** @brief Keyboard and pad for lists: up/down, left/right, ok, back (with repeat). */
    void listKeys( float dt, int &dy, int &dx, bool &ok, bool &back )
    {
        int px = 0, py = 0;
        padDir( dt, px, py );
        dy = py, dx = px;
        if ( IsKeyPressed( KEY_UP ) || IsKeyPressedRepeat( KEY_UP ) || IsKeyPressed( KEY_W ) ) dy = -1;
        if ( IsKeyPressed( KEY_DOWN ) || IsKeyPressedRepeat( KEY_DOWN ) || IsKeyPressed( KEY_S ) ) dy = 1;
        if ( IsKeyPressed( KEY_LEFT ) || IsKeyPressedRepeat( KEY_LEFT ) || IsKeyPressed( KEY_A ) ) dx = -1;
        if ( IsKeyPressed( KEY_RIGHT ) || IsKeyPressedRepeat( KEY_RIGHT ) || IsKeyPressed( KEY_D ) ) dx = 1;
        int p = pad();
        ok = IsKeyPressed( KEY_ENTER ) || IsKeyPressed( KEY_KP_ENTER ) || IsKeyPressed( KEY_SPACE ) || ( p >= 0 && IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_DOWN ) );
        back = IsKeyPressed( KEY_ESCAPE ) || ( p >= 0 && IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT ) );
    }

    void readMouse()
    {
        int   ww = std::max( 1, GetRenderWidth() ), wh = std::max( 1, GetRenderHeight() );
        m_vw = 640;
        m_vh = (float)ww / wh < 1.7f ? 400 : 360;
        float s = (float)std::max( 1, std::min( ww / m_vw, wh / m_vh ) );
        if ( ww < m_vw || wh < m_vh ) s = std::min( (float)ww / m_vw, (float)wh / m_vh );
        float   ox = std::floor( ( ww - m_vw * s ) / 2 ), oy = std::floor( ( wh - m_vh * s ) / 2 );
        Vector2 m = GetMousePosition();
        float   kx = GetScreenWidth() > 0 ? (float)ww / GetScreenWidth() : 1, ky = GetScreenHeight() > 0 ? (float)wh / GetScreenHeight() : 1;
        Vector2 v = { ( m.x * kx - ox ) / s, ( m.y * ky - oy ) / s };
        m_delta = { v.x - m_mouse.x, v.y - m_mouse.y };
        if ( std::fabs( m_delta.x ) + std::fabs( m_delta.y ) > 0.5f && m_mouse.x > -50 ) m_pad = false;
        if ( IsMouseButtonPressed( MOUSE_BUTTON_LEFT ) || IsMouseButtonPressed( MOUSE_BUTTON_RIGHT ) ) m_pad = false;
        m_mouse = v;
    }

    void openField( const std::string &title, const std::string &text, const std::vector<std::string> &presets,
                    std::function<void( const std::string & )> ok )
    {
        if ( m_mode != ModeE::FIELD ) m_fieldBack = m_mode;
        m_mode = ModeE::FIELD;
        m_fieldTitle = title;
        m_fieldText = text;
        m_fieldPresets = presets;
        m_fieldPreset = -1;
        for ( size_t i = 0; i < presets.size(); ++i )
            if ( presets[i] == text ) m_fieldPreset = (int)i;
        m_fieldOk = std::move( ok );
        while ( GetCharPressed() ) {}
    }

    void updateField( float dt )
    {
        int cp;
        while ( ( cp = GetCharPressed() ) > 0 )
            if ( cp >= 32 && m_fieldText.size() < 120 ) m_fieldText += utf8( cp );
        if ( IsKeyPressed( KEY_BACKSPACE ) || IsKeyPressedRepeat( KEY_BACKSPACE ) ) popUtf8( m_fieldText );
        if ( ( IsKeyDown( KEY_LEFT_CONTROL ) || IsKeyDown( KEY_RIGHT_CONTROL ) ) && IsKeyPressed( KEY_V ) )
        {
            const char *clip = GetClipboardText();
            if ( clip ) m_fieldText += std::string( clip ).substr( 0, 120 );
        }
        int px = 0, py = 0;
        padDir( dt, px, py );
        int step = py ? py : px;
        if ( IsKeyPressed( KEY_UP ) || IsKeyPressedRepeat( KEY_UP ) ) step = -1;
        if ( IsKeyPressed( KEY_DOWN ) || IsKeyPressedRepeat( KEY_DOWN ) ) step = 1;
        if ( step && !m_fieldPresets.empty() )
        {
            int n = (int)m_fieldPresets.size();
            m_fieldPreset = m_fieldPreset < 0 ? ( step > 0 ? 0 : n - 1 ) : ( m_fieldPreset + step + n ) % n;
            m_fieldText = m_fieldPresets[m_fieldPreset];
        }
        int  p = pad();
        bool ok = IsKeyPressed( KEY_ENTER ) || IsKeyPressed( KEY_KP_ENTER ) || ( p >= 0 && IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_DOWN ) );
        bool back = IsKeyPressed( KEY_ESCAPE ) || ( p >= 0 && IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT ) );
        Rectangle f = fieldRect();
        if ( IsMouseButtonPressed( MOUSE_BUTTON_LEFT ) )
        {
            Rectangle okR, noR;
            fieldButtons( okR, noR );
            if ( inRect( m_mouse, okR ) ) ok = true;
            else if ( inRect( m_mouse, noR ) || !inRect( m_mouse, f ) )
                back = true;
        }
        if ( ok )
        {
            m_mode = m_fieldBack;
            auto done = m_fieldOk;
            if ( done ) done( m_fieldText );
        }
        else if ( back )
            m_mode = m_fieldBack;
    }

    // ------------------------------------------------------------------------------------------------- menu

    Editor::ResultE updateMenu( float dt )
    {
        int  dy, dx;
        bool ok, back;
        listKeys( dt, dy, dx, ok, back );
        int p = pad();
        if ( p >= 0 && IsGamepadButtonPressed( p, GAMEPAD_BUTTON_MIDDLE_RIGHT ) ) back = true;
        m_menuI = ( m_menuI + dy + 7 ) % 7;
        Rectangle r = menuRect();
        for ( int i = 0; i < 7; ++i )
        {
            Rectangle row = { r.x + 6, r.y + 26 + i * 16.0f, r.width - 12, 15 };
            if ( inRect( m_mouse, row ) && ( std::fabs( m_delta.x ) + std::fabs( m_delta.y ) > 0 || IsMouseButtonPressed( MOUSE_BUTTON_LEFT ) ) ) m_menuI = i;
            if ( inRect( m_mouse, row ) && IsMouseButtonPressed( MOUSE_BUTTON_LEFT ) ) ok = true;
        }
        if ( IsMouseButtonPressed( MOUSE_BUTTON_LEFT ) && !inRect( m_mouse, r ) ) back = true;
        if ( back )
        {
            m_mode = ModeE::EDIT;
            return ResultE::STAY;
        }
        if ( !ok ) return ResultE::STAY;
        m_mode = ModeE::EDIT;
        switch ( m_menuI )
        {
        case 1: save(); break;
        case 2: startCheck(); break;
        case 3: return testPlay();
        case 4: openSettings(); break;
        case 5:
            if ( save() ) return ResultE::LEAVE;
            break;
        case 6: return ResultE::LEAVE;
        default: break;
        }
        return ResultE::STAY;
    }

    // --------------------------------------------------------------------------------------------- settings

    void openSettings()
    {
        m_mode = ModeE::SETTINGS;
        m_setI = 0;
    }

    std::string settingValue( int row ) const
    {
        switch ( row )
        {
        case 0: return m_doc.key( "name" );
        case 1: return m_doc.key( "name.de" );
        case 2: return m_doc.key( "theme", "station" );
        case 3: return m_doc.key( "tint", "0" );
        case 4: return m_doc.key( "bg", m_doc.key( "theme", "station" ) + "_a" );
        case 5: return m_doc.key( "music", "-" );
        case 6: return m_doc.key( "dark", "0" );
        case 7: return m_doc.key( "gravity", "1.0" );
        case 8: return m_doc.key( "par", "-" ) + ( m_doc.key( "par" ).empty() ? "" : " s" );
        case 9:
        case 10: return std::to_string( m_doc.m_w );
        case 11:
        case 12: return std::to_string( m_doc.m_h );
        default: return "";
        }
    }

    /** @brief Changes a setting one step. */
    void changeSetting( int row, int dir, bool big )
    {
        if ( !dir || row < 2 || row > 12 ) return;
        snapshot();
        auto cycle = [&]( const std::vector<std::string> &list, const std::string &now )
        {
            if ( list.empty() ) return now;
            auto it = std::find( list.begin(), list.end(), now );
            int  i = it == list.end() ? 0 : (int)( it - list.begin() );
            return list[( i + dir + (int)list.size() ) % (int)list.size()];
        };
        if ( row == 2 )
        {
            std::string old = m_doc.key( "theme", "station" );
            int         i = 0;
            for ( int k = 0; k < 8; ++k )
                if ( old == Themes[k] ) i = k;
            std::string next = Themes[( i + dir + 8 ) % 8];
            m_doc.setKey( "theme", next );
            // The background and the music follow when they were the old theme's own.
            std::string bg = m_doc.key( "bg" );
            if ( bg.empty() || bg.rfind( old + "_", 0 ) == 0 ) m_doc.setKey( "bg", next + ( bg.size() > old.size() + 1 ? bg.substr( old.size() ) : "_a" ) );
            std::string music = m_doc.key( "music" ), oldCue = "e" + std::to_string( episodeOf( old ) ) + "_" + old;
            if ( music.empty() || music == oldCue ) m_doc.setKey( "music", "e" + std::to_string( episodeOf( next ) ) + "_" + next );
            m_decosDirty = true;
        }
        else if ( row == 3 )
            m_doc.setKey( "tint", std::to_string( ( std::clamp( atoi( m_doc.key( "tint", "0" ).c_str() ), 0, 3 ) + dir + 4 ) % 4 ) );
        else if ( row == 4 )
            m_doc.setKey( "bg", cycle( m_bgs, m_doc.key( "bg", m_doc.key( "theme", "station" ) + "_a" ) ) );
        else if ( row == 5 )
        {
            std::string next = cycle( m_music, m_doc.key( "music" ) );
            m_doc.setKey( "music", next );
        }
        else if ( row == 6 )
            m_doc.setKey( "dark", fmtNum( std::clamp( std::round( ( (float)atof( m_doc.key( "dark", "0" ).c_str() ) + dir * 0.05f ) * 20 ) / 20, 0.0f, 0.9f ) ) );
        else if ( row == 7 )
            m_doc.setKey( "gravity", fmtNum( std::clamp( std::round( ( (float)atof( m_doc.key( "gravity", "1.0" ).c_str() ) + dir * 0.05f ) * 20 ) / 20, 0.3f, 2.0f ) ) );
        else if ( row == 8 )
            m_doc.setKey( "par", std::to_string( std::clamp( atoi( m_doc.key( "par", "240" ).c_str() ) + dir * ( big ? 60 : 10 ), 10, 3600 ) ) );
        else
        {
            int n = dir * ( big ? 5 : 1 );
            int l = row == 9 ? n : 0, r = row == 10 ? n : 0, t = row == 11 ? n : 0, b = row == 12 ? n : 0;
            int w = m_doc.m_w + l + r, h = m_doc.m_h + t + b;
            if ( w < 12 || h < 8 || w > 400 || h > 160 )
            {
                message( tr( "editor.msg.size_limit" ), Warn );
                m_undo.pop_back();
                return;
            }
            m_doc.resize( l, r, t, b );
            m_cam.m_x += l * T, m_cam.m_y += t * T;
            m_curX += l, m_curY += t;
            for ( ReportLine &rl : m_lines )
                if ( rl.m_x >= 0 ) rl.m_x += l, rl.m_y += t;
            m_hasSel = false;
            m_telePending = 0;
            m_decosDirty = true;
            clampCamera();
        }
        m_dirty = true;
    }

    void editSetting( int row )
    {
        if ( row == 13 )
        {
            m_mode = ModeE::EDIT;
            return;
        }
        if ( row > 1 )
        {
            changeSetting( row, 1, false );
            return;
        }
        const char *key = row == 0 ? "name" : "name.de";
        openField( tr( row == 0 ? "editor.set.name" : "editor.set.name_de" ), m_doc.key( key ), {},
                   [this, key]( const std::string &s )
                   {
                       snapshot();
                       std::string v = s;
                       while ( !v.empty() && v.back() == ' ' ) v.pop_back();
                       m_doc.setKey( key, v );
                   } );
    }

    void updateSettings( float dt )
    {
        int  dy, dx;
        bool ok, back;
        listKeys( dt, dy, dx, ok, back );
        bool big = IsKeyDown( KEY_LEFT_SHIFT ) || IsKeyDown( KEY_RIGHT_SHIFT );
        int  p = pad();
        if ( p >= 0 && IsGamepadButtonPressed( p, GAMEPAD_BUTTON_MIDDLE_RIGHT ) ) back = true;
        m_setI = ( m_setI + dy + 14 ) % 14;
        if ( dx ) changeSetting( m_setI, dx, big );
        if ( ok ) editSetting( m_setI );
        Rectangle d = settingsRect();
        for ( int r = 0; r < 14; ++r )
        {
            Rectangle row = settingsRow( r );
            if ( !inRect( m_mouse, row ) ) continue;
            if ( std::fabs( m_delta.x ) + std::fabs( m_delta.y ) > 0 ) m_setI = r;
            if ( !IsMouseButtonPressed( MOUSE_BUTTON_LEFT ) ) continue;
            m_setI = r;
            Rectangle leftR = { d.x + 150, row.y, 16, 14 }, rightR = { row.x + row.width - 16, row.y, 16, 14 };
            if ( inRect( m_mouse, leftR ) ) changeSetting( r, -1, big );
            else if ( inRect( m_mouse, rightR ) )
                changeSetting( r, 1, big );
            else
                editSetting( r );
        }
        if ( IsMouseButtonPressed( MOUSE_BUTTON_LEFT ) && !inRect( m_mouse, d ) ) back = true;
        float wheel = GetMouseWheelMove();
        if ( wheel != 0 && inRect( m_mouse, d ) ) changeSetting( m_setI, wheel > 0 ? 1 : -1, big );
        if ( back && m_mode == ModeE::SETTINGS ) m_mode = ModeE::EDIT;
    }

    // ------------------------------------------------------------------------------------------- editing input

    /** @brief Esc: cancels what is going on, else opens the menu. */
    void escape()
    {
        if ( m_pasting ) m_pasting = false;
        else if ( m_telePending )
        {
            m_telePending = 0;
            message( tr( "editor.msg.tele_cancel" ), Dim );
        }
        else if ( m_drag != DragE::NONE )
            m_drag = DragE::NONE;
        else if ( m_hasSel )
            m_hasSel = false;
        else if ( m_report && !m_checking )
            m_report = false;
        else
            m_mode = ModeE::MENU, m_menuI = 0;
    }

    void brushStep( int dir )
    {
        int n = (int)m_items[m_brushCat].size();
        selectItem( m_brushCat, ( ( m_useRaw ? 0 : m_sel[m_brushCat] ) + dir + n ) % n, false );
        message( nameOf( brush() ), Ink, 1.5f );
    }

    void updatePalettePad( float dt, int p )
    {
        if ( IsGamepadButtonPressed( p, GAMEPAD_BUTTON_LEFT_TRIGGER_1 ) ) m_cat = ( m_cat + 4 ) % 5, m_padSel = m_cat == m_brushCat ? m_sel[m_cat] : 0, m_palFocus = -1;
        if ( IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_TRIGGER_1 ) ) m_cat = ( m_cat + 1 ) % 5, m_padSel = m_cat == m_brushCat ? m_sel[m_cat] : 0, m_palFocus = -1;
        int dx, dy;
        padDir( dt, dx, dy );
        int              n = (int)m_items[m_cat].size(), &sel = m_padSel;
        std::vector<Ctl> ctl = controls();
        if ( m_palFocus >= (int)ctl.size() ) m_palFocus = -1;
        if ( m_palFocus < 0 )
        {
            sel = std::clamp( sel, 0, n - 1 );
            if ( dx ) sel = std::clamp( sel + dx, 0, n - 1 );
            if ( dy < 0 && sel >= 6 ) sel -= 6;
            if ( dy > 0 )
            {
                if ( sel + 6 < n ) sel += 6;
                else if ( ( sel / 6 ) < ( n - 1 ) / 6 )
                    sel = n - 1;
                else if ( !ctl.empty() )
                    m_palFocus = 0;
            }
            if ( IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_DOWN ) )
            {
                selectItem( m_cat, sel );
                m_palette = false;
            }
        }
        else
        {
            const Ctl &c = ctl[m_palFocus];
            if ( dy )
            {
                int want = c.m_row + dy, found = -1;
                for ( size_t i = 0; i < ctl.size(); ++i )
                    if ( ctl[i].m_row == want )
                    {
                        found = (int)i;
                        break;
                    }
                m_palFocus = found >= 0 ? found : dy < 0 ? -1 : m_palFocus;
            }
            else if ( dx )
            {
                int next = m_palFocus + dx;
                if ( next >= 0 && next < (int)ctl.size() && ctl[next].m_row == c.m_row ) m_palFocus = next;
                else if ( c.m_kind >= 4 )
                    activate( c, dx, false );
            }
            if ( IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_DOWN ) && m_palFocus >= 0 ) activate( ctl[m_palFocus], 1, true );
        }
        if ( IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT ) ) m_palette = false;
    }

    void updatePad( float dt )
    {
        int p = pad();
        if ( p < 0 ) return;
        // Any touch of the pad hands the cursor (and an open palette) to it.
        if ( GetGamepadButtonPressed() != GAMEPAD_BUTTON_UNKNOWN || std::fabs( GetGamepadAxisMovement( p, GAMEPAD_AXIS_LEFT_X ) ) > 0.5f ||
             std::fabs( GetGamepadAxisMovement( p, GAMEPAD_AXIS_LEFT_Y ) ) > 0.5f )
            m_pad = true;
        if ( m_pad && !m_padWas ) m_padSel = m_cat == m_brushCat ? m_sel[m_cat] : 0;
        m_padWas = m_pad;
        if ( m_pad && !inside( m_curX, m_curY ) )
        {
            Vector2 c = viewCentre(), w = m_cam.toWorld( c.x, c.y );
            m_curX = std::clamp( (int)( w.x / T ), 0, m_doc.m_w - 1 ), m_curY = std::clamp( (int)( w.y / T ), 0, m_doc.m_h - 1 );
        }
        auto pressed = [&]( int b )
        {
            bool r = IsGamepadButtonPressed( p, b );
            if ( r ) m_pad = true;
            return r;
        };
        if ( pressed( GAMEPAD_BUTTON_MIDDLE_RIGHT ) )
        {
            m_mode = ModeE::MENU, m_menuI = 0;
            return;
        }
        if ( pressed( GAMEPAD_BUTTON_MIDDLE_LEFT ) )
        {
            if ( m_report && !m_checking ) m_report = false;
            else
                startCheck();
        }
        if ( pressed( GAMEPAD_BUTTON_RIGHT_FACE_LEFT ) || pressed( GAMEPAD_BUTTON_RIGHT_FACE_UP ) )
        {
            m_palette = !m_palette;
            m_palFocus = -1;
            m_cat = m_brushCat;
            m_padSel = m_sel[m_cat];
            clampCamera();
        }
        if ( pressed( GAMEPAD_BUTTON_LEFT_TRIGGER_2 ) ) setZoom( m_zoomI + 1, m_cam.toScreen( m_curX * T + T / 2, m_curY * T + T / 2 ) );
        if ( pressed( GAMEPAD_BUTTON_RIGHT_TRIGGER_2 ) ) setZoom( m_zoomI - 1, m_cam.toScreen( m_curX * T + T / 2, m_curY * T + T / 2 ) );
        // The right stick pans.
        float rx = GetGamepadAxisMovement( p, GAMEPAD_AXIS_RIGHT_X ), ry = GetGamepadAxisMovement( p, GAMEPAD_AXIS_RIGHT_Y );
        if ( std::fabs( rx ) > 0.25f || std::fabs( ry ) > 0.25f )
        {
            m_cam.m_x += rx * 700 * dt / m_cam.m_zoom, m_cam.m_y += ry * 700 * dt / m_cam.m_zoom;
            clampCamera();
            m_pad = true;
        }
        if ( m_palette && m_pad )
        {
            updatePalettePad( dt, p );
            return;
        }
        if ( pressed( GAMEPAD_BUTTON_LEFT_TRIGGER_1 ) ) brushStep( -1 );
        if ( pressed( GAMEPAD_BUTTON_RIGHT_TRIGGER_1 ) ) brushStep( 1 );
        int dx, dy;
        padDir( dt, dx, dy );
        if ( dx || dy )
        {
            int nx = std::clamp( m_curX + dx, 0, m_doc.m_w - 1 ), ny = std::clamp( m_curY + dy, 0, m_doc.m_h - 1 );
            if ( m_drag == DragE::PAD_PAINT ) line( m_curX, m_curY, nx, ny, false );
            if ( m_drag == DragE::PAD_ERASE ) line( m_curX, m_curY, nx, ny, true );
            m_curX = nx, m_curY = ny;
            keepCursorInView();
        }
        if ( pressed( GAMEPAD_BUTTON_RIGHT_FACE_DOWN ) )
        {
            if ( m_pasting ) pasteAt( m_curX, m_curY );
            else if ( brush().m_stamp || brush().m_tool != ToolE::PAINT )
            {
                begin();
                stamp( m_curX, m_curY );
            }
            else
            {
                begin();
                m_strokeChar = brushChar();
                if ( m_strokeChar ) m_drag = DragE::PAD_PAINT, put( m_curX, m_curY, m_strokeChar );
            }
        }
        if ( pressed( GAMEPAD_BUTTON_RIGHT_FACE_RIGHT ) )
        {
            if ( m_pasting ) m_pasting = false;
            else if ( m_telePending )
                m_telePending = 0;
            else
            {
                begin();
                m_drag = DragE::PAD_ERASE;
                put( m_curX, m_curY, eraseChar( m_curX, m_curY, true ) );
            }
        }
        if ( m_drag == DragE::PAD_PAINT && !IsGamepadButtonDown( p, GAMEPAD_BUTTON_RIGHT_FACE_DOWN ) ) m_drag = DragE::NONE;
        if ( m_drag == DragE::PAD_ERASE && !IsGamepadButtonDown( p, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT ) ) m_drag = DragE::NONE;
    }

    Editor::ResultE updateEdit( float dt )
    {
        bool   ctrl = IsKeyDown( KEY_LEFT_CONTROL ) || IsKeyDown( KEY_RIGHT_CONTROL );
        bool   shift = IsKeyDown( KEY_LEFT_SHIFT ) || IsKeyDown( KEY_RIGHT_SHIFT );
        bool   alt = IsKeyDown( KEY_LEFT_ALT ) || IsKeyDown( KEY_RIGHT_ALT );
        HoverE hover = hoverAt( m_mouse );
        if ( GetKeyPressed() ) m_pad = false;

        // The cursor's cell: under the mouse, or where the pad moved it.
        if ( !m_pad )
        {
            Vector2 w = m_cam.toWorld( m_mouse.x, m_mouse.y );
            m_curX = (int)std::floor( w.x / T ), m_curY = (int)std::floor( w.y / T );
            m_curOn = hover == HoverE::MAP;
        }
        else
            m_curOn = true;

        // Keys.
        if ( IsKeyPressed( KEY_ESCAPE ) )
        {
            escape();
            return ResultE::STAY;
        }
        if ( IsKeyPressed( KEY_F9 ) ) return testPlay();
        if ( IsKeyPressed( KEY_F5 ) ) startCheck();
        if ( IsKeyPressed( KEY_F2 ) )
        {
            openSettings();
            return ResultE::STAY;
        }
        if ( IsKeyPressed( KEY_F1 ) )
        {
            m_mode = ModeE::HELP;
            return ResultE::STAY;
        }
        if ( IsKeyPressed( KEY_F3 ) ) m_decos = !m_decos;
        if ( IsKeyPressed( KEY_H ) ) toggleDeaths();
        if ( IsKeyPressed( KEY_R ) )
            m_showReach = !m_showReach,
            message( tr( m_showReach ? "editor.msg.reach_on" : "editor.msg.reach_off" ), Dim, 2 );
        if ( IsKeyPressed( KEY_F4 ) ) m_light = !m_light, message( tr( m_light ? "editor.msg.light_on" : "editor.msg.light_off" ), Dim, 2 );
        if ( IsKeyPressed( KEY_TAB ) ) m_palette = !m_palette, clampCamera();
        if ( ctrl )
        {
            if ( IsKeyPressed( KEY_Z ) || IsKeyPressedRepeat( KEY_Z ) ) undo( !shift );
            if ( IsKeyPressed( KEY_Y ) || IsKeyPressedRepeat( KEY_Y ) ) undo( false );
            if ( IsKeyPressed( KEY_S ) ) save();
            if ( IsKeyPressed( KEY_C ) ) copy( false );
            if ( IsKeyPressed( KEY_X ) ) copy( true );
            if ( IsKeyPressed( KEY_V ) )
            {
                if ( m_clip.m_w > 0 ) m_pasting = true, m_hasSel = false;
                else
                    message( tr( "editor.msg.clip_empty" ), Dim );
            }
        }
        else
        {
            if ( IsKeyPressed( KEY_G ) ) m_grid = !m_grid;
            if ( IsKeyPressed( KEY_C ) ) m_showChars = !m_showChars;
            if ( IsKeyPressed( KEY_Z ) ) setZoom( ( m_zoomI + 1 ) % 3, hover == HoverE::MAP ? m_mouse : viewCentre() );
            if ( IsKeyPressed( KEY_Q ) ) pick( m_curX, m_curY );
            if ( IsKeyPressed( KEY_F ) ) flood( m_curX, m_curY );
            if ( IsKeyPressed( KEY_LEFT_BRACKET ) ) brushStep( -1 );
            if ( IsKeyPressed( KEY_RIGHT_BRACKET ) ) brushStep( 1 );
            for ( int k = 0; k < 5; ++k )
                if ( IsKeyPressed( KEY_ONE + k ) ) m_cat = k, m_palette = true;
            if ( IsKeyPressed( KEY_DELETE ) || IsKeyPressed( KEY_BACKSPACE ) )
            {
                begin();
                if ( m_hasSel )
                {
                    normaliseSel();
                    fillRect( m_sx0, m_sy0, m_sx1, m_sy1, true );
                }
                else
                    put( m_curX, m_curY, eraseChar( m_curX, m_curY, true ) );
            }
            // Panning with the keys.
            float sp = ( shift ? 1600.0f : 650.0f ) * dt / m_cam.m_zoom;
            if ( IsKeyDown( KEY_LEFT ) || IsKeyDown( KEY_A ) ) m_cam.m_x -= sp;
            if ( IsKeyDown( KEY_RIGHT ) || IsKeyDown( KEY_D ) ) m_cam.m_x += sp;
            if ( IsKeyDown( KEY_UP ) || IsKeyDown( KEY_W ) ) m_cam.m_y -= sp;
            if ( IsKeyDown( KEY_DOWN ) || IsKeyDown( KEY_S ) ) m_cam.m_y += sp;
        }

        // The wheel: zoom over the map, the category over the palette, scrolling over the report.
        float wheel = GetMouseWheelMove();
        if ( wheel != 0 )
        {
            int step = wheel > 0 ? 1 : -1;
            if ( hover == HoverE::MAP ) setZoom( m_zoomI - step, m_mouse );
            else if ( hover == HoverE::PALETTE )
                m_cat = ( m_cat - step + 5 ) % 5;
            else if ( hover == HoverE::REPORT )
                m_reportScroll = std::clamp( m_reportScroll - step, 0, std::max( 0, (int)m_lines.size() - 7 ) );
        }

        // The left button.
        bool in = inside( m_curX, m_curY );
        if ( IsMouseButtonPressed( MOUSE_BUTTON_LEFT ) )
        {
            if ( hover == HoverE::PALETTE ) paletteClick();
            else if ( hover == HoverE::REPORT )
                reportClick();
            else if ( hover == HoverE::MAP )
            {
                if ( m_pasting )
                {
                    if ( in ) pasteAt( m_curX, m_curY );
                }
                else if ( alt )
                    pick( m_curX, m_curY );
                else if ( ctrl )
                {
                    m_drag = DragE::SELECT;
                    m_hasSel = true;
                    m_sx0 = m_sx1 = m_curX, m_sy0 = m_sy1 = m_curY;
                }
                else if ( shift && !brush().m_stamp && brush().m_tool == ToolE::PAINT )
                    m_drag = DragE::RECT, m_dragX = m_curX, m_dragY = m_curY;
                else if ( brush().m_stamp || brush().m_tool != ToolE::PAINT )
                {
                    begin();
                    stamp( m_curX, m_curY );
                }
                else
                {
                    begin();
                    m_strokeChar = brushChar();
                    if ( m_strokeChar )
                    {
                        m_drag = DragE::PAINT;
                        put( m_curX, m_curY, m_strokeChar );
                        m_lastX = m_curX, m_lastY = m_curY;
                    }
                }
            }
        }
        if ( m_drag == DragE::PAINT && ( m_curX != m_lastX || m_curY != m_lastY ) )
        {
            line( m_lastX, m_lastY, m_curX, m_curY, false );
            m_lastX = m_curX, m_lastY = m_curY;
        }
        if ( m_drag == DragE::SELECT ) m_sx1 = m_curX, m_sy1 = m_curY;
        if ( IsMouseButtonReleased( MOUSE_BUTTON_LEFT ) )
        {
            if ( m_drag == DragE::RECT )
            {
                begin();
                fillRect( m_dragX, m_dragY, m_curX, m_curY, false );
            }
            if ( m_drag == DragE::SELECT )
            {
                normaliseSel();
                message( tr( "editor.msg.selected" ) + " " + std::to_string( m_sx1 - m_sx0 + 1 ) + "x" + std::to_string( m_sy1 - m_sy0 + 1 ), Dim, 2.5f );
            }
            if ( m_drag == DragE::PAINT || m_drag == DragE::RECT || m_drag == DragE::SELECT ) m_drag = DragE::NONE;
        }

        // The right button: a click erases, a drag pans; Shift erases a rectangle.
        if ( IsMouseButtonPressed( MOUSE_BUTTON_RIGHT ) && hover == HoverE::MAP && m_drag == DragE::NONE )
        {
            if ( m_pasting ) m_pasting = false;
            else if ( m_telePending )
            {
                m_telePending = 0;
                message( tr( "editor.msg.tele_cancel" ), Dim );
            }
            else if ( shift )
                m_drag = DragE::ERASE_RECT, m_dragX = m_curX, m_dragY = m_curY;
            else
                m_drag = DragE::RIGHT, m_rightAt = m_mouse, m_rightPanned = false, m_dragX = m_curX, m_dragY = m_curY;
        }
        if ( m_drag == DragE::RIGHT && IsMouseButtonDown( MOUSE_BUTTON_RIGHT ) )
        {
            if ( !m_rightPanned && std::fabs( m_mouse.x - m_rightAt.x ) + std::fabs( m_mouse.y - m_rightAt.y ) > 4 ) m_rightPanned = true;
            if ( m_rightPanned ) m_cam.m_x -= m_delta.x / m_cam.m_zoom, m_cam.m_y -= m_delta.y / m_cam.m_zoom;
        }
        if ( IsMouseButtonReleased( MOUSE_BUTTON_RIGHT ) )
        {
            if ( m_drag == DragE::RIGHT && !m_rightPanned )
            {
                begin();
                put( m_dragX, m_dragY, eraseChar( m_dragX, m_dragY, true ) );
            }
            if ( m_drag == DragE::ERASE_RECT )
            {
                begin();
                fillRect( m_dragX, m_dragY, m_curX, m_curY, true );
            }
            if ( m_drag == DragE::RIGHT || m_drag == DragE::ERASE_RECT ) m_drag = DragE::NONE;
        }
        // The middle button pans.
        if ( IsMouseButtonPressed( MOUSE_BUTTON_MIDDLE ) && hover == HoverE::MAP && m_drag == DragE::NONE ) m_drag = DragE::PAN;
        if ( m_drag == DragE::PAN )
        {
            if ( IsMouseButtonDown( MOUSE_BUTTON_MIDDLE ) ) m_cam.m_x -= m_delta.x / m_cam.m_zoom, m_cam.m_y -= m_delta.y / m_cam.m_zoom;
            else
                m_drag = DragE::NONE;
        }

        updatePad( dt );
        if ( m_mode == ModeE::EDIT ) clampCamera();
        return ResultE::STAY;
    }

    void reportClick()
    {
        Rectangle r = reportRect();
        if ( inRect( m_mouse, { r.x + r.width - 16, r.y + 2, 14, 12 } ) )
        {
            if ( !m_checking ) m_report = false;
            return;
        }
        int i = m_reportScroll + (int)std::floor( ( m_mouse.y - ( r.y + 16 ) ) / 12 );
        if ( m_mouse.y < r.y + 16 || i < 0 || i >= (int)m_lines.size() ) return;
        const ReportLine &l = m_lines[i];
        if ( l.m_x < 0 ) return;
        m_flashX = l.m_x, m_flashY = l.m_y, m_flashT = 2.5f;
        centreOn( l.m_x * T + T / 2, l.m_y * T + T / 2 );
    }

    /** @brief KEPLER_EDITOR_SHOT (test pictures): comma-separated states, applied on the first frame. */
    void applyDemo()
    {
        if ( m_demo.empty() ) return;
        std::string d = m_demo;
        m_demo.clear();
        for ( char &c : d )
            if ( c == ',' ) c = ' ';
        for ( const std::string &w : words( d ) )
        {
            size_t      eq = w.find( '=' );
            std::string k = w.substr( 0, eq ), v = eq == std::string::npos ? "" : w.substr( eq + 1 );
            if ( k == "cat" ) m_cat = m_brushCat = std::clamp( atoi( v.c_str() ), 0, 4 );
            else if ( k == "sel" )
                m_sel[m_cat] = atoi( v.c_str() ), m_brushCat = m_cat, m_padSel = m_sel[m_cat];
            else if ( k == "nopalette" )
                m_palette = false;
            else if ( k == "zoom" )
                setZoom( atoi( v.c_str() ), viewCentre() );
            else if ( k == "nogrid" )
                m_grid = false;
            else if ( k == "chars" )
                m_showChars = true;
            else if ( k == "light" )
                m_light = true;
            else if ( k == "settings" )
                openSettings();
            else if ( k == "menu" )
                m_mode = ModeE::MENU;
            else if ( k == "help" )
                m_mode = ModeE::HELP;
            else if ( k == "check" )
                startCheck( true );
            else if ( k == "field" )
                askArgs( m_brushCat, m_sel[m_brushCat] );
            else if ( k == "cursor" )
            {
                m_pad = true;
                m_curX = atoi( v.c_str() );
                size_t c = v.find( ':' );
                m_curY = c == std::string::npos ? m_curY : atoi( v.c_str() + c + 1 );
                centreOn( m_curX * T, m_curY * T );
            }
            else if ( k == "cam" )
            {
                size_t c = v.find( ':' );
                centreOn( atoi( v.c_str() ) * T, ( c == std::string::npos ? 0 : atoi( v.c_str() + c + 1 ) ) * T );
            }
            else if ( k == "paint" )
            {
                // paint=x:y — one stroke of the brush there (tests of the painting).
                size_t c = v.find( ':' );
                int    x = atoi( v.c_str() ), y = c == std::string::npos ? 0 : atoi( v.c_str() + c + 1 );
                begin();
                if ( brush().m_stamp || brush().m_tool != ToolE::PAINT ) stamp( x, y );
                else
                    m_strokeChar = brushChar(), put( x, y, m_strokeChar );
            }
            else if ( k == "save" )
                save();
            else if ( k == "set" )
            {
                // set=row:step — one step of a level setting (rows as in the dialog).
                size_t c = v.find( ':' );
                changeSetting( atoi( v.c_str() ), c == std::string::npos ? 1 : atoi( v.c_str() + c + 1 ), false );
            }
            else if ( k == "undo" )
                undo( true );
            else if ( k == "redo" )
                undo( false );
            else if ( k == "rect" )
            {
                // rect=x0:y0:x1:y1 — a rectangle of the brush.
                int v4[4] = { 0, 0, 0, 0 }, n = 0;
                for ( const char *c = v.c_str(); *c && n < 4; ++n )
                {
                    v4[n] = atoi( c );
                    while ( *c && *c != ':' ) ++c;
                    if ( *c ) ++c;
                }
                begin();
                fillRect( v4[0], v4[1], v4[2], v4[3], false );
            }
        }
    }

    // ================================================================================================= drawing

    void drawItemIcon( const Item &it, Rectangle r, float alpha = 1 )
    {
        std::string    theme = m_doc.key( "theme", "station" );
        const TileSet &ts = assets().tiles( theme );
        Color          tint = ColorAlpha( ts.m_tints[std::clamp( atoi( m_doc.key( "tint", "0" ).c_str() ), 0, 3 )], alpha );
        Color          white = ColorAlpha( WHITE, alpha );
        float          cx = r.x + r.width / 2, cy = r.y + r.height / 2;
        if ( it.m_look )
        {
            drawCellLook( ts, tint, it.m_look, r.x, r.y, r.width, m_clock );
            if ( it.m_look == 'X' ) txt( "X", cx - 3, cy - 6, ColorAlpha( Gold, alpha ) );
            if ( it.m_look == '?' ) txt( "?", cx - 3, cy - 6, ColorAlpha( { 230, 190, 255, 255 }, alpha ) );
            if ( it.m_group ) txt( std::string( 1, (char)( 'A' + m_group ) ), r.x + 2, r.y + 1, ColorAlpha( Gold, alpha ) );
            return;
        }
        if ( it.m_id == "light" )
        {
            std::vector<std::string> w = words( it.m_args );
            Color                    c = lightColour( w.empty() ? "" : w[0] );
            DrawCircle( (int)cx, (int)cy, 10, ColorAlpha( c, 0.25f * alpha ) );
            DrawCircle( (int)cx, (int)cy, 5, ColorAlpha( c, alpha ) );
            DrawCircle( (int)cx - 1, (int)cy - 1, 2, ColorAlpha( WHITE, alpha ) );
            return;
        }
        if ( it.m_id == "mover_h" || it.m_id == "mover_v" )
        {
            if ( ts.m_platform.id )
            {
                DrawTexturePro( ts.m_platform, { 32, 0, 32, 32 }, { r.x, cy - 8, 16, 16 }, { 0, 0 }, 0, tint );
                DrawTexturePro( ts.m_platform, { 96, 0, 32, 32 }, { r.x + 16, cy - 8, 16, 16 }, { 0, 0 }, 0, tint );
            }
            else
                DrawRectangle( (int)r.x, (int)cy - 4, (int)r.width, 6, ColorAlpha( { 200, 200, 120, 255 }, alpha ) );
            Color a = ColorAlpha( { 120, 220, 255, 255 }, alpha );
            if ( it.m_id == "mover_h" )
                DrawLineEx( { r.x + 4, r.y + 6 }, { r.x + r.width - 4, r.y + 6 }, 1, a ), DrawTriangle( { r.x + r.width - 2, r.y + 6 }, { r.x + r.width - 7, r.y + 3 }, { r.x + r.width - 7, r.y + 9 }, a );
            else
                DrawLineEx( { r.x + r.width - 5, r.y + 3 }, { r.x + r.width - 5, cy + 6 }, 1, a ), DrawTriangle( { r.x + r.width - 5, r.y + 1 }, { r.x + r.width - 8, r.y + 6 }, { r.x + r.width - 2, r.y + 6 }, a );
            return;
        }
        if ( it.m_id == "crusher" )
        {
            DrawRectangle( (int)cx - 3, (int)r.y, 6, 8, ColorAlpha( { 70, 74, 90, 255 }, alpha ) );
            DrawRectangle( (int)r.x + 4, (int)r.y + 8, (int)r.width - 8, 14, ColorAlpha( { 120, 124, 140, 255 }, alpha ) );
            DrawRectangle( (int)r.x + 4, (int)r.y + 8, (int)r.width - 8, 2, ColorAlpha( { 190, 196, 210, 255 }, alpha ) );
            for ( int k = 0; k < 4; ++k )
                DrawTriangle( { r.x + 5 + k * 6.0f, r.y + 22 }, { r.x + 8 + k * 6.0f, r.y + 28 }, { r.x + 11 + k * 6.0f, r.y + 22 }, ColorAlpha( { 200, 200, 215, 255 }, alpha ) );
            return;
        }
        if ( it.m_id == "lore" && !assets().sheet( "items" ).anim( "lore" ) )
        {
            DrawRectangle( (int)cx - 7, (int)cy - 9, 14, 18, ColorAlpha( { 40, 60, 90, 255 }, alpha ) );
            DrawRectangle( (int)cx - 5, (int)cy - 7, 10, 12, ColorAlpha( { 120, 230, 255, 255 }, alpha ) );
            return;
        }
        if ( !it.m_sheet.empty() )
        {
            Color t = it.m_id == "warp" ? ColorAlpha( { 220, 150, 255, 255 }, alpha ) : white;
            drawFit( it.m_sheet, it.m_anim, { r.x + 1, r.y + 1, r.width - 2, r.height - 2 }, t, it.m_enemy && m_left );
        }
        if ( it.m_id == "treasure" ) txt( "?", r.x + r.width - 8, r.y + r.height - 12, ColorAlpha( Gold, alpha ) );
        if ( it.m_id == "teleport_pair" ) txt( "2", r.x + r.width - 8, r.y + 1, ColorAlpha( Gold, alpha ) );
        if ( it.m_id == "teleport_oneway" ) txt( "1", r.x + r.width - 8, r.y + 1, ColorAlpha( Gold, alpha ) );
        if ( it.m_id == "switch" ) txt( std::string( 1, (char)( 'A' + m_group ) ), r.x + 2, r.y + 1, ColorAlpha( Gold, alpha ) );
    }

    /** @brief Editor marks over the level: grid, hidden things, links, the cursor, the selection, the report. */
    void drawOverlay( Screen &s )
    {
        const Level &L = m_doc.m_view;
        float        z = m_cam.m_zoom;
        float        vwW = s.m_w / z, vhW = s.m_h / z;
        int          x0 = std::max( 0, (int)std::floor( m_cam.m_x / T ) - 1 ), x1 = std::min( L.m_w - 1, (int)std::floor( ( m_cam.m_x + vwW ) / T ) + 1 );
        int          y0 = std::max( 0, (int)std::floor( m_cam.m_y / T ) - 1 ), y1 = std::min( L.m_h - 1, (int)std::floor( ( m_cam.m_y + vhW ) / T ) + 1 );
        float        pulse = 0.5f + 0.5f * std::sin( m_clock * 6 );
        Camera2D     c2 = {};
        c2.target = { m_cam.m_x, m_cam.m_y };
        if ( z >= 1 ) c2.target = { std::floor( m_cam.m_x ), std::floor( m_cam.m_y ) };
        c2.zoom = z;
        float lw = 1 / z;
        BeginMode2D( c2 );
        // The map's edge.
        DrawRectangleLinesEx( { -lw, -lw, L.m_w * T + 2 * lw, L.m_h * T + 2 * lw }, lw, { 255, 200, 90, 200 } );
        // Grid: every cell (every fourth when far out), stronger every ten.
        if ( m_grid )
        {
            int step = z < 0.5f ? 4 : 1;
            for ( int x = x0 - x0 % step; x <= x1 + 1; x += step )
                DrawLineEx( { x * T, y0 * T }, { x * T, ( y1 + 1 ) * T }, lw, x % 10 == 0 ? Color{ 255, 255, 255, 70 } : Color{ 255, 255, 255, 26 } );
            for ( int y = y0 - y0 % step; y <= y1 + 1; y += step )
                DrawLineEx( { x0 * T, y * T }, { ( x1 + 1 ) * T, y * T }, lw, y % 10 == 0 ? Color{ 255, 255, 255, 70 } : Color{ 255, 255, 255, 26 } );
        }
        // What the game hides: secrets, fake walls, toggles' groups, lights, arrival points, movers' paths, links.
        for ( int y = y0; y <= y1; ++y )
            for ( int x = x0; x <= x1; ++x )
            {
                char            ch = m_doc.at( x, y );
                const CharInfo &info = m_table[ch];
                float           px = x * T, py = y * T;
                if ( ch == '?' ) DrawRectangle( (int)px, (int)py, Tile, Tile, { 170, 90, 255, 70 } );
                if ( ch == 'X' )
                    for ( int k = 0; k < 4; ++k ) DrawLineEx( { px + k * 8.0f, py + T }, { px + k * 8.0f + 8, py }, lw, { 255, 220, 120, 110 } );
                if ( !knownKind( info.m_kind ) ) DrawRectangle( (int)px + 2, (int)py + 2, Tile - 4, Tile - 4, { 255, 0, 200, 140 } );
                if ( info.m_kind == "light" )
                {
                    Color c = lightColour( info.m_args.empty() ? "" : info.m_args[0] );
                    float r = ( info.m_args.size() > 1 ? (float)atof( info.m_args[1].c_str() ) : 5 ) * T;
                    DrawCircleLines( (int)( px + T / 2 ), (int)( py + T / 2 ), r, ColorAlpha( c, 0.25f ) );
                    DrawCircle( (int)( px + T / 2 ), (int)( py + T / 2 ), 6, ColorAlpha( c, 0.9f ) );
                    DrawCircle( (int)( px + T / 2 ) - 1, (int)( py + T / 2 ) - 1, 2, WHITE );
                }
                if ( info.m_kind == "arrive" )
                {
                    DrawCircleLines( (int)( px + T / 2 ), (int)( py + T - 6 ), 12, { 120, 220, 255, 220 } );
                    DrawCircleLines( (int)( px + T / 2 ), (int)( py + T - 6 ), 8, { 120, 220, 255, 140 } );
                }
                if ( info.m_kind == "teleport" && !info.m_args.empty() && info.m_args[0].size() == 1 )
                {
                    // To the target pad (the nearest cell with that character).
                    char  to = info.m_args[0][0];
                    float best = 1e9f;
                    int   bx = -1, by = -1;
                    for ( int yy = 0; yy < m_doc.m_h; ++yy )
                    {
                        size_t at = m_doc.m_rows[yy].find( to );
                        while ( at != std::string::npos )
                        {
                            float d = std::fabs( (float)at - x ) + std::fabs( (float)yy - y );
                            if ( d < best ) best = d, bx = (int)at, by = yy;
                            at = m_doc.m_rows[yy].find( to, at + 1 );
                        }
                    }
                    if ( bx >= 0 )
                    {
                        Vector2 a = { px + T / 2, py + T / 2 }, b = { bx * T + T / 2, by * T + T / 2 };
                        // A dashed thin line, so long links do not cover the map.
                        float len = std::hypot( b.x - a.x, b.y - a.y ), dash = 10;
                        for ( float t0 = 0; t0 < len; t0 += 2 * dash )
                        {
                            float t1 = std::min( len, t0 + dash );
                            DrawLineEx( { a.x + ( b.x - a.x ) * t0 / len, a.y + ( b.y - a.y ) * t0 / len }, { a.x + ( b.x - a.x ) * t1 / len, a.y + ( b.y - a.y ) * t1 / len },
                                        lw, { 120, 220, 255, 150 } );
                        }
                        DrawCircle( (int)b.x, (int)b.y, 4 * lw, { 120, 220, 255, 200 } );
                    }
                    else
                        DrawRectangleLinesEx( { px + 2, py + 2, T - 4, T - 4 }, 2 * lw, { 255, 90, 90, 200 } );
                }
                if ( info.m_kind == "mover" && m_doc.at( x - 1, y ) != ch )
                {
                    int n = 1;
                    while ( m_doc.at( x + n, y ) == ch && x + n < m_doc.m_w ) ++n;
                    float dx = ( info.m_args.size() > 0 ? (float)atof( info.m_args[0].c_str() ) : 0 ) * T;
                    float dy = ( info.m_args.size() > 1 ? (float)atof( info.m_args[1].c_str() ) : 0 ) * T;
                    DrawRectangleLinesEx( { px + dx, py + dy, n * T, 10 }, lw, { 120, 220, 255, 170 } );
                    DrawLineEx( { px + n * T / 2, py + 5 }, { px + dx + n * T / 2, py + dy + 5 }, lw, { 120, 220, 255, 120 } );
                }
                if ( info.m_kind == "crusher" )
                {
                    float reach = ( info.m_args.size() > 0 ? (float)atof( info.m_args[0].c_str() ) : 3 ) * T;
                    DrawRectangleLinesEx( { px + 2, py, T - 4, reach + T }, lw, { 255, 150, 80, 110 } );
                }
                if ( info.m_kind == "enemy" || info.m_kind == "boss" || info.m_kind == "start" )
                {
                    bool    up = false;
                    Vector2 p = standPoint( m_doc, info, x, y, up );
                    if ( std::fabs( p.y - ( py + T ) ) > T * 1.5f && !up ) DrawLineEx( { px + T / 2, py + T / 2 }, { p.x, p.y - 4 }, lw, { 255, 255, 255, 90 } );
                    bool ambush = std::find( info.m_args.begin(), info.m_args.end(), "ambush" ) != info.m_args.end();
                    bool elite = std::any_of( info.m_args.begin(), info.m_args.end(), []( const std::string &w ) { return w.rfind( "elite", 0 ) == 0; } );
                    if ( ambush ) DrawCircle( (int)px + 5, (int)py + 5, 3, { 120, 220, 255, 230 } );
                    if ( elite ) DrawCircle( (int)px + 13, (int)py + 5, 3, { 255, 200, 60, 230 } );
                }
            }
        // Where the hero can stand (after a check) and where players were knocked out.
        if ( m_showReach && m_report )
            for ( const auto &[x, y] : m_reach )
                DrawRectangleRec( { x * T + T * 0.5f - 2 * lw, y * T - 5 * lw, 4 * lw, 4 * lw },
                                  { 120, 255, 150, 210 } );
        if ( m_showDeaths )
            for ( const DeathMark &d : m_deathMarks )
            {
                float r = T * ( 0.35f + 0.12f * std::min( d.m_n, 8 ) );
                DrawCircleV( { d.m_x * T + T * 0.5f, d.m_y * T + T * 0.5f }, r,
                             { 255, 50, 50, (unsigned char)std::min( 200, 70 + 25 * d.m_n ) } );
                DrawCircleLines( (int)( d.m_x * T + T * 0.5f ), (int)( d.m_y * T + T * 0.5f ), r,
                                 { 255, 220, 220, 230 } );
            }
        // The checker's findings.
        for ( const ReportLine &l : m_lines )
            if ( l.m_x >= 0 )
            {
                DrawRectangleRec( { l.m_x * T, l.m_y * T, T, T }, ColorAlpha( l.m_c, 0.15f + 0.2f * pulse ) );
                DrawRectangleLinesEx( { l.m_x * T - 3, l.m_y * T - 3, T + 6, T + 6 }, std::max( 2.0f, 3 * lw ), ColorAlpha( l.m_c, 0.85f + 0.15f * pulse ) );
            }
        if ( m_flashT > 0 && m_flashX >= 0 )
            DrawRectangleLinesEx( { m_flashX * T - 6, m_flashY * T - 6, T + 12, T + 12 }, 3 * lw, ColorAlpha( WHITE, std::min( 1.0f, m_flashT ) * pulse ) );
        // The first teleport pad waits for its partner.
        if ( m_telePending && inside( m_teleX, m_teleY ) )
            DrawRectangleLinesEx( { m_teleX * T, m_teleY * T, T, T }, 2 * lw, ColorAlpha( Gold, pulse ) );
        // The selection.
        if ( m_hasSel )
        {
            int       sx0 = std::min( m_sx0, m_sx1 ), sx1 = std::max( m_sx0, m_sx1 ), sy0 = std::min( m_sy0, m_sy1 ), sy1 = std::max( m_sy0, m_sy1 );
            Rectangle r = { sx0 * T, sy0 * T, ( sx1 - sx0 + 1 ) * T, ( sy1 - sy0 + 1 ) * T };
            DrawRectangleRec( r, { 120, 200, 255, 40 } );
            DrawRectangleLinesEx( r, 2 * lw, ColorAlpha( { 120, 200, 255, 255 }, 0.5f + 0.5f * pulse ) );
        }
        // Rectangles being dragged.
        if ( m_drag == DragE::RECT || m_drag == DragE::ERASE_RECT )
        {
            int       ax = std::min( m_dragX, m_curX ), bx = std::max( m_dragX, m_curX ), ay = std::min( m_dragY, m_curY ), by = std::max( m_dragY, m_curY );
            Rectangle r = { ax * T, ay * T, ( bx - ax + 1 ) * T, ( by - ay + 1 ) * T };
            if ( m_drag == DragE::RECT )
            {
                const Item &b = brush();
                if ( ( bx - ax + 1 ) * ( by - ay + 1 ) <= 4000 )
                    for ( int y = ay; y <= by; ++y )
                        for ( int x = ax; x <= bx; ++x ) drawGhost( b, x, y, 0.55f );
            }
            DrawRectangleRec( r, m_drag == DragE::RECT ? Color{ 255, 230, 120, 40 } : Color{ 255, 80, 80, 70 } );
            DrawRectangleLinesEx( r, 2 * lw, m_drag == DragE::RECT ? Gold : Bad );
        }
        // The paste ghost and the cursor with the brush.
        bool curIn = inside( m_curX, m_curY );
        if ( m_curOn && m_mode == ModeE::EDIT && m_drag != DragE::RIGHT && m_drag != DragE::PAN )
        {
            if ( m_pasting )
            {
                Rectangle r = { m_curX * T, m_curY * T, m_clip.m_w * T, m_clip.m_h * T };
                for ( int y = 0; y < m_clip.m_h; ++y )
                    for ( int x = 0; x < m_clip.m_w; ++x )
                    {
                        char c = m_clip.m_cells[(size_t)y * m_clip.m_w + x];
                        if ( c == ' ' ) continue;
                        Color col = c == '.' ? Color{ 90, 100, 130, 60 } : c == '#' || c == '%' ? Color{ 200, 200, 220, 120 } : Color{ 255, 200, 90, 130 };
                        DrawRectangle( (int)( ( m_curX + x ) * T ), (int)( ( m_curY + y ) * T ), Tile, Tile, col );
                    }
                DrawRectangleLinesEx( r, 2 * lw, ColorAlpha( Gold, 0.5f + 0.5f * pulse ) );
            }
            else if ( curIn && m_drag == DragE::NONE && !m_useRaw )
                drawGhost( brush(), m_curX, m_curY, 0.45f + 0.2f * pulse );
            if ( curIn || m_pad )
                DrawRectangleLinesEx( { m_curX * T, m_curY * T, T, T }, 2 * lw, ColorAlpha( curIn ? WHITE : Bad, 0.6f + 0.4f * pulse ) );
        }
        EndMode2D();

        // Characters and group letters as text (not zoomed; only when cells are big enough).
        if ( z >= 0.5f )
            for ( int y = y0; y <= y1; ++y )
                for ( int x = x0; x <= x1; ++x )
                {
                    char            ch = m_doc.at( x, y );
                    const CharInfo &info = m_table[ch];
                    Vector2         p = m_cam.toScreen( x * T, y * T );
                    if ( p.y < BarH - 4 ) continue;
                    if ( m_showChars && ch != ' ' && ch != '.' && ( !info.m_kind.empty() || m_doc.legend( ch ) ) )
                        txt( std::string( 1, ch ), p.x + 2, p.y + 1, { 255, 255, 160, 255 } );
                    else if ( ch == '?' && z >= 1 )
                        txt( "?", p.x + 13, p.y + 10, { 230, 200, 255, 200 }, false );
                    if ( ( info.m_kind == "toggle" || info.m_kind == "switch" ) && !info.m_args.empty() )
                        txt( info.m_args[0].substr( 0, 1 ), p.x + T * z - 8, p.y + 1, info.m_kind == "switch" ? Gold : Color{ 160, 255, 240, 255 } );
                    if ( !knownKind( info.m_kind ) ) txt( std::string( 1, ch ), p.x + T * z / 2 - 3, p.y + T * z / 2 - 6, WHITE );
                }
    }

    /** @brief The brush drawn on a cell, see-through. */
    void drawGhost( const Item &b, int x, int y, float alpha )
    {
        std::string    theme = m_doc.key( "theme", "station" );
        const TileSet &ts = assets().tiles( theme );
        Color          tint = ColorAlpha( ts.m_tints[std::clamp( atoi( m_doc.key( "tint", "0" ).c_str() ), 0, 3 )], alpha );
        if ( b.m_look )
        {
            drawCellLook( ts, tint, b.m_look, x * T, y * T, T, m_clock );
            return;
        }
        CharInfo info = infoOf( b );
        if ( info.m_kind == "light" || info.m_kind == "crusher" || info.m_kind.empty() )
        {
            drawItemIcon( b, { x * T, y * T, T, T }, alpha );
            return;
        }
        drawSpawn( m_doc, info, x, y, 0, m_clock, false, alpha );
    }

    void drawBars( Screen &s )
    {
        // Top: the file, the brush, the cell, the zoom, the size; or a message.
        DrawRectangle( 0, 0, s.m_w, BarH, { 8, 10, 26, 255 } );
        DrawRectangle( 0, BarH, s.m_w, 1, { 60, 120, 170, 255 } );
        std::string file = m_doc.m_id + ( m_dirty ? "*" : "" );
        int         x = 4 + txt( file, 4, 1, Gold ) + 10;
        std::string right = ( inside( m_curX, m_curY ) ? std::to_string( m_curX + 1 ) + "," + std::to_string( m_curY + 1 ) + "  " : "" ) +
                            std::to_string( (int)std::lround( m_cam.m_zoom * 100 ) ) + "%  " + std::to_string( m_doc.m_w ) + "x" +
                            std::to_string( m_doc.m_h );
        int rw = txtW( right );
        txt( right, s.m_w - 4 - rw, 1, Dim );
        int room = s.m_w - 4 - rw - 10 - x;
        if ( m_msgT > 0 && !m_msg.empty() ) txt( fit( m_msg, room ), x, 1, ColorAlpha( m_msgC, std::min( 1.0f, m_msgT * 2 ) ) );
        else if ( m_checking )
            txt( fit( tr( "editor.report.running" ) + std::string( (size_t)( (int)( m_clock * 3 ) % 4 ), '.' ), room ), x, 1, Warn );
        else
        {
            std::string b = tr( "editor.brush" ) + ": " + nameOf( brush() );
            if ( !brush().m_ch && brush().m_tool == ToolE::PAINT ) b += "  (" + legendText( brush() ) + ")";
            if ( m_pasting ) b = tr( "editor.msg.pasting" );
            txt( fit( b, room ), x, 1, Ink );
        }

        // Bottom: the main keys (or the pad's buttons).
        DrawRectangle( 0, s.m_h - BarH, s.m_w, BarH, { 8, 10, 26, 255 } );
        DrawRectangle( 0, s.m_h - BarH - 1, s.m_w, 1, { 60, 120, 170, 255 } );
        std::vector<std::pair<std::string, std::string>> hints;
        if ( m_pad )
            hints = { { PadA, "editor.hint.paint" },  { PadB, "editor.hint.erase" },      { PadX, "editor.hint.palette" },
                      { PadLB + PadRB, "editor.hint.brush" }, { PadSelect, "editor.hint.check" }, { PadStart, "editor.hint.menu" } };
        else
            hints = { { tr( "editor.key.lmb" ), "editor.hint.paint" }, { tr( "editor.key.rmb" ), "editor.hint.erase_pan" }, { "Tab", "editor.hint.palette" },
                      { "F1", "editor.hint.help" },  { "F2", "editor.hint.settings" }, { "F5", "editor.hint.check" },
                      { "F9", "editor.hint.test" },  { "Esc", "editor.hint.menu" } };
        float hx = 4;
        for ( const auto &[key, what] : hints )
        {
            std::string w = tr( what );
            if ( hx + txtW( key ) + txtW( w ) + 6 > s.m_w - 4 ) break;
            hx += txt( key, hx, s.m_h - BarH + 1, Gold ) + 3;
            hx += txt( w, hx, s.m_h - BarH + 1, Dim ) + 10;
        }
    }

    void drawPalette( Screen &s )
    {
        (void)s;
        Rectangle p = paletteRect();
        panel( p );
        for ( int i = 0; i < 5; ++i )
        {
            Rectangle   r = tabRect( i );
            bool        on = i == m_cat;
            std::string t = fit( tr( CatKeys[i] ), (int)r.width - 4 );
            DrawRectangleRec( r, on ? Color{ 40, 80, 130, 255 } : Color{ 20, 26, 50, 255 } );
            if ( inRect( m_mouse, r ) ) DrawRectangleLinesEx( r, 1, { 120, 200, 255, 255 } );
            txt( t, r.x + ( r.width - txtW( t ) ) / 2, r.y + 1, on ? Gold : Dim );
        }
        const std::vector<Item> &list = m_items[m_cat];
        int                      hovered = -1;
        for ( int i = 0; i < (int)list.size(); ++i )
        {
            Rectangle r = cellRect( i );
            bool      sel = !m_useRaw && m_cat == m_brushCat && i == m_sel[m_cat];
            DrawRectangleRec( { r.x - 1, r.y - 1, r.width + 2, r.height + 2 }, sel ? Color{ 60, 110, 170, 255 } : Color{ 18, 22, 44, 255 } );
            drawItemIcon( list[i], r );
            if ( inRect( m_mouse, r ) ) hovered = i, DrawRectangleLinesEx( { r.x - 1, r.y - 1, r.width + 2, r.height + 2 }, 1, { 160, 220, 255, 255 } );
            if ( sel ) DrawRectangleLinesEx( { r.x - 2, r.y - 2, r.width + 4, r.height + 4 }, 1, Gold );
            if ( m_pad && m_palFocus < 0 && i == m_padSel ) DrawRectangleLinesEx( { r.x - 3, r.y - 3, r.width + 6, r.height + 6 }, 1, ColorAlpha( Gold, 0.5f + 0.5f * std::sin( m_clock * 6 ) ) );
            // The episode's enemies come first: a line after them.
            if ( m_cat == 2 && i == 7 ) DrawRectangle( (int)r.x + 34, (int)r.y, 1, 32, { 255, 220, 110, 120 } );
        }
        // About the entry under the mouse, else the chosen one.
        float       y = infoTop();
        if ( hovered < 0 && m_pad && m_palFocus < 0 && m_padSel < (int)list.size() ) hovered = m_padSel;
        const Item &shown = hovered >= 0 ? list[hovered] : brush();
        txt( fit( nameOf( shown ), (int)p.width - 12 ), p.x + 6, y, Gold );
        y += 12;
        std::string what;
        if ( shown.m_ch ) what = tr( "editor.char" ) + " " + std::string( 1, shown.m_ch == ' ' ? '_' : shown.m_ch ) + ( shown.m_ch == ' ' ? " (" + tr( "editor.item.sky" ) + ")" : "" );
        else if ( shown.m_tool != ToolE::PAINT )
            what = tr( shown.m_tool == ToolE::TELE_PAIR ? "editor.about.tele_pair" : "editor.about.tele_oneway" );
        else
        {
            std::string t = legendText( shown );
            char        c = 0;
            for ( const LegendLine &l : m_doc.m_legend )
                if ( l.m_text == t ) c = l.m_ch;
            what = std::string( "legend " ) + ( c ? std::string( 1, c ) : tr( "editor.char_new" ) ) + "  " + t;
        }
        txt( fit( what, (int)p.width - 12 ), p.x + 6, y, Dim );
        // The entry's controls.
        std::vector<Ctl> ctl = controls();
        for ( size_t i = 0; i < ctl.size(); ++i )
        {
            const Ctl &c = ctl[i];
            bool       focus = m_pad && m_palFocus == (int)i;
            bool       hot = inRect( m_mouse, c.m_r );
            if ( c.m_kind < 4 )
            {
                static const char *keys[4] = { "editor.flag.ambush", "editor.flag.left", "editor.flag.elite", "editor.flag.ceiling" };
                bool on = c.m_kind == 0 ? m_ambush : c.m_kind == 1 ? m_left : c.m_kind == 2 ? m_elite : m_ceiling;
                DrawRectangleRec( c.m_r, on ? Color{ 50, 120, 80, 255 } : Color{ 24, 30, 56, 255 } );
                DrawRectangleLinesEx( c.m_r, 1, focus ? Gold : hot ? Color{ 160, 220, 255, 255 } : Color{ 60, 80, 120, 255 } );
                txt( tr( keys[c.m_kind] ), c.m_r.x + 5, c.m_r.y + 1, on ? Good : Dim );
            }
            else
            {
                DrawRectangleRec( c.m_r, { 24, 30, 56, 255 } );
                DrawRectangleLinesEx( c.m_r, 1, focus ? Gold : hot ? Color{ 160, 220, 255, 255 } : Color{ 60, 80, 120, 255 } );
                if ( c.m_kind == 4 )
                {
                    std::string t = tr( "editor.group" ) + " " + std::string( 1, (char)( 'A' + m_group ) );
                    txt( "<", c.m_r.x + 4, c.m_r.y + 1, Gold );
                    txt( t, c.m_r.x + ( c.m_r.width - txtW( t ) ) / 2, c.m_r.y + 1, Ink );
                    txt( ">", c.m_r.x + c.m_r.width - 9, c.m_r.y + 1, Gold );
                }
                else
                {
                    const Item &b = brush();
                    std::string t = tr( "editor.args" ) + ": " + ( b.m_args.empty() ? "-" : b.m_args );
                    bool        arrows = !b.m_presets.empty();
                    txt( fit( t, (int)c.m_r.width - ( arrows ? 34 : 8 ) ), c.m_r.x + 4, c.m_r.y + 1, Ink );
                    if ( arrows )
                    {
                        txt( "<", c.m_r.x + c.m_r.width - 22, c.m_r.y + 1, Gold );
                        txt( ">", c.m_r.x + c.m_r.width - 9, c.m_r.y + 1, Gold );
                    }
                }
            }
        }
        // How to use it.
        std::string hint = tr( m_pad ? "editor.pal.hint_pad" : "editor.pal.hint" );
        txt( fit( hint, (int)p.width - 12 ), p.x + 6, p.y + p.height - 13, { 110, 130, 160, 255 } );
    }

    void drawReport( Screen &s )
    {
        (void)s;
        Rectangle r = reportRect();
        panel( r );
        std::string title = tr( "editor.report.title" );
        if ( m_checking ) title += "  " + tr( "editor.report.running" ) + std::string( (size_t)( (int)( m_clock * 3 ) % 4 ), '.' );
        txt( title, r.x + 6, r.y + 2, Gold );
        txt( "x", r.x + r.width - 12, r.y + 2, Dim );
        int shown = 0;
        for ( int i = m_reportScroll; i < (int)m_lines.size() && shown < 7; ++i, ++shown )
        {
            const ReportLine &l = m_lines[i];
            float             ly = r.y + 16 + shown * 12.0f;
            Rectangle         row = { r.x + 3, ly, r.width - 6, 12 };
            if ( l.m_x >= 0 && inRect( m_mouse, row ) ) DrawRectangleRec( row, { 60, 90, 140, 120 } );
            txt( fit( l.m_text, (int)r.width - 14 ), r.x + 6, ly, l.m_c );
        }
        if ( m_lines.empty() && !m_checking ) txt( tr( "editor.report.empty" ), r.x + 6, r.y + 16, Dim );
        if ( (int)m_lines.size() > 7 )
        {
            float h = r.height - 20, bar = h * 7 / m_lines.size();
            DrawRectangle( (int)( r.x + r.width - 4 ), (int)( r.y + 16 + h * m_reportScroll / m_lines.size() ), 2, (int)bar, { 120, 160, 200, 255 } );
        }
    }

    void drawMenu( Screen &s )
    {
        DrawRectangle( 0, 0, s.m_w, s.m_h, { 0, 0, 10, 140 } );
        Rectangle r = menuRect();
        panel( r );
        std::string title = tr( "editor.menu.title" );
        txt( title, r.x + ( r.width - txtW( title ) ) / 2, r.y + 6, Gold );
        static const char *keys[7] = { "editor.menu.back", "editor.menu.save", "editor.menu.check", "editor.menu.test",
                                       "editor.menu.settings", "editor.menu.save_leave", "editor.menu.leave" };
        for ( int i = 0; i < 7; ++i )
        {
            std::string t = tr( keys[i] );
            float       y = r.y + 26 + i * 16.0f;
            bool        sel = i == m_menuI;
            if ( sel ) DrawRectangle( (int)r.x + 6, (int)y - 1, (int)r.width - 12, 15, { 40, 70, 120, 255 } );
            txt( t, r.x + ( r.width - txtW( t ) ) / 2, y + 1, sel ? Gold : Ink );
        }
    }

    void drawSettings( Screen &s )
    {
        DrawRectangle( 0, 0, s.m_w, s.m_h, { 0, 0, 10, 140 } );
        Rectangle d = settingsRect();
        panel( d );
        std::string title = tr( "editor.set.title" );
        txt( title, d.x + ( d.width - txtW( title ) ) / 2, d.y + 6, Gold );
        static const char *keys[14] = { "editor.set.name",  "editor.set.name_de", "editor.set.theme",  "editor.set.tint", "editor.set.bg",
                                        "editor.set.music", "editor.set.dark",    "editor.set.gravity", "editor.set.par", "editor.set.left",
                                        "editor.set.right", "editor.set.top",     "editor.set.bottom", "editor.set.done" };
        for ( int r = 0; r < 14; ++r )
        {
            Rectangle row = settingsRow( r );
            bool      sel = r == m_setI;
            if ( sel ) DrawRectangleRec( row, { 40, 70, 120, 255 } );
            if ( r == 13 )
            {
                std::string t = tr( keys[r] );
                txt( t, row.x + ( row.width - txtW( t ) ) / 2, row.y + 1, sel ? Gold : Ink );
                continue;
            }
            txt( tr( keys[r] ), row.x + 4, row.y + 1, sel ? Gold : Dim );
            std::string v = settingValue( r );
            if ( r == 5 && v.empty() ) v = "-";
            if ( r <= 1 )
                txt( fit( v.empty() ? "-" : v, (int)( row.x + row.width - d.x - 152 ) ), d.x + 152, row.y + 1, Ink );
            else
            {
                txt( "<", d.x + 152, row.y + 1, Gold );
                txt( v, d.x + 168, row.y + 1, Ink );
                txt( ">", row.x + row.width - 10, row.y + 1, Gold );
            }
        }
        std::string hint = tr( m_pad ? "editor.set.hint_pad" : "editor.set.hint" );
        txt( fit( hint, (int)d.width - 12 ), d.x + 6, d.y + d.height - 14, { 110, 130, 160, 255 } );
    }

    void drawField( Screen &s )
    {
        DrawRectangle( 0, 0, s.m_w, s.m_h, { 0, 0, 10, 140 } );
        Rectangle f = fieldRect();
        panel( f );
        txt( fit( m_fieldTitle, (int)f.width - 12 ), f.x + 6, f.y + 5, Gold );
        Rectangle box = { f.x + 6, f.y + 22, f.width - 12, 16 };
        DrawRectangleRec( box, { 4, 6, 16, 255 } );
        DrawRectangleLinesEx( box, 1, { 90, 160, 220, 255 } );
        std::string shown = m_fieldText;
        while ( txtW( shown ) > box.width - 12 && !shown.empty() )
        {
            // Off the front, a whole character at a time.
            size_t n = 1;
            while ( n < shown.size() && ( (unsigned char)shown[n] & 0xC0 ) == 0x80 ) ++n;
            shown.erase( 0, n );
        }
        int w = txt( shown, box.x + 4, box.y + 2, Ink, false );
        if ( (int)( m_clock * 2 ) % 2 == 0 ) DrawRectangle( (int)box.x + 5 + w, (int)box.y + 3, 1, 10, Gold );
        if ( !m_fieldPresets.empty() )
        {
            std::string sug = tr( "editor.field.presets" ) + " " + std::to_string( m_fieldPreset + 1 ) + "/" + std::to_string( m_fieldPresets.size() );
            txt( sug, f.x + 6, f.y + 42, Dim );
        }
        Rectangle okR, noR;
        fieldButtons( okR, noR );
        std::string hint = tr( m_pad ? "editor.field.hint_pad" : "editor.field.hint" );
        txt( fit( hint, (int)( okR.x - f.x - 12 ) ), f.x + 6, f.y + f.height - 19, { 110, 130, 160, 255 } );
        for ( int k = 0; k < 2; ++k )
        {
            Rectangle   r = k ? noR : okR;
            std::string t = tr( k ? "editor.field.cancel" : "editor.field.ok" );
            DrawRectangleRec( r, inRect( m_mouse, r ) ? Color{ 50, 90, 150, 255 } : Color{ 26, 36, 70, 255 } );
            DrawRectangleLinesEx( r, 1, { 90, 160, 220, 255 } );
            txt( t, r.x + ( r.width - txtW( t ) ) / 2, r.y + 1, Ink );
        }
    }

    void drawHelp( Screen &s )
    {
        DrawRectangle( 0, 0, s.m_w, s.m_h, { 0, 0, 10, 160 } );
        Rectangle r = { 16, 20, (float)s.m_w - 32, (float)s.m_h - 40 };
        panel( r );
        std::string title = tr( "editor.help.title" );
        txt( title, r.x + ( r.width - txtW( title ) ) / 2, r.y + 5, Gold );
        int   n = 0;
        float colW = ( r.width - 18 ) / 2;
        for ( int i = 1; i <= 40; ++i )
        {
            std::string key = "editor.help." + std::to_string( i );
            if ( !hasText( key ) ) break;
            int col = n % 2, row = n / 2;
            txt( fit( tr( key ), (int)colW - 6 ), r.x + 8 + col * colW, r.y + 22 + row * 13.0f, i <= 2 ? Ink : Dim );
            ++n;
        }
        std::string close = tr( "editor.help.close" );
        txt( close, r.x + ( r.width - txtW( close ) ) / 2, r.y + r.height - 14, { 110, 130, 160, 255 } );
    }

    void draw( Screen &s )
    {
        m_table.build( m_doc );
        DrawOptions o;
        o.m_decos = m_decos;
        o.m_light = m_light;
        o.m_clock = m_clock;
        drawLevel( s, m_doc, m_table, m_cam, m_decoSpots, o );
        s.begin( LayerE::HUD );
        drawOverlay( s );
        if ( m_report ) drawReport( s );
        if ( m_palette ) drawPalette( s );
        drawBars( s );
        if ( m_mode == ModeE::MENU ) drawMenu( s );
        if ( m_mode == ModeE::SETTINGS || ( m_mode == ModeE::FIELD && m_fieldBack == ModeE::SETTINGS ) ) drawSettings( s );
        if ( m_mode == ModeE::HELP ) drawHelp( s );
        if ( m_mode == ModeE::FIELD ) drawField( s );
        s.end();
    }

    Editor::ResultE update( float dt )
    {
        m_clock += dt;
        m_msgT -= dt;
        m_flashT -= dt;
        if ( IsCursorHidden() ) ShowCursor();
        readMouse();
        pollCheck();
        applyDemo();
        ResultE r = ResultE::STAY;
        switch ( m_mode )
        {
        case ModeE::FIELD: updateField( dt ); break;
        case ModeE::MENU: r = updateMenu( dt ); break;
        case ModeE::SETTINGS: updateSettings( dt ); break;
        case ModeE::HELP:
        {
            int p = pad();
            if ( GetKeyPressed() || IsMouseButtonPressed( MOUSE_BUTTON_LEFT ) || IsMouseButtonPressed( MOUSE_BUTTON_RIGHT ) ||
                 ( p >= 0 && ( IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_DOWN ) || IsGamepadButtonPressed( p, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT ) ||
                               IsGamepadButtonPressed( p, GAMEPAD_BUTTON_MIDDLE_RIGHT ) ) ) )
                m_mode = ModeE::EDIT;
            break;
        }
        case ModeE::EDIT: r = updateEdit( dt ); break;
        }
        if ( m_decosDirty && m_drag == DragE::NONE )
        {
            m_decoSpots = placeDecos( m_doc );
            m_decosDirty = false;
        }
        if ( r != ResultE::STAY )
        {
            m_drag = DragE::NONE;
            HideCursor();
        }
        return r;
    }
};

// ============================================================================================================ Editor

Editor::Editor() : m_impl( std::make_unique<Impl>() ) {}
Editor::~Editor() = default;

bool Editor::open( const std::string &path )
{
    return m_impl->open( path );
}

Editor::ResultE Editor::update( float dt )
{
    return m_impl->update( dt );
}

void Editor::draw( Screen &s )
{
    m_impl->draw( s );
}

const std::string &Editor::path() const
{
    return m_impl->m_path;
}

}   // namespace kepler
