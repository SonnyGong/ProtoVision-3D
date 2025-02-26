import copy
import inspect
import itertools
import math
import sys
import time
import traceback

import numpy as np
from OpenGL.raw.WGL.VERSION.WGL_1_0 import wglGetCurrentDC, wglGetCurrentContext, wglCreateContext, wglShareLists, \
    wglUseFontBitmaps
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QSurfaceFormat, QImage, QPainter, QTransform, QFont, QMovie
from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL.GL import *
import OpenGL.GL.shaders
import imageio
import glm

from ModernOpenglFunc.ACCU_FUNC import CircularBuffer, NumberList
from ModernOpenglFunc.CameraFunc import Camera
from ModernOpenglFunc.GEN_VER_FUNC import generate_fan_vertices, generate_fan_indices, generate_cube_vertices, \
    generate_cube_indices
from ModernOpenglFunc.ModelFunc import LoadOBJECT, return_Tracker_DICT, draw_grid
from ModernOpenglFunc.ShaderFunc import Shader, check_shader_errors
from ctypes import *

MAX_ACCU_PC_NUM = 100000
MAX_ACCU_PC_VBO_BUFFER = 12 * 4 * MAX_ACCU_PC_NUM
MAX_ACCU_FS_LINES_NUM = 3500
MAX_ACCU_FS_LINES_VBO_BUFFER = 6 * 4 * MAX_ACCU_FS_LINES_NUM


class turn_left_right_light:
    def __init__(self):
        self.light_is_on = False


def print_opengl_state():
    print("GL_POLYGON_SMOOTH:", glIsEnabled(GL_POLYGON_SMOOTH))
    print("GL_LINE_SMOOTH:", glIsEnabled(GL_LINE_SMOOTH))
    print("GL_POINT_SMOOTH:", glIsEnabled(GL_POINT_SMOOTH))
    print("GL_PROGRAM_POINT_SIZE:", glIsEnabled(GL_PROGRAM_POINT_SIZE))


SINGLE_ADAS_INFO = {
    "StateCurrent": 0,
    "Warning_Level": 0
}
ADAS_Info_BLANK_dict = {
    "BSD_LCA_L": copy.deepcopy(SINGLE_ADAS_INFO),
    "BSD_LCA_R": copy.deepcopy(SINGLE_ADAS_INFO),
    "RCW": copy.deepcopy(SINGLE_ADAS_INFO),
    "DOW_L": copy.deepcopy(SINGLE_ADAS_INFO),
    "DOW_R": copy.deepcopy(SINGLE_ADAS_INFO),
    "FCTB": copy.deepcopy(SINGLE_ADAS_INFO),
    "RCTB": copy.deepcopy(SINGLE_ADAS_INFO),
    "FCTA_L": copy.deepcopy(SINGLE_ADAS_INFO),
    "FCTA_R": copy.deepcopy(SINGLE_ADAS_INFO),
    "RCTA_L": copy.deepcopy(SINGLE_ADAS_INFO),
    "RCTA_R": copy.deepcopy(SINGLE_ADAS_INFO),
}
class ACTION_CHECKBOX:
    def __init__(self):
        self.fs = 0
        self.fc_lines = 0
        self.tracker = 1
        self.pc = 1
        self.accu_pc = 0
        self.gr = 0
        self.adas = 0



def pick_accu_pc(ori_array, angle, x, y, z, vehicle_x, vehicle_y, vehicle_theta, SENSOR_ID):
    try:

        # # 过滤掉第四个元素不为1的小数组
        filtered_array = ori_array[ori_array[:, 3] == 1.0]
        # for sub_array in filtered_array:
        #     range_m = sub_array[0]
        #     elevation_deg = sub_array[1]
        #     azimuth_deg = sub_array[2]
        #     infrastructure = sub_array[3]
        #     a,b = change_coordnate1(range_m,elevation_deg,azimuth_deg,x, y, z, angle)
        #     y0 = a[0]
        #     x0 = a[1]
        #     z0 = b

        #     rotate_matrix_h = np.array(
        #         [[math.cos(math.pi * (vehicle_theta) / 180), math.sin(math.pi * (vehicle_theta) / 180)],
        #          [-math.sin(math.pi * (vehicle_theta) / 180), math.cos(math.pi * (vehicle_theta) / 180)]])
        #     radarh_xy = np.array([a[0], a[1]])
        #     radar1_xy_angle_h = np.dot(radarh_xy, rotate_matrix_h)
        #     a[0] = radar1_xy_angle_h[0] + vehicle_y
        #     a[1] = radar1_xy_angle_h[1] + vehicle_x
        #     print(-a[0], b, -a[1])
        #     break
        # filtered_array = ori_array
        # 统计剩余的小数组数量
        remaining_count = filtered_array.shape[0]
        # # print(vehicle_x, vehicle_y, vehicle_theta)
        new_elements = np.array([x, y, z, angle, float(vehicle_x), float(vehicle_y), float(vehicle_theta), SENSOR_ID],
                                dtype=np.float32)
        extended_array = np.hstack([filtered_array, np.tile(new_elements, (filtered_array.shape[0], 1))])
        extended_array = extended_array.astype(np.float32)
        # print(f"Extended array shape: {extended_array.shape}")
        # print(f"Extended array dtype: {extended_array.dtype}")
        # print(f"Extended array nbytes: {extended_array.nbytes}")
        # print(extended_array)

        return extended_array, remaining_count
    except Exception as e:
        print(e)
        return np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], dtype=np.float32)


def pick_accu_fc_lines(ori_array, vehicle_x, vehicle_y, vehicle_theta):
    try:

        remaining_count = ori_array.shape[0]

        new_elements = np.array([float(vehicle_x), float(vehicle_y), float(vehicle_theta)], dtype=np.float32)
        extended_array = np.hstack([ori_array, np.tile(new_elements, (ori_array.shape[0], 1))])
        extended_array = extended_array.astype(np.float32)

        return extended_array, remaining_count
    except Exception as e:
        print(e)
        return np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)


class ACCU_INFO:
    def __init__(self):
        self.do_flash = 0
        self.accu_pc_num = 0
        self.accu_fc_lines_num = 0
        self.mount_info_list = []
        self.mount_and_pc_num_list = []
        self.car_position = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
        self.last_pc_NUM = [0, 0, 0, 0]
        self.theta = [0.0, 0.0, 0.0, 0.0, ]  # 车辆的初始航向角
        self.last_theta = [0.0, 0.0, 0.0, 0.0, ]
        self.last_chriptime = [0.0, 0.0, 0.0,0.0]
        self.yaw_rate = [0.0, 0.0, 0.0, 0.0, ]
        self.average_speed_list = []
        self.average_speed = 0
        self.last_car_position = [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]
        self.delta_t = [0.07,0.07,0.07,0.07]
        self.last_pc_data = {
            1: None,
            2: None,
            3: None,
            4: None,
        }
        self.accu_np = CircularBuffer(10000, 3)
        self.speed_flag_func = NumberList(size=60)
        self.speed_flag = 2

    def update_car_position(self, Vehicle_dict):
        # 更新航向角  °每秒
        self.last_theta = self.theta
        self.last_car_position = self.car_position


        for i in range(4):

            self.delta_t[i] = (Vehicle_dict["chriptime" + str(i + 1)] - self.last_chriptime[i]) / 1000
            if self.last_chriptime[i] == 0.0:
                self.delta_t[i] = 0.0
            print(self.delta_t)

            self.theta[i] = self.theta[i] + (Vehicle_dict["yawrate" + str(i + 1)] * self.delta_t[i])
            self.yaw_rate[i] = Vehicle_dict["yawrate" + str(i + 1)]
            SpeedM_S = Vehicle_dict["velocity" + str(i + 1)] / 3.6
            self.average_speed_list.append(Vehicle_dict["velocity" + str(i + 1)])
            if len(self.average_speed_list) >= 2:
                self.average_speed = sum(self.average_speed_list) / len(self.average_speed_list)
                self.speed_flag = self.speed_flag_func.add_number(int(self.average_speed))
                self.average_speed_list = []
            # 更新车辆位置
            self.car_position[i][0] += SpeedM_S * math.cos(math.radians(self.theta[i])) * self.delta_t[i]
            self.car_position[i][1] += SpeedM_S * -(math.sin(math.radians(self.theta[i]))) * self.delta_t[i]
            self.last_chriptime[i] = Vehicle_dict["chriptime" + str(i + 1)]

        # print('car_position', self.car_position, self.theta, SpeedM_S, yaw_rate, )


