from vulkan import *
import numpy as np
from PIL import Image
from Initializers.copyops import *
import io

def SwapToImage(device, commandPool, graphicsQueue, physicalDevice, swapChainExtent, srcImage):
    colorImageInfo = VkImageCreateInfo(
        imageType     = VK_IMAGE_TYPE_2D,
        format        = VK_FORMAT_B8G8R8A8_UNORM,
        mipLevels     = 1,
        arrayLayers   = 1,
        samples       = VK_SAMPLE_COUNT_1_BIT,
        tiling        = VK_IMAGE_TILING_LINEAR,
        usage         = VK_IMAGE_USAGE_TRANSFER_SRC_BIT,#VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT
        initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
        extent        = [swapChainExtent.width, swapChainExtent.height, 1]
    )

    colorImage = vkCreateImage(device, colorImageInfo, None)
    memReqs = vkGetImageMemoryRequirements(device, colorImage)
    memProps = vkGetPhysicalDeviceMemoryProperties(physicalDevice)
    memoryType = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
    typeBits = memReqs.memoryTypeBits
    
    for i in range(32):
        if (typeBits & 1) == 1:
            if (memProps.memoryTypes[i].propertyFlags & memoryType) == memoryType:
                memType = i
                break
        typeBits >>= 1
    
    memAllocInfo = VkMemoryAllocateInfo(memoryTypeIndex = memType, allocationSize  = memReqs.size)
    memAlloc = vkAllocateMemory(device, memAllocInfo, None)
    vkBindImageMemory(device, colorImage, memAlloc, 0)
    
    cmdBuff = beginSingleTimeCommands(device, commandPool)
    
    subresourceRange = VkImageSubresourceRange(
        aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT,
        baseMipLevel   = 0,
        levelCount     = 1,
        baseArrayLayer = 0,
        layerCount     = 1
    )
    barrier = VkImageMemoryBarrier(
        oldLayout           = VK_IMAGE_LAYOUT_UNDEFINED,
        newLayout           = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
        srcQueueFamilyIndex = VK_PIPELINE_STAGE_TRANSFER_BIT,
        dstQueueFamilyIndex = VK_PIPELINE_STAGE_TRANSFER_BIT,
        image               = colorImage,
        srcAccessMask       = 0,
        dstAccessMask       = VK_ACCESS_TRANSFER_WRITE_BIT,
        subresourceRange    = subresourceRange
    )
    # source image barrier
    barrier = VkImageMemoryBarrier(
        oldLayout           = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
        newLayout           = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
        srcQueueFamilyIndex = VK_PIPELINE_STAGE_TRANSFER_BIT,
        dstQueueFamilyIndex = VK_PIPELINE_STAGE_TRANSFER_BIT,
        image               = srcImage,
        srcAccessMask       = VK_ACCESS_MEMORY_READ_BIT,
        dstAccessMask       = VK_ACCESS_TRANSFER_READ_BIT,
        subresourceRange    = subresourceRange
    )
    
    srcSubresource = VkImageSubresourceLayers(
        aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
        layerCount = 1
    )
    dstSubresource = VkImageSubresourceLayers(
        aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
        layerCount = 1
    )
    imageCopy = VkImageCopy(
        srcSubresource = srcSubresource,
        srcOffset = VkOffset3D(1, 0, 0),
        dstSubresource = dstSubresource,
        dstOffset = VkOffset3D(0, 0, 0),
        extent = VkExtent3D(swapChainExtent.width, swapChainExtent.height, 1)
    )

    vkCmdCopyImage(cmdBuff, srcImage, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                   colorImage, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, imageCopy)

    barrier = VkImageMemoryBarrier(
        oldLayout           = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
        newLayout           = VK_IMAGE_LAYOUT_GENERAL,
        srcQueueFamilyIndex = VK_PIPELINE_STAGE_TRANSFER_BIT,
        dstQueueFamilyIndex = VK_PIPELINE_STAGE_TRANSFER_BIT,
        image               = colorImage,
        srcAccessMask       = VK_ACCESS_TRANSFER_WRITE_BIT,
        dstAccessMask       = VK_ACCESS_MEMORY_READ_BIT,
        subresourceRange    = subresourceRange
    )
    
    barrier = VkImageMemoryBarrier(
        oldLayout           = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
        newLayout           = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
        srcQueueFamilyIndex = VK_PIPELINE_STAGE_TRANSFER_BIT,
        dstQueueFamilyIndex = VK_PIPELINE_STAGE_TRANSFER_BIT,
        image               = srcImage,
        srcAccessMask       = VK_ACCESS_TRANSFER_READ_BIT,
        dstAccessMask       = VK_ACCESS_MEMORY_READ_BIT,
        subresourceRange    = subresourceRange
    )
    
    endSingleTimeCommands(cmdBuff, device, commandPool, graphicsQueue)
    imageMemory = memAlloc
    
    #subResource  = VkImageSubresource(VK_IMAGE_ASPECT_COLOR_BIT, 0, 0)
    
    #subResourceLayout = vkGetImageSubresourceLayout(device, colorImage, subResource)
    #print(subResourceLayout.offset, subResourceLayout.size, subResourceLayout.rowPitch, subResourceLayout.arrayPitch, subResourceLayout.depthPitch)
    pb = vkMapMemory(device, imageMemory, 0, swapChainExtent.width * swapChainExtent.height * 4, 0)
    vkUnmapMemory(device, imageMemory)
    dta = Image.frombuffer("RGBA", (swapChainExtent.width, swapChainExtent.height), pb, 'raw', "RGBA", 0, 1)
    dta.show()
    dta.save('gfg_dummy_pic.png')
    