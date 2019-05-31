import socket as sck
import time
from appJar import gui
from PIL import Image, ImageTk
import numpy as np
import cv2

LOW_RESOL_WIDTH = 160
LOW_RESOL_HEIGHT = 120
MID_RESOL_WIDTH = 320
MID_RESOL_HEIGHT = 240
HIGH_RESOL_WIDTH = 640
HIGH_RESOL_HEIGHT = 480

def setImageResolution(capturer, resolution):
    if resolution == "LOW":
        capturer.set(cv2.CAP_PROP_FRAME_WIDTH, LOW_RESOL_WIDTH)
        capturer.set(cv2.CAP_PROP_FRAME_HEIGHT, LOW_RESOL_HEIGHT)
    elif resolution == "MEDIUM":
        capturer.set(cv2.CAP_PROP_FRAME_WIDTH, MID_RESOL_WIDTH)
        capturer.set(cv2.CAP_PROP_FRAME_HEIGHT, MID_RESOL_HEIGHT)
    elif resolution == "HIGH":
        capturer.set(cv2.CAP_PROP_FRAME_WIDTH, HIGH_RESOL_WIDTH)
        capturer.set(cv2.CAP_PROP_FRAME_HEIGHT, HIGH_RESOL_HEIGHT)

def writePackageResolution(resolution):
    sep = "x"
    if resolution == "LOW":
        return str(LOW_RESOL_WIDTH)+sep+str(LOW_RESOL_HEIGHT)
    elif resolution == "MEDIUM":
        return str(MID_RESOL_WIDTH)+sep+str(MID_RESOL_HEIGHT)
    elif resolution == "HIGH":
        return str(HIGH_RESOL_WIDTH)+sep+str(HIGH_RESOL_HEIGHT)

def compress_frame(frame, resolution_perc=50):
    encode_param = [cv2.IMWRITE_JPEG_QUALITY, resolution_perc]
    result, com_frame = cv2.imencode('.jpg', frame, encode_param)
    return result, com_frame



if __name__ == "__main__":
    sending_fps = 15
    resolution = "HIGH"
    send_sck = sck.socket(sck.AF_INET, sck.SOCK_DGRAM)
    cap = cv2.VideoCapture(0)
    setImageResolution(cap, resolution)
    seq_num = 0
    while(1):
        ret_read, frame = cap.read()
        if ret_read == False:
            print("Error reading frame before sending it")
            exit()

        # Compressing frame
        ret_comp, com_frame = compress_frame(frame)
        if ret_comp == False:
            print("Error compressing frame before sending it")
            exit()

        frame_bytes = com_frame.tobytes()
        # Preparing package header
        sep = "#"
        # Writing sequence number + timestamp
        header = str(seq_num)+sep+str(int(time.time()))+sep
        # Writing resolution
        header += (writePackageResolution(resolution)+sep)
        # Writing FPS
        header += str(sending_fps)+sep

        pack_data = header.encode() + frame_bytes

        try:
            print("->", end="")
            send_sck.sendto(pack_data, ("127.0.0.1", 5005))
        except sck.error as err:
            print("Seding error: ", err)
            exit()

        seq_num += 1
        time.sleep(1/sending_fps)
    send_sck.close()
