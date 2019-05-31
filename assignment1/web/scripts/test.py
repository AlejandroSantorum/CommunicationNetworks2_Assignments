import sys
import os
import signal
import time

# Global useful variables
TIMEOUT = 1 # seconds
html_part1 = "<doctype html><html><head><meta charset=\"UTF-8\"></head><body>"
html_part2 = "</body></html>"
FILENAME = "/post_response.html" # Easier to open it on root_server file

def _get_params(str):
    # Separating into the real good parameters
    inter = str.find("=")
    str = str[inter+1:]
    array = str.split("+")
    return array

def _do_work(elem):
    # Doing some work with the parameters
    return elem.swapcase()

def _argv_response():
    aux = "<b><p>Trabajo realizado con los parametros de ARGV:</p></b>"
    if len(sys.argv) < 2:
        return aux
    # Getting input parameter
    argv_str = sys.argv[1]
    #Getting good parameters
    array = _get_params(argv_str)
    # Doing some work
    aux += "<p style=\"color:#0404B4\";>"
    for elem in array:
        aux += _do_work(elem) + " "
    aux += ", a las : "+time.strftime("%c")
    aux += "</p>"
    return aux

def _stdin_response():
    aux_flag = 0
    aux = "<b><p>Trabajo realizado con los parametros de STDIN:</p></b>"
    try:
        aux += "<p style=\"color:#FF0000\";>"
        for line in sys.stdin:
            aux_flag = 1
            array = _get_params(line)
            for elem in array:
                aux += _do_work(elem) + " "
        if aux_flag:
            aux += ", a las : "+time.strftime("%c")
        aux += "</p>"
        return aux
    except:
        return ""

signal.signal(signal.SIGALRM, input)
signal.alarm(TIMEOUT)

argv_work = _argv_response()
html_part1 += argv_work

stdin_work = _stdin_response()
html_part1 += stdin_work
html_str = html_part1 + html_part2

# Writing response html file
file = open(os.path.dirname(__file__) + "/.." + FILENAME, "wb")
file.write(html_str.encode())
file.close()

sys.stdout.write(FILENAME)
