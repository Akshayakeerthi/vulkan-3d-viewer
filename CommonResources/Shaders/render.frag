#version 450
//#extension GL_ARB_seperate_shader_objects : enable

layout(binding = 0) uniform sampler2D rt0;
layout(binding = 1) uniform sampler2D rt1;

layout(location = 0) out vec4 outColor;

void main() {
    // fetch pixel information
    vec4 accum = texelFetch(rt0, ivec2(int(gl_FragCoord.x), int(gl_FragCoord.y)), 0);
    float reveal = texelFetch(rt1, ivec2(int(gl_FragCoord.x), int(gl_FragCoord.y)), 0).r;
    
    // blend func: GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA
    outColor = vec4(accum.rgb / max(accum.a, 1e-5), reveal);
}









