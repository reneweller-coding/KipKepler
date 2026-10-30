/**
 * @file Screen.h
 * @brief The virtual pixel screen (640 x 360, or 640 x 400 on 16:10) and its layers: background, the lit world, the
 *        light map, the glow (bloom), the HUD; put together and scaled up by a whole factor into the window.
 * @author Rene Weller
 */
#pragma once

#include <raylib.h>

namespace kepler
{

/** @brief The layers drawn into, in order of composition. */
enum class LayerE
{
    BACKGROUND,  ///< parallax, not lit
    WORLD,       ///< tiles, sprites: multiplied by the light map
    LIGHT,       ///< additive light (cleared to the ambient light)
    GLOW,        ///< emissive pixels, added on top and bloomed
    HUD          ///< on top of everything, not lit
};

class Screen
{
public:
    /** @brief Makes the render targets for the window's size. */
    void init();
    /** @brief Remakes them when the window's shape changed. */
    void resize();
    void unload();

    /** @brief Starts drawing into a layer (ends the one before). */
    void begin( LayerE layer );
    /** @brief Ends drawing into the current layer. */
    void end();
    /**
     * @brief Clears all layers for a new frame.
     * @param[in] ambient  the light where no lamp shines (0..1 per channel)
     */
    void clear( Color ambient );
    /** @brief Composes the layers and draws them into the window (inside BeginDrawing). */
    void present( float bloom = 0.8f, float fade = 0 );
    /** @brief Composes into an image (pictures for tests). */
    Image capture( float bloom = 0.8f );

    /** @brief A soft round light (additive, into LIGHT or GLOW). */
    void light( float x, float y, float radius, Color c, float strength = 1 );

    int   m_w = 640, m_h = 360;    ///< virtual pixels
    int   m_scale = 1;              ///< whole-number scale to the window
    float m_shakeX = 0, m_shakeY = 0;

private:
    void compose( float bloom );

    RenderTexture2D m_bg = {}, m_world = {}, m_light = {}, m_glow = {}, m_hud = {}, m_out = {};
    RenderTexture2D m_blurA = {}, m_blurB = {};
    Shader          m_lit = {}, m_blur = {};
    int             m_litLight = -1, m_blurDir = -1, m_blurSize = -1;
    Texture2D       m_lamp = {};
    bool            m_open = false;
};

}   // namespace kepler
