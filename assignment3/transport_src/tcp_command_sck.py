################################################################################
#   Authors:                                                                   #
#       · Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es     #
#       · David Cabornero Pascual - david.cabornero@estudiante.uam.es          #
#   Date: Apr. 26, 2019                                                        #
#   File: tcp_command_sck.py                                                   #
#   Project: Communication Networks II Assignment 3                            #                                                            #
################################################################################
import socket as sck
import signal
import time
from transport_src.udp_control import *
import threading as thr

PRNT = 0 # Priting flag: if it's set to 1, debugging messages will appear on terminal
###########################################
ERROR = -1
SUCCESS = 0
RECV_SIZE = 8192
CMD_IND = 0
NICK_IND = 1
PORT_IND = 2
MAX_WAIT_SECS = 30
###########################################
mutex = thr.Lock() # semaphore
mutex_pause = thr.Lock() #semaphore
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

class TCPCommandSocket:
    '''
    TCPCommandSocket class
    Create the TCP Commander class in order to communicate another user
    we are trying to establish a call with him/her

    Attributes (check __init__ function):
		video_client : Instance of the caller VideoClient
        call_sck : TCP socket of the connection with the other user
        call_flag : Flag that indicates if we're in a call (1) or not (0)
        pause_flag : Flag that indicates if the call is paused (1) or not (0)
        my_nickname : Name of the user who is establishing the connection
    '''

    ################################################################
    # Constructor
    # Input:
    #   - video_client: Instance of VideoClient
    # Output:
    #   - None
    # Description:
    #   It builds an instance of TCPCommandSocket, in order to
    #   establish a call with another user
    ################################################################
    def __init__(self, video_client):
        # Storing video client
        self.video_client = video_client
        # Call socket
        self.call_sck = None
        # Calling flag (indicates this user has sent a calling request)
        self.call_flag = 0
        # Indicates if the call has been paused
        self.pause_flag = 0
        self.my_nickname = None

    ################################################################
    # _open_TCP_socket (private function)
    # Input:
    #   - user_ip: IP or URL the user who we're calling
	#	- user_port: TCP port of the user who we're calling
    # Output:
    #   - None
    # Description:
    #   It opens and connects a socket with the user who we want to call
    ################################################################
    def _open_TCP_socket(self, user_ip, user_port):
        # Opening socket internet/TCP
        self.call_sck = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
        # Establishing connection
        self.call_sck.connect((user_ip, user_port))

    ################################################################
    # request_call
    # Input:
    #   - my_name: name of the caller user
    #   - user_ip: ip of the user who we want to call
    #   - user_port: TCP port of the user who we want to call
    #   - my_udp_port: My UDP port where I will receive frames in case
    #       the call is established
    # Output:
    #   - SUCCESS+Status Message on sucess, or ERROR+Error message
	#		if something went wrong
    # Description:
    #   It sends the command 'CALLING <name> <udp_port>' to the user
    #   who want to call
    ################################################################
    def request_call(self, my_name, user_ip, user_port, my_udp_port):
        self.my_nickname = my_name
        ret, msg_ret = self._check_calling_request()
        if ret == ERROR:
            return ERROR, msg_ret
        self.call_flag_raise()
        try:
            self._open_TCP_socket(user_ip, user_port)
            # Sending calling request
            command = "CALLING "+my_name+" "+str(my_udp_port)
            self.call_sck.send(command.encode())
            thread = thr.Thread(
                target = self._handle_call_request
            )
            thread.start()
        except sck.error as err:
            self.call_flag_drop()
            self.call_sck.close()
            error_msg = "No se ha podido establecer la llamada, el receptor no esta disponible"
            return ERROR, error_msg
        return SUCCESS, "Calling request sent"

    ################################################################
    # _handle_call_request (private function)
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It handles a calling request: receives CALL_ACCEPTED,
    #   CALL_DENIED or CALL_BUSY commands (and acts depending on them).
    #   It also establishes a timeout if the called user is away from
    #   keyboard. This function is run by a thread
    ################################################################
    def _handle_call_request(self):
        for i in range(MAX_WAIT_SECS):
            try:
                cmd_recv = self.call_sck.recv(RECV_SIZE, sck.MSG_DONTWAIT)
            except sck.error:
                time.sleep(1)
                continue
            cmd_array = cmd_recv.decode().split()
            if cmd_array[CMD_IND] == "CALL_ACCEPTED":
                printf("Recieved CALL_ACCEPTED")
                # Hiding all subwindows + showing call window
                self.video_client.set_up_call(cmd_array[PORT_IND])
                thread = thr.Thread(target=self._handle_call_commander)
                thread.start()
                return
            elif cmd_array[CMD_IND] == "CALL_DENIED":
                printf("Recieved CALL_DENIED")
                # Informing that the user has denied the call
                self.video_client.inform_call_denied()
                self.call_sck.close()
                self.call_flag_drop()
                return
            elif cmd_array[CMD_IND] == "CALL_BUSY":
                printf("Recieved CALL_BUSY")
                # Informing that the user is already in a call
                self.video_client.inform_call_busy()
                self.call_sck.close()
                self.call_flag_drop()
                return
        self.call_flag_drop()
        self.video_client.inform_call_not_answered()
        self.call_sck.close()
        return

    ################################################################
    # _handle_call_commander (private function)
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It handles a call: receives CALL_END,
    #   CALL_HOLD or CALL_RESUME commands (and acts depending on them).
    #   It also sends CALL_END, CALL_HOLD and CALL_RESUME if
    #   the user has pressed any of them
    ################################################################
    def _handle_call_commander(self):
        self.call_flag_raise()
        current_pause_flag = self._check_pause_flag()

        while(1):
            # Checking if the user has requested to end the call
            ret_call_flag = self._check_call_flag()

            if ret_call_flag == 0:
                try: # Ending call
                    cmd = "CALL_END "+self.my_nickname
                    self.call_sck.send(cmd.encode())
                    printf("Sent CALL_END at commander")
                    self.call_flag_drop()
                    self.call_sck.close()
                    return # Call is finished
                except Exception as err:
                    printf("Sending END_CALL error: ", err)
                    printf("Closing commander due to errror")
                    self.call_sck.close()
                    return

            # Checking if pause/resume has been pressed
            ret_pause_flag = self._check_pause_flag()
            if ret_pause_flag != current_pause_flag:
                if ret_pause_flag == 1:
                    current_pause_flag = 1
                    cmd = "CALL_HOLD "+self.my_nickname
                    self.call_sck.send(cmd.encode())
                    printf("Sent CALL_HOLD at commander")
                elif ret_pause_flag == 0:
                    current_pause_flag = 0
                    cmd = "CALL_RESUME "+self.my_nickname
                    self.call_sck.send(cmd.encode())
                    printf("Sent CALL_RESUME at commander")

            # Recieving possible command
            try:
                cmd_recv = self.call_sck.recv(RECV_SIZE, sck.MSG_DONTWAIT)
            except sck.error:
                continue

            # Parsing command
            cmd = cmd_recv.decode().split()
            if len(cmd) == 0: # Not valid data command
                continue

            # Switching through possible commands
            if cmd[CMD_IND] == "CALL_HOLD":
                printf("Recibido CALL_HOLD en TCP listener socket")
                current_pause_flag = 1
                udp_pause_flag_raise()
                self.pause_flag_raise()
            elif cmd[CMD_IND] == "CALL_RESUME":
                printf("Recibido CALL_RESUME en TCP listener socket")
                current_pause_flag = 0
                udp_pause_flag_drop()
                self.pause_flag_drop()
            elif cmd[CMD_IND] == "CALL_END":
                printf("Recibido CALL_END en TCP commander socket")
                # Finishing call
                self.call_flag_drop()
                # Showing main window GUI
                self.video_client.end_call()
                # Deleting socket
                self.call_sck.close()
                return

    ################################################################
    # _check_calling_request (private function)
    # Input:
    #   - None
    # Output:
    #   - SUCCESS+Status Message on sucess, or ERROR+Error message
	#		if something went wrong
    # Description:
    #   It checks if there is any call currently on progress
    ################################################################
    def _check_calling_request(self):
        mutex.acquire()
        if self.call_flag == 1:
            ret, msg_ret = ERROR, "Ya existe una petición de llamada actualmente"
        else:
            ret, msg_ret = SUCCESS, "Llamada disponible"
        mutex.release()
        return ret, msg_ret

    ################################################################
    # call_flag_raise
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It sets call_flag = 1 (using semaphores!)
    ################################################################
    def call_flag_raise(self):
        mutex.acquire()
        self.call_flag = 1
        mutex.release()

    ################################################################
    # call_flag_drop
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It sets call_flag = 0 (using semaphores!)
    ################################################################
    def call_flag_drop(self):
        mutex.acquire()
        self.call_flag = 0
        mutex.release()

    ################################################################
    # _check_call_flag (private function)
    # Input:
    #   - None
    # Output:
    #   - 1 or 0 depending on call_flag value
    # Description:
    #   It returns current call_flag value (using semaphores!)
    ################################################################
    def _check_call_flag(self):
        mutex.acquire()
        if self.call_flag == 1:
            ret = 1
        else:
            ret = 0
        mutex.release()
        return ret

    ################################################################
    # pause_flag_raise
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It sets pause_flag = 1 (using semaphores!)
    ################################################################
    def pause_flag_raise(self):
        mutex_pause.acquire()
        self.pause_flag = 1
        mutex_pause.release()

    ################################################################
    # pause_flag_drop
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It sets pause_flag = 0 (using semaphores!)
    ################################################################
    def pause_flag_drop(self):
        mutex_pause.acquire()
        self.pause_flag = 0
        mutex_pause.release()

    ################################################################
    # _check_pause_flag (private function)
    # Input:
    #   - None
    # Output:
    #   - 1 or 0 depending on pause_flag value
    # Description:
    #   It returns current pause_flag value (using semaphores!)
    ################################################################
    def _check_pause_flag(self):
        mutex_pause.acquire()
        if self.pause_flag == 1:
            ret = 1
        else:
            ret = 0
        mutex_pause.release()
        return ret

    ################################################################
    # pause_flag_swap (private function)
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It swaps pause_flag value, setting it to 0 if it's equal to
    #   1 or viceversa
    ################################################################
    def pause_flag_swap(self):
        ret = self._check_pause_flag()
        if ret == 1:
            self.pause_flag_drop()
        else:
            self.pause_flag_raise()
