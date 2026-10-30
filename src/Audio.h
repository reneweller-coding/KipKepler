/**
 * @file Audio.h
 * @brief Sound effects (assets/sound/<name>.wav, variants <name>_2 ...) and the music (assets/music/<cue>.ogg).
 *        With --mute the device is never opened and everything here does nothing.
 * @author Rene Weller
 */
#pragma once

#include <string>

namespace kepler
{

/** @brief Opens the audio device (not when muted). */
void audioInit( bool mute );
void audioClose();
/** @brief Plays a sound effect. */
void sfx( const std::string &name, float volume = 1, float pitch = 1, float pan = 0.5f );
/** @brief Starts a music cue (looped unless `loop` is false); the same cue keeps playing, "" stops. */
void music( const std::string &cue, bool loop = true );
/** @brief Switches the level's piece to its fight variant (<cue>_fight, when there is one) and back; the calm piece
 *         goes on where it left off. */
void musicFight( bool fight );
/** @brief Plays a theme's ambience bed under the music (assets/ambience/<theme>.ogg, looped, with the effects
 *         volume); the same keeps playing, "" fades it out. */
void ambience( const std::string &theme );
/** @brief Feeds the music stream; call once per frame. */
void audioUpdate( float dt );
/** @brief Volumes 0..1. */
void setVolumes( float master, float music, float effects );
/** @brief Whether sound is on at all. */
bool audioOn();
/** @brief Plays a spoken line (an OGG/WAV file; the one before stops); false if the file is missing. */
bool voice( const std::string &path );
/** @brief Stops the spoken line. */
void stopVoice();
/** @brief Whether a spoken line is playing. */
bool voicePlaying();

}   // namespace kepler
