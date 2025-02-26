#version 330 core
out vec4 FragColor;
in vec3 fragPos;  // 从顶点着色器传来的坐标
uniform int ADAS_TYPE;
uniform int ADAS_STATE;
uniform int ADAS_LEVEL;

void main()
{
    vec3 colour_gray = vec3(0.5,0.5,0.5); //0
    vec3 colour_green = vec3(0,1,0);  //1
    vec3 colour_orange = vec3(1,0.647,0);  //2
    vec3 colour_red = vec3(1,0,0);  //3
    vec3 colour_blue = vec3(0,0,1);  //4
    vec3 colour_black = vec3(0,0,0);  //other


    vec3 colour;
    float distance;
    float alpha;

    if (ADAS_TYPE == 0 || ADAS_TYPE == 1 || ADAS_TYPE == 3 || ADAS_TYPE == 4 || ADAS_TYPE == 7 || ADAS_TYPE == 8 || ADAS_TYPE == 9 || ADAS_TYPE == 10)
    {
        if (ADAS_LEVEL == 0)
        colour = colour_gray;
        else if (ADAS_LEVEL == 1)
        colour = colour_green;
        else if (ADAS_LEVEL == 2)
        colour = colour_orange;
        else if (ADAS_LEVEL == 3)
        colour = colour_red;
        else if (ADAS_LEVEL == 4)
        colour = colour_blue;
        else
        colour = colour_black;
    }
    else if (ADAS_TYPE == 2)
    {
        if (ADAS_LEVEL == 0)
        colour = colour_green;
        else if (ADAS_LEVEL == 1)
        colour = colour_orange;
        else
        colour = colour_red;
    }
    else if (ADAS_TYPE == 5 || ADAS_TYPE == 6)
    {
        colour = colour_red;
    }

    if (ADAS_TYPE == 0 || ADAS_TYPE == 1 || ADAS_TYPE == 2 || ADAS_TYPE == 3 || ADAS_TYPE == 4 || ADAS_TYPE == 5 || ADAS_TYPE == 6)
        // 根据x轴的距离控制透明度，距离原点越远，透明度越高
    {
            distance = abs(fragPos.x);  // 距离 x = 0 的距离
            alpha = 1- (distance / 100);  // 距离越远，透明度越高（alpha 越低）
            alpha = clamp(alpha - 0.5, 0.0, 0.5);  // 确保透明度在0到1之间
    }

    else
    {
            distance = length(fragPos.xy);
            alpha = 1- (distance / 29);  // 距离越远，透明度越高（alpha 越低）
            alpha = clamp(alpha - 0.5, 0.0, 0.5);  // 确保透明度在0到1之间
    }



    FragColor = vec4(colour,alpha);
}