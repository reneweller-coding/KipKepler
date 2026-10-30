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

bool overlaps( float l0, float t0, float r0, float b0, float l1, float t1, float r1, float b1 )
{
    return l0 < r1 && r0 > l1 && t0 < b1 && b0 > t1;
}

/** @brief Around a move from (x, y) to (tx, ty): room for a spring's throw above, a fall below and a run beside. */
void around( float x, float y, float tx, float ty, float box[4] )
{
    box[0] = std::min( x, tx ) - 12 * T, box[2] = std::max( x, tx ) + 12 * T;
    box[1] = std::min( y, ty ) - 13 * T, box[3] = std::max( y, ty ) + 6 * T;
}

/** @brief The level a few seconds ahead: the platforms near a move run on, everything else as the world has it. */
class Ahead : public Collider
{
public:
    Ahead( const World &w, float x, float y, float tx, float ty ) : m_w( w )
    {
        float box[4];
        around( x, y, tx, ty, box );
        for ( const Mover &m : w.m_movers )
            if ( overlaps( box[0], box[1], box[2], box[3], std::min( m.m_x0, m.m_x0 + m.m_dx ),
                           std::min( m.m_y0, m.m_y0 + m.m_dy ) - T, std::max( m.m_x0, m.m_x0 + m.m_dx ) + m.m_w * T,
                           std::max( m.m_y0, m.m_y0 + m.m_dy ) + T ) )
                m_movers.push_back( m );
    }
    bool solid( int cx, int cy ) const override { return m_w.solid( cx, cy ); }
    bool oneway( int cx, int cy ) const override { return m_w.oneway( cx, cy ); }
    bool icy( int cx, int cy ) const override { return m_w.icy( cx, cy ); }
    bool platformTop( float x0, float x1, float before, float after, float &top ) const override
    {
        bool found = false;
        for ( const Mover &m : m_movers )
            if ( x1 > m.m_x && x0 < m.m_x + m.m_w * T && before <= m.m_y + 0.5f && after >= m.m_y &&
                 ( !found || m.m_y < top ) )
                top = m.m_y, found = true;
        return found;
    }
    /** @brief Whether the hero stands on one of the platforms. */
    bool riding( const HeroBody &b ) const
    {
        for ( const Mover &m : m_movers )
            if ( b.m_ground && std::fabs( b.m_y - m.m_y ) < 1 && b.right() > m.m_x && b.left() < m.m_x + m.m_w * T )
                return true;
        return false;
    }

    const World       &m_w;
    std::vector<Mover> m_movers;
};

/** @brief Where a laser fence or a crusher can hurt at all (its beam on, its full drop). */
bool reachOf( const World &w, const Object &o, float box[4] )
{
    if ( o.m_kind == "laser" ) return w.hazard( o, 0, box );
    if ( o.m_kind != "crusher" ) return false;
    box[0] = o.m_cx * T, box[1] = o.m_cy * T, box[2] = box[0] + T;
    box[3] = box[1] + T + ( o.m_args.empty() ? 3 : (float)atof( o.m_args[0].c_str() ) ) * T;
    return true;
}

/** @brief Whether the hero standing at (x, y) has firm ground under some part of him (no platform that moves). */
bool standsFirm( const World &w, float x, float y )
{
    int row = (int)std::floor( ( y + 1 ) / T );
    for ( int cx = (int)std::floor( ( x - phys::HeroW * 0.5f ) / T );
          cx <= (int)std::floor( ( x + phys::HeroW * 0.5f - 0.01f ) / T ); ++cx )
        if ( w.solid( cx, row ) || w.oneway( cx, row ) ) return true;
    return false;
}

/**
 * @brief Whether the hero stays safe holding a direction for a while and then standing (the platforms running on):
 *        nothing hurts him and he does not fall more than a cell and a half.
 * @param[in] w      the world
 * @param[in] dir    -1, 0, 1
 * @param[in] hold   seconds the direction is held
 * @param[in] total  seconds looked ahead
 * @return whether he stays safe
 */
