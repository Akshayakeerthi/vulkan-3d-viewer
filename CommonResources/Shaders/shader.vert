#version 450
//#extension GL_ARB_seperate_shader_objects : enable

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color;
layout(location = 2) in vec3 normal;
layout(location = 3) in vec2 uv;

layout(location = 0) out vec3 fragColor;
layout(location = 1) out vec2 fraguv;
layout(location = 2) out vec3 fragpos;
layout(location = 3) out vec3 fragnorm;

layout( push_constant ) uniform constants {
    mat4 view;
    mat4 proj;
} push;

layout(binding = 0) uniform UniformBufferObject {
    mat4 model;
    mat4 trans;
    vec4 oid;
    
} ubo;


void main() {
    
    vec4 posModel =  ubo.model * vec4(position, 1.0);
    gl_Position = push.proj * push.view * ubo.model * vec4(position, 1.0);//posModel;
    
    mat3 normMat = transpose(inverse(mat3(ubo.model)));
    fragnorm = normalize(normMat * normal);
    fragpos = posModel.xyz;
    fragColor = color;
    fraguv = uv;
}

