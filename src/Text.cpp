/**
 * @file Text.cpp
 * @brief Texts by key.
 * @author Rene Weller
 */
#include "Text.h"

#include "Assets.h"

#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <map>
#include <vector>

#ifdef _WIN32
extern "C" __declspec( dllimport ) unsigned short __stdcall GetUserDefaultUILanguage( void );
#endif

namespace kepler
{

namespace
{

std::string                        g_lang = "de";
std::map<std::string, std::string> g_texts, g_german;

void readFile( const std::string &path, std::map<std::string, std::string> &into )
{
    std::ifstream in( path, std::ios::binary );
    std::string   line;
    bool          first = true;
    while ( std::getline( in, line ) )
    {
        if ( first && line.size() >= 3 && (unsigned char)line[0] == 0xEF ) line = line.substr( 3 );
        first = false;
        if ( !line.empty() && line.back() == '\r' ) line.pop_back();
        if ( line.empty() || line[0] == '#' ) continue;
        size_t eq = line.find( '=' );
        if ( eq == std::string::npos ) continue;
        std::string k = line.substr( 0, eq ), v = line.substr( eq + 1 );
        while ( !k.empty() && k.back() == ' ' ) k.pop_back();
        while ( !v.empty() && v[0] == ' ' ) v.erase( 0, 1 );
        // "|" breaks a line.
        for ( size_t p = v.find( '|' ); p != std::string::npos; p = v.find( '|', p ) ) v[p] = '\n';
        into[k] = v;
    }
}

/** @brief assets/text/<lang>.txt and every file in assets/text/<lang>/ (the episodes' level names and signs). */
void read( const std::string &lang, std::map<std::string, std::string> &into )
{
    into.clear();
    readFile( assetDir() + "text/" + lang + ".txt", into );
    std::error_code e;
    std::vector<std::string> files;
    for ( const auto &f : std::filesystem::directory_iterator( assetDir() + "text/" + lang, e ) )
        if ( f.path().extension() == ".txt" ) files.push_back( f.path().string() );
    std::sort( files.begin(), files.end() );
    for ( const std::string &f : files ) readFile( f, into );
}

}   // namespace

void setLanguage( const std::string &lang )
{
    g_lang = lang == "en" ? "en" : "de";
    read( "de", g_german );
    if ( g_lang == "de" ) g_texts = g_german;
    else
        read( g_lang, g_texts );
}

const std::string &language()
{
    return g_lang;
}

const std::string &tr( const std::string &key )
{
    auto it = g_texts.find( key );
    if ( it != g_texts.end() ) return it->second;
    it = g_german.find( key );
    if ( it != g_german.end() ) return it->second;
    static std::map<std::string, std::string> missing;
    return missing.emplace( key, key ).first->second;
}

bool hasText( const std::string &key )
{
    return g_texts.count( key ) || g_german.count( key );
}

std::vector<std::string> textKeys( const std::string &prefix, const std::string &suffix )
{
    std::vector<std::string> out;
    for ( const auto &[k, v] : g_german )
        if ( k.rfind( prefix, 0 ) == 0 && k.size() >= prefix.size() + suffix.size() &&
             k.compare( k.size() - suffix.size(), suffix.size(), suffix ) == 0 )
            out.push_back( k );
    return out;
}

std::string glyphs( const std::string &text, bool pad )
{
    // The fonts carry the pad's buttons in the private use area: E000 A, E001 B, E002 X, E003 Y, E004 LB, E005 RB,
    // E006 d-pad, E007 stick, E008 start.
    static const char *names[][3] = { { "{jump}", "\xEE\x80\x80", "Space" }, { "{fire}", "\xEE\x80\x82", "Ctrl" },
                                      { "{alt}", "\xEE\x80\x83", "L" }, { "{weapon}", "\xEE\x80\x84\xEE\x80\x85", "Q/E" },
                                      { "{pause}", "\xEE\x80\x88", "Esc" }, { "{up}", "\xEE\x80\x87", "W" },
                                      { "{down}", "\xEE\x80\x87", "S" } };
    bool        de = language() == "de";
    std::string out = text;
    for ( auto &n : names )
        for ( size_t p = out.find( n[0] ); p != std::string::npos; p = out.find( n[0], p ) )
        {
            const char *with = pad ? n[1] : !de ? n[2] : &n == &names[0] ? "Leertaste" : &n == &names[1] ? "Strg" : n[2];
            out.replace( p, strlen( n[0] ), with );
            p += strlen( with );
        }
    return out;
}

std::string systemLanguage()
{
#ifdef _WIN32
    return ( GetUserDefaultUILanguage() & 0x3FF ) == 0x07 ? "de" : "en";
#else
    const char *l = getenv( "LANG" );
    return l && l[0] == 'd' && l[1] == 'e' ? "de" : "en";
#endif
}

}   // namespace kepler
