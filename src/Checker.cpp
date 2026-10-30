/**
 * @file Checker.cpp
 * @brief The level checker: a search over the places the hero can stand, moving between them with his own physics.
 * @author Rene Weller
 */
#include "Checker.h"

#include "Level.h"
#include "Physics.h"

#include <raylib.h>

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <deque>
#include <set>
#include <thread>
#include <unordered_map>
#include <vector>

namespace kepler
{

namespace
{

constexpr float T = (float)Tile;

/** @brief A moving platform's place at one of its stops (the checker assumes it can be waited for anywhere). */
struct Stop
{
    float m_x0, m_x1, m_top;
};

/** @brief The level as the checker sees it: doors by the keys held, toggles by their groups, movers at all stops. */
class CheckWorld : public Collider
{
public:
    CheckWorld( const Level &level, const std::vector<Stop> &stops ) : m_level( level ), m_stops( stops )
    {
        m_ice = level.key( "theme" ) == "ice";
    }

    bool solid( int cx, int cy ) const override
    {
        if ( cy >= m_level.m_h ) return false;
        const Cell &c = m_level.at( cx, cy );
        switch ( c.m_kind )
        {
        case CellE::CRUMBLE:
        {
            auto it = m_crumbled.find( cy * m_level.m_w + cx );
            return it == m_crumbled.end() || m_now - it->second < 0.5f;
        }
        case CellE::TERRAIN_A:
        case CellE::TERRAIN_B:
        case CellE::CONVEYOR: return true;
        case CellE::DOOR_BLUE: return !( m_keys & 1 );
        case CellE::DOOR_GOLD: return !( m_keys & 2 );
        case CellE::TOGGLE:
        {
            bool on = ( m_toggles >> ( c.m_aux & 7 ) ) & 1;
            bool solidWhenOn = c.m_aux & 8;
            return on == solidWhenOn;
        }
        default: return false;
        }
    }

    bool oneway( int cx, int cy ) const override { return m_level.at( cx, cy ).m_kind == CellE::PLATFORM; }

    bool icy( int cx, int cy ) const override { return m_ice && m_level.at( cx, cy ).m_kind == CellE::TERRAIN_B; }

    bool platformTop( float x0, float x1, float before, float after, float &top ) const override
    {
        if ( m_noMovers ) return false;
        bool found = false;
        for ( const Stop &s : m_stops )
            if ( x1 > s.m_x0 && x0 < s.m_x1 && before <= s.m_top + 0.001f && after >= s.m_top )
                if ( !found || s.m_top < top )
                {
                    top = s.m_top;
                    found = true;
                }
        if ( found ) m_usedMover = true;
        return found;
    }

    const Level             &m_level;
    const std::vector<Stop> &m_stops;
    bool                     m_ice = false;
    int                      m_keys = 0;
    int                      m_toggles = 0;
    bool                     m_noMovers = false;          ///< the movers are elsewhere (falling past them)
    mutable std::unordered_map<int, float> m_crumbled;    ///< crumbling cells stood on in this move: since when
    mutable float            m_now = 0;                   ///< the move's clock
    mutable bool             m_usedMover = false;         ///< a mover carried the hero in this move
};

using Prim = ReachPrim;

std::vector<Prim> makePrims()
{
    std::vector<Prim> p;
    for ( int d : { -1, 1 } )
    {
        p.push_back( { false, 0, d, -1, 0 } );      // one cell along the floor
        p.push_back( { false, 0, d, 99, d } );      // run off the edge
        p.push_back( { false, 0, d, 0.12f, 0 } );   // step off and drop straight
        p.push_back( { false, 0, d, 0.12f, -d } );  // step off and tuck back under
    }
    // Dropping through a one-way platform (down + jump), straight or drifting.
    for ( int d : { -1, 0, 1 } ) p.push_back( { true, 0.05f, d, 99, d, 0, true } );
    // Running jumps: a run-up before the jump (off an edge, coyote time still counts).
    for ( int d : { -1, 1 } )
        for ( float at : { 0.06f, 0.12f, 0.2f } )
            for ( float hold : { 0.15f, 9.0f } )
            {
                p.push_back( { true, hold + at, d, 99, d, at } );
                p.push_back( { true, hold + at, d, at + 0.3f, 0, at } );
            }
    for ( float hold : { 0.07f, 0.15f, 9.0f } )
        for ( int d1 : { -1, 0, 1 } )
        {
            p.push_back( { true, hold, d1, 99, d1 } );
            for ( float t1 : { 0.1f, 0.25f, 0.42f } )
                for ( int d2 : { -1, 0, 1 } )
                    if ( d2 != d1 ) p.push_back( { true, hold, d1, t1, d2 } );
        }
    return p;
}

/** @brief The result of one simulated move. */
struct Sim
{
    bool             m_dead = false;
    bool             m_landed = false;
    float            m_x = 0, m_y = 0;
    int              m_teleport = -1;   ///< spawn index of the teleporter's target
    std::vector<int> m_touched;         ///< spawn indices touched on the way
    std::vector<int> m_cells;           ///< cells the box covered
};

struct Search
{
    const Level            &L;
    std::vector<int>        spawnAt;
    std::vector<Stop>       stops;
    CheckWorld              world;
    std::vector<Prim>       prims;