def mount_info_ini():
    mount_dict_blank = {
        "yaw": 0,
        "x": 0,
        "y": 0,
        "z": 0,
    }
    return_mount_dict = {
        1: copy.deepcopy(mount_dict_blank),
        2: copy.deepcopy(mount_dict_blank),
        3: copy.deepcopy(mount_dict_blank),
        4: copy.deepcopy(mount_dict_blank),
    }
    return return_mount_dict


def errorprint(func_name, extramsg, e):
    print(func_name, extramsg)
    print(e)
    exc_type, exc_obj, tb = sys.exc_info()
    filename = tb.tb_frame.f_code.co_filename
    line_number = tb.tb_lineno
    method_name = inspect.currentframe().f_back.f_code.co_name
    print("Error '%s' happened in %s.%s() on line %d at %s" % (
        exc_type.__name__, filename, method_name, line_number,
        str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))))
    print(traceback.print_exc())


def return_init_Tracker_mat():
    model_car = glm.mat4(1.0)

    # model_car = glm.translate(model_car, glm.vec3(This_Frame_index * 10+math.sin(self.roate), 0.0, math.sin(self.roate)))
    model_car = glm.rotate(model_car, math.radians(-90), glm.vec3(1.0, 0.0, 0.0))
    model_car = glm.rotate(model_car, math.radians(180.0), glm.vec3(0.0, 0.0, 1.0))
    model_car = glm.scale(model_car, glm.vec3(0.008, 0.008, 0.008))
    return model_car


def return_init_ped_mat():
    model_ped = glm.mat4(1.0)

    # model_car = glm.translate(model_car, glm.vec3(This_Frame_index * 10+math.sin(self.roate), 0.0, math.sin(self.roate)))
    model_ped = glm.rotate(model_ped, math.radians(180.0), glm.vec3(0.0, 1.0, 0.0))
    model_ped = glm.rotate(model_ped, math.radians(-90), glm.vec3(1.0, 0.0, 0.0))
    model_ped = glm.scale(model_ped, glm.vec3(1.5, 1.5, 1.5))
    return model_ped


def return_init_truck_mat():
    model_truck = glm.mat4(1.0)

    # model_car = glm.translate(model_car, glm.vec3(This_Frame_index * 10+math.sin(self.roate), 0.0, math.sin(self.roate)))
    # model_truck = glm.rotate(model_truck, math.radians(180.0), glm.vec3(0.0, 1.0, 0.0))
    model_truck = glm.rotate(model_truck, math.radians(180.0), glm.vec3(0.0, 1.0, 0.0))
    model_truck = glm.scale(model_truck, glm.vec3(1.3, 1.3, 1.3))
    return model_truck


def return_init_bike_mat():
    model_bike = glm.mat4(1.0)

    model_bike = glm.translate(model_bike, glm.vec3(0.0, 0.9, 0.0))
    # model_truck = glm.rotate(model_truck, math.radians(180.0), glm.vec3(0.0, 1.0, 0.0))
    model_bike = glm.rotate(model_bike, math.radians(90), glm.vec3(0.0, 1.0, 0.0))
    model_bike = glm.scale(model_bike, glm.vec3(0.7, 0.7, 0.7))

    return model_bike


def return_init_animal_mat():
    model_animal = glm.mat4(1.0)

    model_animal = glm.translate(model_animal, glm.vec3(0.0, 1.3, 0.0))
    model_animal = glm.rotate(model_animal, math.radians(-90), glm.vec3(0.0, 1.0, 0.0))
    model_animal = glm.rotate(model_animal, math.radians(-90), glm.vec3(1.0, 0.0, 0.0))
    model_animal = glm.scale(model_animal, glm.vec3(0.3, 0.3, 0.3))

    return model_animal


