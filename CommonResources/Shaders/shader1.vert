
#version 450
//#extension GL_ARB_separate_shader_objects : enable

layout(location = 0) in vec3 inPosition;
layout(location = 1) in vec3 inColor;
layout(location = 2) in vec3 inNormal;
layout(location = 3) in vec2 inTexture;

layout(location = 0) out float fragColor;

layout(binding = 0) uniform UniformBufferObject {
    mat4 model;
    mat4 trans;
    vec3 oid;
    //vec4 pclr;
    //vec4 ambclr;
    //vec3 ppos;
    
} ubo;

layout( push_constant ) uniform constants {
    mat4 view;
    mat4 proj;
} push;

//out gl_PerVertex {
//    vec4 gl_Position;
//};

void main() {
    gl_Position = push.proj * push.view * ubo.model * vec4(inPosition, 1.0);
    fragColor = ubo.oid.x;
}