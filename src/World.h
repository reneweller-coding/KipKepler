/**
 * @file World.h
 * @brief One level in play: the hero, his weapons, the enemies, pickups, moving parts, the camera; updated in fixed
 *        steps and drawn into the Screen.
 * @author Rene Weller
 */
#pragma once

#include "Content.h"
#include "Level.h"
#include "Physics.h"

#include <raylib.h>

#include <string>
#include <vector>

namespace kepler
{

class Screen;
class TileSet;
class Background;

/** @brief What the player presses, read once per frame. */
struct Controls
{
    bool m_left = false, m_right = false, m_up = false, m_down = false;
    bool m_jump = false, m_jumpPressed = false;
    bool m_fire = false, m_firePressed = false;
    bool m_alt = false;          ///< the weapon's second function (pressed)
    bool m_prevWeapon = false, m_nextWeapon = false;
    bool m_pause = false;
};

/** @brief Kinds of pickups. */
enum class PickE : int
{
    CRYSTAL,
    TREASURE,
    HEALTH,
    HEALTH_BIG,
    KEY_BLUE,
    KEY_GOLD,
    AMMO,
    WEAPON,
    POWER,
    LORE      ///< a logbook page (its key in Pickup::m_key)
};

struct Pickup
{
    PickE       m_kind;
    int         m_sub = 0;      ///< treasure index, weapon, power (0 overdrive, 1 boots, 2 shield)
    std::string m_anim;         ///< in the "items" sheet
    float       m_x, m_y;       ///< centre
    float       m_t = 0;
    bool        m_taken = false;
    bool        m_loose = false; ///< dropped by an enemy: falls, blinks out after a while
    float       m_vy = 0;
    float       m_life = 0;
    int         m_spawn = -1;   ///< its index in the level's spawns (-1: dropped by an enemy)
    std::string m_key;          ///< lore: the page's key
};

struct Shot
{
    WeaponE     m_weapon = WeaponE::BLASTER;
    bool        m_enemy = false;
    std::string m_anim;
    float       m_x, m_y, m_vx, m_vy;
    float       m_damage = 1;
    float       m_life = 2;
    float       m_dist = 0, m_range = 400;
    int         m_bounces = 0;
    bool        m_pierce = false;
    bool        m_gravity = false;
    bool        m_homing = false;
    bool        m_charged = false;
    float       m_t = 0;
    int         m_target = -1;
    float       m_splash = 0;   ///< explodes with this radius
    std::vector<int> m_hit;     ///< enemies a piercing shot already hit
    bool        m_dead = false;
    int         m_hits = 0;     ///< enemies hit so far (the ricochet award)
};

struct Enemy
{
    const EnemyDef *m_def = nullptr;
    float           m_x = 0, m_y = 0;   ///< feet centre (fliers: centre of the box's bottom too)
    float           m_vx = 0, m_vy = 0;
    float           m_hp = 1;
    int             m_dir = -1;         ///< facing
    int             m_state = 0;
    float           m_stateT = 0;
    float           m_t = 0;            ///< seconds alive (paths, bobbing)
    float           m_animT = 0;        ///< seconds in the current animation (starts again when it changes)
    std::string     m_animWas;          ///< the animation of the step before
    float           m_attackT = 0;      ///< shows the attack animation this much longer
    std::string     m_anim = "move";
    float           m_flash = 0;        ///< white flash when hit
    bool            m_alive = true;
    bool            m_hidden = false;   ///< ambush: not there until the hero comes near
    float           m_homeX = 0, m_homeY = 0;
    float           m_shootT = 0;
    float           m_frozen = 0;       ///< seconds left as an ice block
    int             m_parent = -1;
    int             m_children = 0;
    bool            m_ground = false;
    bool            m_ceiling = false;  ///< turrets/droppers hanging from above
    int             m_boss = 0;         ///< 0 no, else the boss kind + 1
    int             m_elite = 0;        ///< 0 none, 1 armoured, 2 swift, 3 splitting, 4 shielded, 5 regenerating
    float           m_speedMul = 1;     ///< swift elites move faster
    bool            m_shieldFront = false; ///< blocks shots from the front (the kind's armour or a shielded elite)
    bool            m_upsideDown = false;  ///< a walker on the ceiling
    float           m_hpMax = 1;
    int             m_phase = 0;        ///< bosses

