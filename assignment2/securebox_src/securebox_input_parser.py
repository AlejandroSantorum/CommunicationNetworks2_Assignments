################################################################################
#   Authors:                                                                   #
#       · Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es     #
#       · David Cabornero Pascual - david.cabornero@estudiante.uam.es          #
#   Date: March 20, 2019                                                       #
#   File: securebox_input_parser.py                                            #
#   Project: Communication Networks II Assignment 2                            #
#   Version: 1.2                                                               #
################################################################################
import argparse
import sys

# Global macros
ERROR = -1
SUCCESS = 0
# Turning on (1) or turning off (0) stdout debugging
DEBUGGING_FLAG = 1


################################################################
# _arg_parser
# Input:
#   - void
# Output:
#   - parser object with the arguments parsed
# Description:
#   It uses argparse library in order to get parsed input arguments
#   Privated module method
################################################################
def _arg_parser():
    parser = argparse.ArgumentParser(description='SecureBox client.')

    # User management
    parser.add_argument("--create_id", nargs = "*")
    parser.add_argument("--search_id", type = str)
    parser.add_argument("--delete_id", type = str)

    # Upload and download files
    parser.add_argument("--upload", type = str)
    parser.add_argument("--source_id", type = str)
    parser.add_argument("--dest_id", type = str)
    parser.add_argument("--list_files", action = "store_true")
    parser.add_argument("--download", type = str)
    parser.add_argument("--delete_file", type = str)

    # Encrypt and sign files
    parser.add_argument("--encrypt", type = str)
    parser.add_argument("--sign", type = str)
    parser.add_argument("--enc_sign", type = str)

    return parser.parse_args()


################################################################
# _check_uniqueness
# Input:
#   - argv: contents a certain argument introduced by the user
# Output:
#   - SUCCESS if the user introduced a correct combination of arguments
#   - ERROR if the user didn't introduce a correct combination of arguments
# Description:
#   It checks there aren't two or more incompatible input arguments
#   Privated module method
################################################################
def _check_uniqueness(arg_dict, *argv):
    keys = arg_dict
    for key in keys:
        if (key not in argv) and (arg_dict[key] != None and arg_dict[key] != False):
            if DEBUGGING_FLAG:
                print("ERROR: Two or more incompatible arguments were introduced")
            return ERROR
    return SUCCESS


################################################################
# _check_create_id
# Input:
#   - arg_dict: set of commands introduced by the user
# Output:
#   - SUCCESS if the user introduced 2 arguments in --create_id and the user
#       didn't introduce more commands
#   - ERROR in any another case
# Description:
#   It checks the correctness of the --create_id command
#   Privated module method
################################################################
def _check_create_id(arg_dict):
    # Checking uniqueness of the argument
    if _check_uniqueness(arg_dict, "create_id") == ERROR:
        return ERROR
    # Checking correct number of parameters
    nargs = len(arg_dict['create_id'])
    if nargs < 2 or nargs > 3:
        if DEBUGGING_FLAG:
            print("ERROR: create_id command must fit this format: --create_id name email [nickname]")
        return ERROR
    return SUCCESS


################################################################
# _check_search_id
# Input:
#   - arg_dict: set of commands introduced by the user
# Output:
#   - SUCCESS if the user didn't introduce more commands
#   - ERROR in any another case
# Description:
#   It checks the correctness of the --search_id command
#   Privated module method
################################################################
def _check_search_id(arg_dict):
    # Checking uniqueness of the argument
    if _check_uniqueness(arg_dict, "search_id") == ERROR:
        return ERROR
    return SUCCESS


################################################################
# _check_delete_id
# Input:
#   - arg_dict: set of commands introduced by the user
# Output:
#   - SUCCESS if the user didn't introduce more commands
#   - ERROR in any another case
# Description:
#   It checks the correctness of the --delete_id command
#   Privated module method
################################################################
def _check_delete_id(arg_dict):
    # Checking uniqueness of the argument
    if _check_uniqueness(arg_dict, "delete_id") == ERROR:
        return ERROR
    return SUCCESS


################################################################
# _check_upload
# Input:
#   - arg_dict: set of commands introduced by the user
# Output:
#   - SUCCESS if the user only introduced upload and dest_id commands
#   - ERROR in any another case
# Description:
#   It checks the correctness of the --upload command
#   Privated module method
################################################################
def _check_upload(arg_dict):
    # Checking uniqueness of the argument
    if _check_uniqueness(arg_dict, "upload", "dest_id") == ERROR:
        return ERROR
    # Checking --dest_id was introduced
    if arg_dict['dest_id'] == None:
        if DEBUGGING_FLAG:
            print("ERROR: When uploading a file, dest_id is required")
        return ERROR
    return SUCCESS


################################################################
# _check_list_files
# Input:
#   - arg_dict: set of commands introduced by the user
# Output:
#   - SUCCESS if the user didn't introduce more commands
#   - ERROR in any another case
# Description:
#   It checks the correctness of the --list_files command
#   Privated module method
################################################################
def _check_list_files(arg_dict):
    # Checking uniqueness of the argument
    if _check_uniqueness(arg_dict, "list_files") == ERROR:
        return ERROR
    return SUCCESS

