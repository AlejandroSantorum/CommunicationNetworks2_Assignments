CC = gcc -ansi
CFLAGS = -g -Wall -D_GNU_SOURCE -Iincludes
CLIBS = -pthread
EXE = run_server
LIBS = picohttpparser
INCLUDES_DIR = includes/
SRCLIB_DIR = srclib/
LIBS_DIR = lib/
SRC_DIR = src/

all: full

$(EXE) : % : %.o $(SRC_DIR)daemon.o $(SRC_DIR)server.o
	$(CC) $(CFLAGS) -o $@ $@.o $(SRC_DIR)daemon.o $(SRC_DIR)server.o $(LIBS_DIR)*.a $(CLIBS)

daemon.o : $(SRC_DIR)daemon.c $(INCLUDES_DIR)daemon.h
	$(CC) $(CFLAGS) -c $<

server.o : $(SRC_DIR)server.c $(INCLUDES_DIR)server.h
	$(CC) $(CFLAGS) -c $<


.PHONY : src
src : $(EXE)

.PHONY : libobj
libobj :
	cd $(SRCLIB_DIR) && $(CC) -c *.c

.PHONY : libs
libs :
	ar rcs $(LIBS_DIR)picohttpparser.a $(SRCLIB_DIR)picohttpparser.o
	ar rcs $(LIBS_DIR)util.a $(SRCLIB_DIR)util.o

.PHONY : full
full : libobj libs $(EXE)

.PHONY : clean
clean : clean_libobj clean_libs clear

.PHONY : clean_libobj
clean_libobj :
	rm -f $(SRCLIB_DIR)*.o

.PHONY : clean_libs
clean_libs :
	rm -f $(LIBS_DIR)*.a

.PHONY : clear
clear :
	rm -f *.o core $(EXE)
	rm -f $(SRC_DIR)*.o
