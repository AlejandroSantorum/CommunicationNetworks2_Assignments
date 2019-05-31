import socket as sck
import time
import threading as thr
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

RECV_SIZE = 1048576


LOW_RESOL_WIDTH = 160
LOW_RESOL_HEIGHT = 120
MID_RESOL_WIDTH = 320
MID_RESOL_HEIGHT = 240
HIGH_RESOL_WIDTH = 640
HIGH_RESOL_HEIGHT = 480


def compress_frame(frame, resolution_perc=50):
    encode_param = [cv2.IMWRITE_JPEG_QUALITY, resolution_perc]
    result, com_frame = cv2.imencode('.jpg', frame, encode_param)
    return result, com_frame

def decompress_frame(com_frame):
    frame = cv2.imdecode(np.frombuffer(com_frame, dtype=np.uint8), 1)
    return frame


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


def setImageResolution2(capturer, resolution):
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

def prepare_Tk_image(frame, res_width, res_height):
    frame = cv2.resize(frame, (res_width, res_height))
    cv2_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_img))
    return img_tk

    frame = cv2.resize(frame, (640,480))
    cv2_im = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))

def parse_package_data(data):
    sep = "#"
    length = len(data)
    cont = 4 # Number of '#' before data frame
    for i in range(0, length):
        if data[i] == 35:
            cont -= 1
            if cont == 0:
                header = data[:i]
                com_frame = data[i+1:]
                break
    array = header.decode().split(sep)
    seq_num = int(array[0])
    ts = int(array[1])
    resolution = array[2]
    resolution = resolution.split("x")
    res_width = int(resolution[0])
    res_height = int(resolution[1])
    fps = int(array[3])
    return seq_num, ts, res_width, res_height, fps, com_frame




class FrameInformation:

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

    def get_nframes(self):
        self.mutex.acquire()
        ret = self.nframes
        self.mutex.release()
        return ret

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



class VideoClient(object):

    def __init__(self, window_size):

		# Creamos una variable que contenga el GUI principal
        self.app = gui("Redes2 - P2P", window_size)
        self.app.setGuiPadding(10,10)

		# Preparación del interfaz
        self.app.addLabel("title", "Cliente Multimedia P2P - Redes2 ")
        self.app.addImage("video", "imgs/webcam.gif")

        ####################self.setImageResolution("HIGH")

		# Añadir los botones
        self.app.addButtons(["Conectar", "Colgar", "Salir"], self.buttonsCallback)

		# Barra de estado
		# Debe actualizarse con información útil sobre la llamada (duración, FPS, etc...)
        self.app.addStatusbar(fields=2)

        self.circular_buffer = CircularBuffer(100)


    def start(self):
        thread_insert = thr.Thread(target=self.recv_insert_test)
        thread_insert.start()
        time.sleep(1)
        thread_show = thr.Thread(target=self.show_test)
        thread_show.start()
        self.app.go()

	# Función que captura el frame a mostrar en cada momento
    def recv_insert_test(self):
        self.recv_sck = sck.socket(sck.AF_INET, sck.SOCK_DGRAM)
        # Binding socket to a given IP and getting a free port
        self.recv_sck.bind(("127.0.0.1", 5005))
        while(1):
            try:
                data = self.recv_sck.recv(RECV_SIZE, sck.MSG_DONTWAIT) # Non-blocking
            except sck.error as err:
                continue

            seq_num, ts, res_width, res_height, fps, com_frame = parse_package_data(data)

            try:
                self.circular_buffer.insert_frameInfo(seq_num,ts,res_width,res_height,fps,com_frame)
            except:
                print("No se inserta bien")
        self.recv_sck.close()



    def show_test(self):
        while(1):
            ret_nframes = self.circular_buffer.get_nframes()
            if ret_nframes == 0:
                continue

            seq_num, ts, res_width, res_height, fps, com_frame = self.circular_buffer.extract_frame()

            try:
                frame = decompress_frame(com_frame)
            except Exception as err:
                print("Error: ", err)
                print("Com_frame: ", com_frame)

            img_tk = prepare_Tk_image(frame, 640, 480)

            # Lo mostramos en el GUI
            self.app.setImageData("video", img_tk, fmt = 'PhotoImage')





	# Establece la resolución de la imagen capturada
    def setImageResolution(self, resolution):
		# Se establece la resolución de captura de la webcam
		# Puede añadirse algún valor superior si la cámara lo permite
		# pero no modificar estos
        if resolution == "LOW":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
        elif resolution == "MEDIUM":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        elif resolution == "HIGH":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

	# Función que gestiona los callbacks de los botones
    def buttonsCallback(self, button):

	    if button == "Salir":
	    	# Salimos de la aplicación
	        self.app.stop()
	    elif button == "Conectar":
	        # Entrada del nick del usuario a conectar
	        nick = self.app.textBox("Conexión",
	        	"Introduce el nick del usuario a buscar")

if __name__ == '__main__':

	vc = VideoClient("640x520")

	# Crear aquí los threads de lectura, de recepción y,
	# en general, todo el código de inicialización que sea necesario
	# ...


	# Lanza el bucle principal del GUI
	# El control ya NO vuelve de esta función, por lo que todas las
	# acciones deberán ser gestionadas desde callbacks y threads
	vc.start()
