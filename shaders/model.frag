#version 330 core

out vec4 FragColor;

in vec3 FragPos;
in vec3 Normal;
in vec3 ObjectColor;
in float Visibility;

uniform vec3 lightColor;
uniform vec3 lightDirection;
uniform vec3 skyColor;
uniform vec3 cameraPosition; // Potrzebne do obliczenia specularyzacji wody

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

    // Lekkie przyciemnienie mokrego obiektu
    vec3 baseColor = ObjectColor * 0.8;

    // EFEKT MOKREJ POWIERZCHNI (Specular Gloss)
    vec3 viewDir = normalize(cameraPosition - FragPos);
    vec3 reflectDir = reflect(-lightDir, norm);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), 64.0); // Wąskie, ostre odbicie
    vec3 wetSpecular = vec3(0.5) * spec * lightColor;

    // Oświetlenie podstawowe + refleks wody
    vec3 lighting = (ambient + diffuse) * baseColor + wetSpecular;
    
    // Wtapianie obiektów OBJ w kolor mgły
    vec3 finalColor = mix(skyColor, lighting, Visibility);
    FragColor = vec4(finalColor, 1.0);
}