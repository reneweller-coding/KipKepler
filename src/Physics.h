/**
 * @file Physics.h
 * @brief The hero's movement against the tiles, shared by the game and the level checker so both agree on what can
 *        be reached (docs/DESIGN.md "Physics").
 * @author Rene Weller
 */
#pragma once

namespace kepler
{

/** @brief The numbers of docs/DESIGN.md "Physics" (pixels and seconds). */
namespace phys
{
constexpr float HeroW = 20.0f;      ///< hero box width
constexpr float HeroH = 44.0f;      ///< hero box height
constexpr float Run = 210.0f;       ///< run speed
constexpr float Gravity = 1900.0f;  ///< px/s^2
constexpr float Jump = 640.0f;      ///< jump speed
constexpr float BootsJump = 900.0f; ///< with the boots
constexpr float SpringJump = 1180.0f; ///< from a spring (~7 tiles)
constexpr float FallMax = 1000.0f;  ///< fall speed cap
constexpr float Cut = 0.45f;        ///< vy *= Cut when the jump is let go while rising
constexpr float Coyote = 0.08f;     ///< jump still allowed this long after walking off
constexpr float Buffer = 0.12f;     ///< a jump pressed this long before landing still counts
constexpr float AccGround = 2400.0f;
constexpr float DecGround = 3000.0f;
constexpr float AccAir = 1600.0f;
constexpr float AccIce = 420.0f;
constexpr float DecIce = 260.0f;
constexpr float Step = 1.0f / 240.0f; ///< the fixed time step (240 Hz: 1-2 steps per frame on 144 Hz screens, never 0)
}   // namespace phys

/** @brief What the hero collides with. */
class Collider
{
public:
    virtual ~Collider() = default;
    /** @brief Whether a cell blocks from every side. */
    virtual bool solid( int cx, int cy ) const = 0;
    /** @brief Whether a cell is a one-way platform (blocks only from above). */
    virtual bool oneway( int cx, int cy ) const = 0;
    /** @brief Whether a cell is slippery ice. */
    virtual bool icy( int cx, int cy ) const = 0;
    /**
     * @brief Moving platforms: the top of one under the box's bottom edge between x0 and x1, if the bottom moves from
     *        `before` to `after` across it.
     * @param[in]  x0, x1         the box's horizontal extent
     * @param[in]  before, after  the bottom edge before and after the step
     * @param[out] top            the platform's top
     * @return whether such a platform is there
     */
    virtual bool platformTop( float x0, float x1, float before, float after, float &top ) const
    {
        (void)x0, (void)x1, (void)before, (void)after, (void)top;
        return false;
    }
};

/** @brief What the player asks of the hero in one step. */
struct HeroInput
{
    int  m_dir = 0;            ///< -1 left, 0, 1 right
    bool m_jump = false;       ///< jump held
    bool m_jumpPressed = false; ///< jump pressed this step
    bool m_down = false;       ///< down held
};

/** @brief The hero's body: position (feet centre), speed and the little timers of a good jump. */
struct HeroBody
{
    float m_x = 0, m_y = 0;    ///< feet centre in pixels
    float m_vx = 0, m_vy = 0;
    bool  m_ground = false;
    bool  m_cut = false;       ///< the jump was already cut
    bool  m_noCut = false;     ///< a spring launch cannot be cut
    float m_coyote = 0;
    float m_buffer = 0;
    float m_drop = 0;          ///< falling through one-way platforms for this long
    float m_jumpSpeed = phys::Jump;
    float m_gravity = phys::Gravity;
    float m_pushX = 0;         ///< extra horizontal speed from conveyors or movers this step
    bool  m_hitWall = false;   ///< ran into a wall this step
    bool  m_hitHead = false;
    bool  m_landed = false;    ///< touched down this step
    bool  m_jumped = false;    ///< left the ground by jumping this step
    bool  m_icy = false;       ///< stands on ice

    float left() const { return m_x - phys::HeroW * 0.5f; }
    float right() const { return m_x + phys::HeroW * 0.5f; }
    float top() const { return m_y - phys::HeroH; }
};

/**
 * @brief One fixed step of the hero's movement.
 * @param[in,out] b   the body
 * @param[in]     in  the input
 * @param[in]     c   the world
 * @param[in]     dt  the step (phys::Step)
 */
void stepHero( HeroBody &b, const HeroInput &in, const Collider &c, float dt );

/**
 * @brief Moves a box through the tiles (enemies, pickups that fall): x then y.
 * @param[in]     c          the world
 * @param[in,out] x, y       the box's bottom centre
 * @param[in]     w, h       the box's size
 * @param[in,out] vx, vy     its speed (zeroed on the blocked axis)
 * @param[in]     dt         the step
 * @param[in]     oneways    whether one-way platforms carry it
 * @param[out]    ground     whether it stands on something after the step
 * @param[out]    wall       whether it ran into a wall
 */
void moveBox( const Collider &c, float &x, float &y, float w, float h, float &vx, float &vy, float dt, bool oneways,
              bool &ground, bool &wall );

}   // namespace kepler
