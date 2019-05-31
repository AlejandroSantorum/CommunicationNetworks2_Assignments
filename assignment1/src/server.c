/******************************************************************************/
/*  PROJECT: Assignment 1 - Communication Networks II                         */
/*  FILE: server.c                                                            */
/*  AUTHORS:                                                                  */
/*      Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es      */
/*      David Cabornero Pascual - david.cabornero@estudiante.uam.es           */
/*  DATE: March 4, 2019                                                       */
/*  VERSION: 1.8                                                              */
/*                                                                            */
/*  DESCRIPTION: Implementation of web server functions                       */
/******************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <resolv.h>
#include <arpa/inet.h>
#include <errno.h>
#include <unistd.h>
#include <syslog.h>
#include <sys/stat.h>
#include <pthread.h>
#include <signal.h>
#include <semaphore.h>
#include <time.h>
#include <fcntl.h>
#include <sys/sendfile.h>
#include "server.h"
#include "util.h"
#include "picohttpparser.h"

#define SERVER_CONF_F "/server.conf" /* Server configuration file name */
#define INDEX_PATH "/index.html" /* Index file name */
#define POST_BODY_F "body.txt"  /* Auxiliary file name where the scripts' input will be stored */
#define ANY_ADDR "0.0.0.0"
#define GET_CHECK_SCRIPT "/scripts/"
#define PYTHON_SCRIPT "python3 " /* Executing python3 script */
#define PHP_SCRIPT "php " /* Executing PHP script */
#define INCOMPLETE_REQUEST -2 /* Constant returned by picohttpparser when a request is incompleted */
#define BUFFER_LEN 4096 /* Max buffer size */
#define LEN 128 /* Max size of different auxiliary buffers */
#define MAX_HEADERS 64 /* Max headers size */
#define METH_LEN 16 /* Max method length */
#define PATH_LEN 64 /* Max path length */
#define INDEX "/" /* Index auxiliary name in HTTP requests */
#define N_SRV_CFG_PAR 6 /* Namber of parameters in server configuration file */
#define SERVER_ROOT 0 /* Location of media files */
#define MAX_CLIENTS 1 /* Maximum number of clients that the server can handle simultaneosly */
#define LISTEN_PORT 2 /* Port where server is listening waiting for clients */
#define SERVER_SIGNATURE 3 /* Server name */
#define MAX_LISTEN_QUEUE 4 /* Maximum number of clients queued waiting to be connected to the server */
#define NTHR_POOL 5 /* Size of pool of threads */

#define ERROR_404_MSG "404 Not Found"
#define ERROR_400_MSG "400 Bad Request"
#define ERROR_501_MSG "501 Not Implemented"

/* Auxiliary structure to link extensions to content-types */
struct{
    char *ext;
    char *filetype;
}extensions[] = {
    {".txt", "text/plain"},
    {".htm", "text/html"},
    {".html", "text/html"},
    {".gif", "image/gif"},
    {".jpg", "image/jpeg"},
    {".jpeg", "image/jpeg"},
    {".mpeg", "video/mpeg"},
    {".mpg", "video/mpeg"},
    {".doc", "application/msword"},
    {".docx", "application/msword"},
    {".pdf", "application/pdf"},
    {0, 0}
};

struct optc options[N_SRV_CFG_PAR]; /* Server configuration global variable */

int listenfd_aux; /* Server socket file descriptor */
int kill_flag=0; /* Flag that indicates the server has been asked to close with ctrl+c */
int server_pid; /* Server PID */
pthread_t *thr; /* Thread pool array */
int nthreads; /* Total number of created threads */
int nclients; /* Total number of clients processed/being processed */
int nbusy_thr=0; /* Number of threads that are processing a client */
sem_t var_mutex; /* Semaphore for variables */
sem_t accept_mutex; /* Semaphore for accepting clients */
char working_dir[LEN] = ".";

