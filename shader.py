from OpenGL.GL import *
import glm

class Shader:
    def __init__(self, vertex_path, fragment_path):
        # 1. Odczyt kodu shaderów z plików
        with open(vertex_path, 'r', encoding='utf-8') as f:
            vertex_code = f.read()
        with open(fragment_path, 'r', encoding='utf-8') as f:
            fragment_code = f.read()

        # 2. Kompilacja Vertex Shadera
        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex_shader, vertex_code)
        glCompileShader(vertex_shader)
        if not glGetShaderiv(vertex_shader, GL_COMPILE_STATUS):
            raise Exception(f"Błąd kompilacji Vertex Shadera: {glGetShaderInfoLog(vertex_shader).decode()}")

        # 3. Kompilacja Fragment Shadera
        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment_shader, fragment_code)
        glCompileShader(fragment_shader)
        if not glGetShaderiv(fragment_shader, GL_COMPILE_STATUS):
            raise Exception(f"Błąd kompilacji Fragment Shadera: {glGetShaderInfoLog(fragment_shader).decode()}")

        # 4. Linkowanie programu
        self.program = glCreateProgram()
        glAttachShader(self.program, vertex_shader)
        glAttachShader(self.program, fragment_shader)
        glLinkProgram(self.program)

        if not glGetProgramiv(self.program, GL_LINK_STATUS):
            raise Exception(f"Błąd linkowania programu Shadera: {glGetProgramInfoLog(self.program).decode()}")

        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

    def use(self):
        glUseProgram(self.program)

    def set_mat4(self, name, value):
        loc = glGetUniformLocation(self.program, name)
        glUniformMatrix4fv(loc, 1, GL_FALSE, glm.value_ptr(value))

    def set_vec4(self, name: str, vector):
        location = glGetUniformLocation(self.program, name)
        glUniform4f(location, vector.x, vector.y, vector.z, vector.w)