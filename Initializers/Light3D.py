#from AddOns import glm
import numpy as np
import pyrr

class Light:
    
    def __init__(self, name = 'point'):
        
        self.trans = pyrr.matrix44.create_from_translation([0, 0, 0])
        self.pix = np.array([0, 0], np.float32)
        
        if name == 'point':
            self.pointLight()
        elif name == 'directional':
            self.directionalLight()
        
    def pointLight(self):
        
        self.light = 'point'
                                 #x, y, z, w
        self.position = np.array([1, 1, 1, 0], dtype = np.float32)
                              #r, g, b, i
        self.color = np.array([1, 1, 1, 1], dtype = np.float32)
        
    def directionalLight(self):
        
        self.light = 'directional'
                                 #x, y, z, w
        self.position = np.array([1, 1, 1, 1], dtype = np.float32)
                              #r, g, b, i
        self.color = np.array([1, 1, 1, 1], dtype = np.float32)