/* Signal handlers */
void handler_SIGUSR1(int sig){
    return;
}
void handler_SIGINT(int sig){
    int i;
    info_message("Server shutdown request");
    kill_flag=1;
    /* Killing all threads */
    for(i=0; i<nthreads; i++){
        pthread_kill(thr[i], SIGKILL);
    }
    close(listenfd_aux);
    return;
}

/* ================== AUXILIARY & PRIVATE FUNCTIONS ====================== */
/* Given a path, it returns the content-type in response buffer */
int _get_content_type(char *path, char *response);
/* It builds and sends an error header (400, 404, 501) */
void _send_error(int clientfd, int minor_version, char *error_msg);
/* It checks if one header is connection: Keep-alive in order to control persistency */
int _check_keep_alive(struct phr_header *headers, size_t num_headers);
/* ======================================================================= */


/******************************************************************************/
/*  FUNCTION: int server_conf()                                               */
/*  INPUT ARGS:                                                               */
/*      None                                                                  */
/*  RETURN: int - 0 on sucess and negative integer on error case              */
/*  DESCRIPTION: It prepares the configuration of the server, given and       */
/*      specified in the file server.conf, allocated in the same folder       */
/*      than this source                                                      */
/******************************************************************************/
int server_config(){
    char path[LEN];

    strcpy(options[SERVER_ROOT].key, "server_root"); /* Location of media files */
    strcpy(options[MAX_CLIENTS].key, "max_clients"); /* Maximum number of clients that the server can handle simultaneosly */
    strcpy(options[LISTEN_PORT].key, "listen_port"); /* Port where server is listening waiting for clients */
    strcpy(options[SERVER_SIGNATURE].key, "server_signature"); /* Server name */
    strcpy(options[MAX_LISTEN_QUEUE].key, "max_listen_queue"); /* Maximum number of clients queued waiting to be connected to the server */
    strcpy(options[NTHR_POOL].key, "thread_pool"); /* Size of pool of threads */

    strcpy(path, working_dir);
    strcat(path, SERVER_CONF_F);
    return my_confuse(path, options, N_SRV_CFG_PAR);
}

/******************************************************************************/
/*  FUNCTION: int tcp_listen(char *serv_addr, int serv_port, int max_queue)   */
/*  INPUT ARGS:                                                               */
/*      char *serv_addr - address where the server is going to be binded      */
/*      int serv_port - port where the server os going to be binded           */
/*      int max_queue - maximum number of clients waiting to connect          */
/*  RETURN: int - 0 on sucess and negative integer on error case              */
/*  DESCRIPTION: It prepares all the server configuration introduced by       */
/*      the user and starts the server                                        */
/******************************************************************************/
int tcp_listen(char *serv_addr, int serv_port, int max_queue){
    int listenfd;
    struct sockaddr_in serv;

    /* Input parameter checking */
    if(serv_port <= 0){
        error_message("ERROR: Invalid server port to listen", __FILE__, __LINE__);
        return ERROR;
    }
    if(max_queue <= 0){
        error_message("ERROR: Invalid listening queue size", __FILE__, __LINE__);
        return ERROR;
    }
    /* Preparing socket struct parameter */
    bzero(&serv, sizeof(serv));
    if(!strcmp(ANY_ADDR, serv_addr) || !strcmp("ANY", serv_addr)){
        info_message("Any server address has been selected");
        serv.sin_addr.s_addr = INADDR_ANY;
    }
    else if(inet_pton(AF_INET, serv_addr, &serv.sin_addr.s_addr) != 1){
        error_message("ERROR: Invalid server address", __FILE__, __LINE__);
        return ERROR;
    }
    serv.sin_family = AF_INET;
    serv.sin_port = htons(serv_port);
    /* Creating the TCP socket */
    if((listenfd = socket(AF_INET, SOCK_STREAM, 0)) == ERROR){
        error_message("ERROR: Unable to OPEN the server socket", __FILE__, __LINE__);
        return ERROR;
    }
    info_message("Server socket opened successfully");
    /* Setting the socket to be reused immediately */
    int aux_int_value = 1;
    if(setsockopt(listenfd, SOL_SOCKET, SO_REUSEADDR, &aux_int_value, sizeof(int)) < 0){
        error_message("ERROR: Unable to set REUSEADDR server socket", __FILE__, __LINE__);
        return ERROR;
    }
    /* Binding the port to the socket */
    if(bind(listenfd, (struct sockaddr*)&serv, sizeof(serv)) != SUCCESS){
        error_message("ERROR: Unable to BIND the server socket", __FILE__, __LINE__);
        close(listenfd);
        return ERROR;
    }
    printf("Server socket binded successfully\n");
    /* Ready to listen, with a maximum confirmation queue of max_queue clients */
    if(listen(listenfd, max_queue) != SUCCESS){
        error_message("ERROR: Unable to LISTEN in this socket", __FILE__, __LINE__);
        close(listenfd);
        return ERROR;
    }
    info_message("Server is listening!");
    return listenfd;
}

