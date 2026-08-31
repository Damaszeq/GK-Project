#version 330 core

in vec2 TexCoords;
in vec3 Normal;
in vec3 FragPos;
in vec3 ObjectColor;

out vec4 FragColor;

uniform vec3 lightColor;
uniform vec3 lightDirection;
uniform vec3 skyColor;
uniform vec3 cameraPosition;

void main()
{
    // Ambient
    float ambientStrength = 0.5;
    vec3 ambient = ambientStrength * lightColor;
    
    // Diffuse
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(-lightDirection);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * lightColor;
    
    vec3 result = (ambient + diffuse) * ObjectColor;
    
    // Odległość od kamery do płynnego wtopienia we mgle
    float distance = length(FragPos - cameraPosition);
    float fogFactor = smoothstep(20.0, 70.0, distance);
    result = mix(result, skyColor, fogFactor);
    
    FragColor = vec4(result, 1.0);
}

