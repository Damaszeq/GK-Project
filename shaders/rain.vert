#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in float aOffset; // 0.0 for top of drop, 1.0 for bottom

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

uniform float time;
uniform float fallSpeed;
uniform vec3 windDirection;

// Płaszczyzna obcinania dla FBO (żeby deszcz nie rysował się pod/nad wodą w odbiciach)
uniform vec4 plane;

out float alpha;

void main()
{
    // Obliczamy spadanie (zapętlone od 0 do 40)
    float newY = aPos.y - (time * fallSpeed);
    newY = mod(newY, 40.0);
    
    vec3 currentPos = vec3(aPos.x, newY, aPos.z);
    
    // Przesunięcie dolnego końca kropli o wiatr i grawitację
    if (aOffset > 0.5) {
        currentPos += windDirection;
    }
    
    vec4 worldPosition = model * vec4(currentPos, 1.0);
    gl_ClipDistance[0] = dot(worldPosition, plane);
    
    gl_Position = projection * view * worldPosition;
    
    // Delikatne zanikanie na samej górze (y=40) i na dole (y=0) żeby krople nie znikały gwałtownie
    float fadeTop = clamp((40.0 - newY) / 2.0, 0.0, 1.0);
    float fadeBottom = clamp(newY / 2.0, 0.0, 1.0);
    alpha = fadeTop * fadeBottom;
}

