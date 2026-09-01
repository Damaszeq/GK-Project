#version 330 core

in float alpha;
out vec4 FinalColor;

void main()
{
    vec3 rainColor = vec3(0.7, 0.8, 0.9); // lekko błękitny
    
    FinalColor = vec4(rainColor, 0.4 * alpha); // przeźroczystość 
}

