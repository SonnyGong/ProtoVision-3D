#version 330 core
out vec4 FragColor;

in vec3 Normal;
in vec3 FragPos;

uniform vec3 lightPos1;  // 第一组光源的位置
uniform vec3 lightColor1;  // 第一组光源的颜色
uniform vec3 lightPos2;  // 第二组光源的位置
uniform vec3 lightColor2;  // 第二组光源的颜色
uniform vec3 objectColor;
uniform vec3 viewPos;

void main()
{
    // 第一组光照计算
    float ambientStrength1 = 0.1;
    vec3 ambient1 = ambientStrength1 * lightColor1;

    vec3 norm1 = normalize(Normal);
    vec3 lightDir1 = normalize(lightPos1 - FragPos);
    float diff1 = max(dot(norm1, lightDir1), 0.0);
    vec3 diffuse1 = diff1 * lightColor1;

    float specularStrength1 = 0.1;
    vec3 viewDir1 = normalize(viewPos - FragPos);
    vec3 reflectDir1 = reflect(-lightDir1, norm1);
    float spec1 = pow(max(dot(viewDir1, reflectDir1), 0.0), 32);
    vec3 specular1 = specularStrength1 * spec1 * lightColor1;

    vec3 result1 = (ambient1 + diffuse1 + specular1) * objectColor;

    // 第二组光照计算
    float ambientStrength2 = 0.1;  // 你可以根据需求调整
    vec3 ambient2 = ambientStrength2 * lightColor2;

    vec3 norm2 = normalize(Normal);
    vec3 lightDir2 = normalize(lightPos2 - FragPos);
    float diff2 = max(dot(norm2, lightDir2), 0.0);
    vec3 diffuse2 = diff2 * lightColor2;

    float specularStrength2 = 0.3;  // 你可以根据需求调整
    vec3 viewDir2 = normalize(viewPos - FragPos);
    vec3 reflectDir2 = reflect(-lightDir2, norm2);
    float spec2 = pow(max(dot(viewDir2, reflectDir2), 0.0), 32);
    vec3 specular2 = specularStrength2 * spec2 * lightColor2;

    vec3 result2 = (ambient2 + diffuse2 + specular2) * objectColor;

    // 合并两组光照的影响
    vec3 finalResult = result1 + result2;

    // 输出最终颜色
    FragColor = vec4(finalResult, 1);
}
