from vulkan import *
from Initializers.copyops import *

def createBottomLevelAccelerationStructure(device, logicalDevice, commandPool, graphicQueue, vertices, stride, indices, numTriangles, maxVertex = 3):

    #Instead of a simple triangle, we'll be loading a more complex scene for this example
    #The shaders are accessing the vertex and index buffers of the scene, so the proper usage flag has to be set on the vertex and index buffers for the scene
    print('on')
    vertices = VkBufferDeviceAddressInfoKHR(
        sType = VK_STRUCTURE_TYPE_BUFFER_DEVICE_ADDRESS_INFO, 
        buffer = vertices
    )
    print('yep')
    vert_dAdrs = vkGetBufferDeviceAddressKHR(logicalDevice, vertices)
    print(vert_dAdrs)
    
    VkBufferDeviceAddressInfoKHR = vkGetDeviceProcAddr(logicalDevice, 'VkBufferDeviceAddressInfoKHR')
    
    indiaces = VkBufferDeviceAddressInfoKHR(
        sType = VK_STRUCTURE_TYPE_BUFFER_DEVICE_ADDRESS_INFO, 
        buffer = indiaces
    )
    
    ind_dAdrs = vkGetBufferDeviceAddressKHR(logicalDevice, indiaces)
    
    tri = VkAccelerationStructureGeometryTrianglesDataKHR(
        sType         = VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_TRIANGLES_DATA_KHR,
        vertexFormat  = VK_FORMAT_R32G32B32_SFLOAT,
        vertexData    = vert_dAdrs,
        maxVertex     = maxVertex,
        vertexStride  = stride,
        indexType     = VK_INDEX_TYPE_UINT32,
        indexData     = ind_dAdrs,
        transformData = VkDeviceOrHostAddressConstKHR(0, None)
    )
    
    triangles = VkAccelerationStructureGeometryDataKHR(
        triangles = tri
    )
    
    accelerationStructureGeometry = VkAccelerationStructureGeometryKHR(
        flags        = VK_GEOMETRY_OPAQUE_BIT_KHR,
        geometryType = VK_GEOMETRY_TYPE_TRIANGLES_KHR,
        geometry     = triangles
    )
    
    accelerationStructureBuildGeometryInfo = VkAccelerationStructureBuildGeometryInfoKHR(
        sType         = VK_ACCELERATION_STRUCTURE_TYPE_BOTTOM_LEVEL_KHR,
        flags         = VK_BUILD_ACCELERATION_STRUCTURE_PREFER_FAST_TRACE_BIT_KHR,
        geometryCount = 1,
        pGeometries   = accelerationStructureGeometry
    )
    
    accelerationStructureBuildSizesInfo = VkAccelerationStructureBuildSizesInfoKHR()
    print('yepp')
    vkGetAccelerationStructureBuildSizesKHR(
        device, VK_ACCELERATION_STRUCTURE_BUILD_TYPE_DEVICE_KHR,
        accelerationStructureBuildGeometryInfo, numTriangles, accelerationStructureBuildSizesInfo)
    
    bottomLevelAS = createAccelerationStructure(VK_ACCELERATION_STRUCTURE_TYPE_BOTTOM_LEVEL_KHR, 
                                                accelerationStructureBuildSizesInfo, logicalDevice)
    
    #Create a small scratch buffer used during build of the bottom level acceleration structure
    scratchBuffer = createScratchBuffer(accelerationStructureBuildSizesInfo.buildScratchSize, logicalDevice);
    
    divAdrs = VkDeviceOrHostAddressKHR(
        deviceAddress = scratchBuffer.deviceAddress
    )
    
    accelerationBuildGeometryInfo = VkAccelerationStructureBuildGeometryInfoKHR(
        sType                     = VK_ACCELERATION_STRUCTURE_TYPE_BOTTOM_LEVEL_KHR,
        flags                     = VK_BUILD_ACCELERATION_STRUCTURE_PREFER_FAST_TRACE_BIT_KHR,
        mode                      = VK_BUILD_ACCELERATION_STRUCTURE_MODE_BUILD_KHR,
        dstAccelerationStructure  = bottomLevelAS.handle,
        geometryCount             = 1,
        pGeometries               = accelerationStructureGeometry,
        scratchData               = divAdrs
    )
    
    accelerationStructureBuildRangeInfo = VkAccelerationStructureBuildRangeInfoKHR(
        primitiveCount  = numTriangles,
        primitiveOffset = 0,
        firstVertex     = 0,
        transformOffset = 0
    )
    #std::vector<VkAccelerationStructureBuildRangeInfoKHR*> accelerationBuildStructureRangeInfos = { &accelerationStructureBuildRangeInfo };
    
    #Build the acceleration structure on the device via a one-time command buffer submission
    #Some implementations may support acceleration structure building on the host (VkPhysicalDeviceAccelerationStructureFeaturesKHR->accelerationStructureHostCommands), but we prefer device builds
    commandBuffer = beginSingleTimeCommands(device, commandPool)
    
    vkCmdBuildAccelerationStructuresKHR(
        commandBuffer,
        1,
        accelerationBuildGeometryInfo,
        #accelerationBuildStructureRangeInfos.data())
        accelerationStructureBuildRangeInfo
    )
    
    endSingleTimeCommands(commandBuffer, device, commandPool, graphicQueue)
    print('yeppp')
    return bottomLevelAS
    
    #deleteScratchBuffer(scratchBuffer)
    
    #'''
    #    The top level acceleration structure contains the scene's object instances
    #'''
    
