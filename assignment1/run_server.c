/******************************************************************************/
/*  PROJECT: Assignment 1 - Communication Networks II                         */
/*  FILE: server_test.c                                                       */
/*  AUTHORS:                                                                  */
/*      Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es      */
/*      David Cabornero Pascual - david.cabornero@estudiante.uam.es           */
/*  DATE: February 6, 2019                                                    */
/*  VERSION: 1.0                                                              */
/*                                                                            */
/*  DESCRIPTION: Small tester program that checks functionality               */
/******************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/socket.h>
#include <resolv.h>
#include <arpa/inet.h>
#include <errno.h>
#include <unistd.h>
#include "daemon.h"
#include "server.h"
#include "util.h"
#include "stddef.h"

#define PORT 5001

#define DEBUG_FLAG 0
#define DEMONIZE_FLAG 1

int main(int argc, char **argv){
    if(DEBUG_FLAG){
        int listenfd, clientfd;
        struct sockaddr_in client_addr;
        socklen_t addrlen = sizeof(client_addr);
        char address[16];

        bzero(address, 16);

        if(argc>=2){
          strcpy(address, argv[1]);
        }
        else{
            strcpy(address, "ANY");
        }

        if((listenfd = tcp_listen(address, PORT, 50)) == ERROR){
          printf("ERROR: tcp listen test\n");
          exit(EXIT_FAILURE);
        }

        server_config();

        while(1){
            printf("Esperando a un nuevo cliente\n");
            if((clientfd = accept(listenfd, (struct sockaddr*)&client_addr, &addrlen)) == ERROR){
                printf("ERROR: Accept test\n");
                exit(EXIT_FAILURE);
            }
            printf("NUEVO CLIENTE ACEPTADO\n");
            server_process_client_request(clientfd);
            close(clientfd);
            printf("Cliente atendido\n");
        }
        close(listenfd);
    }
    else{
        if(DEMONIZE_FLAG){
            char cwd[128];
            if(demonize("testing", cwd, 128) == ERROR){
                perror("Demonize error");
                return EXIT_FAILURE;
            }
            if(server_init("ANY", cwd) == ERROR){
                perror("Imposible to initialize server");
                return EXIT_FAILURE;
            }
        }
        else{
            if(server_init("ANY", NULL) == ERROR){
                perror("Imposible to initialize server");
                return EXIT_FAILURE;
            }
        }
    }
    return EXIT_SUCCESS;
}
