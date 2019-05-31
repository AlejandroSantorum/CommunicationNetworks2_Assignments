################################################################################
#   Authors:                                                                   #
#       · Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es     #
#       · David Cabornero Pascual - david.cabornero@estudiante.uam.es          #
#   Date: March 20, 2019                                                       #
#   File: securebox_handler.py                                                 #
#   Project: Communication Networks II Assignment 2                            #
#   Version: 1.2                                                               #
################################################################################
import sys
import os
import requests
from securebox_src.securebox_input_parser import *
from securebox_src.crypto_util import *
from Crypto.PublicKey import RSA

#########################################
URL = "http://vega.ii.uam.es:8080/api/"
USERS = "users/"
FILES = "files/"
UPLOAD_FOLDER = "upload/"
DOWNLOAD_FOLDER = "download/"
RSAKEYS_FOLDER = "RSAkeys/"
PUBL_KEY_NAME = "public_key"
PRIV_KEY_NAME = "private_key"
PUBL_SITE = RSAKEYS_FOLDER + PUBL_KEY_NAME
PRIV_SITE = RSAKEYS_FOLDER + PRIV_KEY_NAME
KEY_EXT = ".pem"
#########################################
OK = 200
ERROR = -1
SUCCESS = 0
#########################################

################################################################
# Class name: SecureBoxHandler
# It implements all the methods to use securebox
################################################################
class SecureBoxHandler:

    ################################################################
    # Constructor
    # Input:
    #   - token: authorization token provided by vega.ii.uam.es
    #   - nia: id student who is running the software
    # Output:
    #   - SecureBoxHandler instance
    # Description:
    #   It builds an instance of SecureBoxHandler
    ################################################################
    def __init__(self, token, nia):
        # Authorization token
        self.token = token
        # ID of the user register identity
        self.nia = nia
        # File where the private RSA key is getting saved
        self.priv_key_file = PRIV_SITE+nia+KEY_EXT
        # File where the public RSA key is getting saved
        self.publ_key_file = PUBL_SITE+nia+KEY_EXT


    ################################################################
    # _request_error
    # Input:
    #   - req: server response
    # Output:
    #   - void
    # Description:
    #   It prints the error message of the server response.
    #   Privated class method
    ################################################################
    def _request_error(self, req):
        try:
            error = req.json().get("error_code")
            desc = req.json().get("description")
            print("\nError " + error + ": " + desc)
        except JSONDecodeError:
            # It is not a server's controlled error. Printing just the HTML msg
            print("Advertencia, este no es un error comun:")
            print(req.text)


    ################################################################
    # _get_public_key
    # Input:
    #   - id: user ID of the desired public key
    # Output:
    #   - The public key of the user with ID id, or -1 in error case
    # Description:
    #   It sends a request to the server asking for the publicKey
    #   of a given user ID
    #   Privated class method
    ################################################################
    def _get_public_key(self, id):
        TEMP_F = "temp.pem"
        args = {"userID": id}
        sys.stdout.write("Recuperando clave pública de ID " + str(id) + "...")
        # Sending HTTP request to the server
        req = requests.post(URL+USERS+"getPublicKey", headers=self.token, json=args)
        if(req.status_code == OK):
            f = open(TEMP_F, "wb")
            f.write(req.json().get("publicKey").encode())
            f.close()
            publ_key = RSA.import_key(open(TEMP_F).read())
            print("OK")
            os.remove(TEMP_F)
            return publ_key
        else:
            self._request_error(req)
            return ERROR


    ################################################################
    # _equal_user
    # Input:
    #   - name: user name
    #   - email: user email
    #   - publ_key: user public key
    #   - search_user: user found in the server with the same email
    # Output:
    #   - True if users are equal, False otherwise
    # Description:
    #   It checks if two users are apparently equal
    #   Privated class method
    ################################################################
    def _equal_user(self, name, email, publ_key, search_user):
        if name != search_user.get("nombre"):
            print("Nombre no igual")
            return False
        elif email != search_user.get("email"):
            print("email no igual")
            return False
        elif publ_key.decode() != search_user.get("publicKey"):
            return False
        return True


    ################################################################
    # register
    # Input:
    #   - name: user name
    #   - email: user email
    # Output:
    #   - void
    # Description:
    #   It sends a registration request to the server, in order
    #   to register a new user
    ################################################################
    def register(self, name, email):
        # Getting RSA keys
        sys.stdout.write("Generando par de claves RSA de 2048 bits...")
        try:
            priv_key, publ_key = generate_RSA_keys(self.priv_key_file, self.publ_key_file)
            print("OK")
        except:
            print("ERROR")
            print("No se han podido generar las claves RSA")

        args = {"nombre": name, "email": email, "publicKey": publ_key.decode()}
        # Sending HTTP request to the server
        req = requests.post(URL+USERS+"register", headers=self.token, json=args)
        # Handling server respose
        if(req.status_code == OK):
            req = self.search_id(email, 1)
            for user in req.json():
                if self._equal_user(name, email, publ_key, user) == True:
                    print("Identidad con ID#"+user.get("userID")+" creada correctamente")
                    return
            print("ERROR: No se ha podido registrar la identidad ["+name+", "+email+"]")
        else:
            print("ERROR: No se ha podido registrar la identidad ["+name+", "+email+"]")


    ################################################################
    # search_id
    # Input:
    #   - search-str: string to search in the user name or email
    #   - return_flag (optional): flag that indicates this method
    #       is called from register method as an auxiliary method
    # Output:
    #   - void
    # Description:
    #   It sends a request to the server to check if certain
    #   string is found in any user name or email
    ################################################################
    def search_id(self, search_str, return_flag=0):
        args = {"data_search": search_str}
        if return_flag == 0:
            sys.stdout.write("Buscando usuario \'"+ search_str +"\' en el servidor...")
        # Sending HTTP request to the server
        req = requests.post(URL+USERS+"search", headers=self.token, json=args)
        # Handling server respose
        if(req.status_code == OK):
            if return_flag:
                return req
            print("OK")
            print(str(len(req.json())) + " usuarios encontrados:")
            # Printing each user information
            for success in req.json():
                num = str(req.json().index(success) + 1)
                name = str(success.get("nombre"))
                email = str(success.get("email"))
                id = str(success.get("userID"))
                print("[" + num + "] " + name + ", " + email + ", ID: " + id)
        else:
            self._request_error(req)


    ################################################################
    # delete_id
    # Input:
    #   - id: user ID
    # Output:
    #   - void
    # Description:
    #   It sends a request to the server in order to delete an
    #   user with the given ID
    ################################################################
    def delete_id(self, id):
        args = {"userID": id}
        sys.stdout.write("Solicitando borrado de la identidad #" + str(id) + "...")
        # Sending HTTP request to the server
        req = requests.post(URL+USERS+"delete", headers=self.token, json=args)
        # Handling server respose
        if(req.status_code == OK):
            userID = str(req.json().get("userID"))
            print("OK")
            print("Identidad con ID#" + userID +" borrada correctamente")
            try:
                os.remove(PRIV_SITE+id+KEY_EXT)
                os.remove(PUBL_SITE+id+KEY_EXT)
            except OSError as err:
                print("Advertencia: no se han podido eliminar las claves RSA: "+str(err))
        else:
            self._request_error(req)


    ################################################################
    # upload
    # Input:
    #   - filename: file to upload to the server
    #   - dest_id: user ID of the receiver
    # Output:
    #   - -1 in error case, void otherwise
    # Description:
    #   It sends a request to the server in order to upload
    #   a given file
    ################################################################
    def upload(self, filename, dest_id):
        print("Solicitado envio de ficheros a Securebox")
        # Signing and ciphering
        try:
            # All uploaded files must be placed in UPLOAD_FOLDER
            filepath = UPLOAD_FOLDER+filename
            new_filepath = self.enc_sign(filepath, dest_id)
        except Exception as err:
            print("ERROR: No se ha podido fimar/cifrar el fichero: " + str(err))
        # Getting encrypted file
        files = {'ufile': (filename, open(new_filepath, 'rb'))}
        # Sending HTTP request to the server
        req = requests.post(URL+FILES+"upload", headers=self.token, files=files)
        # Handling server respose
        if(req.status_code == OK):
            file_ID = str(req.json().get("file_id"))
            file_size = str(req.json().get("file_size"))
            print("Subida realizada correctamente, ID del fichero: " + file_ID)
        else:
            self._request_error(req)


    ################################################################
    # _decrypt
    # Input:
    #   - binary_file: downloaded binary data
    #   - source_id: user id who uploaded the file
    # Output:
    #   - the deciphered message on success, or -1 in error case
    # Description:
    #   It separates the first 256 bytes (ciphered symm. key) from
    #   the rest of the binary text. Then it decrypts the symm. key
    #   that had been encrypted using RSA2048. Once we have the symm.
    #   key deciphered, we can decrypt the message that had been encrypted
    #   using AES256 with CBC mode. At the end, we separate the digital
    #   sign from the rest of the text, and we check the correctness of
    #   the sign, returning the decrypted message on success, -1 in error
    #   Privated class method
    ################################################################
    def _decrypt(self, binary_file, source_id):
        RSA_KEY_SIZE = 256
        IV_SIZE = 16
        # Breaking up the digital envelope
        iv = binary_file[:IV_SIZE]
        cipher_symm_key = binary_file[IV_SIZE:IV_SIZE+RSA_KEY_SIZE]
        cipher_msg = binary_file[RSA_KEY_SIZE+IV_SIZE:]
        cipher_msg = iv+cipher_msg
        # Decrypting symmetric key using RSA2048
        sys.stdout.write("-> Descifrando fichero...")
        try:
            symm_key = decrypt_RSA2048(cipher_symm_key, self.priv_key_file)
            # Decrypting message using AES256
            msg, signature = decrypt_AES256_CBC(cipher_msg, symm_key, sign_flag=1)
            print("OK")
            # Getting sender public key
            sender_publ_key = self._get_public_key(source_id)
        except:
            print("ERROR")
            print("No se ha podido descrifrar el fichero")
            return ERROR
        # Checking signature
        sys.stdout.write("-> Verificando firma...")
        if verify_signature(msg, signature, sender_publ_key) == True:
            print("OK")
            return msg
        else:
            print("Error")
            print("Firma falsa")
            return ERROR

    ################################################################
    # download
    # Input:
    #   - file_ID: ID of the file that is going to be downloaded
    #   - source_ID: ID of the user who sent the file
    # Output:
    #   - name of the downloaded file
    # Description:
    #   It downloads a file sent by a certain user,uncrypts it and checks
    #   the sign
    ################################################################
    def download(self, file_id, source_id):
        # Auxiliary string to get filename later
        FILE_STR = "filename=\""
        # Request arguments
        args = {"file_id": file_id}
        sys.stdout.write("Descargando fichero de SecureBox...")

        req = requests.post(URL+FILES+"download", headers=self.token, json=args)
        if(req.status_code == OK):
            print("OK")
            binary_crypt = req.content
            size_file = sys.getsizeof(binary_crypt)
            print("-> "+str(size_file) + " bytes descargados correctamente")
            # Decrypting the file
            msg = self._decrypt(binary_crypt, source_id)
            if msg == ERROR:
                return
            # Writing file
            disposition = req.headers['Content-Disposition']
            index = disposition.find(FILE_STR)
            index2 = disposition.find("\"", index+len(FILE_STR))
            filename = disposition[index+len(FILE_STR) : index2]
            filepath = DOWNLOAD_FOLDER+filename
            f = open(filepath, "wb")
            f.write(msg)
            f.close()
        else:
            self._request_error(req)


    ################################################################
    # list_files
    # Input:
    #   - void
    # Output:
    #   - void
    # Description:
    #   It prints on screen the ID's of the files of the actual user
    ################################################################
    def list_files(self):
        sys.stdout.write("Solicitando listado de ficheros...")
        try:
            # Sending HTTP request to the server
            req = requests.post(URL+FILES+"list", headers=self.token)
            # Handling server respose
            nfiles = req.json().get("num_files")
            files_list = req.json().get("files_list")
            print("OK")
            if nfiles == 0:
                print("El usuario actual no tiene ningún fichero")
            else:
                for i in range(nfiles):
                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    print("["+str(i+1)+"] - " + str(files_list[i]))
                    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        except:
            print("ERROR")
            print("No se ha podido obtener el listado de ficheros")


    ################################################################
    # delete_file
    # Input:
    #   - id: ID of file which is going to be deleted
    # Output:
    #   - void
    # Description:
    #   It deletes a certain file knowing its ID. You only can delete it
    #   if you created it.
    ################################################################
    def delete_file(self, id):
        args = {"file_id": id}
        sys.stdout.write("Solicitando borrado del fichero #" + str(id) + "...")
        # Sending HTTP request to the server
        req = requests.post(URL+FILES+"delete", headers=self.token, json=args)
        # Handling server respose
        if(req.status_code == OK):
            file_id = str(req.json().get("file_id"))
            print("OK")
            print("Fichero con ID#" + file_id +" borrado correctamente")
        else:
            self._request_error(req)


    ################################################################
    # enc_sign
    # Input:
    #   - filepath: path of the file which is going to be encrypted
    #   - dest_id: id of the user whose public key is used to encrypt the file
    #   - digital_sign (optional): sign of the file (if the file isn't signed, None)
    #   - new_file_flag (optional): prints on screen the name of the enrypted file
    # Output:
    #   - Name of the new encrypted file, or -1 in error case
    # Description:
    #   It encrypts a file with a certain user's public key
    #   Raises ValueError or IOError in error case
    ################################################################
    def encrypt(self, filepath, dest_id, digital_sign=None, new_file_flag=1):
        # Getting receiver public key
        recv_publ_key = self._get_public_key(dest_id)
        sys.stdout.write("Cifrando fichero...")
        # Opening file at given path
        try:
            f = open(filepath, "rb")
            message = f.read()
            f.close()
            # Getting name
            name = filepath[:filepath.find(".")]
        except:
            raise IOError("ERROR: Unable to open file at given path")
        # Ciphering
        try:
            if digital_sign != None:
                ciphermsg, iv, symm_key = encrypt_AES256_CBC(message, digital_sign)
            else:
                ciphermsg, iv, symm_key = encrypt_AES256_CBC(message)
            cipherkey = encrypt_RSA2048(symm_key, recv_publ_key)
        except:
            print("ERROR")
            print("No se ha podido cifrar el fichero")
            raise ValueError("ERROR: Unable to cipher the file")
        # Saving it into a new file
        try:
            new_filename = name+str(dest_id)+".bin"
            f = open(new_filename, "wb")
            # cipher_data is the digital envelope, ciphered symm_key + ciphered_message
            cipher_data = iv+cipherkey+ciphermsg
            f.write(cipher_data)
            f.close()
            print("OK")
            if new_file_flag:
                print("El fichero cifrado se puede encontrar en este directorio con el nombre \'"+new_filename+"\'")
            return new_filename
        except:
            print("ERROR")
            print("No se ha podido guardar el texto cifrado en un archivo nuevo")
            raise ValueError("ERROR: Unable to save the ciphered text in a file")


    ################################################################
    # sign
    # Input:
    #   - filepath: path of the file that is going to be signed
    # Output:
    #   - name of the signed file
    # Description:
    #   It signs a certain file
    ################################################################
    def sign(self, filepath):
        sys.stdout.write("Firmando fichero...")
        # Opening file at given path
        try:
            f = open(filepath, "rb")
            message = f.read()
            f.close()
        except:
            raise IOError("ERROR: Unable to open file at given path")
            return ERROR
        # Signing
        try:
            signature = digital_sign(message, self.priv_key_file)
            print("OK")
            return signature
        except:
            print("ERROR")
            print("No se ha podido firmar el fichero")
            return ERROR


    ################################################################
    # enc_sign
    # Input:
    #   - filepath: path of the file which is going to be encrypted and signed
    #   - dest_id: the id of the user whose public key is going to be used
    #              to encrypt the file
    # Output:
    #   - Name of the new file (encrypted and signed)
    # Description:
    #   It encrypts and signs a file with a public key of a certain user
    ################################################################
    def enc_sign(self, filepath, dest_id):
        signature = self.sign(filepath)
        if signature == ERROR:
            return ERROR
        try:
            new_filename = self.encrypt(filepath, dest_id, signature, new_file_flag=0)
        except:
            return ERROR
        return new_filename


# Testing module
if __name__ == "__main__":
    TOKEN1 = {'Authorization': 'Bearer df60AeDF78b2EBa4'}
    NIA1 = "357593"
    TOKEN2 = {'Authorization': 'Bearer a6A4b1eF5CDc2E38'}
    NIA2 = "356974"

    TOKEN, NIA = TOKEN1, NIA1

    file_to_upload = "securebox_handler.py"

    handler = SecureBoxHandler(TOKEN, NIA)
    handler.register("Eduardo Serrano", "eduardo_serrano@uamuni.es")
    print("===========================================================")
    handler.search_id("Pedro")
    print("===========================================================")
    handler.list_files()
    print("===========================================================")
    #handler.delete_id(NIA)
    print("===========================================================")
    handler.upload(file_to_upload, NIA2)
