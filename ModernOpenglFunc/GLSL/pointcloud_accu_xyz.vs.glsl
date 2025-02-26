#version 330 core
layout (location = 0) in vec4 aPos_cartesian;

layout (location = 3) in vec4 VehicleInfo_RECORD;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

// 输出的坐标
out vec3 result_xyz;

void main()
{



    // 获取传入的笛卡尔坐标的值
    float x0 = aPos_cartesian.x;
    float y0 = aPos_cartesian.y;
    float z0 = aPos_cartesian.z;
    result_xyz = vec3(-y0,z0,-x0);
    gl_PointSize = 3.0;


    gl_Position = projection * view * model * vec4(result_xyz, 1.0);

}