    Search( const Level &level ) : L( level ), world( level, stops )
    {
        spawnAt.assign( (size_t)L.m_w * L.m_h, -1 );
        for ( size_t i = 0; i < L.m_spawns.size(); ++i )
        {
            const Spawn &s = L.m_spawns[i];
            if ( s.m_kind == "mover" )
            {
                float dx = s.m_args.size() > 0 ? (float)atof( s.m_args[0].c_str() ) : 0;
                float dy = s.m_args.size() > 1 ? (float)atof( s.m_args[1].c_str() ) : 0;
                int   n = (int)std::max( std::fabs( dx ), std::fabs( dy ) );
                for ( int k = 0; k <= n; ++k )
                {
                    float f = n ? (float)k / n : 0;
                    float x = ( s.m_x + dx * f ) * T, y = ( s.m_y + dy * f ) * T;
                    stops.push_back( { x, x + s.m_w * T, y } );
                }
                continue;
            }
            spawnAt[(size_t)s.m_y * L.m_w + s.m_x] = (int)i;
        }
        prims = makePrims();
    }

    bool hurt( const HeroBody &b ) const
    {
        bool liquid = false;
        return L.hurts( b.left(), b.top(), b.right(), b.m_y, liquid );
    }

    void touch( const HeroBody &b, Sim &out ) const
    {
        int c0 = (int)std::floor( b.left() / T ), c1 = (int)std::floor( ( b.right() - 0.001f ) / T );
        int r0 = (int)std::floor( b.top() / T ), r1 = (int)std::floor( ( b.m_y - 0.001f ) / T );
        for ( int cy = r0; cy <= r1; ++cy )
            for ( int cx = c0; cx <= c1; ++cx )
            {
                if ( !L.inside( cx, cy ) ) continue;
                int cell = cy * L.m_w + cx;
                if ( out.m_cells.empty() || out.m_cells.back() != cell ) out.m_cells.push_back( cell );
                int s = spawnAt[cell];
                if ( s >= 0 && std::find( out.m_touched.begin(), out.m_touched.end(), s ) == out.m_touched.end() )
                    out.m_touched.push_back( s );
            }
    }

    /** @brief Whether the hero fits at this place and stands on something. */
    bool standable( float x, float y ) const
    {
        world.m_crumbled.clear();
        HeroBody b;
        b.m_x = x, b.m_y = y;
        int c0 = (int)std::floor( b.left() / T ), c1 = (int)std::floor( ( b.right() - 0.001f ) / T );
        int r0 = (int)std::floor( b.top() / T ), r1 = (int)std::floor( ( b.m_y - 0.001f ) / T );
        // A crumbling block where the hero stands has fallen (he came down through it).
        for ( int cy = r0; cy <= r1; ++cy )
            for ( int cx = c0; cx <= c1; ++cx )
                if ( world.solid( cx, cy ) && !( L.inside( cx, cy ) && L.at( cx, cy ).m_kind == CellE::CRUMBLE ) ) return false;
        bool any = false;
        int  row = (int)std::lround( y / T );
        for ( int cx = c0; cx <= c1; ++cx )
            if ( world.solid( cx, row ) || world.oneway( cx, row ) ) any = true;
        float top = 0;
        if ( !any && world.platformTop( b.left(), b.right(), y - 0.5f, y + 0.5f, top ) ) any = true;
        return any && !hurt( b );
    }

