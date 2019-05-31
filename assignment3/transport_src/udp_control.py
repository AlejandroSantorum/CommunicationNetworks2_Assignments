################################################################################
#   Authors:                                                                   #
#       · Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es     #
#       · David Cabornero Pascual - david.cabornero@estudiante.uam.es          #
#   Date: Apr. 26, 2019                                                        #
#   File: udp_control.py                                                    #
#   Project: Communication Networks II Assignment 3                            #                                                            #
################################################################################
import socket as sck
import numpy as np
import cv2
import time
import threading as thr
from PIL import Image, ImageTk

PRNT = 0 # Priting flag: if it's set to 1, debugging messages will appear on terminal
###########################################
# USEFUL MACROS
LOW_RESOL_WIDTH = 160 # Low resolution width
LOW_RESOL_HEIGHT = 120 # Low resolution height
MID_RESOL_WIDTH = 320 # Medium resolution width
MID_RESOL_HEIGHT = 240 # Medium resolution height
HIGH_RESOL_WIDTH = 640 # High resolution width
HIGH_RESOL_HEIGHT = 480 # High resolution height
SEQ_NUM_IND = 0 # Array index of sequence number
TS_IND = 1 # Array index of timestamp
RES_IND = 2 # Array index of resolution
FPS_IND = 3 # Array index of FPS
COM_FRM_IND = 4 # Array index of data
SEP_CODE = 35 # '#' in binary
###########################################
# GLOBAL SHARED VARIABLES
RECV_SIZE = 1048576
call_flag = 1 # Flag that indicates the call is alive
pause_flag = 0 # Flag that indicates the call is paused or not
sleep_time = 1/15 # Time to sleep in case there exists congestion
send_fps = 25 # FPS field of sent packages header
recv_fps = 0 # FPS field of received packages header
###########################################

################################################################
# printf
# Input:
#   - message: string to be printed
# Output:
#   - None
# Description:
#   If PRNT macro is set to 1, it will print some information
#   on the terminal while executing VideoClient
################################################################
def printf(message):
    if PRNT:
        print(message)
################################################################
# udp_call_flag_raise
# Input:
#   - None
# Output:
#   - None
# Description:
#   It sets call_flag = 1
################################################################
def udp_call_flag_raise():
    global call_flag
    call_flag = 1

################################################################
# udp_call_flag_drop
# Input:
#   - None
# Output:
#   - None
# Description:
#   It sets call_flag = 0
################################################################
def udp_call_flag_drop():
    global call_flag
    call_flag = 0

################################################################
# udp_check_call_flag
# Input:
#   - None
# Output:
#   - 1 or 0 depending on call_flag value
# Description:
#   It returns current call_flag value
################################################################
def udp_check_call_flag():
    return call_flag

################################################################
# udp_pause_flag_swap
# Input:
#   - None
# Output:
#   - None
# Description:
#   It swaps pause_flag value, setting it to 0 if it's equal to
#   1 or viceversa
################################################################
def udp_pause_flag_swap():
    global pause_flag
    if pause_flag == 1:
        pause_flag = 0
    elif pause_flag == 0:
        pause_flag = 1

################################################################
# udp_pause_flag_raise
# Input:
#   - None
# Output:
#   - None
# Description:
#   It sets pause_flag = 1
################################################################
def udp_pause_flag_raise():
    global pause_flag
    pause_flag = 1

################################################################
# udp_pause_flag_drop
# Input:
#   - None
# Output:
#   - None
# Description:
#   It sets pause_flag = 0
################################################################
def udp_pause_flag_drop():
    global pause_flag
    pause_flag = 0

################################################################
# compress_frame
# Input:
#   - frame: a captured frame (represented as a matrix)
#   - resolution_perc (optional): the percentage we are reducing the frame
# Output:
#   - a Boolean value, True on success; False otherwise
#   - the compressed frame
# Description:
#   It compresses a given frame
################################################################
def compress_frame(frame, resolution_perc=50):
    encode_param = [cv2.IMWRITE_JPEG_QUALITY, resolution_perc]
    result, com_frame = cv2.imencode('.jpg', frame, encode_param)
    return result, com_frame

