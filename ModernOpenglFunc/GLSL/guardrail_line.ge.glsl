#version 330 core
layout(points) in;
layout(line_strip, max_vertices = 2) out;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
in vec3 OUTPOS[];

void main()
{
    // 将输入点从模型空间转换到视图空间
    vec4 p0 = gl_in[0].gl_Position;

    // 在视图空间中扩展点，生成第二个顶点
    vec3 pos1 = OUTPOS[0];
    pos1.y += 2;
    vec4 p1 = projection * view * model * vec4(pos1, 1.0);


    // 发出第一个顶点
    gl_Position = p0;
    EmitVertex();

    // 发出第二个顶点
    gl_Position = p1;
    EmitVertex();

    EndPrimitive();
}