def createTopLevelAccelerationStructure(device, physicalDevice, bottomLevelAS):
    
    transformMatrix = VkTransformMatrixKHR(
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0)
    
    instance = VkAccelerationStructureInstanceKHR(
        transform                              = transformMatrix,
        instanceCustomIndex                    = 0,
        mask                                   = 0xFF,
        instanceShaderBindingTableRecordOffset = 0,
        flags                                  = VK_GEOMETRY_INSTANCE_TRIANGLE_FACING_CULL_DISABLE_BIT_KHR,
        accelerationStructureReference         = bottomLevelAS.deviceAddress
    )
    print(len(instance))
    #Buffer for instance data
    instancesBuffer = createBuffer(sizeof(instance),
                 VK_BUFFER_USAGE_SHADER_DEVICE_ADDRESS_BIT | VK_BUFFER_USAGE_ACCELERATION_STRUCTURE_BUILD_INPUT_READ_ONLY_BIT_KHR,
                 VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
                 device, physicalDevice#, instance
    )
    
    instanceDataDeviceAddress = VkDeviceOrHostAddressConstKHR(
        deviceAddress = getBufferDeviceAddress(instancesBuffer.buffer, logicalDevice)
    )
    
    inst = VkAccelerationStructureGeometryInstancesDataKHR(
        sType           = VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_INSTANCES_DATA_KHR,
        arrayOfPointers = VK_FALSE,
        data            = instanceDataDeviceAddress
    )
    
    geo = VkAccelerationStructureGeometryDataKHR(
        instances = inst
    )
    
    accelerationStructureGeometry = VkAccelerationStructureGeometryKHR(
        geometryType = VK_GEOMETRY_TYPE_INSTANCES_KHR,
        flags        = VK_GEOMETRY_OPAQUE_BIT_KHR,
        geometry     = geo
    )
    
    #Get size info
    accelerationStructureBuildGeometryInfo = VkAccelerationStructureBuildGeometryInfoKHR(
        sType         = VK_ACCELERATION_STRUCTURE_TYPE_TOP_LEVEL_KHR,
        flags         = VK_BUILD_ACCELERATION_STRUCTURE_PREFER_FAST_TRACE_BIT_KHR,
        geometryCount = 1,
        pGeometries   = accelerationStructureGeometry
    )
    primitive_count = 1;
    
    accelerationStructureBuildSizesInfo = VkAccelerationStructureBuildSizesInfoKHR()
    
    vkGetAccelerationStructureBuildSizesKHR(
        device,
        VK_ACCELERATION_STRUCTURE_BUILD_TYPE_DEVICE_KHR,
        accelerationStructureBuildGeometryInfo,
        primitive_count,
        accelerationStructureBuildSizesInfo
    )
    
    #@todo: as return value?
    topLevelAS = createAccelerationStructure(VK_ACCELERATION_STRUCTURE_TYPE_TOP_LEVEL_KHR, 
                                             accelerationStructureBuildSizesInfo, logicalDevice)
    
    #Create a small scratch buffer used during build of the top level acceleration structure
    scratchBuffer = createScratchBuffer(accelerationStructureBuildSizesInfo.buildScratchSize, logicalDevice);
    
    divAdrs = VkDeviceOrHostAddressKHR(
        deviceAddress = scratchBuffer.deviceAddress
    )
    
    accelerationBuildGeometryInfo = VkAccelerationStructureBuildGeometryInfoKHR(
        sType                    = VK_ACCELERATION_STRUCTURE_TYPE_TOP_LEVEL_KHR,
        flags                    = VK_BUILD_ACCELERATION_STRUCTURE_PREFER_FAST_TRACE_BIT_KHR,
        mode                     = VK_BUILD_ACCELERATION_STRUCTURE_MODE_BUILD_KHR,
        dstAccelerationStructure = topLevelAS.handle,
        geometryCount            = 1,
        pGeometries              = accelerationStructureGeometry,
        scratchData              = divAdrs
    )
    
    accelerationStructureBuildRangeInfo = VkAccelerationStructureBuildRangeInfoKHR(
        primitiveCount  = 1,
        primitiveOffset = 0,
        firstVertex     = 0,
        transformOffset = 0,
    )
        #std::vector<VkAccelerationStructureBuildRangeInfoKHR*> accelerationBuildStructureRangeInfos = { &accelerationStructureBuildRangeInfo }
    
    #Build the acceleration structure on the device via a one-time command buffer submission
    #Some implementations may support acceleration structure building on the host (VkPhysicalDeviceAccelerationStructureFeaturesKHR->accelerationStructureHostCommands), but we prefer device builds
    commandBuffer = beginSingleTimeCommands(device, commandPool)
    
    vkCmdBuildAccelerationStructuresKHR(
        commandBuffer,
        1,
        accelerationBuildGeometryInfo,
        accelerationStructureBuildRangeInfo
    )
    
    endSingleTimeCommands(commandBuffer, device, commandPool, graphicQueue)
    
    vkFreeMemory(logicalDevice, scratchBuffer.memory, None)
    vkDestroyBuffer(logicalDevice, scratchBuffer.handle, None)
    
    instancesBuffer.destroy()
    