################################################################
# compress_frame
# Input:
#   - com_frame: a compressed frame
# Output:
#   - decompressed frame
# Description:
#   It decompresses a given compressed frame
################################################################
def decompress_frame(com_frame):
    frame = cv2.imdecode(np.frombuffer(com_frame, dtype=np.uint8), 1)
    return frame

################################################################
# getImageResolution
# Input:
#   - resolution: string "LOW", "MEDIUM" or "HIGH"
# Output:
#   - resolution_width: a integer value for the given resolution width
#   - resolution_heigth: a integer value for the fiven resolution height
# Description:
#   It switches between the possible resolutions and returns its
#   width and height
################################################################
def getImageResolution(resolution):
    if resolution == "LOW":
        res_width = LOW_RESOL_WIDTH
        res_height = LOW_RESOL_HEIGHT
    elif resolution == "MEDIUM":
        res_width = MID_RESOL_WIDTH
        res_height = MID_RESOL_HEIGHT
    elif resolution == "HIGH":
        res_width = HIGH_RESOL_WIDTH
        res_height = HIGH_RESOL_HEIGHT
    return res_width, res_height

################################################################
# getImageResolution
# Input:
#   - capturer: video capturer instance
#   - resolution: string "LOW", "MEDIUM" or "HIGH"
# Output:
#   - None
# Description:
#   Sets the capturer resolution
################################################################
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

################################################################
# writePackageResolution
# Input:
#   - resolution: string "LOW", "MEDIUM" or "HIGH"
# Output:
#   - string formed by width x heigth
# Description:
#   It prepares the package header resolution depending on
#   the given resolution string
################################################################
def writePackageResolution(resolution):
    sep = "x"
    if resolution == "LOW":
        return str(LOW_RESOL_WIDTH)+sep+str(LOW_RESOL_HEIGHT)
    elif resolution == "MEDIUM":
        return str(MID_RESOL_WIDTH)+sep+str(MID_RESOL_HEIGHT)
    elif resolution == "HIGH":
        return str(HIGH_RESOL_WIDTH)+sep+str(HIGH_RESOL_HEIGHT)

################################################################
# preapre_Tk_image
# Input:
#   - frame: a given frame
#   - res_width: width of the frame
#   - res_height: height of the frame
# Output:
#   - prepared image to be printed
# Description:
#   It prepares a given frame to be printed
################################################################
def prepare_Tk_image(frame, res_width, res_height):
    frame = cv2.resize(frame, (res_width, res_height))
    cv2_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_img))
    return img_tk

################################################################
# parse_package_data
# Input:
#   - data: package data (header+compressed frame)
# Output:
#   - seq_num: sequence number
#   - TS: timestamp
#   - res_width: frame width
#   - res_height: frame height
#   - fps: frame per second
#   - com_frame: compressed frame data
# Description:
#   It splits a given package into its individual fields
################################################################
def parse_package_data(data):
    sep = "#"
    length = len(data)
    cont = 4 # Number of '#' before data frame
    for i in range(0, length):
        if data[i] == SEP_CODE:
            cont -= 1
            if cont == 0:
                header = data[:i]
                com_frame = data[i+1:]
                break
    array = header.decode().split(sep)
    seq_num = int(array[0])
    ts = float(array[1])
    resolution = array[2]
    resolution = resolution.split("x")
    res_width = int(resolution[0])
    res_height = int(resolution[1])
    fps = int(array[3])
    return seq_num, ts, res_width, res_height, fps, com_frame


class FrameInformation:
    '''
    FrameInformation class
    Create the FrameInformation class in order to store a frame and its
    header fields

    Attributes (check __init__ function):
		__seq_num : sequence number
        __ts : timestamp
        __res_width : width
        __res_height : height
        __fps : fps
        __com_frame : compressed frame
    '''

    # All this class methods are way too intuitive to be commented
    def __init__(self, seq_num, ts, res_width, res_height, fps, com_frame):
        self.__seq_num = seq_num
        self.__ts = ts
        self.__res_width = res_width
        self.__res_height = res_height
        self.__fps = fps
        self.__com_frame = com_frame

    def get_seq_num(self):
        return self.__seq_num

    def get_ts(self):
        return self.__ts

    def get_width(self):
        return self.__res_width

    def get_height(self):
        return self.__res_height

    def get_fps(self):
        return self.__fps

    def get_com_frame(self):
        return self.__com_frame


