################################################################################
#   Authors:                                                                   #
#       · Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es     #
#       · David Cabornero Pascual - david.cabornero@estudiante.uam.es          #
#   Date: Apr. 26, 2019                                                        #
#   File: tcp_listen_sck.py                                                    #
#   Project: Communication Networks II Assignment 3                            #                                                            #
################################################################################
import socket as sck
import time
import threading as thr
from transport_src.udp_control import *

PRNT = 0 # Priting flag: if it's set to 1, debugging messages will appear on terminal
###########################################
# USEFUL MACROS
RECV_SIZE = 8192 # Maximum size of a received message
MAX_WAIT_SECS = 30 # Maximum number of seconds to wait for user response
TIMEOUT_SECS = 10
CMD_IND = 0
NICK_IND = 1
UDP_PORT_IND = 2
###########################################
mutex_call = thr.Lock() # semaphore for call_flag
mutex_ans = thr.Lock() # semaphore for answer_flag
mutex_pause = thr.Lock() # semaphore for pause_flag
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

class TCPListenerSocket:
    '''
    TCPListenerSocket class
    Create the TCP Listener class in order to listen to other user
    requests, mainly, a CALLING request

    Attributes (check __init__ function):
		video_client : Instance of the caller VideoClient
        my_nickname : Name of the user who is establishing the connection
        my_udp_port : UDP port where I want to receive frames
        app_flag : Flag that indicates if the app is still running (1) or not (0)
        call_flag : Flag that indicates if we're in a call (1) or not (0)
        answer_flag : Flag that indicates if the user has given an answer to the call request
        pause_flag : Flag that indicates if the call is paused (1) or not (0)
    '''

    ################################################################
    # Constructor
    # Input:
    #   - video_client: Instance of VideoClient
    # Output:
    #   - None
    # Description:
    #   It builds an instance of TCPListenerSocket, in order to
    #   establish a call with another user
    ################################################################
    def __init__(self, video_client):
        # Storing video client
        self.video_client = video_client
        # Nickname of the logged user
        self.my_nickname = None
        # UDP port of the logged user
        self.my_udp_port = None
        # On live flag (indicates if the app keeps working)
        self.app_flag = 1
        # Calling flag (indicates this user is currently in a call)
        self.call_flag = 0
        # Answer flag
        self.answer_flag = 0
        # Pause flag to indicate the call is paused
        self.pause_flag = 0

    ################################################################
    # shutdown
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #  It just sets app_flag to zero, indicating app has finished,
    #   and closing the socket
    ################################################################
    def shutdown(self):
        self.app_flag = 0
        self._close()

    ################################################################
    # _close (private function)
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #  It just closes the socket
    ################################################################
    def _close(self):
        self.sck.close()

    ################################################################
    # request_call
    # Input:
    #   - my_nickname: name of the caller user
    #   - my_udp_port: My UDP port where I will receive frames in case
    #       the call is established
    #   - listen_ip: ip where we are receiving requests
    #   - listen_port: TCP port where we are receiving requests
    # Output:
    #   - None
    # Description:
    #   It initializes the functionality of TCPListenerSocket, listening
    #   possible users calling requests
    ################################################################
    def run(self, my_nickname, my_udp_port, listen_ip, listen_port):
        self.my_nickname = my_nickname
        self.my_udp_port = my_udp_port
        self.run_thr = thr.Thread(
            target = self._run,
            args = (listen_ip, listen_port, )
        )
        self.run_thr.start()
        return

    ################################################################
    # _run (private function)
    # Input:
    #   - listen_ip: ip where we are receiving requests
    #   - listen_port: TCP port where we are receiving requests
    # Output:
    #   - None
    # Description:
    #   It initializes the functionality of TCPListenerSocket, listening
    #   possible users calling requests. It is run by a thread
    ################################################################
    def _run(self, listen_ip, listen_port):
        # Opening socket internet/TCP
        self.sck = sck.socket(sck.AF_INET, sck.SOCK_STREAM)
        # Reusing the used address after closing
        self.sck.setsockopt(sck.SOL_SOCKET, sck.SO_REUSEADDR, 1)
        # Preparing ip and port to recieve connections
        #listen_ip = "192.168.8.100"# cambiar
        self.sck.bind((listen_ip, listen_port))
        # Maximum number of users waiting to connect
        self.listen_size = 5
        # Listening connections
        self.sck.listen(self.listen_size)
        # Runnign server
        while(self.app_flag):
            self.sck.settimeout(TIMEOUT_SECS)
            try:
                # Accepting client connection
                user_sck, user_addr = self.sck.accept()
                thread = thr.Thread(
                    target = self._handle_connection,
                    args = (user_sck, user_addr, )
                )
                thread.start()
            except sck.timeout:
                pass
            except sck.error as err:
                if self.app_flag:
                    print("Socket Error at Listener: ", err)


    ################################################################
    # _handle_connection (private function)
    # Input:
    #   - user_sck: socket where we are serving the caller user
    #   - user_addr: tuple (ip,port) of the caller user
    # Output:
    #   - None
    # Description:
    #   It handles the connection of a caller user, who is possibly
    #   trying to establish a call with us
    ################################################################
    def _handle_connection(self, user_sck, user_addr):
        printf("Establish connection from" + user_addr[0] + ":" + str(user_addr[1]))
        # Setting up timeout
        self.sck.settimeout(TIMEOUT_SECS)
        try:
            # Waiting for calls
            cmd_recv = user_sck.recv(RECV_SIZE)
        except sck.timeout:
            return
        # Command received
        cmd = cmd_recv.decode()
        if len(cmd) == 0:
            return # Empty command
        # Analyzing command
        cmd_array = cmd.split()
        if cmd_array[CMD_IND] == "CALLING": # Someone has requested to establish a call
            # Checking we are not already in a call
            ret = self._check_call_flag()
            if ret == 1:
                self._send_call_busy(user_sck)
            else:
                # We are not in a call, so we prepare GUI to accept/deny the connection
                self.video_client.pick_up_call(cmd_array[NICK_IND], user_addr[0], cmd_array[UDP_PORT_IND])
                for i in range(MAX_WAIT_SECS):
                    time.sleep(1)
                    ret = self._check_answer()
                    # If ret == 1 it means user has accepted the call
                    if ret == 1:
                        self.ans_flag_init()
                        self._handle_call_listener(user_sck)
                    # If ret == -1 it means user has denied the call
                    elif ret == -1:
                        self.ans_flag_init()
                        self._send_call_denied(user_sck)
                        return
        else:
            print("Command syntax error!")
        user_sck.close()

    ################################################################
    # _handle_call_listener (private function)
    # Input:
    #   - user_sck: socket where we are serving the caller user
    # Output:
    #   - None
    # Description:
    #   It handles the connection of a caller user, who has established
    #   a call with us
    ################################################################
    def _handle_call_listener(self, user_sck):
        cmd = "CALL_ACCEPTED "+self.my_nickname+" "+str(self.my_udp_port)
        user_sck.send(cmd.encode())
        printf("Sent CALL_ACCEPTED at listener")
        # Hiding all subwindows + showing call window
        self.video_client.set_up_call()
        self.call_flag_raise()
        current_pause_flag = self._check_pause_flag()

        while(True):
            # Checking if the user has requested to end the call
            ret_call_flag = self._check_call_flag()
            if ret_call_flag == 0:
                # Ending call
                try:
                    cmd = "CALL_END "+self.my_nickname
                    user_sck.send(cmd.encode())
                    printf("Sent CALL_END at listener")
                    return # Call is finished
                except Exception as err:
                    printf("Sending END_CALL error: ", err)
                    pass
                    return

            # Checking if pause/resume has been pressed
            ret_pause_flag = self._check_pause_flag()
            if ret_pause_flag != current_pause_flag:
                if ret_pause_flag == 1:
                    current_pause_flag = 1
                    cmd = "CALL_HOLD "+self.my_nickname
                    user_sck.send(cmd.encode())
                    printf("Sent CALL_HOLD at listener")
                elif ret_pause_flag == 0:
                    current_pause_flag = 0
                    cmd = "CALL_RESUME "+self.my_nickname
                    user_sck.send(cmd.encode())
                    printf("Sent CALL_HOLD at listener")

            # Recieving possible command
            try:
                cmd_recv = user_sck.recv(RECV_SIZE, sck.MSG_DONTWAIT)
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
                printf("Recibido CALL_END en TCP listener socket")
                # Finishing call
                self.call_flag_drop()
                # Showing main window GUI
                self.video_client.end_call()
                return

    ################################################################
    # _send_call_denied (private function)
    # Input:
    #   - user_sck: socket where we are serving the caller user
    # Output:
    #   - None
    # Description:
    #   It sends the caller user a "CALL_DENIED" response
    ################################################################
    def _send_call_denied(self, user_sck):
        cmd = "CALL_DENIED "+self.my_nickname
        user_sck.send(cmd.encode())

    ################################################################
    # _send_call_busy (private function)
    # Input:
    #   - user_sck: socket where we are serving the caller user
    # Output:
    #   - None
    # Description:
    #   It sends the caller user a "CALL_BUSY" response
    ################################################################
    def _send_call_busy(self, user_sck):
        cmd = "CALL_BUSY "+self.my_nickname
        user_sck.send(cmd.encode())

    ################################################################
    # _check_answer (private function)
    # Input:
    #   - None
    # Output:
    #   - 1 or 0 depending on answer_flag value
    # Description:
    #   It returns current answer_flag value (using semaphores!)
    ################################################################
    def _check_answer(self):
        mutex_ans.acquire()
        if self.answer_flag == 1 or self.answer_flag == -1:
            ret = self.answer_flag
        else:
            ret = 0
        mutex_ans.release()
        return ret

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
        mutex_call.acquire()
        self.call_flag = 1
        mutex_call.release()

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
        mutex_call.acquire()
        self.call_flag = 0
        mutex_call.release()

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
        mutex_call.acquire()
        if self.call_flag == 1:
            ret = 1
        else:
            ret = 0
        mutex_call.release()
        return ret

    ################################################################
    # ans_flag_deny
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It sets answer_flag = -1 (using semaphores!)
    ################################################################
    def ans_flag_deny(self):
        mutex_ans.acquire()
        self.answer_flag = -1
        mutex_ans.release()

    ################################################################
    # ans_flag_accept
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It sets answer_flag = 1 (using semaphores!)
    ################################################################
    def ans_flag_accept(self):
        mutex_ans.acquire()
        self.answer_flag = 1
        mutex_ans.release()

    ################################################################
    # ans_flag_init
    # Input:
    #   - None
    # Output:
    #   - None
    # Description:
    #   It sets answer_flag = 0 (using semaphores!)
    ################################################################
    def ans_flag_init(self):
        mutex_ans.acquire()
        self.answer_flag = 0
        mutex_ans.release()

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
