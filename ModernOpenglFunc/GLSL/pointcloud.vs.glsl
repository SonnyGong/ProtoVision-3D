#version 330 core
layout (location = 0) in vec4 aPos_cartesian;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

// 预先计算好的旋转矩阵通过 uniform 传递
uniform vec4 rotate_matrix0;

uniform vec3 sensor_pos;

// 输出的坐标
out vec3 result_xyz;
out float Infrastructure;

void main()
{
    // 获取传入的笛卡尔坐标的值
    float range0 = aPos_cartesian.x;
    float elevation0 = aPos_cartesian.y;
    float azimuth0 = aPos_cartesian.z;
    Infrastructure = aPos_cartesian.w;

    // 计算雷达坐标的 x 和 y 分量
    float cosElevation = cos(radians(abs(elevation0)));
    float cosAzimuth = cos(radians(azimuth0));
    float sinAzimuth = sin(radians(azimuth0));

    float radar0x = range0 * cosElevation * cosAzimuth;
    float radar0y = -range0 * cosElevation * sinAzimuth;

    // 使用预计算的旋转矩阵
    vec2 radar_xy;
    radar_xy.x = rotate_matrix0.x * radar0x + rotate_matrix0.y * radar0y + sensor_pos.x;
    radar_xy.y = rotate_matrix0.z * radar0x + rotate_matrix0.w * radar0y + sensor_pos.y;

    // Calculate final position
    vec3 transformed_position = vec3(

        -radar_xy.y,
        range0 * sin(radians(elevation0)) + sensor_pos.z,
        -radar_xy.x
    );

    // Output coordinates
    result_xyz = vec3(radar_xy.x,radar_xy.y,transformed_position.y);


    if(Infrastructure == 2.0)
    {gl_PointSize = 5.0;
    }
    else
    {
    gl_PointSize = 3.0;
    }


    // 应用模型、视图和投影矩阵转换
    gl_Position = projection * view * model * vec4(transformed_position, 1.0);

}