class CircularBuffer:
    '''
    CircularBuffer class
    Create the CircularBuffer class in order to store a set of frames

    Attributes (check __init__ function):
		max_size : maximum number of frames
        index : index where the next frame is going to be stored
        buffer : array of FrameInformation instantiations
        nframes : number of frames in the circular buffer
        mutex : semaphore to insert/extract frames from the buffer
    '''

    ################################################################
    # Constructor
    # Input:
    #   - max_size: maximum number of frames
    # Output:
    #   - None
    # Description:
    #   It builds an instance of CircularBuffer, initializing all
    #   its indexes to -1
    ################################################################
    def __init__(self, max_size):
        # Maxmimum number of frames in the buffer
        self.max_size = max_size
        # Next insertion index
        self.index = 0
        # Buffer
        self.buffer = []
        # Init buffer
        for i in range(max_size):
            self.buffer.append(-1)
        # Number of inserted frames
        self.nframes = 0
        # Circular buffer semaphore
        self.mutex = thr.Lock()

    ################################################################
    # get_nframes
    # Input:
    #   - None
    # Output:
    #   - number of frames in the buffer
    # Description:
    #   It returns the current number of frames in the buffer
    ################################################################
    def get_nframes(self):
        self.mutex.acquire()
        ret = self.nframes # Number of frames in the buffer
        self.mutex.release()
        return ret

    ################################################################
    # insert_frameInfo
    # Input:
    #   - seq_num: frame sequence number
    #   - ts: frame timestamp
    #   - res_width: frame width
    #   - res_height: frame height
    #   - com_frame: compressed frame
    # Output:
    #   - None
    # Description:
    #   It creates a FrameInformation instantiation and inserts it into
    #   the circular buffer
    ################################################################
    def insert_frameInfo(self, seq_num, ts, res_width, res_height, fps, com_frame):
        # Protecting buffer with semaphore
        self.mutex.acquire()
        # Inserting frame in the current index indicator
        self.buffer[self.index] = FrameInformation(seq_num,ts,res_width,res_height,fps,com_frame)
        # Incrementing index mod max_size
        self.index = ((self.index + 1) % self.max_size)
        # Incrementing number of inserted frames
        self.nframes += 1
        self.mutex.release()

    ################################################################
    # extract_frame
    # Input:
    #   - None
    # Output:
    #   - seq_num: frame sequence number
    #   - ts: frame timestamp
    #   - res_width: frame width
    #   - res_height: frame height
    #   - com_frame: compressed frame
    # Description:
    #   It extracts the frame with the lowest sequence number
    ################################################################
    def extract_frame(self):
        # Protecting buffer with semaphore
        self.mutex.acquire()
        if self.nframes == 0:
            self.mutex.release()
            return -1,-1,-1,-1,-1,-1
        else:
            for i in range(self.max_size):
                if self.buffer[i] != -1:
                    min = self.buffer[i]
                    ind_min = i
        # Getting frame with minimum sequence number
        for i in range(ind_min+1, self.max_size):
            if self.buffer[i] == -1:
                continue
            else:
                if self.buffer[i].get_seq_num() < min.get_seq_num():
                    min = self.buffer[i]
                    ind_min = i
        # Getting data frame
        seq_num = min.get_seq_num()
        ts = min.get_ts()
        width = min.get_width()
        height = min.get_height()
        fps = min.get_fps()
        com_frame = min.get_com_frame()
        # Delete frame from buffer
        self.buffer[ind_min] = -1
        self.nframes -= 1
        self.mutex.release()
        return seq_num, ts, width, height, fps, com_frame

    ################################################################
    # recalculate_congestion
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It recalculates the FPS field of the sent packages header.
    #   This function must be used only if congestion control is
    #   activated
    ################################################################
    def recalculate_congestion(self):
        global send_fps
        # Setting up FPS header for sent packages depending on congestion of the buffer
        if self.nframes >= 80:
            send_fps = 10
        elif self.nframes >= 60:
            send_fps = 15
        elif self.nframes >= 40:
            send_fps = 25
        elif self.nframes >= 20:
            send_fps = 35
        elif self.nframes >= 10:
            send_fps = 45
        else:
            send_fps = 60



