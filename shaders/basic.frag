#version 330 core

out vec4 FinalColor;

in vec3 FragPos;
in vec3 OurColor;
in float Visibility;
in vec4 FragPosLightSpace;

uniform vec3 skyColor;
uniform vec3 viewPos;
uniform sampler2D shadowMap;

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

    vec3 finalColor = mix(skyColor, terrainColor, Visibility);
    FinalColor = vec4(finalColor, 1.0);
}