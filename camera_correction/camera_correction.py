import cv2
from loguru import logger
import time

d = 10
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(gray)
    cv2.circle(frame, maxLoc, d, (0, 0, 255), -1)
    cv2.imshow('frame', frame)
    logger.info(f"坐标{maxLoc}")
    keyword = cv2.waitKey(30)
    if keyword == ord('q'):
        logger.info("exit")
        break
    elif keyword == ord('w'):
        d = d + 1
        logger.info(f"diameter{d}")
        time.sleep(0.5)
    elif keyword == ord('s'):
        d = d - 1
        logger.info(f"diameter{d}")
        time.sleep(0.5)

cap.release()
cv2.destroyAllWindows()
