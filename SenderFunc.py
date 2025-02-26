# -*- encoding: utf-8 -*-
'''
@File    :   SenderFunc.py
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
2025/2/10 11:07   NotToday      1.0         None
'''
import socket
import time
import message_pb2  # 你的 Protobuf 生成的模块

def send_data_to_server(host='localhost', port=12345):
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                print(f"Attempting to connect to {host}:{port}")
                s.connect((host, port))
                print(f"Connected to {host}:{port}")

                while True:
                    # 生成一个模拟的 Frame 数据
                    frame = generate_dummy_frame()

                    # 将 Frame 编码为字节串
                    data = frame.SerializeToString()

                    # 发送消息长度（4 字节大端序）
                    msg_length = len(data)
                    s.sendall(msg_length.to_bytes(4, 'big'))

                    # 发送实际的 Protobuf 数据
                    s.sendall(data)

                    print(f"Sent frame with {len(frame.pc12)} points, "
                          f"{len(frame.tk1)} trackers, {len(frame.fs)} fence points")

                    # 每隔 50ms 发送一次
                    time.sleep(0.05)

        except (ConnectionError, socket.error) as e:
            print(f"Connection error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)

def generate_dummy_frame():
    """生成一个模拟的 Frame 数据"""
    frame = message_pb2.Frame()
    for _ in range(1000):
        point = frame.pc12.add()
        point.Range_m = 1.0
        point.Elevation_deg = 2.0
        point.Azimuth_deg = 3.0
    return frame


class DataSender:
    def __init__(self, host='localhost', port=12345, reconnect_interval=5):
        self.host = host
        self.port = port
        self.connection = None
        self.is_running = False
        self.reconnect_interval = reconnect_interval  # 重新连接的时间间隔，单位为秒


    def connect(self):
        """连接到服务器，重试直到成功"""
        while self.connection is None:
            try:
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.connect((self.host, self.port))
                print(f"Connected to {self.host}:{self.port}")
            except (ConnectionError, socket.error) as e:
                print(f"Connection failed: {e}. Retrying in {self.reconnect_interval} seconds...")
                time.sleep(self.reconnect_interval)

    def send_frame(self, frame):
        """发送单帧数据到服务器"""
        if self.connection is None:
            print("No connection. Please connect first.")
            return

        try:
            # 将 Frame 编码为字节串
            data = frame.SerializeToString()

            # 发送消息长度（4 字节大端序）
            msg_length = len(data)
            self.connection.sendall(msg_length.to_bytes(4, 'big'))

            # 发送实际的 Protobuf 数据
            self.connection.sendall(data)

            print(f"Sent frame with {len(frame.pc12)} points, "
                  f"{len(frame.tk1)} trackers, {len(frame.fs)} fence points")

        except (ConnectionError, socket.error) as e:
            print(f"Connection error: {e}. Reconnecting...")
            self.connection.close()
            self.connection = None
            self.connect()
            # Retry sending the frame after reconnecting
            self.send_frame(frame)

    def start_sending(self, frame_proto):
        """开始逐帧发送数据"""
        self.is_running = True
        self.connect()
        # 发送单帧数据
        self.send_frame(frame_proto)


    def stop(self):
        """停止发送数据"""
        self.is_running = False
        if self.connection:
            self.connection.close()

# 示例用法
if __name__ == "__main__":
    DataSender_FUNC = DataSender()
    try:
        DataSender_FUNC.start_sending(generate_dummy_frame())  # 发送 10 帧数据
    except KeyboardInterrupt:
        DataSender_FUNC.stop()

