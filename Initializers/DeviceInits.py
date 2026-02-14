from vulkan import *
from utils import *

enableValidationLayers = True
validationLayers = ['VK_LAYER_LUNARG_standard_validation']
deviceExtensions = [VK_KHR_SWAPCHAIN_EXTENSION_NAME]

class InstanceProcAddr(object):
    T = None

    def __init__(self, func):
        self.__func = func

    def __call__(self, *args, **kwargs):
        funcName = self.__func.__name__
        func = InstanceProcAddr.procfunc(funcName)
        if func:
            return func(*args, **kwargs)
        else:
            return VK_ERROR_EXTENSION_NOT_PRESENT

    @staticmethod
    def procfunc(funcName):
        return vkGetInstanceProcAddr(InstanceProcAddr.T, funcName)

# instance ext functions
@InstanceProcAddr
def vkCreateDebugReportCallbackEXT(instance, pCreateInfo, pAllocator):
    pass


@InstanceProcAddr
def vkDestroyDebugReportCallbackEXT(instance, pCreateInfo, pAllocator):
    pass


@InstanceProcAddr
def vkCreateWin32SurfaceKHR(instance, pCreateInfo, pAllocator):
    pass


@InstanceProcAddr
def vkDestroySurfaceKHR(instance, surface, pAllocator):
    pass


@InstanceProcAddr
def vkGetPhysicalDeviceSurfaceSupportKHR(physicalDevice, queueFamilyIndex, surface):
    pass


@InstanceProcAddr
def vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physicalDevice, surface):
    pass


@InstanceProcAddr
def vkGetPhysicalDeviceSurfaceFormatsKHR(physicalDevice, surface):
    pass


@InstanceProcAddr
def vkGetPhysicalDeviceSurfacePresentModesKHR(physicalDevice, surface):
    pass

class DeviceProcAddr(InstanceProcAddr):

    @staticmethod
    def procfunc(funcName):
        return vkGetDeviceProcAddr(InstanceProcAddr.T, funcName)


# device ext functions
@DeviceProcAddr
def vkCreateSwapchainKHR(device, pCreateInfo, pAllocator):
    pass

@DeviceProcAddr
def vkDestroySwapchainKHR(device, swapchain, pAllocator):
    pass

@DeviceProcAddr
def vkGetSwapchainImagesKHR(device, swapchain):
    pass

@DeviceProcAddr
def vkAcquireNextImageKHR(device, swapchain, timeout, semaphore, fence):
    pass

@DeviceProcAddr
def vkQueuePresentKHR(queue, pPresentInfo):
    pass

@DeviceProcAddr
def vkGetBufferDeviceAddressKHR(device, pInfo):
    pass


def debugCallback(*args):
    print('DEBUG: {} {}'.format(args[5], args[6]))
    return 0

class Win32misc(object):
    @staticmethod
    def getInstance(hWnd):
        from cffi import FFI as _FFI
        _ffi = _FFI()
        _ffi.cdef('long __stdcall GetWindowLongA(void* hWnd, int nIndex);')
        _lib = _ffi.dlopen('User32.dll')
        return _lib.GetWindowLongA(_ffi.cast('void*', hWnd), -6)  # GWL_HINSTANCE
    
class QueueFamilyIndices(object):

    def __init__(self):
        self.graphicsFamily = -1
        self.presentFamily = -1

    @property
    def isComplete(self):
        return self.graphicsFamily >= 0 and self.presentFamily >= 0

class SwapChainSupportDetails(object):

    def __init__(self):
        self.capabilities = None
        self.formats = None
        self.presentModes = None


