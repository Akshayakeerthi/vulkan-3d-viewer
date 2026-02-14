from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap, QScreen
from PIL import Image
import numpy as np
from utils import *
import io

MAX_FRAMES_IN_FLIGHT = 2

class HelloTriangleApplication(QWidget):

    def __init__(self, parent):
        super(HelloTriangleApplication, self).__init__(parent)
        
        self.parent = parent
        self.c_move = False
        
        self.setWindowTitle("Vulkan Python - PySide2")
        self.resize(1020, 700)
        self.setMinimumSize(400, 400)
        self.setMouseTracking(True)
        self.selectedItems = []
        
        self.imageAvailableSemaphore = []
        self.renderFinishedSemaphore = []
        self.inFlightImages = []
        self.inFlightFences = []
        self.currentFrame = 0
        
        self.mipLevels = 1
        self.setFocusPolicy(Qt.StrongFocus)
        self.lights = {}
        self.models3d = {}
        
        self.__startTime = time.time()
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.render)
        
        self.initVulkan()
        self.timer.start()

    def __del__(self):
        vkDeviceWaitIdle(self.deviceInfo.device)

        if self.descriptorPool:
            vkDestroyDescriptorPool(self.deviceInfo.device, self.descriptorPool, None)

        for i in self.models3d:
            vkDestroySampler(self.deviceInfo.device, self.models3d[i].textureSampler, None)
            vkDestroyImageView(self.deviceInfo.device, self.models3d[i].textureImageView, None)
            vkDestroyImage(self.deviceInfo.device, self.models3d[i].textureImage, None)
            vkFreeMemory(self.deviceInfo.device, self.models3d[i].textureImageMemory, None)
            vkDestroyBuffer(self.deviceInfo.device, self.models3d[i].vertexBuffer, None)
            vkFreeMemory(self.deviceInfo.device, self.models3d[i].vertexBufferMemory, None)
            vkDestroyBuffer(self.deviceInfo.device, self.models3d[i].indexBuffer, None)
            vkFreeMemory(self.deviceInfo.device, self.models3d[i].indexBufferMemory, None)
            vkDestroyDescriptorPool(self.deviceInfo.device, self.models3d[i].descriptorPool, None)
            vkDestroyDescriptorSetLayout(self.deviceInfo.device, self.models3d[i].descriptorSetLayout, None)
            
        vkDestroyBuffer(self.deviceInfo.device, self.uniformBuffer, None)
        vkFreeMemory(self.deviceInfo.device, self.uniformBufferMemory, None)

        for i in range(MAX_FRAMES_IN_FLIGHT):
            vkDestroySemaphore(self.deviceInfo.device, self.imageAvailableSemaphore[i], None)
            vkDestroySemaphore(self.deviceInfo.device, self.renderFinishedSemaphore[i], None)
            vkDestroyFence(self.deviceInfo.device, self.inFlightFences[i], None)
        
        if self.renderData['SwapChain'].descriptorSetLayout:
            vkDestroyDescriptorSetLayout(self.deviceInfo.device, self.renderData['SwapChain'].descriptorSetLayout, None)

        self.__cleanupSwapChain()

        if self.deviceInfo.commandPool:
            vkDestroyCommandPool(self.deviceInfo.device, self.deviceInfo.commandPool, None)

        if self.deviceInfo.device:
            vkDestroyDevice(self.deviceInfo.device, None)

        if self.deviceInfo.callbcak:
            vkDestroyDebugReportCallbackEXT(self.deviceInfo.instance, self.deviceInfo.callbcak, None)

        if self.deviceInfo.surface:
            vkDestroySurfaceKHR(self.deviceInfo.instance, self.deviceInfo.surface, None)

        if self.deviceInfo.instance:
            vkDestroyInstance(self.deviceInfo.instance, None)
            print('instance destroyed')
    
    
    def __cleanupSwapChain(self):
        
        self.SwapChainFB.destroy(self.deviceInfo)
        
        vkFreeCommandBuffers(self.deviceInfo.device, self.deviceInfo.commandPool, 
                             len(self.SwapChainFB.commandBuffers), self.SwapChainFB.commandBuffers)
        vkDestroySwapchainKHR(self.deviceInfo.device, self.SwapChainFB.swapChain, None)

    def __recreateSwapChain(self):
        
        vkDeviceWaitIdle(self.deviceInfo.device)
        
        self.__cleanupSwapChain()
        
        self.SwapChainFB.recreate(self.deviceInfo, [self.width(), self.height()])
        self.SwapChainFB.renderData['main'].update(False, self.SwapChainFB.Extent, self.deviceInfo.device, self.SwapChainFB.renderpass, 
                                                  self.SwapChainFB.msaaSamples)
        self.SwapChainFB.renderData['grid'].update(True, self.SwapChainFB.Extent, self.deviceInfo.device, self.SwapChainFB.renderpass, 
                                                   self.SwapChainFB.msaaSamples, True)
        
        self.createCommandBuffers()
        self.inFlightImages = []
        
        for image in self.SwapChainFB.RenderImages:
            self.inFlightImages.append(VK_NULL_HANDLE)
    
    def initVulkan(self):
        
        self.deviceInfo = Device(self.winId())
        self.cmr = Camera()
        
        self.SwapChainFB = FrameBuffer(self.deviceInfo, [self.width(), self.height()])
        
        ptypes = [[VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, VK_SHADER_STAGE_ALL],
                 [VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, VK_SHADER_STAGE_FRAGMENT_BIT], 
                 [VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, VK_SHADER_STAGE_FRAGMENT_BIT]]
        path = ['CommonResources/Shaders/CShade/vert0.spv', 'CommonResources/Shaders/CShade/frag0.spv']
        self.SwapChainFB.renderData['main'] = RenderMaker(False, path, ptypes, self.SwapChainFB.Extent, self.deviceInfo.device,
                                                          self.SwapChainFB.renderpass, self.SwapChainFB.msaaSamples)
        
        ptypes = [[VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, VK_SHADER_STAGE_ALL]]
        path = ['CommonResources/Shaders/CShade/gridV.spv', 'CommonResources/Shaders/CShade/gridF.spv']
        self.SwapChainFB.renderData['grid'] = RenderMaker(True, path, ptypes, self.SwapChainFB.Extent, self.deviceInfo.device,
                                                          self.SwapChainFB.renderpass, self.SwapChainFB.msaaSamples, True)
        
        #ptypes = [[VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, VK_SHADER_STAGE_ALL],
        #          [VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, VK_SHADER_STAGE_FRAGMENT_BIT]]
        #path = ['CommonResources/Shaders/vert.spv', 'CommonResources/Shaders/frag.spv']
        #self.ObjPickFB.renderData['main'] = RenderMaker(path, ptypes, self.ObjPickFB.Extend,
        #                                                self.deviceInfo.device, self.ObjPickFB.renderPass)
        
        self.ubo = UniformBufferObject()
        self.uniformBuffer, self.uniformBufferMemory = createUniformBuffer(self.ubo, self.deviceInfo.device, 
                                                                           self.deviceInfo.physicalDevice)
        self.descriptorPool = createDescriptorPool(self.deviceInfo.device, ptypes)
        self.descriptorSet = createDescriptorSet(self.deviceInfo.device, 3, self.descriptorPool, 
                                                 self.SwapChainFB.renderData['grid'].descriptorSetLayout)
        
        ptypes = [[VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, self.ubo, self.uniformBuffer]]
        
        updateDescriptorSet(self.deviceInfo.device, 3, ptypes, self.descriptorSet)
        
        self.ssbo = StorageBufferObject()
        self.storageBuffer, self.storageBufferMemory = createStorageBuffer(self.ssbo, self.deviceInfo.device, 
                                                                           self.deviceInfo.physicalDevice)
        self.psbo = PixelStoreBufferObject()
        self.PstorageBuffer, self.PstorageBufferMemory = createStorageBuffer(self.psbo, self.deviceInfo.device, 
                                                                             self.deviceInfo.physicalDevice)
        self.createCommandBuffers()
        self.__createSemaphores()
        
    def __beginSingleTimeCommands(self):
        
        
        allocInfo = VkCommandBufferAllocateInfo(
            level              = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
            commandPool        = self.deviceInfo.commandPool,
            commandBufferCount = 1
        )
        
        commandBuffer = vkAllocateCommandBuffers(self.deviceInfo.device, allocInfo)[0]
        beginInfo = VkCommandBufferBeginInfo(flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT)
        vkBeginCommandBuffer(commandBuffer, beginInfo)
        
        return commandBuffer
    
    def __endSingleTimeCommands(self, commandBuffer):
        
        vkEndCommandBuffer(commandBuffer)
        
        submitInfo = VkSubmitInfo(pCommandBuffers=[commandBuffer])
        
        vkQueueSubmit(self.deviceInfo.graphicQueue, 1, [submitInfo], VK_NULL_HANDLE)
        vkQueueWaitIdle(self.deviceInfo.graphicQueue)
        
        vkFreeCommandBuffers(self.deviceInfo.device, self.deviceInfo.commandPool, 1, [commandBuffer])
    
    
    def createCommandBuffers(self):
        
        self.SwapChainFB.commandBuffers = []
            
        allocInfo = VkCommandBufferAllocateInfo(
            commandPool        = self.deviceInfo.commandPool,
            level              = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
            commandBufferCount = len(self.SwapChainFB.Framebuffers)
        )
            
        self.SwapChainFB.commandBuffers = vkAllocateCommandBuffers(self.deviceInfo.device, allocInfo)
        
        for i, buffer in enumerate(self.SwapChainFB.commandBuffers):
            
            beginInfo = VkCommandBufferBeginInfo(flags = VK_COMMAND_BUFFER_USAGE_SIMULTANEOUS_USE_BIT)
            vkBeginCommandBuffer(buffer, beginInfo)
            #########first##############
            renderArea = VkRect2D([0, 0], self.SwapChainFB.Extent)
            clearColor = [VkClearValue(color=[[0.0, 0.0, 0.0, 1.0]]), VkClearValue(depthStencil=[1.0, 0])]
            renderPassInfo = VkRenderPassBeginInfo(
                renderPass   = self.SwapChainFB.renderpass,
                framebuffer  = self.SwapChainFB.Framebuffers[i],
                renderArea   = renderArea,
                pClearValues = clearColor
            )
            
            vkCmdBeginRenderPass(buffer, renderPassInfo, VK_SUBPASS_CONTENTS_INLINE)
            for r in self.SwapChainFB.renderData:
                
                vkCmdBindPipeline(buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, self.SwapChainFB.renderData[r].pipeline)
                
                if r == 'grid':
                    
                    vkCmdBindDescriptorSets(buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, self.SwapChainFB.renderData[r].pipelineLayout,
                                            0, 1, self.descriptorSet, 0, None)
                    vkCmdPushConstants(commandBuffer = buffer, layout = self.SwapChainFB.renderData[r].pipelineLayout,
                                       stageFlags = VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, offset = 0,
                                       size = self.cmr.size, pValues = self.cmr.dta.__array_interface__['data'][0])
                        
                    vkCmdDraw(buffer, 6, 1, 0, 0)
                
                else:
                    for j in self.models3d:
                        vkCmdBindVertexBuffers(buffer, 0, 1, [self.models3d[j].vertexBuffer], [0])
                        
                        vkCmdBindIndexBuffer(buffer, self.models3d[j].indexBuffer, 0, VK_INDEX_TYPE_UINT32)
                            
                        vkCmdBindDescriptorSets(buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, self.SwapChainFB.renderData[r].pipelineLayout,
                                                0, 1, self.models3d[j].descriptors['SwapChain'].descriptorSet, 0, None)
                            
                        vkCmdPushConstants(commandBuffer = buffer, layout = self.SwapChainFB.renderData[r].pipelineLayout,
                                           stageFlags = VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, offset = 0,
                                           size = self.cmr.size, pValues = self.cmr.dta.__array_interface__['data'][0])
                            
                        vkCmdDrawIndexed(buffer, len(self.models3d[j].indices), 1, 0, 0, 0)
                   
            vkCmdEndRenderPass(buffer)
            vkEndCommandBuffer(buffer)
                
    def findmem(self, typeBits, memProps, memoryType):
        
        for i in range(32):
            if (typeBits & 1) == 1:
                if (memProps.memoryTypes[i].propertyFlags & memoryType) == memoryType:
                    return i
                    break
            typeBits >>= 1
    
    def __createSemaphores(self):
        
        semaphoreInfo = VkSemaphoreCreateInfo()
        fenceInfo = VkFenceCreateInfo(sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO, flags = VK_FENCE_CREATE_SIGNALED_BIT)
        
        for i in range(MAX_FRAMES_IN_FLIGHT):
            self.imageAvailableSemaphore.append(vkCreateSemaphore(self.deviceInfo.device, semaphoreInfo, None))
            self.renderFinishedSemaphore.append(vkCreateSemaphore(self.deviceInfo.device, semaphoreInfo, None))
            self.inFlightFences.append(vkCreateFence(self.deviceInfo.device, fenceInfo, None))
            
        for i in self.SwapChainFB.RenderImages:
            self.inFlightImages.append(VK_NULL_HANDLE)
    
    def __updateBuffer(self):
        
        currentTime = time.time()
        
        t = currentTime - self.__startTime
        
        ma = self.ubo.toArray()
        data = vkMapMemory(self.deviceInfo.device, self.uniformBufferMemory,
                           0, self.ubo.nbytes, 0)
                
        ffi.memmove(data, ma, self.ubo.nbytes)
                                   
        vkUnmapMemory(self.deviceInfo.device, self.uniformBufferMemory)
        
        for i in self.models3d:
            for r in self.models3d[i].descriptors:
                ma = self.models3d[i].descriptors[r].ubo.toArray()
                data = vkMapMemory(self.deviceInfo.device, self.models3d[i].descriptors[r].uniformBufferMemory,
                                   0, self.models3d[i].descriptors[r].ubo.nbytes, 0)
                
                ffi.memmove(data, ma, self.models3d[i].descriptors[r].ubo.nbytes)
                                   
                vkUnmapMemory(self.deviceInfo.device, self.models3d[i].descriptors[r].uniformBufferMemory)
                
        
        data = vkMapMemory(self.deviceInfo.device, self.PstorageBufferMemory, 0, self.psbo.nbytes, 0)
            
        ffi.memmove(data, self.psbo.dta, self.psbo.nbytes)
                               
        vkUnmapMemory(self.deviceInfo.device, self.PstorageBufferMemory)
        
        data = vkMapMemory(self.deviceInfo.device, self.storageBufferMemory, 0, self.ssbo.nbytes, 0)
            
        ffi.memmove(data, self.ssbo.dta, self.ssbo.nbytes)
                               
        vkUnmapMemory(self.deviceInfo.device, self.storageBufferMemory)
            
    def getPix(self):
        
        data = vkMapMemory(self.deviceInfo.device, self.PstorageBufferMemory, 0, self.psbo.nbytes, 0)
        
        a = np.frombuffer(data, dtype = np.float32)
        if int(a[3]):
            oid1 = str(int(a[3]))
            oid2 = str(int(a[4]))
            oid3 = str(int(a[5]))
            for i in range(5 - len(oid2)):
                oid2 = '0'+oid2
            for i in range(4 - len(oid3)):
                oid3 = '0'+oid3
            #print(oid1, oid2, oid3)
            print(int(a[3]), int(a[4]), int(a[5]))
            
            return oid1+oid2+oid3
        else:
            return None
    
    def drawFrame(self):
        
        if not self.isVisible():
            return
        
        vkWaitForFences(self.deviceInfo.device, 1, [self.inFlightFences[self.currentFrame], ], VK_TRUE, 18446744073709551615)

        try:
            imageIndex = vkAcquireNextImageKHR(self.deviceInfo.device, self.SwapChainFB.swapChain, 18446744073709551615,
                                               self.imageAvailableSemaphore[self.currentFrame], VK_NULL_HANDLE)
        except VkErrorSurfaceLostKhr:
            self.__recreateSwapChain()
            return
        
        
        if (self.inFlightImages[imageIndex] != VK_NULL_HANDLE):
            vkWaitForFences(self.deviceInfo.device, 1, [self.inFlightImages[imageIndex],], VK_TRUE, 18446744073709551615)
        
        self.inFlightImages[self.currentFrame] = self.inFlightFences[self.currentFrame]
        
        submit = VkSubmitInfo(
            pWaitSemaphores   = [self.imageAvailableSemaphore[self.currentFrame], ],
            pWaitDstStageMask = [VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT],
            pCommandBuffers   = [self.SwapChainFB.commandBuffers[imageIndex], ],
            pSignalSemaphores = [self.renderFinishedSemaphore[self.currentFrame], ]
        )
        
        vkResetFences(self.deviceInfo.device, 1, [self.inFlightFences[self.currentFrame],])
        vkQueueSubmit(self.deviceInfo.graphicQueue, 1, submit, self.inFlightFences[self.currentFrame])
        
        presenInfo = VkPresentInfoKHR(
            pWaitSemaphores = [self.renderFinishedSemaphore[self.currentFrame],],
            pSwapchains     = [self.SwapChainFB.swapChain],
            pImageIndices   = [imageIndex,]
        )
        
        try:
            vkQueuePresentKHR(self.deviceInfo.presentQueue, presenInfo)
            
        except VkErrorOutOfDateKhr:
            self.__recreateSwapChain()
        
        if enableValidationLayers:
            vkQueueWaitIdle(self.deviceInfo.presentQueue)
            
        self.currentFrame = (self.currentFrame + 1) % MAX_FRAMES_IN_FLIGHT
    
    def render(self):
        
        self.__updateBuffer()
        self.drawFrame()
        
    def addModel(self, name, iname):
        
        self.models3d[name] = Model(self.deviceInfo.device, self.deviceInfo.physicalDevice, 
                                    self.deviceInfo.graphicQueue, self.deviceInfo.commandPool, iname)
        
        self.models3d[name].descriptors['SwapChain'] = createDescriptor(len(self.SwapChainFB.RenderImages), 
                                                                        self.SwapChainFB.renderData['main'].ptypes, 
                                                                        self.deviceInfo.device,
                                                                        self.deviceInfo.physicalDevice, 
                                                                        self.SwapChainFB.renderData['main'].descriptorSetLayout)
        
        
        ptypes = [[VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, self.models3d[name].descriptors['SwapChain'].ubo,
                   self.models3d[name].descriptors['SwapChain'].uniformBuffer],
                  [VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, self.ssbo, self.storageBuffer],
                  #[VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, self.psbo, self.PstorageBuffer],
                  [VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, self.models3d[name].textureImageView, self.models3d[name].textureSampler]]
        self.models3d[name].descriptors['SwapChain'].update(self.deviceInfo.device, ptypes)
        #texture
        self.models3d[name].addTexture(self.deviceInfo.device, self.deviceInfo.commandPool, self.deviceInfo.graphicQueue, 
                                       self.deviceInfo.physicalDevice, 'CommonResources/Textures/wood.jpeg')
        
        ptypes[-1][1], ptypes[-1][2] = self.models3d[name].textureImageView, self.models3d[name].textureSampler
        self.models3d[name].descriptors['SwapChain'].update(self.deviceInfo.device, ptypes)
        
        #second renderpass
        #self.models3d[name].descriptors['ObjPick'] = createDescriptor(len(self.renderData['SwapChain'].RenderImages),
        #                                                              self.renderData['ObjPick'].ptypes, self.deviceInfo.device,
        #                                                              self.deviceInfo.physicalDevice, 
        #                                                              self.renderData['ObjPick'].descriptorSetLayout)
        
        oid = str(id(self.models3d[name]))
        
        #self.models3d[name].descriptors['SwapChain'].ubo.oid = np.array([1, float('1' + oid[:4]), float(oid[4:9]), float(oid[9:])],
        #                                                                dtype = np.float32)
        #ptypes = [[VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER, self.models3d[name].descriptors['ObjPick'].ubo,
        #           self.models3d[name].descriptors['ObjPick'].uniformBuffer], 
        #          [VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, self.psbo, self.PstorageBuffer]]
        #self.models3d[name].descriptors['ObjPick'].update(self.deviceInfo.device, ptypes)
        
        nData = 'I' + str(id(self.models3d[name]))
        self.models3d[nData] = self.models3d[name]
        
        del self.models3d[name]
        
        createBottomLevelAccelerationStructure(self.deviceInfo.device, self.deviceInfo.device, self.deviceInfo.commandPool,
                                               self.deviceInfo.graphicQueue, self.models3d[nData].vertexBuffer, 4*3*3+8,
                                               self.models3d[nData].indexBuffer, self.models3d[nData].indices.shape[0]/3,
                                               self.models3d[nData].vertices.shape[0])
        
        self.createCommandBuffers()
        
        return nData
    
    def addLight(self, name, Ltype):
        self.lights[name] = Light(Ltype)
        self.ssbo.add(self.lights[name])
        
    def resizeEvent(self, event):
        
        if event.size() != event.oldSize():
            self.__recreateSwapChain()
            self.cmr.updateCamProj(self.width(), self.height())
        super(HelloTriangleApplication, self).resizeEvent(event)
        
    def mouseMoveEvent(self, event):
        
        if self.c_move:
            n_event = self.mapToGlobal(QtCore.QPoint(event.x(), event.y()))
            xoffset = self.prev[0] - n_event.x()
            yoffset = self.prev[1] - n_event.y()
            
            self.cursor().setPos(self.prev[0], self.prev[1])
            
            self.cmr.process_mouse_movement(xoffset, yoffset)
            self.createCommandBuffers()
            
            
    def mousePressEvent(self, event):
        
        self.prev = []
        self.unsetCursor()
        print(event.x(), event.y())
        self.c_move, self.grab, self.scale, self.rotate, self.xAxis, self.yAxis, self.zAxis, self.allAxis = False, False, False, False, False, False, False, True
        
        self.psbo.pixel = np.array([event.x(), event.y()], np.float32)
        self.__updateBuffer()
        
    def mouseReleaseEvent(self, event):
        
        oid = self.getPix()
        if oid:
            if event.button() == Qt.LeftButton:
                if event.modifiers() == Qt.ShiftModifier:
                    if oid[0] == '1':
                        self.selectedItems.append('I' + oid[1:])
                    elif oid[0] == '2':
                        self.selectedItems.append('L' + oid[1:])
                else:
                    self.selectedItems = []
                    if oid[0] == '1':
                        self.selectedItems.append('I' + oid[1:])
                    elif oid[0] == '2':
                        self.selectedItems.append('L' + oid[1:])
            print(self.selectedItems)
        else:
            self.selectedItems = []
            print('No object there....')
        sel = SwapToImage(event.x(), event.y(), self.deviceInfo.device, self.deviceInfo.commandPool, self.deviceInfo.graphicQueue, self.deviceInfo.physicalDevice, self.SwapChainFB.Extent, self.SwapChainFB.RenderImages[self.currentFrame])
        print(sel)
        
    def keyPressEvent(self, event):
        #recreate pipeline
        if event.modifiers() == Qt.ShiftModifier and event.key() == Qt.Key_A:
            print("Shift + A")
        elif event.key() == Qt.Key_P:
            print("printing")
            #self.getPix()
        elif event.key() == Qt.Key_M:
            print(self.cmr.camera_right)
        elif event.key() == Qt.Key_C:
            self.c_move = True
            self.setCursor(Qt.BlankCursor)
            
            mx = self.parent.pos().x() + self.width()/2
            my = self.parent.pos().y() + self.height()/2
            self.cursor().setPos(mx, my)
            
            self.prev = [self.cursor().pos().x(), self.cursor().pos().y()]
        elif event.key() == Qt.Key_Up:
            self.cmr.process_keyboard("FORWARD", 0.3)
            self.createCommandBuffers()
        elif event.key() == Qt.Key_Down:
            self.cmr.process_keyboard("BACKWARD", 0.3)
            self.createCommandBuffers()
        elif event.key() == Qt.Key_Right:
            self.cmr.process_keyboard("RIGHT", - 0.3)
            self.createCommandBuffers()
        elif event.key() == Qt.Key_Left:
            self.cmr.process_keyboard("LEFT", - 0.3)
            self.createCommandBuffers()
        elif event.key() == Qt.Key_G:
            self.grab, self.scale, self.rotate = True, False, False
            print('Grabbing....')
        elif event.key() == Qt.Key_S:
            self.grab, self.scale, self.rotate = False, True, False
            print('Scalling....')
        elif event.key() == Qt.Key_R:
            self.grab, self.scale, self.rotate = False, False, True
            print('Rotating....')
        elif event.key() == Qt.Key_X:
            self.xAxis, self.yAxis, self.zAxis, self.allAxis = True, False, False, False
            print('X-Axis....')
        elif event.key() == Qt.Key_Y:
            self.xAxis, self.yAxis, self.zAxis, self.allAxis = False, True, False, False
            print('Y-Axis....')
        elif event.key() == Qt.Key_Z:
            self.xAxis, self.yAxis, self.zAxis, self.allAxis = False, False, True, False
            print('Z-Axis....')
        elif event.key() == Qt.Key_A:
            if self.grab and self.scale and self.rotate:
                self.xAxis, self.yAxis, self.zAxis, self.allAxis = False, False, False, True
                print('All-Axis....')
            else:
                self.selectedItems = self.models3d.keys()
                print('Selecting all....', self.selectedItems)
        elif event.key() == Qt.Key_I and event.modifiers() != Qt.ShiftModifier:# and event.modifiers() != Qt.CtrlModifier:
            print("Killing")
            #SwapToImage(self.deviceInfo.device, self.deviceInfo.commandPool, self.deviceInfo.graphicQueue, self.deviceInfo.physicalDevice, self.renderData['SwapChain'].swapChainExtent, self.renderData['ObjPick'].RenderImages[self.currentFrame])
        