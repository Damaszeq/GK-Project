import glfw
from OpenGL.GL import *
import time
import glm
from terrain import Terrain

from camera import Camera
from mesh import Mesh
from shader import Shader
from framebuffer import Framebuffer

# Instancja kamery
camera = Camera(glm.vec3(0.0, 2.0, 8.0))

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900

def mouse_callback(window, xpos, ypos):
    camera.process_mouse(xpos, ypos)

def render_scene(shader, terrain, cube_mesh):
    model = glm.mat4(1.0)
    shader.set_mat4("model", model)
    terrain.draw()  # Rysujemy trójwymiarowy teren zamiast płaskiego kwadratu

    model = glm.translate(glm.mat4(1.0), glm.vec3(0.0, 0.0, 0.0))
    shader.set_mat4("model", model)
    cube_mesh.draw()

def main():
    if not glfw.init():
        raise Exception("GLFW error")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Rendering Wody - Faza 2 Completo (3 Passy)", None, None)
    if not window:
        glfw.terminate()
        raise Exception("GLFW error")

    glfw.make_context_current(window)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CLIP_DISTANCE0)

    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    glfw.set_cursor_pos_callback(window, mouse_callback)

    # 1. Wczytanie Shadera
    shader = Shader("shaders/vertex.glsl", "shaders/basic.frag")

    # 2. Geometria
    terrain = Terrain("textures/heightmap.png", size=40.0, max_height=4.0, min_height=-1.5)

    water_vertices = [
        -20.0, 0.0, -20.0,   0.0, 0.4, 0.8,
        20.0, 0.0, -20.0,   0.0, 0.4, 0.8,
        20.0, 0.0,  20.0,   0.0, 0.4, 0.8,
        -20.0, 0.0, -20.0,   0.0, 0.4, 0.8,
        20.0, 0.0,  20.0,   0.0, 0.4, 0.8,
        -20.0, 0.0,  20.0,   0.0, 0.4, 0.8,
    ]
    water_mesh = Mesh(water_vertices)

    cube_vertices = [
        -0.5, -1.0,  0.5,  0.8, 0.1, 0.1,
         0.5, -1.0,  0.5,  0.8, 0.1, 0.1,
         0.5,  1.0,  0.5,  0.8, 0.1, 0.1,
        -0.5, -1.0,  0.5,  0.8, 0.1, 0.1,
         0.5,  1.0,  0.5,  0.8, 0.1, 0.1,
        -0.5,  1.0,  0.5,  0.8, 0.1, 0.1,
        
        -0.5, -1.0, -0.5,  0.8, 0.1, 0.1,
         0.5,  1.0, -0.5,  0.8, 0.1, 0.1,
         0.5, -1.0, -0.5,  0.8, 0.1, 0.1,
        -0.5, -1.0, -0.5,  0.8, 0.1, 0.1,
        -0.5,  1.0, -0.5,  0.8, 0.1, 0.1,
         0.5,  1.0, -0.5,  0.8, 0.1, 0.1,
    ]
    cube_mesh = Mesh(cube_vertices)

    # Bufory klatek dla odbicia i załamania
    reflection_fbo = Framebuffer(WINDOW_WIDTH, WINDOW_HEIGHT)
    refraction_fbo = Framebuffer(WINDOW_WIDTH, WINDOW_HEIGHT)

    last_frame_time = time.time()

    # Pętla główna
    while not glfw.window_should_close(window):
        current_time = time.time()
        delta_time = current_time - last_frame_time
        last_frame_time = current_time

        if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(window, True)

        camera.process_keyboard(window, delta_time)

        shader.use()
        projection = glm.perspective(glm.radians(45.0), WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 100.0)
        shader.set_mat4("projection", projection)

        # =========================================================
        # PASS 1: Renderowanie Odbicia (Reflection Pass -> FBO)
        # =========================================================
        reflection_fbo.bind()
        glClearColor(0.1, 0.1, 0.15, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Kamera odbita + Obcinanie obiektów poniżej tafli (y < 0)
        view_reflection = camera.get_reflection_view_matrix()
        shader.set_mat4("view", view_reflection)
        shader.set_vec4("plane", glm.vec4(0.0, 1.0, 0.0, 0.0))

        render_scene(shader, terrain, cube_mesh)

        # =========================================================
        # PASS 2: Renderowanie Załamania (Refraction Pass -> FBO)
        # =========================================================
        refraction_fbo.bind()
        glClearColor(0.1, 0.1, 0.15, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Kamera zwykła + Obcinanie obiektów powyżej tafli (y > 0)
        view_normal = camera.get_view_matrix()
        shader.set_mat4("view", view_normal)
        shader.set_vec4("plane", glm.vec4(0.0, -1.0, 0.0, 0.0))

        render_scene(shader, terrain, cube_mesh)

        # =========================================================
        # PASS 3: Renderowanie na EKRAN (Default Framebuffer)
        # =========================================================
        reflection_fbo.unbind(WINDOW_WIDTH, WINDOW_HEIGHT)
        glClearColor(0.1, 0.1, 0.15, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Kamera zwykła + Brak obcinania
        shader.set_mat4("view", view_normal)
        shader.set_vec4("plane", glm.vec4(0.0, 0.0, 0.0, 0.0))

        # Rysujemy pełny świat
        render_scene(shader, terrain, cube_mesh)

        # Rysujemy taflę wody
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