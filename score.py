import numpy as np
import math


class Score(object):

    def __init__(self, width=480, height=480):

        self.width = width
        self.height = height
        self.gap = self.width / 10

        self.aim_x_list = []
        self.aim_y_list = []

        self.shoot_xlist = []
        self.shoot_y_list = []

        self.center_x = self.width / 2
        self.center_y = self.width * 0.4

        self.k = 500 / self.width

        self.r = [0, 0, 0, 0, self.gap * 6, self.gap * 5, self.gap * 4, self.gap*3, self.gap * 2, self.gap, 0]

    # 更新瞄准列表
    def update_aim(self, axis_x, axis_y):
        if len(axis_x) < 31:
            self.aim_x_list.append(axis_x)
            self.aim_y_list.append(axis_y)
        else:
            self.aim_x_list = []
            self.aim_y_list = []

    # 更新射击列表
    def update_shoot(self, axis_x, axis_y):
        if len(axis_x) < 31:
            self.aim_x_list.append(axis_x)
            self.aim_y_list.append(axis_y)
        else:
            self.aim_x_list = []
            self.aim_y_list = []

    # 根据坐标算出环数
    def ring(self, xs, ys):
        r = math.sqrt(((xs - self.center_x) ** 2) + ((ys - self.center_y) ** 2))
        # print(r)
        if r >= 0:
            if r <= self.r[9]:
                ri = 10
            elif r <= self.r[8]:
                ri = 9
            elif r <= self.r[7]:
                ri = 8
            elif r <= self.r[6]:
                ri = 7
            elif r <= self.r[5]:
                ri = 6
            elif r <= self.r[4]:
                ri = 5
            else:
                return 0
        else:
            return 0
        # print(ri)
        rd = ((r - self.r[ri]) / self.gap)
        return int(10 * (ri + (1 - rd)))

    # 计算瞄准环值
    def aim_ring(self, aim_x_list, aim_y_list):
        aim_x, aim_y = self.aim_axis(aim_x_list, aim_y_list)
        ring = self.ring(aim_x, aim_y)
        return ring

    # 计算击中环值
    def shoot_ring(self, shoot_x, shoot_y):
        ring = self.ring(shoot_x, shoot_y)
        return ring

    # 计算瞄准平均坐标
    def aim_axis(self, aim_x_list, aim_y_list):
        if len(aim_x_list) > 0 and len(aim_y_list) > 0:
            return np.mean(aim_x_list), np.mean(aim_y_list)
        else:
            return None, None

    # 计算持枪晃动
    def shake(self, aim_x_list, aim_y_list):
        aim_x, aim_y = self.aim_axis(aim_x_list, aim_y_list)
        shake = int(np.mean(np.sqrt(((np.array(aim_x_list) - np.array(aim_x)) ** 2) + ((np.array(aim_y_list) - np.array(aim_y)) ** 2))) * self.k)
        if shake < 255:
            return shake
        else:
            return 255

    # 计算晃动速率
    def shake_v(self, aim_x_list, aim_y_list):
        shake_v = int(np.sum(np.sqrt(((np.array(aim_x_list) - np.array(self.center_x)) ** 2) + (
                (np.array(aim_y_list) - np.array(self.center_y)) ** 2))) * self.k)
        if shake_v < 255:
            return shake_v
        else:
            return 255

    # 计算击发晃动量
    def shoot_shake(self, aim_x_list, aim_y_list, shoot_x, shoot_y):
        aim_x_list = np.array(aim_x_list)
        aim_y_list = np.array(aim_y_list)
        shoot_x = np.array(shoot_x)
        shoot_y = np.array(shoot_y)
        shoot_shake = int(np.max(np.sqrt((((aim_x_list - shoot_x) ** 2) + ((aim_y_list - shoot_y) ** 2)))) * self.k)
        if shoot_shake < 255:
            return shoot_shake
        else:
            return 255

    # 计算击发速率
    def shoot_shake_v(self, aim_x_list, aim_y_list, shoot_x, shoot_y):
        aim_x_list = np.array(aim_x_list)
        aim_y_list = np.array(aim_y_list)
        shoot_x = np.array(shoot_x)
        shoot_y = np.array(shoot_y)
        shoot_shake_v = int(np.sum(np.sqrt(((aim_x_list - shoot_x) ** 2) + ((aim_y_list - shoot_y) ** 2))) * self.k)
        if shoot_shake_v < 255:
            return shoot_shake_v
        else:
            return 255

    def update_para(self, correct_w, correct_h):
        self.width = correct_w
        self.height = correct_h
        self.gap = self.width / 10
