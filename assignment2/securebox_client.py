################################################################################
#   Authors:                                                                   #
#       · Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es     #
#       · David Cabornero Pascual - david.cabornero@estudiante.uam.es          #
#   Date: March 20, 2019                                                       #
#   File: securebox_client.py                                                  #
#   Project: Communication Networks II Assignment 2                            #
#   Version: 1.2                                                               #
################################################################################
import sys
from securebox_src.securebox_input_parser import *
from securebox_src.securebox_handler import *

#############################################################
# USER TOKENS
TOKEN1 = {'Authorization': 'Bearer df60AeDF78b2EBa4'}
NIA1 = "357593"
TOKEN2 = {'Authorization': 'Bearer a6A4b1eF5CDc2E38'}
NIA2 = "356974"
#############################################################
ERROR = -1

# Change this line if you want to use other tokens
TOKEN, NIA = TOKEN2, NIA2

if __name__ == "__main__":
    # Getting and checking input args
    arg_dict = parse_input_args()
    if arg_dict == ERROR:
        exit()
    # Getting SecureBox handler
    handler = SecureBoxHandler(TOKEN, NIA)
    # Switching through input parameters
    if arg_dict['create_id'] != None:
        params = arg_dict['create_id']
        handler.register(params[0], params[1])
    elif arg_dict['search_id'] != None:
        handler.search_id(arg_dict['search_id'])
    elif arg_dict['delete_id'] != None:
        handler.delete_id(arg_dict['delete_id'])
    elif arg_dict['upload'] != None:
        handler.upload(arg_dict['upload'], arg_dict['dest_id'])
    elif arg_dict['list_files'] != False:
        handler.list_files()
    elif arg_dict['delete_file'] != None:
        handler.delete_file(arg_dict['delete_file'])
    elif arg_dict['download'] != None:
        handler.download(arg_dict['download'], arg_dict['source_id'])
    elif arg_dict['encrypt'] != None:
        handler.encrypt(arg_dict['encrypt'], arg_dict['dest_id'])
    elif arg_dict['sign'] != None:
        handler.sign(arg_dict['sign'])
    elif arg_dict['enc_sign'] != None:
        handler.enc_sign(arg_dict['enc_sign'], arg_dict['dest_id'])
    else:
        print("ERROR: Unable to switch correct command")
