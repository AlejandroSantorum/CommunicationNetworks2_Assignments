import socket as sck
import time
# import the library
from appJar import gui
from PIL import Image, ImageTk
import numpy as np
import cv2
import threading as thr

SEP_CODE = 35

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


class VideoClient(object):

    def __init__(self, window_size):

		# Creamos una variable que contenga el GUI principal
        self.app = gui("Redes2 - P2P", window_size)
        self.app.setGuiPadding(10,10)

		# Preparación del interfaz
        self.app.addLabel("title", "Cliente Multimedia P2P - Redes2 ")
        self.app.addImage("video", "imgs/webcam.gif")

		# Registramos la función de captura de video
		# Esta misma función también sirve para enviar un vídeo
        self.cap = cv2.VideoCapture(0)
        self.setImageResolution("HIGH")
        #self.app.setPollTime(20)
        #self.app.registerEvent(self.capturaVideo)
        thread = thr.Thread(target=self.capturaVideo)
        thread.start()

		# Añadir los botones
        self.app.addButtons(["Conectar", "Colgar", "Salir"], self.buttonsCallback)

		# Barra de estado
		# Debe actualizarse con información útil sobre la llamada (duración, FPS, etc...)
        self.app.addStatusbar(fields=2)

        thread_time = thr.Thread(target=self.call_duration)
        thread_time.start()

    def start(self):
        self.app.go()

	# Función que captura el frame a mostrar en cada momento
    def capturaVideo(self):
        mean_fps = 0
        nsums_fps = 0
        last_ts = 0
        time.sleep(1)
        while(1):
    		# Capturamos un frame de la cámara o del vídeo
            ret_read, frame = self.cap.read()
            if ret_read == False:
                print("Error reading frame before sending it")
                return

            # Compressing frame
            ret_comp, com_frame = compress_frame(frame)
            if ret_comp == False:
                print("Error compressing frame before sending it")
                return

            frame_bytes = com_frame.tobytes()

            # Preparing package header
            sep = "#"
            seq_num = 0
            # Writing sequence number + timestamp
            header = str(seq_num)+sep+str(time.time())+sep
            # Writing resolution
            header += (writePackageResolution("HIGH")+sep)
            # Writing FPS
            header += str(25)+sep

            pack_data = header.encode() + frame_bytes

            seq_num, ts, res_width, res_height, fps, com_frame = parse_package_data(pack_data)
            if last_ts == 0:
                last_ts = ts
            else:
                aux = ts - last_ts
                if nsums_fps == 0:
                    mean_fps = aux
                else:
                    mean_fps = ((nsums_fps * mean_fps) + aux)*(1/(nsums_fps+1))
                last_ts = ts
                nsums_fps += 1

            if(mean_fps != 0):
                print("MEAN_FPS: "+str(1/mean_fps)+" (of nsums="+str(nsums_fps)+")")


            frame = decompress_frame(com_frame)

            img_tk = prepare_Tk_image(frame, 640, 480)

    		# Lo mostramos en el GUI
            self.app.setImageData("video", img_tk, fmt = 'PhotoImage')

            time.sleep(1/25)

    		# Aquí tendría que el código que envia el frame a la red
    		# ...
    def call_duration(self):
        time_counter = 0
        while(1):
            h = time_counter // 3600
            h = str(h).zfill(2)
            min_aux = time_counter % 3600
            min = min_aux // 60
            min = str(min).zfill(2)
            sec = min_aux % 60
            sec = str(sec).zfill(2)
            time_str = h+":"+min+":"+sec
            self.app.setStatusbar("Call duration: "+time_str, 0)
            time_counter += 1
            time.sleep(0.95)


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

'''

# Getting frame
ret_read, frame = self.cap.read()
if ret_read == False:
    print("Error reading frame before sending it")
    continue

# Compressing frame
ret_comp, com_frame = compress_frame(frame)
if ret_comp == False:
    print("Error compressing frame before sending it")
    continue

frame_bytes = com_frame.tobytes()

frame = decompress_frame(frame_bytes)

img_tk = prepare_Tk_image(frame, res_width, res_height)
'''
