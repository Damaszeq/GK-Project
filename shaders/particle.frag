#version 330 core
out vec4 FragColor;

void main()
{
    // Nadajemy bąbelkom lekko przezroczysty, jasnoniebieski/biały kolor z okrągłym kształtem
    vec2 coord = gl_PointCoord - vec2(0.5);
    if(length(coord) > 0.5)
        discard; // Tworzy okrągły kształt punktu
        
    FragColor = vec4(0.7, 0.9, 1.0, 0.6);
}