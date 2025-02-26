# -*- encoding: utf-8 -*-
'''
@File    :   ACCU_FUNC.py    
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
2025/2/10 11:00   NotToday      1.0         None
'''
import numpy as np


class CircularBuffer:
    def __init__(self, max_size, element_size):
        """
        初始化循环缓冲区

        参数:
        - max_size: 大数组能容纳的小数组的最大数量
        - element_size: 每个小数组的大小（例如，3 表示每个小数组有 3 个元素）
        """
        self.buffer = np.zeros((max_size, element_size), dtype=np.float32)
        self.max_size = max_size
        self.element_size = element_size
        self.current_index = 0
        self.is_full = False

    def add(self, new_element):
        """
        将一个新的小数组添加到循环缓冲区

        参数:
        - new_element: 要添加的小数组
        """
        self.buffer[self.current_index] = new_element
        self.current_index += 1

        if self.current_index >= self.max_size:
            self.current_index = 0
            self.is_full = True

    def get_data(self):
        """
        获取缓冲区中的数据，按插入顺序排列
        """
        if self.is_full:
            # 如果缓冲区满了，返回数据时应从current_index开始到末尾再到开头
            return np.concatenate((self.buffer[self.current_index:], self.buffer[:self.current_index]))
        else:
            # 如果缓冲区没满，直接返回当前存储的数据
            return self.buffer[:self.current_index]

    def update_all(self, transform_function):
        """
        对大数组的每个小数组进行运算，并将结果替换回大数组。

        参数:
        - transform_function: 一个接受单个小数组并返回更新后的数组的函数。
        """
        for i in range(self.buffer.shape[0]):
            self.buffer[i] = transform_function(self.buffer[i])


from collections import deque

from sklearn.linear_model import LinearRegression


class NumberList:
    def __init__(self, size):
        self.size = size
        self.numbers = deque(maxlen=size)

    def add_number(self, num):
        self.numbers.append(num)
        return self.check_trend()

    def check_trend(self):
        if len(self.numbers) < 60:
            return 2  # Less than 2 numbers cannot determine trend

        # Prepare data for linear regression
        x = np.arange(len(self.numbers)).reshape(-1, 1)  # Time steps
        y = np.array(self.numbers).reshape(-1, 1)  # Data values

        model = LinearRegression().fit(x, y)
        slope = model.coef_[0][0]

        if slope > 0:
            return 0  # Upward trend
        elif slope < 0:
            return 1  # Downward trend
        else:
            return 2  # No trend or constant