class GWidget(QOpenGLWidget):
    #gcy
    def __init__(self, parent=None):
        super(QOpenGLWidget, self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)

        self.ifStarted = 1
        self.fps = 0

        self.width = 200
        self.height = 100
        self.Camera = Camera()

        self.deltaTime = 0.0
        self.lastFrame = 0.0
        self.lightPos = glm.vec3(0, 0, 0)

        self.openGL_frame = 0

        self.car_init_model_car_mat = return_init_Tracker_mat()
        self.truck_init_model_truck_mat = return_init_truck_mat()
        self.pedestrain_init_model_mat = return_init_ped_mat()
        self.bike_init_model_car_mat = return_init_bike_mat()
        self.animal_init_model_mat = return_init_animal_mat()

        # self.car_init_model_car_mat = return_init_animal_mat()
        # self.truck_init_model_truck_mat = return_init_animal_mat()
        # self.pedestrain_init_model_mat = return_init_animal_mat()
        # self.bike_init_model_car_mat = return_init_animal_mat()
        # self.animal_init_model_mat = return_init_animal_mat()

        self.all_return_mat_class_f = []
        self.all_return_mat_class_r = []
        self.MountInfo = mount_info_ini()
        self.steering_wheel_img = QImage(r"image/steering_wheel.png")
        self.left_img = QImage(r"image/left.png")
        self.right_img = QImage(r"image/right.png")
        self.left_enable_img = QImage(r"image/left_enable.png")
        self.right_enable_img = QImage(r"image/right_enable.png")
        self.left_func = turn_left_right_light()
        self.right_func = turn_left_right_light()

        self.vehicle_info_dict = {
            "streeing_angle": 0,

            "turnlight_l": 0,
            "turnlight_r": 0,
            "velocity1": 0,
            "velocity2": 0,
            "velocity3": 0,
            "velocity4": 0,
            "yawrate1": 0,
            "yawrate2": 0,
            "yawrate3": 0,
            "yawrate4": 0,
        }
        self.show_checkbox = ACTION_CHECKBOX()


        self.ADAS_Info_dict = copy.deepcopy(ADAS_Info_BLANK_dict)

        self.timer_left_right = QTimer(self)
        self.timer_left_right.timeout.connect(self.update_left_right_flash_state)
        self.timer_left_right.start(500)  # 每500毫秒更新一次灯的状态

        self.ACCU_PC_CLASS = ACCU_INFO()
        self.ACCU_PC_CONFIG_DICT = {
            "MIN_H": 0.5,
            "MAX_H": 5,
            "MAX_NUM": 50000,
            "SIZE": 2.0,
        }

    def initializeGL(self):
        #gcy
        format = QSurfaceFormat()
        format.setSamples(4)  # 或者其他数量
        self.setFormat(format)
        glEnable(GL_DEPTH_TEST)
        # # 启用混合
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)  # 可选: 请求最佳的平滑效果
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_POLYGON_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_PROGRAM_POINT_SIZE)
        glEnable(GL_TEXTURE_2D)
        print("initializeGL········")

        self.PreCompileShader()
        self.init_speed_logo_func()
        self.init_ground()
        self.init_fs()
        self.init_gr()
        self.init_accu_fclines()
        self.init_accu_pc()
        self.init_CurvedRectangle()
        self.init_pc()
        self.init_adas()

        self.roate = 0.0

        self.OBJ_RETURN_DICT = return_Tracker_DICT()
        # 加载并设置logo纹理
        self.logo_texture = self.load_logo_texture(r"image/ProtoVision_LOGO.png")

    def paintGL(self):
        #gcy
        if self.ifStarted:
            try:
                self.update_fps()

                glClearColor(0.2, 0.2, 0.2, 1.0)
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

                # self.lightPos.x = 1.0 + math.sin(self.roate) * 2.0
                # self.lightPos.y = math.sin(self.roate / 2.0)

                projection, view_m = self.draw_self_car()
                # print(self.ACCU_PC_CLASS.speed_flag)
                if self.ACCU_PC_CLASS.speed_flag != 2:
                    self.draw_front_speed_logo(projection, view_m)
                self.draw_ground(projection, view_m)
                if self.show_checkbox.adas:
                    self.draw_adas(projection, view_m)
                if self.show_checkbox.tracker:
                    self.draw_tracker(projection, view_m)
                if self.show_checkbox.fs:
                    self.draw_freespace(projection, view_m)
                if self.show_checkbox.gr:
                    self.draw_guardrail(projection, view_m)
                if self.show_checkbox.pc:
                    self.draw_pc(projection, view_m)
                if self.show_checkbox.fc_lines:
                    self.draw_accu_fc_lines(projection, view_m)

                self.draw_CurvedRectangle(projection, view_m)
                if self.show_checkbox.accu_pc:
                    self.draw_accu_pc(projection, view_m)
                glPushAttrib(GL_ALL_ATTRIB_BITS)
                self.draw_vehicle_info()
                glPopAttrib()





            except Exception as e:
                errorprint(e, "paintGL", "ERROR")
        else:
            self.draw_logo()
        # self.update()

    def update_left_right_flash_state(self):
        if self.vehicle_info_dict["turnlight_l"]:
            self.left_func.light_is_on = not self.left_func.light_is_on  # 切换灯的状态
        else:
            self.left_func.light_is_on = False  # 如果转向灯关闭，则确保灯也关闭

        if self.vehicle_info_dict["turnlight_r"]:
            self.right_func.light_is_on = not self.right_func.light_is_on  # 切换灯的状态
        else:
            self.right_func.light_is_on = False  # 如果转向灯关闭，则确保灯也关闭




    def update_fps(self):
        currentFrame = time.time()
        self.openGL_frame += 1
        self.deltaTime = currentFrame - self.lastFrame
        # 每秒计算一次帧率
        if self.deltaTime > 1.0:
            self.fps = self.openGL_frame / self.deltaTime
            # print(f"FPS: {fps:.2f}")
            self.openGL_frame = 0

            self.lastFrame = currentFrame

    def init_adas(self):
        self.adasVBO = glGenBuffers(1)
        self.adasVAO = glGenVertexArrays(1)
        self.adasEBO = glGenBuffers(1)

        adasvertices = np.array([
            #BSD_LCA_L
            1.63, 1.3, 0.05,
            1.63, 4.81, 0.05,
            -75.68, 4.81, 0.05,
            -75.68, 1.3, 0.05,
            # BSD_LCA_R
            1.63, -1.3, 0.05,
            1.63, -4.81, 0.05,
            -75.68, -4.81, 0.05,
            -75.68, -1.3, 0.05,
            #RCW
            -0.98, 0.91, 0.05,
            -0.98, -0.91, 0.05,
            -70.93, -0.91, 0.05,
            -70.93, 0.91, 0.05,
            #DOWL
            1.59, 1.01, 0.051,
            1.59, 2.6, 0.051,
            -31.55, 2.6, 0.051,
            -31.55, 1.01, 0.051,
            #DOWR
            1.59, -1.01, 0.051,
            1.59, -2.6, 0.051,
            -31.55, -2.6, 0.051,
            -31.55, -1.01, 0.051,

        ], dtype=np.float32)

        adasindices = np.array([
            0, 1, 2,
            2, 3, 0,

            4, 5, 6,
            6, 7, 4,

            8, 9, 10,
            10, 11, 8,

            12, 13, 14,
            14, 15, 12,

            16, 17, 18,
            18, 19, 16,
        ], dtype=np.uint32)
        F_cube_vertices = generate_cube_vertices(5,0,1,1,5,2)
        F_cube_indices = generate_cube_indices(max(adasindices) + 1)
        adasvertices = np.concatenate(
            (adasvertices, F_cube_vertices), axis=0)
        adasindices = np.concatenate(
            (adasindices, F_cube_indices), axis=0)


        R_cube_vertices = generate_cube_vertices(-5,0,1,1,5,2)
        R_cube_indices = generate_cube_indices(max(adasindices) + 1)
        adasvertices = np.concatenate(
            (adasvertices, R_cube_vertices), axis=0)
        adasindices = np.concatenate(
            (adasindices, R_cube_indices), axis=0)


        # 扇形的顶点和索引
        FCTA_L_fan_vertices = generate_fan_vertices(radius=10.0, segments=50, start_angle=0, end_angle=100,
                                                    x_offset=3.36, y_offset=0.98)
        FCTA_L_fan_indices = generate_fan_indices(offset=len(adasvertices) / 3, segments=50)
        FCTA_R_fan_vertices = generate_fan_vertices(radius=10.0, segments=50, start_angle=260, end_angle=360,
                                                    x_offset=3.36, y_offset=-0.98)
        FCTA_R_fan_indices = generate_fan_indices(offset=int(len(adasvertices) / 3 + len(FCTA_L_fan_vertices) / 3),
                                                  segments=50)

        RCTA_L_fan_vertices = generate_fan_vertices(radius=10.0, segments=50, start_angle=80, end_angle=180,
                                                    x_offset=-1.38, y_offset=1.11)
        RCTA_L_fan_indices = generate_fan_indices(
            offset=int(len(adasvertices) / 3 + len(FCTA_L_fan_vertices) / 3 + len(FCTA_R_fan_vertices) / 3),
            segments=50)
        RCTA_R_fan_vertices = generate_fan_vertices(radius=10.0, segments=50, start_angle=180, end_angle=360 - 80,
                                                    x_offset=-1.38, y_offset=-1.11)
        RCTA_R_fan_indices = generate_fan_indices(offset=int(
            len(adasvertices) / 3 + len(FCTA_L_fan_vertices) / 3 + len(FCTA_R_fan_vertices) / 3 + len(
                RCTA_L_fan_vertices) / 3), segments=50)

        # 合并矩形和扇形的顶点数据
        vertices = np.concatenate(
            (adasvertices, FCTA_L_fan_vertices, FCTA_R_fan_vertices, RCTA_L_fan_vertices, RCTA_R_fan_vertices), axis=0)
        indices = np.concatenate(
            (adasindices, FCTA_L_fan_indices, FCTA_R_fan_indices, RCTA_L_fan_indices, RCTA_R_fan_indices), axis=0)

        glBindVertexArray(self.adasVAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.adasVBO)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.adasEBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def init_ground(self):
        self.groundVBO = glGenBuffers(1)
        self.groundVAO = glGenVertexArrays(1)
        self.groundEBO = glGenBuffers(1)

        groundvertices = np.array([
            1500.0, 0.0, 1500.0,
            -1500.0, 0.0, 1500.0,
            -1500.0, 0.0, -1500.0,
            1500.0, 0.0, -1500.0
        ], dtype=np.float32)

        groundindices = np.array([
            0, 1, 2,
            2, 3, 0
        ], dtype=np.uint32)
        glBindVertexArray(self.groundVAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.groundVBO)
        glBufferData(GL_ARRAY_BUFFER, groundvertices.nbytes, groundvertices, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.groundEBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, groundindices.nbytes, groundindices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def init_fs(self):
        #FS初始化
        self.fs_VAO = glGenVertexArrays(1)
        self.fs_VBO = glGenBuffers(1)
        self.freespace_num = 0
        glBindVertexArray(self.fs_VAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.fs_VBO)
        self.max_buffer_size_fs = 4 * 3 * 5000
        glBufferData(GL_ARRAY_BUFFER, self.max_buffer_size_fs, None, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def init_gr(self):
        #GR初始化
        self.gr_VAO = [glGenVertexArrays(1) for i in range(4)]
        self.gr_VBO = [glGenBuffers(1) for i in range(4)]
        self.gr_num = [0, 0, 0, 0]

        i = 0
        for single_vbo in self.gr_VBO:
            glBindVertexArray(self.gr_VAO[i])
            glBindBuffer(GL_ARRAY_BUFFER, single_vbo)

            glBufferData(GL_ARRAY_BUFFER, self.max_buffer_size_fs, None, GL_DYNAMIC_DRAW)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * 4, ctypes.c_void_p(0))
            i += 1
            glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def init_accu_fclines(self):
        #车道线累计初始化
        self.ACCU_FS_LINES_VAO = glGenVertexArrays(1)
        self.ACCU_FS_LINES_VBO = glGenBuffers(1)
        glBindVertexArray(self.ACCU_FS_LINES_VAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.ACCU_FS_LINES_VBO)
        glBufferData(GL_ARRAY_BUFFER, MAX_ACCU_FS_LINES_VBO_BUFFER, None, GL_DYNAMIC_DRAW)
        # 配置顶点属性指针
        glVertexAttribPointer(0, 3, GL_FLOAT, False, 6 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glVertexAttribPointer(1, 3, GL_FLOAT, False, 6 * 4, ctypes.c_void_p(3 * 4))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def init_accu_pc(self):
        #点云累计初始化
        self.ACCU_PC_VAO = glGenVertexArrays(1)
        self.ACCU_PC_VBO = glGenBuffers(1)

        glBindVertexArray(self.ACCU_PC_VAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.ACCU_PC_VBO)
        glBufferData(GL_ARRAY_BUFFER, MAX_ACCU_PC_VBO_BUFFER, None, GL_DYNAMIC_DRAW)
        # 配置顶点属性指针
        glVertexAttribPointer(0, 4, GL_FLOAT, False, 12 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glVertexAttribPointer(1, 4, GL_FLOAT, False, 12 * 4, ctypes.c_void_p(4 * 4))
        glEnableVertexAttribArray(1)

        glVertexAttribPointer(2, 4, GL_FLOAT, False, 12 * 4, ctypes.c_void_p(8 * 4))
        glEnableVertexAttribArray(2)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def init_CurvedRectangle(self):
        #前向指示
        segments = 500
        vertices = np.zeros((segments * 2, 3), dtype=np.float32)
        for i in range(segments):
            y_pos = i / segments  # 根据分段设置Y位置
            vertices[2 * i] = [y_pos, -1, 0.4]  # 左侧顶点
            vertices[2 * i + 1] = [y_pos, 1, 0.4]  # 右侧顶点

        self.CurvedRectangle_VAO = glGenVertexArrays(1)
        self.CurvedRectangle_VBO = glGenBuffers(1)
        glBindVertexArray(self.CurvedRectangle_VAO)
        glBindBuffer(GL_ARRAY_BUFFER, self.CurvedRectangle_VBO)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * vertices.itemsize, None)
        glEnableVertexAttribArray(0)

    def init_pc(self):
        #PC初始化
        self.PC_VAO = [glGenVertexArrays(1) for i in range(4)]
        self.PC_VBO = [glGenBuffers(1) for i in range(4)]
        self.PC_num = [0, 0, 0, 0]

        self.transform_feedback = [glGenTransformFeedbacks(1) for i in range(4)]
        self.feedback_buffer = [glGenBuffers(1) for i in range(4)]

        i = 0
        for single_vbo in self.PC_VBO:
            glBindVertexArray(self.PC_VAO[i])
            glBindBuffer(GL_ARRAY_BUFFER, single_vbo)
            self.max_buffer_size_pc = 4 * 4 * 5000
            glBufferData(GL_ARRAY_BUFFER, self.max_buffer_size_pc, None, GL_DYNAMIC_DRAW)
            glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))

            glEnableVertexAttribArray(0)
            glBindTransformFeedback(GL_TRANSFORM_FEEDBACK, self.transform_feedback[i])
            glBindBuffer(GL_TRANSFORM_FEEDBACK_BUFFER, self.feedback_buffer[i])
            glBufferData(GL_TRANSFORM_FEEDBACK_BUFFER, 3 * 4 * 5000, None, GL_DYNAMIC_DRAW)
            glBindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER, 0, self.feedback_buffer[i])
            i += 1

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def PreCompileShader(self):
        print("着色器编译中··········")
        try:
            self.TrackerShader = Shader("ModernOpenglFunc/GLSL/Tracker.vs.glsl",
                                        "ModernOpenglFunc/GLSL/Tracker.fs.glsl")
            self.GroundShader = Shader("ModernOpenglFunc/GLSL/ground.vs.glsl",
                                       "ModernOpenglFunc/GLSL/ground.fs.glsl")
            self.SelfCarShader = Shader("ModernOpenglFunc/GLSL/Tracker.vs.glsl",
                                        "ModernOpenglFunc/GLSL/selfcar.fs.glsl")
            self.FreespaceLineShader = Shader("ModernOpenglFunc/GLSL/freespace_line.vs.glsl",
                                              "ModernOpenglFunc/GLSL/freespace_line.fs.glsl")
            self.FreespaceFaceShader = Shader("ModernOpenglFunc/GLSL/ground.vs.glsl",
                                              "ModernOpenglFunc/GLSL/freespace_face.fs.glsl")
            self.GuardrailLineShader_shu = Shader("ModernOpenglFunc/GLSL/guardrail_line.vs.glsl",
                                                  "ModernOpenglFunc/GLSL/guardrail_line.fs.glsl",
                                                  "ModernOpenglFunc/GLSL/guardrail_line.ge.glsl")
            self.GuardrailLineShader_heng1 = Shader("ModernOpenglFunc/GLSL/guardline_heng1.vs.glsl",
                                                    "ModernOpenglFunc/GLSL/guardrail_line.fs.glsl")
            self.GuardrailLineShader_heng2 = Shader("ModernOpenglFunc/GLSL/guardrail_heng2.vs.glsl",
                                                    "ModernOpenglFunc/GLSL/guardrail_line.fs.glsl")
            # self.PointCloudShader = Shader("ModernOpenglFunc/pointcloud.vs",
            #                                         "ModernOpenglFunc/pointcloud.fs","",1)
            self.debug = 0
            self.PointCloudShader = Shader("ModernOpenglFunc/GLSL/pointcloud.vs.glsl",
                                           "ModernOpenglFunc/GLSL/pointcloud.fs.glsl", "", self.debug)

            self.PC_ACCU_Shader = Shader("ModernOpenglFunc/GLSL/pointcloud_accu.vs.glsl",
                                         "ModernOpenglFunc/GLSL/pointcloud_accu.fs.glsl", "", 1)
            self.PRE_SPEED_Shader = Shader("ModernOpenglFunc/GLSL/pre_speed_logo.vs.glsl",
                                           "ModernOpenglFunc/GLSL/pre_speed_logo.fs.glsl", )
            self.FC_LINES_ACCU_Shader = Shader("ModernOpenglFunc/GLSL/fc_lines_accu.vs.glsl",
                                               "ModernOpenglFunc/GLSL/fc_lines_accu.fs.glsl", )
            self.CurvedRectangle_Shader = Shader(
                r"ModernOpenglFunc/GLSL/CurvedRectangle.vs.glsl",
                r"ModernOpenglFunc/GLSL/CurvedRectangle.fs.glsl",
            )
            self.Adas_Shader = Shader(
                r"ModernOpenglFunc/GLSL/adas.vs.glsl",
                r"ModernOpenglFunc/GLSL/adas.fs.glsl"

            )

        except Exception as e:
            print("着色器编译失败！")
            print(e)

    def init_speed_logo_func(self):
        #加速减速图标
        self.front_speed_movie = QMovie(r"image/front.gif")
        self.front_speed_texture_id = None
        self.front_speed_movie.frameChanged.connect(self.update_speed_texture)
        self.front_speed_movie.start()

        vertices = np.array([
            # positions       # texCoords

            3.55, -0.75, 0.3, 0.0, 0.0,
            3.55, 0.75, 0.3, 0.0, 1.0,
            10.0, 0.75, 0.3, 1.0, 1.0,
            10, -0.75, 0.3, 1.0, 0.0,
        ], dtype=np.float32)

        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

        self.pre_speed_logo_VAO = glGenVertexArrays(1)
        VBO = glGenBuffers(1)
        EBO = glGenBuffers(1)

        glBindVertexArray(self.pre_speed_logo_VAO)

        glBindBuffer(GL_ARRAY_BUFFER, VBO)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        # Position attribute
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # Texture coord attribute
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, ctypes.c_void_p(3 * vertices.itemsize))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)

        # Generate texture
        self.front_speed_texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.front_speed_texture_id)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    def draw_front_speed_logo(self, projection, view_m):
        if self.front_speed_texture_id is None:
            return
        self.PRE_SPEED_Shader.use()
        self.PRE_SPEED_Shader.setMat4('projection', projection)
        self.PRE_SPEED_Shader.setMat4('view', view_m)
        self.PRE_SPEED_Shader.setMat4('model', glm.mat4(1.0))
        self.PRE_SPEED_Shader.setInt("NEED_ROTATE", self.ACCU_PC_CLASS.speed_flag)
        glBindTexture(GL_TEXTURE_2D, self.front_speed_texture_id)
        glBindVertexArray(self.pre_speed_logo_VAO)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def draw_CurvedRectangle(self, projection, view_m):
        self.CurvedRectangle_Shader.use()
        check_shader_errors(self.CurvedRectangle_Shader.ID, 'program')
        self.CurvedRectangle_Shader.setMat4("projection", projection)
        self.CurvedRectangle_Shader.setMat4("view", view_m)
        self.CurvedRectangle_Shader.setMat4("model", glm.mat4(1.0))
        self.CurvedRectangle_Shader.setFloat("speed", self.ACCU_PC_CLASS.average_speed)
        # print(self.ACCU_PC_CLASS.average_speed)
        # print(self.ACCU_PC_CLASS.yaw_rate[3])
        self.CurvedRectangle_Shader.setFloat("yawrate", self.ACCU_PC_CLASS.yaw_rate[3])

        glBindVertexArray(self.CurvedRectangle_VAO)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 1000)

    def update_speed_texture(self):
        if self.front_speed_texture_id is None:
            return
        try:
            frame = self.front_speed_movie.currentImage()
            frame = frame.convertToFormat(QImage.Format_RGBA8888)
            width = frame.width()
            height = frame.height()

            frame_bits = frame.bits()
            frame_bits.setsize(frame.byteCount())
            frame_data = np.frombuffer(frame_bits, np.uint8)

            glBindTexture(GL_TEXTURE_2D, self.front_speed_texture_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, frame_data)
        except AttributeError as e:
            # print(e)
            return

    def load_logo_texture(self, image_path):
        image = QImage(image_path)
        if image.isNull():
            print(f"Failed to load image from {image_path}")
            return None

        # Convert the image to a format that can be used by OpenGL
        image = image.convertToFormat(QImage.Format_RGBA8888)
        width, height = image.width(), image.height()

        # Convert QImage to numpy array
        data = np.frombuffer(image.bits().asstring(image.bytesPerLine() * height), dtype=np.uint8)
        data = data.reshape((height, width, 4))  # RGBA format

        # Generate and bind texture
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        # Load the texture data into OpenGL
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

        # Set texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glBindTexture(GL_TEXTURE_2D, 0)  # Unbind the texture

        return texture_id

    def draw_logo(self):
        glBindTexture(GL_TEXTURE_2D, self.logo_texture)
        glEnable(GL_TEXTURE_2D)

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(-1.0, -1.0)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(1.0, -1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(1.0, 1.0)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(-1.0, 1.0)
        glEnd()

        glDisable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, 0)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        # print(width, height)
        self.width = width
        self.height = height

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_W, Qt.Key_S, Qt.Key_A, Qt.Key_D):
            self.Camera.KeyFunc(event.key(), self.deltaTime)
        else:
            super(QOpenGLWidget, self).keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.Camera.MouseFunc(event.x(), event.y(), "mousePressEvent")

    def mouseMoveEvent(self, event):
        self.Camera.MouseFunc(event.x(), event.y(), "mouseMoveEvent")

    def wheelEvent(self, event):
        self.Camera.MouseFunc(event.angleDelta().y(), event.angleDelta().y(), "wheelEvent")

    def update_tracker_data_f(self, mat_list):
        self.all_return_mat_class_f = mat_list

    def update_tracker_data_r(self, mat_list):
        self.all_return_mat_class_r = mat_list

    def update_mount_info(self, this_time_mount):
        print(this_time_mount)
        for sensor_id in this_time_mount:
            self.MountInfo[sensor_id]["yaw"] = this_time_mount[sensor_id][0]
            self.MountInfo[sensor_id]["x"] = this_time_mount[sensor_id][1]["x"]
            self.MountInfo[sensor_id]["y"] = this_time_mount[sensor_id][1]["y"]
            self.MountInfo[sensor_id]["z"] = this_time_mount[sensor_id][1]["z"]
        # print(self.MountInfo)

    def update_pc_data(self, pc_list):
        SENSOR_ID = pc_list[0] - 1
        PC_NUM = pc_list[1]
        if PC_NUM == 0:
            return
        if self.ACCU_PC_CLASS.delta_t[SENSOR_ID] == 0:
            return
        PC_DATA = pc_list[2]
        self.PC_num[SENSOR_ID] = PC_NUM
        # print(self.PC_num)
        glBindBuffer(GL_ARRAY_BUFFER, self.PC_VBO[SENSOR_ID])
        point_size = PC_DATA.itemsize * PC_DATA.shape[1]
        data_size = min(PC_DATA.nbytes, self.max_buffer_size_pc)
        # 截取数据
        truncated_data = PC_DATA[:data_size // point_size]
        glBufferSubData(GL_ARRAY_BUFFER, 0, data_size, truncated_data)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        MountInfo = self.MountInfo[pc_list[0]]

        self.ACCU_PC_CLASS.last_pc_data[pc_list[0]] = truncated_data
        self.ACCU_PC_CLASS.last_pc_NUM[SENSOR_ID] = PC_NUM

        if self.ACCU_PC_CLASS.last_pc_data[pc_list[0]] is not None:
            extended_array, remaining_count = pick_accu_pc(self.ACCU_PC_CLASS.last_pc_data[pc_list[0]],
                                                           MountInfo["yaw"], MountInfo["x"], MountInfo["y"],
                                                           MountInfo["z"],
                                                           self.ACCU_PC_CLASS.last_car_position[SENSOR_ID][0],
                                                           self.ACCU_PC_CLASS.last_car_position[SENSOR_ID][1],
                                                           self.ACCU_PC_CLASS.last_theta[SENSOR_ID], pc_list[0]
                                                           )

            if self.ACCU_PC_CLASS.accu_pc_num + remaining_count > self.ACCU_PC_CONFIG_DICT["MAX_NUM"]:
                self.ACCU_PC_CLASS.accu_pc_num = 0
                # print("\n\n从0开始")

            glBindBuffer(GL_ARRAY_BUFFER, self.ACCU_PC_VBO)

            glBufferSubData(GL_ARRAY_BUFFER, self.ACCU_PC_CLASS.accu_pc_num * 12 * 4, extended_array.nbytes,
                            extended_array)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

            self.ACCU_PC_CLASS.accu_pc_num += remaining_count

    def update_fc_lines_data(self, fc_lines_array):
        extended_array, remaining_count = pick_accu_fc_lines(fc_lines_array, self.ACCU_PC_CLASS.last_car_position[3][0],
                                                             self.ACCU_PC_CLASS.last_car_position[3][1],
                                                             self.ACCU_PC_CLASS.last_theta[3])
        if self.ACCU_PC_CLASS.accu_fc_lines_num + remaining_count > MAX_ACCU_FS_LINES_NUM:
            self.ACCU_PC_CLASS.accu_fc_lines_num = 0
        glBindBuffer(GL_ARRAY_BUFFER, self.ACCU_FS_LINES_VBO)

        glBufferSubData(GL_ARRAY_BUFFER, self.ACCU_PC_CLASS.accu_fc_lines_num * 6 * 4, extended_array.nbytes,
                        extended_array)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        self.ACCU_PC_CLASS.accu_fc_lines_num += remaining_count

    def update_freespace_data(self, data):
        glBindBuffer(GL_ARRAY_BUFFER, self.fs_VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, data.nbytes, data)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        self.freespace_num = len(data)

    def draw_pc(self, projection, view_m):
        for sensor_id in range(1, 5):
            # print(self.MountInfo)
            # 传感器的角度
            sensor_angle = self.MountInfo[sensor_id]["yaw"]

            # 在 CPU 端预计算旋转矩阵
            angle_rad = glm.radians(sensor_angle)
            rotate_matrix0 = glm.vec4(
                glm.cos(angle_rad), glm.sin(angle_rad),
                -glm.sin(angle_rad), glm.cos(angle_rad)
            )

            self.PointCloudShader.use()
            check_shader_errors(self.PointCloudShader.ID, 'program')
            self.PointCloudShader.setMat4("projection", projection)
            self.PointCloudShader.setMat4("view", view_m)
            model_m = glm.mat4(1.0)
            self.PointCloudShader.setMat4("model", model_m)
            self.PointCloudShader.setVec4("rotate_matrix0", rotate_matrix0)
            self.PointCloudShader.setVec3f("sensor_pos", self.MountInfo[sensor_id]["x"],
                                           self.MountInfo[sensor_id]["y"],
                                           self.MountInfo[sensor_id]["z"])

            # glBindTransformFeedback(GL_TRANSFORM_FEEDBACK, self.transform_feedback[sensor_id - 1])
            # glBeginTransformFeedback(GL_POINTS)

            glBindVertexArray(self.PC_VAO[sensor_id - 1])

            glDrawArrays(GL_POINTS, 0, self.PC_num[sensor_id - 1])

            # glEndTransformFeedback()
            #
            # # # 读取反馈缓冲区中的数据
            # glBindBuffer(GL_ARRAY_BUFFER, self.feedback_buffer[sensor_id - 1])
            # feedback_data = glGetBufferSubData(GL_ARRAY_BUFFER, 0, 500 * 3 * 4)
            # feedback_array = np.frombuffer(feedback_data, dtype=np.float32).reshape(-1, 3)
            # #
            # # print("Feedback data:", feedback_array)

    def draw_accu_pc(self, projection, view_m):

        self.PC_ACCU_Shader.use()
        check_shader_errors(self.PC_ACCU_Shader.ID, 'program')
        self.PC_ACCU_Shader.setMat4("projection", projection)
        self.PC_ACCU_Shader.setMat4("view", view_m)
        self.PC_ACCU_Shader.setMat4("model", glm.mat4(1.0))
        self.PC_ACCU_Shader.setFloat("MIN_H",self.ACCU_PC_CONFIG_DICT["MIN_H"])
        self.PC_ACCU_Shader.setFloat("MAX_H", self.ACCU_PC_CONFIG_DICT["MAX_H"])
        self.PC_ACCU_Shader.setFloat("SIZE", self.ACCU_PC_CONFIG_DICT["SIZE"])

        for i in range(4):
            self.PC_ACCU_Shader.setVec3("model" + str(i + 1), glm.vec3(self.ACCU_PC_CLASS.car_position[i][0],
                                                                       self.ACCU_PC_CLASS.car_position[i][1],
                                                                       self.ACCU_PC_CLASS.theta[i]
                                                                       ))
        glBindVertexArray(self.ACCU_PC_VAO)
        glDrawArrays(GL_POINTS, 0, self.ACCU_PC_CONFIG_DICT["MAX_NUM"])
        glBindVertexArray(0)

    def draw_accu_fc_lines(self, projection, view_m):

        self.FC_LINES_ACCU_Shader.use()
        check_shader_errors(self.FC_LINES_ACCU_Shader.ID, 'program')
        self.FC_LINES_ACCU_Shader.setMat4("projection", projection)
        self.FC_LINES_ACCU_Shader.setMat4("view", view_m)
        self.FC_LINES_ACCU_Shader.setMat4("model", glm.mat4(1.0))

        self.FC_LINES_ACCU_Shader.setVec3("final_model", glm.vec3(self.ACCU_PC_CLASS.car_position[3][0],
                                                                  self.ACCU_PC_CLASS.car_position[3][1],
                                                                  self.ACCU_PC_CLASS.theta[3]
                                                                  ))
        glBindVertexArray(self.ACCU_FS_LINES_VAO)
        glDrawArrays(GL_POINTS, 0, MAX_ACCU_FS_LINES_NUM)
        glBindVertexArray(0)

    def draw_freespace(self, projection, view_m):
        if self.freespace_num > 1:
            self.FreespaceLineShader.use()
            self.FreespaceLineShader.setMat4("projection", projection)
            self.FreespaceLineShader.setMat4("view", view_m)
            model_m = glm.mat4(1.0)
            self.FreespaceLineShader.setMat4("model", model_m)
            glBindVertexArray(self.fs_VAO)
            glLineWidth(10)

            glDrawArrays(GL_LINE_LOOP, 1, int(self.freespace_num) - 1)

            self.FreespaceFaceShader.use()
            self.FreespaceFaceShader.setMat4("projection", projection)
            self.FreespaceFaceShader.setMat4("view", view_m)
            model_m = glm.mat4(1.0)
            self.FreespaceFaceShader.setMat4("model", model_m)
            glDrawArrays(GL_TRIANGLE_FAN, 0, int(self.freespace_num))
            glBindVertexArray(0)

    def update_guardrail_data(self, data_sensor_list):
        sensor_id = data_sensor_list[0] - 1
        data = data_sensor_list[1]
        self.gr_num[sensor_id] = len(data)
        glBindBuffer(GL_ARRAY_BUFFER, self.gr_VBO[sensor_id])
        glBufferSubData(GL_ARRAY_BUFFER, 0, data.nbytes, data)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def draw_guardrail(self, projection, view_m):

        self.GuardrailLineShader_shu.use()
        self.GuardrailLineShader_shu.setMat4("projection", projection)
        self.GuardrailLineShader_shu.setMat4("view", view_m)
        model_m = glm.mat4(1.0)
        self.GuardrailLineShader_shu.setMat4("model", model_m)

        glLineWidth(2)
        for sensor_id in range(4):
            glBindVertexArray(self.gr_VAO[sensor_id])
            glDrawArrays(GL_POINTS, 0, int(self.gr_num[sensor_id]))
            glBindVertexArray(0)

        self.GuardrailLineShader_heng1.use()
        self.GuardrailLineShader_heng1.setMat4("projection", projection)
        self.GuardrailLineShader_heng1.setMat4("view", view_m)
        model_m = glm.mat4(1.0)
        self.GuardrailLineShader_heng1.setMat4("model", model_m)
        for sensor_id in range(4):
            glBindVertexArray(self.gr_VAO[sensor_id])
            glDrawArrays(GL_LINE_STRIP, 0, int(self.gr_num[sensor_id]))
            glBindVertexArray(0)

        self.GuardrailLineShader_heng2.use()
        self.GuardrailLineShader_heng2.setMat4('projection', projection)
        self.GuardrailLineShader_heng2.setMat4('view', view_m)
        model_m = glm.mat4(1.0)
        self.GuardrailLineShader_heng2.setMat4("model", model_m)
        for sensor_id in range(4):
            glBindVertexArray(self.gr_VAO[sensor_id])
            glDrawArrays(GL_LINE_STRIP, 0, int(self.gr_num[sensor_id]))
            glBindVertexArray(0)

    def draw_tracker(self, projection, view_m):
        _temp_tracker = list(itertools.chain(self.all_return_mat_class_f, self.all_return_mat_class_r))
        self.TrackerShader.use()
        self.TrackerShader.setVec3f('lightColor1', 0.5, 0.5, 0.5)
        self.TrackerShader.setVec3('lightPos1', glm.vec3(-50, 100, -100))
        self.TrackerShader.setVec3f('lightColor2', 0.5, 0.5, 0.5)
        self.TrackerShader.setVec3('lightPos2', glm.vec3(100, -5, 100))

        self.TrackerShader.setVec3f('objectColor', 255 / 255.0, 255 / 255.0, 255 / 255.0)
        self.TrackerShader.setVec3("viewPos", self.Camera.cameraPos)

        # projection = glm.ortho(-10 * 1300 / 600, 10 * 1300 / 600, -10, 10, -10, 10)
        self.TrackerShader.setMat4("projection", projection)

        self.TrackerShader.setMat4("view", view_m)
        model_m = glm.mat4(1.0)
        self.TrackerShader.setMat4("model", model_m)
        # print("OPENGL:", len(self.all_return_mat_class_f),len(self.all_return_mat_class_r))
        for single_mat_class in _temp_tracker:
            this_mat = single_mat_class[0]
            this_class = single_mat_class[1]
            if this_class in (6,):
                model_car = this_mat * self.animal_init_model_mat

                self.TrackerShader.setMat4("model", model_car)

                for index, i in enumerate(self.OBJ_RETURN_DICT["ANIMAL"].VAOs):
                    if self.OBJ_RETURN_DICT["ANIMAL"].checkbox[index]:
                        glBindVertexArray(i['VAO'])
                        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                        glDrawElements(GL_TRIANGLES, len(i['Index']), GL_UNSIGNED_INT, None)
                        glBindVertexArray(0)
            if this_class in (3,):
                model_car = this_mat * self.bike_init_model_car_mat

                self.TrackerShader.setMat4("model", model_car)

                for index, i in enumerate(self.OBJ_RETURN_DICT["BIKE"].VAOs):
                    if self.OBJ_RETURN_DICT["BIKE"].checkbox[index]:
                        glBindVertexArray(i['VAO'])
                        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                        glDrawElements(GL_TRIANGLES, len(i['Index']), GL_UNSIGNED_INT, None)
                        glBindVertexArray(0)
            if this_class in (1, 7, 5):
                model_car = this_mat * self.car_init_model_car_mat

                self.TrackerShader.setMat4("model", model_car)

                for index, i in enumerate(self.OBJ_RETURN_DICT["CAR"].VAOs):
                    if self.OBJ_RETURN_DICT["CAR"].checkbox[index]:
                        glBindVertexArray(i['VAO'])
                        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                        glDrawElements(GL_TRIANGLES, len(i['Index']), GL_UNSIGNED_INT, None)
                        glBindVertexArray(0)
            if this_class in (2,):
                model_car = this_mat * self.truck_init_model_truck_mat

                self.TrackerShader.setMat4("model", model_car)

                for index, i in enumerate(self.OBJ_RETURN_DICT["TRUCK"].VAOs):
                    if self.OBJ_RETURN_DICT["TRUCK"].checkbox[index]:
                        glBindVertexArray(i['VAO'])
                        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                        glDrawElements(GL_TRIANGLES, len(i['Index']), GL_UNSIGNED_INT, None)
                        glBindVertexArray(0)
            if this_class in (4,):
                model_ped = this_mat * self.pedestrain_init_model_mat

                self.TrackerShader.setMat4("model", model_ped)

                for index, i in enumerate(self.OBJ_RETURN_DICT["PEDESTRIAN"].VAOs):
                    if self.OBJ_RETURN_DICT["PEDESTRIAN"].checkbox[index]:
                        glBindVertexArray(i['VAO'])
                        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                        glDrawElements(GL_TRIANGLES, len(i['Index']), GL_UNSIGNED_INT, None)
                        glBindVertexArray(0)

    def draw_self_car(self):

        self.SelfCarShader.use()
        self.SelfCarShader.setVec3f('objectColor', 210 / 255.0, 210 / 255.0, 210 / 255.0)
        self.TrackerShader.setVec3f('lightColor1', 1.0, 1.0, 1.0)
        self.TrackerShader.setVec3('lightPos1', glm.vec3(-50, 100, -100))
        self.TrackerShader.setVec3f('lightColor2', 0.5, 0.5, 0.5)
        self.TrackerShader.setVec3('lightPos2', glm.vec3(100, -5, 100))
        self.SelfCarShader.setVec3("viewPos", self.Camera.cameraPos)
        projection = glm.perspective(glm.radians(self.Camera.fov), self.width / self.height, 0.1, 1000)
        self.SelfCarShader.setMat4("projection", projection)
        view_m = self.Camera.GetViewMatrix()
        self.SelfCarShader.setMat4("view", view_m)
        self.SelfCarShader.setMat4("model", self.car_init_model_car_mat)

        # print("cameraPos:",self.Camera.cameraPos,"\n","cameraFront",self.Camera.cameraFront,"\n","cameraUp",self.Camera.cameraUp,"\n\n")

        for index, i in enumerate(self.OBJ_RETURN_DICT["CAR"].VAOs):
            if self.OBJ_RETURN_DICT["CAR"].checkbox[index]:
                glBindVertexArray(i['VAO'])
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                glDrawElements(GL_TRIANGLES, len(i['Index']), GL_UNSIGNED_INT, None)
                glBindVertexArray(0)
        return projection, view_m

    def draw_ground(self, projection, view_m):
        self.GroundShader.use()
        self.GroundShader.setMat4('projection', projection)
        self.GroundShader.setMat4('view', view_m)
        model_light = glm.mat4(1.0)
        model_light = glm.translate(model_light, self.lightPos)
        model_light = glm.scale(model_light, glm.vec3(0.2))
        self.GroundShader.setMat4('model', model_light)
        glBindVertexArray(self.groundVAO)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def draw_adas(self, projection, view_m):
        self.Adas_Shader.use()
        self.Adas_Shader.setMat4('projection', projection)
        self.Adas_Shader.setMat4('view', view_m)
        self.Adas_Shader.setMat4('model', glm.mat4(1.0))
        glBindVertexArray(self.adasVAO)

        # print(self.ADAS_Info_dict)
        fan_indices_num = 150
        triangles_indices_num = 6

        if self.ADAS_Info_dict["BSD_LCA_L"]["StateCurrent"] in (2, 3, 6, 4, 5):
            self.Adas_Shader.setInt("ADAS_TYPE",0)
            self.Adas_Shader.setInt("ADAS_STATE", self.ADAS_Info_dict["BSD_LCA_L"]["StateCurrent"])
            self.Adas_Shader.setInt("ADAS_LEVEL", self.ADAS_Info_dict["BSD_LCA_L"]["Warning_Level"])
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, ctypes.c_void_p(0))  # BSD_LCA_L

        if self.ADAS_Info_dict["BSD_LCA_R"]["StateCurrent"] in (2, 3, 6, 4, 5):
            self.Adas_Shader.setInt("ADAS_TYPE",1)
            self.Adas_Shader.setInt("ADAS_STATE", self.ADAS_Info_dict["BSD_LCA_R"]["StateCurrent"])
            self.Adas_Shader.setInt("ADAS_LEVEL", self.ADAS_Info_dict["BSD_LCA_R"]["Warning_Level"])
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, ctypes.c_void_p(triangles_indices_num * 4))  # BSD_LCA_R

        triangles_indices_num += 6

        if self.ADAS_Info_dict["RCW"]["StateCurrent"] in (2, ):
            self.Adas_Shader.setInt("ADAS_TYPE",2)
            self.Adas_Shader.setInt("ADAS_STATE", self.ADAS_Info_dict["RCW"]["StateCurrent"])
            self.Adas_Shader.setInt("ADAS_LEVEL", self.ADAS_Info_dict["RCW"]["Warning_Level"])
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, ctypes.c_void_p(triangles_indices_num * 4))  # RCW


        triangles_indices_num += 6

        if self.ADAS_Info_dict["DOW_L"]["StateCurrent"] in (2, ):
            self.Adas_Shader.setInt("ADAS_TYPE",3)
            self.Adas_Shader.setInt("ADAS_STATE", self.ADAS_Info_dict["DOW_L"]["StateCurrent"])
            self.Adas_Shader.setInt("ADAS_LEVEL", self.ADAS_Info_dict["DOW_L"]["Warning_Level"])
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, ctypes.c_void_p(triangles_indices_num * 4))  # DOWL

        triangles_indices_num += 6

        if self.ADAS_Info_dict["DOW_R"]["StateCurrent"] in (2, ):
            self.Adas_Shader.setInt("ADAS_TYPE",4)
            self.Adas_Shader.setInt("ADAS_STATE", self.ADAS_Info_dict["DOW_R"]["StateCurrent"])
            self.Adas_Shader.setInt("ADAS_LEVEL", self.ADAS_Info_dict["DOW_R"]["Warning_Level"])
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, ctypes.c_void_p(triangles_indices_num * 4))  # DOWR

        triangles_indices_num += 6

        if self.ADAS_Info_dict["FCTB"]["StateCurrent"] in (1, ):
            self.Adas_Shader.setInt("ADAS_TYPE",5)
            self.Adas_Shader.setInt("ADAS_STATE", self.ADAS_Info_dict["FCTB"]["StateCurrent"])
            self.Adas_Shader.setInt("ADAS_LEVEL", self.ADAS_Info_dict["FCTB"]["Warning_Level"])
            glDrawElements(GL_TRIANGLES, 36, GL_UNSIGNED_INT, ctypes.c_void_p(triangles_indices_num * 4))  # FCTB


        triangles_indices_num += 36

        if self.ADAS_Info_dict["RCTB"]["StateCurrent"] in (1, ):
            self.Adas_Shader.setInt("ADAS_TYPE",6)
            self.Adas_Shader.setInt("ADAS_STATE", self.ADAS_Info_dict["RCTB"]["StateCurrent"])
            self.Adas_Shader.setInt("ADAS_LEVEL", self.ADAS_Info_dict["RCTB"]["Warning_Level"])
            glDrawElements(GL_TRIANGLES, 36, GL_UNSIGNED_INT, ctypes.c_void_p(triangles_indices_num * 4))  # RCTB
        triangles_indices_num += 36




        fan_indices_offset = triangles_indices_num
        if self.ADAS_Info_dict["FCTA_L"]["StateCurrent"] in (2, ):
            self.Adas_Shader.setInt("ADAS_TYPE",7)
            self.Adas_Shader.setInt("ADAS_STATE", self.ADAS_Info_dict["FCTA_L"]["StateCurrent"])
            self.Adas_Shader.setInt("ADAS_LEVEL", self.ADAS_Info_dict["FCTA_L"]["Warning_Level"])
            glDrawElements(GL_TRIANGLES, 150, GL_UNSIGNED_INT, ctypes.c_void_p(fan_indices_offset * 4))  #FCTA_L

        fan_indices_offset += fan_indices_num
        if self.ADAS_Info_dict["FCTA_R"]["StateCurrent"] in (2, ):
            self.Adas_Shader.setInt("ADAS_TYPE",8)
            self.Adas_Shader.setInt("ADAS_STATE", self.ADAS_Info_dict["FCTA_R"]["StateCurrent"])
            self.Adas_Shader.setInt("ADAS_LEVEL", self.ADAS_Info_dict["FCTA_R"]["Warning_Level"])
            glDrawElements(GL_TRIANGLES, 150, GL_UNSIGNED_INT, ctypes.c_void_p(fan_indices_offset * 4))  #FCTA_R

        fan_indices_offset += fan_indices_num
        if self.ADAS_Info_dict["RCTA_L"]["StateCurrent"] in (2, ):
            self.Adas_Shader.setInt("ADAS_TYPE",9)
            self.Adas_Shader.setInt("ADAS_STATE", self.ADAS_Info_dict["RCTA_L"]["StateCurrent"])
            self.Adas_Shader.setInt("ADAS_LEVEL", self.ADAS_Info_dict["RCTA_L"]["Warning_Level"])
            glDrawElements(GL_TRIANGLES, 150, GL_UNSIGNED_INT, ctypes.c_void_p(fan_indices_offset * 4))  #RCTA_L

        fan_indices_offset += fan_indices_num
        if self.ADAS_Info_dict["RCTA_R"]["StateCurrent"] in (2, ):
            self.Adas_Shader.setInt("ADAS_TYPE",10)
            self.Adas_Shader.setInt("ADAS_STATE", self.ADAS_Info_dict["RCTA_R"]["StateCurrent"])
            self.Adas_Shader.setInt("ADAS_LEVEL", self.ADAS_Info_dict["RCTA_R"]["Warning_Level"])
            glDrawElements(GL_TRIANGLES, 150, GL_UNSIGNED_INT, ctypes.c_void_p(fan_indices_offset * 4))   #RCTA_R
        glBindVertexArray(0)

    def closeEvent(self, event):
        if self.logo_texture:
            glDeleteTextures([self.logo_texture])
        super().closeEvent(event)

    def update_vehicle_info_dict(self, this_vehicle_info_dict):
        self.vehicle_info_dict = this_vehicle_info_dict
        self.ACCU_PC_CLASS.update_car_position(self.vehicle_info_dict)

    def update_ADAS_Info(self,ADAS_Info_dict):
        self.ADAS_Info_dict = copy.deepcopy(ADAS_Info_dict)

    def update_accu_config(self,accu_config_dict):
        self.ACCU_PC_CONFIG_DICT = copy.deepcopy(accu_config_dict)

    def draw_vehicle_info(self):
        # 使用QPainter绘制方向盘
        glBindVertexArray(0)
        steering_wheel_painter = QPainter(self)
        steering_wheel_painter.setRenderHint(QPainter.Antialiasing)
        # 设置图片透明度
        steering_wheel_painter.setOpacity(0.8)

        # 创建一个QTransform来旋转图片
        steering_wheel_transform = QTransform()
        steering_wheel_transform.translate(self.steering_wheel_img.width() / 4, self.steering_wheel_img.height() / 4)
        steering_wheel_transform.rotate(-self.vehicle_info_dict["streeing_angle"])
        steering_wheel_transform.scale(0.5, 0.5)
        steering_wheel_transform.translate(-self.steering_wheel_img.width() // 2,
                                           -self.steering_wheel_img.height() // 2)
        # 绘制旋转后的方向盘图片
        steering_wheel_painter.setTransform(steering_wheel_transform)
        steering_wheel_painter.drawImage(0, 0, self.steering_wheel_img)
        steering_wheel_painter.end()

        # 设置字体和大小
        font_painter = QPainter(self)
        font = QFont("Arial", 35)
        font.setBold(True)  # 设置加粗
        font_painter.setFont(font)
        # 设置文本颜色
        font_painter.setPen(Qt.lightGray)

        # 绘制文本
        font_painter.drawText(15, 150, str(int(self.ACCU_PC_CLASS.average_speed)))

        font = QFont("Arial", 8)
        font.setBold(False)  # 设置加粗
        font_painter.setFont(font)
        # 设置文本颜色
        font_painter.setPen(Qt.lightGray)
        font_painter.drawText(67, 162, str("KM/H"))

        font = QFont("Arial", 8)
        font.setBold(False)  # 设置加粗
        font_painter.setFont(font)
        # 设置文本颜色
        font_painter.setPen(Qt.lightGray)
        font_painter.drawText(self.width - 50, 12, f"{self.fps:.2f} FPS")

        font_painter.end()

        if self.left_func.light_is_on:
            self.draw_left(1)

        if self.right_func.light_is_on:
            self.draw_right(1)

        glBindVertexArray(0)

    def draw_left(self, enable=0):
        left_painter = QPainter(self)
        left_painter.setRenderHint(QPainter.Antialiasing)
        # 设置图片透明度
        left_painter.setOpacity(0.8)
        left_transform = QTransform()
        left_transform.translate(5, 153)
        left_transform.scale(0.2, 0.2)

        # 绘制旋转后的方向盘图片
        left_painter.setTransform(left_transform)
        if enable == 0:
            left_painter.drawImage(0, 0, self.left_img)
        else:
            left_painter.drawImage(0, 0, self.left_enable_img)
        left_painter.end()

    def draw_right(self, enable=0):
        right_painter = QPainter(self)
        right_painter.setRenderHint(QPainter.Antialiasing)
        # 设置图片透明度
        right_painter.setOpacity(0.8)
        right_transform = QTransform()
        right_transform.translate(45, 153)
        right_transform.scale(0.2, 0.2)

        # 绘制旋转后的方向盘图片
        right_painter.setTransform(right_transform)
        if enable == 0:
            right_painter.drawImage(0, 0, self.right_img)
        else:
            right_painter.drawImage(0, 0, self.right_enable_img)
        right_painter.end()