/******************************************************************************/
/*  FUNCTION: int server_init(char *serv_addr, char *work_dir)                */
/*  INPUT ARGS:                                                               */
/*      char *serv_addr - address where the server is going to be binded      */
/*      char *work_dir - current working directory before calling daemonize   */
/*  RETURN: int - 0 on sucess and negative integer on error case              */
/*  DESCRIPTION: It prepares all the server configuration introduced by       */
/*      the user and starts the server                                        */
/******************************************************************************/
int server_init(char *serv_addr, char *work_dir){
    int listenfd;

    if(!serv_addr){
        error_message("ERROR: serv_address is NULL\n", __FILE__, __LINE__);
        return ERROR;
    }
    /* Setting up server working directory */
    if(work_dir){
        strcpy(working_dir, work_dir);
    }
    /* Preparing and setting up server configuration */
    if(server_config() == ERROR){
        error_message("ERROR: Unable to set up server configuration", __FILE__, __LINE__);
        return ERROR;
    }
    /* socket + bind + listen */
    if((listenfd = tcp_listen(serv_addr, atoi(options[LISTEN_PORT].value), atoi(options[MAX_LISTEN_QUEUE].value))) == ERROR){
        error_message("ERROR: tcp_listen has failed", __FILE__, __LINE__);
        return ERROR;
    }
    info_message("Server initialized successfully");
    /* It may be helpful later */
    server_pid = getpid();
    /* Running server */
    server_run(listenfd);
    close(listenfd);
    return SUCCESS;
}

