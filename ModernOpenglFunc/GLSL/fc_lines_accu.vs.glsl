#version 330 core
layout (location = 0) in vec3 aPos_cartesian;
layout (location = 1) in vec3 VehicleInfo_RECORD;


uniform mat4 model;
uniform vec3 final_model;

uniform mat4 view;
uniform mat4 projection;

// 输出的坐标
out vec3 result_xyz;


void main()
{


    float angle_accu = radians(VehicleInfo_RECORD.z);
    float final_accu_angle = radians(final_model.z);

    vec4 rotate_accu = vec4(
        cos(angle_accu), sin(angle_accu),
        -sin(angle_accu), cos(angle_accu)
    );
    vec4 final_accu = vec4(
        cos(final_accu_angle), -sin(final_accu_angle),
        sin(final_accu_angle), cos(final_accu_angle)
    );


    float radar0x = aPos_cartesian.x;
    float radar0y = aPos_cartesian.y;

    // 使用预计算的旋转矩阵
    vec2 radar_xy = vec2(radar0x,radar0y);

    // 累积旋转（rotate_accu）
    float x_accu = rotate_accu.x * radar_xy.x + rotate_accu.y * radar_xy.y;
    float y_accu = rotate_accu.z * radar_xy.x + rotate_accu.w * radar_xy.y;
    radar_xy = vec2(x_accu, y_accu);

    // 加上车辆偏移
    radar_xy.x += VehicleInfo_RECORD.x - final_model.x;
    radar_xy.y += VehicleInfo_RECORD.y - final_model.y;

    // 最后一次旋转（final_accu）
    float x_final = final_accu.x * radar_xy.x + final_accu.y * radar_xy.y;
    float y_final = final_accu.z * radar_xy.x + final_accu.w * radar_xy.y;
    radar_xy = vec2(x_final, y_final);








    // Calculate final position
    vec3 transformed_position = vec3(

        -radar_xy.y,
        0.6,
        -radar_xy.x
    );



    result_xyz = transformed_position.xyz;

    gl_PointSize = 2.0;

    // 应用模型、视图和投影矩阵转换
    gl_Position = projection * view * model * vec4(transformed_position, 1.0);

}
