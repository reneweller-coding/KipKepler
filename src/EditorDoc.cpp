/**
 * @file EditorDoc.cpp
 * @brief The level editor's document: reading, writing and changing a level file, and the view of its cells.
 * @author Rene Weller
 */
#include "EditorDoc.h"

#include <algorithm>
#include <cstdlib>

namespace kepler::edit
{

namespace
{

const char *FixedChars = " .#%-_BX^v<>~*$+H&kKdD?PEC";
/** @brief The characters handed out for new legend lines, in this order. */
const char *FreeOrder = "abcefghijlmnopqrstuwxyz0123456789AFGIJLMNOQRSTUVWYZ!()[]{};:=@,/|'\"`\\";

}   // namespace

uint32_t hashCell( int x, int y, uint32_t salt )
{
    uint32_t h = (uint32_t)x * 73856093u ^ (uint32_t)y * 19349663u ^ salt * 83492791u;
    h ^= h >> 13;
    h *= 0x5bd1e995u;
    h ^= h >> 15;
    return h;
}

int episodeOf( const std::string &theme )
{
    if ( theme == "jungle" || theme == "hive" ) return 2;
    if ( theme == "ice" || theme == "crystal" ) return 3;
    if ( theme == "foundry" || theme == "citadel" ) return 4;
    return 1;
}

bool fixedChar( char c )
{
    for ( const char *p = FixedChars; *p; ++p )
        if ( *p == c ) return true;
    return false;
}

std::string joinWords( const std::vector<std::string> &w, size_t from )
{
    std::string out;
    for ( size_t i = from; i < w.size(); ++i )
    {
        if ( !out.empty() ) out += ' ';
        out += w[i];
    }
    return out;
}

// ------------------------------------------------------------------------------------------------ new, read, write

void Doc::makeNew( int w, int h )
{
    m_comments = { "# made with the KIP KEPLER level editor" };
    m_keys = { { "name", "Custom Level" }, { "name.de", "Eigenes Level" }, { "theme", "station" }, { "tint", "0" },
               { "bg", "station_a" },      { "music", "e1_station" },      { "dark", "0.1" },        { "par", "300" },
               { "gravity", "1.0" } };
    m_legend.clear();
    m_w = w, m_h = h;
    m_rows.assign( h, std::string( w, '.' ) );
    for ( int y = 0; y < h; ++y )
        for ( int x = 0; x < w; ++x )
            if ( x < 2 || x >= w - 2 || y < 2 || y >= h - 3 ) m_rows[y][x] = '#';
    m_rows[h - 4][5] = 'P';
    m_rows[h - 4][w - 7] = 'E';
    rebuild();
}

bool Doc::parse( const std::string &text, std::string &error )
{
    error.clear();
    DocData d;
    bool    inMap = false;
    int     lineNo = 0;
    size_t  pos = 0;
    while ( pos <= text.size() )
    {
        size_t      nl = text.find( '\n', pos );
        std::string line = text.substr( pos, nl == std::string::npos ? std::string::npos : nl - pos );
        if ( nl == std::string::npos && line.empty() ) break;
        pos = nl == std::string::npos ? text.size() + 1 : nl + 1;
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
            d.m_rows.push_back( line );
            continue;
        }
        if ( line.empty() ) continue;
        if ( line[0] == '#' )
        {
            d.m_comments.push_back( line );
            continue;
        }
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
            LegendLine l;
            l.m_ch = w[1][0];
            l.m_text = joinWords( w, 2 );
            l.m_fromFile = true;
            auto old = std::find_if( d.m_legend.begin(), d.m_legend.end(), [&]( const LegendLine &o ) { return o.m_ch == l.m_ch; } );
            if ( old != d.m_legend.end() ) *old = l;
            else
                d.m_legend.push_back( l );
            continue;
        }
        size_t      start = line.find_first_not_of( " \t", w[0].size() );
        std::string value = start == std::string::npos ? "" : line.substr( start );
        size_t      hash = value.find( " #" );
        if ( hash != std::string::npos ) value.resize( hash );
        while ( !value.empty() && ( value.back() == ' ' || value.back() == '\t' ) ) value.pop_back();
        auto old = std::find_if( d.m_keys.begin(), d.m_keys.end(), [&]( const auto &k ) { return k.first == w[0]; } );
        if ( old != d.m_keys.end() ) old->second = value;
        else
            d.m_keys.push_back( { w[0], value } );
    }
    if ( d.m_rows.empty() )
    {
        error = "no map";
        return false;
    }
    d.m_h = (int)d.m_rows.size();
    d.m_w = 0;
    for ( const std::string &r : d.m_rows ) d.m_w = std::max( d.m_w, (int)r.size() );
    if ( d.m_w > 400 || d.m_h > 160 )
    {
        error = "map larger than 400 x 160";
        return false;
    }
    if ( d.m_w < 1 )
    {
        error = "empty map";
        return false;
    }
    for ( std::string &r : d.m_rows ) r.resize( d.m_w, ' ' );
    static_cast<DocData &>( *this ) = std::move( d );
    rebuild();
    return true;
}