################################################################
# _check_download_files
# Input:
#   - arg_dict: set of commands introduced by the user
# Output:
#   - SUCCESS if the user only introduced download and source_id commands
#   - ERROR in any another case
# Description:
#   It checks the correctness of the --download command
#   Privated module method
################################################################
def _check_download(arg_dict):
    # Checking uniqueness of the argument
    if _check_uniqueness(arg_dict, "download", "source_id") == ERROR:
        return ERROR
    # Checking --source_id was introduced
    if arg_dict['source_id'] == None:
        if DEBUGGING_FLAG:
            print("ERROR: When downloading a file, source_id is required")
        return ERROR
    return SUCCESS


################################################################
# _check_delete_file
# Input:
#   - arg_dict: set of commands introduced by the user
# Output:
#   - SUCCESS if the user didn't introduce more commands
#   - ERROR in any another case
# Description:
#   It checks the correctness of the --delete_file command
#   Privated module method
################################################################
def _check_delete_file(arg_dict):
    # Checking uniqueness of the argument
    if _check_uniqueness(arg_dict, "delete_file") == ERROR:
        return ERROR
    return SUCCESS


################################################################
# _check_encrypt
# Input:
#   - arg_dict: set of commands introduced by the user
# Output:
#   - SUCCESS if the user didn't introduce more commands
#   - ERROR in any another case
# Description:
#   It checks the correctness of the --encrypt command
#   Privated module method
################################################################
def _check_encrypt(arg_dict):
    # Checking uniqueness of the argument
    if _check_uniqueness(arg_dict, "encrypt", "dest_id") == ERROR:
        return ERROR
    # Checking --dest_id was introduced
    if arg_dict['dest_id'] == None:
        if DEBUGGING_FLAG:
            print("ERROR: When encrypting a file, dest_id is required")
        return ERROR
    return SUCCESS


################################################################
# _check_sign
# Input:
#   - arg_dict: set of commands introduced by the user
# Output:
#   - SUCCESS if the user didn't introduce more commands
#   - ERROR in any another case
# Description:
#   It checks the correctness of the --sign command
#   Privated module method
################################################################
def _check_sign(arg_dict):
    # Checking uniqueness of the argument
    if _check_uniqueness(arg_dict, "sign") == ERROR:
        return ERROR
    return SUCCESS


################################################################
# _check_enc_sign
# Input:
#   - arg_dict: set of commands introduced by the user
# Output:
#   - SUCCESS if the user didn't introduce more commands
#   - ERROR in any another case
# Description:
#   It checks the correctness of the --enc_sign command
#   Privated module method
################################################################
def _check_enc_sign(arg_dict):
    # Checking uniqueness of the argument
    if _check_uniqueness(arg_dict, "enc_sign", "dest_id") == ERROR:
        return ERROR
    # Checking --dest_id was introduced
    if arg_dict['dest_id'] == None:
        if DEBUGGING_FLAG:
            print("ERROR: When encrypting and signing a file, dest_id is required")
        return ERROR
    return SUCCESS


################################################################
# _check_args
# Input:
#   - arg_dict: set of commands introduced by the user
# Output:
#   - SUCCESS if the user introduced a correct combination of commands
#       and arguments of the commands
#   - ERROR in any another case
# Description:
#   It checks the correctness of the arguments introduced
#   Privated module method
################################################################
def _check_args(arg_dict):
    if arg_dict['create_id'] != None:
        return _check_create_id(arg_dict)
    if arg_dict['search_id'] != None:
        return _check_search_id(arg_dict)
    if arg_dict['delete_id'] != None:
        return _check_delete_id(arg_dict)
    if arg_dict['upload'] != None:
        return _check_upload(arg_dict)
    if arg_dict['list_files'] != False:
        return _check_list_files(arg_dict)
    if arg_dict['download'] != None:
        return _check_download(arg_dict)
    if arg_dict['delete_file'] != None:
        return _check_delete_file(arg_dict)
    if arg_dict['encrypt'] != None:
        return _check_encrypt(arg_dict)
    if arg_dict['sign'] != None:
        return _check_sign(arg_dict)
    if arg_dict['enc_sign'] != None:
        return _check_enc_sign(arg_dict)
    if DEBUGGING_FLAG:
        if arg_dict['dest_id'] != None or arg_dict['source_id'] != None:
            print("ERROR: Required another command apart from --dest_id and/or --source_id")
        else:
            print("ERROR: None input arguments")
    return ERROR


################################################################
# parse_input_args
# Input:
#   - debugging: global flag used to debug the program
# Output:
#   - SUCCESS the arguments are right
#   - ERROR in any another case
# Description:
#   It parses input arguments, calling auxiliary functions of this file
################################################################
def parse_input_args(debugging=1):
    # Configurating stdout debugging
    global DEBUGGING_FLAG
    DEBUGGING_FLAG = debugging
    # Getting input args with argparse library
    namespace_struct = _arg_parser()
    # Transforming it into a dictionary to access data easily
    arg_dict = vars(namespace_struct)
    # Checking correct format
    ret = _check_args(arg_dict)
    if ret == ERROR:
        return ERROR
    else:
        return arg_dict


# Testing this module
if __name__ == "__main__":
    print(parse_input_args(debugging=1))
