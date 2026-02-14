#version 450
//#extension GL_ARB_seperate_shader_objects : enable

layout(location = 0) in vec3 fragColor;
layout(location = 1) in vec2 fraguv;
layout(location = 2) in vec3 fragpos;
layout(location = 3) in vec3 fragnorm;
layout(origin_upper_left, pixel_center_integer) in vec4 gl_FragCoord;

layout(location = 0) out vec4 outColor;

layout(binding = 0) uniform UniformBufferObject {
    mat4 model;
    mat4 trans;
    vec4 oid;
    
} ubo;

layout( push_constant ) uniform constants {
    mat4 view;
    mat4 proj;
} push;


struct Light {
    vec4 position;
    vec4 color;
    vec2 pix;
};

layout(std430,binding = 1) buffer ObjectBuffer{
    
    Light obj[];
} objectBuffer;

//layout(std430,binding = 2) buffer PixelBuffer{

//    vec2 pix;
//    vec2 coord;
    
//} pixCoord;

layout(binding = 2) uniform sampler2D texSampler;

void main() {
    
    vec3 dirtoLight = objectBuffer.obj[0].position.xyz - fragpos.xyz;
    
    float attenuation = 1.0 / dot(dirtoLight, dirtoLight);
    
    vec3 lightColor = objectBuffer.obj[0].color.xyz * objectBuffer.obj[0].color.w * attenuation;
    vec3 ambientColor = objectBuffer.obj[0].color.xyz * 0.2;
    vec3 diffuseColor = lightColor * max(dot(normalize(fragnorm), normalize(dirtoLight)), 0.0);
    
    if (ubo.oid.x != 0){
        outColor = vec4((diffuseColor + ambientColor) * fragColor, 1) * texture(texSampler, fraguv);
        //outId = ubo.oid;
        //if(abs(pixCoord.pix.y-gl_FragCoord.y) < 0.6 && abs(pixCoord.pix.x-gl_FragCoord.x) < 0.6) {
        //    if(gl_FragCoord.z > pixCoord.coord.x){
        //        pixCoord.coord = vec2(gl_FragCoord.z, ubo.oid);
        //    }
        //}
    }else{
        outColor = vec4((diffuseColor + ambientColor) * fragColor, 1);
    }
        
}









