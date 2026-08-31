#version 330 core
in vec3 FragColor;
in vec3 FragPos;
out vec4 FinalColor;

#define MAX_LANTERNS 10
uniform vec3 lanternPositions[MAX_LANTERNS];
uniform int numLanterns;
uniform vec3 lanternColor;

void main() {
    vec3 result = FragColor;
    
    // Add point lights
    for(int i = 0; i < numLanterns; i++) {
        float distance = length(lanternPositions[i] - FragPos);
        // Attenuation
        float attenuation = 1.0 / (1.0 + 0.7 * distance + 1.8 * (distance * distance));
        // We boost the intensity slightly
        result += lanternColor * attenuation * 5.0;
    }
    
    FinalColor = vec4(result, 1.0);
}