class Device:
    
    def __init__(self, winId):
        self.__cretaeInstance()
        self.__setupDebugCallback()
        self.__createSurface(winId)
        self.__pickPhysicalDevice()
        self.__createLogicalDevice()
        self.__createCommandPool()
    
    def __cretaeInstance(self):
        
        if enableValidationLayers and not self.__checkValidationLayerSupport():
            raise Exception("validation layers requested, but not available!")
        
        appInfo = VkApplicationInfo(
            #sType             = VK_STRUCTURE_TYPE_APPLICATION_INFO,
            pApplicationName   ='Python VK',
            applicationVersion = VK_MAKE_VERSION(1, 0, 0),
            pEngineName        = 'pyvulkan',
            engineVersion      = VK_MAKE_VERSION(1, 0, 0),
            apiVersion         = VK_API_VERSION
        )
        
        extenstions = self.__getRequiredExtensions()
        
        if enableValidationLayers:
            instanceInfo = VkInstanceCreateInfo(
                pApplicationInfo        = appInfo,
                # enabledLayerCount     = len(validationLayers),
                ppEnabledLayerNames     = validationLayers,
                # enabledExtensionCount = len(extenstions),
                ppEnabledExtensionNames = extenstions
            )
        else:
            instanceInfo = VkInstanceCreateInfo(
                pApplicationInfo        = appInfo,
                enabledLayerCount       = 0,
                # enabledExtensionCount = len(extenstions),
                ppEnabledExtensionNames = extenstions
            )
        
        self.instance = vkCreateInstance(instanceInfo, None)
        
        InstanceProcAddr.T = self.instance
    
    def __setupDebugCallback(self):
        
        if not enableValidationLayers:
            return
        
        createInfo = VkDebugReportCallbackCreateInfoEXT(
            flags       = VK_DEBUG_REPORT_WARNING_BIT_EXT | VK_DEBUG_REPORT_ERROR_BIT_EXT,
            pfnCallback = debugCallback
        )
        
        self.callbcak = vkCreateDebugReportCallbackEXT(self.instance, createInfo, None)
    
    def __createSurface(self, winId):
        
        if sys.platform == 'win32':
            hwnd       = winId
            hinstance  = Win32misc.getInstance(hwnd)
            
            createInfo = VkWin32SurfaceCreateInfoKHR(hinstance = hinstance, hwnd = hwnd)
            
            self.surface = vkCreateWin32SurfaceKHR(self.instance, createInfo, None)
        # elif sys.platform == 'linux':
        #     pass
    
    def __pickPhysicalDevice(self):
        
        physicalDevices = vkEnumeratePhysicalDevices(self.instance)
        
        for device in physicalDevices:
            if self.__isDeviceSuitable(device):
                self.physicalDevice = device
                break
        
        assert self.physicalDevice != None
    
    def __createLogicalDevice(self):
        
        indices = self.findQueueFamilies(self.physicalDevice)
        
        uniqueQueueFamilies = {}.fromkeys([indices.graphicsFamily, indices.presentFamily])
        queueCreateInfos = []
        
        for i in uniqueQueueFamilies:
            queueCreateInfo = VkDeviceQueueCreateInfo(
                queueFamilyIndex = i,
                queueCount       = 1,
                pQueuePriorities = [1.0]
            )
            queueCreateInfos.append(queueCreateInfo)
        
        deviceFeatures = VkPhysicalDeviceFeatures()
        deviceFeatures.samplerAnisotropy = True
        
        if enableValidationLayers:
            createInfo = VkDeviceCreateInfo(
                # queueCreateInfoCount  = len(queueCreateInfos),
                pQueueCreateInfos       = queueCreateInfos,
                # enabledExtensionCount = len(deviceExtensions),
                ppEnabledExtensionNames = deviceExtensions,
                # enabledLayerCount     = len(validationLayers),
                ppEnabledLayerNames     = validationLayers,
                pEnabledFeatures        = deviceFeatures
            )
        else:
            createInfo = VkDeviceCreateInfo(
                queueCreateInfoCount    = 1,
                pQueueCreateInfos       = queueCreateInfo,
                # enabledExtensionCount = len(deviceExtensions),
                ppEnabledExtensionNames = deviceExtensions,
                enabledLayerCount       = 0,
                pEnabledFeatures        = deviceFeatures
            )
        
        self.device = vkCreateDevice(self.physicalDevice, createInfo, None)
        
        DeviceProcAddr.T = self.device
        
        self.graphicQueue = vkGetDeviceQueue(self.device, indices.graphicsFamily, 0)
        self.presentQueue = vkGetDeviceQueue(self.device, indices.presentFamily, 0)
        
    def __createCommandPool(self):
        
        queueFamilyIndices = self.findQueueFamilies(self.physicalDevice)
        
        createInfo = VkCommandPoolCreateInfo(queueFamilyIndex = queueFamilyIndices.graphicsFamily,
                                             flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT)
        
        self.commandPool = vkCreateCommandPool(self.device, createInfo, None)
    
    def __getRequiredExtensions(self):
        
        extenstions = [e.extensionName for e in vkEnumerateInstanceExtensionProperties(None)]
        
        if enableValidationLayers:
            extenstions.append(VK_EXT_DEBUG_REPORT_EXTENSION_NAME)
        
        return extenstions
    
    def __checkValidationLayerSupport(self):
        
        availableLayers = vkEnumerateInstanceLayerProperties()
        
        for layer in validationLayers:
            layerfound = False
            
            for layerProp in availableLayers:
                if layer == layerProp.layerName:
                    layerfound = True
                    break
            return layerfound
        
        return False
    
    def __isDeviceSuitable(self, device):
        
        indices = self.findQueueFamilies(device)
        
        extensionsSupported = self.__checkDeviceExtensionSupport(device)
        swapChainAdequate = False
        
        if extensionsSupported:
            swapChainSupport = self.querySwapChainSupport(device)
            swapChainAdequate = (swapChainSupport.formats is not None) and (swapChainSupport.presentModes is not None)
        
        supportedFeatures = vkGetPhysicalDeviceFeatures(device)
        
        return indices.isComplete and extensionsSupported and swapChainAdequate and supportedFeatures.samplerAnisotropy
    
    def __checkDeviceExtensionSupport(self, device):
        
        availableExtensions = vkEnumerateDeviceExtensionProperties(device, None)
        aen = [i.extensionName for i in availableExtensions]
        
        for i in deviceExtensions:
            if i not in aen:
                return False
        
        return True
    
    def findQueueFamilies(self, device):
        
        indices = QueueFamilyIndices()
        familyProperties = vkGetPhysicalDeviceQueueFamilyProperties(device)
        
        for i, prop in enumerate(familyProperties):
            if prop.queueCount > 0 and prop.queueFlags & VK_QUEUE_GRAPHICS_BIT:
                indices.graphicsFamily = i
            
            presentSupport = vkGetPhysicalDeviceSurfaceSupportKHR(device, i, self.surface)
            
            if prop.queueCount > 0 and presentSupport:
                indices.presentFamily = i
            
            if indices.isComplete:
                break
        
        return indices
    
    def querySwapChainSupport(self, device):
        
        detail = SwapChainSupportDetails()
        
        detail.capabilities = vkGetPhysicalDeviceSurfaceCapabilitiesKHR(device, self.surface)
        detail.formats = vkGetPhysicalDeviceSurfaceFormatsKHR(device, self.surface)
        detail.presentModes = vkGetPhysicalDeviceSurfacePresentModesKHR(device, self.surface)
        
        return detail
    
    