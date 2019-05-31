################################################################################
#   Authors:                                                                   #
#       · Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es     #
#       · David Cabornero Pascual - david.cabornero@estudiante.uam.es          #
#   Date: Apr. 25, 2019                                                        #
#   File: video_client.py                                                      #
#   Project: Communication Networks II Assignment 3                            #                                                            #
################################################################################
from appJar import gui
from PIL import Image, ImageTk
import threading
import numpy as np
import socket as sck
import signal
import cv2
import sys
import requests
from transport_src.tcp_listen_sck import *
from transport_src.tcp_command_sck import *
from transport_src.udp_control import *
###########################################
# SOCKETS
DEFAULT_TCP_IP = "127.0.0.1"
DEFAULT_TCP_PORT = 5001
###########################################
# SERVER MACROS
DS_SERVER_NAME = "vega.ii.uam.es"
DS_SERVER_PORT = 8000
RECV_SIZE = 1048576
PROTOCOLS = "V0"
REGISTER_CMD = "REGISTER "
OK_ANS = "OK"
NOK_ANS = "NOK"
WEL_ANS = "WELCOME"
LIST_USERS_ANS = "USERS_LIST"
LIST_USERS_CMD = "LIST_USERS"
QUERY_CMD = "QUERY "
QUERY_ANS = "USER_FOUND"
QUIT_CMD = "QUIT"
BYE_ANS = "BYE"
CALL_ACCEPTED = "CALL_ACCEPTED"
CALL_DENIED = "CALL_DENIED"
CALL_BUDY = "CALL_BUSY"
###########################################
# USEFUL MACROS
SUCCESS = 0
ERROR = -1
SECS = 0.3
REGISTER = 1
EXIT = 2
OKNOK = 0
INFO = 1
NUSERS = 2
NAME = 2
TS_REG = 3
IP_QUERY = 3
PORT_QUERY = 4
PROTOCOLS_QUERY = 5
NICK_IND = 0
IP_IND = 1
PORT_IND = 2
PROTO_IND = 3
CMD_IND = 0
###########################################
# MESSAGE MACROS
USERS_LIST_INIT_MSG = "Pulse en un usuario para llamarlo o pulse \'Ocultar\' para volver a la pagina principal"
PORT_NOT_INT_FAIL = "El puerto introducido no es válido. Compruebe que esta entre 1024 y 65535"
QUERY_FAIL = "No se han encontrado resultados para la búsqueda"
CONN_FAIL = "ERROR DE CONEXIÓN: No se ha encontrado el usuario "
########################################################################################
class VideoClient():
	'''
    VideoClient class
    Create the Video Client to handle its functionality

    Attributes (check __init__ function):
		sever_sck : Socket to connect to Discover Server
		local_ip_addr : private IP address
		users_list : List to show when pressing "Mostrar usuarios" button
		tcp_listen_sck : TCP socket to listen to possible users who are calling us
		tcp_cmd_sck : TCP socket to request a call with another user
		my_udp_port : UDP port where I want to receive frames
		udp_send_sck : UDP socket to send frames to the calling user
		udp_recv_sck : UDP socket to receive frames from the calling user
		logged_nick : Nick of the user who has signed in
		logged_ip : IP of the user who has signed in
		logged_port : TCP port of the user who has signed in
		peer_nick : Nick of the user who we're having a call
		peer_ip : IP of the user who we're having a call
		peer_tcp_port : TCP port of the user who we're having a call
		peer_udp_port : UDP port of the user who we're having a call
		call_flag : Flag that indicates if we're in a call (1) or not (0)
		caller : Boolean value that indicates we're the caller user in a call
		app : GUI Instance
    '''

	################################################################
    # Constructor
    # Input:
    #   None
    # Output:
    #   - VideoClient instance
    # Description:
    #   It builds an instance of VideoClient, setting up all its
	#	attributes and preparing all GUI stuff
    ################################################################
	def __init__(self):
		# Discover server
		self.server_sck = self._open_DSsocket(DS_SERVER_NAME, DS_SERVER_PORT)
		self.users_list = None # List of users
		self.tcp_listen_sck = TCPListenerSocket(self) # TCP Listener socket
		self.tcp_cmd_sck = TCPCommandSocket(self) # TCP Commander socket
		self.my_udp_port = None # UDP port to receive frames
		self.udp_send_sck = None # UDP sender socket
		self.udp_recv_sck = None # UDP sender socket
		# Client nickname, ip and tcp port
		self.logged_nick = None
		self.logged_ip = None
		self.logged_port = None
		# Data of the user we are talking to (in case a call is established)
		self.peer_nick = None
		self.peer_ip = None
		self.peer_tcp_port = None
		self.peer_udp_port = None
		self.call_flag = 0 # Flag that indicates if we are in a call
		self.caller = False # Flag that indicates we are the user who has started the call
		self.congest_control = 0 # Flag that indicates if the user wants to check congestion
		#  ---------------- Main GUI ---------------- #
		self.app = gui("Redes2 - P2P")
		self.app.setGeometry(400, 500)
		self.app.setGuiPadding(10,10)
		#  ---------------- Registration and/or Sign in ---------------- #
		self.app.addLabel("register_name_label", "Nombre de usuario")
		self.app.addEntry("register_name_entry")
		self.app.addLabel("register_password_label", "Contraseña")
		self.app.addSecretEntry("register_password_entry")
		self.app.addLabel("register_ip_label", "Dirección IP")
		self.app.addRadioButton("default_ip",DEFAULT_TCP_IP) # Loopback IP
		self.app.addRadioButton("default_ip",requests.get('https://api.ipify.org').text) # Getting public IP
		# Getting private IP
		try:
			s = sck.socket(sck.AF_INET, sck.SOCK_DGRAM)
			s.connect(('8.8.8.8', 1)) # Getting private IP address with a tricky method
			self.local_ip_addr = s.getsockname()[0]
			s.close() # Closing auxiliary connection
			self.app.addRadioButton("default_ip", self.local_ip_addr)
		except:
			self.local_ip_addr = None
			pass # If you are connected using VPN the sentences above will raise an exception, but the app can keep running
		self.app.setRadioButton("default_ip",DEFAULT_TCP_IP)
		self.app.addLabel("register_port_label", "Puerto")
		self.app.addRadioButton("default_port",DEFAULT_TCP_PORT)
		self.app.addRadioButton("default_port","Personalizado")
		self.app.setRadioButton("default_port",DEFAULT_TCP_PORT)
		self.app.addEntry("register_port_entry")
		self.app.addCheckBox("Activar control de congestión (para desarrolladores)")
		self.app.addButtons(["Registrarse", "Salir"], self.registerCallback)
		#  ---------------- Main Window ---------------- #
		self.app.startSubWindow("main_window", title="CLIENTE MULTIMEDIA P2P - REDES 2")
		self.app.setGeometry(500, 500)
		self.app.addImage("main_p2p_img", "imgs/p2pimg.jpeg")
		self.app.addButtons(["Mostrar usuarios", "Buscar usuario", "Conectar", "Salir aplicación"], self.mainCallback)
		self.app.stopSubWindow()
		#  ---------------- Subwindow to list registered users ---------------- #
		self.app.startSubWindow("users_list_win", title="LISTADO DE USUARIOS", modal=True)
		self.app.setGeometry(400, 500)
		self.app.addMessage("users_list_msg", USERS_LIST_INIT_MSG)
		self.app.addButtons(["Ocultar"], self.usersListCallback)
		self.app.stopSubWindow()
		#  ---------------- Subwindow to ask the user to query ---------------- #
		self.app.startSubWindow("query_ask_win", title="BÚSQUEDA DE USUARIOS", modal=True)
		self.app.setGeometry(300, 140)
		self.app.addLabelEntry("Nick")
		self.app.addButtons(["Buscar Nick","Cancelar búsqueda"], self.queryCallback)
		self.app.addEmptyMessage("query message")
		self.app.stopSubWindow()
		#  ---------------- Subwindow to show the query results ---------------- #
		self.app.startSubWindow("query_result_win", title="USUARIOS ENCONTRADOS", modal=True)
		self.app.setGeometry(360, 260)
		self.app.addLabel("query nick")
		self.app.addLabel("query ip")
		self.app.addLabel("query port")
		self.app.addLabel("query protocols")
		self.app.addButton("Cerrar", self.closeQueryCallback)
		self.app.stopSubWindow()
		#  ---------------- Subwindow to stablish connection with an user ---------------- #
		self.app.startSubWindow("connect_win", title="CONEXIÓN CON UN USUARIO", modal=True)
		self.app.setGeometry(420, 180)
		self.app.addLabelEntry("Nombre del usuario a llamar")
		self.app.addEmptyMessage("connection_l")
		self.app.addButtons(["Llamar", "Volver"], self.connectCallback)
		self.app.stopSubWindow()
		#  ---------------- Subwindow to accept/deny a call ---------------- #
		self.app.startSubWindow("acc_den_call_win", title="LLAMADA ENTRANTE", modal=True)
		self.app.setGeometry(300, 200)
		self.app.addLabel("acc_den_call_l")
		self.app.addButtons(["Aceptar llamada", "Rechazar llamada"], self.pickUpCallback)
		self.app.stopSubWindow()
		#  ---------------- Subwindow to control the call ---------------- #
		self.app.startSubWindow("call_window", title="LLAMADA", modal=True)
		self.app.setGeometry(1000, 700)
		# Preparing interface
		video_send_row = 0
		video_send_col = 0
		video_recv_row = 0
		video_recv_col = 1
		self.app.addImage("video_send", "imgs/webcam.gif", video_send_row, video_send_col)
		self.app.addImage("video_recv", "imgs/webcam.gif", video_recv_row, video_recv_col)
		# Adding buttons
		self.app.addButton("Pausar/Retomar llamada", self.callingCallback, 1, 0)
		self.app.addButton("Colgar llamada", self.callingCallback, 1, 1)
		self.app.addLabel("call_duration_l", "Duracion de llamada: ", 2, 0)
		self.app.addLabel("fps_l", "FPS: ", 2, 1)
		self.app.stopSubWindow()

	################################################################
    # start
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It runs the VideoClient after instantiation
    ################################################################
	def start(self):
		self.app.go()

	################################################################
    # _close_client (private function)
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It closes and terminates VideoClient
    ################################################################
	def _close_client(self):
		self.server_sck.send(QUIT_CMD.encode())
		self.server_sck.close()
		self.app.stop()

	################################################################
    # _open_DSsocket (private function)
    # Input:
    #   - server_name: IP or URL of Discover Server
	#	- server_port: port of Discover Server
    # Output:
    #   - Socket of Discover Server on success. Exit the VideoClient
	#		on error case.
    # Description:
    #   It connects to Discover Server given the DS name and DS port.
    ################################################################
	def _open_DSsocket(self, server_name, server_port):
		print("Iniciando contacto con el servidor...")
		try:
			# Opening socket
			server_sck = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
			# Connection with server
			server_sck.connect((DS_SERVER_NAME, DS_SERVER_PORT))
			print("Contacto establecido exitosamente")
			return server_sck
		except sck.error as err:
			print("No ha sido posible establecer contacto con el servidor: "+str(err))
			exit()

	################################################################
    # _register (private function)
    # Input:
    #   - nickname: name of user to register
	#	- password: password of user to register
	#	- ip: IP of user to register
	#	- port: TCP port of user to register
    # Output:
    #   - SUCCESS+Status Message on sucess, or ERROR+Error message
	#		if something went wrong
    # Description:
    #   It sends a request to the Discover Server to register an user.
    ################################################################
	def _register(self, nickname, password, ip, port):
		# Preparing command string to be sent through socket
		command = REGISTER_CMD+nickname+" "+ip+" "+str(port)+" "+password+" "+PROTOCOLS
		# Sending command
		self.server_sck.send(command.encode())
		# Waiting for response
		server_answer = self.server_sck.recv(RECV_SIZE)
		# Parsing response
		ans = server_answer.decode()
		answer = ans.split()
		if answer[OKNOK] == OK_ANS and answer[INFO] == WEL_ANS:
			ret_msg = "Usuario \'"+answer[NAME]+"\' registrado con exito con timestamp="+answer[TS_REG]
			return SUCCESS, ret_msg
		elif answer[OKNOK] == NOK_ANS:
			ret_msg = "No se ha podido registrar al usuario \'"+nickname+"\': "+answer[INFO]
			return ERROR, ret_msg
		else:
			ret_msg = "Server error: "+ans
			return ERROR, ret_msg

	################################################################
    # _query (private function)
    # Input:
    #   - name: name of the user to query
    # Output:
    #   - Nick, IP, port and a list with handled protocols of the
	#		queried user on success, ERROR otherwise
    # Description:
    #   It sends a request to the Discover Server in order to
	#	get an user information (If it exists).
    ################################################################
	def _query(self, name):
		# Preparing command string to be sent through socket
		command = QUERY_CMD+" "+name
		# Sending command
		self.server_sck.send(command.encode())
		# Waiting for response
		server_answer = self.server_sck.recv(RECV_SIZE)
		# Parsing response
		ans = server_answer.decode()
		answer = ans.split()
		if answer[OKNOK] == OK_ANS and answer[INFO] == QUERY_ANS:
			protocols = ""
			protocols_list = answer[PROTOCOLS_QUERY].split("#")
			for prot in protocols_list:
				protocols += prot
			return [answer[NAME], answer[IP_QUERY], answer[PORT_QUERY], protocols]
		elif answer[OKNOK] == NOK_ANS:
			return ERROR
		else:
			print("Server error: "+ans)
			return ERROR

	################################################################
    # registerCallback
    # Input:
    #   - button: pressed button indentifier
    # Output:
    #   - None.
    # Description:
    #   It performs an action depending on the pressed button of
	#	the registration window
    ################################################################
	def registerCallback(self, button):
		if button == "Salir":
			# Exiting app
			self._close_client()
		elif button == "Registrarse":
			### Getting introduced nickname ###
			name = self.app.getEntry("register_name_entry")
			### Getting introduced password ###
			password = self.app.getEntry("register_password_entry")
			### Getting introduced IP ###
			if self.app.getRadioButton("default_ip") == DEFAULT_TCP_IP: # Default IP (Callback IP)
				ds_ip = DEFAULT_TCP_IP
				sockets_ip = DEFAULT_TCP_IP
			elif self.app.getRadioButton("default_ip") == self.local_ip_addr: #(private IP)
				ds_ip = self.app.getRadioButton("default_ip")
				sockets_ip = self.app.getRadioButton("default_ip")
			else:
				ds_ip = self.app.getRadioButton("default_ip") #(public IP)
				if self.local_ip_addr != None:
					sockets_ip = self.local_ip_addr #(private IP)
				else:
					sockets_ip = ds_ip
			### Getting introduced port ###
			if self.app.getRadioButton("default_port") == str(DEFAULT_TCP_PORT): # Default port
				port = DEFAULT_TCP_PORT
			else:
				port = self.app.getEntry("register_port_entry")
				try: # Checking port is an integer
					port = int(port)
				except ValueError: # Error: port is not an integer
					self.app.warningBox("Puerto erróneo", PORT_NOT_INT_FAIL)
					return
			### Getting introduced congestion control option ###
			if self.app.getCheckBox("Activar control de congestión (para desarrolladores)"):
				self.congest_control = 1
			# Sending command to sign up
			ret, msg = self._register(name, password, ds_ip, port)
			if ret == ERROR:
				# Error at registering
				self.app.warningBox("Error de registro", msg)
			else:
				# Success
				self.app.infoBox("Cliente iniciado con exito", msg)
				self.app.hide()
				# Saving logged user information
				self.logged_nick = name
				self.logged_ip = sockets_ip
				self.logged_port = port
				# Running UDP receiver socket to get a free UDP port
				self.init_UDP_recver()
				# Running TCP Listener socket using the registered IP+port
				self.tcp_listen_sck.run(name, self.my_udp_port, sockets_ip, port)
				# Showning main window
				self.app.showSubWindow("main_window")

	def init_UDP_recver(self):
		self.udp_recv_sck = UDP_Recver(self, self.logged_ip)
		self.my_udp_port = self.udp_recv_sck.get_my_UDP_port()

	################################################################
    # mainCallback
    # Input:
    #   - button: pressed button indentifier
    # Output:
    #   - None.
    # Description:
    #   It performs an action depending on the pressed button of
	#	the main window
    ################################################################
	def mainCallback(self, button):
		if button == "Mostrar usuarios":
			# Sending a request to the discover server
			self._get_users_list()
			self.app.openSubWindow("users_list_win")
			self.app.addGrid("users_list_grid", self.users_list, action=self._call_user_by_row)
			self.app.stopSubWindow()
			self.app.showSubWindow("users_list_win")
		elif button == "Buscar usuario":
			self.app.showSubWindow("query_ask_win")
		elif button == "Conectar":
			self.app.showSubWindow("connect_win")
		elif button == "Salir aplicación":
			# Exiting app
			self.tcp_listen_sck.shutdown()
			self.udp_recv_sck.close()
			self._close_client()

	################################################################
    # _get_users_list (private function)
    # Input:
    #   - None
    # Output:
    #   - None.
    # Description:
    #   It sends a request to the DS to get all the users list,
	#	and it stores this list (in the desired format) in the
	#	self.users_list attribute
    ################################################################
	def _get_users_list(self):
		# Preparing command
		command = LIST_USERS_CMD
		self.server_sck.send(command.encode())
		# Getting answer
		server_answer = self.server_sck.recv(RECV_SIZE)
		# Casting to string
		answer = server_answer.decode()

		ans_array = answer.split(" ")
		if ans_array[OKNOK] != "OK":
			print("Discover server error: Unable to receive users list")
			return ERROR
		else:
			nusers = ans_array[NUSERS]
			answer = answer[len("OK")+1 + len(LIST_USERS_ANS)+1 + len(str(nusers))+1:] #Removing header (+1 its becuase of spaces)
			self.users_list = [["NOMBRE", "IP", "PUERTO"]]
			users = answer.split("#")
			for user in users:
				if self._is_valid_user(user):
					self.users_list.append(user.split(" ")[:-1])

	################################################################
    # _is_valid_user (private function)
    # Input:
    #   - user: a list of user attributes
    # Output:
    #   - Boolean value: True if the obtained lsit truly represents
	#		an user information, False otherwise
    # Description:
    #   It sends a request to the DS to get all the users list,
	#	and it stores this list (in the desired format) in the
	#	self.users_list attribute
    ################################################################
	def _is_valid_user(self, user):
		if len(user.split(" ")) >= 3: # 3 becuase of NICK, IP, PORT fields
			return True
		else:
			return False

	################################################################
    # _call_user_by_row (private function)
    # Input:
    #   - selected_row: row of the selected user (indexed in 1)
    # Output:
    #   - None.
    # Description:
    #   It uses a TCP socket in order to request a call with a given
	#	user. This function just sends the CALLING command, it does
	# 	not wait for the response
    ################################################################
	def _call_user_by_row(self, selected_row):
		user_info = self.users_list[selected_row+1]
		# Calling the same function that we would call if
		# we would have written the username on the
		# connection request window
		try:
			peer_port = int(user_info[PORT_IND]) # Trying to convert port to integer
		except ValueError:
			self.app.clearMessage("users_list_msg")
			msg = "El puerto con que se ha registrado dicho usuario no es válido"
			self.app.setMessage("users_list_msg", msg)
			return
		# Calling request_call function with the information we already know
		self._request_callf(user_info[NICK_IND], user_info[IP_IND], peer_port, "users_list_msg")

	################################################################
    # usersListCallback
    # Input:
    #   - button: pressed button indentifier
    # Output:
    #   - None.
    # Description:
    #   It performs an action depending on the pressed button of
	#	the users list window
    ################################################################
	def usersListCallback(self, button):
		if button == "Ocultar":
			self.app.hideSubWindow("users_list_win")
			self.app.removeGrid("users_list_grid")
			self.app.showSubWindow("main_window")

	################################################################
    # queryCallback
    # Input:
    #   - button: pressed button indentifier
    # Output:
    #   - None.
    # Description:
    #   It performs an action depending on the pressed button of
	#	the query window
    ################################################################
	def queryCallback(self, button):
		if button == "Buscar Nick":
			nick = self.app.getEntry("Nick")
			answer = self._query(nick)
			if(answer != ERROR):
				self.app.clearMessage("query message")
				self.app.setLabel("query nick","Nombre: "+answer[NICK_IND])
				self.app.setLabel("query ip", "Dirección IP: "+answer[IP_IND])
				self.app.setLabel("query port", "Puerto: "+answer[PORT_IND])
				self.app.setLabel("query protocols", "Protocolos: "+answer[PROTO_IND])
				self.app.hideSubWindow("query_ask_win")
				self.app.showSubWindow("query_result_win")
			else:
				self.app.clearMessage("query message")
				self.app.setMessage("query message",QUERY_FAIL)
		elif button == "Cancelar búsqueda":
			self.app.clearMessage("query message")
			self.app.hideSubWindow("query_ask_win")

	################################################################
	# closeQueryCallback
	# Input:
	#   - None
	# Output:
	#   - None.
	# Description:
	#   It hides result query window and shows query window
	################################################################
	def closeQueryCallback(self, button):
		self.app.hideSubWindow("query_result_win")
		self.app.showSubWindow("query_ask_win")

	################################################################
	# connectCallback
	# Input:
	#   - button: pressed button indentifier
	# Output:
	#   - None.
	# Description:
	#   It performs an action depending on the pressed button of
	#	the connection window (the window to establish a call)
	################################################################
	def connectCallback(self, button):
		if button == "Llamar":
			nick = self.app.getEntry("Nombre del usuario a llamar")
			self._request_callf(nick)
		elif button == "Volver":
			self.app.clearMessage("connection_l")
			self.app.hideSubWindow("connect_win")

	################################################################
    # _request_callf (private function)
    # Input:
    #   - peer_nick: nick of the user who we want to call
	#	- peer_ip (optional): IP of the user who we want to call
	#	- peer_port (optional): TCP port of the user who we want to call
	#	- win_str (optional): Identifier of the GUI's window to show feedback
    # Output:
    #   - None.
    # Description:
    #   It uses a TCP socket in order to request a call with a given
	#	user. This function just sends the CALLING command, it does
	# 	not wait for the response.
	#	This function can be call from the connection request
	#	window callback or from the user list callback
    ################################################################
	def _request_callf(self, peer_nick, peer_ip=None, peer_port=None, win_str="connection_l"):
		if peer_ip==None or peer_port==None:
			answer = self._query(peer_nick) # It needs to get the information from a query
			if answer != ERROR:
				# Converting port to integer
				try:
					peer_port = int(answer[PORT_IND])
					peer_ip = answer[IP_IND]
				except ValueError:
					self.app.clearMessage(win_str)
					msg = "El puerto con que se ha registrado dicho usuario no es válido"
					self.app.setMessage(win_str, msg)
					return
			else: # Error when quering
				self.app.clearMessage(win_str)
				self.app.setMessage(win_str, CONN_FAIL+"\'"+peer_nick+"\'")
		# Calling given user establishing a TCP connection
		ret, msg_ret = self.tcp_cmd_sck.request_call(self.logged_nick, peer_ip, peer_port, self.my_udp_port)
		if ret == ERROR:
			self.app.clearMessage(win_str)
			self.app.setMessage(win_str, msg_ret)
		elif ret == SUCCESS: # Priting a 'calling' message and waiting the other user to response
			self.app.clearMessage(win_str)
			self.app.setMessage(win_str, "Llamando al usuario \'"+peer_nick+"\'")
			self.caller = True
			self.peer_ip = peer_ip
			self.peer_tcp_port = peer_port

	################################################################
    # pickUpCallback
    # Input:
    #   - button: pressed button indentifier
    # Output:
    #   - None.
    # Description:
    #   It performs an action depending on the pressed button of
	#	the pickUp window (the window to acept/deny a call)
    ################################################################
	def pickUpCallback(self, button):
		if button == "Aceptar llamada":
			self.tcp_listen_sck.ans_flag_accept() # Accepting call
			self.app.hideSubWindow("acc_den_call_win")
		elif button == "Rechazar llamada":
			# Setting up deny flag
			self.tcp_listen_sck.ans_flag_deny()
			# Deleting other peer info
			self.peer_nick = None
			self.peer_ip = None
			self.peer_udp_port = None
			# Showing back main window
			self.app.hideSubWindow("acc_den_call_win")
			self.app.showSubWindow("main_window")

	################################################################
    # pick_up_call
    # Input:
    #   - nickname: nick of the user who is calling
	#	- ip: ip of the user who is calling
	#	- udp_port: UDP port of the user who is calling
    # Output:
    #   - None.
    # Description:
    #   It shows a new window where the user can accept or deny
	#	a requested call
    ################################################################
	def pick_up_call(self, nickname, ip, udp_port):
		# Showing accept/deny window
		self.app.showSubWindow("acc_den_call_win")
		self.app.setLabel("acc_den_call_l", "Llamada entrante del usuario \'"+nickname+"\'")
		# Setting up other peer info
		self.peer_nick = nickname
		self.peer_ip = ip
		try:
			self.peer_udp_port = int(udp_port)
		except ValueError:
			print("ERROR: the other peer UDP port is not valid!")

	################################################################
    # set_up_call
    # Input:
    #   - peer_udp_port (optional): UDP port of the user who we're are calling
    # Output:
    #   - None.
    # Description:
    #   It sets up a call, initializing UDP Sending socket, and running
	#	UDP sender and receiver sockets (as a threads). It also sets up
	# 	GUI windows for the call
    ################################################################
	def set_up_call(self, peer_udp_port=None):
		self.app.hideSubWindow("users_list_win")
		self.app.showSubWindow("call_window")
		if peer_udp_port != None:
			try:
				self.peer_udp_port = int(peer_udp_port)
			except ValueError:
				print("ERROR: the other peer UDP port is not valid!")
				return
		try:
			self.udp_send_sck = UDP_Sender(self, self.peer_ip, self.peer_udp_port)
		except sck.error as err:
			print("ERROR: Unable to open udp sender socket: "+str(err))
			# Deleting other peer info
			self.peer_nick = None
			self.peer_ip = None
			self.peer_udp_port = None
			# Showing back main window
			self.app.hideSubWindow("call_window")
			self.app.showSubWindow("main_window")
			self.udp_recv_sck.close()
			return
		# Initializing frames capture
		self.udp_recv_sck.run_pack_recver(congest_control=self.congest_control)
		time.sleep(1)
		# Initializing frames delivery
		self.udp_send_sck.run_pack_sender(congest_control=self.congest_control)
		# Call duration thread
		self.call_flag = 1
		call_durat_thr = thr.Thread(target=self._show_call_duration)
		call_durat_thr.start()

	################################################################
    # callingCallback
    # Input:
    #   - button: pressed button indentifier
    # Output:
    #   - None.
    # Description:
    #   It performs an action depending on the pressed button of
	#	the calling window
    ################################################################
	def callingCallback(self, button):
		if button == "Colgar llamada":
			print("Pressed End Call")
			self.close_TCP_connection()
			self.end_call()
		elif button == "Pausar/Retomar llamada":
			# Activating pause or retaking the call (depending the current status)
			udp_pause_flag_swap()
			if self.caller == True:
				self.tcp_cmd_sck.pause_flag_swap()
			else:
				self.tcp_listen_sck.pause_flag_swap()

	################################################################
    # _show_call_duration (private function)
    # Input:
    #   - None
    # Output:
    #   - None.
    # Description:
    #   It is the routine function of the thread that prints the
	#	duration
    ################################################################
	def _show_call_duration(self):
		time_counter = 0
		while(self.call_flag):
			h = time_counter // 3600 # Converting seconds into hours
			h = str(h).zfill(2) # Filling with two significative digits
			min_aux = time_counter % 3600
			min = min_aux // 60 # Converting the rest of the secs into mins
			min = str(min).zfill(2) # Filling with two significative digits
			sec = min_aux % 60 # Getting seconds
			sec = str(sec).zfill(2) # Filling with two significative digits
			time_str = h+":"+min+":"+sec # Converting to a string
			self.app.setLabel("call_duration_l", "Duracion de llamada: "+time_str)
			time_counter += 1 # Incrementing one second
			time.sleep(0.95) # Sleeping for a second (minus an aproximation of the time used)

	################################################################
    # close_TCP_connection
    # Input:
    #   - None
    # Output:
    #   - None.
    # Description:
    #   It terminates a call droping TCP call flags
    ################################################################
	def close_TCP_connection(self):
		if self.caller == True:
			# If we are calling, we finish the TCP commander socket
			self.tcp_cmd_sck.call_flag_drop()
			self.caller = False
		else:
			# Closing TCP control socket
			self.tcp_listen_sck.call_flag_drop()

	################################################################
    # end_call
    # Input:
    #   - None
    # Output:
    #   - None.
    # Description:
    #   It terminates a call and drops UDP call flags
    ################################################################
	def end_call(self):
		self.call_flag = 0
		# Closing UDP sockets
		udp_call_flag_drop()
		# Showing back main window
		self.app.hideSubWindow("call_window")
		self.app.showSubWindow("main_window")

	################################################################
    # inform_call_denied
    # Input:
    #   - None
    # Output:
    #   - None.
    # Description:
    #   It prints in the desired window that the call have been denied
    ################################################################
	def inform_call_denied(self):
		self.caller = False
		self.app.clearMessage("connection_l")
		self.app.setMessage("connection_l", "El usuario ha rechazado la llamada")

	################################################################
    # inform_call_busy
    # Input:
    #   - None
    # Output:
    #   - None.
    # Description:
    #   It prints in the desired window that the user who we're
	#	calling is currently on a call
    ################################################################
	def inform_call_busy(self):
		self.caller = False
		self.app.clearMessage("connection_l")
		self.app.setMessage("connection_l", "El usuario se encuentra ya en llamada")

	################################################################
    # inform_call_not_answered
    # Input:
    #   - None
    # Output:
    #   - None.
    # Description:
    #   It prints in the desired window that the call cannot be
	#	establish because the user does not response
    ################################################################
	def inform_call_not_answered(self):
		self.app.hideSubWindow("acc_den_call_win")
		self.caller = False
		self.app.clearMessage("connection_l")
		self.app.setMessage("connection_l", "El usuario no ha contestado, puede que se encuentre ausente")

	################################################################
    # show_recv_frame
    # Input:
    #   - image: a decompress frame (an image)
    # Output:
    #   - None.
    # Description:
    #   It prints in the desired window the received frame of a call
    ################################################################
	def show_recv_frame(self, image):
		# Showing received frame
		self.app.setImageData("video_recv", image, fmt='PhotoImage')

	################################################################
    # show_send_frame
    # Input:
    #   - image: a decompress frame (an image)
    # Output:
    #   - None.
    # Description:
    #   It prints in the desired window the sent frame of a call
    ################################################################
	def show_send_frame(self, image):
		# Showing sent frame
		self.app.setImageData("video_send", image, fmt='PhotoImage')

	################################################################
    # refresh_fps
    # Input:
    #   - send_fps: FPS sent
	#	- recv_fps FPS received
    # Output:
    #   - None.
    # Description:
    #   It prints in the desired window the FPS information
    ################################################################
	def refresh_fps(self, send_fps, recv_fps):
		# Refreshing FPS info
		info = "FPS de envio: "+str(send_fps)+"\nFPS de recepcion: "+str(recv_fps)
		self.app.setLabel("fps_l", info)

########################################################################################
if __name__ == '__main__':
	vc = VideoClient() # Init video client
	vc.start()
