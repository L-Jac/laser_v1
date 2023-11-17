"""
接收端nmap -p 22 192.168.2.0/24
"""
import serial
import keyboard
from loguru import logger
import time

ser = serial.Serial(
    port='COM4',  # 串口号，根据实际情况修改
    baudrate=19200,  # 波特率
    # parity=serial.PARITY_NONE,
    # stopbits=serial.STOPBITS_ONE,
)


def to_hex_string(b):
    return list(map(lambda x: hex(x), b))

def main():
    while True:
        if ser.inWaiting():
            uart_temp = ser.read(ser.inWaiting())
            logger.info("get: {}".format(to_hex_string(uart_temp)))
        else:
            if keyboard.is_pressed('q'):  # 如果按下'q'键
                logger.info('退出')
                break  # 跳出循环


if __name__ == '__main__':
    logger.info("Start")
    main()
