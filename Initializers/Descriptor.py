import pyrr
from vulkan import *
import numpy as np
from AddOns import glm
from Initializers.copyops import *
from Initializers.camera import *

class UniformBufferObject(object):

    def __init__(self):
        self.model = glm.rotate(np.identity(4, np.float32), 90.0, 0.0, 1.0, 0.0)
        self.trans = pyrr.matrix44.create_from_translation([0, 0, 0])
        self.oid = np.array([0, 0, 0, 0], np.float32)
        
    def rotate(self, x = 0, y = 0, z = 0):
        
        if x:
            rx = pyrr.Matrix44.from_x_rotation(x)
            return np.dot(self.trans, rx)
        elif y:
            ry = pyrr.Matrix44.from_y_rotation(y)
            return np.dot(self.trans, ry)
        elif z:
            rz = pyrr.Matrix44.from_z_rotation(z)
            return np.dot(self.trans, rz)
            
    def move(self, x = 0, y = 0, z = 0):
        
        g = pyrr.matrix44.create_from_translation(pyrr.Vector3([x, y, z]))
        return np.dot(self.trans, g)
        
    def scale(self, x = 1, y = 1, z = 1):
        
        s = pyrr.matrix44.create_from_scale(pyrr.Vector3([x, y, z]))
        return np.dot(self.trans, s)
    
    def toArray(self):
        
        self.dta = self.model.astype("f").tobytes() + self.trans.astype("f").tobytes() + self.oid.astype("f").tobytes()
        return self.dta
        
    @property
    def nbytes(self):
        return len(self.dta)
    
class StorageBufferObject(object):

    def __init__(self):
        self.dta = np.array([1.0, -2.0, 1.0, 0, 1, 1, 1, 15], np.float32).astype("f").tobytes()
        self.pixel = np.array([0, 0], np.float32)
    
    def reCreate(self, lights = {}):
        self.dta = None
        for i in lights:
            if self.dta:
                self.dta += lights[i].position.astype("f").tobytes()
                self.dta += lights[i].color.astype("f").tobytes()
                self.dta += lights[i].pix.astype("f").tobytes()
                
            else:
                self.dta = lights[i].position.astype("f").tobytes()
                self.dta += lights[i].color.astype("f").tobytes()
                self.dta += lights[i].pix.astype("f").tobytes()
        
    def add(self, item):
        self.dta += item.position.astype("f").tobytes()
        self.dta += item.color.astype("f").tobytes()
        self.dta += item.pix.astype("f").tobytes()
    
    @property
    def nbytes(self):
        return len(self.dta)
    
class PixelStoreBufferObject(object):

    def __init__(self):
        self.pixel = np.array([0, 0], np.float32)
        self.objpix = np.array([0, 0, 0, 0], np.float32)
        
    @property
    def nbytes(self):
        self.dta = self.pixel.astype("f").tobytes() + self.objpix.astype("f").tobytes()
        return len(self.dta)
        
def createUniformBuffer(ubo, device, physicalDevice):
    
    a = ubo.toArray()
    uniformBuffer, uniformBufferMemory = createBuffer(ubo.nbytes, VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT,
                                                     VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
                                                     device, physicalDevice)
    
    return uniformBuffer, uniformBufferMemory

def createStorageBuffer(ssbo, device, physicalDevice):
    
    storageBuffer, storageBufferMemory = createBuffer(ssbo.nbytes, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,
                                                     VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
                                                     device, physicalDevice)
    
    return storageBuffer, storageBufferMemory

def createDescriptorPool(device, ptypes):
    
    poolSize = []
    
    for i in ptypes:
        poolSize.append(VkDescriptorPoolSize(type = i[0], descriptorCount = 3))
    
    poolInfo = VkDescriptorPoolCreateInfo(pPoolSizes = poolSize, maxSets = 3)
    
    return vkCreateDescriptorPool(device, poolInfo, None)
    
def createDescriptorSetLayout(device, ptypes):
    
    layoutBindings = []
    
    for i in range(len(ptypes)):
        layoutBindings.append(VkDescriptorSetLayoutBinding(
            binding         = i,
            descriptorType  = ptypes[i][0],
            descriptorCount = 1,
            stageFlags      = ptypes[i][1]
        ))
    
    layoutInfo = VkDescriptorSetLayoutCreateInfo(
        sType        = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
        bindingCount = len(layoutBindings),
        pBindings    = layoutBindings
    )
    
    return vkCreateDescriptorSetLayout(device, layoutInfo, None)

def createDescriptorSet(device, count, descriptorPool, descriptorSetLayout):
    
    layouts = []
    for i in range(count):
        layouts.append(descriptorSetLayout)
            
    allocInfo = VkDescriptorSetAllocateInfo(
        descriptorPool     = descriptorPool,
        descriptorSetCount = count,
        pSetLayouts        = layouts
    )
    
    return vkAllocateDescriptorSets(device, allocInfo)
    
    
def updateDescriptorSet(device, count, buffs, descriptorSet):
        
    descriptWrite = []
    
    for i in range(count):
        for j in range(len(buffs)):
            if buffs[j][0] == VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER:
                if buffs[j][1]:
                    bufferInfo = VkDescriptorImageInfo(
                        imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
                        imageView   = buffs[j][1],
                        sampler     = buffs[j][2]
                    )
                    
                    descriptWrite.append(VkWriteDescriptorSet(
                        dstSet            = descriptorSet[i],
                        dstBinding        = j,
                        dstArrayElement   = 0,
                        descriptorType    = buffs[j][0],
                        #descriptorCount = 1,
                        pImageInfo       = [bufferInfo]
                    ))
                    vkUpdateDescriptorSets(device, j+1, descriptWrite, 0, None)
                    return
                else:
                    vkUpdateDescriptorSets(device, j, descriptWrite, 0, None)
                    return
                    
            else:
                bufferInfo = VkDescriptorBufferInfo(
                    buffer = buffs[j][2],
                    offset = 0,
                    range  = buffs[j][1].nbytes
                )
            
                descriptWrite.append(VkWriteDescriptorSet(
                    dstSet            = descriptorSet[i],
                    dstBinding        = j,
                    dstArrayElement   = 0,
                    descriptorType    = buffs[j][0],
                    #descriptorCount = 1,
                    pBufferInfo       = [bufferInfo]
                ))
        
        vkUpdateDescriptorSets(device, j+1, descriptWrite, 0, None)