import keyboard
from loguru import logger
import serial
import time

# b'\x01\x03\x00\x09\x00\x01\x84\x0a'

ser = serial.Serial(
    port='COM3',  # 串口号，根据实际情况修改
    baudrate=19200,  # 波特率
    # parity=serial.PARITY_NONE,
    # stopbits=serial.STOPBITS_ONE,
)

message = [0x10, 0x01, 0x00, 0x09, 0x00, 0x01, 0x84, 0x09]
message_enroll = [0x16, 0x0, 0x10, 0x0, 0xc, 0x0, 0x0, 0x1, 0x0, 0x1e, 0x7, 0x8, 0x69, 0x70, 0x71]


def to_hex_string(b):
    return list(map(lambda x: hex(x), b))


def send(data_buffer):
    logger.info("send: {}".format(to_hex_string(data_buffer)))
    temp = bytearray(data_buffer)
    ser.write(temp)


def main():
    while True:

        if keyboard.is_pressed('q'):  # 如果按下'q'键
            logger.info('退出')
            break  # 跳出循环
        if ser.inWaiting():
            uart_temp = ser.read(ser.inWaiting())
            if uart_temp[0] == 0x00:
                logger.info("get: {}".format(to_hex_string(uart_temp)))
                send([0x10, 0x10, 0x10, 0x10])
            elif uart_temp[0] == 0x10:
                logger.info("get: {}".format(to_hex_string(uart_temp)))
                send([0x01, 0x10, 0x10, 0x10])
            elif uart_temp[0] == 0x16:
                logger.info("get: {}".format(to_hex_string(uart_temp)))
                send([0x01, 0x10, 0x10, 0x10])
            else:
                logger.info("get: {}".format(to_hex_string(uart_temp)))
                logger.info("?")
        else:
            time.sleep(1)
            send(message_enroll)


if __name__ == '__main__':
    logger.info("Start")
    main()
