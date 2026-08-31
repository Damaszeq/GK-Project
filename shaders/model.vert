#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoords;
layout (location = 2) in vec3 aNormal;
layout (location = 3) in vec3 aColor;

out vec2 TexCoords;
out vec3 Normal;
out vec3 FragPos;
out vec3 ObjectColor;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform vec4 plane;

void main()
{
    vec4 worldPosition = model * vec4(aPos, 1.0);
    
    // Klipowanie dla odbicia/załamania
    gl_ClipDistance[0] = dot(worldPosition, plane);
    
    FragPos = vec3(worldPosition);
    Normal = mat3(transpose(inverse(model))) * aNormal;
    ObjectColor = aColor;
    
    // Odwracamy oś V (Y) tekstury, bo format OBJ często zakłada odwrócone UV
    TexCoords = vec2(aTexCoords.x, 1.0 - aTexCoords.y);
    
    gl_Position = projection * view * worldPosition;
}

