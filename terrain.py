import math
from PIL import Image
from mesh import Mesh

class Terrain:
    def __init__(self, heightmap_path, size=40.0, max_height=4.0, min_height=-1.5):
        self.size = size
        self.max_height = max_height
        self.min_height = min_height
        
        self.mesh = self._generate_terrain(heightmap_path)

    def _generate_terrain(self, path):
        # 1. Wczytanie obrazu
        img = Image.open(path).convert('L')
        width, height = img.size
        pixels = img.load()

        # 2. Generowanie siatki wysokości z organicznym szumem
        heights = []
        for z in range(height):
            row = []
            for x in range(width):
                gray_val = pixels[x, z] / 255.0
                base_y = self.min_height + gray_val * (self.max_height - self.min_height)
                
                world_x = (x / (width - 1)) * self.size
                world_z = (z / (height - 1)) * self.size
                
                if base_y > 0.1:
                    n1 = math.sin(world_x * 0.6 + world_z * 0.4) * math.cos(world_z * 0.7 - world_x * 0.3) * 0.35
                    n2 = math.sin(world_x * 1.5 - world_z * 1.2) * 0.12
                    y = base_y + n1 + n2
                else:
                    y = base_y
                    
                row.append(y)
            heights.append(row)
            
        self.heights = heights
        self.width = width
        self.height = height

        # 3. Wyliczanie wygładzonych normalnych
        normals = [[(0.0, 1.0, 0.0) for _ in range(width)] for _ in range(height)]
        dx = self.size / (width - 1)
        dz = self.size / (height - 1)

        for z in range(1, height - 1):
            for x in range(1, width - 1):
                hl = heights[z][x - 1]
                hr = heights[z][x + 1]
                hd = heights[z - 1][x]
                hu = heights[z + 1][x]

                nx = (hl - hr) / (2.0 * dx)
                ny = 1.0
                nz = (hd - hu) / (2.0 * dz)
                
                length = math.sqrt(nx * nx + ny * ny + nz * nz)
                if length > 0:
                    normals[z][x] = (nx / length, ny / length, nz / length)

        # 4. Generowanie wierzchołków
        vertices = []
        half_size = self.size / 2.0

        def calculate_shaded_color(y, normal):
            slope = normal[1]
            t = (y - self.min_height) / (self.max_height - self.min_height)
            t = max(0.0, min(1.0, t))

            sand = (0.32, 0.28, 0.22)
            grass = (0.16, 0.32, 0.12)
            rock = (0.24, 0.25, 0.24)

            if y < 0.1:
                base = sand
            elif slope < 0.72:
                base = rock
            else:
                base = (grass[0] * (0.7 + 0.3 * t), 
                        grass[1] * (0.7 + 0.3 * t), 
                        grass[2] * (0.7 + 0.3 * t))

            light_dir = (0.2, 0.8, 0.3)
            dot_val = normal[0] * light_dir[0] + normal[1] * light_dir[1] + normal[2] * light_dir[2]
            diffuse = max(0.45, dot_val)

            return (base[0] * diffuse, base[1] * diffuse, base[2] * diffuse)

        # --- Powierzchnia terenu ---
        for z in range(height - 1):
            for x in range(width - 1):
                x0 = (x / (width - 1)) * self.size - half_size
                x1 = ((x + 1) / (width - 1)) * self.size - half_size
                z0 = (z / (height - 1)) * self.size - half_size
                z1 = ((z + 1) / (height - 1)) * self.size - half_size

                y00, y10 = heights[z][x], heights[z][x + 1]
                y01, y11 = heights[z + 1][x], heights[z + 1][x + 1]

                c00 = calculate_shaded_color(y00, normals[z][x])
                c10 = calculate_shaded_color(y10, normals[z][x + 1])
                c01 = calculate_shaded_color(y01, normals[z + 1][x])
                c11 = calculate_shaded_color(y11, normals[z + 1][x + 1])

                vertices.extend([x0, y00, z0, c00[0], c00[1], c00[2]])
                vertices.extend([x0, y01, z1, c01[0], c01[1], c01[2]])
                vertices.extend([x1, y10, z0, c10[0], c10[1], c10[2]])

                vertices.extend([x1, y10, z0, c10[0], c10[1], c10[2]])
                vertices.extend([x0, y01, z1, c01[0], c01[1], c01[2]])
                vertices.extend([x1, y11, z1, c11[0], c11[1], c11[2]])

        # --- Dodawanie pionowych ścian na krawędziach (Skirt) ---
        skirt_bottom = -5.0
        skirt_color = (0.15, 0.15, 0.14)

        def add_quad(p1, p2, p3, p4, col):
            # p1, p2, p3, p4: (x, y, z)
            vertices.extend([p1[0], p1[1], p1[2], col[0], col[1], col[2]])
            vertices.extend([p2[0], p2[1], p2[2], col[0], col[1], col[2]])
            vertices.extend([p3[0], p3[1], p3[2], col[0], col[1], col[2]])

            vertices.extend([p3[0], p3[1], p3[2], col[0], col[1], col[2]])
            vertices.extend([p2[0], p2[1], p2[2], col[0], col[1], col[2]])
            vertices.extend([p4[0], p4[1], p4[2], col[0], col[1], col[2]])

        # Krawędź Zachodnia (x = 0)
        for z in range(height - 1):
            z0 = (z / (height - 1)) * self.size - half_size
            z1 = ((z + 1) / (height - 1)) * self.size - half_size
            y0, y1 = heights[z][0], heights[z + 1][0]
            add_quad((-half_size, y0, z0), (-half_size, skirt_bottom, z0),
                     (-half_size, y1, z1), (-half_size, skirt_bottom, z1), skirt_color)

        # Krawędź Wschodnia (x = width - 1)
        for z in range(height - 1):
            z0 = (z / (height - 1)) * self.size - half_size
            z1 = ((z + 1) / (height - 1)) * self.size - half_size
            y0, y1 = heights[z][width - 1], heights[z + 1][width - 1]
            add_quad((half_size, skirt_bottom, z0), (half_size, y0, z0),
                     (half_size, skirt_bottom, z1), (half_size, y1, z1), skirt_color)

        # Krawędź Północna (z = 0)
        for x in range(width - 1):
            x0 = (x / (width - 1)) * self.size - half_size
            x1 = ((x + 1) / (width - 1)) * self.size - half_size
            y0, y1 = heights[0][x], heights[0][x + 1]
            add_quad((x0, skirt_bottom, -half_size), (x0, y0, -half_size),
                     (x1, skirt_bottom, -half_size), (x1, y1, -half_size), skirt_color)

        # Krawędź Południowa (z = height - 1)
        for x in range(width - 1):
            x0 = (x / (width - 1)) * self.size - half_size
            x1 = ((x + 1) / (width - 1)) * self.size - half_size
            y0, y1 = heights[height - 1][x], heights[height - 1][x + 1]
            add_quad((x0, y0, half_size), (x0, skirt_bottom, half_size),
                     (x1, y1, half_size), (x1, skirt_bottom, half_size), skirt_color)

        return Mesh(vertices)

    def get_height(self, x, z):
        half_size = self.size / 2.0
        nx = (x + half_size) / self.size
        nz = (z + half_size) / self.size
        
        gx = nx * (self.width - 1)
        gz = nz * (self.height - 1)
        
        if gx < 0 or gx >= self.width - 1 or gz < 0 or gz >= self.height - 1:
            return 0.0
            
        ix = int(gx)
        iz = int(gz)
        fx = gx - ix
        fz = gz - iz
        
        h00 = self.heights[iz][ix]
        h10 = self.heights[iz][ix + 1]
        h01 = self.heights[iz + 1][ix]
        h11 = self.heights[iz + 1][ix + 1]
        
        h0 = h00 * (1 - fx) + h10 * fx
        h1 = h01 * (1 - fx) + h11 * fx
        return h0 * (1 - fz) + h1 * fz

    def draw(self):
        self.mesh.draw()