/******************************************************************************/
/*  FUNCTION: int server_run(int listenfd, int nthr_pool)                     */
/*  INPUT ARGS:                                                               */
/*      int listenfd - file descriptor returned by socket function            */
/*  RETURN: int - 0 on sucess and negative integer on error case              */
/*  DESCRIPTION: Main function of the server, where the initial pool of       */
/*      threads is initialized and where a new pool of threads is created     */
/*      as soon as all the created threads are working                        */
/******************************************************************************/
int server_run(int listenfd){
    int i;
    int nthr_pool = atoi(options[NTHR_POOL].value);
    int max_clients = atoi(options[MAX_CLIENTS].value);
    /* Defining new signal handler for SIGUSR1: It is raised when the pool of threads is full */
    if(signal(SIGUSR1, handler_SIGUSR1) == SIG_ERR){
        error_message("ERROR: Unable to set up the new signal USR1 handler in the server", __FILE__, __LINE__);
        return ERROR;
    }
    /* Defining new signal handler for SIGINT: It termiantes all threads when the server is requested to end */
    if(signal(SIGINT, handler_SIGINT) == SIG_ERR){
        error_message("ERROR: Unable to set up the new SIGINT handler in the server", __FILE__, __LINE__);
        return ERROR;
    }
    /* Initializing some semaphores */
    if(sem_init(&var_mutex, 0, 1) == ERROR){
        error_message("ERROR: Unable to create var_mutex sem", __FILE__, __LINE__);
        return ERROR;
    }
    if(sem_init(&accept_mutex, 0, 1) == ERROR){
        error_message("ERROR: Unable to create accept_mutex sem", __FILE__, __LINE__);
        return ERROR;
    }
    nthreads = nthr_pool;
    /* Creating first pool of threads */
    thr = (pthread_t*) malloc(nthr_pool * sizeof(pthread_t));
    if(!thr){
        error_message("ERROR: Memory NULL pointer allocating threads", __FILE__, __LINE__);
        return ERROR;
    }
    for(i=0; i<nthr_pool; i++){
        if(pthread_create(&thr[i], NULL, thread_run, (void*)&listenfd) != SUCCESS){
            error_message("ERROR: Unable to create the first pool of threads", __FILE__, __LINE__);
            return ERROR;
        }
    }
    info_message("First pool of threads created");

    while(!kill_flag){ /* While user does not press ctrl+c */
        pause(); /* Waiting until SIGUSR1 is received, indicating a new pool of threads is needed */
        if(!kill_flag){
            if((nthreads + nthr_pool) <= max_clients){
                info_message("Creating new pool of threads");
                sem_wait(&var_mutex);
                nthreads += nthr_pool;
                thr = (pthread_t*) realloc(thr, nthreads*sizeof(pthread_t)); /* Adding more memory for new threads */
                if(!thr){
                    error_message("ERROR: Unable to realloc more threads", __FILE__, __LINE__);
                    return ERROR;
                }
                for(i=(nthreads-nthr_pool); i<nthreads; i++){ /* Creating new pool of threads */
                    if(pthread_create(&thr[i], NULL, thread_run, (void*)&listenfd) != SUCCESS){
                        error_message("ERROR: Unable to create a new pool of threads", __FILE__, __LINE__);
                        return ERROR;
                    }
                }
                sem_post(&var_mutex);
            }
        }
    }
    for(i=0; i<nthreads; i++){ /* Waiting 'workers' to finish */
        pthread_join(thr[i], NULL);
    }
    sem_destroy(&var_mutex);
    sem_destroy(&accept_mutex);
    free(thr);
    return SUCCESS;
}

/******************************************************************************/
/*  FUNCTION: void* thread_run(void *arg)                                     */
/*  INPUT ARGS:                                                               */
/*      void *arg - input parameters, in this case the server file descript.  */
/*  RETURN: NULL in all cases                                                 */
/*  DESCRIPTION: Function called by pthread_create, main routine of each thr  */
/******************************************************************************/
void* thread_run(void *arg){
    int listenfd = *((int *)arg);
    if(signal(SIGUSR1, handler_SIGUSR1) == SIG_ERR){
        error_message("ERROR: Unable to set up the new signal USR1 handler in thread", __FILE__, __LINE__);
        return NULL;
    }
    while(!kill_flag){
        int clientfd;
        struct sockaddr_in cl_addr;
        socklen_t addrlen = sizeof(cl_addr);

        /* Accepting new client, protected with a semaphore */
        sem_wait(&accept_mutex);
        if((clientfd = accept(listenfd, (struct sockaddr*)&cl_addr, &addrlen)) == ERROR){
            error_message("ERROR: Unable to accept a client", __FILE__, __LINE__);
            exit(EXIT_FAILURE);
        }
        sem_wait(&var_mutex);
        nclients++; /* New client */
        nbusy_thr++; /* New busy thread */
        if(nbusy_thr == nthreads){
            kill(server_pid, SIGUSR1); /* Sending SIGUSR1 if a new pool of threads is needed */
        }
        sem_post(&var_mutex);
        sem_post(&accept_mutex);
        /* Working! */
        server_process_client_request(clientfd);

        sem_wait(&var_mutex);
        nbusy_thr--;
        sem_post(&var_mutex);
        close(clientfd);
    }
    return NULL;
}

