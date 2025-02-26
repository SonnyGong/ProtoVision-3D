# This is a sample Python script.
import copy
import math
import multiprocessing
import sys
from ctypes import CDLL
from typing import Callable

import glm
import numpy as np

from PyQt5.QtCore import pyqtSignal, QThread, Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidgetAction, QDoubleSpinBox, QLabel, QSpinBox
from ModernOpenglFunc.ModernOpenGLFunc import GWidget, ADAS_Info_BLANK_dict, MAX_ACCU_PC_NUM
import pywinstyles
import qtawesome
from tcpip_func import server_receive_data
from window import *

from qt_material import apply_stylesheet


ViewPort_dict = {
    "RESET":{
        "cameraPos":glm.vec3(1,20,35),
        "cameraFront":glm.vec3(-0.01,-0.4,-1),
        "cameraUp":glm.vec3(0,1,0),
    },
    "ON": {
        "cameraPos": glm.vec3(3, 30, 10),
        "cameraFront": glm.vec3(-0.005, -1, -0.1),
        "cameraUp": glm.vec3(0, 1, 0),
    }
}

def process_and_emit_pc_data(pc_data, trigger_signal: Callable,index):
    pc_list = [(pc.Range_m, pc.Elevation_deg, pc.Azimuth_deg, pc.Infrastructure) for pc in pc_data]
    pc_num = len(pc_list)
    vbo_data_np = np.array(pc_list, dtype=np.float32)
    trigger_signal.emit([index, pc_num, vbo_data_np])


def process_and_emit_tracker_data(tk_data, trigger_signal: Callable):
    all_return_mat_list = []
    temp_tk_list = [(tk.x, tk.y, tk.heading, tk.class_of_tk) for tk in tk_data]

    for single_tk in temp_tk_list:
        x, y, heading, class_of_tk = single_tk
        model_car = glm.translate(glm.mat4(1.0), glm.vec3(-y, 0.0, -x))
        model_car = glm.rotate(model_car, math.radians(heading), glm.vec3(0.0, 1.0, 0.0))
        all_return_mat_list.append([model_car, class_of_tk])

    trigger_signal.emit(all_return_mat_list)


def process_and_emit_guardrail_data(guardrail_data, signal_emit: Callable, identifier: int):
    """
    处理护栏数据并通过指定的信号发射器发出信号。

    :param guardrail_data: 护栏数据的 protobuf 消息列表
    :param signal_emit: 用于发射信号的 emit 方法
    :param identifier: 用于区分不同护栏的数据标识符
    """
    # 提取数据并转换为 numpy 数组
    _gr_list = [(gr.x, gr.y, gr.z) for gr in guardrail_data]
    data_array = np.array(_gr_list, dtype=np.float32)

    # 发出信号
    signal_emit.emit([identifier, data_array])

def process_and_emit_vehicle_data(VehicleCommonInfo,Veh_radar_list, signal_emit: Callable):
    this_vehicle_info_dict = {
        "streeing_angle": VehicleCommonInfo.streeing_angle,
        "turnlight_l": VehicleCommonInfo.turnlight_l,
        "turnlight_r": VehicleCommonInfo.turnlight_r,

    }
    Sensor_ID = 1
    for single_Veh in Veh_radar_list:
        this_vehicle_info_dict["velocity" + str(Sensor_ID)] = single_Veh.velocity
        this_vehicle_info_dict["yawrate" + str(Sensor_ID)] = single_Veh.yawrate
        this_vehicle_info_dict["chriptime" + str(Sensor_ID)] = single_Veh.chriptime
        Sensor_ID += 1
    # print(this_vehicle_info_dict)
    signal_emit.emit(this_vehicle_info_dict)


