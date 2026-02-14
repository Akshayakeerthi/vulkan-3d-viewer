from vulkan import *

def beginSingleTimeCommands(device, commandPool):
    
    allocInfo = VkCommandBufferAllocateInfo(
        level              = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
        commandPool        = commandPool,
        commandBufferCount = 1
    )
    
    commandBuffer = vkAllocateCommandBuffers(device, allocInfo)[0]
    beginInfo = VkCommandBufferBeginInfo(flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT)
    vkBeginCommandBuffer(commandBuffer, beginInfo)
    
    return commandBuffer
    
def endSingleTimeCommands(commandBuffer, device, commandPool, graphicQueue):
    
    vkEndCommandBuffer(commandBuffer)
    
    submitInfo = VkSubmitInfo(pCommandBuffers = [commandBuffer])
    
    vkQueueSubmit(graphicQueue, 1, [submitInfo], VK_NULL_HANDLE)
    vkQueueWaitIdle(graphicQueue)
    
    vkFreeCommandBuffers(device, commandPool, 1, [commandBuffer])
    
def copyBuffer(src, dst, bufferSize, device, commandPool, graphicQueue):
    
    commandBuffer = beginSingleTimeCommands(device, commandPool)
    
    # copyRegion = VkBufferCopy(size=bufferSize)
    copyRegion = VkBufferCopy(0, 0, bufferSize)
    vkCmdCopyBuffer(commandBuffer, src, dst, 1, [copyRegion])
    
    endSingleTimeCommands(commandBuffer, device, commandPool, graphicQueue)
    
def createBuffer(size, usage, properties, device, physicalDevice):
    
    buffer = None
    bufferMemory = None
    
    bufferInfo = VkBufferCreateInfo(
        size        = size,
        usage       = usage,
        sharingMode = VK_SHARING_MODE_EXCLUSIVE
    )
    
    buffer = vkCreateBuffer(device, bufferInfo, None)
    
    memRequirements = vkGetBufferMemoryRequirements(device, buffer)
    pNext = None
    
    if False:
        if usage & VK_BUFFER_USAGE_SHADER_DEVICE_ADDRESS_BIT:
            allocFlagsInfo = VkMemoryAllocateFlagsInfoKHR(
                sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_FLAGS_INFO_KHR,
                flags = VK_MEMORY_ALLOCATE_DEVICE_ADDRESS_BIT_KHR
            )
            
            pNext = allocFlagsInfo
            
    allocInfo = VkMemoryAllocateInfo(
        pNext           = pNext,
        allocationSize  = memRequirements.size,
        memoryTypeIndex = findMemoryType(memRequirements.memoryTypeBits, properties, physicalDevice)
    )
    
    bufferMemory = vkAllocateMemory(device, allocInfo, None)
    vkBindBufferMemory(device, buffer, bufferMemory, 0)
    
    return (buffer, bufferMemory)

def findMemoryType(typeFilter, properties, physicalDevice):
    
    memProperties = vkGetPhysicalDeviceMemoryProperties(physicalDevice)
    
    for i, prop in enumerate(memProperties.memoryTypes):
        if (typeFilter & (1 << i)) and ((prop.propertyFlags & properties) == properties):
            return i
    
    return -1