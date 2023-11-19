import serial

print("gun")
with serial.Serial("/dev/ttyUSB0", 9600, timeout=0.05) as ser:
    buf = [0xc0, 0x00, 0x08,
           0x03, 0xea, 0x84, 0x00, 0x0f, 0x03, 0x00, 0x00]
    ser.write(bytes(buf))
    r = ser.read(11)
    print(r)
    buf = [0xc1, 0x00, 0x08]
    ser.write(bytes(buf))
    r = ser.read(11)
    print(r)

print("system")
with serial.Serial("/dev/ttyUSB1", 9600, timeout=0.05) as ser:
    buf = [0xc0, 0x00, 0x08,
           0x03, 0xe9, 0x84, 0x00, 0x19, 0x03, 0x00, 0x00]
    ser.write(bytes(buf))
    r = ser.read(11)
    print(r)
    buf = [0xc1, 0x00, 0x08]
    ser.write(bytes(buf))
    r = ser.read(11)
    print(r)