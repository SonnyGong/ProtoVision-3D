#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec2 texCoord;
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
out vec2 TexCoord;
uniform int NEED_ROTATE;
void main()

{
    vec3 radar_xy;
    vec3 return_xyz;
    radar_xy = position.xyz;
    if (NEED_ROTATE == 1)
    {
        float angle_rad = radians(180.0);
        vec4 rotate_matrix = vec4(
        cos(angle_rad), sin(angle_rad),
        -sin(angle_rad), cos(angle_rad)
    );
            // 使用预计算的旋转矩阵


    // 初次旋转并平移
    radar_xy.x = radar_xy.x - 12.3;
    float x_initial = rotate_matrix.x * radar_xy.x + rotate_matrix.y * radar_xy.y;
    float y_initial = rotate_matrix.z * radar_xy.x + rotate_matrix.w * radar_xy.y;
    radar_xy.xy = vec2(x_initial, y_initial);

    }
    return_xyz = vec3(
    -radar_xy.y,
    0.5,
    -radar_xy.x
    );


    gl_Position = projection * view * model * vec4(return_xyz,1.0);
    TexCoord = texCoord;
}