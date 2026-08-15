from PIL import Image
from mesh import Mesh

class Terrain:
    def __init__(self, heightmap_path, size=40.0, max_height=4.0, min_height=-1.5):
        self.size = size
        self.max_height = max_height
        self.min_height = min_height
        
        self.mesh = self._generate_terrain(heightmap_path)

    def _generate_terrain(self, path):
        # 1. Wczytanie obrazu i konwersja
        img = Image.open(path).convert('L')
        width, height = img.size
        pixels = img.load()

        # 2. Tworzenie siatki wysokości 
        heights = []
        for z in range(height):
            row = []
            for x in range(width):
                # Odczytujemy jasność piksela przeskalowujemy na zakres [min_height, max_height]
                gray_val = pixels[x, z] / 255.0
                #gray_val = gray_val ** 0.5 ## korekcja gamma (opcjonalne, złagodzenie kontrastu)
                y = self.min_height + gray_val * (self.max_height - self.min_height)
                row.append(y)
            heights.append(row)

        vertices = []

        # 3. Generowanie trójkątów dla każdego kwadratu siatki (Grid Quad)
        half_size = self.size / 2.0
        
        for z in range(height - 1):
            for x in range(width - 1):
                # Obliczanie pozycji (X, Z) w przestrzeni świata 3D
                x0 = (x / (width - 1)) * self.size - half_size
                x1 = ((x + 1) / (width - 1)) * self.size - half_size
                z0 = (z / (height - 1)) * self.size - half_size
                z1 = ((z + 1) / (height - 1)) * self.size - half_size

                # Wysokości Y dla 4 narożników kwadratu
                y00 = heights[z][x]        # Lewy-górny
                y10 = heights[z][x + 1]    # Prawy-górny
                y01 = heights[z + 1][x]    # Lewy-dolny
                y11 = heights[z + 1][x + 1]# Prawy-dolny
                def get_color(y):
                    # Płynny współczynnik t (od 0.0 na dnie do 1.0 na szczytach)
                    t = (y - self.min_height) / (self.max_height - self.min_height)
                    
                    # Kolor dna (ciemno-brązowy/szary) i góry (zielony)
                    bottom_color = (0.25, 0.22, 0.20)
                    top_color = (0.25, 0.45, 0.15)
                    
                    r = bottom_color[0] + t * (top_color[0] - bottom_color[0])
                    g = bottom_color[1] + t * (top_color[1] - bottom_color[1])
                    b = bottom_color[2] + t * (top_color[2] - bottom_color[2])
                    return (r, g, b)

                c00 = get_color(y00)
                c10 = get_color(y10)
                c01 = get_color(y01)
                c11 = get_color(y11)

                # Pierwszy trójkąt kwadratu (0,0 -> 0,1 -> 1,0)
                vertices.extend([x0, y00, z0,  c00[0], c00[1], c00[2]])
                vertices.extend([x0, y01, z1,  c01[0], c01[1], c01[2]])
                vertices.extend([x1, y10, z0,  c10[0], c10[1], c10[2]])

                # Drugi trójkąt kwadratu (1,0 -> 0,1 -> 1,1)
                vertices.extend([x1, y10, z0,  c10[0], c10[1], c10[2]])
                vertices.extend([x0, y01, z1,  c01[0], c01[1], c01[2]])
                vertices.extend([x1, y11, z1,  c11[0], c11[1], c11[2]])

        return Mesh(vertices)

    def draw(self):
        self.mesh.draw()