#version 450
//#extension GL_ARB_seperate_shader_objects : enable

layout( push_constant ) uniform constants {
    mat4 view;
    mat4 proj;
} push;

layout(location = 1) out vec3 nearPoint;
layout(location = 2) out vec3 farPoint;

// Grid position are in clipped space
vec3 gridPlane[6] = vec3[] (
    vec3(1, 0, 1), vec3(-1, 0, -1), vec3(-1, 0, 1),
    vec3(-1, 0, -1), vec3(1, 0, 1), vec3(1, 0, -1)
);

void main() {
    vec3 p = gridPlane[gl_VertexIndex].xyz;
    //nearPoint = UnprojectPoint(p.x, p.y, 0.0, push.view, push.proj).xyz; // unprojecting on the near plane
    //farPoint = UnprojectPoint(p.x, p.y, 1.0, push.view, push.proj).xyz; // unprojecting on the far plane
    gl_Position = vec4(p, 1.0); // using directly the clipped coordinates
}