std::string Doc::write() const
{
    std::string out;
    for ( const std::string &c : m_comments ) out += c + "\n";
    for ( const auto &[name, value] : m_keys )
    {
        std::string line = name;
        line.resize( std::max<size_t>( name.size() + 1, 10 ), ' ' );
        out += line + value + "\n";
    }
    for ( const LegendLine &l : m_legend )
    {
        if ( !l.m_fromFile && !used( l.m_ch ) ) continue;
        out += std::string( "legend " ) + l.m_ch + "  " + l.m_text + "\n";
    }
    out += "map\n";
    for ( const std::string &r : m_rows ) out += r + "\n";
    out += "end\n";
    return out;
}

// ------------------------------------------------------------------------------------------------------- access

char Doc::at( int x, int y ) const
{
    if ( x < 0 || y < 0 || x >= m_w || y >= m_h ) return '#';
    return m_rows[y][x];
}

bool Doc::set( int x, int y, char c )
{
    if ( x < 0 || y < 0 || x >= m_w || y >= m_h || m_rows[y][x] == c ) return false;
    m_rows[y][x] = c;
    return true;
}

std::string Doc::key( const std::string &name, const std::string &fallback ) const
{
    for ( const auto &[k, v] : m_keys )
        if ( k == name ) return v.empty() ? fallback : v;
    return fallback;
}

void Doc::setKey( const std::string &name, const std::string &value )
{
    auto it = std::find_if( m_keys.begin(), m_keys.end(), [&]( const auto &k ) { return k.first == name; } );
    if ( value.empty() )
    {
        if ( it != m_keys.end() ) m_keys.erase( it );
        return;
    }
    if ( it != m_keys.end() ) it->second = value;
    else
        m_keys.push_back( { name, value } );
}

const LegendLine *Doc::legend( char c ) const
{
    for ( const LegendLine &l : m_legend )
        if ( l.m_ch == c ) return &l;
    return nullptr;
}

std::string Doc::kindOf( char c ) const
{
    if ( c != ' ' && c != '.' )
        if ( const LegendLine *l = legend( c ) )
        {
            std::vector<std::string> w = words( l->m_text );
            return w.empty() ? "?" : w[0];
        }
    switch ( c )
    {
    case '*': return "crystal";
    case '$': return "treasure";
    case '+':
    case 'H': return "health";
    case '&': return "ammo";
    case 'k':
    case 'K': return "key";
    case 'P': return "start";
    case 'E': return "exit";
    case 'C': return "checkpoint";
    default: return fixedChar( c ) ? "" : "?";
    }
}

std::vector<std::string> Doc::argsOf( char c ) const
{
    if ( c != ' ' && c != '.' )
        if ( const LegendLine *l = legend( c ) )
        {
            std::vector<std::string> w = words( l->m_text );
            if ( !w.empty() ) w.erase( w.begin() );
            return w;
        }
    switch ( c )
    {
    case '+': return { "small" };
    case 'H': return { "big" };
    case 'k': return { "blue" };
    case 'K': return { "gold" };
    default: return {};
    }
}

bool Doc::used( char c ) const
{
    for ( const std::string &r : m_rows )
        if ( r.find( c ) != std::string::npos ) return true;
    return false;
}

