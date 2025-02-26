#version 330 core
layout (location = 0) in vec3 position;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 model;
uniform float speed;
uniform float yawrate;
void main() {
vec3 pos;
pos.xyz = position.xyz;
pos.x *= (1.0 + speed) * 2;  // 根据速度拉长矩形

// 根据yawrate产生弯曲，y越大，弯曲越明显
float angle = radians(-yawrate * pos.x / 100) ;
vec4 rotate_accu = vec4(
cos(angle), -sin(angle),
sin(angle), cos(angle)
);

// 累积旋转（rotate_accu）
float x_accu = rotate_accu.x * pos.x + rotate_accu.y * pos.y;
float y_accu = rotate_accu.z * pos.x + rotate_accu.w * pos.y;
vec2 radar_xy = vec2(x_accu, y_accu);
// Calculate final position
vec3 endpos = vec3(

-radar_xy.y,
0.6,
-radar_xy.x
);

        gl_Position = projection * view * model * vec4(endpos, 1.0);

}