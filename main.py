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

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900

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

def render_scene(shader, terrain):
    model = glm.mat4(1.0)
    shader.set_mat4("model", model)
    terrain.draw()

def render_models(model_shader, projection, view, camera, sky_color, light_color, light_direction, plane, models_to_draw):
    model_shader.use()
    model_shader.set_mat4("projection", projection)
    model_shader.set_mat4("view", view)
    model_shader.set_vec4("plane", plane)
    model_shader.set_vec3("cameraPosition", camera.position)
    model_shader.set_vec3("skyColor", glm.vec3(sky_color[0], sky_color[1], sky_color[2]))
    model_shader.set_vec3("lightColor", light_color)
    model_shader.set_vec3("lightDirection", light_direction)
    
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
    
    # Przesuwamy chmury wysoko na niebo (Y = 25.0)
    model = glm.translate(glm.mat4(1.0), glm.vec3(0.0, 25.0, 0.0))
    cloud_shader.set_mat4("model", model)
    
    # Zabezpieczenie przed ucięciem
    # Nie ustawiamy zmiennej "plane" w shaderze chmur, ale chmury są zawsze nad wodą (Y=25.0).
    
    cloud_shader.set_float("time", app_time)
    cloud_shader.set_vec3("skyColor", glm.vec3(sky_color[0], sky_color[1], sky_color[2]))
    
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, cloud_texture)
    cloud_shader.set_int("cloudTexture", 0)
    
    # Disable depth writing so clouds act strictly as a sky background
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

    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Rendering Wody", None, None)
    if not window:
        glfw.terminate()
        raise Exception("GLFW error")

    glfw.make_context_current(window)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CLIP_DISTANCE0)
    glEnable(GL_MULTISAMPLE)

    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    glfw.set_cursor_pos_callback(window, mouse_callback)

    shader = Shader("shaders/vertex.glsl", "shaders/basic.frag")
    water_shader = Shader("shaders/water.vert", "shaders/water.frag")
    rain_shader = Shader("shaders/rain.vert", "shaders/rain.frag")
    ripple_shader = Shader("shaders/ripple.vert", "shaders/ripple.frag")
    cloud_shader = Shader("shaders/cloud.vert", "shaders/cloud.frag")
    model_shader = Shader("shaders/model.vert", "shaders/model.frag")
    
    # Load Models (colors are handled automatically by MTL)
    rock_model = Model("models/Obj/stone_largeA.obj")
    plant_model = Model("models/Obj/plant_bush.obj")
    plant2_model = Model("models/Obj/plant_flatTall.obj")
    
    # Shoreline nature assets
    tree_model1 = Model("models/Obj/tree_detailed.obj")
    tree_model2 = Model("models/Obj/tree_pineDefaultA.obj")
    mushroom_red = Model("models/Obj/mushroom_redGroup.obj")
    mushroom_tan = Model("models/Obj/mushroom_tanGroup.obj")
    grass_model = Model("models/Obj/grass_large.obj")
    stone_small = Model("models/Obj/stone_smallA.obj")
    
    # We will pass a dummy color vec3(1.0) because model shader ignores it
    dummy_color = glm.vec3(1.0)
    
    TERRAIN_SIZE = 60.0
    HALF_SIZE = TERRAIN_SIZE / 2.0
    terrain = Terrain("textures/heightmap.png", size=TERRAIN_SIZE, max_height=8.0, min_height=-0.8)
    
    random.seed(123)
    models_to_draw = []
    
    # We will generate 400 objects, mostly plants
    attempts = 0
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
                
    # Shoreline nature
    attempts = 0
    nature_placed = 0
    while attempts < 3000 and nature_placed < 200:
        attempts += 1
        x = random.uniform(-25.0, 25.0)
        z = random.uniform(-25.0, 25.0)
        terrain_y = terrain.get_height(x, z)
        
        # Place only on land
        if 0.2 < terrain_y < 4.5:
            rand_val = random.random()
            if rand_val < 0.3:
                # 30% chance for trees
                scale = random.uniform(1.2, 2.8)
                t_model = tree_model1 if random.random() > 0.5 else tree_model2
                models_to_draw.append((t_model, dummy_color, glm.vec3(x, terrain_y, z), glm.vec3(scale)))
            elif rand_val < 0.6:
                # 30% chance for grass
                scale = random.uniform(0.6, 1.2)
                models_to_draw.append((grass_model, dummy_color, glm.vec3(x, terrain_y, z), glm.vec3(scale)))
            elif rand_val < 0.8:
                # 20% chance for small stones
                scale = random.uniform(0.4, 1.0)
                models_to_draw.append((stone_small, dummy_color, glm.vec3(x, terrain_y, z), glm.vec3(scale)))
            else:
                # 20% chance for mushrooms
                scale = random.uniform(0.3, 0.7)
                m_model = mushroom_red if random.random() > 0.5 else mushroom_tan
                models_to_draw.append((m_model, dummy_color, glm.vec3(x, terrain_y, z), glm.vec3(scale)))
                
            nature_placed += 1

    rain = Rain(num_drops=1500, bounds=(-HALF_SIZE, HALF_SIZE, 0, 40, -HALF_SIZE, HALF_SIZE))
    
    water_shader.use()
    water_shader.set_int("reflectionTexture", 0)
    water_shader.set_int("refractionTexture", 1)
    water_shader.set_int("depthMap", 4)
    water_shader.set_int("rippleMap", 5)
    
    cloud_texture = load_texture("textures/clouds.jpg")
    
    light_color = glm.vec3(1.0, 0.98, 0.9)
    light_direction = glm.normalize(glm.vec3(0.0, -1.0, 0.5))

    water_vertices = [
        -HALF_SIZE, 0.0, -HALF_SIZE,  0.0, 0.0, 0.0,
        -HALF_SIZE, 0.0,  HALF_SIZE,  0.0, 0.0, 0.0,
         HALF_SIZE, 0.0, -HALF_SIZE,  0.0, 0.0, 0.0,
         HALF_SIZE, 0.0, -HALF_SIZE,  0.0, 0.0, 0.0,
        -HALF_SIZE, 0.0,  HALF_SIZE,  0.0, 0.0, 0.0,
         HALF_SIZE, 0.0,  HALF_SIZE,  0.0, 0.0, 0.0,
    ]
    water_mesh = Mesh(water_vertices)

    CLOUD_SIZE = 1000.0
    cloud_vertices = [
        -CLOUD_SIZE, 0.0, -CLOUD_SIZE,  1.0, 1.0, 1.0,
        -CLOUD_SIZE, 0.0,  CLOUD_SIZE,  1.0, 1.0, 1.0,
         CLOUD_SIZE, 0.0, -CLOUD_SIZE,  1.0, 1.0, 1.0,
         CLOUD_SIZE, 0.0, -CLOUD_SIZE,  1.0, 1.0, 1.0,
        -CLOUD_SIZE, 0.0,  CLOUD_SIZE,  1.0, 1.0, 1.0,
         CLOUD_SIZE, 0.0,  CLOUD_SIZE,  1.0, 1.0, 1.0,
    ]
    cloud_mesh = Mesh(cloud_vertices)

    reflection_fbo = Framebuffer(WINDOW_WIDTH, WINDOW_HEIGHT)
    refraction_fbo = Framebuffer(WINDOW_WIDTH, WINDOW_HEIGHT)
    ripple_fbo = Framebuffer(512, 512)

    start_time = time.time()
    last_frame_time = start_time

    sky_color = (0.45, 0.68, 0.9, 1.0)

    while not glfw.window_should_close(window):
        current_time = time.time()
        delta_time = current_time - last_frame_time
        last_frame_time = current_time
        app_time = current_time - start_time

        if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(window, True)

        camera.process_keyboard(window, delta_time)

        shader.use()
        projection = glm.perspective(glm.radians(45.0), WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 1000.0)
        shader.set_mat4("projection", projection)

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