char Doc::freeChar()
{
    for ( const char *p = FreeOrder; *p; ++p )
        if ( !legend( *p ) ) return *p;
    // None left: take over a line no cell uses (and no used teleport points to).
    for ( const char *p = FreeOrder; *p; ++p )
    {
        if ( used( *p ) ) continue;
        bool target = false;
        for ( const LegendLine &l : m_legend )
        {
            std::vector<std::string> w = words( l.m_text );
            if ( w.size() > 1 && w[0] == "teleport" && w[1].size() == 1 && w[1][0] == *p && used( l.m_ch ) ) target = true;
        }
        if ( target ) continue;
        m_legend.erase( std::remove_if( m_legend.begin(), m_legend.end(), [&]( const LegendLine &l ) { return l.m_ch == *p; } ),
                        m_legend.end() );
        return *p;
    }
    return 0;
}

char Doc::charFor( const std::string &text, bool fresh )
{
    if ( !fresh )
        for ( const LegendLine &l : m_legend )
            if ( l.m_text == text ) return l.m_ch;
    char c = freeChar();
    if ( !c ) return 0;
    LegendLine l;
    l.m_ch = c;
    l.m_text = text;
    m_legend.push_back( l );
    return c;
}

// --------------------------------------------------------------------------------------------------------- view

void Doc::rebuild()
{
    rebuild( 0, 0, m_w - 1, m_h - 1 );
}

void Doc::rebuild( int x0, int y0, int x1, int y1 )
{
    size_t n = (size_t)m_w * m_h;
    if ( m_view.m_w != m_w || m_view.m_h != m_h || m_view.m_cells.size() != n )
    {
        m_view.m_w = m_w, m_view.m_h = m_h;
        m_view.m_cells.assign( n, Cell() );
        m_maskT.assign( n, 0 ), m_maskB.assign( n, 0 ), m_variant.assign( n, 0 );
        for ( int y = 0; y < m_h; ++y )
            for ( int x = 0; x < m_w; ++x ) m_variant[(size_t)y * m_w + x] = (uint8_t)( hashCell( x, y ) >> 7 );
        x0 = 0, y0 = 0, x1 = m_w - 1, y1 = m_h - 1;
    }
    m_view.m_id = m_id;
    const LegendLine *table[256] = {};
    for ( const LegendLine &l : m_legend ) table[(unsigned char)l.m_ch] = &l;

    auto raw = [&]( int x, int y ) -> char { return x < 0 || y < 0 || x >= m_w || y >= m_h ? '#' : m_rows[y][x]; };
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

    int cx0 = std::max( 0, x0 - 1 ), cy0 = std::max( 0, y0 - 1 ), cx1 = std::min( m_w - 1, x1 + 1 ), cy1 = std::min( m_h - 1, y1 + 1 );
    for ( int y = cy0; y <= cy1; ++y )
        for ( int x = cx0; x <= cx1; ++x )
        {
            char  c = m_rows[y][x];
            Cell &cell = m_view.m_cells[(size_t)y * m_w + x];
            cell = Cell();
            const LegendLine *l = c != ' ' && c != '.' ? table[(unsigned char)c] : nullptr;
            if ( l )
            {
                std::vector<std::string> w = words( l->m_text );
                std::string              kind = w.empty() ? "" : w[0];
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
                else
                    cell.m_interior = interiorAround( x, y );
                continue;
            }
            switch ( c )
            {
            case ' ': break;
            case '.': cell.m_kind = CellE::INTERIOR, cell.m_interior = true; break;
            case '?':
                cell.m_kind = CellE::INTERIOR, cell.m_interior = true;
                cell.m_secret = true;
                break;
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
            default: cell.m_interior = interiorAround( x, y ); break;   // pickups, P E C, unknown characters
            }
        }
    int mx0 = std::max( 0, cx0 - 1 ), my0 = std::max( 0, cy0 - 1 ), mx1 = std::min( m_w - 1, cx1 + 1 ), my1 = std::min( m_h - 1, cy1 + 1 );
    for ( int y = my0; y <= my1; ++y )
        for ( int x = mx0; x <= mx1; ++x )
        {
            m_maskT[(size_t)y * m_w + x] = m_view.terrainMask( x, y );
            m_maskB[(size_t)y * m_w + x] = m_view.backMask( x, y );
        }
}

