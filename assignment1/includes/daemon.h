/******************************************************************************/
/*  PROJECT: Assignment 1 - Communication Networks II                         */
/*  FILE: daemon.h                                                            */
/*  AUTHORS:                                                                  */
/*      Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es      */
/*      David Cabornero Pascual - david.cabornero@estudiante.uam.es           */
/*  DATE: March 4, 2019                                                       */
/*  VERSION: 1.5                                                              */
/*                                                                            */
/*  DESCRIPTION: Definition of the functions for daemon                       */
/******************************************************************************/
#ifndef DAEMON_H
#define DAEMON_H
#include "util.h"

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
int demonize(char *service, char *current_dir, int len_dir);

#endif
