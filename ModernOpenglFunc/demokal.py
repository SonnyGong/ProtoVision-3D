import numpy as np
from filterpy.kalman import KalmanFilter


def initialize_kalman_filter():
    # 创建一个卡尔曼滤波器对象
    kf = KalmanFilter(dim_x=4, dim_z=2)

    # 状态转移矩阵 F
    dt = 1.0  # 时间步长
    kf.F = np.array([[1, 0, dt, 0],
                     [0, 1, 0, dt],
                     [0, 0, 1, 0],
                     [0, 0, 0, 1]])

    # 观测矩阵 H
    kf.H = np.array([[1, 0, 0, 0],
                     [0, 1, 0, 0]])

    # 测量噪声协方差矩阵 R
    kf.R = np.array([[0.1, 0],
                     [0, 0.1]])

    # 过程噪声协方差矩阵 Q
    kf.Q = np.array([[0.1, 0, 0, 0],
                     [0, 0.1, 0, 0],
                     [0, 0, 0.1, 0],
                     [0, 0, 0, 0.1]])

    # 初始状态估计
    kf.x = np.array([0, 0, 0, 0])

    # 初始协方差矩阵
    kf.P = np.eye(4) * 1.0

    return kf


def update_kalman_filter(kf, velocity, yaw_rate):
    # 预测步骤
    kf.predict()

    # 计算控制输入
    measurement = np.array([velocity, yaw_rate])

    # 更新步骤
    kf.update(measurement)

    return kf.x


# 示例使用
if __name__ == "__main__":
    kf = initialize_kalman_filter()

    # 模拟一些车速和yaw rate数据
    velocities = [1, 1.2, 1.1, 1.3, 1.0]
    yaw_rates = [0.1, 0.05, 0.08, 0.07, 0.06]

    for velocity, yaw_rate in zip(velocities, yaw_rates):
        state_estimate = update_kalman_filter(kf, velocity, yaw_rate)
        print(f"车速: {velocity}, 航向角速度: {yaw_rate}")
        print(f"状态估计: {state_estimate}")
