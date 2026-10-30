# KIP KEPLER -- a 2D sci-fi action platformer in HD pixel art.
# C++20 on raylib (fetched at configure time), like Dark Concordance.
cmake_minimum_required( VERSION 3.22 )

# raylib 5.5 and its GLFW still ask for old CMake versions; CMake 4 refuses those without this floor.
set( CMAKE_POLICY_VERSION_MINIMUM 3.5 )
set( CMAKE_POLICY_DEFAULT_CMP0091 NEW )
set( CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>" )

project( KipKepler VERSION 1.0.0 LANGUAGES C CXX )

set( CMAKE_CXX_STANDARD 20 )
set( CMAKE_CXX_STANDARD_REQUIRED ON )
set( CMAKE_CXX_EXTENSIONS OFF )

set( KEPLER_BIN_DIR "" CACHE PATH "where the game is copied after each build (bin/<preset>)" )

include( FetchContent )
set( KEPLER_EXTRACT_TIMESTAMP "" )
if( CMAKE_VERSION VERSION_GREATER_EQUAL 3.24 )
    set( KEPLER_EXTRACT_TIMESTAMP DOWNLOAD_EXTRACT_TIMESTAMP TRUE )
endif()
set( BUILD_EXAMPLES OFF CACHE BOOL "" FORCE )
set( BUILD_GAMES OFF CACHE BOOL "" FORCE )
set( BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE )
# raylib 5.5's sources travel with the game in third_party/raylib (src, cmake, CMakeLists of the 5.5 tag), so a
# build needs no network; without that folder the tag is fetched.
if( EXISTS ${CMAKE_SOURCE_DIR}/third_party/raylib/CMakeLists.txt )
    set( FETCHCONTENT_SOURCE_DIR_RAYLIB ${CMAKE_SOURCE_DIR}/third_party/raylib )
endif()
FetchContent_Declare( raylib
    URL https://github.com/raysan5/raylib/archive/refs/tags/5.5.tar.gz
    ${KEPLER_EXTRACT_TIMESTAMP} )
FetchContent_MakeAvailable( raylib )

file( GLOB KEPLER_SOURCES CONFIGURE_DEPENDS ${CMAKE_SOURCE_DIR}/src/*.cpp ${CMAKE_SOURCE_DIR}/src/*.h )

# KeplerTool: the console helper for level design (the checker), no window.
add_executable( KeplerTool ${CMAKE_SOURCE_DIR}/src/tool/Tool.cpp ${CMAKE_SOURCE_DIR}/src/Level.cpp
                           ${CMAKE_SOURCE_DIR}/src/Physics.cpp ${CMAKE_SOURCE_DIR}/src/Checker.cpp
                           ${CMAKE_SOURCE_DIR}/src/Content.cpp )
target_link_libraries( KeplerTool PRIVATE raylib )
target_compile_definitions( KeplerTool PRIVATE KEPLER_ASSETS="${CMAKE_SOURCE_DIR}/assets" )
if( MSVC )
    target_compile_options( KeplerTool PRIVATE /W4 /permissive- /utf-8 /wd4244 /wd4267 /wd4305 )
    target_compile_definitions( KeplerTool PRIVATE _CRT_SECURE_NO_WARNINGS )
else()
    target_compile_options( KeplerTool PRIVATE -Wall -Wextra -fwrapv )
    target_link_options( KeplerTool PRIVATE -static-libstdc++ -static-libgcc )
endif()
add_executable( KipKepler WIN32 ${KEPLER_SOURCES} )
target_link_libraries( KipKepler PRIVATE raylib )
# The assets are read from assets/ beside the program, else from the source tree.
target_compile_definitions( KipKepler PRIVATE KEPLER_ASSETS="${CMAKE_SOURCE_DIR}/assets"
                                              KEPLER_VERSION="${PROJECT_VERSION}" )
if( MSVC )
    target_compile_options( KipKepler PRIVATE /W4 /permissive- /utf-8 /wd4244 /wd4267 /wd4305 )
    target_compile_definitions( KipKepler PRIVATE _CRT_SECURE_NO_WARNINGS )
    # A window program without a console that still starts in main().
    target_link_options( KipKepler PRIVATE /ENTRY:mainCRTStartup )
else()
    # -fwrapv: an int that overflows wraps round as with MSVC, so hashes pick the same tiles everywhere.
    target_compile_options( KipKepler PRIVATE -Wall -Wextra -Wno-missing-field-initializers -fwrapv )
    target_link_options( KipKepler PRIVATE -static-libstdc++ -static-libgcc )
endif()

if( KEPLER_BIN_DIR )
    foreach( target KipKepler KeplerTool )
        add_custom_command( TARGET ${target} POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E make_directory "${KEPLER_BIN_DIR}"
            COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:${target}> "${KEPLER_BIN_DIR}" )
    endforeach()
endif()
