from vulkan import *
import numpy as np

def createShaderModule(device, shaderFile):
    
    with open(shaderFile, 'rb') as sf:
        code = sf.read()
        
        createInfo = VkShaderModuleCreateInfo(
            codeSize = len(code),
            pCode    = code
        )
        
        return vkCreateShaderModule(device, createInfo, None)

class Vertex(object):

    POS = np.array([0, 0, 0], np.float32)
    COLOR = np.array([0, 0, 0], np.float32)
    NORMAL = np.array([0, 0, 0], np.float32)
    TEXCOORD = np.array([0, 0], np.float32)
    
    @staticmethod
    def getBindingDescription():
        return VkVertexInputBindingDescription(
            binding        = 0,
            stride         = Vertex.POS.nbytes + Vertex.COLOR.nbytes + Vertex.NORMAL.nbytes + Vertex.TEXCOORD.nbytes,
            inputRate      = VK_VERTEX_INPUT_RATE_VERTEX
            )
        

    @staticmethod
    def getAttributeDescriptions():
        
        pos = VkVertexInputAttributeDescription(
            location = 0,
            binding  = 0,
            format   = VK_FORMAT_R32G32B32_SFLOAT,
            offset   = 0
        )
        
        color = VkVertexInputAttributeDescription(
            location = 1,
            binding  = 0,
            format   = VK_FORMAT_R32G32B32_SFLOAT,
            offset   = Vertex.POS.nbytes,
        )
        
        normal = VkVertexInputAttributeDescription(
            location = 2,
            binding  = 0,
            format   = VK_FORMAT_R32G32B32_SFLOAT,
            offset   = Vertex.POS.nbytes+Vertex.COLOR.nbytes,
        )
        
        texcoord = VkVertexInputAttributeDescription(
            location = 3,
            binding  = 0,
            format   = VK_FORMAT_R32G32_SFLOAT,
            offset   = Vertex.POS.nbytes+Vertex.COLOR.nbytes+Vertex.NORMAL.nbytes,
        )
        
        objid = VkVertexInputAttributeDescription(
            location = 4,
            binding  = 0,
            format   = VK_FORMAT_R32_SFLOAT,
            offset   = Vertex.POS.nbytes+Vertex.COLOR.nbytes+Vertex.NORMAL.nbytes+Vertex.TEXCOORD.nbytes,
        )
        
        return [pos, color, normal, texcoord]
        
    
def cRenderPass(device, StageMask, msaaSamples, depthFormat, accumFormat, revealageFormat):
    
    colorAttachment1 = VkAttachmentDescription(
        format         = accumFormat,
        samples        = msaaSamples,
        loadOp         = VK_ATTACHMENT_LOAD_OP_CLEAR,
        storeOp        = VK_ATTACHMENT_STORE_OP_STORE,
        stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED,
        finalLayout    = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL
    )
    
    colorAttachment2 = VkAttachmentDescription(
        format         = revealageFormat,
        samples        = msaaSamples,
        loadOp         = VK_ATTACHMENT_LOAD_OP_CLEAR,
        storeOp        = VK_ATTACHMENT_STORE_OP_STORE,
        stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED,
        finalLayout    = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL
    )
    
    msaaAttachment1 = VkAttachmentDescription(
        format         = accumFormat,
        samples        = VK_SAMPLE_COUNT_1_BIT,
        loadOp         = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        storeOp        = VK_ATTACHMENT_STORE_OP_STORE,
        stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED,
        finalLayout    = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR
    )
    
    msaaAttachment2 = VkAttachmentDescription(
        format         = revealageFormat,
        samples        = VK_SAMPLE_COUNT_1_BIT,
        loadOp         = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        storeOp        = VK_ATTACHMENT_STORE_OP_STORE,
        stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED,
        finalLayout    = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR
    )
    
    depthAttachment = VkAttachmentDescription(
        format         = depthFormat,
        samples        = msaaSamples,
        loadOp         = VK_ATTACHMENT_LOAD_OP_CLEAR,
        storeOp        = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED,
        finalLayout    = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
    )
    
    colorAttachmentRef1 = VkAttachmentReference(0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL)
    colorAttachmentRef2 = VkAttachmentReference(1, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL)
    msaaAttachmentRef1 = VkAttachmentReference(2, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL)
    msaaAttachmentRef2 = VkAttachmentReference(3, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL)
    depthAttachmentRef = VkAttachmentReference(4, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL)
    
    subpass = VkSubpassDescription(
        pipelineBindPoint       = VK_PIPELINE_BIND_POINT_GRAPHICS,
        pResolveAttachments     = [msaaAttachmentRef1, msaaAttachmentRef2],
        pColorAttachments       = [colorAttachmentRef1, colorAttachmentRef2],
        pDepthStencilAttachment = [depthAttachmentRef]
    )
    
    dependency = VkSubpassDependency(
        srcSubpass    = VK_SUBPASS_EXTERNAL,
        dstSubpass    = 0,
        srcStageMask  = StageMask,
        srcAccessMask = 0,
        dstStageMask  = StageMask,
        dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT | VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT
    )
    
    renderPassInfo = VkRenderPassCreateInfo(
        pAttachments  = [colorAttachment1, colorAttachment2, msaaAttachment1, msaaAttachment2, depthAttachment],
        pSubpasses    = [subpass],
        pDependencies = [dependency]
    )
    
    return vkCreateRenderPass(device, renderPassInfo, None)

