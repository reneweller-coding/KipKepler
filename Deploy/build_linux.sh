#!/usr/bin/env bash
# Builds KIP KEPLER for Linux (Release, GCC 12) and packs dist/KipKepler-<version>-linux-x86_64.tar.gz: the program,
# its assets, the player's readme and the licence. Built on Ubuntu 22.04 it runs on glibc 2.35 and newer, SteamOS (the
# Steam Deck) included.
#
#   bash Deploy/build_linux.sh [BUILD_DIR]      (default ~/build/kipkepler-release; nice -n 15, four jobs)
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
build="${1:-$HOME/build/kipkepler-release}"
version="$(sed -n 's/^project( KipKepler VERSION \([0-9.]*\).*/\1/p' "$root/CMakeLists.txt")"

extra=()
command -v ninja > /dev/null && extra+=(-G Ninja)
CC="${CC:-gcc-12}" CXX="${CXX:-g++-12}" cmake -S "$root" -B "$build" -DCMAKE_BUILD_TYPE=Release "${extra[@]}"
nice -n 15 cmake --build "$build" --parallel 4

name="KipKepler-$version-linux-x86_64"
stage="$build/release/$name"
rm -rf "$build/release"
mkdir -p "$stage/assets"
cp "$build/KipKepler" "$stage/KipKepler"
(cd "$root/assets" && tar -cf - .) | (cd "$stage/assets" && tar -xf -)
[ -f "$root/docs/README-player.txt" ] && cp "$root/docs/README-player.txt" "$stage/README.txt"
[ -f "$root/LICENSE" ] && cp "$root/LICENSE" "$stage/"
mkdir -p "$root/dist"
tar -C "$build/release" -czf "$root/dist/$name.tar.gz" "$name"
echo "$root/dist/$name.tar.gz"
