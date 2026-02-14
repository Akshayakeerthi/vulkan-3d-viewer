from AddOns import tinyobjloader as tol
from Initializers.AddTexture import Textures
from Initializers.Descriptor import *
from Initializers.copyops import *
from AddOns import glm
import pyrr
import numpy as np

class createDescriptor:
    def __init__(self, swap_len, ptypes, device, physicalDevice, descriptorSetLayout):
        self.ubo = UniformBufferObject()
        self.uniformBuffer, self.uniformBufferMemory = createUniformBuffer(self.ubo, device, physicalDevice)
        self.descriptorPool = createDescriptorPool(device, ptypes)
        self.descriptorSet = createDescriptorSet(device, 3, self.descriptorPool, descriptorSetLayout)
        
    def update(self, device, ptypes):
        updateDescriptorSet(device, 3, ptypes, self.descriptorSet)

class Model:
    
    def __init__(self, device, physicalDevice, graphicQueue, commandPool, path = None):
        
        self.device, self.physicalDevice = device, physicalDevice
        self.graphicQueue, self.commandPool = graphicQueue, commandPool
        self.textureImage, self.textureImageMemory = VK_NULL_HANDLE, VK_NULL_HANDLE
        self.textureImageView, self.textureSampler = VK_NULL_HANDLE, VK_FALSE
        
        self.descriptors = {}
        
        #startTime = time.time()
        reader = tol.ObjReader()
        model = reader.ParseFromFile(path)
        attrib = reader.GetAttrib()
        
        vertices = attrib.vertices
        normals = attrib.normals
        texcoords = attrib.texcoords
        shapes = reader.GetShapes()
        uniqueVertices = {}
        vertexData = []
        vertexDataOP = []
        indexData = []
        indexDataOP = []
        
        for shape in shapes:
            allIndices = shape.mesh.indices
            
            for index in shape.mesh.indices:
                data = (
                    # vertex position
                    vertices[3 * index.vertex_index + 0],
                    vertices[3 * index.vertex_index + 1],
                    vertices[3 * index.vertex_index + 2],
                
                    # color
                    1.0, 1.0, 1.0,
                    
                    # normal
                    normals[3 * index.normal_index + 0],
                    normals[3 * index.normal_index + 1],
                    normals[3 * index.normal_index + 2],
                    
                    # texture
                    texcoords[2 * index.texcoord_index + 0],
                    texcoords[2 * index.texcoord_index + 1]
                )
                
                if data not in uniqueVertices:
                    uniqueVertices[data] = len(vertexData)
                    vertexData.append(data)
                    
                indexData.append(uniqueVertices[data])
                
        #useTime = time.time() - startTime
        #print('Model loading time: {} s'.format(useTime))
        self.vertices = np.array(vertexData, np.float32)
        self.indices = np.array(indexData, np.uint32)
        
        self.createVertexBuffer()
        self.createIndexBuffer()
        
    def addTexture(self, device, commandPool, graphicQueue, physicalDevice, texturePath):
        
        self.textureImage, self.textureImageMemory, self.textureImageView, self.textureSampler = Textures(device, commandPool,
                                                                                                          graphicQueue, physicalDevice,
                                                                                                          texturePath)
        
    def createVertexBuffer(self):
        
        bufferSize = self.vertices.nbytes
        
        stagingBuffer, stagingMemory = createBuffer(bufferSize, VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
                                                    VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
                                                    self.device, self.physicalDevice )
        
        data = vkMapMemory(self.device, stagingMemory, 0, bufferSize, 0)
        vertePtr = ffi.cast('float *', self.vertices.ctypes.data)
        ffi.memmove(data, vertePtr, bufferSize)
        vkUnmapMemory(self.device, stagingMemory)
        
        self.vertexBuffer, self.vertexBufferMemory = createBuffer(bufferSize,
                                                                  VK_BUFFER_USAGE_TRANSFER_DST_BIT |VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
                                                                  VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, self.device, self.physicalDevice)
        copyBuffer(stagingBuffer, self.vertexBuffer, bufferSize, self.device, self.commandPool, self.graphicQueue)
        
        vkDestroyBuffer(self.device, stagingBuffer, None)
        vkFreeMemory(self.device, stagingMemory, None)
        
    def createIndexBuffer(self):
        
        bufferSize = self.indices.nbytes
        
        stagingBuffer, stagingMemory = createBuffer(bufferSize, VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
                                                    VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
                                                    self.device, self.physicalDevice)
        data = vkMapMemory(self.device, stagingMemory, 0, bufferSize, 0)
        
        indicesPtr = ffi.cast('uint16_t*', self.indices.ctypes.data)
        ffi.memmove(data, indicesPtr, bufferSize)
        
        vkUnmapMemory(self.device, stagingMemory)
        
        self.indexBuffer, self.indexBufferMemory = createBuffer(bufferSize,
                                                                VK_BUFFER_USAGE_TRANSFER_DST_BIT | VK_BUFFER_USAGE_INDEX_BUFFER_BIT,
                                                                VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, self.device, self.physicalDevice)
        
        copyBuffer(stagingBuffer, self.indexBuffer, bufferSize, self.device, self.commandPool, self.graphicQueue)
        
        vkDestroyBuffer(self.device, stagingBuffer, None)
        vkFreeMemory(self.device, stagingMemory, None)
        