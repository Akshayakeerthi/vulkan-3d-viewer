from vulkan import *
import numpy as np
from PIL import Image
from Initializers.copyops import *

def SwapToImage(x, y, device, commandPool, graphicsQueue, physicalDevice, swapChainExtent, srcImage):
    
    imageCreateCI = VkImageCreateInfo(imageType = VK_IMAGE_TYPE_2D,
                                      format = VK_FORMAT_R8G8B8A8_UNORM,
                                      extent = [swapChainExtent.width, swapChainExtent.height, 1],
                                      arrayLayers = 1,
                                      mipLevels = 1,
                                      initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
                                      samples = VK_SAMPLE_COUNT_1_BIT,
                                      tiling = VK_IMAGE_TILING_LINEAR,
                                      usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT
    )
    
    dstImage = vkCreateImage(device, imageCreateCI, None)
    memRequirements = vkGetImageMemoryRequirements(device, dstImage)
    memProps = vkGetPhysicalDeviceMemoryProperties(physicalDevice)
    memoryType = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
    typeBits = memRequirements.memoryTypeBits
    
    for i in range(32):
        if (typeBits & 1) == 1:
            if (memProps.memoryTypes[i].propertyFlags & memoryType) == memoryType:
                memType = i
                break
        typeBits >>= 1
    
    memAllocInfo = VkMemoryAllocateInfo(allocationSize = memRequirements.size,
                                        memoryTypeIndex = memType)
    
    dstImageMemory = vkAllocateMemory(device, memAllocInfo, None)
    vkBindImageMemory(device, dstImage, dstImageMemory, 0)
    
    # Do the actual blit from the swapchain image to our host visible destination image
    copyCmd = beginSingleTimeCommands(device, commandPool) 
    
    imageMemoryBarrier = VkImageMemoryBarrier(sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
                                              srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                                              dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                                              srcAccessMask = 0,
                                              dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT,
                                              oldLayout = VK_IMAGE_LAYOUT_UNDEFINED,
                                              newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                                              image = dstImage,
                                              subresourceRange = VkImageSubresourceRange(VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1)
                                             )
        
        
    vkCmdPipelineBarrier(copyCmd,
                         VK_PIPELINE_STAGE_TRANSFER_BIT,
                         VK_PIPELINE_STAGE_TRANSFER_BIT,
                         0,
                         0, None,
                         0, None,
                         1, imageMemoryBarrier
                        )
    
    imageMemoryBarrier = VkImageMemoryBarrier(sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
                                              srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                                              dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                                              srcAccessMask = VK_ACCESS_MEMORY_READ_BIT,
                                              dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT,
                                              oldLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                                              newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                                              image = srcImage,
                                              subresourceRange = VkImageSubresourceRange(VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1)
                                             )
        
        
    vkCmdPipelineBarrier(copyCmd,
                         VK_PIPELINE_STAGE_TRANSFER_BIT,
                         VK_PIPELINE_STAGE_TRANSFER_BIT,
                         0,
                         0, None,
                         0, None,
                         1, imageMemoryBarrier
                        )
    
    # If source and destination support blit we'll blit as this also does automatic format conversion (e.g. from BGR to RGB)
    copysrc = VkImageSubresourceLayers(
            aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
            layerCount = 1
    )
    # Otherwise use image copy (requires us to manually flip components)
    imageCopyRegion = VkImageCopy(srcSubresource = copysrc,
                                  dstSubresource = copysrc,
                                  extent = VkExtent3D(swapChainExtent.width, swapChainExtent.height, 1)
                                  )
    #Issue the copy command
    vkCmdCopyImage(
        copyCmd,
        srcImage, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
        dstImage, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
        1,
        imageCopyRegion
    )
        
    imageMemoryBarrier = VkImageMemoryBarrier(sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
                                              srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                                              dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                                              srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT,
                                              dstAccessMask = VK_ACCESS_MEMORY_READ_BIT,
                                              oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                                              newLayout = VK_IMAGE_LAYOUT_GENERAL,
                                              image = dstImage,
                                              subresourceRange = VkImageSubresourceRange(VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1)
                                             )
        
        
    vkCmdPipelineBarrier(copyCmd,
                         VK_PIPELINE_STAGE_TRANSFER_BIT,
                         VK_PIPELINE_STAGE_TRANSFER_BIT,
                         0,
                         0, None,
                         0, None,
                         1, imageMemoryBarrier
                        )
        
    imageMemoryBarrier = VkImageMemoryBarrier(sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
                                              srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                                              dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
                                              srcAccessMask = VK_ACCESS_TRANSFER_READ_BIT,
                                              dstAccessMask = VK_ACCESS_MEMORY_READ_BIT,
                                              oldLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                                              newLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                                              image = srcImage,
                                              subresourceRange = VkImageSubresourceRange(VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1)
                                             )
        
        
    vkCmdPipelineBarrier(copyCmd,
                         VK_PIPELINE_STAGE_TRANSFER_BIT,
                         VK_PIPELINE_STAGE_TRANSFER_BIT,
                         0,
                         0, None,
                         0, None,
                         1, imageMemoryBarrier
                        )
    
    #vulkanDevice.flushCommandBuffer(copyCmd, queue)
    endSingleTimeCommands(copyCmd, device, commandPool, graphicsQueue)
    
    subResource = VkImageSubresource(VK_IMAGE_ASPECT_COLOR_BIT, 0, 0 )
    subResourceLayout = vkGetImageSubresourceLayout(device, dstImage, subResource)
    
    # Map image memory so we can start copying from it
    #const char* data;
    #data = vkMapMemory(device, dstImageMemory, 0, VK_WHOLE_SIZE, 0, )
    pb = vkMapMemory(device, dstImageMemory, 0, swapChainExtent.width * swapChainExtent.height * 4, 0)
    #pb += subResourceLayout.offset
    nn = np.frombuffer(pb,  dtype='f')
    #print(nn.shape)
    for i in range(697):#nn[i*1020]
        nn = np.delete(nn, [i*1020, i*1020+1, i*1020+2, i*1020+3])
    
    n1 = nn[:709920]
    n = n1.reshape(696, swapChainExtent.width)
    
    #nk = np.zeros((696, swapChainExtent.width, 3), dtype = np.uint8)
    #for i in range(n.shape[0]):
    #    for j in range(n.shape[1]):
    #        if n[i][j] > 0:
    #            print(float(n[i][j]))
            #nk[i][j][0] = n[i][j] * 255
            #nk[i][j][1] = n[i][j] * 255
            #nk[i][j][2] = n[i][j] * 255
            
    
    #Image.fromarray(nk).show()
    
    vkUnmapMemory(device, dstImageMemory)
    vkFreeMemory(device, dstImageMemory, None)
    vkDestroyImage(device, dstImage, None)
    
    return n[y][x]
    #dta = Image.frombuffer("RGBA", (swapChainExtent.width, swapChainExtent.height), pb, 'raw', "RGBA", 0, 1)
    
    #Image.fromarray(nn).show()
    #dta.show()
    #dta.save('gfg_dummy_pic.png')