/******************************************************************************/
/*  FUNCTION: void server_process_client_request(int clientfd)                */
/*  INPUT ARGS:                                                               */
/*      int clientfd - file descriptor of the client served by the calling thr*/
/*  RETURN: void                                                              */
/*  DESCRIPTION: It serves the client connected to the calling thread         */
/******************************************************************************/
int server_process_client_request(int clientfd){
    int recvlen, parse_ret;
    char buffer_request[BUFFER_LEN];
    const char *method, *path;
    int minor_version, keep_alive=1;
    size_t method_len, path_len, num_headers/*, buflen=0, prevbuflen=0*/;
    struct phr_header headers[MAX_HEADERS];
    char method_str[METH_LEN], path_str[PATH_LEN];

    if(clientfd < 0){ /* Input argument error */
        error_message("ERROR: Invalid client descriptor", __FILE__, __LINE__);
        return ERROR;
    }

    while(keep_alive){ /* Looping through several requests in HTTP/1.1 */
        bzero(buffer_request, BUFFER_LEN);
        recvlen = recv(clientfd, buffer_request, BUFFER_LEN, 0);
        if(recvlen < 0){
            error_message("ERROR: Unable to recieve request correctly", __FILE__, __LINE__);
            return ERROR;
        }
        else if(!recvlen){
            return SUCCESS; /* The client has performed an orderly shutdown */
        }

        num_headers = MAX_HEADERS;
        parse_ret = phr_parse_request(buffer_request, recvlen, &method, &method_len, &path, &path_len,
                                        &minor_version, headers, &num_headers, 0);
        if(parse_ret == ERROR){
            error_message("ERROR: Unable to parse client request", __FILE__, __LINE__);
            _send_error(clientfd, minor_version, ERROR_400_MSG);
            return ERROR;
        }
        else if(parse_ret == INCOMPLETE_REQUEST){
            error_message("ERROR: Unable to parse (request too long)", __FILE__, __LINE__);
            return ERROR;
        }

        if(!_check_keep_alive(headers, num_headers)){ /* Checking if the browser wants to close the connection */
            keep_alive = 0;
        }
        if(minor_version == 0){ /* HTTP/1.0 is not persistent */
            keep_alive = 0;
        }
        sprintf(method_str, "%.*s", (int)method_len, method);
        sprintf(path_str, "%.*s", (int)path_len, path);

        if(!strcmp(method_str, "GET")){
            server_get_response(clientfd, path_str, minor_version, buffer_request+parse_ret);
        }
        else if(!strcmp(method_str, "POST")){
            server_post_response(clientfd, path_str, minor_version, buffer_request+parse_ret);
        }
        else if(!strcmp(method_str, "OPTIONS")){
            server_options_response(clientfd, minor_version);
        }
        else{
            _send_error(clientfd, minor_version, ERROR_501_MSG);
        }
    }
    info_message("Client served successfully");
    return SUCCESS;
}

