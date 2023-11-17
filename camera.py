#!/usr/bin/python3
import time
import cv2
from threading import Thread  # library for implementing multi-threaded processing.

import numpy as np

from score import Score


class Detector:
    def __init__(self, open_flag):

        self.open_flag = open_flag
        self.center_list = []
        self.center = []
        self.center_x = 0
        self.center_y = 0
        self.frame_cnt = 1
        self.det_flag = 0
        self.score = Score()
        self.aim_xlist = []
        self.aim_ylist = []
        self.shoot_xlist = []
        self.shoot_ylist = []
        self.shoot_x_list = []
        self.shoot_y_list = []
        self.aim_ring = 0
        self.shoot_ring = 0
        self.shake = 0
        self.shake_v = 0
        self.shoot_shake = 0
        self.shoot_shake_v = 0
        self.update_flag = 0
        self.shoot_flag = 0

        pst1 = np.float32([[135.0, 100.0], [525.0, 95.0], [514.0, 470.0], [150, 470.0]])
        pst2 = np.float32([[0, 0], [480, 0], [480, 480], [0, 480]])
        matrix = cv2.getPerspectiveTransform(pst1, pst2)

        self.correct_m = matrix
        self.correct_w = 480
        self.correct_h = 480

    # 追踪激光点
    def highlight(self, img):
        if self.frame_cnt > 7:
            self.aim_xlist = []
            self.aim_ylist = []
            self.frame_cnt = 0
        if len(self.shoot_xlist) > 100:
            self.shoot_xlist = []
            self.shoot_ylist = []
        if self.open_flag:
            self.frame_cnt += 1
            frame = cv2.warpPerspective(img, self.correct_m, (480, 480))
            cv2.imwrite('../cut.png', frame)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (7, 7), 0)
            thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1]
            cents = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cents = cents[0] if len(cents) == 2 else cents[1]

            for c in cents:
                if cv2.contourArea(c) > 5:
                    m = cv2.moments(c)
                    if m["m00"] != 0:
                        cx = int(m["m10"] / m["m00"])
                        cy = int(m["m01"] / m["m00"])
                        self.center_list.append((cx, cy))
                        self.center = [cx, cy]
                        self.det_flag = 1
                    else:
                        self.det_flag = 0
                else:
                    self.det_flag = 0

    def get_center(self, frame):
        self.highlight(frame)
        if self.det_flag:
            return self.center
        else:
            return None

    def mask(self, flag, frame):
        self.highlight(frame)
        if self.det_flag:
            self.det_flag = 0
            self.aim_xlist.append(self.center[0])
            self.aim_ylist.append(self.center[1])
            self.shoot_xlist.append(self.center[0])
            self.shoot_ylist.append(self.center[1])
            self.shoot_x_list.append(self.center[0])
            self.shoot_y_list.append(self.center[1])
            self.center_x = self.center[0]
            self.center_y = self.center[1]
            self.center = []

            self.aim_ring = self.score.aim_ring(self.aim_xlist, self.aim_ylist)
            self.shake = self.score.shake(self.aim_xlist, self.aim_ylist)
            self.shake_v = self.score.shake(self.aim_xlist, self.aim_ylist)
            print(self.score.shoot_ring(self.center_x, self.center_y))
            print("self.frame_cnt", self.frame_cnt)
            if flag:
                self.shoot_ring = self.score.shoot_ring(self.center_x, self.center_y)
                if self.shoot_ring > 0:
                    print("打中", self.shoot_ring)
                    self.shoot_flag = 1
            self.shoot_shake = self.score.shoot_shake(self.shoot_xlist,
                                                      self.shoot_ylist,
                                                      self.center_x,
                                                      self.center_y)
            self.shoot_shake_v = self.score.shoot_shake_v(self.shoot_xlist,
                                                          self.shoot_ylist,
                                                          self.center_x,
                                                          self.center_y)
            self.shoot_x_list = []
            self.shoot_y_list = []
            self.update_flag = 1

    def update(self):
        if self.update_flag:
            return self.shoot_ring, self.aim_ring, self.shake, self.shake_v, self.shoot_shake, self.shoot_shake_v, self.center_x, self.center_y
        else:
            return 0, 0, 0, 0, 0, 0, 0, 0


class WebcamStream:

    def __init__(self, stream_id=0):
        self.stream_id = stream_id
        self.vcap = cv2.VideoCapture(self.stream_id)
        self.vcap.set(3, 640)
        self.vcap.set(4, 480)
        self.vcap.set(cv2.CAP_PROP_FPS, 30)
        if self.vcap.isOpened() is False:
            print("[Exiting]: Error accessing webcam stream.")
            exit(0)
        fps_input_stream = int(self.vcap.get(5))
        print("FPS of webcam hardware/input stream: {}".format(fps_input_stream))

        self.grabbed, self.frame = self.vcap.read()
        if self.grabbed is False:
            print('[Exiting] No more frames to read')
            exit(0)

        self.stopped = True
        self.t = Thread(target=self.update, args=())
        self.t.daemon = True

    def start(self):
        self.stopped = False
        self.t.start()

    # method for reading next frame
    def update(self):
        while True:
            if self.stopped is True:
                break
            self.grabbed, self.frame = self.vcap.read()
            if self.grabbed is False:
                print('帧读取失败')
                self.stopped = True
                break
        self.vcap.release()

    # method for returning latest read frame
    def read(self):
        return self.frame

    # method called to stop reading frames
    def stop(self):
        self.stopped = True