    float left() const { return m_x - m_def->m_w * 0.5f; }
    float right() const { return m_x + m_def->m_w * 0.5f; }
    float top() const { return m_y - m_def->m_h; }
    float cy() const { return m_y - m_def->m_h * 0.5f; }
};

struct Particle
{
    float m_x, m_y, m_vx, m_vy;
    float m_life, m_max;
    Color m_c;
    int   m_size = 1;
    bool  m_glow = false;
    float m_grav = 0;
};

/** @brief A one-shot animation from a sheet (explosions, sparks, beams). */
struct Effect
{
    std::string m_sheet = "fx";
    std::string m_anim;
    float       m_x, m_y;
    float       m_t = 0;
    bool        m_flip = false;
    float       m_angle = 0;
    Color       m_tint = WHITE;
    bool        m_dead = false;
};

struct Mover
{
    float m_x0, m_y0, m_dx, m_dy;   ///< start (px, top left) and travel (px)
    int   m_w;                      ///< cells
    float m_speed, m_wait;
    float m_x, m_y, m_px, m_py;     ///< now and before this step
    float m_s = 0;                  ///< position along the path, 0..2 (there and back)
    float m_hold = 0;
};

/**
 * @brief Moves a platform on by a step (the game and the autopilot's look-ahead alike).
 * @param[in,out] m   the platform
 * @param[in]     dt  the step
 */
void advanceMover( Mover &m, float dt );

struct Object
{
    std::string m_kind;    ///< exit checkpoint teleport switch spring sign laser crusher light
    int         m_cx, m_cy;
    float       m_x, m_y;  ///< bottom centre of the cell
    std::vector<std::string> m_args;
    bool        m_on = false;
    float       m_t = 0;
    int         m_target = -1;   ///< teleport: object index
    char        m_ch = 0;
    int         m_spawn = -1;    ///< its index in the level's spawns
    bool        m_held = false;  ///< switches: the hero touched it in the step before (it flips on a new touch)
};

struct Light
{
    float m_x, m_y, m_r;
    Color m_c;
    float m_flicker = 0;
};

/** @brief A straight or jagged line drawn for a moment: the lancer's beam, the arc caster's lightning. */
struct Beam
{
    std::vector<Vector2> m_points;
    float                m_t = 0, m_life = 0.15f;
    Color                m_c;
    bool                 m_arc = false;
};

struct Popup
{
    std::string m_text;
    float       m_x, m_y, m_t = 0;
    Color       m_c;
};

/** @brief One level in play. */
class World : public Collider
{
public:
    /**
     * @brief Starts a level.
     * @param[in]     path     the level file
     * @param[in,out] progress the player's progress (weapons, ammo, credits ...)
     * @param[out]    error    why it failed
     * @return whether it loaded
     */
    bool load( const std::string &path, Progress &progress, std::string &error );

    /** @brief Runs the world for a frame (in fixed steps). */
    void update( float dt, const Controls &c );
    /** @brief Draws the world into the screen's layers. */
    void draw( Screen &screen );
    /** @brief Draws the HUD (virtual screen pixels). */
    void drawHud( Screen &screen );

    /** @brief The view's size in virtual pixels (from the Screen). */
    void setView( int w, int h ) { m_vw = w, m_vh = h; }
    /** @brief Puts the camera on a point (tests and pictures). */
    void lookAt( float x, float y );
    /** @brief Back to the last checkpoint (pause menu: a way out of any spot). */
    void giveUp() { if ( !m_dead && m_exitT < 0 ) killHero(); }
    /** @brief Puts the hero somewhere (tests). */
    void place( float x, float y );

    // Collider
    bool solid( int cx, int cy ) const override;
    bool oneway( int cx, int cy ) const override;
    bool icy( int cx, int cy ) const override;
    bool platformTop( float x0, float x1, float before, float after, float &top ) const override;

    /**
     * @brief Where a laser fence or a crusher hurts at a moment of its own clock.
     * @param[in]  o     the object
     * @param[in]  at    its clock (Object::m_t then)
     * @param[out] box   left, top, right, bottom of what hurts
     * @param[out] beam  lasers: the beam's length in cells (may be null)
     * @return whether it hurts at all then
     */
    bool hazard( const Object &o, float at, float box[4], int *beam = nullptr ) const;

    // What the level's end screen shows.
    bool  m_finished = false;   ///< the hero went through the exit
    float m_time = 0;
    int   m_crystalsTaken = 0, m_crystals = 0;
    int   m_treasureTaken = 0, m_treasure = 0;
    int   m_secretsFound = 0, m_secrets = 0;
    int   m_kills = 0, m_enemiesTotal = 0;
    int   m_deaths = 0;
    int   m_score = 0;          ///< earned in this level
    int   m_credits = 0;        ///< earned in this level
    bool  m_restart = false;    ///< asked for a restart at the checkpoint (pause menu)
    int   m_hits = 0;           ///< times the hero was hurt (the unhurt medal)
    std::string m_warp;         ///< the hero left through a secret warp to this level
    bool  m_trial = false;      ///< a time trial: the clock is shown big
    bool  m_assistInvulnerable = false; ///< assist mode: nothing hurts
    bool  m_assistAmmo = false;  ///< assist mode: ammo never runs out
    bool  m_rumbleOn = false;    ///< the pad's motors follow the shake
    std::vector<int> m_awardQueue;   ///< awards won in this level, to show (AwardE)
    float m_awardT = 0;
    void  grant( int award );   ///< gives an award (once) and queues its toast

    Level     m_level;
    Progress *m_progress = nullptr;

