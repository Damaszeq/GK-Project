#version 330 core

in vec4 clipSpace;
in vec2 textureCoords;
in vec3 toCameraVector;
out vec4 FinalColor;

uniform sampler2D reflectionTexture;
uniform sampler2D refractionTexture;
uniform sampler2D dudvMap;
uniform sampler2D normalMap;
uniform sampler2D depthMap;
uniform float moveFactor;
uniform vec3 lightColor;
uniform vec3 lightDirection; // Direction FROM light TO surface

const float waveStrength = 0.02;
const float near = 0.1;
const float far = 100.0;

void main() {
    // 1. Perspective divide to get Normalized Device Coordinates (NDC) in range [-1, 1]
    vec2 ndc = (clipSpace.xy / clipSpace.w);
    
    // 2. Map NDC to texture coordinates [0, 1]
    vec2 texCoords = ndc / 2.0 + 0.5;

    // Calculate water depth first
    float depth = texture(depthMap, texCoords).r;
    float floorDistance = 2.0 * near * far / (far + near - (2.0 * depth - 1.0) * (far - near));
    float waterDepth_z = gl_FragCoord.z;
    float waterDistance = 2.0 * near * far / (far + near - (2.0 * waterDepth_z - 1.0) * (far - near));
    float waterDepth = floorDistance - waterDistance;

    // Calculate distortion
    vec2 distortion1 = (texture(dudvMap, vec2(textureCoords.x + moveFactor, textureCoords.y)).rg * 2.0 - 1.0) * waveStrength;
    vec2 distortion2 = (texture(dudvMap, vec2(-textureCoords.x + moveFactor, textureCoords.y + moveFactor)).rg * 2.0 - 1.0) * waveStrength;
    vec2 totalDistortion = distortion1 + distortion2;
    
    // Dampen distortion near shore
    totalDistortion *= clamp(waterDepth / 2.0, 0.0, 1.0);

    // 3. Define reflection and refraction texture coordinates
    vec2 refractTexCoords = vec2(texCoords.x, texCoords.y) + totalDistortion;
    vec2 reflectTexCoords = vec2(texCoords.x, 1.0 - texCoords.y) + totalDistortion; // Inverse Y for reflection
    
    // clamp edge bleeding
    refractTexCoords = clamp(refractTexCoords, 0.001, 0.999);
    reflectTexCoords = clamp(reflectTexCoords, 0.001, 0.999);

    // 4. Sample textures
    vec4 reflectColor = texture(reflectionTexture, reflectTexCoords);
    vec4 refractColor = texture(refractionTexture, refractTexCoords);

    vec3 viewVector = normalize(toCameraVector);
    
    // Fresnel Effect
    float refractiveFactor = dot(viewVector, vec3(0.0, 1.0, 0.0));
    refractiveFactor = pow(refractiveFactor, 1.5);
    refractiveFactor = clamp(refractiveFactor, 0.0, 1.0);
    
    // Mix reflection and refraction based on Fresnel
    FinalColor = mix(reflectColor, refractColor, refractiveFactor);
    
    // Normal map calculation
    vec4 normalMapColor = texture(normalMap, vec2(textureCoords.x + moveFactor, textureCoords.y));
    vec3 normal = vec3(normalMapColor.r * 2.0 - 1.0, normalMapColor.b * 3.0, normalMapColor.g * 2.0 - 1.0);
    normal = normalize(normal);
    
    vec3 lightVector = normalize(lightDirection);
    
    vec3 reflectedLight = reflect(lightVector, normal);
    float specularFactor = max(dot(reflectedLight, viewVector), 0.0);
    specularFactor = pow(specularFactor, 20.0); // shineDamper
    vec3 specularHighlights = lightColor * specularFactor * 0.6; // reflectivity
    
    // Add a slight blue tint and specular highlight, fade at shore
    FinalColor = mix(FinalColor, vec4(0.0, 0.3, 0.5, 1.0), 0.2 * clamp(waterDepth / 5.0, 0.0, 1.0)) + vec4(specularHighlights, 0.0) * clamp(waterDepth / 1.0, 0.0, 1.0);
    
    // Soft edges: fade water alpha at shore
    FinalColor.a = clamp(waterDepth / 2.0, 0.0, 1.0);
}

