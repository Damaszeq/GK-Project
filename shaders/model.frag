#version 330 core

out vec4 FragColor;

in vec3 FragPos;
in vec3 Normal;
in vec3 ObjectColor;
in float Visibility;

uniform vec3 lightColor;
uniform vec3 lightDirection;
uniform vec3 skyColor;
uniform vec3 cameraPosition; 
uniform float isUnderwater;
uniform float time;

float getCaustics(vec3 pos) {
    float c = sin(pos.x * 1.5 + time * 2.0) * cos(pos.z * 1.5 + time * 1.5);
    c += sin(pos.x * 3.0 - time * 1.5) * sin(pos.z * 3.0 + time * 2.5);
    return smoothstep(0.2, 0.8, c * 0.5 + 0.5);
}

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
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), 64.0); 
    vec3 wetSpecular = vec3(0.5) * spec * lightColor;

    // Oświetlenie podstawowe + refleks wody
    vec3 lighting = (ambient + diffuse) * baseColor + wetSpecular;
    
    // CAUSTYKI NA MODELACH
    float depthFactor = clamp(-FragPos.y * 0.2, 0.0, 1.0);
    float caustics = getCaustics(FragPos) * isUnderwater * depthFactor * 0.4;
    lighting += vec3(0.1, 0.3, 0.4) * caustics;

    // Podwodna mgła i gęstość
    vec3 underwaterFogColor = vec3(0.02, 0.15, 0.25);
    vec3 currentSkyColor = mix(skyColor, underwaterFogColor, isUnderwater);
    float currentVisibility = mix(Visibility, pow(Visibility, 2.0), isUnderwater);

    // Wtapianie obiektów OBJ w kolor mgły
    vec3 finalColor = mix(currentSkyColor, lighting, currentVisibility);
    FragColor = vec4(finalColor, 1.0);
}