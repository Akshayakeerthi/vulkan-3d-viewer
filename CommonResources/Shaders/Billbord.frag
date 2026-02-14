#version 450
//#extension GL_ARB_seperate_shader_objects : enable

layout(location = 0) in vec2 offset;
 
layout(location = 0) out vec4 outColor;

struct Light {
    vec4 posAtype;
    vec4 clrAint;
    vec2 rdsAamb;
};

layout(binding = 0) uniform UniformBufferObject {
    Light light[];
    
} ubo;
 
void main() {
    
    vec3 lightInt = ubo.light[0].clrAint.xyz * ubo.light[0].clrAint.w;
    
    outColor = vec4(lightInt + ubo.light[0].rdsAamb.y, 1.0);
}