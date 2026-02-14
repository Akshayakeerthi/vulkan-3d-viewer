from pyrr import Vector3, vector, vector3, matrix44
from math import sin, cos, radians
from AddOns import glm
import numpy as np

class Camera:
    
    def __init__(self):
        
        self.camera_pos = Vector3([0.0, 0.0, 1.0])
        self.camera_front = Vector3([1.0, 0.0, 0.0])
        self.camera_up = Vector3([0.0, 1.0, 0.0])
        self.camera_right = Vector3([0.0, 0.0, 0.0])
        
        self.mouse_sensitivity = 0.20
        self.jaw = -90
        self.pitch = 0
        
        #self.model = glm.rotate(np.identity(4, np.float32), 90.0, 0.0, 0.0, 1.0)
        self.proj = glm.perspective(-45.0, float(1020) / 700, 0.1, 10.0 ** 5)
        self.update_camera_vectors()
        
    def updateCamProj(self, w, h):
        self.proj = glm.perspective(-45.0, float(w) / h, 0.1, 10.0 ** 5)
        self.dta = np.concatenate((
                np.array(self.view).flatten(order='C'),
                np.array(self.proj).flatten(order='C')
        ))
        
        self.size = 128
        
    def updateCamView(self):
        
        self.view = glm.lookAt(np.array(self.camera_pos, np.float32), np.array(self.camera_pos + self.camera_front, np.float32), np.array(self.camera_up, np.float32))#matrix44.create_look_at(self.camera_pos, self.camera_pos + self.camera_front, self.camera_up)
        self.dta = np.concatenate((
                np.array(self.view).flatten(order='C'),
                np.array(self.proj).flatten(order='C'),
        ))
        
        self.size = 128
        
    def process_mouse_movement(self, xoffset, yoffset, constrain_pitch=True):
        
        xoffset *= self.mouse_sensitivity
        yoffset *= self.mouse_sensitivity
        
        self.jaw += xoffset
        self.pitch += yoffset
        
        if constrain_pitch:
            
            if self.pitch > 45:
                self.pitch = 45
            
            if self.pitch < -45:
                self.pitch = -45
        
        self.update_camera_vectors()
        
    def update_camera_vectors(self):
        
        front = Vector3([0.0, 0.0, 0.0])
        front.x = cos(radians(self.jaw)) * cos(radians(self.pitch))
        front.y = sin(radians(self.pitch))
        front.z = sin(radians(self.jaw)) * cos(radians(self.pitch))
        
        self.camera_front = vector.normalise(front)
        self.camera_right = vector.normalise(vector3.cross(self.camera_front, Vector3([0.0, 1.0, 0.0])))
        self.camera_up = vector.normalise(vector3.cross(self.camera_right, self.camera_front))
        
        self.updateCamView()
        
    # Camera method for the WASD movement
    def process_keyboard(self, direction, velocity):
        
        if direction == "FORWARD":
            self.camera_pos += self.camera_front * velocity
        
        elif direction == "BACKWARD":
            self.camera_pos -= self.camera_front * velocity
        
        elif direction == "LEFT":
            self.camera_pos -= self.camera_right * velocity
        
        elif direction == "RIGHT":
            self.camera_pos += self.camera_right * velocity
        
        elif direction == "DOWN":
            self.camera_pos -= self.camera_up * velocity
        
        elif direction == "UP":
            self.camera_pos += self.camera_up * velocity

        self.updateCamView()