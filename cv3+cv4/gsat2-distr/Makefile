BINDIR?=~/bin
LDLIBS+=-lm
CC=gcc ${DBG} -O ${TRACE} -Wall -Wpedantic
PROGS=gsat2 rngstart rngstub

all: $(PROGS)
gsat2: gsat2.o sat_inst.o sat_sol.o xoshiro256plus.o rngctrl.o 
rngstart: rngstart.o xoshiro256plus.o rngctrl.o 
rngstub: rngstub.o xoshiro256plus.o rngctrl.o 

gsat2.o:: sat_inst.h sat_sol.h rngctrl.h xoshiro256plus.h
rngstart.o:: rngctrl.h xoshiro256plus.h
rngstub.o:: rngctrl.h xoshiro256plus.h
sat_inst.o:: sat_inst.h 
sat_sol.o:: sat_sol.h xoshiro256plus.h
xoshiro256plus.o:: xoshiro256plus.h

clean:
	- rm *.o *.log ${PROGS}
	
install:
	mkdir -p ${BINDIR}
	cp ${PROGS} ${BINDIR}


