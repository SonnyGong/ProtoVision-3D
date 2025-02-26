import pyassimp
from pyassimp import *
import OpenGL.GL.shaders as shader
import numpy as np
from OpenGL.GL import *


from PIL import Image
import pyrr


class LoadOBJECT():
    def __init__(self, Path) -> None:
        self.Path = Path
        self.Scene = ''  # variable to hold the loaded scene object
        self.Mesh = []  # list to hold all the meshes in the scene
        self.VAOs = []  # list to hold all the VAOs for each mesh
        self.AABB_VAO = []  # list to hold all the VAOs for each AABB
        self.Data = []  # optional it contains vertices,normal,faces,textureCoord
        self.Lookat = []  # optional variable for camera position
        self.checkbox = []  # list to hold boolean values for each mesh's checkbox
        self.TextureID = []  # optional list to hold texture IDs for each mesh

    def Loadfile(self):  # loadFile method
        # load the file using pyassimp
        scene = pyassimp.load(self.Path)
        # check if the file was loaded successfully
        if scene is not None:
            print("Model loaded successfully")
            self.Scene = scene
        else:
            print("Failed to load the model")

    def LoadMesh(self):  # find all the mesh from pyassimp nodes
        # getting the root node of the scene graph using the "self.Scene.rootnode" attribute
        node = self.Scene.rootnode

        # defines a nested function named "RecursiveSearch" that takes a node object and a string as arguments
        def RecursiveSearch(node, string='0'):
            # The string argument is used to generate unique names for each mesh by appending it with an index value.
            if node.meshes:
                # The "RecursiveSearch" function first checks if the node has any meshes using the "node.meshes" attribute
                num = 0
                # loop through each mesh in the node and add it to the "Mesh" list
                for mesh in node.meshes:
                    empty = []
                    empty.append(mesh)  # append the mesh object
                    empty.append(mesh.name + string + str(num))  # append a unique name for the mesh
                    self.Mesh.append(empty)  # add the mesh to the "Mesh" list
                    self.checkbox.append(True)  # add a boolean value to the "checkbox" list
                    num += 1  # increment the mesh index
            count = 0
            # recursively search for meshes in each child node of the current node
            for i in node.children:
                RecursiveSearch(i, string + str(count))  # call the function with the child node and an updated string
                count += 1  # increment the child node index

        # call the recursive search function with the root node as an argument to start the search
        RecursiveSearch(node)

    def SendData(self):  # send all required data of module to GPU
        # loop through each mesh in the "Mesh" list
        for Mesh in self.Mesh:
            struct = Mesh[0]  # for 0 its Mesh and 1 its name

            # define a nested function to create a VAO for the mesh
            def vaos(struct):
                # extract vertex, face, normal, and texture coordinate data from the mesh object
                vertices = np.array(struct.vertices, dtype=np.float32)
                faces = np.array(struct.faces, dtype=np.int32)
                normals = np.array(struct.normals, dtype=np.float32)
                texturecoord = np.array(struct.texturecoords, dtype=np.float32)
                # create a VAO and bind it
                vao = glGenVertexArrays(1)
                glBindVertexArray(vao)
                # create and bind a VBO for the vertex data
                VBO_vertices = glGenBuffers(1)
                glBindBuffer(GL_ARRAY_BUFFER, VBO_vertices)
                glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
                # enable the vertex attribute array for the vertex data and set the format
                glEnableVertexAttribArray(0)
                glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))
                # create and bind a VBO for the texture coordinate data
                VBO_Normal = glGenBuffers(1)
                glBindBuffer(GL_ARRAY_BUFFER, VBO_Normal)
                glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
                # enable the vertex attribute array for the texture coordinate data and set the format
                glEnableVertexAttribArray(1)
                glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))
                # create and bind a VBO for the texture coordinate data
                VBO_Texturecoord = glGenBuffers(1)
                glBindBuffer(GL_ARRAY_BUFFER, VBO_Texturecoord)
                glBufferData(GL_ARRAY_BUFFER, texturecoord.nbytes, texturecoord, GL_STATIC_DRAW)
                # enable the vertex attribute array for the texture coordinate data and set the format
                glEnableVertexAttribArray(2)
                glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))
                # create and bind an EBO for the face data
                EBO = glGenBuffers(1)
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
                glBufferData(GL_ELEMENT_ARRAY_BUFFER, faces.nbytes, faces, GL_STATIC_DRAW)
                # unbind the VAO and buffers
                glBindVertexArray(0)
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
                glBindBuffer(GL_ARRAY_BUFFER, 0)
                # create a dictionary containing the VAO, vertex data, and AABB and return it
                rvalue = {'VAO': vao, 'Index': vertices, 'AABB': pyrr.aabb.create_from_points(vertices)}

                return rvalue

            # call the "vaos" function with the mesh object as an argument and append the resulting dictionary to the "VAOs" list
            value = vaos(struct)
            self.VAOs.append(value)

    def GenerateAABB_VAO(self):  # send VAO Data to GPU

        # This is an inner function named Pass_points that takes two tuples representing the lower and upper bounds of an AABB.
        def Pass_points(lower_point, higher_point):
            # Extract the x, y, z values from the lower and upper points.
            x1, y1, z1 = lower_point
            x2, y2, z2 = higher_point
            # Define the points of the AABB box by combining the lower and upper points.
            points = [(x1, y1, z1), (x2, y1, z1), (x2, y2, z1), (x1, y2, z1), (x1, y1, z2), (x2, y1, z2), (x2, y2, z2),
                      (x1, y2, z2)]
            # Define the indices of each vertex for every face of the AABB box.
            index = [[0, 4, 1], [4, 5, 1], [3, 7, 2], [7, 6, 2], [6, 5, 2], [5, 1, 2], [4, 7, 6], [4, 5, 6], [3, 0, 2],
                     [0, 1, 2], [3, 7, 4], [3, 0, 4]]
            # Convert the points and indices into numpy arrays.
            vertices = np.array(points, dtype=np.float32)
            faces = np.array(index, dtype=np.int32)
            # Generate and bind a vertex array object (VAO).
            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)

            # Define the vertex buffer object (VBO) for the vertices
            vbo_vertices = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo_vertices)
            glBufferData(GL_ARRAY_BUFFER, vertices, GL_STATIC_DRAW)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
            glEnableVertexAttribArray(0)

            # Define the element buffer object (EBO) for the faces
            ebo_faces = glGenBuffers(1)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo_faces)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, faces, GL_STATIC_DRAW)
            # Unbind the buffers and VAO.
            glBindVertexArray(0)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            # Append the generated VAO to the AABB_VAO list.
            self.AABB_VAO.append(vao)

        # Create an empty list to store all the AABB points.
        overall_AABB_points = []
        # Loop through every VAO in the VAOs list.
        for obj in self.VAOs:
            # Extract the lower and upper points of the AABB for each VAO.
            lower_point, higher_point = obj['AABB']
            # Append the points to the overall_AABB_points list.
            overall_AABB_points.append(lower_point)
            overall_AABB_points.append(higher_point)
            # Call the Pass_points function to generate and bind the VAO for the AABB.
            Pass_points(lower_point, higher_point)
        # Create an AABB for all the overall_AABB_points and append it to the Lookat list.
        overall_AABB_points = pyrr.aabb.create_from_points(overall_AABB_points)
        self.Lookat.append(overall_AABB_points)
        # Generate and bind the VAO for the overall AABB.
        Pass_points(overall_AABB_points[0], overall_AABB_points[1])

    def LoadData(self):
        # iterate through each mesh in the list of meshes stored in the class's Mesh attribute.
        for mesh in self.Mesh:
            # create a list to store the binding data for the mesh.
            # This list has six elements, which correspond to the mesh's name, vertices, faces, normals, texture coordinates, and colors.
            binding = [0, 0, 0, 0, 0, 0]
            # since each mesh is stored as a tuple (the mesh object and some metadata),
            # this line extracts the mesh object from the tuple and assigns it to the mesh variable.
            mesh = mesh[0]
            # set the first element of the binding list to the mesh's name.
            binding[0] = mesh.name
            # set the second element of the binding list to the mesh's vertices.
            binding[1] = mesh.vertices
            # set the third element of the binding list to the mesh's faces.
            binding[2] = mesh.faces
            # set the fourth element of the binding list to the mesh's normals.
            binding[3] = mesh.normals
            # set the fifth element of the binding list to the mesh's texture coordinates.
            binding[4] = mesh.texturecoords
            # set the sixth element of the binding list to the mesh's colors.
            binding[5] = mesh.colors
            # add the binding list to the class's Data attribute, which stores all the loaded data.
            self.Data.append(binding)


