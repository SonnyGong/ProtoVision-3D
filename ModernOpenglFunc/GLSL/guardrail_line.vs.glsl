#version 330 core
layout (location = 0) in vec3 aPos;
out vec3 OUTPOS;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    vec3 modifiedPos = aPos; // 创建一个临时变量
    gl_Position = projection * view * model * vec4(modifiedPos, 1.0); // 使用修改后的坐标
    OUTPOS = aPos;
}
