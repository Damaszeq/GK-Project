#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoords;
layout (location = 2) in vec3 aNormal;
layout (location = 3) in vec3 aColor;

out vec3 Normal;
out vec3 FragPos;
out vec3 ObjectColor;
out float Visibility;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform vec4 plane;

// gęstość mgły
uniform float density = 0.016;
uniform float gradient = 1.5;

void main()
{
    vec4 worldPosition = model * vec4(aPos, 1.0);
    
    // Klipowanie dla odbicia/załamania
    gl_ClipDistance[0] = dot(worldPosition, plane);
    
    vec4 positionRelativeToCam = view * worldPosition;
    gl_Position = projection * positionRelativeToCam;
    
    FragPos = vec3(worldPosition);
    Normal = mat3(transpose(inverse(model))) * aNormal;
    ObjectColor = aColor;

    // Obliczanie widoczności
    float distance = length(positionRelativeToCam.xyz);
    Visibility = exp(-pow((distance * density), gradient));
    Visibility = clamp(Visibility, 0.0, 1.0);
}