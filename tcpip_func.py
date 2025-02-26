# -*- encoding: utf-8 -*-
'''
@File    :   tcpip_func.py    
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
2025/2/10 10:54   NotToday      1.0         None
'''
import multiprocessing
import socket
import threading
import time

import message_pb2


def handle_client(client_socket, addr, data_queue):
    NetWork_Info = {
        'IP': addr[0],
        'Port': addr[1],
        'receive_rate_MBps': 0,
    }
    try:
        print(f"Accepted connection from {addr}")
        with client_socket:
            total_data_received = 0  # 统计接收到的数据字节数
            start_time = time.time() # 记录开始时间
            while True:
                msg_length = client_socket.recv(4)
                if not msg_length:
                    print(f"Connection from {addr} closed")
                    break
                if msg_length == b'9999':
                    # 发送回应
                    response = "收到你的信息: " + str(msg_length)
                    print(f"发送回应: {response}")
                    client_socket.sendall("1".encode('utf-8'))
                    continue

                msg_length = int.from_bytes(msg_length, 'big')
                total_data_received += msg_length

                # 根据长度读取实际的数据
                data = bytearray()
                while len(data) < msg_length:
                    packet = client_socket.recv(msg_length - len(data))
                    if not packet:
                        print(f"Connection from {addr} closed during data reception")
                        break
                    data.extend(packet)


                # 解析 Protobuf 数据
                frame = message_pb2.Frame()
                frame.ParseFromString(bytes(data))

                # 发送解析后的信息到队列
                data_queue.put([frame,NetWork_Info])
                # 每隔1秒打印一次速率
                elapsed_time = time.time() - start_time
                if elapsed_time > 1:
                    NetWork_Info['receive_rate_MBps'] = (total_data_received / elapsed_time) / (1024 * 1024) * 8

                    # 重置统计
                    total_data_received = 0
                    start_time = time.time()

    except (ConnectionError, socket.error) as e:
        print(f"Connection error from {addr}: {e}")

def server_receive_data(data_queue, host='0.0.0.0', port=12345):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)  # 设置为 5 个待处理连接的队列大小
        print(f"Server listening on {host}:{port}")

        while True:
            try:
                client_socket, addr = server_socket.accept()
                # 每个客户端连接创建一个线程
                client_thread = threading.Thread(target=handle_client, args=(client_socket, addr, data_queue))
                client_thread.daemon = True  # 设置为守护线程，主线程退出时结束
                client_thread.start()
            except (ConnectionError, socket.error) as e:
                print(f"Connection error: {e}. Waiting for new connection...")



if __name__ == '__main__':
    # 创建队列，用于进程间通信
    data_queue = multiprocessing.Queue()

    # 创建并启动子进程
    process = multiprocessing.Process(target=server_receive_data, args=(data_queue,))
    process.start()

    # 等待子进程结束
    process.join()