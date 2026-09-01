import random
import glm
import OpenGL.GL as GL

class BubbleSystem:
    def __init__(self, count=150):
        self.count = count
        self.positions = []
        
        # Inicjalizacja losowych pozycji bąbelków wokół środka
        for _ in range(count):
            x = random.uniform(-30.0, 30.0)
            y = random.uniform(-3.0, 0.0)
            z = random.uniform(-30.0, 30.0)
            self.positions.append(glm.vec3(x, y, z))
            
        # Przygotowanie buforów OpenGL
        self.quad_vertices = [0.0, 0.0, 0.0]
        self.VAO = GL.glGenVertexArrays(1)
        self.VBO = GL.glGenBuffers(1)
        
        GL.glBindVertexArray(self.VAO)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.VBO)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, len(self.quad_vertices) * 4, (GL.GLfloat * len(self.quad_vertices))(*self.quad_vertices), GL.GL_STATIC_DRAW)
        
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 3 * 4, None)
        GL.glEnableVertexAttribArray(0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

    def update(self, delta_time, camera_pos):
        # Unoszenie bąbelków do góry i zapętlanie wokół kamery
        for i in range(self.count):
            self.positions[i].y += 1.5 * delta_time # Prędkość unoszenia
            
            # Jeśli bąbelek wzinię się nad poziom wody (np. y = 0.0) albo za daleko od kamery, wraca na dół
            if self.positions[i].y > 0.0 or glm.distance(self.positions[i], camera_pos) > 25.0:
                self.positions[i].x = camera_pos.x + random.uniform(-20.0, 20.0)
                self.positions[i].y = random.uniform(-3.8, -1.0) # Start blisko dna
                self.positions[i].z = camera_pos.z + random.uniform(-20.0, 20.0)

    def draw(self, shader, projection, view, is_underwater):
        if is_underwater <= 0.0:
            return

        shader.use()
        shader.set_mat4("projection", projection)
        shader.set_mat4("view", view)
        
        # Obsługa rozmiaru punktów w OpenGL oraz blendingu (przezroczystości)
        GL.glEnable(GL.GL_PROGRAM_POINT_SIZE)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        
        GL.glBindVertexArray(self.VAO)
        for pos in self.positions:
            model = glm.translate(glm.mat4(1.0), pos)
            shader.set_mat4("model", model)
            GL.glDrawArrays(GL.GL_POINTS, 0, 1)
            
        GL.glBindVertexArray(0)
        GL.glDisable(GL.GL_BLEND)