class UDP_Recver:
    '''
    UDP_Recver class
    Create the UDP_Recver class in order to receive frames from another user

    Attributes (check __init__ function):
		video_client: VideoClient instantiation
        recv_sck: UDP socket from where we get frames
        my_ip: user IP
        my_udp_port: user UDP port
        circular_buffer: CircularBuffer instantiation
    '''

    ################################################################
    # Constructor
    # Input:
    #   - video_client: VideoClient instantiation
    #   - my_ip: IP to bind the socket
    # Output:
    #   - None
    # Description:
    #   It initializes a UDP socket to receive frames from the other user
    ################################################################
    def __init__(self, video_client, my_ip):
        # GUI handler
        self.video_client = video_client
        # Opening UDP socket
        self.recv_sck = sck.socket(sck.AF_INET, sck.SOCK_DGRAM)
        # Binding socket to a given IP and getting a free port
        #my_ip = "192.168.8.100" # para abajo
        self.recv_sck.bind((my_ip, 0))
        self.my_ip, self.my_udp_port = self.recv_sck.getsockname()
        # Flag that indicates if the congestion control is activated
        self.congest_control = None
        # Circular buffer to reorder frames
        self.circular_buffer = CircularBuffer(100) # 100 = buffer max size

    ################################################################
    # close
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It closes the UDP receiver socket
    ################################################################
    def close(self):
        self.recv_sck.close()

    def get_my_UDP_port(self):
        return self.my_udp_port

    ################################################################
    # run_pack_recver
    # Input:
    #   - congest_control (optional): integer that indicates if
    #       congestion control is activated (default: 0)
    # Output:
    #   - None
    # Description:
    #   It runs the UDP receiver thread and the printer thread
    ################################################################
    def run_pack_recver(self, congest_control=0):
        self.congest_control = congest_control
        udp_call_flag_raise()
        # Thread that receives frames
        thread_recv = thr.Thread(target=self._recv_packages)
        thread_recv.start()
        # Waiting to recieve some data
        time.sleep(1)
        # Thread that showns received frames using GUI
        thread_show = thr.Thread(target=self._show_packages)
        thread_show.start()

    ################################################################
    # _recv_packages (private function)
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   Main function of the receiver thread: it tries to receive a
    #   package, parses it, inserts it into the circular buffer and
    #   evaluates the UDP congestion
    ################################################################
    def _recv_packages(self):
        global send_fps
        global recv_fps
        mean_fps = 0.1
        nsums_fps = 0
        last_ts = 0
        while(1):
            if call_flag == 0: # Call has ended
                printf("Recieving packages process has ended")
                break
            if pause_flag == 1: # Call is paused
                continue

            # Receiving packages
            try:
                data = self.recv_sck.recv(RECV_SIZE, sck.MSG_DONTWAIT) # Non-blocking
            except sck.error as err:
                continue
            # Parsing received package and splitting it
            seq_num, ts, res_width, res_height, recv_fps, com_frame = parse_package_data(data)
            # Inserting frame information into the circular buffer
            try:
                self.circular_buffer.insert_frameInfo(seq_num,ts,res_width,res_height,recv_fps,com_frame)
            except:
                print("Error inserting frame in circular buffer")
                continue
            # Recalculating FPS header of sent packages if congestion control is activated
            if self.congest_control:
                self.circular_buffer.recalculate_congestion()

    ################################################################
    # _show_packages (private function)
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   Main function of the printer thread: it tries to extract a
    #   frame from the circular buffer, prepares it and prints it
    #   using GUI functions.
    ################################################################
    def _show_packages(self):
        global send_fps
        global recv_fps
        while(1):
            if call_flag == 0: # Call has ended
                printf("Showing packages process has ended")
                break
            ret_nframes = self.circular_buffer.get_nframes()
            if ret_nframes == 0:
                continue

            seq_num, ts, res_width, res_height, fps, com_frame = self.circular_buffer.extract_frame()

            try:
                frame = decompress_frame(com_frame)
            except Exception as err:
                print("Error: ", err)
                print("Com_frame: ", com_frame)

            img_tk = prepare_Tk_image(frame, res_width, res_height)

            # Showing frame using GUI (only if it is not paused)
            if pause_flag == 0:
                self.video_client.show_recv_frame(img_tk) # Showing frame
                self.video_client.refresh_fps(send_fps, recv_fps) # Showing FPS


