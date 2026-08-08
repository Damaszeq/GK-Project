#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aColor;


out vec3 FragColor; 

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

// Uniform dla płaszczyzny obcinania
uniform vec4 plane;

void main()
{
    // Obliczamy pozycję wierzchołka w przestrzeni świata
    vec4 worldPosition = model * vec4(aPos, 1.0);

    // Obcinanie obiektów
    gl_ClipDistance[0] = dot(worldPosition, plane);

    // Standardowe przeliczenie pozycji na ekran
    gl_Position = projection * view * worldPosition;
    
    // ZMIANA: Przekazujemy kolor do FragColor
    FragColor = aColor; 
}