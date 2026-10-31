/**
 * @file Bot.h
 * @brief The autopilot (`--autoplay`): plays a level in the real game with the checker's graph -- walks to where a
 *        move begins, replays the move's input step by step, picks the nearest crystal (key, exit) by the graph,
 *        shoots what is in front of it. Moves whose timing matters (onto or off moving platforms, past laser fences
 *        and crushers) start when a look-ahead -- the move replayed with the world running on -- lands them safely;
 *        moves that never work at any moment of the platforms' round trip are left out. For testing levels with
 *        their enemies: time, deaths, stalls.
 * @author Rene Weller
 */
#pragma once

#include "Checker.h"
#include "World.h"

#include <cstdio>
#include <map>
#include <string>

namespace kepler
{

class Bot
{
public:
    /** @brief Builds the level's graph. */
    void start( const World &w );
    /** @brief The controls for the next fixed step. */
    Controls think( const World &w );
    /** @brief Real time: a new frame begins, with this many look-aheads for all its steps. */
    void newFrame( int lookAheads = 2 ) { m_lookAheads = lookAheads; }

    std::string m_status;      ///< what it does (for the log)
    int         m_stalls = 0;  ///< times it found no way on
    int         m_lost = 0;    ///< of those: standing on no known place
    int         m_noWay = 0;   ///< of those: no move leads to anything wanted
    bool        m_gaveUp = false;
    std::string m_stallLog;    ///< where it stalled (the first few)
    bool        m_realTime = false;   ///< plays in real time (the demo): a few look-aheads per step at most
    FILE       *m_trace = nullptr;   ///< every move and its outcome (--trace)

private:
    enum class ModeE
    {
        PLAN,
        APPROACH,
        MOVE,
        SHOOT,
        FIGHT,
        WANDER,
        BOSS    ///< stands off from the boss and shoots, jumping now and then
    };
    int  here( const World &w ) const;
    bool plan( const World &w );
    void fight( const World &w, Controls &c );
    /** @brief Whether a move begun at (x, y) needs timing: onto or off a platform that moves, past lasers or crushers. */
    bool timed( const World &w, const ReachEdge &e, float x, float y ) const;
    /** @brief The move replayed from the hero's state now with the world running on: whether it lands safely (why not). */
    bool forecast( const World &w, const ReachEdge &e, std::string *why = nullptr ) const;
    /** @brief Takes one look-ahead from the step's allowance (only in real time); false when none is left. */
    bool spend() const;
    /** @brief Whether a timed move works at any moment of the platforms' round trip (remembered per move). */
    bool possible( const World &w, int node, int edge );
    /** @brief How long a timed move at (x, y) may wait for its moment (the platforms' longest round trip and some). */
    float waitLimit( const World &w, float x, float y ) const;
    /** @brief Riding a platform: steps aside when standing still would carry the hero into a wall or a laser. */
    void ride( const World &w, Controls &c );
    /** @brief In the air for long (a spring keeps bouncing him): steers off the spring towards the nearest place. */
    void steer( const World &w, Controls &c ) const;

    ReachGraph         m_graph;
    ModeE              m_mode = ModeE::PLAN;
    ReachEdge          m_edge;
    int                m_from = -1;     ///< node the move began at
    int                m_edgeIndex = -1;
    int                m_step = 0;
    bool               m_phase2 = false;
    int                m_startCell = 0;
    float              m_modeT = 0;
    bool               m_left = false;   ///< left the ground during the move
    float              m_lastX = 0, m_lastY = 0;
    std::map<long, int> m_failed;       ///< (node, edge) -> failures
    std::map<long, bool> m_possible;     ///< (node, edge): timed moves that work at some moment
    std::map<long, int>  m_impossible;   ///< (node, edge): never let go by the look-ahead, deadly twice, missed thrice
    std::map<long, int>  m_deaths;       ///< (node, edge) -> deaths in it
    std::map<long, int>  m_misses;       ///< (node, edge) -> times it landed elsewhere
    long                 m_lastMove = -1;   ///< (node, edge) of the move that ended last
    float                m_lastMoveT = 0;   ///< and when
    float              m_noPlanT = 0;
    float              m_fireT = 0;
    int                m_wanderDir = 1;
    float              m_progressT = 0; ///< seconds since something was collected
    int                m_collected = 0;
    bool               m_wasDead = false;
    float                m_airT = 0;           ///< seconds off the ground
    int                  m_forecastWait = 0;   ///< steps until the next look-ahead after one that failed
    int                  m_budget = 0;         ///< look-aheads over a round trip one plan may still run
    mutable int          m_lookAheads = 0;     ///< real time: look-aheads this step may still run
    float                m_rideCheckT = 0;     ///< riding: seconds until the next look whether standing is safe
    int                  m_rideDir = 0;        ///< riding: the side to step to (0: stand)
    float                m_rideT = 0;          ///< riding with nothing to do: seconds until the next plan
};

}   // namespace kepler
