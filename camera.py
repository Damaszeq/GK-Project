import glm
import glfw

class Camera:
    def __init__(self, position=glm.vec3(0.0, 2.0, 5.0)):
        self.position = position
        self.front = glm.vec3(0.0, 0.0, -1.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)
        self.right = glm.vec3(1.0, 0.0, 0.0)
        
        self.yaw = -90.0
        self.pitch = 0.0
        self.speed = 4.0
        self.sensitivity = 0.1
        self.first_mouse = True
        self.last_x = 640.0
        self.last_y = 360.0

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.position + self.front, self.up)

    def get_reflection_view_matrix(self, water_height=0.0):
        # 1. Odwracamy pozycję kamery względem wysokości wody (2 * water_height - Y)
        ref_position = glm.vec3(
            self.position.x,
            2.0 * water_height - self.position.y,
            self.position.z
        )
        
        # 2. Odwracamy składową Y kierunku patrzenia
        ref_front = glm.vec3(
            self.front.x,
            -self.front.y,
            self.front.z
        )
        
        # 3. Zwracamy macierz odbitą
        return glm.lookAt(ref_position, ref_position + ref_front, self.up)

    def process_keyboard(self, window, delta_time):
        velocity = self.speed * delta_time
        if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
            self.position += self.front * velocity
        if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
            self.position -= self.front * velocity
        if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
            self.position -= glm.normalize(glm.cross(self.front, self.up)) * velocity
        if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
            self.position += glm.normalize(glm.cross(self.front, self.up)) * velocity

    def process_mouse(self, xpos, ypos):
        if self.first_mouse:
            self.last_x = xpos
            self.last_y = ypos
            self.first_mouse = False

        xoffset = (xpos - self.last_x) * self.sensitivity
        yoffset = (self.last_y - ypos) * self.sensitivity
        self.last_x = xpos
        self.last_y = ypos

        self.yaw += xoffset
        self.pitch += yoffset

        if self.pitch > 89.0: self.pitch = 89.0
        if self.pitch < -89.0: self.pitch = -89.0

        front = glm.vec3()
        front.x = glm.cos(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        front.y = glm.sin(glm.radians(self.pitch))
        front.z = glm.sin(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        self.front = glm.normalize(front)