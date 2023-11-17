#!/usr/bin/python3
from lc12s import Lc12s
from camera import Detector
import cv2
from enum import Enum
from camera import WebcamStream
import time


# 枚举处理端状态
class Status(Enum):
    IDLE = 0  # 空闲态
    ENROLL_WEB = 1  # 注册网关
    GUN_ENROLL = 2  # 枪抢占
    QUIT = 4  # 退出
    CONFIRM_QUIT = 5  # 确认退出态


# 枚举事件
class Event(Enum):
    NULL = 0  # 无事件
    OPEN_DETECT = 1  # 注册事件
    QUIT = 3  # 关闭摄像头
    SEND_CURVE = 4  # 发送轨迹信息
    SEND_POINT = 5  # 发送击中坐标信息


class Core(object):
    wireless: Lc12s
    detect: Detector
    status: Status
    event: Event
    webcam_stream: WebcamStream

    target_start: float
    target_end: float

    def __init__(self, wireless: Lc12s, detect: Detector):
        self.wireless = wireless
        self.detect = detect
        self.status = Status.IDLE
        self.event = Event.NULL
        self.webcam_stream = WebcamStream(stream_id=0)  # stream_id = 0 is for primary camera

        self.target_start = 0
        self.target_end = 0

    def get_action(self):
        self.wireless.recv()
        self.wireless.get_message()

    def recv_fsm(self):
        self.get_action()
        while 1:
            if self.status == Status.IDLE:
                if self.wireless.target_enroll:
                    self.wireless.target_enroll = False
                    self.status = Status.ENROLL_WEB
                    self.event = Event.NULL
                    print("靶箱确认注册")
                else:
                    self.status = Status.IDLE
                    self.event = Event.NULL
                    print("靶箱注册中")
                    self.wireless.enroll()
                break
            if self.status == Status.ENROLL_WEB:
                # 跳过枪注册
                #if self.wireless.receive_enroll_flag:
                self.status = Status.GUN_ENROLL
                self.event = Event.OPEN_DETECT
                    # self.wireless.answer_gun([0x10])
               # else:
               #     self.status = Status.ENROLL_WEB
               #     self.event = Event.NULL
               #     break
            if self.status == Status.GUN_ENROLL:
                if self.wireless.receive_data_flag:
                    self.wireless.core_web_flag = True
                    self.wireless.receive_data_flag = False
                if self.wireless.receive_quit_flag:
                    print("枪退出")
                    self.wireless.receive_quit_flag = False
                    self.status = Status.ENROLL_WEB
                    self.event = Event.QUIT
                    break
                if self.wireless.core_web_flag and self.detect.open_flag:
                    self.status = Status.GUN_ENROLL
                    self.event = Event.SEND_POINT
                    self.wireless.core_web_flag = False
                else:
                    if self.detect.open_flag:
                        self.status = Status.GUN_ENROLL
                        self.event = Event.SEND_CURVE
                break
            else:
                break

    def event_handle(self):
        self.recv_fsm()
        while 1:
            if self.event == Event.OPEN_DETECT:
                self.detect.open_flag = True
                self.event = Event.NULL
                print("枪注册")
                break
            if self.event == Event.QUIT:
                self.wireless.open_flag = False
                self.wireless.receive_quit_flag = False
                self.wireless.receive_enroll_flag = False
                cv2.destroyAllWindows()
                self.webcam_stream.stop()
                self.event = Event.NULL
                print("close camera")
                break
            if self.event == Event.SEND_CURVE:
                if self.webcam_stream.stopped is True:
                    break
                else:
                    frame = self.webcam_stream.read()
                self.detect.mask(0x00, frame)
                mes = self.detect.update()
                if self.detect.update_flag:
                    self.detect.update_flag = 0
                    self.wireless.hit_curve(0x00, mes[0], mes[1], mes[2], mes[3], mes[4], mes[5], mes[6], mes[7])
                    self.target_start = time.time()
                    print("set time", self.target_start)
                    self.event = Event.NULL
                break
            elif self.event == Event.SEND_POINT:
                if self.webcam_stream.stopped:
                    break
                else:
                    frame = self.webcam_stream.read()
                self.detect.mask(0x01, frame)
                mes = self.detect.update()
                self.target_end = time.time()
                print("时间差", self.target_end, "-", self.target_start)
                if (self.target_end - self.target_start) > 0.4:
                    self.wireless.hit(0x01, 0, 0, mes[2], mes[3], mes[4], mes[5], mes[6], mes[7])
                else:
                    if mes[0] > 0:
                        self.wireless.hit(0x01, mes[0], mes[1], mes[2], mes[3], mes[4], mes[5], mes[6], mes[7])
                    else:
                        self.wireless.hit_lose()
                print("瞄准环数：", mes[0],
                      "击中环数：", mes[1],
                      "持枪晃动量：", mes[2],
                      "持枪晃动速率：", mes[3],
                      "击发晃动:", mes[4],
                      "击发晃动速率:", mes[5],
                      "中心坐标X:", mes[6],
                      "中心坐标Y:", mes[7])
                self.event = Event.NULL
                break
            else:
                self.event = Event.NULL
                break


def main():
    lc12s = Lc12s(19200, 0x01, 0xc8, 0x00, 0x0C, 0x1E, 0x14, 0X12)
    camera = Detector(False)
    core = Core(lc12s, camera)
    core.webcam_stream.start()
    while True:
        core.event_handle()


# 主程序部分
if __name__ == '__main__':
    main()
