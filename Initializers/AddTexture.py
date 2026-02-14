from Initializers.Images import *
from PIL import Image
import math
from vulkan import *
from Initializers.copyops import *

def Textures(device, commandPool, graphicQueue, physicalDevice, texturePath):
    
    _image    = Image.open(texturePath)
    _image.putalpha(1)
    width     = _image.width
    height    = _image.height
    imageSize = width * height * 4
    
    mipLevels = int(math.floor(math.log2(max(width, height)))) + 1
        
    stagingBuffer, stagingMem = createBuffer(imageSize, VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
                                             VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT, 
                                             device, physicalDevice)
    
    data = vkMapMemory(device, stagingMem, 0, imageSize, 0)
    ffi.memmove(data, _image.tobytes(), imageSize)
    vkUnmapMemory(device, stagingMem)
        
    del _image
    
    textureImage, textureImageMemory = createImage(width, height, VK_SAMPLE_COUNT_1_BIT,
                                                   mipLevels,
                                                   VK_FORMAT_R8G8B8A8_UNORM,
                                                   VK_IMAGE_TILING_OPTIMAL,
                                                   VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
                                                   VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, device, physicalDevice)
    
    transitionImageLayout(textureImage, VK_FORMAT_R8G8B8A8_UNORM,
                          VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                          mipLevels, device, commandPool, graphicQueue)
    
    copyBufferToImage(stagingBuffer, textureImage, width, height, device, commandPool, graphicQueue)
    
    vkDestroyBuffer(device, stagingBuffer, None)
    vkFreeMemory(device, stagingMem, None)
    
    generateMipmaps(textureImage, width, height, mipLevels, device, commandPool, graphicQueue)
    textureImageView = createTextureImageView(device, mipLevels, textureImage)
    textureSampler = createTextureSampler(device, mipLevels)
    
    return textureImage, textureImageMemory, textureImageView, textureSampler
    
def transitionImageLayout(image, imFormat, oldLayout, newLayout, mipLevels, device, commandPool, graphicQueue):
    
    cmdBuffer = beginSingleTimeCommands(device, commandPool)
    
    subresourceRange = VkImageSubresourceRange(
        aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT,
        baseMipLevel   = 0,
        levelCount     = mipLevels,
        baseArrayLayer = 0,
        layerCount     = 1
    )
    
    if newLayout == VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL:
        subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT
        
        if hasStencilComponent(imFormat):
            subresourceRange.aspectMask = VK_IMAGE_ASPECT_DEPTH_BIT | VK_IMAGE_ASPECT_STENCIL_BIT
    
    barrier = VkImageMemoryBarrier(
        oldLayout           = oldLayout,
        newLayout           = newLayout,
        srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        image               = image,
        subresourceRange    = subresourceRange
    )
    
    sourceStage = 0
    destinationStage = 0
    
    if oldLayout == VK_IMAGE_LAYOUT_UNDEFINED and newLayout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL:
        barrier.srcAccessMask = 0
        barrier.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT
        
        sourceStage = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT
        destinationStage = VK_PIPELINE_STAGE_TRANSFER_BIT
    elif oldLayout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL and newLayout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL:
        barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT
        barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT
        
        sourceStage = VK_PIPELINE_STAGE_TRANSFER_BIT
        destinationStage = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT
    elif oldLayout == VK_IMAGE_LAYOUT_UNDEFINED and newLayout == VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL:
        barrier.srcAccessMask = 0
        barrier.dstAccessMask = VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT | VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT
        
        sourceStage = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT
        destinationStage = VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT
    else:
        raise Exception('unsupported layout transition!')
    
    vkCmdPipelineBarrier(cmdBuffer,
                         sourceStage,
                         destinationStage,
                         0,
                         0, None,
                         0, None,
                         1, barrier)
    
    endSingleTimeCommands(cmdBuffer, device, commandPool, graphicQueue)

def hasStencilComponent(fm):
    
    return fm == VK_FORMAT_D32_SFLOAT_S8_UINT or fm == VK_FORMAT_D24_UNORM_S8_UINT

