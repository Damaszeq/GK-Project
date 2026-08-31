#version 330 core

out vec4 FinalColor;

in vec3 FragPos;
in vec3 OurColor;
in float Visibility;

uniform vec3 skyColor;

void main()
{
    // Mieszanie koloru terenu z kolorem mgły/nieba
    vec3 finalColor = mix(skyColor, OurColor, Visibility);
    FinalColor = vec4(finalColor, 1.0);
}