    Sim run( float x, float y, const Prim &p, bool settle = false ) const
    {
        Sim      out;
        HeroBody b;
        b.m_x = x, b.m_y = y;
        b.m_ground = !settle;
        b.m_jumpSpeed = phys::Jump;
        b.m_gravity = phys::Gravity * L.num( "gravity", 1.0f );
        int   startCell = (int)std::floor( x / T );
        bool  left = settle, phase2 = false;
        float t = 0;
        // Crumbling blocks under the start have been stood on for a moment already (walking there).
        world.m_crumbled.clear();
        world.m_now = 0;
        if ( !settle )
            for ( int cx = (int)std::floor( ( x - phys::HeroW * 0.5f ) / T ); cx <= (int)std::floor( ( x + phys::HeroW * 0.5f - 0.01f ) / T ); ++cx )
            {
                int row = (int)std::lround( y / T );
                if ( L.inside( cx, row ) && L.at( cx, row ).m_kind == CellE::CRUMBLE ) world.m_crumbled[row * L.m_w + cx] = -0.15f;
                // Crumbling blocks the hero stands in have fallen (he came down through them; the game keeps them
                // away while he is there).
                for ( int cy = (int)std::floor( ( y - phys::HeroH ) / T ); cy <= (int)std::floor( ( y - 0.01f ) / T ); ++cy )
                    if ( L.inside( cx, cy ) && L.at( cx, cy ).m_kind == CellE::CRUMBLE ) world.m_crumbled[cy * L.m_w + cx] = -10.0f;
            }
        std::vector<int> springsUsed, locked;
        {
            Sim under;
            touch( b, under );
            for ( int sp : under.m_touched )
                if ( L.m_spawns[sp].m_kind == "teleport" ) locked.push_back( sp );
        }
        for ( int i = 0; i < (int)( 4.0f / phys::Step ); ++i, t += phys::Step )
        {
            HeroInput in;
            if ( !settle ) in = reachInput( p, i, b.m_x, startCell, phase2 );
            world.m_now = t;
            stepHero( b, in, world, phys::Step );
            if ( b.m_ground )
            {
                int row = (int)std::lround( b.m_y / T );
                for ( int cx = (int)std::floor( b.left() / T ); cx <= (int)std::floor( ( b.right() - 0.01f ) / T ); ++cx )
                    if ( L.inside( cx, row ) && L.at( cx, row ).m_kind == CellE::CRUMBLE && !world.m_crumbled.count( row * L.m_w + cx ) )
                        world.m_crumbled[row * L.m_w + cx] = t;
            }
            if ( !b.m_ground ) left = true;
            touch( b, out );
            // Springs and teleporters act on touch.
            for ( int s : out.m_touched )
            {
                const Spawn &sp = L.m_spawns[s];
                // (The cell must hold the hero now, as in the game: out.m_touched is everything touched so far.)
                bool here = b.right() > sp.m_x * T && b.left() < ( sp.m_x + 1 ) * T && b.m_y > sp.m_y * T &&
                            b.top() < ( sp.m_y + 1 ) * T;
                if ( sp.m_kind == "spring" && here && b.m_vy >= 0 && b.m_y >= sp.m_y * T + 8 &&
                     std::find( springsUsed.begin(), springsUsed.end(), s ) == springsUsed.end() )
                {
                    b.m_vy = -phys::SpringJump;
                    b.m_noCut = true;
                    b.m_ground = false;
                    left = true;
                    springsUsed.push_back( s );
                }
                if ( sp.m_kind == "teleport" && !sp.m_args.empty() && !sp.m_args[0].empty() )
                {
                    // Teleporters fire when entered: a pad under the hero when the move began (he arrived on it)
                    // waits until he has stepped off.
                    bool now = b.right() > sp.m_x * T && b.left() < ( sp.m_x + 1 ) * T && b.m_y > sp.m_y * T && b.top() < ( sp.m_y + 1 ) * T;
                    auto lk = std::find( locked.begin(), locked.end(), s );
                    if ( lk != locked.end() )
                    {
                        if ( !now ) locked.erase( lk );
                        continue;
                    }
                    if ( !now ) continue;
                    char target = sp.m_args[0][0];
                    for ( size_t k = 0; k < L.m_spawns.size(); ++k )
                        if ( L.m_spawns[k].m_ch == target && (int)k != s )
                        {
                            out.m_teleport = (int)k;
                            return out;
                        }
                }
            }
            if ( hurt( b ) || b.top() > L.m_h * T )
            {
                out.m_dead = true;
                return out;
            }
            bool done = b.m_ground && ( left ? true : ( phase2 && std::fabs( b.m_vx ) < 1.0f ) || b.m_hitWall );
            if ( done && t > 0.02f )
            {
                out.m_landed = true;
                out.m_x = b.m_x;
                out.m_y = b.m_y;
                return out;
            }
        }
        return out;
    }
};

uint64_t keyOf( int fx, int fy, int keys, int toggles )
{
    return (uint64_t)fx | (uint64_t)fy << 10 | (uint64_t)keys << 20 | (uint64_t)toggles << 24;
}

struct Node
{
    float            m_x, m_y;   ///< a representative standing place
    int              m_fx, m_fy;
    int              m_keys, m_toggles;
    bool             m_exit = false;   ///< touches the exit from here
    bool             m_dies = false;   ///< some move from here kills (a way out by respawning)
    std::vector<int> m_next;
    std::vector<ReachEdge> m_edges;
};

/** @brief What the search found besides the places. */
struct Found
{
    std::vector<char> m_reached, m_visited, m_stand;
};

/** @brief The search: every standing place reachable from the start and the moves between them. */
bool explore( const Level &level, Search &S, std::vector<Node> &nodes, Found &f, std::string &report )
{
    const Level                      &L = level;
    std::unordered_map<uint64_t, int> index;
    std::deque<int>                   queue;
    f.m_reached.assign( L.m_spawns.size(), 0 );
    f.m_visited.assign( (size_t)L.m_w * L.m_h, 0 );
    f.m_stand.assign( (size_t)L.m_w * L.m_h, 0 );
    std::vector<char> &reached = f.m_reached, &visited = f.m_visited, &stand = f.m_stand;

    auto nodeAt = [&]( float x, float y, int keys, int toggles ) -> int
    {
        int      fx = (int)std::floor( x / T ), fy = (int)std::lround( y / T );
        uint64_t k = keyOf( fx, fy, keys, toggles );
        auto     it = index.find( k );
        if ( it != index.end() ) return it->second;
        Node n;
        n.m_x = x, n.m_y = y, n.m_fx = fx, n.m_fy = fy, n.m_keys = keys, n.m_toggles = toggles;
        nodes.push_back( n );
        index[k] = (int)nodes.size() - 1;
        queue.push_back( (int)nodes.size() - 1 );
        if ( L.inside( fx, fy - 1 ) ) stand[(size_t)( fy - 1 ) * L.m_w + fx] = 1;
        return (int)nodes.size() - 1;
    };
    // What touching things on the way does to the keys and switches.
    auto apply = [&]( const Sim &s, int &keys, int &toggles, bool &exit )
    {
        for ( int i : s.m_touched )
        {
            const Spawn &sp = L.m_spawns[i];
            reached[i] = 1;
            if ( sp.m_kind == "key" ) keys |= !sp.m_args.empty() && sp.m_args[0] == "gold" ? 2 : 1;
            if ( sp.m_kind == "switch" && !sp.m_args.empty() && !sp.m_args[0].empty() )
                toggles ^= 1 << ( ( sp.m_args[0][0] - 'A' ) & 7 );
            if ( sp.m_kind == "exit" ) exit = true;
        }
        for ( int c : s.m_cells ) visited[c] = 1;
    };

    const Spawn *start = L.first( "start" );
    Prim         none = { false, 0, 0, 0, 0 };
    Sim          first = S.run( start->m_x * T + T * 0.5f, ( start->m_y + 1 ) * T - 0.01f, none, true );
    if ( !first.m_landed )
    {
        report = "ERROR the hero does not land at the start (P): no floor below it, or a hazard\n";
        return false;
    }
    {
        int  keys = 0, toggles = 0;
        bool exit = false;
        apply( first, keys, toggles, exit );
        int n = nodeAt( first.m_x, first.m_y, keys, toggles );
        nodes[n].m_exit = exit;
    }

    // The moves from each place are simulated on several cores (each with its own copy of the search's world), a
    // batch of places at a time; the results are merged in order afterwards.
    struct PrimOut
    {
        int   m_code;
        float m_x;
        bool  m_dead = false, m_tele = false, m_landOk = false;
        Sim   m_run, m_land;
    };
    auto simulate = [&]( Search &W, const Node &n, std::vector<PrimOut> &out )
    {
        W.world.m_keys = n.m_keys;
        W.world.m_toggles = n.m_toggles;
        float xs[5] = { n.m_fx * T + T * 0.5f, n.m_fx * T + phys::HeroW * 0.5f + 0.01f, ( n.m_fx + 1 ) * T - phys::HeroW * 0.5f - 0.01f,
                        n.m_fx * T - phys::HeroW * 0.5f + 0.5f, ( n.m_fx + 1 ) * T + phys::HeroW * 0.5f - 0.5f };
        for ( float x : xs )
        {
            if ( !W.standable( x, n.m_y ) ) continue;
            for ( size_t pi = 0; pi < W.prims.size(); ++pi )
            {
                // A move that a mover carried is tried again without the movers: the platform may be elsewhere
                // when the player does it, and what lies below must be reachable (and escapable) too. Such moves
                // are kept with the move's index + 100000.
                W.world.m_usedMover = false;
                W.world.m_noMovers = false;
                Sim  firstRun = W.run( x, n.m_y, W.prims[pi] );
                bool rode = W.world.m_usedMover;
                for ( int pass = 0; pass < ( rode ? 2 : 1 ); ++pass )
                {
                    W.world.m_noMovers = pass == 1;
                    PrimOut o;
                    o.m_code = (int)pi + ( pass == 1 ? 100000 : 0 );
                    o.m_x = x;
                    o.m_run = pass == 0 ? firstRun : W.run( x, n.m_y, W.prims[pi] );
                    o.m_dead = o.m_run.m_dead;
                    if ( !o.m_dead && o.m_run.m_teleport >= 0 )
                    {
                        const Spawn &tg = L.m_spawns[o.m_run.m_teleport];
                        o.m_tele = true;
                        o.m_land = W.run( tg.m_x * T + T * 0.5f, ( tg.m_y + 1 ) * T - 0.01f, none, true );
                        o.m_landOk = o.m_land.m_landed;
                    }
                    out.push_back( std::move( o ) );
                }
                W.world.m_noMovers = false;
            }
        }
    };
    unsigned threads = std::clamp( std::thread::hardware_concurrency() / 2, 1u, 8u );
    std::vector<Search> workers( threads, S );

    const size_t MaxNodes = 150000;
    while ( !queue.empty() && nodes.size() < MaxNodes )
    {
        std::vector<int> batch;
        while ( !queue.empty() && batch.size() < 256 ) batch.push_back( queue.front() ), queue.pop_front();
        std::vector<std::vector<PrimOut>> outs( batch.size() );
        std::atomic<size_t>               nextJob{ 0 };
        auto                              work = [&]( unsigned t )
        {
            for ( size_t j; ( j = nextJob++ ) < batch.size(); ) simulate( workers[t], nodes[batch[j]], outs[j] );
        };
        std::vector<std::thread> pool;
        for ( unsigned t = 1; t < threads; ++t ) pool.emplace_back( work, t );
        work( 0 );
        for ( std::thread &th : pool ) th.join();

        for ( size_t bi = 0; bi < batch.size(); ++bi )
        {
            int  ni = batch[bi];
            Node n = nodes[ni];
            S.world.m_keys = n.m_keys;
            S.world.m_toggles = n.m_toggles;
            std::set<int> next;
            // Standing here touches what the box covers.
            {
                HeroBody b;
                b.m_x = n.m_x, b.m_y = n.m_y;
                Sim here;
                S.touch( b, here );
                int  keys = n.m_keys, toggles = n.m_toggles;
                bool exit = false;
                apply( here, keys, toggles, exit );
                if ( exit ) nodes[ni].m_exit = true;
                if ( keys != n.m_keys || toggles != n.m_toggles )
                {
                    int to = nodeAt( n.m_x, n.m_y, keys, toggles );
                    if ( next.insert( to ).second ) nodes[ni].m_edges.push_back( { to, -1, n.m_x, here.m_touched } );
                }
            }
            // Switches in the line of fire (left, right at the cannon's height, or straight up) can be shot.
            {
                int row = n.m_fy - 1;
                for ( int dir : { -1, 1 } )
                    for ( int k = 1; k <= 16; ++k )
                    {
                        int cx = n.m_fx + dir * k;
                        if ( !L.inside( cx, row ) || S.world.solid( cx, row ) ) break;
                        int sp = S.spawnAt[(size_t)row * L.m_w + cx];
                        if ( sp >= 0 && L.m_spawns[sp].m_kind == "switch" && !L.m_spawns[sp].m_args.empty() )
                        {
                            reached[sp] = 1;
                            int toggles = n.m_toggles ^ ( 1 << ( ( L.m_spawns[sp].m_args[0][0] - 'A' ) & 7 ) );
                            int to = nodeAt( n.m_x, n.m_y, n.m_keys, toggles );
                            if ( next.insert( to ).second ) nodes[ni].m_edges.push_back( { to, dir < 0 ? -2 : -3, n.m_x, {} } );
                        }
                    }
                for ( int k = 2; k <= 10; ++k )
                {
                    int cy = n.m_fy - k;
                    if ( !L.inside( n.m_fx, cy ) || S.world.solid( n.m_fx, cy ) ) break;
                    int sp = S.spawnAt[(size_t)cy * L.m_w + n.m_fx];
                    if ( sp >= 0 && L.m_spawns[sp].m_kind == "switch" && !L.m_spawns[sp].m_args.empty() )
                    {
                        reached[sp] = 1;
                        int toggles = n.m_toggles ^ ( 1 << ( ( L.m_spawns[sp].m_args[0][0] - 'A' ) & 7 ) );
                        int to = nodeAt( n.m_x, n.m_y, n.m_keys, toggles );
                        if ( next.insert( to ).second ) nodes[ni].m_edges.push_back( { to, -4, n.m_x, {} } );
                    }
                }
            }
            // The moves.
            for ( PrimOut &o : outs[bi] )
            {
                if ( o.m_dead )
                {
                    nodes[ni].m_dies = true;
                    continue;
                }
                int              keys = n.m_keys, toggles = n.m_toggles;
                bool             exit = false;
                std::vector<int> touched = o.m_run.m_touched;
                Sim             *end = &o.m_run;
                if ( o.m_tele )
                {
                    apply( o.m_run, keys, toggles, exit );
                    if ( !o.m_landOk ) continue;
                    apply( o.m_land, keys, toggles, exit );
                    touched.insert( touched.end(), o.m_land.m_touched.begin(), o.m_land.m_touched.end() );
                    end = &o.m_land;
                }
                else if ( !o.m_run.m_landed )
                    continue;
                else
                    apply( o.m_run, keys, toggles, exit );
                if ( exit ) nodes[ni].m_exit = true;
                int to = nodeAt( end->m_x, end->m_y, keys, toggles );
                // One move per target (the first found) keeps the graph small; moves that touch something are
                // kept too (the autopilot wants the crystal on the way).
                bool fresh = next.insert( to ).second;
                bool takes = false;
                for ( int t : touched ) takes |= L.m_spawns[t].m_kind != "teleport" && L.m_spawns[t].m_kind != "spring";
                if ( fresh || ( takes && nodes[ni].m_edges.size() < 400 ) ) nodes[ni].m_edges.push_back( { to, o.m_code, o.m_x, touched } );
            }
            nodes[ni].m_next.assign( next.begin(), next.end() );
        }
    }
    if ( nodes.size() >= MaxNodes ) report += "WARN  search stopped at its limit of places\n";
    return true;
}

}   // namespace

bool checkLevel( const Level &level, const std::string &picture, std::string &report )
{
    Search            S( level );
    const Level      &L = level;
    std::vector<Node> nodes;
    Found             f;
    char              line[256];
    report.clear();
    if ( !explore( level, S, nodes, f, report ) ) return false;
    std::vector<char> &reached = f.m_reached, &visited = f.m_visited, &stand = f.m_stand;

    // Who can get to the exit without dying on the way: walk the moves backwards. A place left only by dying is a
    // trap too (the respawn may well be in the same pit).
    std::vector<std::vector<int>> prev( nodes.size() );
    for ( size_t i = 0; i < nodes.size(); ++i )
        for ( int j : nodes[i].m_next ) prev[j].push_back( (int)i );
    std::vector<char> out( nodes.size(), 0 );
    std::deque<int>   back;
    for ( size_t i = 0; i < nodes.size(); ++i )
        if ( nodes[i].m_exit ) out[i] = 1, back.push_back( (int)i );
    while ( !back.empty() )
    {
        int i = back.front();
        back.pop_front();
        for ( int j : prev[i] )
            if ( !out[j] ) out[j] = 1, back.push_back( j );
    }

    // Who can get back to the start (with whatever keys and switches): one-way parts strand a player who goes in
    // before he has everything.
    std::vector<char> home( nodes.size(), 0 );
    for ( size_t i = 0; i < nodes.size(); ++i )
        if ( nodes[i].m_fx == nodes[0].m_fx && nodes[i].m_fy == nodes[0].m_fy ) home[i] = 1, back.push_back( (int)i );
    while ( !back.empty() )
    {
        int i = back.front();
        back.pop_front();
        for ( int j : prev[i] )
            if ( !home[j] ) home[j] = 1, back.push_back( j );
    }

    bool ok = true;
    int  crystals = 0, crystalsReached = 0, treasure = 0, treasureReached = 0;
    for ( size_t i = 0; i < L.m_spawns.size(); ++i )
    {
        const Spawn &s = L.m_spawns[i];
        bool         must = s.m_kind == "crystal" || s.m_kind == "key" || s.m_kind == "exit";
        bool         want = s.m_kind == "treasure" || s.m_kind == "health" || s.m_kind == "weapon" ||
                    s.m_kind == "power" || s.m_kind == "ammo" || s.m_kind == "checkpoint" || s.m_kind == "switch" ||
                    s.m_kind == "lore" || s.m_kind == "warp";
        if ( s.m_kind == "crystal" ) ++crystals, crystalsReached += reached[i];
        if ( s.m_kind == "treasure" ) ++treasure, treasureReached += reached[i];
        if ( ( must || want ) && !reached[i] )
        {
            snprintf( line, sizeof( line ), "%s %s unreachable at column %d, row %d (map line %d)\n",
                      must ? "ERROR" : "WARN ", s.m_kind.c_str(), s.m_x + 1, s.m_y + 1, s.m_y + 1 );
            report += line;
            if ( must ) ok = false;
        }
    }
    // Secrets: groups of '?' cells, each reached when any of its cells was covered.
    int               secrets = 0, secretsReached = 0;
    std::vector<char> seen( (size_t)L.m_w * L.m_h, 0 );
    for ( int y = 0; y < L.m_h; ++y )
        for ( int x = 0; x < L.m_w; ++x )
        {
            if ( !L.at( x, y ).m_secret || seen[(size_t)y * L.m_w + x] ) continue;
            ++secrets;
            bool             got = false;
            std::vector<int> stack = { y * L.m_w + x };
            seen[(size_t)y * L.m_w + x] = 1;
            while ( !stack.empty() )
            {
                int c = stack.back();
                stack.pop_back();
                if ( visited[c] ) got = true;
                int cx = c % L.m_w, cy = c / L.m_w;
                for ( auto [dx, dy] : { std::pair{ 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } } )
                {
                    int nx = cx + dx, ny = cy + dy;
                    if ( L.inside( nx, ny ) && L.at( nx, ny ).m_secret && !seen[(size_t)ny * L.m_w + nx] )
                        seen[(size_t)ny * L.m_w + nx] = 1, stack.push_back( ny * L.m_w + nx );
                }
            }
            secretsReached += got;
            if ( !got )
            {
                snprintf( line, sizeof( line ), "WARN  secret unreachable at column %d, row %d\n", x + 1, y + 1 );
                report += line;
            }
        }
    // Traps: places reached from which neither the exit nor a death can be reached.
    int              traps = 0;
    std::set<int>    trapCells;
    for ( size_t i = 0; i < nodes.size(); ++i )
        if ( !out[i] )
        {
            ++traps;
            trapCells.insert( nodes[i].m_fy * L.m_w + nodes[i].m_fx );
        }
    int listed = 0;
    for ( int c : trapCells )
    {
        if ( listed++ >= 12 ) break;
        snprintf( line, sizeof( line ), "WARN  trap: standing on column %d, row %d the exit cannot be reached without dying\n",
                  c % L.m_w + 1, c / L.m_w );
        report += line;
    }
    // No way back: places (not traps) from which the start cannot be reached again.
    std::set<int> oneWay;
    for ( size_t i = 0; i < nodes.size(); ++i )
        if ( out[i] && !home[i] ) oneWay.insert( nodes[i].m_fy * L.m_w + nodes[i].m_fx );
    listed = 0;
    for ( int c : oneWay )
    {
        if ( listed++ >= 12 ) break;
        snprintf( line, sizeof( line ), "WARN  no way back: standing on column %d, row %d the start cannot be reached again\n",
                  c % L.m_w + 1, c / L.m_w );
        report += line;
    }
    snprintf( line, sizeof( line ),
              "%s %s: %dx%d, crystals %d/%d, treasure %d/%d, secrets %d/%d, places %d, trap places %d, no-way-back places %d\n",
              ok ? "OK   " : "FAIL ", L.m_id.c_str(), L.m_w, L.m_h, crystalsReached, crystals, treasureReached,
              treasure, secretsReached, secrets, (int)nodes.size(), (int)trapCells.size(), (int)oneWay.size() );
    report += line;

    if ( !picture.empty() )
    {
        const int P = 6;
        Image     img = GenImageColor( L.m_w * P, L.m_h * P, Color{ 12, 14, 30, 255 } );
        for ( int y = 0; y < L.m_h; ++y )
            for ( int x = 0; x < L.m_w; ++x )
            {
                const Cell &c = L.at( x, y );
                Color       col = c.m_interior ? Color{ 34, 36, 48, 255 } : Color{ 12, 14, 30, 255 };
                switch ( c.m_kind )
                {
                case CellE::TERRAIN_A: col = { 150, 156, 170, 255 }; break;
                case CellE::TERRAIN_B: col = { 120, 104, 90, 255 }; break;
                case CellE::FAKE: col = { 150, 120, 170, 255 }; break;
                case CellE::BREAKABLE: col = { 170, 130, 90, 255 }; break;
                case CellE::CRUMBLE: col = { 140, 110, 70, 255 }; break;
                case CellE::CONVEYOR: col = { 100, 100, 60, 255 }; break;
                case CellE::SPIKE_UP:
                case CellE::SPIKE_DOWN:
                case CellE::SPIKE_LEFT:
                case CellE::SPIKE_RIGHT: col = { 220, 40, 40, 255 }; break;
                case CellE::LIQUID: col = { 140, 40, 200, 255 }; break;
                case CellE::DOOR_BLUE: col = { 40, 90, 240, 255 }; break;
                case CellE::DOOR_GOLD: col = { 240, 190, 30, 255 }; break;
                case CellE::TOGGLE: col = ( c.m_aux & 8 ) ? Color{ 20, 120, 120, 255 } : Color{ 40, 220, 220, 255 }; break;
                default: break;
                }
                ImageDrawRectangle( &img, x * P, y * P, P, P, col );
                if ( c.m_kind == CellE::PLATFORM ) ImageDrawRectangle( &img, x * P, y * P, P, 2, { 230, 210, 80, 255 } );
                if ( c.m_secret ) ImageDrawRectangleLines( &img, { (float)x * P, (float)y * P, P, P }, 1, { 200, 80, 220, 255 } );
                bool empty = c.m_kind == CellE::SKY || c.m_kind == CellE::INTERIOR;
                if ( empty && visited[(size_t)y * L.m_w + x] )
                    ImageDrawRectangle( &img, x * P + 1, y * P + 1, P - 2, P - 2,
                                        c.m_interior ? Color{ 40, 80, 50, 255 } : Color{ 24, 60, 40, 255 } );
                if ( stand[(size_t)y * L.m_w + x] ) ImageDrawRectangle( &img, x * P + 2, y * P + P - 2, P - 4, 2, { 80, 240, 120, 255 } );
            }
        for ( int c : oneWay )
            ImageDrawRectangle( &img, ( c % L.m_w ) * P, ( c / L.m_w - 1 ) * P, P, P, { 240, 230, 40, 255 } );
        for ( int c : trapCells )
            ImageDrawRectangle( &img, ( c % L.m_w ) * P, ( c / L.m_w - 1 ) * P, P, P, { 255, 140, 0, 255 } );
        for ( const Stop &s : S.stops )
            ImageDrawRectangle( &img, (int)( s.m_x0 / T * P ), (int)( s.m_top / T * P ), (int)( ( s.m_x1 - s.m_x0 ) / T * P ), 1, { 230, 210, 80, 160 } );
        for ( size_t i = 0; i < L.m_spawns.size(); ++i )
        {
            const Spawn &s = L.m_spawns[i];
            Color        col = { 255, 255, 255, 255 };
            if ( s.m_kind == "crystal" ) col = { 60, 230, 255, 255 };
            else if ( s.m_kind == "treasure" ) col = { 255, 220, 60, 255 };
            else if ( s.m_kind == "enemy" || s.m_kind == "boss" ) col = { 255, 120, 40, 255 };
            else if ( s.m_kind == "exit" ) col = { 255, 60, 255, 255 };
            else if ( s.m_kind == "key" ) col = !s.m_args.empty() && s.m_args[0] == "gold" ? Color{ 255, 200, 0, 255 } : Color{ 60, 120, 255, 255 };
            else if ( s.m_kind == "lore" ) col = { 120, 255, 140, 255 };
            else if ( s.m_kind == "warp" ) col = { 200, 120, 255, 255 };
            else if ( s.m_kind == "mover" ) continue;
            int cx = s.m_x * P + P / 2, cy = s.m_y * P + P / 2;
            ImageDrawCircle( &img, cx, cy, P / 2, col );
            bool scored = s.m_kind != "enemy" && s.m_kind != "boss" && s.m_kind != "light" && s.m_kind != "sign";
            if ( scored && !reached[i] )
            {
                ImageDrawLine( &img, cx - P, cy - P, cx + P, cy + P, { 255, 0, 0, 255 } );
                ImageDrawLine( &img, cx - P, cy + P, cx + P, cy - P, { 255, 0, 0, 255 } );
            }
        }
        ExportImage( img, picture.c_str() );
        UnloadImage( img );
    }
    return ok;
}

const std::vector<ReachPrim> &reachPrims()
{
    static const std::vector<ReachPrim> prims = makePrims();
    return prims;
}

HeroInput reachInput( const ReachPrim &p, int i, float x, int startCell, bool &phase2 )
{
    HeroInput in;
    float     t = i * phys::Step;
    if ( p.m_t1 < 0 )
    {
        if ( (int)std::floor( x / T ) != startCell ) phase2 = true;
    }
    else if ( t >= p.m_t1 )
        phase2 = true;
    in.m_dir = phase2 ? p.m_d2 : p.m_d1;
    in.m_jump = p.m_jump && t >= p.m_jumpAt && t < p.m_hold;
    in.m_down = p.m_down && t < 0.1f;
    in.m_jumpPressed = p.m_jump && i == (int)std::lround( p.m_jumpAt / phys::Step );
    return in;
}

int ReachGraph::find( int fx, int fy, int keys, int toggles ) const
{
    auto it = m_index.find( keyOf( fx, fy, keys, toggles ) );
    return it == m_index.end() ? -1 : it->second;
}

bool buildGraph( const Level &level, ReachGraph &graph )
{
    Search            S( level );
    std::vector<Node> nodes;
    Found             f;
    std::string       report;
    if ( !explore( level, S, nodes, f, report ) ) return false;
    graph.m_nodes.clear();
    graph.m_index.clear();
    for ( size_t i = 0; i < nodes.size(); ++i )
    {
        Node     &n = nodes[i];
        ReachNode r;
        r.m_x = n.m_x, r.m_y = n.m_y, r.m_fx = n.m_fx, r.m_fy = n.m_fy, r.m_keys = n.m_keys, r.m_toggles = n.m_toggles;
        r.m_exit = n.m_exit;
        r.m_edges = std::move( n.m_edges );
        graph.m_nodes.push_back( std::move( r ) );
        graph.m_index[keyOf( n.m_fx, n.m_fy, n.m_keys, n.m_toggles )] = (int)i;
    }
    return true;
}

}   // namespace kepler
