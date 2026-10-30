/**
 * @file Text.h
 * @brief Texts by key from assets/text/<lang>.txt (`key = text`); German fills what English lacks, the key itself
 *        what both lack.
 * @author Rene Weller
 */
#pragma once

#include <string>
#include <vector>

namespace kepler
{

/** @brief Chooses the language ("de" or "en") and reads its texts. */
void setLanguage( const std::string &lang );
/** @brief The language in use. */
const std::string &language();
/** @brief The text of a key. */
const std::string &tr( const std::string &key );
/** @brief Whether a key has a text. */
bool hasText( const std::string &key );
/** @brief Every key that starts with `prefix` and ends with `suffix`, sorted. */
std::vector<std::string> textKeys( const std::string &prefix, const std::string &suffix = "" );
/** @brief Replaces {jump} {fire} {alt} {weapon} {pause} {up} {down} by the pad's button glyphs or the keys' names. */
std::string glyphs( const std::string &text, bool pad );

/** @brief The system's language if it is one of ours, else English. */
std::string systemLanguage();

}   // namespace kepler
