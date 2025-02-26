#version 330 core
out vec4 FragColor;
in vec3 result_xyz;  // 传入的坐标
in float height;     // 传入的高度信息
//设置项
uniform float MIN_H;
uniform float MAX_H;
uniform float SIZE;

void main()
{
    // 定义颜色阶段
    vec3 greenColor = vec3(0.0, 1.0, 0.0);   // 绿色 (低高度)
    vec3 yellowColor = vec3(1.0, 1.0, 0.0);  // 黄色 (中等偏低)
    vec3 orangeColor = vec3(1.0, 0.5, 0.0);  // 橙色 (中等偏高)
    vec3 redColor = vec3(1.0, 0.0, 0.0);     // 红色 (高高度)
    if (height >= MIN_H && height <= MAX_H)
    {

    float normalizedHeight = clamp((height - MIN_H) / (MAX_H - MIN_H), 0.0, 1.0);

    vec3 color;

    // 根据 normalizedHeight 插值不同的颜色阶段
    if (normalizedHeight < 0.33)
    {
        // 从绿色过渡到黄色
        color = mix(greenColor, yellowColor, normalizedHeight / 0.33);
    }
    else if (normalizedHeight < 0.66)
    {
        // 从黄色过渡到橙色
        color = mix(yellowColor, orangeColor, (normalizedHeight - 0.33) / 0.33);
    }
    else
    {
        // 从橙色过渡到红色
        color = mix(orangeColor, redColor, (normalizedHeight - 0.66) / 0.34);
    }

    // 将颜色应用到输出
    FragColor = vec4(color, 1.0);  // 使用计算出的颜色，alpha 设置为 1.0
    }
    else{
        FragColor = vec4(0,0,0, 0.0);  // 使用计算出的颜色，alpha 设置为 1.0
    }

}
