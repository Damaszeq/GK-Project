#version 330 core

layout (location = 0) in vec3 aPos;

out vec4 clipSpace;
out vec2 textureCoords;
out vec3 toCameraVector;
out vec3 worldPosFrag;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform vec3 cameraPosition;

const float tiling = 6.0;

void main()
{
    vec4 worldPosition = model * vec4(aPos, 1.0);
    clipSpace = projection * view * worldPosition;
    gl_Position = clipSpace;
    textureCoords = vec2(aPos.x / 2.0, aPos.z / 2.0) * tiling;
    
    toCameraVector = cameraPosition - worldPosition.xyz;
    worldPosFrag = worldPosition.xyz;
}