def createGraphicsPipeline(device, blend, msaaSamples, renderpass, swapChainExtent, descriptorSetLayout, s_path, grid = False, name = 'SwapChain'):
    
    vertexShaderMode = createShaderModule(device, s_path[0])
    fragmentShaderMode = createShaderModule(device, s_path[1])
    
    vertexShaderStageInfo = VkPipelineShaderStageCreateInfo(
        stage  = VK_SHADER_STAGE_VERTEX_BIT,
        module = vertexShaderMode,
        pName  = 'main'
    )
    
    fragmentShaderStageInfo = VkPipelineShaderStageCreateInfo(
        stage  = VK_SHADER_STAGE_FRAGMENT_BIT,
        module = fragmentShaderMode,
        pName  = 'main'
    )
    
    shaderStageInfos = [vertexShaderStageInfo, fragmentShaderStageInfo]
    
    if grid:
        vertexInputInfo = VkPipelineVertexInputStateCreateInfo(
            vertexBindingDescriptionCount    = 0,
            #pVertexBindingDescriptions        = [bindingDescription],
             vertexAttributeDescriptionCount = 0,
            #pVertexAttributeDescriptions      = attributeDescription,
        )
    else:
        bindingDescription = Vertex.getBindingDescription()
        attributeDescription = Vertex.getAttributeDescriptions()
        
        vertexInputInfo = VkPipelineVertexInputStateCreateInfo(
            #vertexBindingDescriptionCount    = 0,
            pVertexBindingDescriptions        = [bindingDescription],
            # vertexAttributeDescriptionCount = 0,
            pVertexAttributeDescriptions      = attributeDescription,
        )
    
    
    
    inputAssembly = VkPipelineInputAssemblyStateCreateInfo(
        topology               = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
        primitiveRestartEnable = False
    )
    
    viewport = VkViewport(0.0, 0.0, float(swapChainExtent.width), float(swapChainExtent.height), 0.0, 1.0)
    
    scissor = VkRect2D([0, 0], swapChainExtent)
    viewportStage = VkPipelineViewportStateCreateInfo(
        viewportCount = 1,
        pViewports    = viewport,
        scissorCount  = 1,
        pScissors     = scissor
    )
    
    rasterizer = VkPipelineRasterizationStateCreateInfo(
        depthClampEnable        = False,
        rasterizerDiscardEnable = False,
        polygonMode             = VK_POLYGON_MODE_FILL,
        lineWidth               = 1.0,
        cullMode                = VK_CULL_MODE_NONE,#BACK_BIT
        frontFace               = VK_FRONT_FACE_CLOCKWISE,
        depthBiasEnable         = False,
    )
    
    multisampling = VkPipelineMultisampleStateCreateInfo(
        sampleShadingEnable  = False,
        rasterizationSamples = msaaSamples
    )
    
    depthStencil = VkPipelineDepthStencilStateCreateInfo(
        depthTestEnable       = True,
        depthWriteEnable      = True,
        depthCompareOp        = VK_COMPARE_OP_LESS_OR_EQUAL,
        depthBoundsTestEnable = False,
        stencilTestEnable     = False
    )
    
    colorBlendAttachment = VkPipelineColorBlendAttachmentState(
        colorWriteMask      = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT | VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT,
        blendEnable         = blend,
        srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA,
        dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA,
        colorBlendOp        = VK_BLEND_OP_ADD,
        srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE,
        dstAlphaBlendFactor = VK_BLEND_FACTOR_ZERO,
        alphaBlendOp        = VK_BLEND_OP_ADD
    )
    
    colorBending = VkPipelineColorBlendStateCreateInfo(
        logicOpEnable   = False,
        logicOp         = VK_LOGIC_OP_COPY,
        attachmentCount = 1,
        pAttachments    = colorBlendAttachment,
        #blendConstants  = [1.0, 0.0, 0.0, 0.0]
    )
    
    dynamicState = VkPipelineDynamicStateCreateInfo(
        dynamicStateCount = 1,
        pDynamicStates    = [VK_DYNAMIC_STATE_SCISSOR]
    )
    
    pushConst_Range = VkPushConstantRange(stageFlags = VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT,
                                         offset = 0,
                                         size = 2*4*4*4)
    
    pipelineLayoutInfo = VkPipelineLayoutCreateInfo(
        #setLayoutCount        = 0,
        pushConstantRangeCount = 1,
        pPushConstantRanges    = [pushConst_Range],
        pSetLayouts            = [descriptorSetLayout]
    )
    
    pipelineLayout = vkCreatePipelineLayout(device, pipelineLayoutInfo, None)
    
    pipelineInfo = VkGraphicsPipelineCreateInfo(
        #stageCount         = len(shaderStageInfos),
        pStages             = shaderStageInfos,
        pVertexInputState   = vertexInputInfo,
        pInputAssemblyState = inputAssembly,
        pViewportState      = viewportStage,
        pRasterizationState = rasterizer,
        pMultisampleState   = multisampling,
        pColorBlendState    = colorBending,
        pDepthStencilState  = depthStencil,
        layout              = pipelineLayout,
        renderPass          = renderpass,
        subpass             = 0,
        pDynamicState       = dynamicState,
        basePipelineHandle  = VK_NULL_HANDLE
    )
    
    pipeline = vkCreateGraphicsPipelines(device, VK_NULL_HANDLE, 1, pipelineInfo, None)[0]
    
    vkDestroyShaderModule(device, vertexShaderMode, None)
    vkDestroyShaderModule(device, fragmentShaderMode, None)
    
    return pipelineLayout, pipeline
