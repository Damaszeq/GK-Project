#version 330 core

const float rippleSize = 5.0;

layout (location = 0) in vec3 aPos;
layout (location = 1) in float aOffset;

uniform float time;
uniform float fallSpeed;

out float age;

void main() {
    float newY = aPos.y - (time * fallSpeed);
    newY = mod(newY, 40.0);
    
    // Gdy kropla spada poniżej 0, nowY przeskakuje na 40.0.
    // Wiek kropli na wodzie (od 0.0 do 1.0 sekundy):
    age = (40.0 - newY) / fallSpeed;
    
    // Z każdym punktem deszczu mamy 2 wierzchołki (aOffset 0 i 1). Rysujemy okrąg tylko raz per kropla.
    // Rysujemy tylko te, które uderzyły niedawno (age < 1.0)
    if (aOffset > 0.5 || age > 1.0 || age < 0.0) {
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0); // Wyrzucamy poza ekran
        gl_PointSize = 0.0;
    } else {
        // Mapowanie jeziora (-20.0 do 20.0) na NDC (-1.0 do 1.0)
        gl_Position = vec4(aPos.x / 20.0, aPos.z / 20.0, 0.0, 1.0);
        
        // Zwiększamy rozmiar punktu wraz z wiekiem, ale fale są teraz znacznie mniejsze
        gl_PointSize = rippleSize * age; 
    }
}