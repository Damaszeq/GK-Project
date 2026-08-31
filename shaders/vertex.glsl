#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aColor;

out vec3 FragPos;
out vec3 OurColor;
out float Visibility;
out vec4 FragPosLightSpace; // Do cieni

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform vec4 plane;
uniform mat4 lightSpaceMatrix; // Macierz rzutowania światła

uniform float density = 0.010;
uniform float gradient = 1.5;

void main()
{
    vec4 worldPosition = model * vec4(aPos, 1.0);
    gl_ClipDistance[0] = dot(worldPosition, plane);

    vec4 positionRelativeToCam = view * worldPosition;
    gl_Position = projection * positionRelativeToCam;

    FragPos = vec3(worldPosition);
    OurColor = aColor;
    FragPosLightSpace = lightSpaceMatrix * worldPosition;

    float distance = length(positionRelativeToCam.xyz);
    float baseVisibility = exp(-pow((distance * density), gradient));
    
    float heightFactor = clamp((FragPos.y + 0.5) * 0.08, 0.0, 0.4); 
    
    Visibility = clamp(baseVisibility - heightFactor, 0.0, 1.0);
}