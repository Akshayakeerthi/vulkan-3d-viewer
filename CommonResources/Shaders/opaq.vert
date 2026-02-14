#version 450
//#extension GL_ARB_seperate_shader_objects : enable

layout( push_constant ) uniform constants {
    mat4 view;
    mat4 proj;
} push;

layout(binding = 0) uniform UniformBufferObject {
    mat4 model;
    mat4 trans;
    vec4 oid;
    
} ubo;

// Grid position are in clipped space
vec3 gridPlane[6] = vec3[] (
    vec3(1, 1, -1), vec3(-1, -1, -1), vec3(-1, 1, -1),
    vec3(-1, -1, -1), vec3(1, 1, -1), vec3(1, -1, -1)
);

void main() {
    gl_Position = push.proj * push.view * ubo.model * vec4(gridPlane[gl_VertexIndex].xyz, 1.);
    
}