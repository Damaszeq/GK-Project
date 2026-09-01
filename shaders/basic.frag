#version 330 core

out vec4 FinalColor;

in vec3 FragPos;
in vec3 OurColor;
in float Visibility;
in vec4 FragPosLightSpace;

uniform vec3 skyColor;
uniform vec3 viewPos;
uniform sampler2D shadowMap;
uniform float isUnderwater;
uniform float time;

float ShadowCalculation(vec4 fragPosLightSpace, vec3 normal, vec3 lightDir)
{
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;
    projCoords = projCoords * 0.5 + 0.5;
    
    if(projCoords.z > 1.0)
        return 0.0;
        
    float closestDepth = texture(shadowMap, projCoords.xy).r; 
    float currentDepth = projCoords.z;
    
    float bias = max(0.005 * (1.0 - dot(normal, lightDir)), 0.001);
    
    float shadow = 0.0;
    vec2 texelSize = 1.0 / textureSize(shadowMap, 0);
    for(int x = -2; x <= 2; ++x)
    {
        for(int y = -2; y <= 2; ++y)
        {
            float pcfDepth = texture(shadowMap, projCoords.xy + vec2(x, y) * texelSize).r; 
            shadow += currentDepth - bias > pcfDepth ? 1.0 : 0.0;        
        }    
    }
    shadow /= 25.0;
    
    return shadow * 0.4;
}

// Proceduralna funkcja generująca caustyki na podstawie pozycji i czasu
float getCaustics(vec3 pos) {
    float c = sin(pos.x * 1.5 + time * 2.0) * cos(pos.z * 1.5 + time * 1.5);
    c += sin(pos.x * 3.0 - time * 1.5) * sin(pos.z * 3.0 + time * 2.5);
    return smoothstep(0.2, 0.8, c * 0.5 + 0.5);
}

void main()
{
    vec3 baseColor = OurColor * 0.75;

    vec3 lightDir = normalize(vec3(-0.2, -1.0, -0.1));
    vec3 lightColor = vec3(0.6, 0.65, 0.7);
    vec3 norm = vec3(0.0, 1.0, 0.0);

    float diff = max(dot(norm, -lightDir), 0.0);
    vec3 diffuse = diff * lightColor * baseColor;
    vec3 ambient = 0.55 * baseColor;

    vec3 viewDir = normalize(viewPos - FragPos);
    vec3 reflectDir = reflect(lightDir, norm);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), 16.0);
    vec3 wetSpecular = vec3(0.15) * spec * lightColor;

    float shadow = ShadowCalculation(FragPosLightSpace, norm, -lightDir);
    
    vec3 terrainColor = ambient + (1.0 - shadow) * diffuse + wetSpecular;

    // CAUSTYKI
    // Im niżej (mniejsza współrzędna Y), tym wyraźniejsze caustyki pod wodą
    float depthFactor = clamp(-FragPos.y * 0.2, 0.0, 1.0);
    float caustics = getCaustics(FragPos) * isUnderwater * depthFactor * 0.4;
    terrainColor += vec3(0.1, 0.3, 0.4) * caustics;

    // Podwodna mgła i gęstość
    vec3 underwaterFogColor = vec3(0.02, 0.15, 0.25);
    vec3 currentSkyColor = mix(skyColor, underwaterFogColor, isUnderwater);
    float currentVisibility = mix(Visibility, pow(Visibility, 2.0), isUnderwater);

    vec3 finalColor = mix(currentSkyColor, terrainColor, currentVisibility);
    FinalColor = vec4(finalColor, 1.0);
}