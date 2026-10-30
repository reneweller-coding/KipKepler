/**
 * @file Bot.h
 * @brief The autopilot (`--autoplay`): plays a level in the real game with the checker's graph -- walks to where a
 *        move begins, replays the move's input step by step, picks the nearest crystal (key, exit) by the graph,
 *        shoots what is in front of it. For testing levels with their enemies: time, deaths, stalls.
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

    std::string m_status;      ///< what it does (for the log)
    int         m_stalls = 0;  ///< times it found no way on
    int         m_lost = 0;    ///< of those: standing on no known place
    int         m_noWay = 0;   ///< of those: no move leads to anything wanted
    bool        m_gaveUp = false;
    std::string m_stallLog;    ///< where it stalled (the first few)
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
    float              m_noPlanT = 0;
    float              m_fireT = 0;
    int                m_wanderDir = 1;
    float              m_progressT = 0; ///< seconds since something was collected
    int                m_collected = 0;
    bool               m_wasDead = false;
};

}   // namespace kepler