bool holdSafe( const World &w, int dir, float hold, float total )
{
    HeroBody b = w.m_hero;
    Ahead    a( w, b.m_x, b.m_y, b.m_x, b.m_y );
    float    y0 = b.m_y;
    for ( int i = 0; i < (int)( total / phys::Step ); ++i )
    {
        float t = ( i + 1 ) * phys::Step;
        for ( Mover &m : a.m_movers )
        {
            advanceMover( m, phys::Step );
            if ( b.m_ground && b.right() > m.m_px && b.left() < m.m_px + m.m_w * T &&
                 std::fabs( b.m_y - m.m_py ) < 1.0f )
            {
                // Carried along -- unless a wall stops him (then the platform slides away under him).
                float nx = b.m_x + m.m_x - m.m_px;
                int   row0 = (int)std::floor( ( b.top() + 1 ) / T ), row1 = (int)std::floor( ( b.m_y - 1 ) / T );
                int col = (int)std::floor( ( nx + ( m.m_x > m.m_px ? phys::HeroW * 0.5f : -phys::HeroW * 0.5f ) ) / T );
                bool wall = false;
                for ( int r = row0; r <= row1; ++r ) wall |= w.solid( col, r );
                if ( !wall ) b.m_x = nx;
                b.m_y = m.m_y;
            }
        }
        HeroInput in;
        in.m_dir = t < hold ? dir : 0;
        stepHero( b, in, a, phys::Step );
        bool liquid = false;
        if ( w.m_level.hurts( b.left(), b.top(), b.right(), b.m_y, liquid ) || b.m_y > y0 + 1.5f * T ) return false;
        for ( const Object &o : w.m_objects )
        {
            float box[4];
            if ( ( o.m_kind == "laser" || o.m_kind == "crusher" ) && std::fabs( o.m_x - b.m_x ) < 12 * T &&
                 w.hazard( o, o.m_t + t, box ) &&
                 overlaps( b.left(), b.top(), b.right(), b.m_y, box[0], box[1], box[2], box[3] ) )
                return false;
        }
    }
    return true;
}

/**
 * @brief A move as the autopilot's MOVE replays it, the platforms, laser fences and crushers running on by their clocks
 *        and springs acting: it has to end near where it leads (or on a platform that carries on), touch nothing that
 *        hurts on the way and stay unhurt for a moment after.
 * @param[in]  w      the world
 * @param[in]  to     where the move leads
 * @param[in]  e      the move
 * @param[in]  b      the hero when it begins
 * @param[in]  a      the platforms when it begins
 * @param[in]  clock  how far the laser fences' and crushers' clocks are ahead of the world's
 * @param[out] why    why not (may be null)
 * @return whether it lands safely
 */
