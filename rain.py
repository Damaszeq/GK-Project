import numpy as np
import random
from OpenGL.GL import *
import ctypes

class Rain:
    def __init__(self, num_drops=15000, bounds=(-50, 50, 0, 40, -50, 50)):
        self.num_drops = num_drops
        
        min_x, max_x, min_y, max_y, min_z, max_z = bounds
        
        vertices = []
        for _ in range(num_drops):
            x = random.uniform(min_x, max_x)
            y = random.uniform(min_y, max_y)
            z = random.uniform(min_z, max_z)
            
            # Wierzchołek górny kropli (offset = 0.0)
            vertices.extend([x, y, z, 0.0])
            # Wierzchołek dolny kropli (offset = 1.0)
            vertices.extend([x, y, z, 1.0])
            
        vertices = np.array(vertices, dtype=np.float32)
        
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        
        stride = 4 * vertices.itemsize
        
        # aPos (vec3)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        
        # aOffset (float)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * vertices.itemsize))
        
        glBindVertexArray(0)

    def draw(self):
        glBindVertexArray(self.vao)
        glDrawArrays(GL_LINES, 0, self.num_drops * 2)
        glBindVertexArray(0)

    def draw_points(self):
        glBindVertexArray(self.vao)
        glDrawArrays(GL_POINTS, 0, self.num_drops * 2)
        glBindVertexArray(0)

