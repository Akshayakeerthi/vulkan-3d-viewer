#version 450
//#extension GL_ARB_seperate_shader_objects : enable

layout(location = 1) in vec3 nearPoint;
layout(location = 2) in vec3 farPoint;

layout( push_constant ) uniform constants {
    mat4 view;
    mat4 proj;
} push;

layout(location = 0) out vec4 outColor;


void main() {
    outColor = vec4(1., 0., 0., 0.3);
}









