#version 330 core
layout (location = 0) in vec3 aPos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

uniform int ADAS_TYPE;
uniform int ADAS_STATE;
uniform int ADAS_LEVEL;

out vec3 fragPos;
/*
ADAS_TYPE

0 BSD_LCA_L
1 BSD_LCA_R
2 RCW
3 DOW_L
4 DOW_R
5 FCTB
6 RCTB
7 FCTA_L
8 FCTA_R
9 RCTA_L
10 RCTA_R

ADAS_STATE
0 alpha = 0
1或者其他 alpha = 计算出的alpha

ADAS_LEVEL
0 gray
1 green
2 orange
3 red

*/

void main()
{	fragPos = aPos;
	vec3 final_pos = vec3(
	-aPos.y,
	aPos.z,
	-aPos.x
	);
	gl_Position = projection * view * model * vec4(final_pos, 1.0);
}