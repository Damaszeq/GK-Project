#version 330 core

in vec4 clipSpace;
in vec2 textureCoords;
in vec3 toCameraVector;
in vec3 worldPosFrag;

out vec4 FinalColor;

uniform sampler2D reflectionTexture;
uniform sampler2D refractionTexture;
uniform sampler2D dudvMap;
uniform sampler2D normalMap;
uniform sampler2D depthMap;
uniform sampler2D rippleMap;

uniform float moveFactor;
uniform vec3 lightColor;
uniform vec3 lightDirection;
uniform float appTime;

const float waveStrength = 0.0; // Płaska woda (lustro)
const float near = 0.1;
const float far = 100.0;

const vec3 shallowWaterTint = vec3(0.10, 0.38, 0.46);
const vec3 deepWaterFog = vec3(0.02, 0.10, 0.18);

float getLinearDepth(vec2 coords) {
    float depth = texture(depthMap, coords).r;
    return 2.0 * near * far / (far + near - (2.0 * depth - 1.0) * (far - near));
}

void main() {
    // 1. NDC i współrzędne UV ekranu
    vec2 ndc = (clipSpace.xy / clipSpace.w);
    vec2 texCoords = ndc * 0.5 + 0.5;

    // 2. Weryfikacja głębokości
    float waterDistance = 2.0 * near * far / (far + near - (2.0 * gl_FragCoord.z - 1.0) * (far - near));
    float floorDistance = getLinearDepth(texCoords);
    float waterDepth = floorDistance - waterDistance;

    // 3. Obliczenie zniekształceń DuDv & Ripples
    vec2 distCoord1 = textureCoords * 4.5 + vec2(moveFactor * 2.0, moveFactor * 1.5);
    vec2 distCoord2 = textureCoords * 4.5 + vec2(-moveFactor * 1.8, moveFactor * 2.2);

    vec2 distortion1 = (texture(dudvMap, distCoord1).rg * 2.0 - 1.0) * waveStrength;
    vec2 distortion2 = (texture(dudvMap, distCoord2).rg * 2.0 - 1.0) * waveStrength;

    vec2 ripTex = vec2(worldPosFrag.x / 40.0 + 0.5, worldPosFrag.z / 40.0 + 0.5);
    float texel = 1.0 / 512.0;
    float rL = texture(rippleMap, ripTex - vec2(texel, 0.0)).r;
    float rR = texture(rippleMap, ripTex + vec2(texel, 0.0)).r;
    float rU = texture(rippleMap, ripTex + vec2(0.0, texel)).r;
    float rD = texture(rippleMap, ripTex - vec2(0.0, texel)).r;
    
    float ripX = (rL - rR) * 8.0;
    float ripZ = (rD - rU) * 8.0;
    
    vec3 rippleNormal = vec3(ripX, 0.0, ripZ);
    vec2 rippleDistortion = vec2(ripX, ripZ) * 0.02;

    vec2 totalDistortion = (distortion1 + distortion2 + rippleDistortion) * clamp(waterDepth / 1.5, 0.0, 1.0);

    // 4. DEPTH SAFETY CHECK (dla Refrakcji)
    vec2 testRefractCoords = clamp(texCoords + totalDistortion, 0.001, 0.999);
    float testFloorDistance = getLinearDepth(testRefractCoords);

    if (testFloorDistance < waterDistance + 0.05) {
        float depthDiff = waterDistance - testFloorDistance;
        float correction = clamp(1.0 - (depthDiff + 0.05) / 0.4, 0.0, 1.0);
        totalDistortion *= correction;
    }

    // Ostateczne UV dla Refrakcji
    vec2 refractTexCoords = clamp(texCoords + totalDistortion, 0.005, 0.995);

    // 5. ODBICIE (bez odwracania osi Y)
    vec2 screenEdgeFactor = smoothstep(vec2(0.0), vec2(0.12), texCoords) * 
                             smoothstep(vec2(1.0), vec2(0.88), texCoords);
    float edgeWeight = screenEdgeFactor.x * screenEdgeFactor.y;

    // Używamy texCoords z odwróconą osią Y, ponieważ kamera odbicia renderuje obraz odwrócony przestrzennie.
    vec2 reflectTexCoords = clamp(vec2(texCoords.x, 1.0 - texCoords.y) + (totalDistortion * edgeWeight), 0.005, 0.995);

    // 6. Próbkowanie buforów
    vec4 reflectColor = texture(reflectionTexture, reflectTexCoords);
    vec4 refractColor = texture(refractionTexture, refractTexCoords);

    float depthFactor = clamp(waterDepth / 5.0, 0.0, 1.0);
    vec4 depthAdjustedRefract = mix(refractColor, vec4(deepWaterFog, 1.0), depthFactor * 0.85);

    // 7. Fresnel
    vec3 viewVector = normalize(toCameraVector);
    float refractiveFactor = dot(viewVector, vec3(0.0, 1.0, 0.0));
    refractiveFactor = pow(refractiveFactor, 1.5);
    refractiveFactor = clamp(refractiveFactor, 0.05, 0.90);

    vec4 baseColor = mix(reflectColor, depthAdjustedRefract, refractiveFactor);

    // Płaska woda, tylko fale od deszczu
    vec3 normal = normalize(vec3(0.0, 1.0, 0.0) + rippleNormal);

    // Brak bezpośredniego słońca (pochmurny dzień)
    vec3 specularHighlights = vec3(0.0);

    vec3 finalRGB = mix(baseColor.rgb, shallowWaterTint, 0.15) + specularHighlights;

    FinalColor = vec4(finalRGB, clamp(waterDepth / 3.0, 0.0, 1.0));
}