class UDP_Sender:
    '''
    UDP_Sender class
    Create the UDP_Sender class in order to send frames to another user

    Attributes (check __init__ function):
		video_client: VideoClient instantiation
        peer_ip: other peer user IP
        peer_port: other peer user UDP port
        send_sck: UDP socket from where we send frames
        cap: capturer of video (usually, from webcam)
    '''

    ################################################################
    # Constructor
    # Input:
    #   - video_client: VideoClient instantiation
    #   - peer_ip: other peer user IP
    #   - peer_port: other peer user UDP port
    # Output:
    #   - None
    # Description:
    #   It initializes a UDP socket to receive frames from the other user
    ################################################################
    def __init__(self, video_client, peer_ip, peer_port):
        # GUI handler
        self.video_client = video_client
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        # Opening UDP socket to send frames
        self.send_sck = sck.socket(sck.AF_INET, sck.SOCK_DGRAM)
        # Video capturer
        self.cap = None
        # Flag that indicates if congestion control is activated or not
        self.congest_control = None

    ################################################################
    # close
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It closes the UDP sender socket
    ################################################################
    def close(self):
        self.send_sck.close()

    ################################################################
    # run_pack_recver
    # Input:
    #   - capture_from: url of .mp4 video to send or 0 (to read the webcam)
    #   - resolution: resolution string
    #   - congest_control (optional): integer that indicates if
    #       congestion control is activated (default: 0)
    # Output:
    #   - None
    # Description:
    #   It runs the UDP sender thread
    ################################################################
    def run_pack_sender(self, capture_from=0, resolution="HIGH", congest_control=0):
        self.congest_control = congest_control
        udp_call_flag_raise()
        # Thread to emit frames
        thread = thr.Thread(target=self._send_packages, args=(capture_from,resolution,))
        thread.start()

    ################################################################
    # _send_packages (private function)
    # Input:
    #   - capture_from: url of .mp4 video to send or 0 (to read the webcam)
    #   - resolution: resolution string
    # Output:
    #   - None
    # Description:
    #   Main function of the sender thread: it sets up VideoCapturer,
    #   prepares image resolution, and then loops reading the video/
    #   /webcam in order to read frames, compressing them, calculating
    #   its header and sending them. It also perfoms a UDP congestion
    #   control
    ################################################################
    def _send_packages(self, capture_from, resolution):
        global send_fps
        global recv_fps
        # Init video capturer
        self.cap = cv2.VideoCapture(capture_from)
        # Setting image resolution
        setImageResolution(self.cap, resolution)
        cap = cv2.VideoCapture(0)
        seq_num = 0
        while(1):
            if call_flag == 0: # Call has ended
                printf("Sending packages process has ended")
                break

            if pause_flag == 1: # Call is paused
                continue

            ret_read, frame = cap.read()
            if ret_read == False:
                print("Error reading frame before sending it")
                continue

            # Compressing frame
            ret_comp, com_frame = compress_frame(frame)
            if ret_comp == False:
                print("Error compressing frame before sending it")
                continue

            frame_bytes = com_frame.tobytes()
            # Preparing package header
            sep = "#"
            # Writing sequence number + timestamp
            header = str(seq_num)+sep+str(time.time())+sep
            # Writing resolution
            header += (writePackageResolution(resolution)+sep)
            # Writing FPS
            header += str(send_fps)+sep
            # Concatenating header + compressed frame
            pack_data = header.encode() + frame_bytes

            try:
                # Sending frame
                self.send_sck.sendto(pack_data, (self.peer_ip, self.peer_port))
            except sck.error as err:
                print("Sending error: ", err)
                exit()

            seq_num += 1

            # Congestion control if activated
            if self.congest_control and recv_fps<=15:
                # Sleeping due to congestion
                time.sleep(sleep_time)

            # Getting correct resolution format
            res_width, res_height = getImageResolution(resolution)

            # Preparing frame to be shown
            img_tk = prepare_Tk_image(frame, res_width, res_height)

            # Showing frame using GUI
            self.video_client.show_send_frame(img_tk)

        # Closing socket after while(1) finishes
        self.send_sck.close()
