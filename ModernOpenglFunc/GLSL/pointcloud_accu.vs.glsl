#version 330 core
layout (location = 0) in vec4 aPos_cartesian;
layout (location = 1) in vec4 MountInfo;  // 后四个属性
layout (location = 2) in vec4 VehicleInfo_RECORD;



uniform vec3 model1;
uniform vec3 model2;
uniform vec3 model3;
uniform vec3 model4;
vec3 final_model;

uniform mat4 model;

uniform mat4 view;
uniform mat4 projection;

//设置项
uniform float MIN_H;
uniform float MAX_H;
uniform float SIZE;

// 输出的坐标
out vec3 result_xyz;
out float height;

void main()
{

    float SENSOR_ID = VehicleInfo_RECORD.w;
    if (SENSOR_ID == 1.0)
    {
    final_model = model1;
    }
    if (SENSOR_ID == 2.0)
    {
    final_model = model2;
    }
    if (SENSOR_ID == 3.0)
    {
    final_model = model3;
    }
    if (SENSOR_ID == 4.0)
    {
    final_model = model4;
    }

    // 将角度转换为弧度
    float angle_rad = radians(MountInfo.w);
    float angle_accu = radians(VehicleInfo_RECORD.z);
    float final_accu_angle = -radians(final_model.z);






        // 计算旋转矩阵
    vec4 rotate_matrix = vec4(
        cos(angle_rad), sin(angle_rad),
        -sin(angle_rad), cos(angle_rad)
    );
    vec4 rotate_accu = vec4(
        cos(angle_accu), sin(angle_accu),
        -sin(angle_accu), cos(angle_accu)
    );
    vec4 final_accu = vec4(
        cos(final_accu_angle), sin(final_accu_angle),
        -sin(final_accu_angle), cos(final_accu_angle)
    );



    // 获取传入的笛卡尔坐标的值
    float range0 = aPos_cartesian.x;
    float elevation0 = aPos_cartesian.y;
    float azimuth0 = aPos_cartesian.z;

    // 计算雷达坐标的 x 和 y 分量
    float cosElevation = cos(radians(abs(elevation0)));
    float cosAzimuth = cos(radians(azimuth0));
    float sinAzimuth = sin(radians(azimuth0));

    float radar0x = range0 * cosElevation * cosAzimuth;
    float radar0y = -range0 * cosElevation * sinAzimuth;

    // 使用预计算的旋转矩阵
    vec2 radar_xy;

    // 初次旋转并平移
    float x_initial = rotate_matrix.x * radar0x + rotate_matrix.y * radar0y + MountInfo.x;
    float y_initial = rotate_matrix.z * radar0x + rotate_matrix.w * radar0y + MountInfo.y;
    radar_xy = vec2(x_initial, y_initial);

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
        range0 * sin(radians(elevation0)) + MountInfo.z,
        -radar_xy.x
    );



    result_xyz = transformed_position.xyz;

    height = transformed_position.y;
    if (height >= MIN_H && height <= MAX_H)
    gl_PointSize = SIZE;
    else
    gl_PointSize = 0;
    // 应用模型、视图和投影矩阵转换
    gl_Position = projection * view * model * vec4(transformed_position, 1.0);

}
