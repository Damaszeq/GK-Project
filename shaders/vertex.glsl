#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aColor;

out vec3 FragPos;
out vec3 OurColor;
out float Visibility;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform vec4 plane;

// Zmniejszona gęstość mgły (wcześniej 0.025)
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

    // Obliczanie widoczności
    float distance = length(positionRelativeToCam.xyz);
    Visibility = exp(-pow((distance * density), gradient));
    Visibility = clamp(Visibility, 0.0, 1.0);
}