def return_Tracker_DICT():
    CAR_OBJ_PATH = r"ModernOpenglFunc/OBJ/car.fbx"
    PEDESTRIAN_OBJ_PATH = r"ModernOpenglFunc/OBJ/pedestrian.obj"
    TRUCK_OBJ_PATH = r"ModernOpenglFunc/OBJ/truck2.obj"
    BIKE_OBJ_PATH = r"ModernOpenglFunc/OBJ/bike.fbx"
    ANIMAL_OBJ_PATH = r"ModernOpenglFunc/OBJ/animal.fbx"
    # OBJ_DICT = {
    #     "CAR":CAR_OBJ_PATH,
    #     "BIKE":BIKE_OBJ_PATH,
    #     "TRUCK":TRUCK_OBJ_PATH,
    #     "ANIMAL": ANIMAL_OBJ_PATH,
    #     "PEDESTRIAN":PEDESTRIAN_OBJ_PATH,
    # }
    OBJ_DICT = {
        "CAR":CAR_OBJ_PATH,
        "BIKE":ANIMAL_OBJ_PATH,
        "TRUCK":ANIMAL_OBJ_PATH,
        "ANIMAL": ANIMAL_OBJ_PATH,
        "PEDESTRIAN":ANIMAL_OBJ_PATH,
    }
    RETURN_DICT = {}
    for OBJTYPE in OBJ_DICT:
        instance = LoadOBJECT(OBJ_DICT[OBJTYPE])
        instance.Loadfile()
        instance.LoadMesh()
        instance.SendData()
        instance.GenerateAABB_VAO()
        RETURN_DICT[OBJTYPE] = instance
    return RETURN_DICT

def draw_grid(size, step):
    glBegin(GL_LINES)
    glColor3f(0.25, 0.75, 0.75)
    for i in np.arange(-size, size + step, step):
        glVertex3f(i, 0, -size)
        glVertex3f(i, 0, size)
        glVertex3f(-size, 0, i)
        glVertex3f(size, 0, i)
    glEnd()