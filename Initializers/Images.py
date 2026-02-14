from vulkan import *
from Initializers.copyops import findMemoryType

def createImage(widht, height, numSamples, mipLevels, imFormat, tiling, usage, properties, device, physicalDevice):
    
    imageInfo = VkImageCreateInfo(
        imageType     = VK_IMAGE_TYPE_2D,
        extent        = [widht, height, 1],
        mipLevels     = mipLevels,
        arrayLayers   = 1,
        format        = imFormat,
        samples       = numSamples,
        tiling        = tiling,
        usage         = usage,
        sharingMode   = VK_SHARING_MODE_EXCLUSIVE,
        initialLayout = VK_IMAGE_LAYOUT_UNDEFINED
    )
    
    image = vkCreateImage(device, imageInfo, None)
    
    memReuirements = vkGetImageMemoryRequirements(device, image)
    allocInfo = VkMemoryAllocateInfo(
        allocationSize  = memReuirements.size,
        memoryTypeIndex = findMemoryType(memReuirements.memoryTypeBits, properties, physicalDevice)
    )
    
    imageMemory = vkAllocateMemory(device, allocInfo, None)
    
    vkBindImageMemory(device, image, imageMemory, 0)
    
    return (image, imageMemory)
    
def createImageView(image, imFormat, aspectFlage, mipLevels, device):
    
    ssr = VkImageSubresourceRange(
        aspectMask     = aspectFlage,
        baseMipLevel   = 0,
        levelCount     = mipLevels,
        baseArrayLayer = 0,
        layerCount     = 1
    )
    
    viewInfo = VkImageViewCreateInfo(
        image            = image,
        viewType         = VK_IMAGE_VIEW_TYPE_2D,
        format           = imFormat,
        subresourceRange = ssr
    )
    
    return vkCreateImageView(device, viewInfo, None)