def createAccelerationStructure(type, acStructBSInfo, logicalDevice):
    
    bLAS = BTLevelAS()
    #######       Buffer and memory
    bufferCreateInfo = VkBufferCreateInfo(
        sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
        size = acStructBSInfo.accelerationStructureSize,
        usage = VK_BUFFER_USAGE_ACCELERATION_STRUCTURE_STORAGE_BIT_KHR | VK_BUFFER_USAGE_SHADER_DEVICE_ADDRESS_BIT
    )
    
    bLAS.buffer = vkCreateBuffer(logicalDevice, bufferCreateInfo, None)
    
    memoryRequirements = VkMemoryRequirements(
        sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_FLAGS_INFO,
        flags = VK_MEMORY_ALLOCATE_DEVICE_ADDRESS_BIT_KHR
    )
    ######
    memoryAllocateInfo = VkMemoryAllocateInfo(
        sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        pNext = memoryAllocateFlagsInfo,
        allocationSize = memoryRequirements.size,
        memoryTypeIndex = getMemoryType(memoryRequirements.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT)
    )
    ######
    bLAS.memory = vkAllocateMemory(logicalDevice, memoryAllocateInfo, None)
    vkBindBufferMemory(logicalDevice, bLAS.buffer, bLAS.memory, 0)
    
    #######      Acceleration structure
    accelerationStructureCreate_info = VkAccelerationStructureCreateInfoKHR(
        sType = VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_CREATE_INFO_KHR,
        size = acStructBSInfo.accelerationStructureSize,
        type = type,
    )
    
    bLAS.handle = vkCreateAccelerationStructureKHR(logicalDevice, accelerationStructureCreate_info, None)
    
    accelerationDeviceAddressInfo = VkAccelerationStructureDeviceAddressInfoKHR(
        sType = VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_DEVICE_ADDRESS_INFO_KHR,
        accelerationStructure = bLAS.handle
    )
    
    bLAS.deviceAddress = vkGetAccelerationStructureDeviceAddressKHR(logicalDevice, accelerationDeviceAddressInfo)


def createScratchBuffer(size, logicalDevice):
    
    scratchBuffer = BTLevelAS()
    
    bufferCreateInfo = VkBufferCreateInfo(
        sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
        size  = size, 
        usage = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_SHADER_DEVICE_ADDRESS_BIT
    )
    
    scratchBuffer.handle = vkCreateBuffer(logicalDevice, bufferCreateInfo, None)
    
    #memoryRequirements = VkMemoryRequirements()
    memoryRequirements = vkGetBufferMemoryRequirements(logicalDevice, scratchBuffer.handle)
    
    memoryAllocateFlagsInfo = VkMemoryAllocateFlagsInfo(
        sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_FLAGS_INFO,
        flags = VK_MEMORY_ALLOCATE_DEVICE_ADDRESS_BIT_KHR
    )
    
    memoryAllocateInfo = VkMemoryAllocateInfo(
        sType           = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        pNext           = memoryAllocateFlagsInfo,
        allocationSize  = memoryRequirements.size,
        memoryTypeIndex = getMemoryType(memoryRequirements.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT)
    )
    
    scratchBuffer.memory = vkAllocateMemory(logicalDevice, memoryAllocateInfo, None)
    vkBindBufferMemory(logicalDevice, scratchBuffer.handle, scratchBuffer.memory, 0)
    
    bufferDeviceAddresInfo = VkBufferDeviceAddressInfoKHR(
        sType = VK_STRUCTURE_TYPE_BUFFER_DEVICE_ADDRESS_INFO, 
        buffer = scratchBuffer.handle
    )
    
    scratchBuffer.deviceAddress = vkGetBufferDeviceAddressKHR(logicalDevice, bufferDeviceAddresInfo)
    
    return scratchBuffer
    
class BTLevelAS:
    
    buffer = None
    memory = None
    handle = None
    deviceAddress = None


def getBufferDeviceAddress(buffer, logicalDevice):
    
    bufferDeviceAI = VkBufferDeviceAddressInfoKHR(
        sType = VK_STRUCTURE_TYPE_BUFFER_DEVICE_ADDRESS_INFO,
        buffer = buffer
    )
    
    return vkGetBufferDeviceAddressKHR(logicalDevice, bufferDeviceAI)



















