#version 330 core

in vec4 clipSpace;
in vec2 textureCoords;
in vec3 toCameraVector;
out vec4 FinalColor;

in vec3 worldPosFrag;

uniform sampler2D reflectionTexture;
uniform sampler2D refractionTexture;
uniform sampler2D dudvMap;
uniform sampler2D normalMap;
uniform sampler2D depthMap;
uniform float moveFactor;
uniform vec3 lightColor;
uniform vec3 lightDirection;
uniform float appTime;
uniform sampler2D rippleMap;

const float waveStrength = 0.008;
const float near = 0.1;
const float far = 100.0;

// Jasne zabarwienie tafli oraz ciemniejszy błękit głębi (Water Fog)
const vec3 shallowWaterTint = vec3(0.15, 0.55, 0.65);
const vec3 deepWaterFog = vec3(0.04, 0.18, 0.28);

void main() {
    // 1. NDC & Mapowanie współrzędnych tekstur
    vec2 ndc = (clipSpace.xy / clipSpace.w);
    vec2 texCoords = ndc / 2.0 + 0.5;

    // 2. Wyliczenie głębokości (Water Depth)
    float depth = texture(depthMap, texCoords).r;
    float floorDistance = 2.0 * near * far / (far + near - (2.0 * depth - 1.0) * (far - near));
    float waterDistance = 2.0 * near * far / (far + near - (2.0 * gl_FragCoord.z - 1.0) * (far - near));
    float waterDepth = floorDistance - waterDistance;

    // 3. Zniekształcenie DuDv z dwoma warstwami ruchu (Interferencja fal)
    vec2 distCoord1 = textureCoords * 2.0 + vec2(moveFactor, moveFactor * 0.6);
    vec2 distCoord2 = textureCoords * 2.0 + vec2(-moveFactor * 0.8, moveFactor * 1.2);

    vec2 distortion1 = (texture(dudvMap, distCoord1).rg * 2.0 - 1.0) * waveStrength;
    vec2 distortion2 = (texture(dudvMap, distCoord2).rg * 2.0 - 1.0) * waveStrength;
    // Procedural Ripples from Ripple Map
    vec2 ripTex = vec2(worldPosFrag.x / 40.0 + 0.5, worldPosFrag.z / 40.0 + 0.5);
    
    float texel = 1.0 / 512.0;
    float rL = texture(rippleMap, ripTex - vec2(texel, 0.0)).r;
    float rR = texture(rippleMap, ripTex + vec2(texel, 0.0)).r;
    float rU = texture(rippleMap, ripTex + vec2(0.0, texel)).r;
    float rD = texture(rippleMap, ripTex - vec2(0.0, texel)).r;
    
    // Siła rippli (zwiększona do 5.0 by mocniej zaginać wodę)
    float ripX = (rL - rR) * 5.0;
    float ripZ = (rD - rU) * 5.0;
    
    vec3 rippleNormal = vec3(ripX, 0.0, ripZ);
    vec2 rippleDistortion = vec2(ripX, ripZ) * 0.05;

    vec2 totalDistortion = (distortion1 + distortion2 + rippleDistortion) * clamp(waterDepth / 2.0, 0.0, 1.0);

    vec2 refractTexCoords = clamp(texCoords + totalDistortion, 0.001, 0.999);
    vec2 reflectTexCoords = clamp(vec2(texCoords.x, 1.0 - texCoords.y) + totalDistortion, 0.001, 0.999);

    // 4. Pobranie tekstur Odbicia i Załamania
    vec4 reflectColor = texture(reflectionTexture, reflectTexCoords);
    vec4 refractColor = texture(refractionTexture, refractTexCoords);

    // Efekt mgły wodnej (Water Fog) — im głębsza woda, tym dno staje się ciemniejsze i bardziej niebieskie
    float depthFactor = clamp(waterDepth / 5.0, 0.0, 1.0);
    vec4 depthAdjustedRefract = mix(refractColor, vec4(deepWaterFog, 1.0), depthFactor * 0.75);

    // 5. Efekt Fresnela
    vec3 viewVector = normalize(toCameraVector);
    float refractiveFactor = dot(viewVector, vec3(0.0, 1.0, 0.0));
    refractiveFactor = pow(refractiveFactor, 2.0);
    refractiveFactor = clamp(refractiveFactor, 0.1, 0.85);

    // Miksowanie odbicia z zabarwioną refrakcją
    vec4 baseColor = mix(reflectColor, depthAdjustedRefract, refractiveFactor);

    // 6. Normalne z dwóch warstw i Oświetlenie Specular
    vec4 normalMap1 = texture(normalMap, distCoord1);
    vec4 normalMap2 = texture(normalMap, distCoord2);

    vec3 normal = normalize(vec3(
        (normalMap1.r + normalMap2.r) * 2.0 - 2.0,
        (normalMap1.b + normalMap2.b) * 3.0,
        (normalMap1.g + normalMap2.g) * 2.0 - 2.0
    ) + rippleNormal);

    vec3 lightVector = normalize(-lightDirection);
    vec3 reflectedLight = reflect(-lightVector, normal);
    float specularFactor = max(dot(reflectedLight, viewVector), 0.0);
    specularFactor = pow(specularFactor, 32.0);
    vec3 specularHighlights = lightColor * specularFactor * 0.8;

    // 7. Kolor końcowy z delikatnym filtracją i miękkim brzegiem
    vec3 finalRGB = mix(baseColor.rgb, shallowWaterTint, 0.2) + specularHighlights;

    FinalColor = vec4(finalRGB, clamp(waterDepth / 3.0, 0.0, 1.0));
}