def copyBufferToImage(buffer, image, width, height, device, commandPool, graphicQueue):
    
    cmdBuffer = beginSingleTimeCommands(device, commandPool)
    
    subresource = VkImageSubresourceLayers(
        aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT,
        mipLevel       = 0,
        baseArrayLayer = 0,
        layerCount     = 1
    )
    
    region = VkBufferImageCopy(
        bufferOffset      = 0,
        bufferRowLength   = 0,
        bufferImageHeight = 0,
        imageSubresource  = subresource,
        imageOffset       = [0, 0],
        imageExtent       = [width, height, 1]
    )
    
    vkCmdCopyBufferToImage(cmdBuffer, buffer, image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, region)
    
    endSingleTimeCommands(cmdBuffer, device, commandPool, graphicQueue)

def generateMipmaps(image, width, height, mipLevels, device, commandPool, graphicQueue):
    
    cmdBuffer = beginSingleTimeCommands(device, commandPool)
    
    subresourceRange = VkImageSubresourceRange(
        aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT,
        baseArrayLayer = 0,
        layerCount     = 1,
        levelCount     = 1,
        baseMipLevel   = 1
    )
    
    barrier = VkImageMemoryBarrier(
        image               = image,
        srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
        subresourceRange    = subresourceRange
    )
    
    mipWidth = width
    mipHeight = height
    
    for i in range(1, mipLevels):
        barrier.subresourceRange.baseMipLevel = i - 1
        barrier.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL
        barrier.newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL
        barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT
        barrier.dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT
        
        vkCmdPipelineBarrier(cmdBuffer,
                             VK_PIPELINE_STAGE_TRANSFER_BIT,
                             VK_PIPELINE_STAGE_TRANSFER_BIT,
                             0,
                             0, None,
                             0, None,
                             1, barrier)
        
        sss = VkImageSubresourceLayers(
            aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT,
            mipLevel       = i - 1,
            baseArrayLayer = 0,
            layerCount     = 1
        )
        
        soffset = [VkOffset3D(0, 0, 0), VkOffset3D(mipWidth, mipHeight, 1)]
        dss = VkImageSubresourceLayers(
            aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT,
            mipLevel       = i,
            baseArrayLayer = 0,
            layerCount     = 1
        )
        
        doffset = [VkOffset3D(0, 0, 0), VkOffset3D(int(mipWidth / 2), int(mipHeight / 2), 1)]
        blit = VkImageBlit(
            srcSubresource = sss,
            srcOffsets     = soffset,
            dstSubresource = dss,
            dstOffsets     = doffset
        )
        
        vkCmdBlitImage(cmdBuffer,
                       image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                       image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                       1, blit,
                       VK_FILTER_LINEAR)
        
        
        barrier.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL
        barrier.newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL
        barrier.srcAccessMask = VK_ACCESS_TRANSFER_READ_BIT
        barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT
        
        vkCmdPipelineBarrier(cmdBuffer,
                             VK_PIPELINE_STAGE_TRANSFER_BIT,
                             VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
                             0, 0, None,
                             0, None,
                             1, barrier)
        
        if mipWidth > 1: mipWidth = int(mipWidth / 2)
        if mipHeight > 1: mipHeight = int(mipHeight / 2)
        
    barrier.subresourceRange.baseMipLevel = mipLevels - 1
    barrier.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL
    barrier.newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL
    barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT
    barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT
    
    vkCmdPipelineBarrier(cmdBuffer,
                         VK_PIPELINE_STAGE_TRANSFER_BIT,
                         VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
                         0, 0, None, 0, None,
                         1, barrier)
    
    endSingleTimeCommands(cmdBuffer, device, commandPool, graphicQueue)
    
def createTextureImageView(device, mipLevels, textureImage):
    
    return createImageView(textureImage, VK_FORMAT_R8G8B8A8_UNORM, VK_IMAGE_ASPECT_COLOR_BIT, mipLevels, device)

def createTextureSampler(device, mipLevels):
    
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
        maxLod                  = float(mipLevels),
        mipLodBias              = 0
    )
    
    return vkCreateSampler(device, samplerInfo, None)