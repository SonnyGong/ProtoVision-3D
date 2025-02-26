# -*- encoding: utf-8 -*-
'''
@File    :   GEN_VER_FUNC.py    
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
2025/2/10 16:09   NotToday      1.0         None
'''
import numpy as np


def generate_fan_vertices(radius, segments, start_angle, end_angle,x_offset = 0,y_offset = 0):
    vertices = [(x_offset ,y_offset, 0.06)]  # 扇形的中心
    angle_step = (end_angle - start_angle) / segments

    for i in range(segments + 1):
        angle = np.radians(start_angle + i * angle_step)
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        vertices.append((x+x_offset, y+y_offset, 0.06))

    return np.array(vertices, dtype=np.float32).flatten()


def generate_fan_indices(offset, segments):
    indices = []
    for i in range(segments):
        indices.append(offset)
        indices.append(offset + i + 1)
        indices.append(offset + i + 2)
    return np.array(indices, dtype=np.uint32).flatten()

def generate_cube_vertices(x, y, z, width, height, depth):
    # 计算立方体8个顶点的坐标
    hw = width / 2.0  # half width
    hh = height / 2.0 # half height
    hd = depth / 2.0  # half depth
    Z_OFFSET = 0.05

    # 顶点顺序为前后左右上下
    vertices = np.array([
        x - hw, y - hh, z - hd + Z_OFFSET,  # 0: 左下前
        x + hw, y - hh, z - hd + Z_OFFSET,  # 1: 右下前
        x + hw, y + hh, z - hd + Z_OFFSET,  # 2: 右上前
        x - hw, y + hh, z - hd + Z_OFFSET,  # 3: 左上前
        x - hw, y - hh, z + hd + Z_OFFSET,  # 4: 左下后
        x + hw, y - hh, z + hd + Z_OFFSET,  # 5: 右下后
        x + hw, y + hh, z + hd + Z_OFFSET,  # 6: 右上后
        x - hw, y + hh, z + hd + Z_OFFSET,  # 7: 左上后
    ], dtype=np.float32)

    return vertices

def generate_cube_indices(offset):
    # offset 是索引的起始值
    indices = np.array([
        # 前面
        offset + 0, offset + 1, offset + 2,
        offset + 2, offset + 3, offset + 0,

        # 后面
        offset + 4, offset + 5, offset + 6,
        offset + 6, offset + 7, offset + 4,

        # 左面
        offset + 0, offset + 3, offset + 7,
        offset + 7, offset + 4, offset + 0,

        # 右面
        offset + 1, offset + 2, offset + 6,
        offset + 6, offset + 5, offset + 1,

        # 上面
        offset + 3, offset + 2, offset + 6,
        offset + 6, offset + 7, offset + 3,

        # 下面
        offset + 0, offset + 1, offset + 5,
        offset + 5, offset + 4, offset + 0
    ], dtype=np.uint32)

    return indices