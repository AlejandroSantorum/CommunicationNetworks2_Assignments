/******************************************************************************/
/*  PROJECT: Assignment 1 - Communication Networks II                         */
/*  FILE: util.h                                                              */
/*  AUTHORS:                                                                  */
/*      Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es      */
/*      David Cabornero Pascual - david.cabornero@estudiante.uam.es           */
/*  DATE: March 2, 2019                                                       */
/*  VERSION: 1.3                                                              */
/*                                                                            */
/*  DESCRIPTION: Definition of common utilities for the assignment            */
/******************************************************************************/
#ifndef UTIL_H
#define UTIL_H

#define ERROR -1 /* Error macro */
#define SUCCESS 0 /* Success macro */
#define CONF_LENGTH 64

/* Auxiliary struct to use my_confuse function */
struct optc{
	char key[CONF_LENGTH]; /* key = key to search in the file */
	char value[CONF_LENGTH]; /* value: where the value of the key is returned */
};

/******************************************************************************/
/*  FUNCTION: int my_confuse(char *filename, struct optc *options, int nopts) */
/*  INPUT ARGS:                                                               */
/*      char *filename - filename of the file where the config is stored      */
/*      struct optc *options - array of structs where the key is the name of  */
/*                             the variable to be searched, and value is the  */
/*                             value of the variable represented with key.    */
/*      int nopts - size of the array of structs and the number of tuples     */
/*                  key = value desired to be read in the file                */
/*  RETURN: int - 0 on sucess and negative integer on error case              */
/*  DESCRIPTION: Function that reads a file searching for tuples key = value, */
/*      where the key is stored in options[i].key, and the value is returned  */
/*      in options[i].value if it is found                                    */
/******************************************************************************/
int my_confuse(char *filename, struct optc *options, int nopts);

/******************************************************************************/
/*  FUNCTION: void error_message(char *msg, char *file, int line)             */
/*  INPUT ARGS:                                                               */
/*      char *msg - error message                                             */
/*      char *file - name of the file where the error appeared (__FILE__)     */
/*      int line: line of the file where the error appeared (__LINE__)        */
/*  RETURN: void                                                              */
/*  DESCRIPTION: Function that outputs in syslog the error message            */
/******************************************************************************/
void error_message(char *msg, char *file, int line);

/******************************************************************************/
/*  FUNCTION: void error_message(char *msg)                                   */
/*  INPUT ARGS:                                                               */
/*      char *msg - error message                                             */
/*  RETURN: void                                                              */
/*  DESCRIPTION: Function that outputs in syslog the message                  */
/******************************************************************************/
void info_message(char *msg);

#endif
