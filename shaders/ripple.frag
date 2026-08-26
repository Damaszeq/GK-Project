#version 330 core

in float age;
out vec4 FragColor;

void main() {
    // Współrzędne wewnątrz punktu (Point Sprite) od -1.0 do 1.0
    vec2 coord = gl_PointCoord * 2.0 - 1.0;
    float dist = length(coord);
    
    if (dist > 1.0) discard;
    
    // Okrąg powiększający się i zanikający
    // Chcemy falę (grzbiet). Smoothstep tworzy ładny, miękki pierścień
    float thickness = 0.15; // Grubość fali
    float ring = smoothstep(1.0 - thickness, 1.0, dist) - smoothstep(1.0, 1.0 + thickness, dist);
    
    // Zmniejszamy siłę fali wraz z jej wiekiem
    float strength = (1.0 - age) * ring * 0.2; 
    
    // Zapisujemy wyliczoną siłę (będzie zsumowana w FBO dzięki Additive Blending)
    FragColor = vec4(strength, strength, strength, 1.0);
}

