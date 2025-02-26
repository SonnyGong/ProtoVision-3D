# -*- encoding: utf-8 -*-
'''
@File    :   ShaderFunc.py    
@Contact :   https://github.com/SonnyGong

┌───┐ ┌───┬───┬───┬───┐ ┌───┬───┬───┬───┐ ┌───┬───┬───┬───┐ ┌───┬───┬───┐
│Esc│ │ F1│ F2│ F3│ F4│ │ F5│ F6│ F7│ F8│ │ F9│F10│F11│F12│ │P/S│S L│P/B│ ┌┐ ┌┐ ┌┐
└───┘ └───┴───┴───┴───┘ └───┴───┴───┴───┘ └───┴───┴───┴───┘ └───┴───┴───┘ └┘ └┘ └┘
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───────┐ ┌───┬───┬───┐ ┌───┬───┬───┬───┐
│~ `│! 1│@ 2│# 3│$ 4│% 5│^ 6│& 7│* 8│( 9│) 0│_ -│+ =│ BacSp │ │Ins│Hom│PUp│ │N L│ / │ * │ - │
├───┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─────┤ ├───┼───┼───┤ ├───┼───┼───┼───┤
│ Tab │ Q │ W │ E │ R │ T │ Y │ U │ I │ O │ P │{ [│} ]│ | \ │ │Del│End│PDn│ │ 7 │ 8 │ 9 │   │
├─────┴┬──┴┬──┴┬──┴┬──┴┬──┴┬──┴┬──┴┬──┴┬──┴┬──┴┬──┴┬──┴─────┤ └───┴───┴───┘ ├───┼───┼───┤ + │
│ Caps │ A │ S │ D │ F │ G │ H │ J │ K │ L │: ;│" '│ Enter  │               │ 4 │ 5 │ 6 │   │
├──────┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴─┬─┴────────┤     ┌───┐     ├───┼───┼───┼───┤
│ Shift  │ Z │ X │ C │ V │ B │ N │ M │< ,│> .│? /│ Shift    │     │ ↑ │     │ 1 │ 2 │ 3 │   │
├─────┬──┴─┬─┴──┬┴───┴───┴───┴───┴───┴──┬┴───┼───┴┬────┬────┤ ┌───┼───┼───┐ ├───┴───┼───┤ E││
│ Ctrl│WIN │Alt │ Space  @NotToday      │ Alt│ fn │ WIN│Ctrl│ │ ← │ ↓ │ → │ │ 0     │ . │←─┘│
└─────┴────┴────┴───────────────────────┴────┴────┴────┴────┘ └───┴───┴───┘ └───────┴───┴───┘

@Modify Time      @Author        @Version    @Desciption
------------      -----------    --------    -----------
2025/2/10 13:59   NotToday      1.0         None
'''
import os.path

from OpenGL.GL import *
import OpenGL.GL.shaders
import glm


# 添加检查着色器编译和链接状态的函数
def check_shader_errors(shader, shader_type):
    if shader_type == 'program':
        success = glGetProgramiv(shader, GL_LINK_STATUS)
        if not success:
            info_log = glGetProgramInfoLog(shader)
            print(f'Program linking error: {info_log}')
    else:
        success = glGetShaderiv(shader, GL_COMPILE_STATUS)
        if not success:
            info_log = glGetShaderInfoLog(shader)
            print(f'Shader compile error ({shader_type}): {info_log}')


class Shader:
    def __init__(self, vertexPath, fragmentPath,geometryPath = "",is_debug = 0):
        self.vertex = self.return_text_by_path(vertexPath)
        self.fragment = self.return_text_by_path(fragmentPath)
        self.geometry = self.return_text_by_path(geometryPath)
        self.is_debug = is_debug
        self.create_shader()

    def return_text_by_path(self, path):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = f.read()
                return data
        else:
            return None

    def create_shader(self):
        geometry_shader = None
        vertex_shader = OpenGL.GL.shaders.compileShader(self.vertex, GL_VERTEX_SHADER)
        if self.geometry != None:
            geometry_shader = OpenGL.GL.shaders.compileShader(self.geometry, GL_GEOMETRY_SHADER)
        fragment_shader = OpenGL.GL.shaders.compileShader(self.fragment, GL_FRAGMENT_SHADER)

        self.ID = glCreateProgram()
        glAttachShader(self.ID, vertex_shader)
        if self.geometry != None:
            glAttachShader(self.ID, geometry_shader)
        glAttachShader(self.ID, fragment_shader)
        if self.is_debug:
            # 将 varyings 定义为包含一个元素的列表
            varyings = b"result_xyz"
            buff = ctypes.create_string_buffer(varyings)
            c_text = ctypes.cast(ctypes.pointer(ctypes.pointer(buff)), ctypes.POINTER(ctypes.POINTER(GLchar)))

            glTransformFeedbackVaryings(self.ID, 1,c_text, GL_INTERLEAVED_ATTRIBS)

        glLinkProgram(self.ID)
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)
        if self.geometry != None:
            glDeleteShader(geometry_shader)
        # self.shader_program = OpenGL.GL.shaders.compileProgram(vertex_shader, fragment_shader)

    def use(self):
        glUseProgram(self.ID)

    def setBool(self, name_out, value):
        glUniform1i(glGetUniformLocation(self.ID, str(name_out)), int(value))

    def setInt(self, name_out, value):
        glUniform1i(glGetUniformLocation(self.ID, str(name_out)), int(value))

    def setFloat(self, name_out, value):
        glUniform1f(glGetUniformLocation(self.ID, str(name_out)), value)

    def setVec2(self, name_out, value):
        glUniform2fv(glGetUniformLocation(self.ID, str(name_out)), 1, glm.value_ptr(value))

    def setVec2f(self, name_out, value1, value2):
        glUniform2f(glGetUniformLocation(self.ID, str(name_out)), value1, value2)

    def setVec3(self, name_out, value):
        glUniform3fv(glGetUniformLocation(self.ID, str(name_out)), 1, glm.value_ptr(value))

    def setVec3f(self, name_out, value1, value2, value3):
        glUniform3f(glGetUniformLocation(self.ID, str(name_out)), value1, value2, value3)

    def setVec4(self, name_out, value):
        glUniform4fv(glGetUniformLocation(self.ID, str(name_out)), 1, glm.value_ptr(value))

    def setVec4f(self, name_out, value1, value2, value3, value4):
        glUniform4f(glGetUniformLocation(self.ID, str(name_out)), value1, value2, value3, value4)

    def setMat2(self, name_out, value):
        glUniformMatrix2fv(glGetUniformLocation(self.ID, str(name_out)), 1, GL_FALSE, glm.value_ptr(value))

    def setMat3(self, name_out, value):
        glUniformMatrix3fv(glGetUniformLocation(self.ID, str(name_out)), 1, GL_FALSE, glm.value_ptr(value))

    def setMat4(self, name_out, value):
        glUniformMatrix4fv(glGetUniformLocation(self.ID, str(name_out)), 1, GL_FALSE, glm.value_ptr(value))

