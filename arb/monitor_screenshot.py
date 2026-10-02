import mss
import mss.tools
import cv2
import numpy as np

def screen_shot():
    with mss.MSS() as sct:
        monitor_number = 2
        mon = sct.monitors[monitor_number]
        # monitor = {"top": mon["top"]}
        sct_img = sct.grab(mon)
        return sct_img
