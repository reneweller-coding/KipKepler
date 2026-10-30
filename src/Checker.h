/**
 * @file Checker.h
 * @brief The level checker (`--check <level> [picture.png]`): plays the hero's own physics from every place he can
 *        stand and reports what cannot be reached (crystals, keys, the exit), spots he cannot get out of, and a
 *        picture of the map with what was reached.
 * @author Rene Weller
 */
#pragma once

#include "Physics.h"

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace kepler
{

class Level;

/** @brief One way of moving from a standing place: jump or not, how long held, which way when. */
struct ReachPrim
{
    bool  m_jump;
    float m_hold;        ///< how long jump is held (seconds from the start)
    int   m_d1;          ///< direction first
    float m_t1;          ///< for this long (< 0: until the feet are over the next cell)
    int   m_d2;          ///< direction after
    float m_jumpAt = 0;  ///< the jump is pressed this late (a run-up)
    bool  m_down = false; ///< down is held (with the jump: dropping through a one-way platform)
};

/** @brief The moves the checker tries from every standing place. */
const std::vector<ReachPrim> &reachPrims();

/**
 * @brief The input of a move at one step (the checker and the autopilot replay moves alike).
 * @param[in]     p          the move
 * @param[in]     i          the step since the move began
 * @param[in]     x          the hero's x now
 * @param[in]     startCell  the column the move began in
 * @param[in,out] phase2     whether the move is in its second direction (starts false)
 * @return the input
 */
HeroInput reachInput( const ReachPrim &p, int i, float x, int startCell, bool &phase2 );

/** @brief A move found: from a standing place to another. */
struct ReachEdge
{
    int              m_to;
    int              m_prim;      ///< index into reachPrims() (+ 100000: with the movers elsewhere); -1 standing
                                  ///< still, -2/-3/-4 shooting left/right/up
    float            m_x;         ///< where the hero stands when it begins
    std::vector<int> m_touched;   ///< spawns touched on the way
};

/** @brief A standing place with the keys held and the switch groups on. */
struct ReachNode
{
    float                  m_x, m_y;
    int                    m_fx, m_fy, m_keys, m_toggles;
    bool                   m_exit = false;
    std::vector<ReachEdge> m_edges;
};

/** @brief All standing places and the moves between them. */
struct ReachGraph
{
    std::vector<ReachNode>            m_nodes;
    std::unordered_map<uint64_t, int> m_index;
    /** @brief The node of a place (-1 if never reached). */
    int find( int fx, int fy, int keys, int toggles ) const;
};

/**
 * @brief Builds the graph of a level (what the checker searches).
 * @param[in]  level  the level
 * @param[out] graph  its places and moves
 * @return whether the start could be stood on
 */
bool buildGraph( const Level &level, ReachGraph &graph );

/**
 * @brief Checks a level.
 * @param[in]  level    the level
 * @param[in]  picture  a PNG to write the overview into (empty: none)
 * @param[out] report   the report, one finding per line
 * @return whether the level can be finished (all crystals and the exit reachable)
 */
bool checkLevel( const Level &level, const std::string &picture, std::string &report );

}   // namespace kepler
