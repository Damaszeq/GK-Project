#version 330 core

layout (location = 0) in vec3 aPos;

out vec2 TexCoords;
out vec3 WorldPos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform vec4 plane;

const float tiling = 20.0; // Kafelkowanie

void main()
{
    vec4 worldPosition = model * vec4(aPos, 1.0);
    WorldPos = worldPosition.xyz;
    
    // Płaszczyzna obcinania (dla poprawnego odbicia w wodzie)
    gl_ClipDistance[0] = dot(worldPosition, plane);

    gl_Position = projection * view * worldPosition;
    
    TexCoords = vec2(aPos.x / 1000.0, aPos.z / 1000.0) * tiling;
}