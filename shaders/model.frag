#version 330 core

out vec4 FragColor;

in vec3 FragPos;
in vec3 Normal;
in vec3 ObjectColor;
in float Visibility;

uniform vec3 lightColor;
uniform vec3 lightDirection;
uniform vec3 skyColor;

void main()
{
    // Ambient
    float ambientStrength = 0.35;
    vec3 ambient = ambientStrength * lightColor;

    // Diffuse
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(-lightDirection);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * lightColor;

    vec3 baseColor = ObjectColor;
    vec3 lighting = (ambient + diffuse) * baseColor;
    
    // Wtapianie obiektów OBJ w kolor mgły
    vec3 finalColor = mix(skyColor, lighting, Visibility);
    FragColor = vec4(finalColor, 1.0);
}