import glfw
from OpenGL.GL import *
import time
import glm

# Importujemy stworzone wcześniej klasy
from camera import Camera
from mesh import Mesh
from shader import Shader
from framebuffer import Framebuffer

# Instancja kamery
camera = Camera(glm.vec3(0.0, 2.0, 8.0))

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900

# Callback dla ruchu myszy
def mouse_callback(window, xpos, ypos):
    camera.process_mouse(xpos, ypos)

def main():
    if not glfw.init():
        raise Exception("GLFW error")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Rendering Wody - Faza 1", None, None)
    if not window:
        glfw.terminate()
        raise Exception("GLFW error")

    glfw.make_context_current(window)
    glEnable(GL_DEPTH_TEST)

    # Prchwycenie kursora myszy do okna aplikacji
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    glfw.set_cursor_pos_callback(window, mouse_callback)

    # 1. Wczytanie Shadera
    shader = Shader("shaders/basic.vert", "shaders/basic.frag")

    # 2. Definicja geometrii dla obiektów (Pozycja X,Y,Z + Kolor R,G,B)
    
    # Dno stawu (Duży szary kwadrat na Y = -2.0)
    floor_vertices = [
    -20.0, -2.0, -20.0,   0.2, 0.2, 0.2,
     20.0, -2.0, -20.0,   0.2, 0.2, 0.2,
     20.0, -2.0,  20.0,   0.2, 0.2, 0.2,
    -20.0, -2.0, -20.0,   0.2, 0.2, 0.2,
     20.0, -2.0,  20.0,   0.2, 0.2, 0.2,
    -20.0, -2.0,  20.0,   0.2, 0.2, 0.2,
]
    floor_mesh = Mesh(floor_vertices)

    # Płaszczyzna wody (Niebieski kwadrat na Y = 0.0)
    water_vertices = [
        -10.0, 0.0, -10.0,   0.0, 0.4, 0.8,
         10.0, 0.0, -10.0,   0.0, 0.4, 0.8,
         10.0, 0.0,  10.0,   0.0, 0.4, 0.8,
        -10.0, 0.0, -10.0,   0.0, 0.4, 0.8,
         10.0, 0.0,  10.0,   0.0, 0.4, 0.8,
        -10.0, 0.0,  10.0,   0.0, 0.4, 0.8,
    ]
    water_mesh = Mesh(water_vertices)

    # Sześcian testowy przecinający tafllę wody (Czerwony)
    cube_vertices = [
        # Przednia ściana
        -0.5, -1.0,  0.5,  0.8, 0.1, 0.1,
         0.5, -1.0,  0.5,  0.8, 0.1, 0.1,
         0.5,  1.0,  0.5,  0.8, 0.1, 0.1,
        -0.5, -1.0,  0.5,  0.8, 0.1, 0.1,
         0.5,  1.0,  0.5,  0.8, 0.1, 0.1,
        -0.5,  1.0,  0.5,  0.8, 0.1, 0.1,
        # Tylna ściana
        -0.5, -1.0, -0.5,  0.8, 0.1, 0.1,
         0.5,  1.0, -0.5,  0.8, 0.1, 0.1,
         0.5, -1.0, -0.5,  0.8, 0.1, 0.1,
        -0.5, -1.0, -0.5,  0.8, 0.1, 0.1,
        -0.5,  1.0, -0.5,  0.8, 0.1, 0.1,
         0.5,  1.0, -0.5,  0.8, 0.1, 0.1,
    ]
    cube_mesh = Mesh(cube_vertices)

    last_frame_time = time.time()

    reflection_fbo = Framebuffer(WINDOW_WIDTH, WINDOW_HEIGHT)
    refraction_fbo = Framebuffer(WINDOW_WIDTH, WINDOW_HEIGHT)

    # Pętla główna
    while not glfw.window_should_close(window):
        current_time = time.time()
        delta_time = current_time - last_frame_time
        last_frame_time = current_time

        # Reakcja na klawiaturę
        if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(window, True)

        # Obsługa sterowania kamerą z keyboardu
        camera.process_keyboard(window, delta_time)

        # Czyszczenie buforów
        glClearColor(0.1, 0.1, 0.15, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Aktywacja shadera
        shader.use()

        # Tworzenie macierzi Widoku (View) i Projekcji (Projection)
        projection = glm.perspective(glm.radians(45.0), 1600.0 / 900.0, 0.1, 100.0)
        view = camera.get_view_matrix()

        shader.set_mat4("projection", projection)
        shader.set_mat4("view", view)

        # --- TEST FBO ---
        reflection_fbo.bind()
        print(f"Reflection Color Texture ID: {reflection_fbo.color_texture}")
        print(f"Refraction Color Texture ID: {refraction_fbo.color_texture}")
        print(f"Reflection Depth RBO ID: {reflection_fbo.depth_rbo}")
        print(f"Refraction Depth RBO ID: {refraction_fbo.depth_rbo}")
        # Tutaj rysowanie trafia do pamięci (do tekstury FBO)
        reflection_fbo.unbind(WINDOW_WIDTH, WINDOW_HEIGHT)
        # Tutaj rysowanie wraca na ekran

        # 1. Rysowanie dna stawu
        model = glm.mat4(1.0)
        shader.set_mat4("model", model)
        floor_mesh.draw()

        # 2. Rysowanie sześcianu (przesuniętego w środku sceny)
        model = glm.translate(glm.mat4(1.0), glm.vec3(0.0, 0.0, 0.0))
        shader.set_mat4("model", model)
        cube_mesh.draw()

        # 3. Rysowanie niebieskiej wody
        model = glm.mat4(1.0)
        shader.set_mat4("model", model)
        water_mesh.draw()

        glfw.swap_buffers(window)
        glfw.poll_events()

    reflection_fbo.clean_up()
    refraction_fbo.clean_up()
    glfw.terminate()

if __name__ == "__main__":
    main()