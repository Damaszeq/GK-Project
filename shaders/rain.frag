#version 330 core

in float alpha;
out vec4 FinalColor;

void main()
{
    // Lekko błękitny, jasny kolor deszczu
    vec3 rainColor = vec3(0.7, 0.8, 0.9);
    
    // Przezroczystość bazowa ok. 0.4 * alpha zanikania z vertex shadera
    FinalColor = vec4(rainColor, 0.4 * alpha);
}

