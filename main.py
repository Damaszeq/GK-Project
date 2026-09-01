import glfw
from OpenGL.GL import *
import time
import glm
from PIL import Image
import random

from terrain import Terrain
from camera import Camera
from mesh import Mesh
from shader import Shader
from framebuffer import Framebuffer
from rain import Rain
from model import Model
from particles import BubbleSystem

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900
SHADOW_WIDTH, SHADOW_HEIGHT = 2048, 2048

camera = Camera(glm.vec3(0.0, 4.0, 15.0))

def load_texture(path):
    img = Image.open(path).convert("RGBA")
    img_data = img.tobytes("raw", "RGBA", 0, -1)
    
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    glGenerateMipmap(GL_TEXTURE_2D)
    
    return tex_id

def mouse_callback(window, xpos, ypos):
    camera.process_mouse(xpos, ypos)

def render_scene(shader, terrain, sky_color, is_underwater, app_time):
    shader.use()
    shader.set_vec3("skyColor", glm.vec3(sky_color[0], sky_color[1], sky_color[2]))
    shader.set_float("isUnderwater", is_underwater)
    shader.set_float("time", app_time)
    model = glm.mat4(1.0)
    shader.set_mat4("model", model)
    terrain.draw()

def render_models(model_shader, projection, view, camera, sky_color, light_color, light_direction, plane, models_to_draw, is_underwater, app_time):
    model_shader.use()
    model_shader.set_mat4("projection", projection)
    model_shader.set_mat4("view", view)
    model_shader.set_vec4("plane", plane)
    model_shader.set_vec3("cameraPosition", camera.position)
    model_shader.set_vec3("skyColor", glm.vec3(sky_color[0], sky_color[1], sky_color[2]))
    model_shader.set_vec3("lightColor", light_color)
    model_shader.set_vec3("lightDirection", light_direction)
    model_shader.set_float("isUnderwater", is_underwater)
    model_shader.set_float("time", app_time)
    
    for obj, color, pos, scale in models_to_draw:
        mat = glm.translate(glm.mat4(1.0), pos)
        mat = glm.scale(mat, scale)
        model_shader.set_mat4("model", mat)
        obj.draw()

def render_water(water_shader, water_mesh, projection, view, camera, reflection_fbo, refraction_fbo, app_time, ripple_fbo):
    water_shader.use()
    water_shader.set_mat4("projection", projection)
    water_shader.set_mat4("view", view)
    water_shader.set_vec3("cameraPosition", camera.position)
    
    model = glm.mat4(1.0)
    water_shader.set_mat4("model", model)
    
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, reflection_fbo.color_texture)
    
    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_2D, refraction_fbo.color_texture)
    
    glActiveTexture(GL_TEXTURE4)
    glBindTexture(GL_TEXTURE_2D, refraction_fbo.depth_texture)
    
    glActiveTexture(GL_TEXTURE5)
    glBindTexture(GL_TEXTURE_2D, ripple_fbo.color_texture)
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    water_mesh.draw()
    
    glDisable(GL_BLEND)

def render_rain(rain_shader, rain, projection, view, current_time, plane):
    rain_shader.use()
    rain_shader.set_mat4("projection", projection)
    rain_shader.set_mat4("view", view)
    
    rain_shader.set_mat4("model", glm.mat4(1.0))
    rain_shader.set_vec4("plane", plane)
    
    rain_shader.set_float("time", current_time)
    rain_shader.set_float("fallSpeed", 15.0)
    rain_shader.set_vec3("windDirection", glm.vec3(-0.1, -0.6, 0.2))
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)
    
    rain.draw()
    
    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)

def render_clouds(cloud_shader, cloud_mesh, projection, view, app_time, sky_color, cloud_texture, clip_plane):
    cloud_shader.use()
    cloud_shader.set_mat4("projection", projection)
    cloud_shader.set_mat4("view", view)
    cloud_shader.set_vec4("plane", clip_plane)
    
    model = glm.translate(glm.mat4(1.0), glm.vec3(0.0, 25.0, 0.0))
    cloud_shader.set_mat4("model", model)
    
    cloud_shader.set_float("time", app_time)
    cloud_shader.set_vec3("skyColor", glm.vec3(sky_color[0], sky_color[1], sky_color[2]))
    
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, cloud_texture)
    cloud_shader.set_int("cloudTexture", 0)
    
    glDepthMask(GL_FALSE)
    cloud_mesh.draw()
    glDepthMask(GL_TRUE)

