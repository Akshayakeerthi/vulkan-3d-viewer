#version 450
//#extension GL_ARB_separate_shader_objects : enable

layout(location = 0) in float fragColor;

layout(location = 0) out float outColor;

layout(binding = 0) uniform UniformBufferObject {
    mat4 model;
    mat4 trans;
    vec3 oid;
    //vec4 pclr;
    //vec4 ambclr;
    //vec3 ppos;
    
} ubo;

layout(std430,binding = 1) buffer PixelBuffer{

    vec2 pix;
    vec2 depth;
    vec2 cord;
    
} pixCoord;

void main() {
    outColor = ubo.oid.x;
    if(abs(pixCoord.pix.y-gl_FragCoord.y) < 0.6 && abs(pixCoord.pix.x-gl_FragCoord.x) < 0.6) {
        if(pixCoord.depth.x != 0.0){
            if (pixCoord.depth.x > gl_FragCoord.z){
                pixCoord.depth.x = gl_FragCoord.z;
                pixCoord.depth.y = ubo.oid.x;
                pixCoord.cord.x = ubo.oid.y;
                pixCoord.cord.y = ubo.oid.z;
                
            }
        }else{
            pixCoord.depth.x = gl_FragCoord.z;
            pixCoord.depth.y = ubo.oid.x;
            pixCoord.cord.x = ubo.oid.y;
            pixCoord.cord.y = ubo.oid.z;
            
        }
    }
    
}

