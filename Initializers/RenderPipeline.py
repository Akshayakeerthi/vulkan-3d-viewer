from vulkan import *
from Initializers.Images import *
from Initializers.Descriptor import *
from Initializers.RenderPass import *
from Initializers.DeviceInits import *
from Initializers.AddTexture import transitionImageLayout


class RenderMaker:
    
    def __init__(self, blend, path, ptypes, extent, device, renderPass, msaaSamples, grid = False):
        
        self.path = path
        self.ptypes = ptypes
        self.descriptorSetLayout = createDescriptorSetLayout(device, ptypes)
        
        self.pipelineLayout, self.pipeline = createGraphicsPipeline(device, blend, msaaSamples, renderPass, extent,
                                                                    self.descriptorSetLayout, self.path, grid)
        
    def update(self, blend, extent, device, renderPass, msaaSamples, grid = False):
        self.pipelineLayout, self.pipeline = createGraphicsPipeline(device, blend, msaaSamples, renderPass, extent,
                                                                    self.descriptorSetLayout, self.path, grid)

class FrameBuffer:
    
    def __init__(self, deviceInfo, extent, imgFormat = None):
        
        self.renderData = {}
        self.commandBuffers = []
        
        if not imgFormat:
            self.__createSwapChain(deviceInfo, extent[0], extent[1])
            
        else:
            self.createObjPicker(deviceInfo, extent, imgFormat)
            
    def recreate(self, deviceInfo, extent):
        self.__createSwapChain(deviceInfo, extent[0], extent[1])
        
    def destroy(self, deviceInfo):
        
        [vkDestroyFramebuffer(deviceInfo.device, i, None) for i in self.Framebuffers]
        
        vkDestroyImageView(deviceInfo.device, self.mRenderImageViews, None)
        vkDestroyImage(deviceInfo.device, self.mRenderImages, None)
        vkFreeMemory(deviceInfo.device, self.mRenderImageMemory, None)
        
        vkDestroyImageView(deviceInfo.device, self.depthImageView, None)
        vkDestroyImage(deviceInfo.device, self.depthImage, None)
        vkFreeMemory(deviceInfo.device, self.depthImageMemory, None)
        vkDestroyRenderPass(deviceInfo.device, self.renderpass, None)
        
        for i in self.renderData:
            vkDestroyPipeline(deviceInfo.device, self.renderData[i].pipeline, None)
            vkDestroyPipelineLayout(deviceInfo.device, self.renderData[i].pipelineLayout, None)
        
        [vkDestroyImageView(deviceInfo.device, j, None) for j in self.RenderImageViews]
        self.RenderImagesViews = []
        
    
    def __createSwapChain(self, deviceInfo, w, h):
        
        swapChainSupport = deviceInfo.querySwapChainSupport(deviceInfo.physicalDevice)
        
        surfaceFormat = self.__chooseSwapSurfaceFormat(swapChainSupport.formats)
        presentMode = self.__chooseSwapPresentMode(swapChainSupport.presentModes)
        extent = self.__chooseSwapExtent(swapChainSupport.capabilities, w, h)
        
        imageCount = swapChainSupport.capabilities.minImageCount + 1
        
        if swapChainSupport.capabilities.maxImageCount > 0 and imageCount > swapChainSupport.capabilities.maxImageCount:
            imageCount = swapChainSupport.capabilities.maxImageCount
        
        indices = deviceInfo.findQueueFamilies(deviceInfo.physicalDevice)
        queueFamily = {}.fromkeys([indices.graphicsFamily, indices.presentFamily])
        queueFamilies = list(queueFamily.keys())
        
        formList = VkImageFormatListCreateInfoKHR(viewFormatCount = 2, pViewFormats = [surfaceFormat.format, VK_FORMAT_R32_SFLOAT])
        
        if len(queueFamilies) > 1:
            createInfo = VkSwapchainCreateInfoKHR(
                surface                 = deviceInfo.surface,
                minImageCount           = imageCount,
                imageFormat             = surfaceFormat.format,
                imageColorSpace         = surfaceFormat.colorSpace,
                imageExtent             = extent,
                imageArrayLayers        = 1,
                imageUsage              = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
                # queueFamilyIndexCount = len(queueFamilies),
                pQueueFamilyIndices     = queueFamilies,
                imageSharingMode        = VK_SHARING_MODE_CONCURRENT,
                preTransform            = swapChainSupport.capabilities.currentTransform,
                compositeAlpha          = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
                presentMode             = presentMode,
                clipped                 = True,
                flags                   = VK_SWAPCHAIN_CREATE_MUTABLE_FORMAT_BIT_KHR,
                pNext                   = formList
            )
        else:
            createInfo = VkSwapchainCreateInfoKHR(
                surface                 = deviceInfo.surface,
                minImageCount           = imageCount,
                imageFormat             = surfaceFormat.format,
                imageColorSpace         = surfaceFormat.colorSpace,
                imageExtent             = extent,
                imageArrayLayers        = 1,
                imageUsage              = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
                # queueFamilyIndexCount = len(queueFamilies),
                pQueueFamilyIndices     = queueFamilies,
                imageSharingMode        = VK_SHARING_MODE_EXCLUSIVE,
                preTransform            = swapChainSupport.capabilities.currentTransform,
                compositeAlpha          = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
                presentMode             = presentMode,
                clipped                 = True
            )
        
        self.swapChain = vkCreateSwapchainKHR(deviceInfo.device, createInfo, None)
        assert self.swapChain != None
        
        self.RenderImages = vkGetSwapchainImagesKHR(deviceInfo.device, self.swapChain)
        self.ImageFormat = surfaceFormat.format
        self.Extent = extent
        
        self.__createImageViews(deviceInfo.device)
        
        self.multiSampler(deviceInfo)
        
        self.createDdpeth_FB(deviceInfo)
        
    def createObjPicker(self, deviceInfo, extent, imgFormat):
        
        self.RenderImages = []
        self.RenderImageViews = []
        self.ImageFormat = imgFormat
        self.Extent = VkExtent2D(extent[0], extent[1])
        
        for i in range(3):
            RImages, colorImageMemory = createImage(self.Extent.width, self.Extent.height, VK_SAMPLE_COUNT_1_BIT,
                                                    1, imgFormat, VK_IMAGE_TILING_OPTIMAL,
                                                    VK_IMAGE_USAGE_TRANSIENT_ATTACHMENT_BIT | VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
                                                    VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, deviceInfo.device, deviceInfo.physicalDevice)
            
            self.RenderImages.append(RImages)
            self.RenderImageViews.append(createImageView(RImages, self.ImageFormat, VK_IMAGE_ASPECT_DEPTH_BIT, 1, deviceInfo.device))
        
        self.multiSampler(deviceInfo)
        
        self.createDdpeth_FB(deviceInfo)
        
    def createDdpeth_FB(self, deviceInfo):
        
        self.DepthFormat = self.depthFormat(deviceInfo)
        
        self.depthImage, self.depthImageMemory = createImage(self.Extent.width, self.Extent.height, self.msaaSamples, 1, 
                                                             self.DepthFormat, VK_IMAGE_TILING_OPTIMAL,
                                                             VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT,
                                                             VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, deviceInfo.device,
                                                             deviceInfo.physicalDevice)
        self.depthImageView = createImageView(self.depthImage, self.DepthFormat, VK_IMAGE_ASPECT_DEPTH_BIT, 1, deviceInfo.device)
        
        transitionImageLayout(self.depthImage, self.DepthFormat, VK_IMAGE_LAYOUT_UNDEFINED,
                              VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL, 1,
                              deviceInfo.device, deviceInfo.commandPool, deviceInfo.graphicQueue)
        
        self.renderpass = createRenderPass(deviceInfo.device, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, self.msaaSamples,
                                           self.DepthFormat, self.ImageFormat)
        
        self.__createFrambuffers(deviceInfo.device)
    
    def multiSampler(self, deviceInfo):
        
        physicalDeviceProperties = vkGetPhysicalDeviceProperties(deviceInfo.physicalDevice)
    
        counts = physicalDeviceProperties.limits.framebufferColorSampleCounts & physicalDeviceProperties.limits.framebufferDepthSampleCounts
        
        if counts & VK_SAMPLE_COUNT_64_BIT:
            self.msaaSamples = VK_SAMPLE_COUNT_64_BIT
        elif counts & VK_SAMPLE_COUNT_32_BIT:
            self.msaaSamples = VK_SAMPLE_COUNT_32_BIT
        elif counts & VK_SAMPLE_COUNT_16_BIT:
            self.msaaSamples = VK_SAMPLE_COUNT_16_BIT
        elif counts & VK_SAMPLE_COUNT_8_BIT:
            self.msaaSamples = VK_SAMPLE_COUNT_8_BIT
        elif counts & VK_SAMPLE_COUNT_4_BIT:
            self.msaaSamples = VK_SAMPLE_COUNT_4_BIT
        elif counts & VK_SAMPLE_COUNT_2_BIT:
            self.msaaSamples = VK_SAMPLE_COUNT_2_BIT
        else:
            self.msaaSamples = VK_SAMPLE_COUNT_1_BIT;
        
        self.mRenderImages, self.mRenderImageMemory = createImage(self.Extent.width, self.Extent.height, self.msaaSamples,
                                                      1, self.ImageFormat, VK_IMAGE_TILING_OPTIMAL,
                                                      VK_IMAGE_USAGE_TRANSIENT_ATTACHMENT_BIT | VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
                                                      VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, deviceInfo.device, deviceInfo.physicalDevice)
            
        self.mRenderImageViews = createImageView(self.mRenderImages, self.ImageFormat, VK_IMAGE_ASPECT_COLOR_BIT, 1, deviceInfo.device)
        
        
    def __createFrambuffers(self, device):
        
        self.Framebuffers = []
        try:
            for i, iv in enumerate(self.RenderImageViews):
                framebufferInfo = VkFramebufferCreateInfo(
                    renderPass   = self.renderpass,
                    pAttachments = [self.mRenderImageViews, self.depthImageView, iv],
                    width        = self.Extent.width,
                    height       = self.Extent.height,
                    layers       = 1
                )
                
                self.Framebuffers.append(vkCreateFramebuffer(device, framebufferInfo, None))
        except TypeError:
            framebufferInfo = VkFramebufferCreateInfo(
                renderPass   = self.renderpass,
                pAttachments = [self.mRenderImageViews, self.depthImageView, self.RenderImageViews],
                width        = self.Extent.width,
                height       = self.Extent.height,
                layers       = 1
            )
            
            self.Framebuffers.append(vkCreateFramebuffer(device, framebufferInfo, None))
            
    def depthFormat(self, deviceInfo):
        
        return self.__findSupportedFormat(deviceInfo, [VK_FORMAT_D32_SFLOAT, VK_FORMAT_D32_SFLOAT_S8_UINT, VK_FORMAT_D24_UNORM_S8_UINT],
                                          VK_IMAGE_TILING_OPTIMAL, VK_FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT)
    
    def __createImageViews(self, device):
        
        self.RenderImageViews = []
        
        for i, image in enumerate(self.RenderImages):
            self.RenderImageViews.append(createImageView(image, self.ImageFormat, VK_IMAGE_ASPECT_COLOR_BIT, 1, device))
    
    def __findSupportedFormat(self, deviceInfo, candidates, tiling, feature):
        
        for i in candidates:
            props = vkGetPhysicalDeviceFormatProperties(deviceInfo.physicalDevice, i)
            
            if tiling == VK_IMAGE_TILING_LINEAR and (props.linearTilingFeatures & feature == feature):
                return i
            elif tiling == VK_IMAGE_TILING_OPTIMAL and (props.optimalTilingFeatures & feature == feature):
                return i
            
        return -1
    
    def __chooseSwapSurfaceFormat(self, formats):
        
        if len(formats) == 1 and formats[0].format == VK_FORMAT_UNDEFINED:
            return [VK_FORMAT_R8G8B8A8_UNORM, VK_COLOR_SPACE_SRGB_NONLINEAR_KHR]
        
        for i in formats:
            if i.format == VK_FORMAT_R8G8B8A8_UNORM and i.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR:
                return i
        
        return formats[0]
    
    def __chooseSwapPresentMode(self, presentModes):
        
        bestMode = VK_PRESENT_MODE_FIFO_KHR
        
        for i in presentModes:
            if i == VK_PRESENT_MODE_FIFO_KHR:
                return i
            elif i == VK_PRESENT_MODE_MAILBOX_KHR:
                return i
            elif i == VK_PRESENT_MODE_IMMEDIATE_KHR:
                return i
        
        return bestMode
    
    def __chooseSwapExtent(self, capabilities, w, h):
        
        width = max(capabilities.minImageExtent.width, min(capabilities.maxImageExtent.width, w))
        height = max(capabilities.minImageExtent.height, min(capabilities.maxImageExtent.height, h))
        
        return VkExtent2D(width, height)