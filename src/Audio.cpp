/**
 * @file Audio.cpp
 * @brief Sound effects and music on raylib's audio.
 * @author Rene Weller
 */
#include "Audio.h"

#include "Assets.h"

#include <raylib.h>

#include <algorithm>
#include <cctype>
#include <map>
#include <vector>

namespace kepler
{

namespace
{

/** @brief A sound with copies so it can overlap itself, and its variants. */
struct Bank
{
    std::vector<Sound> m_voices;   ///< variant 0 first, then the others
    std::vector<int>   m_variantStart;
    int                m_next = 0;
};

bool                        g_on = false;
std::map<std::string, Bank> g_banks;
std::string                 g_cue;
float                       g_master = 0.8f, g_musicVol = 0.6f, g_effects = 0.8f;

Bank &bank( const std::string &name )
{
    auto it = g_banks.find( name );
    if ( it != g_banks.end() ) return it->second;
    Bank &b = g_banks[name];
    for ( int v = 1; v <= 4; ++v )
    {
        std::string path = assetDir() + "sound/" + name + ( v == 1 ? "" : "_" + std::to_string( v ) ) + ".wav";
        if ( !FileExists( path.c_str() ) ) break;
        Sound s = LoadSound( path.c_str() );
        b.m_variantStart.push_back( (int)b.m_voices.size() );
        b.m_voices.push_back( s );
        for ( int k = 0; k < 3; ++k ) b.m_voices.push_back( LoadSoundAlias( s ) );
    }
    return b;
}

}   // namespace

namespace
{

/** @brief One of two music streams: the one playing and the one fading in or out. */
struct Track
{
    Music m_music = {};
    float m_volume = 0, m_target = 0;
    float m_length = 0;
    bool  m_open = false;
};

Track                    g_tracks[2];
int                      g_current = -1;
std::vector<std::string> g_takes;    ///< the cue's takes (files)
size_t                   g_take = 0;
bool                     g_loop = true;
constexpr float          CrossFade = 1.5f;
// The fight variant of the piece: its takes, and where the calm piece stood when the fight began.
std::vector<std::string> g_calmTakes, g_fightTakes;
size_t                   g_calmTake = 0, g_fightTake = 0;
float                    g_calmAt = 0;
bool                     g_fight = false;

std::vector<std::string> takesOf( const std::string &base )
{
    std::vector<std::string> takes;
    for ( int n = 1; n <= 4; ++n )
    {
        std::string p = assetDir() + "music/" + base + "_t" + std::to_string( n ) + ".ogg";
        if ( FileExists( p.c_str() ) ) takes.push_back( p );
    }
    if ( takes.empty() && FileExists( ( assetDir() + "music/" + base + ".ogg" ).c_str() ) )
        takes.push_back( assetDir() + "music/" + base + ".ogg" );
    return takes;
}

void closeTrack( Track &t )
{
    if ( !t.m_open ) return;
    StopMusicStream( t.m_music );
    UnloadMusicStream( t.m_music );
    t = Track();
}

/** @brief Starts a take in the free slot, fading in over `fade` seconds (0: at once), from `at` seconds on. */
void startTake( const std::string &path, float fade, float at = 0 )
{
    int slot = g_current < 0 ? 0 : 1 - g_current;
    closeTrack( g_tracks[slot] );
    Track &t = g_tracks[slot];
    t.m_music = LoadMusicStream( path.c_str() );
    if ( !t.m_music.stream.buffer ) return;
    t.m_music.looping = false;
    t.m_length = GetMusicTimeLength( t.m_music );
    t.m_open = true;
    t.m_volume = fade > 0 ? 0.0f : 1.0f;
    t.m_target = 1;
    SetMusicVolume( t.m_music, t.m_volume * g_musicVol );
    PlayMusicStream( t.m_music );
    if ( at > 0 && at < t.m_length - 3 ) SeekMusicStream( t.m_music, at );
    if ( g_current >= 0 ) g_tracks[g_current].m_target = 0;
    g_current = slot;
}

}   // namespace

namespace
{
// The ambience bed: one stream, faded in and out.
Music       g_bed = {};
bool        g_bedOpen = false;
std::string g_bedName, g_bedWant;
float       g_bedVol = 0;
constexpr float BedGain = 0.7f;
}   // namespace

void audioInit( bool mute )
{
    if ( mute ) return;
    InitAudioDevice();
    g_on = IsAudioDeviceReady();
    if ( g_on ) SetMasterVolume( g_master );
}

void audioClose()
{
    if ( !g_on ) return;
    for ( Track &t : g_tracks ) closeTrack( t );
    if ( g_bedOpen ) StopMusicStream( g_bed ), UnloadMusicStream( g_bed ), g_bedOpen = false;
    for ( auto &[name, b] : g_banks )
        for ( size_t i = 0; i < b.m_voices.size(); ++i )
        {
            bool root = std::find( b.m_variantStart.begin(), b.m_variantStart.end(), (int)i ) != b.m_variantStart.end();
            if ( root ) UnloadSound( b.m_voices[i] );
            else
                UnloadSoundAlias( b.m_voices[i] );
        }
    g_banks.clear();
    CloseAudioDevice();
    g_on = false;
}

bool audioOn()
{
    return g_on;
}

void sfx( const std::string &name, float volume, float pitch, float pan )
{
    if ( !g_on ) return;
    Bank &b = bank( name );
    if ( b.m_voices.empty() ) return;
    int variants = (int)b.m_variantStart.size();
    int v = variants > 1 ? GetRandomValue( 0, variants - 1 ) : 0;
    int base = b.m_variantStart[v];
    int count = ( v + 1 < variants ? b.m_variantStart[v + 1] : (int)b.m_voices.size() ) - base;
    Sound &s = b.m_voices[base + ( b.m_next++ % count )];
    SetSoundVolume( s, std::clamp( volume * g_effects, 0.0f, 1.0f ) );
    SetSoundPitch( s, pitch );
    SetSoundPan( s, std::clamp( pan, 0.0f, 1.0f ) );
    PlaySound( s );
}

void music( const std::string &cue, bool loop )
{
    if ( !g_on || cue == g_cue ) return;
    g_cue = cue;
    g_loop = loop;
    if ( g_current >= 0 ) g_tracks[g_current].m_target = 0;
    g_takes.clear();
    if ( cue.empty() ) return;
    // "<cue>_t2" starts with the second take; the takes then alternate (crossfaded, so the loops never gap).
    size_t      t = cue.rfind( "_t" );
    bool        numbered = t != std::string::npos && t + 2 < cue.size() && isdigit( (unsigned char)cue[t + 2] );
    std::string base = numbered ? cue.substr( 0, t ) : cue;
    g_takes = takesOf( base );
    // An episode's own piece that is missing falls back to the common one (boss_e2 -> boss).
    if ( g_takes.empty() && base.rfind( '_' ) != std::string::npos ) base = base.substr( 0, base.rfind( '_' ) ), g_takes = takesOf( base );
    g_calmTakes = g_takes;
    g_fightTakes = loop ? takesOf( base + "_fight" ) : std::vector<std::string>();
    g_fight = false;
    if ( g_takes.empty() ) return;
    g_take = numbered ? ( (size_t)atoi( cue.c_str() + t + 2 ) - 1 ) % g_takes.size() : 0;
    g_fightTake = g_take;
    startTake( g_takes[g_take], g_current >= 0 ? 0.6f : 0 );
}

void musicFight( bool fight )
{
    if ( !g_on || fight == g_fight || g_fightTakes.empty() || g_calmTakes.empty() ) return;
    g_fight = fight;
    if ( fight )
    {
        g_calmTake = g_take;
        g_calmAt = g_current >= 0 && g_tracks[g_current].m_open ? GetMusicTimePlayed( g_tracks[g_current].m_music ) : 0;
        g_takes = g_fightTakes;
        g_take = g_fightTake % g_takes.size();
        startTake( g_takes[g_take], 0.8f );
    }
    else
    {
        g_fightTake = ( g_take + 1 ) % g_fightTakes.size();
        g_takes = g_calmTakes;
        g_take = g_calmTake;
        startTake( g_takes[g_take], 2.5f, g_calmAt );
    }
}

void ambience( const std::string &theme )
{
    g_bedWant = theme;
}

void audioUpdate( float dt )
{
    if ( !g_on ) return;
    // The bed fades out before another one starts.
    if ( g_bedOpen && g_bedName != g_bedWant )
    {
        g_bedVol -= dt / 1.0f;
        if ( g_bedVol <= 0 )
        {
            StopMusicStream( g_bed );
            UnloadMusicStream( g_bed );
            g_bedOpen = false, g_bedName.clear(), g_bedVol = 0;
        }
    }
    if ( !g_bedOpen && !g_bedWant.empty() && g_bedName != g_bedWant )
    {
        std::string path = assetDir() + "ambience/" + g_bedWant + ".ogg";
        g_bedName = g_bedWant;
        if ( FileExists( path.c_str() ) )
        {
            g_bed = LoadMusicStream( path.c_str() );
            g_bedOpen = g_bed.stream.buffer != nullptr;
            if ( g_bedOpen ) g_bed.looping = true, g_bedVol = 0, PlayMusicStream( g_bed );
        }
    }
    if ( g_bedOpen )
    {
        if ( g_bedName == g_bedWant ) g_bedVol = std::min( 1.0f, g_bedVol + dt / 2.0f );
        UpdateMusicStream( g_bed );
        SetMusicVolume( g_bed, g_bedVol * g_effects * BedGain );
    }
    for ( int i = 0; i < 2; ++i )
    {
        Track &t = g_tracks[i];
        if ( !t.m_open ) continue;
        UpdateMusicStream( t.m_music );
        float rate = dt / ( t.m_target > t.m_volume && i == g_current ? 0.6f : CrossFade );
        t.m_volume = t.m_volume < t.m_target ? std::min( t.m_target, t.m_volume + rate ) : std::max( t.m_target, t.m_volume - rate );
        SetMusicVolume( t.m_music, t.m_volume * g_musicVol );
        bool ended = !IsMusicStreamPlaying( t.m_music );
        if ( ( t.m_target == 0 && t.m_volume <= 0 ) || ( ended && i != g_current ) ) closeTrack( t );
    }
    // Near the end of the take the next one fades in over it.
    if ( g_current >= 0 && g_tracks[g_current].m_open && g_loop && !g_takes.empty() )
    {
        Track &t = g_tracks[g_current];
        float  left = t.m_length - GetMusicTimePlayed( t.m_music );
        if ( left < CrossFade || !IsMusicStreamPlaying( t.m_music ) )
        {
            g_take = ( g_take + 1 ) % g_takes.size();
            startTake( g_takes[g_take], CrossFade );
        }
    }
}

namespace
{
Sound g_voice = {};
bool  g_voiceOn = false;
}   // namespace

bool voice( const std::string &path )
{
    stopVoice();
    if ( !g_on || !FileExists( path.c_str() ) ) return false;
    g_voice = LoadSound( path.c_str() );
    g_voiceOn = g_voice.frameCount > 0;
    if ( !g_voiceOn ) return false;
    SetSoundVolume( g_voice, std::min( 1.0f, g_effects * 1.1f ) );
    PlaySound( g_voice );
    return true;
}

bool voicePlaying()
{
    return g_voiceOn && IsSoundPlaying( g_voice );
}

void stopVoice()
{
    if ( !g_voiceOn ) return;
    StopSound( g_voice );
    UnloadSound( g_voice );
    g_voiceOn = false;
}

void setVolumes( float master, float musicVolume, float effects )
{
    g_master = master, g_musicVol = musicVolume, g_effects = effects;
    if ( !g_on ) return;
    SetMasterVolume( g_master );

}

}   // namespace kepler
