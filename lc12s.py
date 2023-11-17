#!/usr/bin/python3
import time
import serial
import threading
from copy import deepcopy


class Lc12s(object):

    def __init__(self, uart_baud, machine_idh, machine_idl, net_idh, net_idl, rf_power,
                 rf_channel, data_length):

        self.net_idl = net_idl
        self.start = None
        self.data_length = data_length
        self.uart1 = serial.Serial('/dev/ttyUSB1', uart_baud, timeout=1)  # control box
        self.uart2 = serial.Serial('/dev/ttyUSB0', uart_baud, timeout=1)  # gun
        # AA 5A 00 00 FF FF 00 1E 00 04 00 14 00 01 00 12 00 4B
        self.init_order = [0xaa, 0x5a, 0x00, 0x00, 0x00, 0x0c, 0x00, 0x1E, 0x00, 0x04, 0x00, 0x14, 0x00, 0x01, 0x00,
                           0x12, 0x00, 0x59]
        self.order = bytearray(self.init_order)
        self.machineid_high = machine_idh  # 1byte
        self.machineid_low = machine_idl  # 1byte
        self.init_order[4] = net_idh  # 1byte
        self.init_order[5] = net_idl  # 1byte
        self.init_order[7] = rf_power  # 0:6dbm 1:3dbm 2:1dbm 3:-2dbm 4:-8dbm
        self.init_order[11] = rf_channel  # 0~127
        self.checksum = self.check
        self.init_order[17] = self.checksum
        self.hit_check_message = bytearray([0x16, 0x01])

        # self.core_gun = [0x0c, 0x10, 0x10, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x1E, 0x67, 0x68]
        self.core_web = [0x16, 0x10, 0x10, 0x00, 0x0c, 0x00, 0x00, 0x01, 0x00, 0x1E, 0x07, 0x08, 0x69, 0x70, 0x71]
        self.datat_gun = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.datat_web = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.core_web_lose = [0x16, 0x10, 0x10, 0x00, 0x0c, 0x00, 0x00, 0x01, 0x00, 0x1E, 0x07, 0x08, 0x69, 0x70, 0x71]
        self.data_temp = None
        # state machine
        self.count = 0
        # function flag
        self.receive_flag_g = False
        self.receive_flag_w = False
        self.target_enroll = False
        self.core_gun_flag = False
        self.core_web_flag = False
        self.receive_enroll_flag = False
        self.receive_data_flag = False
        self.receive_quit_flag = False
        self.confirm_set_flag = False
        self.send_interval = False
        self.open_flag = False
        # LOCK
        self.target_enroll_lock = threading.Lock()
        self.receive_enroll_lock = threading.Lock()
        self.receive_quit_lock = threading.Lock()
        self.confirm_set_lock = threading.Lock()
        self.gun_data_lock = threading.Lock()
        self.web_data_lock = threading.Lock()
        self.receive_gun_lock = threading.Lock()
        self.receive_web_lock = threading.Lock()
        self.receive_data_lock = threading.Lock()
        # Send state
        self.send_flag = False

    def config(self):
        # 设置
        self.uart1.write(bytearray(self.order))
        time.sleep(0.5)
        self.uart1.flushInput()

    def check(self):
        # checksum count
        temp = 0
        for i in range(17):
            temp = self.init_order[i] + temp
        temp = (temp & 0xff)
        return temp

    # 发送消息函数
    def send_1(self, data_buffer):
        print("send to server:", data_buffer)
        temp = bytearray(data_buffer)
        self.uart1.write(temp)
        if not self.send_interval:
            time.sleep(0.01)
        else:
            time.sleep(0.100)

    def send_2(self, data_buffer):
        print("send to gun:", data_buffer)
        temp = bytearray(data_buffer)
        self.uart2.write(temp)
        if not self.send_interval:
            time.sleep(0.01)
        else:
            time.sleep(0.100)

    def check_1(self, data_buffer_send, data_buffer_back):
        for attempt in range(5):
            # 发送数据
            self.send_interval = False
            self.send_1(data_buffer_send)
            self.send_interval = True
            # 等待确认消息
            start_time = time.time()
            while True:
                time.sleep(0.01)
                if self.uart1.inWaiting() > 0:
                    data_received = self.uart1.read(self.uart1.inWaiting())
                    if data_buffer_back in data_received:
                        print('确认收到')
                        return 
                elif time.time() - start_time > 0.3:  # 超时时间为0.5秒
                    print('超时重发')
                    break

    # 接收消息函数
    def recv(self):
        self.start = time.time()
        if self.uart2.inWaiting():
            self.gun_data_lock.acquire()
            uart_temp = self.uart2.read(self.uart2.inWaiting())
            if len(uart_temp) == len(self.datat_gun):
                for i in range(0, len(self.datat_gun)):
                    self.datat_gun[i] = int(uart_temp[i])
                print("gun message:", self.datat_gun)
                self.gun_data_lock.release()
                self.receive_gun_lock.acquire()
                self.receive_flag_g = True
                self.receive_gun_lock.release()
            else:
                print('unexpect: ',list(uart_temp))
                print("无效枪信息")
                self.gun_data_lock.release()
        elif self.uart1.inWaiting():
            self.web_data_lock.acquire()
            uart_temp = self.uart1.read(self.uart1.inWaiting())
            if len(uart_temp) == len(self.datat_web):
                for i in range(0, len(self.datat_web)):
                    self.datat_web[i] = int(uart_temp[i])
                print("web message:", self.datat_web)
                self.web_data_lock.release()
                self.receive_web_lock.acquire()
                self.receive_flag_w = True
                self.receive_web_lock.release()
            else:
                print('unexpect: ',list(uart_temp))
                print("无效服务器信息")
                self.web_data_lock.release()
                self.receive_web_lock.acquire()
                self.receive_flag_w = True
                self.receive_web_lock.release()

    def get_message(self):
        if self.receive_flag_g:
            self.receive_gun_lock.acquire()
            self.receive_flag_g = False
            self.receive_gun_lock.release()
            if self.datat_gun[0] == 12 and (self.datat_gun[2] == 16):
                if self.datat_gun[1] == 0x00:
                    self.answer_gun([0x10])
                    self.receive_enroll_lock.acquire()
                    self.receive_enroll_flag = True
                    self.receive_enroll_lock.release()
                    self.receive_quit_lock.acquire()
                    self.receive_quit_flag = False
                    self.receive_quit_lock.release()
                    # self.core_gun[3] = self.datat_gun[3]
                    # self.core_gun[4] = self.datat_gun[4]
                elif self.datat_gun[1] == 0x01:
                    self.receive_enroll_lock.acquire()
                    self.receive_enroll_flag = False
                    self.receive_enroll_lock.release()
                    self.receive_quit_lock.acquire()
                    self.receive_quit_flag = True
                    self.receive_quit_lock.release()
                    # self.core_gun[3] = 0xff
                    # self.core_gun[4] = 0xff
                elif self.datat_gun[1] == 0x10:
                    self.answer_gun([0x01])
                    print("shoot")
                    self.receive_data_lock.acquire()
                    self.receive_data_flag = True
                    self.receive_data_lock.release()
                elif self.datat_gun[1] == 0x11:
                    self.confirm_set_flag = True
        elif self.receive_flag_w:
            self.receive_web_lock.acquire()
            self.receive_flag_w = False
            self.receive_web_lock.release()
            if self.datat_web[0] == 0x16 and self.datat_web[2] == 0x01:
                if self.datat_web[1] == 0x00:
                    if self.datat_web[8] == 0x99:
                        print("确认注册")
                        self.target_enroll_lock.acquire()
                        self.target_enroll = True
                        self.target_enroll_lock.release()
                elif self.datat_web[1] == 0x01:
                    if self.datat_web[8] == 0x99:
                        print("quit confirm")
                elif self.datat_web[1] == 0x10:
                    if self.datat_web[8] == 0x99:
                        print("data confirm")
                elif self.datat_web[1] == 0x11:
                    print("收到设置")
                    self.core_gun_flag = True
        else:
            self.gun_data_lock.acquire()
            self.datat_web = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            self.gun_data_lock.release()
            self.web_data_lock.acquire()
            self.datat_gun = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            self.web_data_lock.release()

    # enroll
    def enroll(self):
        self.core_web[0] = 0x16
        self.core_web[1] = 0x00
        self.core_web[2] = 0x10
        self.core_web[8] = 0x00
        time.sleep(1)
        self.send_interval = True
        self.send_1(self.core_web)
        self.send_interval = False
        # quit

    def answer_gun(self, answer):
        self.send_interval = True
        self.send_2(answer)
        self.send_interval = False

    def quit(self):
        self.core_web[0] = 0x16
        self.core_web[1] = 0x01
        self.core_web[2] = 0x10
        self.core_web[8] = 0x00
        self.send_interval = True
        self.send_1(self.core_web)
        self.send_interval = False
        # send axis

    def hit_curve(self, flag, aim_ring, shoot_ring, shake, shake_v, shoot_shake, shoot_shake_v, axis_x=0, axis_y=0):
        self.core_web[0] = 0x16
        self.core_web[1] = 0x10
        self.core_web[2] = 0x10
        self.core_web[3] = flag  # 击中靶子
        self.core_web[4] = aim_ring
        self.core_web[5] = shoot_ring
        self.core_web[6] = shake
        self.core_web[7] = shake_v
        self.core_web[8] = shoot_shake
        self.core_web[9] = shoot_shake_v
        axis_xh = int(axis_x / 480.0 * 100)
        axis_xl = int((axis_x / 480.0 * 100 - axis_xh)) * 100
        axis_yh = int(axis_y / 480.0 * 100)
        axis_yl = int((axis_y / 480.0 * 100) - axis_yh) * 100
        self.core_web[10] = axis_xh  # 取出高位
        self.core_web[11] = axis_xl  # 取出低位
        self.core_web[12] = axis_yh  # 取出高位
        self.core_web[13] = axis_yl  # 取出低位
        self.core_web_lose = deepcopy(self.core_web)
        self.core_web_lose[3] = 0x01
        self.core_web_lose[4] = shoot_ring
        print("坐标为", axis_x, axis_y)
        self.send_interval = False
        self.send_1(self.core_web)
        self.send_interval = True

    def hit(self, flag, aim_ring, shoot_ring, shake, shake_v, shoot_shake, shoot_shake_v, axis_x=0, axis_y=0):
        self.core_web[0] = 0x16
        self.core_web[1] = 0x10
        self.core_web[2] = 0x10
        self.core_web[3] = flag  # 击中靶子
        self.core_web[4] = aim_ring
        self.core_web[5] = shoot_ring
        self.core_web[6] = shake
        self.core_web[7] = shake_v
        self.core_web[8] = shoot_shake
        self.core_web[9] = shoot_shake_v
        axis_xh = int(axis_x / 480.0 * 100)
        axis_xl = int((axis_x / 480.0 * 100 - axis_xh)) * 100
        axis_yh = int(axis_y / 480.0 * 100)
        axis_yl = int((axis_y / 480.0 * 100) - axis_yh) * 100
        self.core_web[10] = axis_xh  # 取出高位
        self.core_web[11] = axis_xl  # 取出低位
        self.core_web[12] = axis_yh  # 取出高位
        self.core_web[13] = axis_yl  # 取出低位
        self.check_1(self.core_web, self.hit_check_message)
        print("坐标为", axis_x, axis_y)
        self.core_web_lose = deepcopy(self.core_web)
        self.core_web_lose[3] = 0x01
        self.core_web_lose[4] = shoot_ring

    def hit_lose(self):
        print("坐标(lose)")
        self.check_1(self.core_web_lose, self.hit_check_message)
