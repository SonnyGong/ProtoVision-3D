import numpy as np
import matplotlib.pyplot as plt

# 初始化车辆的位置和方向
car_position = np.array([0.0, 0.0])  # 车辆起始位置 (始终固定为原点)
car_angle = 0  # 初始角度 (0表示正东方向)

# 参数设置
num_steps = 10  # 模拟的步数
move_distance = 1  # 每步前进的距离
yawrate = np.pi / 18  # 每步左转角度（左转 10 度）

# 存储每次检测到的点在车辆坐标系中的位置
detected_points_local = [np.array([1.0, 0.0])]  # 初始时刻检测到的点位置 (1, 0)

# 模拟车辆前进并小幅度左转
for step in range(1, num_steps):
    # 将之前检测到的所有点转换到新的车辆坐标系中
    new_detected_points_local = []
    rotation_matrix = np.array([
        [np.cos(-yawrate), -np.sin(-yawrate)],
        [np.sin(-yawrate), np.cos(-yawrate)]
    ])

    for point in detected_points_local:
        # 先将点向后平移 move_distance, 然后旋转 -yawrate 角度
        point = point - np.array([move_distance, 0.0])  # 平移
        rotated_point = rotation_matrix @ point  # 旋转
        new_detected_points_local.append(rotated_point)

    # 添加当前帧检测到的点
    new_detected_points_local.append(np.array([1.0, 0.0]))  # 当前时刻新检测的点

    # 更新检测点列表
    detected_points_local = new_detected_points_local

# 绘图
fig, ax = plt.subplots()
ax.set_aspect('equal', 'box')
ax.set_xlim(-10, 10)
ax.set_ylim(-10, 10)

# 绘制所有检测到的点在新的自车坐标系中的位置
detected_points_local = np.array(detected_points_local)
ax.plot(detected_points_local[:, 0], detected_points_local[:, 1], 'rx')  # 检测到的点（红色叉）
ax.plot(detected_points_local[:, 0], detected_points_local[:, 1], 'r--')  # 连接检测到的点（红色虚线）

# 绘制车辆的位置（始终固定在原点）
ax.plot(0, 0, 'bo')  # 车辆位置（蓝色圆点）

# 显示图形
plt.title("Points in Current Car Coordinate System")
plt.xlabel("X Position (relative to car)")
plt.ylabel("Y Position (relative to car)")
plt.grid(True)
plt.show()
