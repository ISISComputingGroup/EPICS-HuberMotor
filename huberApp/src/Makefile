# Makefile
TOP = ../..
include $(TOP)/configure/CONFIG

# The following are used for debugging messages.
USR_CXXFLAGS += -DDEBUG

DBD += devHuberMotor.dbd
DBD += homing.dbd

LIBRARY_IOC = Huber

# Advanced Control Systems driver support.
SRCS += SMC9300Driver.cpp
SRCS += homing.st

Huber_LIBS += motor asyn
Huber_LIBS += seq
Huber_LIBS += pv
Huber_LIBS += $(EPICS_BASE_IOC_LIBS)

include $(TOP)/configure/RULES

