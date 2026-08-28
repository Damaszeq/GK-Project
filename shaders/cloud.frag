#version 330 core

in vec2 TexCoords;
in vec3 WorldPos;
out vec4 FragColor;

uniform sampler2D cloudTexture;
uniform float time;
uniform vec3 skyColor;

void main()
{
    // Pomalutku przesuwamy chmury z wiatrem
    vec2 scrolledTex = TexCoords + vec2(time * 0.008, time * 0.003);
    
    // Pobieramy kolor chmur z tekstury
    vec4 texColor = texture(cloudTexture, scrolledTex);
    
    // Odległość od środka mapy (0,0)
    float dist = length(WorldPos.xz);
    
    // Miękkie zanikanie krawędzi chmur (wtapianie w kolor nieba), aby nie było widać kwadratu
    float alpha = smoothstep(900.0, 500.0, dist); 
    
    // Mieszamy kolor nieba z chmurami (maksymalnie 90% nieprzezroczystości)
    vec3 finalColor = mix(skyColor, texColor.rgb, alpha * 0.9);
    
    FragColor = vec4(finalColor, 1.0);
}