bool replay( const World &w, const ReachNode &to, const ReachEdge &e, HeroBody b, Ahead a, float clock,
             std::string *why = nullptr )
{
    const ReachPrim &p = reachPrims()[e.m_prim % 100000];
    float            room[4], reach[4];
    around( b.m_x, b.m_y, to.m_x, to.m_y, room );
    std::vector<const Object *> near;
    for ( const Object &o : w.m_objects )
        if ( ( o.m_kind == "laser" || o.m_kind == "crusher" )
                 ? reachOf( w, o, reach ) &&
                       overlaps( room[0], room[1], room[2], room[3], reach[0], reach[1], reach[2], reach[3] )
                 : ( o.m_kind == "spring" || o.m_kind == "teleport" ) && o.m_x > room[0] && o.m_x < room[2] &&
                       o.m_y > room[1] && o.m_y < room[3] + T )
            near.push_back( &o );
    bool phase2 = false, left = false;
    int  startCell = (int)std::floor( b.m_x / T ), landed = -1;
    // A teleporter under the hero when the move begins (he arrived on it) waits until he has stepped off.
    std::vector<const Object *> locked;
    for ( const Object *o : near )
        if ( o->m_kind == "teleport" && overlaps( b.left(), b.top(), b.right(), b.m_y, o->m_cx * T, o->m_cy * T,
                                                  ( o->m_cx + 1 ) * T, ( o->m_cy + 1 ) * T ) )
            locked.push_back( o );
    auto no = [&]( const char *what )
    {
        if ( why )
            *why = std::string( what ) + " at " + std::to_string( (int)b.m_x ) + "," + std::to_string( (int)b.m_y ) +
                   " (to " + std::to_string( (int)to.m_x ) + "," + std::to_string( (int)to.m_y ) + ")";
        return false;
    };
    for ( int i = 0; i < (int)( 5.0f / phys::Step ); ++i )
    {
        float t = ( i + 1 ) * phys::Step;
        for ( Mover &m : a.m_movers )
        {
            advanceMover( m, phys::Step );
            if ( b.m_ground && b.right() > m.m_px && b.left() < m.m_px + m.m_w * T &&
                 std::fabs( b.m_y - m.m_py ) < 1.0f )
                b.m_x += m.m_x - m.m_px, b.m_y = m.m_y;
        }
        // Conveyors push what stands on them (as World::stepHero).
        b.m_pushX = 0;
        if ( b.m_ground )
        {
            int row = (int)std::floor( ( b.m_y + 1 ) / T );
            for ( int cx : { (int)std::floor( b.left() / T ), (int)std::floor( ( b.right() - 1 ) / T ) } )
                if ( w.m_level.inside( cx, row ) && w.m_level.at( cx, row ).m_kind == CellE::CONVEYOR )
                    b.m_pushX = w.m_level.at( cx, row ).m_aux ? 90.0f : -90.0f;
        }
        HeroInput in;
        if ( landed < 0 ) in = reachInput( p, i, b.m_x, startCell, phase2 );
        stepHero( b, in, a, phys::Step );
        if ( !b.m_ground ) left = true;
        bool liquid = false;
        if ( w.m_level.hurts( b.left(), b.top(), b.right(), b.m_y, liquid ) || b.m_y > w.m_level.m_h * T )
            return no( "hurt" );
        for ( const Object *o : near )
        {
            float l = o->m_cx * T, top = o->m_cy * T, box[4];
            bool  inCell = overlaps( b.left(), b.top(), b.right(), b.m_y, l, top, l + T, top + T );
            if ( o->m_kind == "spring" )
            {
                if ( inCell && b.m_vy >= 0 && b.m_y >= top + 8 )
                    b.m_vy = -phys::SpringJump, b.m_noCut = true, b.m_ground = false, left = true;
            }
            else if ( o->m_kind == "teleport" )
            {
                // Where it leads the look-ahead cannot follow: what came before was safe.
                auto lk = std::find( locked.begin(), locked.end(), o );
                if ( lk != locked.end() )
                {
                    if ( !inCell ) locked.erase( lk );
                }
                else if ( inCell )
                    return true;
            }
            else if ( w.hazard( *o, o->m_t + clock + t, box ) &&
                      overlaps( b.left(), b.top(), b.right(), b.m_y, box[0], box[1], box[2], box[3] ) )
                return no( o->m_kind.c_str() );
        }
        if ( landed < 0 )
        {
            if ( !( b.m_ground && ( left || ( phase2 && std::fabs( b.m_vx ) < 1 ) || b.m_hitWall ) && t > 0.02f ) )
                continue;
            float dx = std::fabs( b.m_x - to.m_x ), dy = std::fabs( b.m_y - to.m_y );
            if ( dx > 1.5f * T || dy > ( a.riding( b ) ? 4.0f : 1.5f ) * T ) return no( "landed" );
            landed = i;
        }
        else if ( ( i - landed ) * phys::Step > 0.4f )
            return true;
    }
    return no( "no landing" );
}

}   // namespace

