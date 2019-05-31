/******************************************************************************/
/*  PROJECT: Assignment 1 - Communication Networks II                         */
/*  FILE: daemon.c                                                            */
/*  AUTHORS:                                                                  */
/*      Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es      */
/*      David Cabornero Pascual - david.cabornero@estudiante.uam.es           */
/*  DATE: March 4, 2019                                                       */
/*  VERSION: 1.5                                                              */
/*                                                                            */
/*  DESCRIPTION: Implementation of daemon function                            */
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
#include "daemon.h"
#include "util.h"

#define WORKING_DIR "/"

/******************************************************************************/
/*  FUNCTION: int demonize(char *service)                                     */
/*  INPUT ARGS:                                                               */
/*      char *service - service that describes the server                     */
/*      char *current_dir - buffer to return current working directory        */
/*      int len_dir - size of current_dir buffer                              */
/*  RETURN: int - 0 on sucess and negative integer on error case              */
/*  DESCRIPTION: Function that detaches the program from the controlling      */
/*      terminal and run in the background as system daemon. Additionally,    */
/*      it returns the current working directory before detaching it from     */
/*      the terminal in the buffer called current_dir with length len_dir     */
/******************************************************************************/
int demonize(char *service, char *current_dir, int len_dir){
    int pid, max_fds;
    int i;

    if(!service){ /* NULL pointer error */
        error_message("ERROR: Server service description NULL pointer", __FILE__, __LINE__);
        return ERROR;
    }

    /*Creating the daemon*/
    if((pid = fork()) == ERROR){
        error_message("ERROR: Unable to fork", __FILE__, __LINE__);
        return ERROR;
    }
    if(pid){ /* Terminating father process */
        exit(SUCCESS);
    }

    /* Setting up syslog */
    setlogmask(LOG_UPTO (LOG_INFO));
    openlog("Server system messages", LOG_CONS | LOG_PID | LOG_NDELAY, LOG_LOCAL1);
    syslog(LOG_INFO, "Initializing daemon...");

    /* Changing mask to be accessible for everybody */
    umask(0);

    /* Making the daemon the leader of the group */
    if(setsid() == ERROR){
        error_message("ERROR: Unable to make the daemon the leader of the group", __FILE__, __LINE__);
        return ERROR;
    }

    /* Getting current working directory */
    if(current_dir && len_dir > 0){
        bzero(current_dir, len_dir);
        if(!getcwd(current_dir, len_dir)){
            error_message("ERROR: Unable to get current working directory", __FILE__, __LINE__);
            return ERROR;
        }
    }
    /* Setting root directory as the working directory */
    if(chdir(WORKING_DIR) == ERROR){
        error_message("ERROR: Unable to change the working directory", __FILE__, __LINE__);
        return ERROR;
    }

    /* Getting the maximum number of files a process can have open */
    if((max_fds = getdtablesize()) < 0){
        error_message("ERROR: Unable to get RLIMIT_NOFILE", __FILE__, __LINE__);
        return ERROR;
    }
    /* Closing all file descriptors that may be opened */

    for(i=0; i<max_fds; i++){
        close(i);
    }
    syslog(LOG_INFO, "Daemonize completed!");

    return SUCCESS;
}
