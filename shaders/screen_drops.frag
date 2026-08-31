#version 330 core
out vec4 FragColor;

in vec2 TexCoords;
uniform float time;

// Proceduralny wzór kropel na ekranie
float N21(vec2 p) {
    p = fract(p * vec2(123.34, 345.45));
    p += dot(p, p + 34.34);
    return fract(p.x * p.y);
}

void main()
{
    vec2 uv = TexCoords;
    vec2 st = uv * vec2(6.0, 3.5);
    vec2 id = floor(st);
    st = fract(st) - 0.5;
    
    float n = N21(id);
    float t = time * 2.0 + n * 6.28;
    
    float y = -sin(t + sin(t) * 0.5) * 0.4;
    vec2 dropPos = vec2((n - 0.5) * 0.6, y);
    
    float d = length(st - dropPos);
    float drop = smoothstep(0.15, 0.03, d);
    
    // Zniekształcenie/rozmycie ekranu pod kropelkami
    vec3 dropColor = vec3(1.0) * drop * 0.25;
    
    FragColor = vec4(dropColor, drop * 0.4);
}