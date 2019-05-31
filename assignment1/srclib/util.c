/******************************************************************************/
/*  PROJECT: Assignment 1 - Communication Networks II                         */
/*  FILE: util.c                                                              */
/*  AUTHORS:                                                                  */
/*      Alejandro Santorum Varela - alejandro.santorum@estudiante.uam.es      */
/*      David Cabornero Pascual - david.cabornero@estudiante.uam.es           */
/*  DATE: March 2, 2019                                                       */
/*  VERSION: 1.5                                                              */
/*                                                                            */
/*  DESCRIPTION: Implementation of some common utilities for the assignm.     */
/******************************************************************************/
#include "util.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <syslog.h>
#include <errno.h>

/* Flag that indicates we want to print info/error messages
on the terminal standard output or in the initialized syslog */
#define SYSLOG_ON 1

/******************************************************************************/
/*  FUNCTION: void error_message(char *msg, char *file, int line)             */
/*  INPUT ARGS:                                                               */
/*      char *msg - error message                                             */
/*      char *file - name of the file where the error appeared (__FILE__)     */
/*      int line: line of the file where the error appeared (__LINE__)        */
/*  RETURN: void                                                              */
/*  DESCRIPTION: Function that outputs in syslog the error message            */
/******************************************************************************/
void error_message(char *msg, char *file, int line){
    if(SYSLOG_ON){
        syslog(LOG_ERR, "%s || File: %s - Line: %d\n", msg, file, line);
    }
    else{
        printf("%s || File: %s - Line: %d\n%s\n", msg, file, line, strerror(errno));
    }
}

/******************************************************************************/
/*  FUNCTION: void error_message(char *msg)                                   */
/*  INPUT ARGS:                                                               */
/*      char *msg - error message                                             */
/*  RETURN: void                                                              */
/*  DESCRIPTION: Function that outputs in syslog the message                  */
/******************************************************************************/
void info_message(char *msg){
    if(SYSLOG_ON){
        syslog(LOG_INFO, "%s\n", msg);
    }
    else{
        printf("%s\n", msg);
    }
}

/******************************************************************************/
/*  FUNCTION: void _clear_linebreaks(char *str, int maxlen)                   */
/*  INPUT ARGS:                                                               */
/*      char *str - string to delete linebreaks                               */
/*      int maxlen - length of the given string                               */
/*  RETURN: void                                                              */
/*  DESCRIPTION: Private function that deletes linebreaks of a given string,  */
/*      substituting them for 0                                               */
/******************************************************************************/
void _clear_linebreaks(char *str, int maxlen){
    int i;
	for(i=0; i<maxlen; i++){
		if(str[i] == '\n'){
			str[i] = 0;
			return;
		}
	}
}

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
int my_confuse(char *filename, struct optc *options, int nopts){
    char buffer[CONF_LENGTH], key[CONF_LENGTH], value[CONF_LENGTH];
	FILE *f=NULL;
	char *b1;
	int i, len;

  printf("Filename confuse: %s\n", filename);
	f = (FILE*) fopen(filename, "r");
	if(!f){
		return ERROR;
	}

	while(!feof(f)){
		bzero(buffer, CONF_LENGTH);
		if(fgets(buffer, CONF_LENGTH, f) == 0){ /* End of file */
			break;
		}
		if(buffer[0] == '#'){ /* Commentary must be ignored */
			continue;
		}
		b1 = strchr(buffer, '='); /* Getting '=' index */
		len = (int) (b1-buffer-1);
		bzero(key, CONF_LENGTH);
		strncpy(key, buffer, len); /* Getting key */
		b1 += 2; /* We do not need '= ' */
		bzero(value, CONF_LENGTH); /* Getting value */
		strcpy(value, b1);

		for(i=0; i<nopts; i++){
			if(!strcmp(key, options[i].key)){
                _clear_linebreaks(value, CONF_LENGTH);
				strcpy(options[i].value, value); /* Adding new config macro */
				break;
			}
		}
	}
	fclose(f);
	return SUCCESS;
}
