# -*- encoding: utf-8 -*-
'''
@File    :   CameraFunc.py    
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
2025/2/10 14:02   NotToday      1.0         None
'''
import math

import glm
from PyQt5.QtCore import Qt



class Camera:
    def __init__(self,):
        self.cameraPos = glm.vec3(1, 20, 35)
        # self.cameraFront = glm.vec3(0.06, -0.54, -0.83)
        self.cameraFront = glm.vec3(-0.009639328345656395, -0.3907311260700226, -0.9204543828964233)
        self.cameraUp = glm.vec3(0, 1, 0)
        self.firstMouse = True
        self.yaw = -90.0
        self.pitch = 0.0

        self.lastX = 200 / 2
        self.lastY = 100 / 2
        self.fov = 79
        self.cameraSpeed = 1
        self.sensitivity = 0.1

    def GetViewMatrix(self):
        view_m = glm.lookAt(self.cameraPos, self.cameraPos + self.cameraFront, self.cameraUp)
        return view_m

    def KeyFunc(self,Key,deltaTime):
        self.cameraSpeed = 5.5 * deltaTime
        if Key == Qt.Key_W:
            self.cameraPos += self.cameraSpeed * self.cameraFront
        elif Key == Qt.Key_S:
            self.cameraPos -= self.cameraSpeed * self.cameraFront
        elif Key == Qt.Key_A:
            self.cameraPos -= glm.normalize(glm.cross(self.cameraFront, self.cameraUp)) * self.cameraSpeed
        elif Key== Qt.Key_D:
            self.cameraPos += glm.normalize(glm.cross(self.cameraFront, self.cameraUp)) * self.cameraSpeed
        # print(self.cameraFront, self.cameraUp,self.cameraPos)

    def MouseFunc(self,X,Y,EventType):
        if EventType == "mousePressEvent":
            if self.firstMouse:
                self.firstMouse = False
            self.lastX = X
            self.lastY = Y
        if EventType == "mouseMoveEvent":
            if not self.firstMouse:
                sensitivity = 0.1
                self.yaw -= (X - self.lastX) * sensitivity
                self.lastX = X
                self.pitch -= (self.lastY - Y) * sensitivity
                self.lastY = Y
                if self.pitch > 89.0:
                    self.pitch = 89.0
                if self.pitch < -89.0:
                    self.pitch = -89.0
                temp_front = glm.vec3(1, 1, 1)
                temp_front.x = math.cos(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch))
                temp_front.y = math.sin(glm.radians(self.pitch))
                temp_front.z = math.sin(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch))
                self.cameraFront = glm.normalize(temp_front)
                # print("temp_front",self.cameraFront.x,self.cameraFront.y,self.cameraFront.z)
        if EventType == "wheelEvent":

            self.fov -= Y * 0.01
            if self.fov > 120:
                self.fov = 120
            if self.fov < 1:
                self.fov = 1
            print("fov",self.fov)