    // The hero.
    HeroBody    m_hero;
    float       m_hp = 100;
    float       m_hurtT = 0;      ///< invulnerable after a hit
    int         m_face = 1;
    float       m_cool = 0;
    float       m_charge = 0;
    WeaponE     m_weapon = WeaponE::BLASTER;
    std::string m_anim = "idle";
    float       m_animT = 0;
    float       m_shootPose = 0;
    bool        m_aimUp = false;
    bool        m_dead = false;
    float       m_deadT = 0;
    float       m_overdrive = 0, m_shield = 0;
    bool        m_boots = false;
    bool        m_keys[2] = { false, false };
    float       m_exitT = -1;     ///< beaming out through the exit
    float       m_appearT = 0;    ///< beaming in
    float       m_spawnX = 0, m_spawnY = 0;
    float       m_stepT = 0;
    float       m_lastLandVy = 0;

    // Everything else.
    std::vector<Pickup>   m_pickups;
    std::vector<Shot>     m_shots;
    std::vector<Enemy>    m_enemies;
    std::vector<Particle> m_particles;
    std::vector<Effect>   m_effects;
    std::vector<Mover>    m_movers;
    std::vector<Object>   m_objects;
    std::vector<Light>    m_lights;
    std::vector<Popup>    m_popups;
    std::vector<Beam>     m_beams;
    float                 m_acc = 0;     ///< time not yet stepped
    std::string           m_banner;      ///< a message across the screen
    float                 m_bannerT = 0;
    std::string           m_sign;        ///< the sign the hero stands at
    float                 m_signT = 0;

    // Changing cells.
    std::vector<uint8_t> m_broken;      ///< breakable: hits taken (2 = gone); crumble: 1 cracking, 2 gone
    std::vector<float>   m_crumbleT;
    std::vector<uint8_t> m_doorOpen;
    std::vector<int>     m_secretGroup; ///< per cell: secret group + 1 (0 none)
    std::vector<bool>    m_secretSeen;
    unsigned             m_groups = 0;  ///< toggle groups switched on
    float                m_toggleFlash = 0;
    bool                 m_exitOpen = false;
    int                  m_bossIndex = -1;
    bool                 m_bossAwake = false;
    float                m_dangerT = 0, m_calmT = 0;   ///< enemies close / none for this long (the music follows)
    bool                 m_fightMusic = false;

    // Look.
    float       m_camX = 0, m_camY = 0;
    float       m_camYSmooth = 0;   ///< the camera's y, followed slowly (the foreground sways by the difference)
    float       m_lookAhead = 0;
    float       m_shake = 0;
    float       m_clock = 0;
    float       m_dark = 0;
    int         m_tint = 0;
    std::string m_theme, m_bgName;
    struct DecoPlace
    {
        int   m_index;
        float m_x, m_y;   ///< top left in pixels
    };
    std::vector<DecoPlace> m_decoList;
    std::vector<uint8_t>   m_maskTerrain, m_maskBack, m_variant;   ///< per cell, worked out once
    int         m_vw = 640, m_vh = 360;    ///< the view in virtual pixels
    float       m_teleCool = 0, m_switchCool = 0;
    int         m_teleLock = -1;           ///< the pad the hero arrived on: it waits until he steps off
    bool        m_boss = false;            ///< a boss level
    float       m_hitStop = 0;

private:
    void step( float dt, const Controls &c );
    void stepHero( float dt, const Controls &c );
    void stepShots( float dt );
    void stepEnemies( float dt );
    void stepEnemy( Enemy &e, int index, float dt );
    void stepBoss( Enemy &e, int index, float dt );
    void stepPickups( float dt );
    void stepObjects( float dt );
    void stepMovers( float dt );
    void stepCamera( float dt, bool snap = false );
    void fire();
    void fireAlt();
    void enemyShoot( Enemy &e, const std::string &kind, float x, float y, float vx, float vy );
    void hurtHero( float amount, float fromX );
    void killHero();
    void respawn();
    bool hurtEnemy( int index, float damage, float fromX, WeaponE w, bool charged );
    void killEnemy( int index );
    void explode( float x, float y, float radius, float damage, bool byHero );
    void burst( float x, float y, int n, Color c, float speed, bool glow = true, float grav = 300 );
    void effect( const std::string &anim, float x, float y, bool flip = false, float angle = 0 );
    void popup( const std::string &text, float x, float y, Color c );
    void banner( const std::string &text, float seconds = 3 );
    void take( Pickup &p );
    void openExitIfDone();
    void hitCell( int cx, int cy, float damage );
    void flipGroup( int group );
    void placeDecos();
    bool lineOfSight( float x0, float y0, float x1, float y1 ) const;
    int  spawnEnemy( const std::string &type, float x, float y, bool ambush );
    float heroCx() const { return m_hero.m_x; }
    float heroCy() const { return m_hero.m_y - phys::HeroH * 0.5f; }

    void drawTiles( Screen &s, int layer );
    void drawBackground( Screen &s );
};

}   // namespace kepler