def main():
    if not glfw.init():
        raise Exception("GLFW error")
    
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.SAMPLES, 4)

    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Rendering Wody + Cienie", None, None)
    if not window:
        glfw.terminate()
        raise Exception("GLFW error")

    glfw.make_context_current(window)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CLIP_DISTANCE0)
    glEnable(GL_MULTISAMPLE)

    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    glfw.set_cursor_pos_callback(window, mouse_callback)

    # Inicjalizacja shaderów
    shader = Shader("shaders/vertex.glsl", "shaders/basic.frag")
    water_shader = Shader("shaders/water.vert", "shaders/water.frag")
    rain_shader = Shader("shaders/rain.vert", "shaders/rain.frag")
    ripple_shader = Shader("shaders/ripple.vert", "shaders/ripple.frag")
    cloud_shader = Shader("shaders/cloud.vert", "shaders/cloud.frag")
    model_shader = Shader("shaders/model.vert", "shaders/model.frag")
    shadow_shader = Shader("shaders/shadow.vert", "shaders/shadow.frag")
    particle_shader = Shader("shaders/particle.vert", "shaders/particle.frag")
    
    # SYSTEM BĄBELKÓW PODWODNYCH
    bubbles = BubbleSystem(count=50)
    
    # SHADOW MAP FBO
    depthMapFBO = glGenFramebuffers(1)
    depthMap = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, depthMap)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, SHADOW_WIDTH, SHADOW_HEIGHT, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
    borderColor = [1.0, 1.0, 1.0, 1.0]
    glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, borderColor)

    glBindFramebuffer(GL_FRAMEBUFFER, depthMapFBO)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, depthMap, 0)
    glDrawBuffer(GL_NONE)
    glReadBuffer(GL_NONE)
    glBindFramebuffer(GL_FRAMEBUFFER, 0)

    # Wczytanie modeli
    rock_model = Model("models/Obj/stone_largeA.obj")
    plant_model = Model("models/Obj/plant_bush.obj")
    plant2_model = Model("models/Obj/plant_flatTall.obj")
    
    tree_model1 = Model("models/Obj/tree_detailed.obj")
    tree_model2 = Model("models/Obj/tree_pineDefaultA.obj")
    mushroom_red = Model("models/Obj/mushroom_redGroup.obj")
    mushroom_tan = Model("models/Obj/mushroom_tanGroup.obj")
    grass_model = Model("models/Obj/grass_large.obj")
    stone_small = Model("models/Obj/stone_smallA.obj")
    
    dummy_color = glm.vec3(1.0)
    
    TERRAIN_SIZE = 60.0
    HALF_SIZE = TERRAIN_SIZE / 2.0
    terrain = Terrain("textures/heightmap.png", size=TERRAIN_SIZE, max_height=8.0, min_height=-0.8)
    
    # Generowanie losowych pozycji modeli
    random.seed(123)
    models_to_draw = []
    
    attempts = 0
    # Generowanie modeli pod wodą
    while len(models_to_draw) < 400 and attempts < 2000:
        attempts += 1
        x = random.uniform(-25.0, 25.0)
        z = random.uniform(-25.0, 25.0)
        
        terrain_y = terrain.get_height(x, z)
        scale = random.uniform(0.4, 0.75)
        
        if terrain_y + scale < -0.1:
            y = terrain_y
            rand_val = random.random()
            if rand_val < 0.20:
                models_to_draw.append((rock_model, dummy_color, glm.vec3(x, y, z), glm.vec3(scale)))
            elif rand_val < 0.60:
                models_to_draw.append((plant_model, dummy_color, glm.vec3(x, y, z), glm.vec3(scale)))
            else:
                models_to_draw.append((plant2_model, dummy_color, glm.vec3(x, y, z), glm.vec3(scale)))
                
    attempts = 0
    nature_placed = 0

    # Generowanie modeli nad wodą
    while attempts < 3000 and nature_placed < 200:
        attempts += 1
        x = random.uniform(-25.0, 25.0)
        z = random.uniform(-25.0, 25.0)
        terrain_y = terrain.get_height(x, z)
        
        if 0.2 < terrain_y < 4.5:
            rand_val = random.random()
            if rand_val < 0.3:
                scale = random.uniform(1.2, 2.8)
                t_model = tree_model1 if random.random() > 0.5 else tree_model2
                models_to_draw.append((t_model, dummy_color, glm.vec3(x, terrain_y, z), glm.vec3(scale)))
            elif rand_val < 0.6:
                scale = random.uniform(0.6, 1.2)
                models_to_draw.append((grass_model, dummy_color, glm.vec3(x, terrain_y, z), glm.vec3(scale)))
            elif rand_val < 0.8:
                scale = random.uniform(0.4, 1.0)
                models_to_draw.append((stone_small, dummy_color, glm.vec3(x, terrain_y, z), glm.vec3(scale)))
            else:
                scale = random.uniform(0.3, 0.7)
                m_model = mushroom_red if random.random() > 0.5 else mushroom_tan
                models_to_draw.append((m_model, dummy_color, glm.vec3(x, terrain_y, z), glm.vec3(scale)))
                
            nature_placed += 1


    # Inicjalizacja deszczu
    rain = Rain(num_drops=1500, bounds=(-HALF_SIZE, HALF_SIZE, 0, 40, -HALF_SIZE, HALF_SIZE))

    # Inicjalizacja shaderów wody
    water_shader.use()
    water_shader.set_int("reflectionTexture", 0)
    water_shader.set_int("refractionTexture", 1)
    water_shader.set_int("depthMap", 4)
    water_shader.set_int("rippleMap", 5)
    
    cloud_texture = load_texture("textures/clouds.jpg")
    
    light_direction = glm.normalize(glm.vec3(-0.2, -1.0, -0.1))
    light_color = glm.vec3(0.6, 0.65, 0.7)

    # Generowanie wierzchołków dla powietrza i wody
    water_vertices = [
        -HALF_SIZE, 0.0, -HALF_SIZE,  0.0, 0.0, 0.0,
        -HALF_SIZE, 0.0,  HALF_SIZE,  0.0, 0.0, 0.0,
         HALF_SIZE, 0.0, -HALF_SIZE,  0.0, 0.0, 0.0,
         HALF_SIZE, 0.0, -HALF_SIZE,  0.0, 0.0, 0.0,
        -HALF_SIZE, 0.0,  HALF_SIZE,  0.0, 0.0, 0.0,
         HALF_SIZE, 0.0,  HALF_SIZE,  0.0, 0.0, 0.0,
    ]
    water_mesh = Mesh(water_vertices)

    CLOUD_SIZE = 120.0
    cloud_vertices = [
        -CLOUD_SIZE, 0.0, -CLOUD_SIZE,  1.0, 1.0, 1.0,
        -CLOUD_SIZE, 0.0,  CLOUD_SIZE,  1.0, 1.0, 1.0,
         CLOUD_SIZE, 0.0, -CLOUD_SIZE,  1.0, 1.0, 1.0,
         CLOUD_SIZE, 0.0, -CLOUD_SIZE,  1.0, 1.0, 1.0,
        -CLOUD_SIZE, 0.0,  CLOUD_SIZE,  1.0, 1.0, 1.0,
         CLOUD_SIZE, 0.0,  CLOUD_SIZE,  1.0, 1.0, 1.0,
    ]
    cloud_mesh = Mesh(cloud_vertices)

    # Inicjalizacja buforów dla odbicia, załamania i falowania
    reflection_fbo = Framebuffer(WINDOW_WIDTH, WINDOW_HEIGHT)
    refraction_fbo = Framebuffer(WINDOW_WIDTH, WINDOW_HEIGHT)
    ripple_fbo = Framebuffer(512, 512)

    start_time = time.time()
    last_frame_time = start_time

    sky_color = (0.48, 0.52, 0.58, 1.0)

    # Główna pętla renderowania
    while not glfw.window_should_close(window):
        current_time = time.time()
        delta_time = current_time - last_frame_time
        last_frame_time = current_time
        app_time = current_time - start_time

        if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(window, True)

        camera.process_keyboard(window, delta_time)

        # Flaga zanurzenia pod wodą (poziom wody y = 0.0)
        is_underwater = 1.0 if camera.position.y < 0.0 else 0.0

        # Aktualizacja pozycji bąbelków
        bubbles.update(delta_time, camera.position)

        # Macierz rzutowania światła (Shadow Pass Matrix)
        lightProjection = glm.ortho(-40.0, 40.0, -40.0, 40.0, 1.0, 75.0)
        lightView = glm.lookAt(-light_direction * 30.0, glm.vec3(0.0), glm.vec3(0.0, 1.0, 0.0))
        lightSpaceMatrix = lightProjection * lightView

        # PASS -1: Shadow Map Pass
        shadow_shader.use()
        shadow_shader.set_mat4("lightSpaceMatrix", lightSpaceMatrix)
        glViewport(0, 0, SHADOW_WIDTH, SHADOW_HEIGHT)
        glBindFramebuffer(GL_FRAMEBUFFER, depthMapFBO)
        glClear(GL_DEPTH_BUFFER_BIT)
        
        shadow_shader.set_mat4("model", glm.mat4(1.0))
        terrain.draw()
        for obj, color, pos, scale in models_to_draw:
            mat = glm.translate(glm.mat4(1.0), pos)
            mat = glm.scale(mat, scale)
            shadow_shader.set_mat4("model", mat)
            obj.draw()
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        # Przekazanie macierzy światła i tekstury cieni do shadera terenu
        shader.use()
        projection = glm.perspective(glm.radians(45.0), WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 1000.0)
        shader.set_mat4("projection", projection)
        shader.set_mat4("lightSpaceMatrix", lightSpaceMatrix)
        glActiveTexture(GL_TEXTURE3)
        glBindTexture(GL_TEXTURE_2D, depthMap)
        shader.set_int("shadowMap", 3)

        # PASS 0: Ripple Map (bufor 512x512)
        ripple_fbo.bind()
        glViewport(0, 0, 512, 512)
        glClearColor(0.48, 0.52, 0.58, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glEnable(GL_PROGRAM_POINT_SIZE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_ONE, GL_ONE)
        glDepthMask(GL_FALSE)
        glDisable(GL_DEPTH_TEST)
        
        ripple_shader.use()
        ripple_shader.set_float("time", app_time)
        ripple_shader.set_float("fallSpeed", 15.0)
        rain.draw_points()
        
        glDisable(GL_PROGRAM_POINT_SIZE)
        glDisable(GL_BLEND)
        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)

        # PASS 1: Odbicie
        reflection_fbo.bind()
        glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        glClearColor(*sky_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        view_reflection = camera.get_reflection_view_matrix(water_height=0.0)
        reflection_plane = glm.vec4(0.0, 1.0, 0.0, -0.05)

        render_clouds(cloud_shader, cloud_mesh, projection, view_reflection, app_time, sky_color, cloud_texture, reflection_plane)

        shader.use()
        shader.set_vec4("plane", reflection_plane)
        shader.set_mat4("view", view_reflection)
        shader.set_vec3("viewPos", camera.position)

        render_scene(shader, terrain, sky_color, is_underwater, app_time)
        render_models(model_shader, projection, view_reflection, camera, sky_color, light_color, light_direction, reflection_plane, models_to_draw, is_underwater, app_time)

        # PASS 2: Załamanie
        refraction_fbo.bind()
        glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        glClearColor(*sky_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        shader.use()
        view_normal = camera.get_view_matrix()
        refraction_plane = glm.vec4(0.0, -1.0, 0.0, 0.05)

        shader.set_mat4("view", view_normal)
        shader.set_vec4("plane", refraction_plane)
        shader.set_vec3("viewPos", camera.position)
        
        render_scene(shader, terrain, sky_color, is_underwater, app_time)
        render_models(model_shader, projection, view_normal, camera, sky_color, light_color, light_direction, refraction_plane, models_to_draw, is_underwater, app_time)

        # PASS 3: Renderowanie na EKRAN
        reflection_fbo.unbind(WINDOW_WIDTH, WINDOW_HEIGHT)
        glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        glClearColor(*sky_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        screen_plane = glm.vec4(0.0, 0.0, 0.0, 0.0)
        render_clouds(cloud_shader, cloud_mesh, projection, view_normal, app_time, sky_color, cloud_texture, screen_plane)

        shader.use()
        shader.set_mat4("view", view_normal)
        shader.set_vec4("plane", screen_plane)
        shader.set_vec3("viewPos", camera.position)

        render_scene(shader, terrain, sky_color, is_underwater, app_time)
        render_models(model_shader, projection, view_normal, camera, sky_color, light_color, light_direction, screen_plane, models_to_draw, is_underwater, app_time)

        render_water(
            water_shader, water_mesh, projection, view_normal, camera,
            reflection_fbo, refraction_fbo,
            app_time, ripple_fbo
        )
        
        render_rain(rain_shader, rain, projection, view_normal, app_time, screen_plane)
        
        # Rysowanie bąbelków widocznych tylko pod wodą
        bubbles.draw(particle_shader, projection, view_normal, is_underwater)

        glfw.swap_buffers(window)
        glfw.poll_events()

    reflection_fbo.clean_up()
    refraction_fbo.clean_up()
    glfw.terminate()

if __name__ == "__main__":
    main()