/******************************************************************************/
/*  FUNCTION: int server_get_response(int clientfd, char *path,               */
/*                                    int minor_version, char *body)          */
/*  INPUT ARGS:                                                               */
/*      int clientfd - file descriptor of the client                          */
/*      char *path - path requested in GET petition                           */
/*      int minor_version - 1 or 0 depending on HTTP/1.1 or HTTP/1.0          */
/*      char *body - body of the request                                      */
/*  RETURN: int - 0 on sucess and negative integer on error case              */
/*  DESCRIPTION: It processes a GET request                                   */
/******************************************************************************/
int server_get_response(int clientfd, char *path, int minor_version, char *body){
    int filedescr, size;
    char path_str[LEN], buffer_response[BUFFER_LEN];
    char date_aux[LEN], mod_date_aux[LEN], server_aux[LEN], content_length_aux[LEN], content_type_aux[LEN];
    struct tm tm;
    struct stat f_stat;
    time_t now;
    off_t offs=0;

    /* Input argument error */
    if(!path){
        error_message("ERROR: Path NULL pointer", __FILE__, __LINE__);
        return ERROR;
    }
    /* Checking if the client requests to run a script */
    if(strstr(path, GET_CHECK_SCRIPT)){
        return server_post_response(clientfd, path, minor_version, body);
    }
    /* Setting up path of the resource */
    bzero(buffer_response, PATH_LEN);
    bzero(path_str, LEN);
    strcpy(path_str, working_dir);
    strcat(path_str, INDEX);
    strncat(path_str, options[SERVER_ROOT].value, strlen(options[SERVER_ROOT].value)-1);
    /* Getting current date for headers */
    now = time(0);
    tm = *gmtime(&now);
    strftime(date_aux, LEN, "Date: %a, %d %b %Y %H:%M:%S %Z\r\n", &tm);
    /* Setting up server name */
    sprintf(server_aux, "Server: %s\r\n", options[SERVER_SIGNATURE].value);
    /* Opening resource file */
    if(!strcmp(path, INDEX)){ /* GET / is equal to GET /index.html */
        strcat(path_str, INDEX_PATH);
        filedescr = open(path_str, O_RDONLY);
    }
    else{
        strcat(path_str, path);
        filedescr = open(path_str, O_RDONLY);
    }
    if(filedescr == ERROR){
        error_message("ERROR: Resource not found (error 404)", __FILE__, __LINE__);
        _send_error(clientfd, minor_version, ERROR_404_MSG);
        return ERROR;
    }
    /* PREPARING OK HEADER ... */
    /* OK message */
    sprintf(buffer_response, "HTTP/1.%d 200 OK\r\n", minor_version);
    /* Current date (previously allocated) */
    strcat(buffer_response, date_aux);
    /* Server name (previously allocated) */
    strcat(buffer_response, server_aux);
    /* Getting last modification date of the file */
    if(stat(path_str, &f_stat) == ERROR){
        error_message("ERROR: Unable to last modification date", __FILE__, __LINE__);
        return ERROR;
    }
    strftime(mod_date_aux, LEN, "Last-Modified: %a, %d %b %Y %H:%M:%S %Z\r\n", gmtime(&(f_stat.st_ctime)));
    strcat(buffer_response, mod_date_aux);
    /* Calculating body length (content-length)*/
    size = lseek(filedescr, 0, SEEK_END);
    lseek(filedescr, 0, SEEK_SET);
    sprintf(content_length_aux, "Content-Length: %d\r\n", size);
    strcat(buffer_response, content_length_aux);
    /* Getting file type (content-type) */
    if(_get_content_type(path_str, content_type_aux) == ERROR){
        error_message("ERROR: Get content type function has failed", __FILE__, __LINE__);
        return ERROR;
    }
    strcat(buffer_response, content_type_aux);
    /* Sending header to the client */
    if(send(clientfd, buffer_response, strlen(buffer_response), 0) == ERROR){
        error_message("ERROR: Unable to response the client (header)", __FILE__, __LINE__);
        close(filedescr);
        return ERROR;
    }
    /* Sending body to the client */
    while(offs < size){
        if(sendfile(clientfd, filedescr, &offs, BUFFER_LEN) == ERROR){
            error_message("ERROR: Sendfile function has failed", __FILE__, __LINE__);
            close(filedescr);
            return ERROR;
        }
    }
    close(filedescr);
    return SUCCESS;
}

