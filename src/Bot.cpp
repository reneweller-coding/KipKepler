/**
 * @file Bot.cpp
 * @brief The autopilot.
 * @author Rene Weller
 */
#include "Bot.h"

#include <algorithm>
#include <cmath>
#include <deque>
#include <set>

namespace kepler
{

namespace
{

constexpr float T = (float)Tile;

int keysOf( const World &w )
{
    return ( w.m_keys[0] ? 1 : 0 ) | ( w.m_keys[1] ? 2 : 0 );
}

}   // namespace

void Bot::start( const World &w )
{
    buildGraph( w.m_level, m_graph );
    m_mode = ModeE::PLAN;
    m_failed.clear();
    m_status = "graph " + std::to_string( m_graph.m_nodes.size() ) + " places";
}

int Bot::here( const World &w ) const
{
    int fx = (int)std::floor( w.m_hero.m_x / T ), fy = (int)std::lround( w.m_hero.m_y / T );
    int keys = keysOf( w ), toggles = (int)( w.m_groups & 255 );
    int n = m_graph.find( fx, fy, keys, toggles );
    if ( n < 0 ) n = m_graph.find( (int)std::floor( ( w.m_hero.m_x - 9 ) / T ), fy, keys, toggles );
    if ( n < 0 ) n = m_graph.find( (int)std::floor( ( w.m_hero.m_x + 9 ) / T ), fy, keys, toggles );
    return n;
}

bool Bot::plan( const World &w )
{
    int n = here( w );
    if ( n < 0 )
    {
        // Not on a known place: walk to the nearest one on this floor.
        int   fy = (int)std::lround( w.m_hero.m_y / T ), keys = keysOf( w ), toggles = (int)( w.m_groups & 255 );
        float best = 7 * T;
        int   pick = -1;
        for ( size_t i = 0; i < m_graph.m_nodes.size(); ++i )
        {
            const ReachNode &r = m_graph.m_nodes[i];
            if ( r.m_fy != fy || r.m_keys != keys || r.m_toggles != toggles ) continue;
            float d = std::fabs( r.m_x - w.m_hero.m_x );
            if ( d < best ) best = d, pick = (int)i;
        }
        if ( pick < 0 )
        {
            ++m_lost;
            m_status = "lost at " + std::to_string( (int)( w.m_hero.m_x / T ) ) + "," + std::to_string( fy );
            return false;
        }
        m_edge = { pick, -1, m_graph.m_nodes[pick].m_x, {} };
        m_from = -1;
        m_mode = ModeE::APPROACH;
        m_modeT = 0;
        m_status = "to a known place";
        return true;
    }
    // What is still wanted: crystals, keys, weapons; the exit once it is open.
    std::set<int> wanted;
    for ( const Pickup &p : w.m_pickups )
        if ( !p.m_taken && p.m_spawn >= 0 &&
             ( p.m_kind == PickE::CRYSTAL || p.m_kind == PickE::KEY_BLUE || p.m_kind == PickE::KEY_GOLD || p.m_kind == PickE::WEAPON ) )
            wanted.insert( p.m_spawn );
    if ( w.m_exitOpen )
        for ( const Object &o : w.m_objects )
            if ( o.m_kind == "exit" ) wanted.insert( o.m_spawn );
    // With nothing else left and the boss alive: places at a fair distance from it are the goal.
    std::vector<char> fightFrom;
    const Enemy      *boss = w.m_bossIndex >= 0 && w.m_enemies[w.m_bossIndex].m_alive ? &w.m_enemies[w.m_bossIndex] : nullptr;
    if ( wanted.empty() && boss && !w.m_exitOpen )
    {
        fightFrom.assign( m_graph.m_nodes.size(), 0 );
        int keys = keysOf( w ), toggles = (int)( w.m_groups & 255 );
        for ( size_t i = 0; i < m_graph.m_nodes.size(); ++i )
        {
            const ReachNode &r = m_graph.m_nodes[i];
            float            dx = std::fabs( r.m_x - boss->m_x ), dy = std::fabs( r.m_y - boss->m_y );
            if ( r.m_keys == keys && r.m_toggles == toggles && dx > 100 && dx < 300 && dy < 70 ) fightFrom[i] = 1;
        }
        if ( fightFrom[n] )
        {
            m_mode = ModeE::BOSS;
            m_modeT = 0;
            m_status = "boss";
            return true;
        }
    }
    if ( wanted.empty() && fightFrom.empty() ) return false;

    // Breadth first over the moves to the nearest move that touches something wanted (or a place to fight from).
    std::vector<int>                 parent( m_graph.m_nodes.size(), -2 ), parentEdge( m_graph.m_nodes.size(), -1 );
    std::deque<int>                  queue = { n };
    parent[n] = -1;
    int foundNode = -1, foundEdge = -1;
    while ( !queue.empty() && foundNode < 0 )
    {
        int u = queue.front();
        queue.pop_front();
        const ReachNode &r = m_graph.m_nodes[u];
        if ( !fightFrom.empty() && fightFrom[u] && u != n && parent[u] >= 0 )
        {
            foundNode = parent[u], foundEdge = parentEdge[u];
            break;
        }
        for ( size_t e = 0; e < r.m_edges.size(); ++e )
        {
            const ReachEdge &edge = r.m_edges[e];
            auto             f = m_failed.find( (long)u * 4096 + (long)e );
            if ( f != m_failed.end() && f->second >= 2 ) continue;
            bool hit = false;
            for ( int t : edge.m_touched ) hit |= wanted.count( t ) > 0;
            if ( hit )
            {
                foundNode = u, foundEdge = (int)e;
                break;
            }
            if ( parent[edge.m_to] == -2 )
            {
                parent[edge.m_to] = u;
                parentEdge[edge.m_to] = (int)e;
                queue.push_back( edge.m_to );
            }
        }
    }
    if ( foundNode < 0 )
    {
        ++m_noWay;
        m_status = "no way from " + std::to_string( m_graph.m_nodes[n].m_fx ) + "," + std::to_string( m_graph.m_nodes[n].m_fy );
        return false;
    }
    // Back to the first move from here.
    int u = foundNode, e = foundEdge;
    while ( parent[u] >= 0 )
    {
        e = parentEdge[u];
        u = parent[u];
    }
    m_from = n;
    m_edgeIndex = e;
    m_edge = m_graph.m_nodes[n].m_edges[e];
    m_mode = ModeE::APPROACH;
    m_modeT = 0;
    m_status = "move " + std::to_string( m_edge.m_prim );
    return true;
}

void Bot::fight( const World &w, Controls &c )
{
    // Shoot what is in front at the cannon's height, or straight above.
    float hx = w.m_hero.m_x, hy = w.m_hero.m_y - 26;
    bool  front = false, above = false;
    for ( const Enemy &e : w.m_enemies )
    {
        if ( !e.m_alive || e.m_hidden ) continue;
        float dx = e.m_x - hx, dy = e.cy() - hy;
        if ( dx * w.m_face > -4 && std::fabs( dx ) < 300 && std::fabs( dy ) < e.m_def->m_h * 0.5f + 10 ) front = true;
        if ( std::fabs( dx ) < 30 && dy < -20 && dy > -260 ) above = true;
    }
    // A breakable block ahead at the cannon's height is in the way: shoot it.
    for ( int k = 0; k <= 2 && !front; ++k )
    {
        int cx = (int)std::floor( ( hx + w.m_face * ( 14 + k * T ) ) / T ), cy = (int)std::floor( hy / T );
        if ( w.solid( cx, cy ) && w.m_level.inside( cx, cy ) && w.m_level.at( cx, cy ).m_kind == CellE::BREAKABLE ) front = true;
        else if ( w.solid( cx, cy ) )
            break;
    }
    if ( !front && above ) c.m_up = true;
    if ( front || above )
    {
        c.m_fire = true;
        if ( m_fireT <= 0 )
        {
            c.m_firePressed = true;
            m_fireT = 0.27f;
        }
    }
}

Controls Bot::think( const World &w )
{
    Controls c;
    float    dt = phys::Step;
    m_modeT += dt;
    if ( m_fireT > 0 ) m_fireT -= dt;
    m_progressT += dt;
    int got = w.m_crystalsTaken + ( w.m_keys[0] ? 1 : 0 ) + ( w.m_keys[1] ? 1 : 0 );
    if ( got != m_collected ) m_collected = got, m_progressT = 0;
    if ( w.m_dead && !m_wasDead && m_trace )
    {
        // Why: what is under and around the hero, the nearest enemy, the move that was running.
        const HeroBody &h = w.m_hero;
        std::string     cells;
        for ( int dy = -1; dy <= 1; ++dy )
            for ( int dx = -1; dx <= 1; ++dx )
            {
                int cx = (int)std::floor( h.m_x / T ) + dx, cy = (int)std::floor( ( h.m_y - 1 ) / T ) + dy;
                cells += (char)( '0' + (int)w.m_level.at( cx, cy ).m_kind % 10 );
            }
        float       best = 1e9f;
        std::string near = "-";
        for ( const Enemy &e : w.m_enemies )
            if ( e.m_alive && !e.m_hidden )
            {
                float d = std::hypot( e.m_x - h.m_x, e.cy() - h.m_y + 22 );
                if ( d < best ) best = d, near = e.m_def->m_id;
            }
        for ( const Object &o : w.m_objects )
            if ( ( o.m_kind == "laser" || o.m_kind == "crusher" ) && std::hypot( o.m_x - h.m_x, o.m_y - h.m_y ) < 200 ) near += "+" + o.m_kind;
        fprintf( m_trace, "t=%.1f DEATH at %d,%d cells %s nearest %s %.0f px, mode %d move %d\n", w.m_time, (int)( h.m_x / T ), (int)std::lround( h.m_y / T ),
                 cells.c_str(), near.c_str(), best, (int)m_mode, m_edge.m_prim );
    }
    m_wasDead = w.m_dead;
    if ( w.m_dead || w.m_exitT >= 0 || w.m_appearT > 0 )
    {
        // A move that ended in death is not tried again soon.
        if ( w.m_dead && m_mode == ModeE::MOVE && m_from >= 0 ) m_failed[(long)m_from * 4096 + m_edgeIndex] += 2;
        m_mode = ModeE::PLAN;
        return c;
    }
    const HeroBody &h = w.m_hero;
    // A minute without collecting anything: forget the failed moves and shake loose.
    if ( m_progressT > 60 && m_mode != ModeE::MOVE && m_mode != ModeE::BOSS )
    {
        m_failed.clear();
        m_progressT = 30;
        ++m_stalls;
        if ( m_trace ) fprintf( m_trace, "t=%.1f WATCHDOG %s\n", w.m_time, m_status.c_str() );
        m_mode = ModeE::WANDER;
        m_modeT = 0;
        m_wanderDir = GetRandomValue( 0, 1 ) ? 1 : -1;
    }
    switch ( m_mode )
    {
    case ModeE::PLAN:
        if ( !h.m_ground ) break;
        if ( plan( w ) )
        {
            m_noPlanT = 0;
            return think( w );
        }
        m_noPlanT += dt;
        if ( m_noPlanT > 0.5f )
        {
            ++m_stalls;
            // Moves that failed may work from a slightly different spot: give them another chance.
            m_failed.clear();
            if ( m_trace ) fprintf( m_trace, "t=%.1f STALL %s\n", w.m_time, m_status.c_str() );
            if ( m_stalls <= 6 ) m_stallLog += "[" + m_status + " t=" + std::to_string( (int)w.m_time ) + "]";
            m_mode = ModeE::WANDER;
            m_modeT = 0;
            m_wanderDir = GetRandomValue( 0, 1 ) ? 1 : -1;
            m_noPlanT = 0;
            m_status = "wander";
        }
        break;

    case ModeE::APPROACH:
    {
        if ( !h.m_ground )
        {
            m_mode = ModeE::PLAN;
            break;
        }
        float dx = m_edge.m_x - h.m_x;
        // On a conveyor the hero never stands still, crumbling blocks give way, movers carry him on: close enough
        // is enough there.
        int   row = (int)std::floor( ( h.m_y + 1 ) / T );
        bool  crumble = false, staticFloor = false;
        for ( int cx = (int)std::floor( h.left() / T ); cx <= (int)std::floor( ( h.right() - 1 ) / T ); ++cx )
        {
            if ( w.m_level.inside( cx, row ) && w.m_level.at( cx, row ).m_kind == CellE::CRUMBLE ) crumble = true;
            if ( w.solid( cx, row ) || w.oneway( cx, row ) ) staticFloor = true;
        }
        bool loose = h.m_pushX != 0 || crumble || !staticFloor;
        // A move onto a mover waits until the platform is under where it lands.
        bool moverReady = true;
        if ( m_edge.m_prim >= 0 && m_edge.m_prim < 100000 )
        {
            const ReachNode &to = m_graph.m_nodes[m_edge.m_to];
            int              trow = to.m_fy, tc = to.m_fx;
            bool             floorThere = w.solid( tc, trow ) || w.oneway( tc, trow ) || w.solid( tc - 1, trow ) || w.solid( tc + 1, trow );
            if ( !floorThere )
            {
                moverReady = false;
                for ( const Mover &m : w.m_movers )
                    if ( std::fabs( m.m_y - to.m_y ) < 6 && to.m_x > m.m_x + 8 && to.m_x < m.m_x + m.m_w * T - 8 ) moverReady = true;
            }
        }
        bool riding = !staticFloor && h.m_pushX == 0 && !crumble;
        if ( riding && !( std::fabs( dx ) < 24 && moverReady ) )
        {
            // Riding a platform: walk on it towards the start of the move if that lies on the platform, else stand
            // still and let it carry; think again in a moment.
            bool onIt = false;
            for ( const Mover &m : w.m_movers )
                if ( std::fabs( m.m_y - h.m_y ) < 2 && h.right() > m.m_x && h.left() < m.m_x + m.m_w * T &&
                     m_edge.m_x > m.m_x + 10 && m_edge.m_x < m.m_x + m.m_w * T - 10 )
                    onIt = true;
            if ( onIt ) ( dx > 0 ? c.m_right : c.m_left ) = true;
            if ( m_modeT > 0.25f ) m_mode = ModeE::PLAN;
            fight( w, c );
            break;
        }
        // On a crumbling block there is no time to walk about: the move starts where the hero is.
        float tolerance = crumble ? 40.0f : riding ? 24.0f : 12.0f;
        if ( ( std::fabs( dx ) < 2.0f && std::fabs( h.m_vx ) < 6 && moverReady ) || ( loose && std::fabs( dx ) < tolerance && moverReady ) )
        {
            if ( m_edge.m_prim <= -2 ) m_mode = ModeE::SHOOT;
            else if ( m_edge.m_prim == -1 )
                m_mode = ModeE::PLAN;
            else
            {
                m_mode = ModeE::MOVE;
                m_step = 0;
                m_phase2 = false;
                m_startCell = (int)std::floor( h.m_x / T );
                m_left = false;
                m_lastX = h.m_x, m_lastY = h.m_y;
            }
            m_modeT = 0;
            break;
        }
        // Run there and let the deceleration stop on the spot.
        float stop = h.m_vx * h.m_vx / ( 2 * phys::DecGround );
        int   dir = dx > 0 ? 1 : -1;
        if ( h.m_vx * dir < 0 || std::fabs( dx ) > stop + 0.4f ) ( dir > 0 ? c.m_right : c.m_left ) = true;
        if ( m_modeT > ( moverReady ? 3.0f : 12.0f ) )
        {
            if ( m_trace ) fprintf( m_trace, "t=%.1f approach to x %.1f failed at x %.1f\n", w.m_time, m_edge.m_x, h.m_x );
            if ( m_from >= 0 ) m_failed[(long)m_from * 4096 + m_edgeIndex] += 2;
            m_mode = ModeE::PLAN;
        }
        fight( w, c );
        break;
    }

    case ModeE::MOVE:
    {
        const ReachPrim &p = reachPrims()[m_edge.m_prim % 100000];
        if ( m_step > 0 )
        {
            if ( !h.m_ground ) m_left = true;
            bool jumped = std::fabs( h.m_x - m_lastX ) > 48 || std::fabs( h.m_y - m_lastY ) > 48;
            bool done = h.m_ground && ( m_left || ( m_phase2 && std::fabs( h.m_vx ) < 1 ) || h.m_hitWall ) && m_step * dt > 0.02f;
            if ( done || jumped || m_step * dt > 4 )
            {
                int now = here( w );
                if ( now != m_edge.m_to && m_from >= 0 ) ++m_failed[(long)m_from * 4096 + m_edgeIndex];
                if ( m_trace )
                {
                    const ReachNode &a = m_graph.m_nodes[m_from >= 0 ? m_from : 0], &b = m_graph.m_nodes[m_edge.m_to];
                    fprintf( m_trace, "t=%.1f move %d from %d,%d (x %.1f) to %d,%d -> now %s %d,%d x=%.1f y=%.1f\n", w.m_time, m_edge.m_prim, a.m_fx, a.m_fy, m_edge.m_x, b.m_fx, b.m_fy,
                             now == m_edge.m_to ? "ok" : "MISS", (int)std::floor( h.m_x / T ), (int)std::lround( h.m_y / T ), h.m_x, h.m_y );
                }
                m_mode = ModeE::PLAN;
                break;
            }
        }
        m_lastX = h.m_x, m_lastY = h.m_y;
        HeroInput in = reachInput( p, m_step, h.m_x, m_startCell, m_phase2 );
        c.m_left = in.m_dir < 0;
        c.m_right = in.m_dir > 0;
        c.m_jump = in.m_jump;
        c.m_jumpPressed = in.m_jumpPressed;
        c.m_down = in.m_down;
        ++m_step;
        fight( w, c );
        // Aiming up must not hold while a move runs on: the hero's movement ignores it anyway.
        break;
    }

    case ModeE::SHOOT:
    {
        int dir = m_edge.m_prim == -2 ? -1 : m_edge.m_prim == -3 ? 1 : 0;
        if ( dir && w.m_face != dir ) ( dir > 0 ? c.m_right : c.m_left ) = true;
        else
        {
            c.m_up = dir == 0;
            c.m_fire = true;
            c.m_firePressed = m_modeT < dt * 1.5f || m_fireT <= 0;
            if ( c.m_firePressed ) m_fireT = 0.3f;
        }
        if ( m_modeT > 0.6f ) m_mode = ModeE::PLAN;
        break;
    }

    case ModeE::BOSS:
    {
        // Face the boss, keep firing, hop now and then over shockwaves and shots; think again every few seconds.
        const Enemy *boss = w.m_bossIndex >= 0 && w.m_enemies[w.m_bossIndex].m_alive ? &w.m_enemies[w.m_bossIndex] : nullptr;
        if ( !boss || std::fabs( boss->m_x - h.m_x ) > 360 || m_modeT > 3.0f )
        {
            m_mode = ModeE::PLAN;
            break;
        }
        int dir = boss->m_x < h.m_x ? -1 : 1;
        if ( w.m_face != dir ) ( dir > 0 ? c.m_right : c.m_left ) = true;
        c.m_up = boss->cy() < h.m_y - 90 && std::fabs( boss->m_x - h.m_x ) < 60;
        c.m_fire = true;
        if ( m_fireT <= 0 ) c.m_firePressed = true, m_fireT = 0.2f;
        if ( std::fmod( m_modeT, 1.3f ) < phys::Step * 1.5f ) c.m_jump = true, c.m_jumpPressed = true;
        else if ( !h.m_ground )
            c.m_jump = true;
        break;
    }

    case ModeE::WANDER:
    {
        // A few steps along the floor (never over an edge or into a hazard), then think again.
        float ahead = h.m_x + m_wanderDir * 16;
        int   cx = (int)std::floor( ahead / T ), row = (int)std::floor( ( h.m_y + 1 ) / T );
        bool  floor = w.solid( cx, row ) || w.oneway( cx, row );
        bool  liquid = false;
        if ( !floor || w.m_level.hurts( ahead - 10, h.m_y - 40, ahead + 10, h.m_y + 2, liquid ) || h.m_hitWall ) m_wanderDir = -m_wanderDir;
        else
            ( m_wanderDir > 0 ? c.m_right : c.m_left ) = true;
        fight( w, c );
        if ( m_modeT > 0.8f ) m_mode = ModeE::PLAN;
        break;
    }

    default: m_mode = ModeE::PLAN; break;
    }
    return c;
}

}   // namespace kepler
