#version 450
//#extension GL_ARB_seperate_shader_objects : enable

const vec2 OFFSETS[6] = vec2[](
  vec2(-1.0, -1.0),
  vec2(-1.0, 1.0),
  vec2(1.0, -1.0),
  vec2(1.0, -1.0),
  vec2(-1.0, 1.0),
  vec2(1.0, 1.0)
);

struct Light {
    vec4 posAtype;
    vec4 clrAint;
    vec2 rdsAamb;
};

layout (location = 0) out vec2 offset;

layout( push_constant ) uniform constants {
    mat4 view;
    mat4 proj;
} push;


layout(binding = 0) uniform UniformBufferObject {
    Light light[];
    
} ubo;

void main() {
    offset = OFFSETS[gl_VertexIndex];
    vec3 cameraRightWorld = {push.view[0].x, push.view[1].x, push.view[2].x};
    vec3 cameraUpWorld = {push.view[0].y, push.view[1].y, push.view[2].y};
    
    vec3 posWorld = ubo.light[0].posAtype.xyz
        + ubo.light[0].rdsAamb.x * offset.x * cameraRightWorld
        + ubo.light[0].rdsAamb.x * offset.y * cameraUpWorld;
    
    gl_Position = push.proj * push.view *vec4(posWorld, 1.0);
    
}

















