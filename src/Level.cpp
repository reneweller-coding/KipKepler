/**
 * @file Level.cpp
 * @brief Reading a level file.
 * @author Rene Weller
 */
#include "Level.h"

#include <cmath>
#include <cstdlib>
#include <fstream>
#include <sstream>

namespace kepler
{

std::vector<std::string> words( const std::string &line )
{
    std::vector<std::string> out;
    std::string              w;
    for ( char c : line )
    {
        if ( c == ' ' || c == '\t' || c == '\r' || c == '\n' )
        {
            if ( !w.empty() ) out.push_back( w );
            w.clear();
        }
        else
            w += c;
    }
    if ( !w.empty() ) out.push_back( w );
    return out;
}

const Cell &Level::at( int x, int y ) const
{
    static const Cell wall = { CellE::TERRAIN_A, 0, true, false };
    static const Cell sky = { CellE::SKY, 0, false, false };
    if ( inside( x, y ) ) return m_cells[y * m_w + x];
    return y >= m_h ? sky : wall;
}

const Spawn *Level::first( const std::string &kind ) const
{
    for ( const Spawn &s : m_spawns )
        if ( s.m_kind == kind ) return &s;
    return nullptr;
}

std::string Level::key( const std::string &name, const std::string &fallback ) const
{
    auto it = m_keys.find( name );
    return it == m_keys.end() ? fallback : it->second;
}

float Level::num( const std::string &name, float fallback ) const
{
    auto it = m_keys.find( name );
    return it == m_keys.end() || it->second.empty() ? fallback : (float)atof( it->second.c_str() );
}

bool Level::load( const std::string &path, std::string &error )
{
    error.clear();
    std::ifstream in( path, std::ios::binary );
    if ( !in )
    {
        error = "cannot open " + path;
        return false;
    }
    m_path = path;
    size_t slash = path.find_last_of( "/\\" );
    m_id = path.substr( slash == std::string::npos ? 0 : slash + 1 );
    if ( m_id.size() > 4 && m_id.substr( m_id.size() - 4 ) == ".txt" ) m_id.resize( m_id.size() - 4 );

    std::map<char, std::vector<std::string>> legend;
    std::vector<std::string>                 rows;
    std::string                              line;
    bool                                     inMap = false;
    int                                      lineNo = 0;
    while ( std::getline( in, line ) )
    {
        ++lineNo;
        if ( !line.empty() && line.back() == '\r' ) line.pop_back();
        if ( lineNo == 1 && line.size() >= 3 && (unsigned char)line[0] == 0xEF ) line = line.substr( 3 );
        if ( inMap )
        {
            if ( line == "end" )
            {
                inMap = false;
                continue;
            }
            rows.push_back( line );
            continue;
        }
        if ( line.empty() || line[0] == '#' ) continue;
        if ( line == "map" )
        {
            inMap = true;
            continue;
        }
        std::vector<std::string> w = words( line );
        if ( w.empty() ) continue;
        if ( w[0] == "legend" )
        {
            if ( w.size() < 3 || w[1].size() != 1 )
            {
                error = "line " + std::to_string( lineNo ) + ": legend needs one character and a kind";
                return false;
            }
            legend[w[1][0]] = std::vector<std::string>( w.begin() + 2, w.end() );
            continue;
        }
        // A key: the rest of the line after the first word (names have spaces); a trailing comment is cut.
        size_t      start = line.find_first_not_of( " \t", w[0].size() );
        std::string value = start == std::string::npos ? "" : line.substr( start );
        size_t      hash = value.find( " #" );
        if ( hash != std::string::npos ) value.resize( hash );
        while ( !value.empty() && ( value.back() == ' ' || value.back() == '\t' ) ) value.pop_back();
        m_keys[w[0]] = value;
    }
    if ( rows.empty() )
    {
        error = "no map";
        return false;
    }
    m_h = (int)rows.size();
    m_w = 0;
    for ( const std::string &r : rows ) m_w = std::max( m_w, (int)r.size() );
    if ( m_w > 400 || m_h > 160 )
    {
        error = "map larger than 400 x 160";
        return false;
    }
    for ( std::string &r : rows ) r.resize( m_w, ' ' );
    m_cells.assign( (size_t)m_w * m_h, Cell() );
    m_spawns.clear();
    m_crystals = 0;

    auto raw = [&]( int x, int y ) -> char { return x < 0 || y < 0 || x >= m_w || y >= m_h ? '#' : rows[y][x]; };
    // Whether the back wall shows behind a cell that is not plain '.' or ' ': most of its neighbours decide.
    auto interiorAround = [&]( int x, int y )
    {
        int in = 0, out = 0;
        for ( int dy = -1; dy <= 1; ++dy )
            for ( int dx = -1; dx <= 1; ++dx )
            {
                char c = raw( x + dx, y + dy );
                if ( c == '.' || c == '?' ) ++in;
                if ( c == ' ' ) ++out;
            }
        return in >= out;
    };

    for ( int y = 0; y < m_h; ++y )
        for ( int x = 0; x < m_w; ++x )
        {
            char  c = rows[y][x];
            Cell &cell = m_cells[y * m_w + x];
            auto  spawn = [&]( const std::string &kind, std::vector<std::string> args = {} )
            {
                Spawn s;
                s.m_kind = kind;
                s.m_args = std::move( args );
                s.m_x = x;
                s.m_y = y;
                s.m_ch = c;
                m_spawns.push_back( s );
                cell.m_kind = CellE::SKY;
                cell.m_interior = interiorAround( x, y );
            };
            auto lit = legend.find( c );
            if ( lit != legend.end() && c != ' ' && c != '.' )
            {
                const std::vector<std::string> &w = lit->second;
                const std::string              &kind = w[0];
                if ( kind == "toggle" )
                {
                    int group = w.size() > 1 && !w[1].empty() ? ( w[1][0] - 'A' ) & 7 : 0;
                    cell.m_kind = CellE::TOGGLE;
                    cell.m_aux = (uint8_t)( group | ( w.size() > 2 && w[2] == "empty" ? 8 : 0 ) );
                    cell.m_interior = interiorAround( x, y );
                }
                else if ( kind == "conveyor" )
                {
                    cell.m_kind = CellE::CONVEYOR;
                    cell.m_aux = w.size() > 1 && atoi( w[1].c_str() ) > 0 ? 1 : 0;
                    cell.m_interior = true;
                }
                else if ( kind == "mover" )
                {
                    // A horizontal run of the same character is one platform: only its first cell spawns.
                    if ( x > 0 && rows[y][x - 1] == c )
                    {
                        cell.m_kind = CellE::SKY;
                        cell.m_interior = interiorAround( x, y );
                        continue;
                    }
                    int width = 1;
                    while ( x + width < m_w && rows[y][x + width] == c ) ++width;
                    spawn( kind, std::vector<std::string>( w.begin() + 1, w.end() ) );
                    m_spawns.back().m_w = width;
                }
                else
                {
                    spawn( kind, std::vector<std::string>( w.begin() + 1, w.end() ) );
                    if ( kind == "crystal" ) ++m_crystals;
                }
                continue;
            }
            switch ( c )
            {
            case ' ': cell.m_kind = CellE::SKY; break;
            case '.': cell.m_kind = CellE::INTERIOR, cell.m_interior = true; break;
            case '?':
                cell.m_kind = CellE::INTERIOR, cell.m_interior = true;
                cell.m_secret = true;
                break;
            // Terrain is not fully opaque (rounded corners, hanging roots): the back wall or the sky shows behind,
            // whichever its neighbours are.
            case '#': cell.m_kind = CellE::TERRAIN_A, cell.m_interior = interiorAround( x, y ); break;
            case '%': cell.m_kind = CellE::TERRAIN_B, cell.m_interior = interiorAround( x, y ); break;
            case 'X': cell.m_kind = CellE::FAKE, cell.m_interior = interiorAround( x, y ); break;
            case 'B': cell.m_kind = CellE::BREAKABLE, cell.m_interior = interiorAround( x, y ); break;
            case '-': cell.m_kind = CellE::PLATFORM, cell.m_interior = interiorAround( x, y ); break;
            case '_': cell.m_kind = CellE::CRUMBLE, cell.m_interior = interiorAround( x, y ); break;
            case '^': cell.m_kind = CellE::SPIKE_UP, cell.m_interior = interiorAround( x, y ); break;
            case 'v': cell.m_kind = CellE::SPIKE_DOWN, cell.m_interior = interiorAround( x, y ); break;
            case '<': cell.m_kind = CellE::SPIKE_LEFT, cell.m_interior = interiorAround( x, y ); break;
            case '>': cell.m_kind = CellE::SPIKE_RIGHT, cell.m_interior = interiorAround( x, y ); break;
            case '~': cell.m_kind = CellE::LIQUID, cell.m_interior = interiorAround( x, y ); break;
            case 'd': cell.m_kind = CellE::DOOR_BLUE, cell.m_interior = true; break;
            case 'D': cell.m_kind = CellE::DOOR_GOLD, cell.m_interior = true; break;
            case '*':
                spawn( "crystal" );
                ++m_crystals;
                break;
            case '$': spawn( "treasure" ); break;
            case '+': spawn( "health", { "small" } ); break;
            case 'H': spawn( "health", { "big" } ); break;
            case '&': spawn( "ammo" ); break;
            case 'k': spawn( "key", { "blue" } ); break;
            case 'K': spawn( "key", { "gold" } ); break;
            case 'P': spawn( "start" ); break;
            case 'E': spawn( "exit" ); break;
            case 'C': spawn( "checkpoint" ); break;
            default:
                error = "line " + std::to_string( y + 1 ) + " of the map: unknown character '" + std::string( 1, c ) +
                        "' at column " + std::to_string( x + 1 );
                return false;
            }
        }
    if ( !first( "start" ) )
    {
        error = "no start (P)";
        return false;
    }
    if ( !first( "exit" ) )
    {
        error = "no exit (E)";
        return false;
    }
    return true;
}

namespace
{
const int Around[8][2] = { { 0, -1 }, { 1, -1 }, { 1, 0 }, { 1, 1 }, { 0, 1 }, { -1, 1 }, { -1, 0 }, { -1, -1 } };
}

uint8_t Level::terrainMask( int x, int y ) const
{
    auto like = [&]( int cx, int cy )
    {
        if ( !inside( cx, cy ) ) return cy < m_h;
        switch ( at( cx, cy ).m_kind )
        {
        case CellE::TERRAIN_A:
        case CellE::TERRAIN_B:
        case CellE::FAKE:
        case CellE::BREAKABLE:
        case CellE::DOOR_BLUE:
        case CellE::DOOR_GOLD:
        case CellE::CONVEYOR: return true;
        default: return false;
        }
    };
    uint8_t m = 0;
    for ( int b = 0; b < 8; ++b )
        if ( like( x + Around[b][0], y + Around[b][1] ) ) m |= 1 << b;
    return m;
}

uint8_t Level::backMask( int x, int y ) const
{
    auto like = [&]( int cx, int cy )
    {
        if ( !inside( cx, cy ) ) return cy < m_h;
        const Cell &c = at( cx, cy );
        switch ( c.m_kind )
        {
        case CellE::SKY:
        case CellE::PLATFORM:
        case CellE::LIQUID:
        case CellE::CRUMBLE:
        case CellE::TOGGLE:
        case CellE::SPIKE_UP:
        case CellE::SPIKE_DOWN:
        case CellE::SPIKE_LEFT:
        case CellE::SPIKE_RIGHT: return c.m_interior;
        default: return true;
        }
    };
    uint8_t m = 0;
    for ( int b = 0; b < 8; ++b )
        if ( like( x + Around[b][0], y + Around[b][1] ) ) m |= 1 << b;
    return m;
}

bool Level::hurts( float l, float t, float r, float b, bool &liquid ) const
{
    liquid = false;
    const float T = (float)Tile;
    int         c0 = (int)std::floor( l / T ), c1 = (int)std::floor( ( r - 0.001f ) / T );
    int         r0 = (int)std::floor( t / T ), r1 = (int)std::floor( ( b - 0.001f ) / T );
    bool        hit = false;
    for ( int cy = r0; cy <= r1; ++cy )
        for ( int cx = c0; cx <= c1; ++cx )
        {
            if ( !inside( cx, cy ) ) continue;
            float x0 = cx * T, y0 = cy * T, x1 = x0, y1 = y0;
            switch ( at( cx, cy ).m_kind )
            {
            case CellE::SPIKE_UP: x0 += 4, x1 += T - 4, y0 += 18, y1 += T; break;
            case CellE::SPIKE_DOWN: x0 += 4, x1 += T - 4, y1 += 14; break;
            case CellE::SPIKE_LEFT: x0 += 0, x1 += 14, y0 += 4, y1 += T - 4; break;
            case CellE::SPIKE_RIGHT: x0 += 18, x1 += T, y0 += 4, y1 += T - 4; break;
            case CellE::LIQUID: x1 += T, y0 += 8, y1 += T; break;
            default: continue;
            }
            if ( l < x1 && r > x0 && t < y1 && b > y0 )
            {
                hit = true;
                if ( at( cx, cy ).m_kind == CellE::LIQUID ) liquid = true;
            }
        }
    return hit;
}

}   // namespace kepler