void Bot::start( const World &w )
{
    buildGraph( w.m_level, m_graph );
    m_mode = ModeE::PLAN;
    m_failed.clear();
    m_impossible.clear();
    m_deaths.clear();
    m_misses.clear();
    m_possible.clear();
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
        // Not on a known place: walk to the nearest one on this floor -- or, standing on what the checker never
        // stood on (the last of a column of blocks shot away), off the edge towards the nearest one below.
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
        for ( size_t i = 0; i < m_graph.m_nodes.size() && pick < 0 && best >= 7 * T; ++i )
        {
            const ReachNode &r = m_graph.m_nodes[i];
            float            dx = std::fabs( r.m_x - w.m_hero.m_x );
            if ( r.m_fy <= fy || r.m_fy > fy + 12 || r.m_keys != keys || r.m_toggles != toggles || dx < 0.75f * T ||
                 dx > 12 * T )
                continue;
            float d = dx + ( r.m_fy - fy ) * T * 0.5f;
            if ( d < 14 * T && ( pick < 0 || d < best ) ) best = d, pick = (int)i;
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

    // Riding a platform the hero cannot wait at a place: only the moves the look-ahead lets go now lead on from here.
    bool riding = false;
    for ( const Mover &m : w.m_movers )
        riding |=
            std::fabs( w.m_hero.m_y - m.m_y ) < 2 && w.m_hero.right() > m.m_x && w.m_hero.left() < m.m_x + m.m_w * T;
    // Breadth first over the moves to the nearest move that touches something wanted (or a place to fight from).
    // The timed moves on the way found are checked (do they work at any moment? the first one from a platform: now?)
    // and the search runs again without those that do not.
    std::vector<int> parent, parentEdge;
    std::set<long>   notNow;
    m_budget = 6;
    int foundNode = -1, foundEdge = -1;
    for ( int round = 0; round < 64; ++round )
    {
        parent.assign( m_graph.m_nodes.size(), -2 );
        parentEdge.assign( m_graph.m_nodes.size(), -1 );
        std::deque<int> queue = { n };
        parent[n] = -1;
        foundNode = foundEdge = -1;
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
                long             key = (long)u * 4096 + (long)e;
                auto             f = m_failed.find( key );
                auto             p = m_possible.find( key );
                if ( ( f != m_failed.end() && f->second >= 2 ) || m_impossible.count( key ) ||
                     ( p != m_possible.end() && !p->second ) || ( u == n && notNow.count( key ) ) )
                    continue;
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
        if ( foundNode < 0 ) break;
        // The way from here, first move first.
        std::vector<std::pair<int, int>> way = { { foundNode, foundEdge } };
        for ( int u = foundNode; parent[u] >= 0; u = parent[u] )
            way.insert( way.begin(), { parent[u], parentEdge[u] } );
        bool clear = true;
        for ( auto [u, e] : way )
        {
            const ReachEdge &edge = m_graph.m_nodes[u].m_edges[e];
            bool             first = u == n;
            float            x = first ? w.m_hero.m_x : edge.m_x, y = first ? w.m_hero.m_y : m_graph.m_nodes[u].m_y;
            if ( edge.m_prim < 0 || !timed( w, edge, x, y ) ) continue;
            if ( first && riding ? forecast( w, edge ) : possible( w, u, e ) ) continue;
            if ( first && riding ) notNow.insert( (long)u * 4096 + e );
            clear = false;
            break;
        }
        if ( clear ) break;
        foundNode = -1;
    }
    if ( foundNode < 0 && riding )
    {
        // Nothing to do from the platform just now: let it carry on and look again in a moment.
        m_rideT = 0.1f;
        m_status = "ride";
        return false;
    }
    if ( foundNode < 0 )
    {
        // Moves given up for good may have been the only way after all: try them all again once more.
        if ( !m_impossible.empty() ) m_impossible.clear(), m_deaths.clear(), m_misses.clear();
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

bool Bot::timed( const World &w, const ReachEdge &e, float x, float y ) const
{
    if ( e.m_prim < 0 ) return false;
    const ReachNode &to = m_graph.m_nodes[e.m_to];
    // Beginning on a platform (no firm ground under the start).
    if ( !standsFirm( w, x, y ) ) return true;
    // Landing where only a platform can be (a move found with the platforms elsewhere lands on firm ground).
    if ( e.m_prim < 100000 )
    {
        int r = to.m_fy, c = to.m_fx;
        if ( !( w.solid( c, r ) || w.oneway( c, r ) || w.solid( c - 1, r ) || w.solid( c + 1, r ) ) ) return true;
    }
    // A platform's way crossing the move's (the checker has a platform at every stop: a run along them is a
    // bridge that is not there).
    float mx0 = std::min( x, to.m_x ) - T, mx1 = std::max( x, to.m_x ) + T;
    float my0 = std::min( y, to.m_y ) - 4 * T, my1 = std::max( y, to.m_y ) + T;
    for ( const Mover &m : w.m_movers )
        if ( overlaps( mx0, my0, mx1, my1, std::min( m.m_x0, m.m_x0 + m.m_dx ), std::min( m.m_y0, m.m_y0 + m.m_dy ) - T,
                       std::max( m.m_x0, m.m_x0 + m.m_dx ) + m.m_w * T, std::max( m.m_y0, m.m_y0 + m.m_dy ) + T ) )
            return true;
    // Laser fences and crushers anywhere near the way (with room for the jump's arc).
    float x0 = std::min( x, to.m_x ) - 4 * T, x1 = std::max( x, to.m_x ) + 4 * T;
    float y0 = std::min( y, to.m_y ) - 8 * T, y1 = std::max( y, to.m_y ) + 3 * T, box[4];
    for ( const Object &o : w.m_objects )
        if ( reachOf( w, o, box ) && overlaps( x0, y0, x1, y1, box[0], box[1], box[2], box[3] ) ) return true;
    return false;
}

bool Bot::forecast( const World &w, const ReachEdge &e, std::string *why ) const
{
    const ReachNode &to = m_graph.m_nodes[e.m_to];
    return replay( w, to, e, w.m_hero, Ahead( w, w.m_hero.m_x, w.m_hero.m_y, to.m_x, to.m_y ), 0, why );
}

bool Bot::possible( const World &w, int node, int edge )
{
    // Whether the move works at any moment of the platforms' round trip, the hero standing at its start until then
    // (what does not cannot work from here at all: the checker's platforms stand at every stop, a run along them is a
    // bridge that is never there).
    long key = (long)node * 4096 + edge;
    auto it = m_possible.find( key );
    if ( it != m_possible.end() ) return it->second;
    const ReachNode &from = m_graph.m_nodes[node];
    const ReachEdge &e = from.m_edges[edge];
    const ReachNode &to = m_graph.m_nodes[e.m_to];
    HeroBody         b = w.m_hero;
    b.m_x = e.m_x, b.m_y = from.m_y, b.m_vx = b.m_vy = 0, b.m_ground = true, b.m_pushX = 0;
    // A platform's stop: only riding there tells.
    if ( !standsFirm( w, b.m_x, b.m_y ) ) return m_possible[key] = true;
    // A plan checks only a few moves it has not seen before: the rest count as possible until a later plan has
    // looked (the wait at the move's start finds out too).
    if ( m_budget <= 0 ) return true;
    --m_budget;
    Ahead a( w, b.m_x, b.m_y, to.m_x, to.m_y );
    bool  ok = false;
    for ( float wait = 0; wait <= waitLimit( w, b.m_x, b.m_y ) - 4 && !ok; wait += 0.25f )
    {
        ok = replay( w, to, e, b, a, wait );
        for ( int k = 0; k < (int)( 0.25f / phys::Step + 0.5f ); ++k )
            for ( Mover &m : a.m_movers ) advanceMover( m, phys::Step );
    }
    return m_possible[key] = ok;
}

float Bot::waitLimit( const World &w, float x, float y ) const
{
    // The longest round trip of the platforms near the place (there and back with the rests), at least a few seconds
    // for laser fences and crushers.
    float most = 4;
    for ( const Mover &m : w.m_movers )
        if ( std::fabs( m.m_x - x ) < 30 * T && std::fabs( m.m_y - y ) < 30 * T && m.m_speed > 0 )
            most = std::max( most, 2 * std::hypot( m.m_dx, m.m_dy ) / m.m_speed + 2 * m.m_wait );
    return most + 4;
}

void Bot::ride( const World &w, Controls &c )
{
    // Standing on a platform is safe unless it carries the hero into a wall or a laser: a few times a second look
    // ahead, and step to the side that stays safe.
    m_rideCheckT -= phys::Step;
    if ( m_rideCheckT <= 0 )
    {
        m_rideCheckT = 0.1f;
        m_rideDir = 0;
        if ( !holdSafe( w, 0, 0, 1.5f ) )
            for ( int d : { 1, -1 } )
                if ( holdSafe( w, d, 0.3f, 1.5f ) )
                {
                    m_rideDir = d;
                    break;
                }
    }
    if ( m_rideDir ) ( m_rideDir > 0 ? c.m_right : c.m_left ) = true;
}

void Bot::steer( const World &w, Controls &c ) const
{
    const HeroBody &h = w.m_hero;
    // The spring under the hero (if any): the places that do not stand on it.
    const Object *spring = nullptr;
    for ( const Object &o : w.m_objects )
        if ( o.m_kind == "spring" && std::fabs( o.m_x - h.m_x ) < ( T + phys::HeroW ) * 0.5f + 2 &&
             o.m_cy * T > h.m_y - T )
            spring = &o;
    float fromX = spring ? spring->m_x : h.m_x, fromY = spring ? spring->m_y : h.m_y, best = 1e9f, goal = h.m_x;
    int   keys = keysOf( w ), toggles = (int)( w.m_groups & 255 );
    for ( const ReachNode &r : m_graph.m_nodes )
    {
        if ( r.m_keys != keys || r.m_toggles != toggles ) continue;
        if ( spring && std::fabs( r.m_x - spring->m_x ) < ( T + phys::HeroW ) * 0.5f + 2 ) continue;
        float d = std::hypot( r.m_x - fromX, r.m_y - fromY );
        if ( d < best ) best = d, goal = r.m_x;
    }
    if ( std::fabs( goal - h.m_x ) > 2 ) ( goal > h.m_x ? c.m_right : c.m_left ) = true;
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
        // A move that ended in death is not tried again soon, after the second death never again (the watchdog
        // forgets failures, not deaths).
        if ( w.m_dead && m_mode == ModeE::MOVE && m_from >= 0 )
        {
            long key = (long)m_from * 4096 + m_edgeIndex;
            m_failed[key] += 2;
            if ( ++m_deaths[key] >= 2 ) m_impossible[key] = 1;
        }
        m_mode = ModeE::PLAN;
        return c;
    }
    const HeroBody &h = w.m_hero;
    m_airT = h.m_ground ? 0 : m_airT + dt;
    // A minute without collecting anything: forget the failed moves and shake loose.
    if ( m_progressT > 60 && m_mode != ModeE::MOVE && m_mode != ModeE::BOSS )
    {
        m_failed.clear();
        m_progressT = 30;
        ++m_stalls;
        if ( m_trace )
            fprintf( m_trace,
                     "t=%.1f WATCHDOG %s at x=%.1f y=%.1f ground %d vx %.0f vy %.0f push %.0f mode %d here %d\n",
                     w.m_time, m_status.c_str(), h.m_x, h.m_y, h.m_ground ? 1 : 0, h.m_vx, h.m_vy, h.m_pushX,
                     (int)m_mode, here( w ) );
        m_mode = ModeE::WANDER;
        m_modeT = 0;
        m_wanderDir = GetRandomValue( 0, 1 ) ? 1 : -1;
    }
    // KEPLER_TRACE_FROM=<seconds>: two and a half seconds of the bot's state from then on, into the trace.
    if ( m_trace && getenv( "KEPLER_TRACE_FROM" ) && w.m_time >= atof( getenv( "KEPLER_TRACE_FROM" ) ) &&
         w.m_time < atof( getenv( "KEPLER_TRACE_FROM" ) ) + 2.5f && ( (int)( w.m_time / phys::Step ) % 12 ) == 0 )
        fprintf( m_trace, "DBG t=%.2f mode %d x %.1f y %.1f g %d hp %.0f status %s edge prim %d x %.1f to %d\n",
                 w.m_time, (int)m_mode, h.m_x, h.m_y, h.m_ground ? 1 : 0, w.m_hp, m_status.c_str(), m_edge.m_prim,
                 m_edge.m_x, m_edge.m_to );
    switch ( m_mode )
    {
    case ModeE::PLAN:
        if ( !h.m_ground )
        {
            // Nothing keeps the hero in the air this long but a spring that bounces him again and again.
            if ( m_airT > 0.8f ) steer( w, c );
            break;
        }
        if ( m_rideT > 0 )
        {
            m_rideT -= dt;
            ride( w, c );
            fight( w, c );
            break;
        }
        if ( plan( w ) )
        {
            m_noPlanT = 0;
            return think( w );
        }
        if ( m_rideT > 0 ) break;
        m_noPlanT += dt;
        if ( m_noPlanT > 0.5f )
        {
            ++m_stalls;
            // Moves that failed may work from a slightly different spot: give them another chance.
            m_failed.clear();
            if ( m_trace )
            {
                // What the hero stands on: the cells below and around his feet (solid?), movers, frozen enemies.
                std::string under;
                for ( int dx = -1; dx <= 1; ++dx )
                {
                    int cx = (int)std::floor( h.m_x / T ) + dx, cy = (int)std::floor( ( h.m_y + 1 ) / T );
                    under += std::to_string( (int)w.m_level.at( cx, cy ).m_kind ) + ( w.solid( cx, cy ) ? "s" : "" ) +
                             ( w.oneway( cx, cy ) ? "o" : "" ) + " ";
                }
                float top = 0;
                bool  plat = w.platformTop( h.left(), h.right(), h.m_y - 1, h.m_y + 1, top );
                fprintf( m_trace, "t=%.1f STALL %s x=%.1f y=%.1f under %s platform %d\n", w.m_time, m_status.c_str(),
                         h.m_x, h.m_y, under.c_str(), plat ? 1 : 0 );
            }
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
        float dx = m_edge.m_x - h.m_x;
        if ( !h.m_ground )
        {
            // A move that begins on a spring (the checker stood there) begins when the spring throws the hero.
            bool spring = false;
            if ( m_edge.m_prim >= 0 && m_from >= 0 && std::fabs( dx ) < T )
                for ( const Object &o : w.m_objects )
                    spring |= o.m_kind == "spring" &&
                              overlaps( m_edge.m_x - phys::HeroW * 0.5f, m_graph.m_nodes[m_from].m_y - phys::HeroH,
                                        m_edge.m_x + phys::HeroW * 0.5f, m_graph.m_nodes[m_from].m_y, o.m_cx * T,
                                        o.m_cy * T, ( o.m_cx + 1 ) * T, ( o.m_cy + 1 ) * T );
            if ( !spring )
            {
                // Slipped off on the way to the move's start (ice, a ledge): that counts against the move.
                if ( m_from >= 0 && m_edge.m_prim >= 0 )
                {
                    long key = (long)m_from * 4096 + m_edgeIndex;
                    ++m_failed[key];
                    if ( ++m_misses[key] >= 3 ) m_impossible[key] = 1;
                }
                m_mode = ModeE::PLAN;
                break;
            }
            m_mode = ModeE::MOVE;
            m_step = 0;
            m_phase2 = false;
            m_startCell = (int)std::floor( m_edge.m_x / T );
            m_left = true;
            m_lastX = h.m_x, m_lastY = h.m_y;
            m_modeT = 0;
            return think( w );
        }
        // On a conveyor the hero never stands still, crumbling blocks give way, movers carry him on: close enough
        // is enough there.
        int   row = (int)std::floor( ( h.m_y + 1 ) / T );
        bool  crumble = false, staticFloor = false;
        for ( int cx = (int)std::floor( h.left() / T ); cx <= (int)std::floor( ( h.right() - 0.01f ) / T ); ++cx )
        {
            if ( w.m_level.inside( cx, row ) && w.m_level.at( cx, row ).m_kind == CellE::CRUMBLE ) crumble = true;
            if ( w.solid( cx, row ) || w.oneway( cx, row ) ) staticFloor = true;
        }
        // On ice the hero slides a long way before he stops: close (and slow) is enough there too.
        bool loose = h.m_pushX != 0 || crumble || !staticFloor || h.m_icy;
        bool riding = !staticFloor && h.m_pushX == 0 && !crumble;
        // On a crumbling block there is no time to walk about: the move starts where the hero is.
        float tolerance = crumble ? 40.0f : riding ? 24.0f : h.m_icy ? 16.0f : 12.0f;
        bool  there = ( std::fabs( dx ) < 2.0f && std::fabs( h.m_vx ) < 6 ) ||
                      ( loose && std::fabs( dx ) < tolerance && ( !h.m_icy || std::fabs( h.m_vx ) < 40 ) );
        // On a platform the place a move was found at has moved on: only the look-ahead decides.
        if ( riding && m_edge.m_prim >= 0 ) there = true;
        // Never step off a ledge on the way to where a move begins (the checker may stand on its last half pixel):
        // close to it is close enough then.
        bool brink = m_edge.m_prim >= 0 && staticFloor && !standsFirm( w, h.m_x + ( dx > 0 ? 3 : -3 ), h.m_y );
        if ( brink && std::fabs( dx ) < 10 && std::fabs( h.m_vx ) < 40 ) there = true;
        // A move whose timing matters starts when the look-ahead lands it safely (tried again a few steps later);
        // crumbling blocks do not wait.
        bool timing = !crumble && timed( w, m_edge, h.m_x, h.m_y ), ready = true;
        if ( there && timing )
        {
            if ( m_forecastWait > 0 )
                --m_forecastWait, ready = false;
            else if ( std::string why; !( ready = forecast( w, m_edge, m_trace && m_modeT < 0.1f ? &why : nullptr ) ) )
            {
                if ( m_trace && m_modeT < 0.1f )
                    fprintf( m_trace, "t=%.1f wait for move %d (%s)\n", w.m_time, m_edge.m_prim, why.c_str() );
                m_forecastWait = 3;
            }
        }
        if ( riding && !( there && ready ) )
        {
            // Riding a platform: stand still and let it carry (walking to a place of the world would walk off it);
            // think again in a moment.
            if ( m_modeT > 0.25f ) m_mode = ModeE::PLAN;
            ride( w, c );
            fight( w, c );
            break;
        }
        if ( there && ready )
        {
            m_modeT = 0;
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
                if ( m_trace && timing )
                    fprintf( m_trace, "t=%.1f go move %d (look-ahead)\n", w.m_time, m_edge.m_prim );
                // The move begins with this very step (as the look-ahead had it).
                return think( w );
            }
            break;
        }
        // Run there and let the deceleration stop on the spot.
        float stop = h.m_vx * h.m_vx / ( 2 * ( h.m_icy ? phys::DecIce : phys::DecGround ) );
        int   dir = dx > 0 ? 1 : -1;
        if ( !there && !brink && ( h.m_vx * dir < 0 || std::fabs( dx ) > stop + 0.4f ) )
            ( dir > 0 ? c.m_right : c.m_left ) = true;
        if ( m_modeT > ( timing ? waitLimit( w, h.m_x, h.m_y ) : 3.0f ) )
        {
            if ( m_trace ) fprintf( m_trace, "t=%.1f approach to x %.1f failed at x %.1f\n", w.m_time, m_edge.m_x, h.m_x );
            // A timed move the look-ahead never let go through a whole cycle of the platforms cannot work from here.
            if ( m_from >= 0 ) ( there && timing ? m_impossible : m_failed )[(long)m_from * 4096 + m_edgeIndex] += 2;
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
                if ( now != m_edge.m_to && m_from >= 0 )
                {
                    // A move that keeps landing elsewhere is given up for good (the watchdog forgets failures).
                    long key = (long)m_from * 4096 + m_edgeIndex;
                    ++m_failed[key];
                    if ( ++m_misses[key] >= 3 ) m_impossible[key] = 1;
                }
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