/******************************************************************************/
/*  FUNCTION: int server_options_response(int clientfd, int minor_version     */
/*  INPUT ARGS:                                                               */
/*      int clientfd - file descriptor of the client                          */
/*      int minor_version - 1 or 0 depending on HTTP/1.1 or HTTP/1.0          */
/*  RETURN: int - 0 on sucess and negative integer on error case              */
/*  DESCRIPTION: It processes a OPTIONS request                               */
/******************************************************************************/
int server_options_response(int clientfd, int minor_version){
    char buffer_response[BUFFER_LEN];
    char date_aux[LEN], server_aux[LEN], allow_aux[LEN];
    struct tm tm;
    time_t now;

    sprintf(buffer_response, "HTTP/1.%d 200 OK\r\n", minor_version);
    /* Allow options */
    sprintf(allow_aux, "Allow: OPTIONS, GET, POST\r\n");
    strcat(buffer_response, allow_aux);
    /* Getting date for headers */
    now = time(0);
    tm = *gmtime(&now);
    strftime(date_aux, LEN, "Date: %a, %d %b %Y %H:%M:%S %Z\r\n", &tm);
    strcat(buffer_response, date_aux);
    /* Writing server name and content length = 0*/
    sprintf(server_aux, "Server: %s\r\n", options[SERVER_SIGNATURE].value);
    strcat(server_aux, "Content-Length: 0\r\n\r\n");
    strcat(buffer_response, server_aux);
    if(send(clientfd, buffer_response, BUFFER_LEN, 0) == ERROR){
        error_message("ERROR: Unable to response the client (options)", __FILE__, __LINE__);
        return ERROR;
    }
    return SUCCESS;
}

/******************************************************************************/
/*  FUNCTION: int server_post_response(int clientfd, char *path,              */
/*                                    int minor_version, char *body)          */
/*  INPUT ARGS:                                                               */
/*      int clientfd - file descriptor of the client                          */
/*      char *path - path requested in POST petition                          */
/*      int minor_version - 1 or 0 depending on HTTP/1.1 or HTTP/1.0          */
/*      char *body - body of the request                                      */
/*  RETURN: int - 0 on sucess and negative integer on error case              */
/*  DESCRIPTION: It processes a POST request                                  */
/******************************************************************************/
int server_post_response(int clientfd, char *path, int minor_version, char *body){
    char command[LEN];
    char script_path[PATH_LEN];
    char *inter;
    int len;
    FILE *pf=NULL, *body_f=NULL;

    if(!path){ /* Input argument error */
        error_message("ERROR: Path NULL pointer", __FILE__, __LINE__);
        return ERROR;
    }
    /* Main part of the command */
    bzero(command, LEN);
    if(strstr(path, ".py")){
        sprintf(command, PYTHON_SCRIPT);
    }
    else{
        sprintf(command, PHP_SCRIPT);
    }
    strcat(command, working_dir);
    strcat(command, INDEX);
    strncat(command, options[SERVER_ROOT].value, strlen(options[SERVER_ROOT].value)-1);
    inter = strrchr(path, '?');
    if(inter){
        len = (int)(inter-path);
        strncat(command, path, len);
        strcat(command, " ");
        strcat(command, inter+1);
    }
    else{
        strcat(command, path);
    }
    /* Body */
    if(body){
        body_f = fopen(POST_BODY_F, "wb");
        if(!body_f){
            error_message("ERROR: Unable to open file to transfer body", __FILE__, __LINE__);
            _send_error(clientfd, minor_version, ERROR_404_MSG);
            return ERROR;
        }
        fwrite(body, strlen(body), 1, body_f);
        fclose(body_f);
        strcat(command, " < ");
        strcat(command, POST_BODY_F);
    }
    /* Running script */
    if(!(pf = popen(command, "r"))){
        error_message("ERROR: Unable to execute POST script", __FILE__, __LINE__);
        return ERROR;
    }

    bzero(script_path, PATH_LEN);
    fread(script_path, PATH_LEN, 1, pf);
    /* Sending response*/
    if(server_get_response(clientfd, script_path, minor_version, NULL) == ERROR){
        error_message("ERROR: Unable to send post response", __FILE__, __LINE__);
        return ERROR;
    }
    return SUCCESS;
}

