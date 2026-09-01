import numpy as np
from OpenGL.GL import *

class Model:
    def __init__(self, filepath):
        self.vertices = []
        self.vertex_count = 0
        self.vao = 0
        self.vbo = 0
        self.load_obj(filepath)
        self.setup_gl()

    def load_obj(self, filepath):
        import os
        base_dir = os.path.dirname(filepath)
        
        temp_vertices = []
        temp_uvs = []
        temp_normals = []
        
        materials = {}
        current_color = (1.0, 1.0, 1.0)
        
        final_data = [] # [px, py, pz, u, v, nx, ny, nz, cr, cg, cb] (pozycja, UV, normal, kolor)

        # Wczytywanie pliku OBJ
        with open(filepath, 'r') as file:
            for line in file:
                if line.startswith('mtllib '):
                    mtl_filename = line.split()[1]
                    mtl_path = os.path.join(base_dir, mtl_filename)
                    if os.path.exists(mtl_path):
                        with open(mtl_path, 'r') as mfile:
                            curr_mtl = None
                            for mline in mfile:
                                if mline.startswith('newmtl '):
                                    curr_mtl = mline.split()[1]
                                elif mline.startswith('Kd '):
                                    parts = mline.split()
                                    materials[curr_mtl] = (float(parts[1]), float(parts[2]), float(parts[3]))
                elif line.startswith('usemtl '):
                    mtl_name = line.split()[1]
                    if mtl_name in materials:
                        current_color = materials[mtl_name]
                elif line.startswith('v '):
                    parts = line.split()
                    temp_vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
                elif line.startswith('vt '):
                    parts = line.split()
                    temp_uvs.append((float(parts[1]), float(parts[2])))
                elif line.startswith('vn '):
                    parts = line.split()
                    temp_normals.append((float(parts[1]), float(parts[2]), float(parts[3])))
                elif line.startswith('f '):
                    parts = line.split()[1:]
                    
                    # Triangulacja wielokątów (jeśli jest więcej niż 3 wierzchołki)
                    for i in range(1, len(parts) - 1):
                        indices = [parts[0], parts[i], parts[i+1]]
                        for vertex_data in indices:
                            v_data = vertex_data.split('/')
                            
                            # pozycja wierzchołka
                            v_idx = int(v_data[0]) - 1
                            pos = temp_vertices[v_idx]
                            
                            # koordynaty UV
                            uv = (0.0, 0.0)
                            if len(v_data) > 1 and v_data[1] != '':
                                vt_idx = int(v_data[1]) - 1
                                uv = temp_uvs[vt_idx]
                                
                            # normale
                            normal = (0.0, 1.0, 0.0)
                            if len(v_data) > 2 and v_data[2] != '':
                                vn_idx = int(v_data[2]) - 1
                                normal = temp_normals[vn_idx]
                            
                            final_data.extend([
                                pos[0], pos[1], pos[2], 
                                uv[0], uv[1], 
                                normal[0], normal[1], normal[2],
                                current_color[0], current_color[1], current_color[2]
                            ])

        self.vertices = np.array(final_data, dtype=np.float32)
        self.vertex_count = len(self.vertices) // 11

    def setup_gl(self):
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        # Stride -> 11 floats (3 pozycja, 2 uv, 3 normal, 3 kolor)
        stride = 11 * 4
        
        # Pozycja wierzchołka
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        # UV 
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))
        glEnableVertexAttribArray(1)
        
        # Normal 
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(5 * 4))
        glEnableVertexAttribArray(2)
        
        # Kolor 
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8 * 4))
        glEnableVertexAttribArray(3)

        glBindVertexArray(0)

    def draw(self):
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
        glBindVertexArray(0)