bool Doc::solidAt( int x, int y ) const
{
    if ( y >= m_h ) return false;
    if ( x < 0 || x >= m_w || y < 0 ) return true;
    const Cell &c = m_view.m_cells[(size_t)y * m_w + x];
    switch ( c.m_kind )
    {
    case CellE::TERRAIN_A:
    case CellE::TERRAIN_B:
    case CellE::CONVEYOR:
    case CellE::BREAKABLE:
    case CellE::CRUMBLE:
    case CellE::DOOR_BLUE:
    case CellE::DOOR_GOLD: return true;
    case CellE::TOGGLE: return ( c.m_aux & 8 ) == 0;
    default: return false;
    }
}

bool Doc::onewayAt( int x, int y ) const
{
    return x >= 0 && y >= 0 && x < m_w && y < m_h && m_view.m_cells[(size_t)y * m_w + x].m_kind == CellE::PLATFORM;
}

// ------------------------------------------------------------------------------------------------------- resize

namespace
{

bool wallChar( char c )
{
    return c == '#' || c == '%';
}

/** @brief What new cells next to an edge cell become: walls, floors, interior and sky go on; anything else is
 *         interior. */
char extend( char c )
{
    return c == '#' || c == '%' || c == '.' || c == ' ' || c == '~' ? c : '.';
}

}   // namespace

void Doc::resize( int left, int right, int top, int bottom )
{
    // Growing puts new columns (rows) in just inside the wall along that edge (as thick as its thinnest place), so
    // the rooms grow and the wall stays at the edge. Shrinking takes such a plain column (only walls, interior, sky,
    // liquid) from inside the wall when there is one, else crops the outer edge: what was placed is never lost
    // before the edge's wall is.
    auto plain = []( char c ) { return c == '#' || c == '%' || c == '.' || c == ' ' || c == '~'; };
    auto columns = [&]( bool atRight, int n )
    {
        for ( int step = 0; step < std::abs( n ) && ( n > 0 || m_w > 1 ); ++step )
        {
            int b = 4;
            for ( const std::string &r : m_rows )
            {
                int k = 0;
                while ( k < b && k < m_w && wallChar( atRight ? r[m_w - 1 - k] : r[k] ) ) ++k;
                b = std::min( b, k );
            }
            int inner = atRight ? m_w - b - 1 : b;   // the column just inside the wall
            if ( n > 0 )
            {
                for ( std::string &r : m_rows )
                    r.insert( (size_t)( atRight ? m_w - b : b ), 1, extend( inner >= 0 && inner < m_w ? r[inner] : '.' ) );
                ++m_w;
                continue;
            }
            bool clear = inner >= 0 && inner < m_w && b < m_w - 1;
            for ( const std::string &r : m_rows )
                if ( clear && !plain( r[inner] ) ) clear = false;
            int gone = clear ? inner : atRight ? m_w - 1 : 0;
            for ( std::string &r : m_rows ) r.erase( (size_t)gone, 1 );
            --m_w;
        }
    };
    auto rows = [&]( bool atBottom, int n )
    {
        for ( int step = 0; step < std::abs( n ) && ( n > 0 || m_h > 1 ); ++step )
        {
            int b = 4;
            for ( int x = 0; x < m_w; ++x )
            {
                int k = 0;
                while ( k < b && k < m_h && wallChar( m_rows[atBottom ? m_h - 1 - k : k][x] ) ) ++k;
                b = std::min( b, k );
            }
            int inner = atBottom ? m_h - b - 1 : b;   // the row just inside the wall
            if ( n > 0 )
            {
                std::string fill = inner >= 0 && inner < m_h ? m_rows[inner] : std::string( m_w, '.' );
                for ( char &c : fill ) c = extend( c );
                m_rows.insert( m_rows.begin() + ( atBottom ? m_h - b : b ), fill );
                ++m_h;
                continue;
            }
            bool clear = inner >= 0 && inner < m_h && b < m_h - 1;
            if ( clear )
                for ( char c : m_rows[inner] )
                    if ( !plain( c ) ) clear = false;
            m_rows.erase( m_rows.begin() + ( clear ? inner : atBottom ? m_h - 1 : 0 ) );
            --m_h;
        }
    };
    columns( true, right );
    columns( false, left );
    rows( true, bottom );
    rows( false, top );
    rebuild();
}

}   // namespace kepler::edit