/******************************************************************************/
/*  FUNCTION: _get_content_type                                               */
/*  INPUT ARGS:                                                               */
/*      char *path - path requested                                           */
/*      char *response - type of the file requested                           */
/*  RETURN: int - 0 on sucess and negative integer on error case              */
/*  DESCRIPTION: Specifies the type of a file                                 */
/******************************************************************************/
int _get_content_type(char *path, char *response){
    char buf_aux[LEN];
    char *last_dot, *last_inter;
    int i, len;
    /* Getting file extension */
    last_dot = strrchr(path, '.');
    if((last_inter = strrchr(path, '?')) == NULL){
        strcpy(buf_aux, last_dot);
    }
    else{
        len = (int)(last_inter - last_dot);
        strncpy(buf_aux, last_dot, len);
        buf_aux[len] = '\0';
    }
    /* Getting content type */
    for(i=0; ;i++){
        if(extensions[i].ext == 0){
            break;
        }
        if(!strcmp(buf_aux, extensions[i].ext)){
            bzero(response, LEN);
            sprintf(response, "Content-Type: %s\r\n\r\n", extensions[i].filetype);
            return SUCCESS;
        }
    }
    return ERROR;
}

/******************************************************************************/
/*  FUNCTION: _send_error                                                     */
/*  INPUT ARGS:                                                               */
/*      int clientfd - file descriptor of the socket of the client            */
/*      int minor_version - HTTP version (1 or 0)                             */
/*      char *error_msg - error message that we have to sends                 */
/*  DESCRIPTION:  sends an error to the client                                */
/******************************************************************************/
void _send_error(int clientfd, int minor_version, char *error_msg){
    char buffer_response[BUFFER_LEN];
    char date_aux[LEN], server_aux[LEN], error_aux[LEN];
    struct tm tm;
    time_t now;

    /* Setting up path of the resource */
    bzero(buffer_response, PATH_LEN);
    /* Getting current date for headers */
    now = time(0);
    tm = *gmtime(&now);
    strftime(date_aux, LEN, "Date: %a, %d %b %Y %H:%M:%S %Z\r\n", &tm);
    /* Setting up server name */
    sprintf(server_aux, "Server: %s\r\n", options[SERVER_SIGNATURE].value);

    sprintf(buffer_response, "HTTP/1.%d %s\r\n", minor_version, error_msg);
    strcat(buffer_response, date_aux);
    strcat(server_aux, "Content-Length: 0\r\n\r\n");
    strcat(buffer_response, server_aux);
    if(send(clientfd, buffer_response, strlen(buffer_response), 0) == ERROR){
        sprintf(error_aux, "ERROR: Unable to send error %s to the client", error_msg);
        error_message(error_aux, __FILE__, __LINE__);
    }
}

/******************************************************************************/
/*  FUNCTION: _check_keep_alive                                               */
/*  INPUT ARGS:                                                               */
/*      struct phr_header *headers - array of headers of a requests           */
/*      size_t num_headers - number of headers                                */
/*  RETURN: int - Returns 1 if any header includes "Connection: Keep-Alive"   */
/*                Returns 0 in another case                                   */
/*  DESCRIPTION:  Checks if a header includes "Connection: Keep-Alive"        */
/******************************************************************************/
int _check_keep_alive(struct phr_header *headers, size_t num_headers){
    char aux_buf[LEN];
    int i;

    for(i=0; i<num_headers; i++){
        bzero(aux_buf, LEN);
        sprintf(aux_buf, "%.*s", (int)headers[i].name_len, headers[i].name);
        if(!strcmp(aux_buf, "Connection") || !strcmp(aux_buf, "connection")){
            bzero(aux_buf, LEN);
            sprintf(aux_buf, "%.*s", (int)headers[i].value_len, headers[i].value);
            if(!strcmp(aux_buf, "Keep-Alive") || !strcmp(aux_buf, "keep-alive")){
                return 1;
            }
            return 0;
        }
    }
    return 0;
}
