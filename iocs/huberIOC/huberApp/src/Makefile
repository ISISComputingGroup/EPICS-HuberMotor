TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = huber
# huber.dbd will be created and installed
DBD += huber.dbd

# huber.dbd will be made up from these files:
huber_DBD += base.dbd

# Include dbd files from all support applications:
#ifdef ASYN
huber_DBD += asyn.dbd
huber_DBD += drvAsynSerialPort.dbd
huber_DBD += drvAsynIPPort.dbd
#endif
huber_DBD += motorSupport.dbd
huber_DBD += devHuberMotor.dbd

# Add all the support libraries needed by this IOC
huber_LIBS += Huber
huber_LIBS += motor
#ifdef ASYN
huber_LIBS += asyn
#endif
#ifdef SNCSEQ
huber_LIBS += seq pv
#endif

# huber_registerRecordDeviceDriver.cpp derives from huber.dbd
huber_SRCS += huber_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
huber_SRCS_DEFAULT += huberMain.cpp
huber_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#huber_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
huber_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

