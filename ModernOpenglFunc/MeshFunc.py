# -*- encoding: utf-8 -*-
'''
@File    :   MeshFunc.py    
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
2025/2/10 16:08   NotToday      1.0         None
'''
import glm
from OpenGL.GL import *
import ctypes
MAX_BONE_INFLUENCE = 4
# 定义顶点数据结构
class Vertex(ctypes.Structure):
    _fields_ = [
        ("Position", ctypes.c_float * 3),
        ("Normal", ctypes.c_float * 3),
        ("TexCoords", ctypes.c_float * 2),
        ("Tangent", ctypes.c_float * 3),
        ("Bitangent", ctypes.c_float * 3),
        ("m_BoneIDs", ctypes.c_int * MAX_BONE_INFLUENCE),
        ("m_Weights", ctypes.c_float * MAX_BONE_INFLUENCE)
    ]

class Texture:
    def __init__(self, id, type):
        self.id = id
        self.type = type

class Mesh:
    def __init__(self,vertices,indices,textures):
        self.vertices = vertices
        self.indices = indices
        self.textures = textures
        self.VAO = glGenVertexArrays(1)
        self.VBO = glGenBuffers(1)
        self.EBO = glGenBuffers(1)

    def setupMesh(self):
        glBindVertexArray(self.VAO)

        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, len(self.vertices) * ctypes.sizeof(Vertex), (ctypes.c_void_p * len(self.vertices))(*[ctypes.pointer(v) for v in self.vertices]), GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(self.indices) * ctypes.sizeof(ctypes.c_uint), (ctypes.c_uint * len(self.indices))(*self.indices), GL_STATIC_DRAW)

        stride = ctypes.sizeof(Vertex)
        # vertex Positions
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        # vertex normals
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(ctypes.sizeof(Vertex.Position)))
        # vertex texture coords
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(ctypes.sizeof(Vertex.Position) + ctypes.sizeof(Vertex.Normal)))
        # vertex tangent
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(ctypes.sizeof(Vertex.Position) + ctypes.sizeof(Vertex.Normal) + ctypes.sizeof(Vertex.TexCoords)))
        # vertex bitangent
        glEnableVertexAttribArray(4)
        glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(ctypes.sizeof(Vertex.Position) + ctypes.sizeof(Vertex.Normal) + ctypes.sizeof(Vertex.TexCoords) + ctypes.sizeof(Vertex.Tangent)))
        # ids
        glEnableVertexAttribArray(5)
        glVertexAttribIPointer(5, 4, GL_INT, stride, ctypes.c_void_p(ctypes.sizeof(Vertex.Position) + ctypes.sizeof(Vertex.Normal) + ctypes.sizeof(Vertex.TexCoords) + ctypes.sizeof(Vertex.Tangent) + ctypes.sizeof(Vertex.Bitangent)))
        # weights
        glEnableVertexAttribArray(6)
        glVertexAttribPointer(6, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(ctypes.sizeof(Vertex.Position) + ctypes.sizeof(Vertex.Normal) + ctypes.sizeof(Vertex.TexCoords) + ctypes.sizeof(Vertex.Tangent) + ctypes.sizeof(Vertex.Bitangent) + ctypes.sizeof(Vertex.m_BoneIDs)))

        glBindVertexArray(0)

    def Draw(self, shader):
        diffuseNr = 1
        specularNr = 1
        normalNr = 1
        heightNr = 1

        for i, texture in enumerate(self.textures):
            glActiveTexture(GL_TEXTURE0 + i)
            number = ''
            if texture.type == "texture_diffuse":
                number = str(diffuseNr)
                diffuseNr += 1
            elif texture.type == "texture_specular":
                number = str(specularNr)
                specularNr += 1
            elif texture.type == "texture_normal":
                number = str(normalNr)
                normalNr += 1
            elif texture.type == "texture_height":
                number = str(heightNr)
                heightNr += 1

            glUniform1i(glGetUniformLocation(shader.ID, (texture.type + number).encode('utf-8')), i)
            glBindTexture(GL_TEXTURE_2D, texture.id)

        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glActiveTexture(GL_TEXTURE0)