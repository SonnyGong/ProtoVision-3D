#version 330 core
out vec4 FragColor;
in vec3 result_xyz;
in float Infrastructure;

void main()
{
//     FragColor = vec4(0.15,0.16,0.15,0.5); // set all 4 vector values to 1.0
    if(Infrastructure == 2.0)
    {FragColor = vec4(0,0,0,1); // set all 4 vector values to 1.0
    }
    else
    {
    FragColor = vec4(1,0,0,1); // set all 4 vector values to 1.0
    }

}