# PASS 1: Odbicie (Reflection Pass)
        reflection_fbo.bind()
        glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        glClearColor(*sky_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        view_reflection = camera.get_reflection_view_matrix(water_height=0.0)
        render_clouds(cloud_shader, cloud_mesh, projection, view_reflection, app_time, sky_color, cloud_texture, glm.vec4(0,1,0,0))

        shader.use()
        # ZACHOWUJEMY GEOMETRIĘ NAD WODĄ (Y >= 0.0)
        shader.set_vec4("plane", glm.vec4(0.0, 1.0, 0.0, -0.05))
        shader.set_mat4("view", view_reflection)

        render_scene(shader, terrain)
        render_models(model_shader, projection, view_reflection, camera, sky_color, light_color, light_direction, glm.vec4(0.0, 1.0, 0.0, -0.05), models_to_draw)
        render_rain(rain_shader, rain, projection, view_reflection, app_time, glm.vec4(0.0, 1.0, 0.0, -0.05))

        # PASS 2: Załamanie (Refraction Pass)
        refraction_fbo.bind()
        glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        glClearColor(*sky_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        shader.use()
        view_normal = camera.get_view_matrix()
        shader.set_mat4("view", view_normal)
        # ZACHOWUJEMY GEOMETRIĘ POD WODĄ (Y <= 0.0)
        shader.set_vec4("plane", glm.vec4(0.0, -1.0, 0.0, 0.05))
        render_scene(shader, terrain)
        render_models(model_shader, projection, view_normal, camera, sky_color, light_color, light_direction, glm.vec4(0.0, -1.0, 0.0, 0.05), models_to_draw)

        # PASS 3: Renderowanie na EKRAN
        reflection_fbo.unbind(WINDOW_WIDTH, WINDOW_HEIGHT)
        glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        glClearColor(*sky_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        render_clouds(cloud_shader, cloud_mesh, projection, view_normal, app_time, sky_color, cloud_texture, glm.vec4(0,1,0,0))

        shader.use()
        shader.set_mat4("view", view_normal)
        shader.set_vec4("plane", glm.vec4(0.0, 0.0, 0.0, 0.0))
        render_scene(shader, terrain)
        render_models(model_shader, projection, view_normal, camera, sky_color, light_color, light_direction, glm.vec4(0.0, 0.0, 0.0, 0.0), models_to_draw)

        render_water(
            water_shader, water_mesh, projection, view_normal, camera,
            reflection_fbo, refraction_fbo,
            app_time, ripple_fbo
        )
        
        render_rain(rain_shader, rain, projection, view_normal, app_time, glm.vec4(0.0, 0.0, 0.0, 0.0))

        glfw.swap_buffers(window)
        glfw.poll_events()

    reflection_fbo.clean_up()
    refraction_fbo.clean_up()
    glfw.terminate()

if __name__ == "__main__":
    main()