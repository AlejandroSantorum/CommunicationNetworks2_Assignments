/******************************************************************************/
/*  PROJECT: Assignment 1 - Communication Networks II                         */
/*  FILE: server.h                                                            */
/*  AUTHORS:                                                                  */
/*      Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es      */
/*      David Cabornero Pascual - david.cabornero@estudiante.uam.es           */
/*  DATE: March 4, 2019                                                       */
/*  VERSION: 1.8                                                              */
/*                                                                            */
/*  DESCRIPTION: Definition of web server functions                           */
/******************************************************************************/
#ifndef SERVER_H
#define SERVER_H

/**
* Struct used as a input parameter to server_daemon_init function, in order
* to be passed from the daemon set up function
*/
typedef struct{
    char *serv_addr;
    int serv_port;
    int max_queue;
    int nthr_pool;
} serv_param;

/* Public function in order to debug, otherwise it would be private of server.c */
int server_config();

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
int tcp_listen(char *serv_addr, int serv_port, int max_queue);

/******************************************************************************/
/*  FUNCTION: int server_init(char *serv_addr, char *work_dir)                */
/*  INPUT ARGS:                                                               */
/*      char *serv_addr - address where the server is going to be binded      */
/*      char *work_dir - current working directory before calling daemonize   */
/*  RETURN: int - 0 on sucess and negative integer on error case              */
/*  DESCRIPTION: It prepares all the server configuration introduced by       */
/*      the user and starts the server                                        */
/******************************************************************************/
int server_init(char *serv_addr, char *work_dir);

/******************************************************************************/
/*  FUNCTION: int server_run(int listenfd, int nthr_pool)                     */
/*  INPUT ARGS:                                                               */
/*      int listenfd - file descriptor returned by socket function            */
/*  RETURN: int - 0 on sucess and negative integer on error case              */
/*  DESCRIPTION: Main function of the server, where the initial pool of       */
/*      threads is initialized and where a new pool of threads is created     */
/*      as soon as all the created threads are working                        */
/******************************************************************************/
int server_run(int listenfd);

/******************************************************************************/
/*  FUNCTION: void* thread_run(void *arg)                                     */
/*  INPUT ARGS:                                                               */
/*      void *arg - input parameters, in this case the server file descript.  */
/*  RETURN: NULL in all cases                                                 */
/*  DESCRIPTION: Function called by pthread_create, main routine of each thr  */
/******************************************************************************/
void* thread_run(void *arg);

/******************************************************************************/
/*  FUNCTION: void server_process_client_request(int clientfd)                */
/*  INPUT ARGS:                                                               */
/*      int clientfd - file descriptor of the client served by the calling thr*/
/*  RETURN: void                                                              */
/*  DESCRIPTION: It serves the client connected to the calling thread         */
/******************************************************************************/
int server_process_client_request(int clientfd);

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
int server_get_response(int clientfd, char *path, int minor_version, char *body);

/******************************************************************************/
/*  FUNCTION: int server_options_response(int clientfd, int minor_version     */
/*  INPUT ARGS:                                                               */
/*      int clientfd - file descriptor of the client                          */
/*      int minor_version - 1 or 0 depending on HTTP/1.1 or HTTP/1.0          */
/*  RETURN: int - 0 on sucess and negative integer on error case              */
/*  DESCRIPTION: It processes a OPTIONS request                               */
/******************************************************************************/
int server_options_response(int clientfd, int minor_version);

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
int server_post_response(int clientfd, char *path, int minor_version, char *body);


#endif
