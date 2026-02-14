import math
from vulkan import *
from Initializers.Images import *
from Initializers.Descriptor import *
from Initializers.AR_Pass import *
from Initializers.DeviceInits import *
from Initializers.AddTexture import transitionImageLayout


class RenderMakerAR:
    
    def __init__(self, blend, path, ptypes, extent, device, renderPass, msaaSamples, grid = False):
        
        self.path = path
        self.ptypes = ptypes
        self.descriptorSetLayout = createDescriptorSetLayout(device, ptypes)
        
        self.pipelineLayout, self.pipeline = createGraphicsPipeline(device, blend, msaaSamples, renderPass, extent,
                                                                    self.descriptorSetLayout, self.path, grid)
        
    def update(self, blend, extent, device, renderPass, msaaSamples, grid = False):
        self.pipelineLayout, self.pipeline = createGraphicsPipeline(device, blend, msaaSamples, renderPass, extent,
                                                                    self.descriptorSetLayout, self.path, grid)

class OffScreenFB:
    
    def __init__(self, deviceInfo, extent, imgFormat):
        
        self.renderData = {}
        self.commandBuffers = []
        self.ImageFormat = imgFormat
        self.mipLevels = int(math.floor(math.log2(max(extent[0], extent[1])))) + 1
        self.createAccumRevealage(deviceInfo, extent)
            
    def recreate(self, deviceInfo, extent):
        self.mipLevels = int(math.floor(math.log2(max(extent[0], extent[1])))) + 1
        self.createAccumRevealage(deviceInfo, extent)
        
    def destroy(self, deviceInfo):
        
        [vkDestroyFramebuffer(deviceInfo.device, i, None) for i in self.Framebuffers]
        
        vkDestroyImageView(deviceInfo.device, self.mRenderImageViews, None)
        vkDestroyImage(deviceInfo.device, self.mRenderImages, None)
        vkFreeMemory(deviceInfo.device, self.mRenderImageMemory, None)
        
        vkDestroyImageView(deviceInfo.device, self.mmRenderImageViews, None)
        vkDestroyImage(deviceInfo.device, self.mmRenderImages, None)
        vkFreeMemory(deviceInfo.device, self.mmRenderImageMemory, None)
        
        vkDestroyImageView(deviceInfo.device, self.depthImageView, None)
        vkDestroyImage(deviceInfo.device, self.depthImage, None)
        vkFreeMemory(deviceInfo.device, self.depthImageMemory, None)
        
        vkDestroyRenderPass(deviceInfo.device, self.renderpass, None)
        
        for i in self.renderData:
            vkDestroyPipeline(deviceInfo.device, self.renderData[i].pipeline, None)
            vkDestroyPipelineLayout(deviceInfo.device, self.renderData[i].pipelineLayout, None)
        
        [vkDestroyImageView(deviceInfo.device, j, None) for j in self.AccumImageViews]
        self.AccumImageViews = []
        [vkDestroyImageView(deviceInfo.device, j, None) for j in self.RevealageImageViews]
        self.RevealageImageViews = []
        for i in range(3):
            vkDestroyImage(deviceInfo.device, self.AccumImages[i], None)
            vkFreeMemory(deviceInfo.device, self.AccumImageMem[i], None)
            
            vkDestroyImage(deviceInfo.device, self.RevealageImages[i], None)
            vkFreeMemory(deviceInfo.device, self.RevealageImageMem[i], None)
        
            
    def createAccumRevealage(self, deviceInfo, extent):
        
        self.AccumImages = []
        self.AccumImageMem = []
        self.AccumImageViews = []
        self.RevealageImages = []
        self.RevealageImageMem = []
        self.RevealageImageViews = []
        self.Extent = VkExtent2D(extent[0], extent[1])
        self.multiSampler(deviceInfo)
        self.AccumSample = self.createTextureSampler(deviceInfo.device)
        self.RevealageSample = self.createTextureSampler(deviceInfo.device)
        for i in range(3):
            RImages, colorImageMemory = createImage(self.Extent.width, self.Extent.height, self.msaaSamples,
                                                1, self.ImageFormat, VK_IMAGE_TILING_OPTIMAL,
                                                VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
                                                VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, deviceInfo.device, deviceInfo.physicalDevice)
            
            self.AccumImages.append(RImages)
            self.AccumImageMem.append(colorImageMemory)
            self.AccumImageViews.append(createImageView(RImages, self.ImageFormat, VK_IMAGE_ASPECT_COLOR_BIT, 1, deviceInfo.device))
                
            RImages, colorImageMemory = createImage(self.Extent.width, self.Extent.height, self.msaaSamples,
                                                    1, VK_FORMAT_R32_SFLOAT, VK_IMAGE_TILING_OPTIMAL,
                                                    VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_SAMPLED_BIT, 
                                                    VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, deviceInfo.device, deviceInfo.physicalDevice)
            self.RevealageImages.append(RImages)  
            self.RevealageImageMem.append(colorImageMemory)
            self.RevealageImageViews.append(createImageView(RImages, VK_FORMAT_R32_SFLOAT, VK_IMAGE_ASPECT_COLOR_BIT, 1, deviceInfo.device))
            
        self.createDdpeth_FB(deviceInfo)
        
    def createTextureSampler(self, device):
        
        samplerInfo = VkSamplerCreateInfo(
            magFilter               = VK_FILTER_LINEAR,
            minFilter               = VK_FILTER_LINEAR,
            addressModeU            = VK_SAMPLER_ADDRESS_MODE_REPEAT,
            addressModeV            = VK_SAMPLER_ADDRESS_MODE_REPEAT,
            addressModeW            = VK_SAMPLER_ADDRESS_MODE_REPEAT,
            anisotropyEnable        = True,
            maxAnisotropy           = 16,
            compareEnable           = False,
            compareOp               = VK_COMPARE_OP_ALWAYS,
            borderColor             = VK_BORDER_COLOR_INT_OPAQUE_BLACK,
            unnormalizedCoordinates = False,
            minLod                  = 0,#float(mipLevels / 2),
            maxLod                  = float(self.mipLevels),
            mipLodBias              = 0
        )
        
        return vkCreateSampler(device, samplerInfo, None)
    
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
        
        self.renderpass = cRenderPass(deviceInfo.device, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, self.msaaSamples,
                                      self.DepthFormat, self.ImageFormat, VK_FORMAT_R32_SFLOAT)
        
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
        
        self.mmRenderImages, self.mmRenderImageMemory = createImage(self.Extent.width, self.Extent.height, self.msaaSamples,
                                                      1, VK_FORMAT_R32_SFLOAT, VK_IMAGE_TILING_OPTIMAL,
                                                      VK_IMAGE_USAGE_TRANSIENT_ATTACHMENT_BIT | VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
                                                      VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, deviceInfo.device, deviceInfo.physicalDevice)
            
        self.mmRenderImageViews = createImageView(self.mmRenderImages, VK_FORMAT_R32_SFLOAT, VK_IMAGE_ASPECT_COLOR_BIT, 1, deviceInfo.device)
        
        
    def __createFrambuffers(self, device):
        
        self.Framebuffers = []
        for i, iv in enumerate(self.AccumImageViews):
            framebufferInfo = VkFramebufferCreateInfo(
                renderPass   = self.renderpass,
                pAttachments = [iv, self.RevealageImageViews[i], self.mRenderImageViews, self.mmRenderImageViews, self.depthImageView],
                width        = self.Extent.width,
                height       = self.Extent.height,
                layers       = 1
            )
            
            self.Framebuffers.append(vkCreateFramebuffer(device, framebufferInfo, None))
        
            
    def depthFormat(self, deviceInfo):
        
        return self.__findSupportedFormat(deviceInfo, [VK_FORMAT_D32_SFLOAT, VK_FORMAT_D32_SFLOAT_S8_UINT, VK_FORMAT_D24_UNORM_S8_UINT],
                                          VK_IMAGE_TILING_OPTIMAL, VK_FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT)
    
    def __findSupportedFormat(self, deviceInfo, candidates, tiling, feature):
        
        for i in candidates:
            props = vkGetPhysicalDeviceFormatProperties(deviceInfo.physicalDevice, i)
            
            if tiling == VK_IMAGE_TILING_LINEAR and (props.linearTilingFeatures & feature == feature):
                return i
            elif tiling == VK_IMAGE_TILING_OPTIMAL and (props.optimalTilingFeatures & feature == feature):
                return i
            
        return -1
    