def process_and_emit_camera_data(camera_list, signal_emit: Callable):
    index = 0
    emit_list = [None,None,None,None]
    for camera in camera_list:
        if len(camera.data) != 0:
            img = QImage.fromData(camera.data, camera.format)
            # 缩小图像
            scaled_img = img.scaled(img.width() // 2, img.height() // 2, Qt.KeepAspectRatio)
            emit_list[index] = scaled_img
            index += 1
    signal_emit.emit(emit_list)


def process_and_emit_fs_data(fs_data, trigger_update_freespace: Callable):
    fs_list = [(fs.x, fs.y, fs.z) for fs in fs_data]
    if len(fs_list) > 0:
        data_array = np.array(fs_list, dtype=np.float32)
        trigger_update_freespace.emit(data_array)


def process_and_emit_fc_lines_data(fc_line_data, trigger_update_fc_lines: Callable):
    fc_line_list = [(fc_line.x, fc_line.y, fc_line.z) for fc_line in fc_line_data]
    if len(fc_line_list) > 0:
        data_array = np.array(fc_line_list, dtype=np.float32)
        trigger_update_fc_lines.emit(data_array)


def process_and_emit_NetWork_Info(NetWork_Info, trigger_update_NetWork_Info: Callable):

    trigger_update_NetWork_Info.emit(NetWork_Info)


def process_and_emit_ADAS_INFO(ADAS_INFO, trigger_update_ADAS_Info: Callable):
    _temp_dict = copy.deepcopy(ADAS_Info_BLANK_dict)
    _temp_dict["BSD_LCA_L"]["StateCurrent"] = ADAS_INFO.BSD_LCA_L.StateCurrent
    _temp_dict["BSD_LCA_L"]["Warning_Level"] = ADAS_INFO.BSD_LCA_L.Warning_Level

    _temp_dict["BSD_LCA_R"]["StateCurrent"] = ADAS_INFO.BSD_LCA_R.StateCurrent
    _temp_dict["BSD_LCA_R"]["Warning_Level"] = ADAS_INFO.BSD_LCA_R.Warning_Level

    _temp_dict["DOW_L"]["StateCurrent"] = ADAS_INFO.DOW_L.StateCurrent
    _temp_dict["DOW_L"]["Warning_Level"] = ADAS_INFO.DOW_L.Warning_Level

    _temp_dict["DOW_R"]["StateCurrent"] = ADAS_INFO.DOW_R.StateCurrent
    _temp_dict["DOW_R"]["Warning_Level"] = ADAS_INFO.DOW_R.Warning_Level

    _temp_dict["RCTB"]["StateCurrent"] = ADAS_INFO.RCTB.StateCurrent

    _temp_dict["RCTA_L"]["StateCurrent"] = ADAS_INFO.RCTA_L.StateCurrent
    _temp_dict["RCTA_L"]["Warning_Level"] = ADAS_INFO.RCTA_L.Warning_Level

    _temp_dict["RCTA_R"]["StateCurrent"] = ADAS_INFO.RCTA_R.StateCurrent
    _temp_dict["RCTA_R"]["Warning_Level"] = ADAS_INFO.RCTA_R.Warning_Level

    _temp_dict["RCW"]["StateCurrent"] = ADAS_INFO.RCW.StateCurrent
    _temp_dict["RCW"]["Warning_Level"] = ADAS_INFO.RCW.Warning_Level


    _temp_dict["FCTA_L"]["StateCurrent"] = ADAS_INFO.FCTA_L.StateCurrent
    _temp_dict["FCTA_L"]["Warning_Level"] = ADAS_INFO.FCTA_L.Warning_Level

    _temp_dict["FCTA_R"]["StateCurrent"] = ADAS_INFO.FCTA_R.StateCurrent
    _temp_dict["FCTA_R"]["Warning_Level"] = ADAS_INFO.FCTA_R.Warning_Level

    _temp_dict["FCTB"]["StateCurrent"] = ADAS_INFO.FCTB.StateCurrent

    trigger_update_ADAS_Info.emit(_temp_dict)


def process_and_emit_MountInfo(RadarMnt_1,RadarMnt_2,RadarMnt_3,RadarMnt_4, trigger_update_mount: Callable):
    temp_mount_dict = {}
    temp_mount_dict[1] = [RadarMnt_1.yaw, {"x": RadarMnt_1.x, "y": RadarMnt_1.y, "z": RadarMnt_1.z}]
    temp_mount_dict[2] = [RadarMnt_2.yaw, {"x": RadarMnt_2.x, "y": RadarMnt_2.y, "z": RadarMnt_2.z}]
    temp_mount_dict[3] = [RadarMnt_3.yaw, {"x": RadarMnt_3.x, "y": RadarMnt_3.y, "z": RadarMnt_3.z}]
    temp_mount_dict[4] = [RadarMnt_4.yaw, {"x": RadarMnt_4.x, "y": RadarMnt_4.y, "z": RadarMnt_4.z}]
    trigger_update_mount.emit(copy.deepcopy(temp_mount_dict))


class Worker(QThread):
    trigger_update_opengl = pyqtSignal()
    trigger_update_freespace = pyqtSignal(np.ndarray)
    trigger_update_fc_lines = pyqtSignal(np.ndarray)
    trigger_update_mount = pyqtSignal(dict)
    trigger_update_pc = pyqtSignal(list)
    trigger_update_tracker_f = pyqtSignal(list)
    trigger_update_tracker_r = pyqtSignal(list)
    trigger_update_guardrail = pyqtSignal(list)
    trigger_update_camera = pyqtSignal(list)
    trigger_update_vehicleinfo = pyqtSignal(dict)
    trigger_update_NetWork_Info = pyqtSignal(dict)
    trigger_update_ADAS_Info = pyqtSignal(dict)
    def __init__(self,GET_QUEUE):
        super().__init__()  # 调用父类构造函数
        self.GET_QUEUE = GET_QUEUE




    def run(self):
        while True:
            ONE_FRAME_DATA,NetWork_Info = self.GET_QUEUE.get()

            process_and_emit_MountInfo(ONE_FRAME_DATA.RadarMnt_1,ONE_FRAME_DATA.RadarMnt_2,ONE_FRAME_DATA.RadarMnt_3,ONE_FRAME_DATA.RadarMnt_4, self.trigger_update_mount)


            process_and_emit_NetWork_Info(NetWork_Info,self.trigger_update_NetWork_Info)

            process_and_emit_ADAS_INFO(ONE_FRAME_DATA.ADAS_INFO,self.trigger_update_ADAS_Info)

            process_and_emit_camera_data([ONE_FRAME_DATA.Camera1,ONE_FRAME_DATA.Camera2,ONE_FRAME_DATA.Camera3,ONE_FRAME_DATA.Camera4],self.trigger_update_camera)

            process_and_emit_vehicle_data(ONE_FRAME_DATA.VehicleCommonInfo,
                                          [ONE_FRAME_DATA.Veh1,
                                          ONE_FRAME_DATA.Veh2,
                                          ONE_FRAME_DATA.Veh3,
                                          ONE_FRAME_DATA.Veh4,],

                                          self.trigger_update_vehicleinfo)

            process_and_emit_pc_data(ONE_FRAME_DATA.pc1, self.trigger_update_pc,1)

            process_and_emit_pc_data(ONE_FRAME_DATA.pc2, self.trigger_update_pc, 2)

            process_and_emit_pc_data(ONE_FRAME_DATA.pc3, self.trigger_update_pc, 3)

            process_and_emit_pc_data(ONE_FRAME_DATA.pc4, self.trigger_update_pc, 4)

            process_and_emit_tracker_data(ONE_FRAME_DATA.tk1, self.trigger_update_tracker_f)

            process_and_emit_tracker_data(ONE_FRAME_DATA.tk3, self.trigger_update_tracker_r)

            process_and_emit_guardrail_data(ONE_FRAME_DATA.gr1, self.trigger_update_guardrail, 1)
            process_and_emit_guardrail_data(ONE_FRAME_DATA.gr2, self.trigger_update_guardrail, 2)
            process_and_emit_guardrail_data(ONE_FRAME_DATA.gr3, self.trigger_update_guardrail, 3)
            process_and_emit_guardrail_data(ONE_FRAME_DATA.gr4, self.trigger_update_guardrail, 4)

            process_and_emit_fs_data(ONE_FRAME_DATA.fs, self.trigger_update_freespace)
            process_and_emit_fc_lines_data(ONE_FRAME_DATA.fc_lines,self.trigger_update_fc_lines)





            self.trigger_update_opengl.emit()


class mainui(QMainWindow):
    trigger_update_accu_config = pyqtSignal(dict)

    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.openGLWidget = GWidget(self)
        self.ui.openGLWidget.setMinimumSize(QtCore.QSize(480, 230))
        self.ui.gridLayout_4.addWidget(self.ui.openGLWidget, 0, 0, 16, 21)
        pywinstyles.apply_style(self, "mica")
        self.start_task()
        self.camera_label_init()
        # 应用 QMenu 的 QSS
        self.setStyleSheet("""
            QMenu {
                background-color: #333300;
            }
            QMenu::item {
                color: #ffffff;
            }
            QMenu::item:checked {
                background-color: #cccc66;
                color: black;
                }
        """)
        self.ui.action_pc.triggered.connect(self.update_opengl_checkbox_pc)
        self.ui.action_fs.triggered.connect(self.update_opengl_checkbox_fs)
        self.ui.action_fcline.triggered.connect(self.update_opengl_checkbox_fc_lines)
        self.ui.action_tracker.triggered.connect(self.update_opengl_checkbox_tracker)
        self.ui.action_pcaccu.triggered.connect(self.update_opengl_checkbox_accu_pc)
        self.ui.action_adas.triggered.connect(self.update_opengl_checkbox_adas)
        self.ui.action_gr.triggered.connect(self.update_opengl_checkbox_gr)

        self.ACCU_MENU_SET()

        self.ui.action_look_cycle.triggered.connect(self.camera_view_set_cycle)
        self.ui.action_look_reset.triggered.connect(self.camera_view_set_reset)
        self.ui.action_look_on.triggered.connect(self.camera_view_set_on)

    def camera_view_set_on(self):
        # 目标摄像头参数
        self.ui.openGLWidget.Camera.cameraPos = glm.vec3(-2.30707, 55.7652, -10.3427)
        self.ui.openGLWidget.Camera.cameraFront = glm.vec3(-1.83074e-17, -0.999848,   -0.0174524)
        self.ui.openGLWidget.update()




    def camera_view_set_reset(self):
        self.ui.openGLWidget.Camera.cameraPos = glm.vec3(1,20,35)
        self.ui.openGLWidget.Camera.cameraFront = glm.vec3(-0.00963933,-0.390731,-0.920454)
        self.ui.openGLWidget.update()



    def camera_view_set_cycle(self):
        if self.ui.action_look_cycle.isChecked():
            self.step_size_cycle = 0.001  # 每次步进的大小
            self.radius_cycle = glm.length(glm.vec3(self.ui.openGLWidget.Camera.cameraPos.x, 0, self.ui.openGLWidget.Camera.cameraPos.z))  # 平面上距离原点的半径
            self.theta_cycle = math.atan2(self.ui.openGLWidget.Camera.cameraPos.z, self.ui.openGLWidget.Camera.cameraPos.x)  # 初始角度 (绕Y轴的角度)

            # 设置计时器
            self.timer_cycle = QTimer(self)
            self.timer_cycle.timeout.connect(self.step_towards_target_cycle)

            self.timer_cycle.start(10)  # 每10ms触发一次
        else:
            self.timer_cycle.stop()

    def step_towards_target_cycle(self):
        # 计算两个 vec3 之间的差值


        self.theta_cycle += 0.01

        # 更新摄像头的位置，保持 y 不变
        self.ui.openGLWidget.Camera.cameraPos.x = self.radius_cycle * math.cos(self.theta_cycle)
        self.ui.openGLWidget.Camera.cameraPos.z = self.radius_cycle * math.sin(self.theta_cycle)

        # 保持摄像头始终朝向原点
        self.ui.openGLWidget.Camera.cameraFront = glm.normalize(-self.ui.openGLWidget.Camera.cameraPos)
        self.ui.openGLWidget.update()




    def ACCU_MENU_SET(self):
        widget_action = QWidgetAction(self)
        # 创建 QDoubleSpinBox 并将其添加到 QMenu 中
        _temp = QLabel(self)
        _temp.setText("最小高度(m)")
        widget_action.setDefaultWidget(_temp)
        self.ui.menu_accu_pc.addAction(widget_action)

        widget_action = QWidgetAction(self)
        # 创建 QDoubleSpinBox 并将其添加到 QMenu 中
        self.accu_min_height_spin_box = QDoubleSpinBox(self)
        self.accu_min_height_spin_box.setRange(0.0, 15.0)  # 设置范围
        self.accu_min_height_spin_box.setSingleStep(0.1)    # 设置步长
        self.accu_min_height_spin_box.setValue(0.5)        # 设置默认值
        self.accu_min_height_spin_box.setStyleSheet("color: rgba(255,255,255,1);")
        widget_action.setDefaultWidget(self.accu_min_height_spin_box)
        self.ui.menu_accu_pc.addAction(widget_action)

        widget_action = QWidgetAction(self)
        # 创建 QDoubleSpinBox 并将其添加到 QMenu 中
        _temp = QLabel(self)
        _temp.setText("最大高度(m)")
        widget_action.setDefaultWidget(_temp)
        self.ui.menu_accu_pc.addAction(widget_action)

        widget_action = QWidgetAction(self)
        # 创建 QDoubleSpinBox 并将其添加到 QMenu 中
        self.accu_max_height_spin_box = QDoubleSpinBox(self)
        self.accu_max_height_spin_box.setRange(0.0, 15.0)  # 设置范围
        self.accu_max_height_spin_box.setSingleStep(0.1)    # 设置步长
        self.accu_max_height_spin_box.setValue(5)        # 设置默认值
        self.accu_max_height_spin_box.setStyleSheet("color: rgba(255,255,255,1);")
        widget_action.setDefaultWidget(self.accu_max_height_spin_box)
        self.ui.menu_accu_pc.addAction(widget_action)

        widget_action = QWidgetAction(self)
        # 创建 QDoubleSpinBox 并将其添加到 QMenu 中
        _temp = QLabel(self)
        _temp.setText("最大累积点个数")
        widget_action.setDefaultWidget(_temp)
        self.ui.menu_accu_pc.addAction(widget_action)

        widget_action = QWidgetAction(self)
        self.MAX_ACCU_PC_NUM_spin_box = QSpinBox(self)
        self.MAX_ACCU_PC_NUM_spin_box.setRange(20000, MAX_ACCU_PC_NUM)  # 设置范围
        self.MAX_ACCU_PC_NUM_spin_box.setSingleStep(1000)    # 设置步长
        self.MAX_ACCU_PC_NUM_spin_box.setValue(50000)        # 设置默认值
        self.MAX_ACCU_PC_NUM_spin_box.setStyleSheet("color: rgba(255,255,255,1);")
        widget_action.setDefaultWidget(self.MAX_ACCU_PC_NUM_spin_box)
        self.ui.menu_accu_pc.addAction(widget_action)

        widget_action = QWidgetAction(self)
        # 创建 QDoubleSpinBox 并将其添加到 QMenu 中
        _temp = QLabel(self)
        _temp.setText("累积点绘制大小")
        widget_action.setDefaultWidget(_temp)
        self.ui.menu_accu_pc.addAction(widget_action)

        widget_action = QWidgetAction(self)
        self.MAX_ACCU_PC_SIZE_spin_box = QDoubleSpinBox(self)
        self.MAX_ACCU_PC_SIZE_spin_box.setRange(0.1, 10.0)  # 设置范围
        self.MAX_ACCU_PC_SIZE_spin_box.setSingleStep(0.1)    # 设置步长
        self.MAX_ACCU_PC_SIZE_spin_box.setValue(2.0)        # 设置默认值
        self.MAX_ACCU_PC_SIZE_spin_box.setStyleSheet("color: rgba(255,255,255,1);")
        widget_action.setDefaultWidget(self.MAX_ACCU_PC_SIZE_spin_box)
        self.ui.menu_accu_pc.addAction(widget_action)

        self.accu_min_height_spin_box.valueChanged.connect(self.update_accu_config)
        self.accu_max_height_spin_box.valueChanged.connect(self.update_accu_config)
        self.MAX_ACCU_PC_NUM_spin_box.valueChanged.connect(self.update_accu_config)
        self.MAX_ACCU_PC_SIZE_spin_box.valueChanged.connect(self.update_accu_config)

        self.trigger_update_accu_config.connect(self.ui.openGLWidget.update_accu_config)


    def update_accu_config(self):
        _ = {
            "MIN_H":self.accu_min_height_spin_box.value(),
            "MAX_H": self.accu_max_height_spin_box.value(),
            "MAX_NUM": self.MAX_ACCU_PC_NUM_spin_box.value(),
            "SIZE": self.MAX_ACCU_PC_SIZE_spin_box.value(),
        }
        self.trigger_update_accu_config.emit(_)


    def update_opengl_checkbox_pc(self):
        if self.ui.action_pc.isChecked():
            self.ui.openGLWidget.show_checkbox.pc = 1
        else:
            self.ui.openGLWidget.show_checkbox.pc = 0

    def update_opengl_checkbox_fs(self):
        if self.ui.action_fs.isChecked():
            self.ui.openGLWidget.show_checkbox.fs = 1
        else:
            self.ui.openGLWidget.show_checkbox.fs = 0

    def update_opengl_checkbox_fc_lines(self):
        if self.ui.action_fcline.isChecked():
            self.ui.openGLWidget.show_checkbox.fc_lines = 1
        else:
            self.ui.openGLWidget.show_checkbox.fc_lines = 0

    def update_opengl_checkbox_tracker(self):
        if self.ui.action_tracker.isChecked():
            self.ui.openGLWidget.show_checkbox.tracker = 1
        else:
            self.ui.openGLWidget.show_checkbox.tracker = 0

    def update_opengl_checkbox_accu_pc(self):
        if self.ui.action_pcaccu.isChecked():
            self.ui.openGLWidget.show_checkbox.accu_pc = 1
        else:
            self.ui.openGLWidget.show_checkbox.accu_pc = 0

    def update_opengl_checkbox_adas(self):
        if self.ui.action_adas.isChecked():
            self.ui.openGLWidget.show_checkbox.adas = 1
        else:
            self.ui.openGLWidget.show_checkbox.adas = 0

    def update_opengl_checkbox_gr(self):
        if self.ui.action_gr.isChecked():
            self.ui.openGLWidget.show_checkbox.gr = 1
        else:
            self.ui.openGLWidget.show_checkbox.gr = 0


    def update_image(self, img_list):
        # 更新 QLabel 显示图像
        img1,img2,img3,img4 = img_list
        if img1 != None:
            pixmap = QPixmap.fromImage(img1)
            self.ui.camera_1.setPixmap(pixmap)
        if img2 != None:
            pixmap = QPixmap.fromImage(img2)
            self.ui.camera_2.setPixmap(pixmap)
        if img3 != None:
            pixmap = QPixmap.fromImage(img3)
            self.ui.camera_3.setPixmap(pixmap)
        if img4 != None:
            pixmap = QPixmap.fromImage(img4)
            self.ui.camera_4.setPixmap(pixmap)
    def update_opengl(self):
        # print("update")
        self.ui.openGLWidget.ifStarted = 1
        self.ui.openGLWidget.update()

    def update_status_bar(self,NetWork_Info):
        self.ui.statusbar.showMessage(f"客户端：{NetWork_Info['IP']} 端口:{NetWork_Info['Port']}  接收速率：{NetWork_Info['receive_rate_MBps']:.2f} Mbps ",1000)

    def camera_label_init(self):
        image2 = QtGui.QPixmap((qtawesome.icon('fa.video-camera', color='#dedede')).pixmap(300, 200))
        self.ui.camera_1.setPixmap(image2)
        self.ui.camera_1.setAlignment(QtCore.Qt.AlignCenter)

        self.ui.camera_2.setPixmap(image2)
        self.ui.camera_2.setAlignment(QtCore.Qt.AlignCenter)
        self.ui.camera_3.setPixmap(image2)
        self.ui.camera_3.setAlignment(QtCore.Qt.AlignCenter)
        self.ui.camera_4.setPixmap(image2)
        self.ui.camera_4.setAlignment(QtCore.Qt.AlignCenter)

    def start_task(self):
        # 创建并启动线程

        self.thread = Worker(data_queue)
        self.thread.trigger_update_opengl.connect(self.update_opengl)
        self.thread.trigger_update_freespace.connect(self.ui.openGLWidget.update_freespace_data)
        self.thread.trigger_update_fc_lines.connect(self.ui.openGLWidget.update_fc_lines_data)
        self.thread.trigger_update_mount.connect(self.ui.openGLWidget.update_mount_info)
        self.thread.trigger_update_pc.connect(self.ui.openGLWidget.update_pc_data)
        self.thread.trigger_update_tracker_f.connect(self.ui.openGLWidget.update_tracker_data_f)
        self.thread.trigger_update_tracker_r.connect(self.ui.openGLWidget.update_tracker_data_r)
        self.thread.trigger_update_guardrail.connect(self.ui.openGLWidget.update_guardrail_data)
        self.thread.trigger_update_camera.connect(self.update_image)
        self.thread.trigger_update_vehicleinfo.connect(self.ui.openGLWidget.update_vehicle_info_dict)
        self.thread.trigger_update_NetWork_Info.connect(self.update_status_bar)
        self.thread.trigger_update_ADAS_Info.connect(self.ui.openGLWidget.update_ADAS_Info)
        self.thread.start()









if __name__ == '__main__':
    #2025-02-26

    multiprocessing.freeze_support()
    QApplication.setAttribute(QtCore.Qt.AA_UseDesktopOpenGL)
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_medical.xml')
    # 创建队列，用于进程间通信
    data_queue = multiprocessing.Queue()

    # 创建并启动子进程
    process = multiprocessing.Process(target=server_receive_data, args=(data_queue,))
    process.start()


    mainwin = mainui()

    mainwin.showMaximized()

    sys.exit(app.exec_())
