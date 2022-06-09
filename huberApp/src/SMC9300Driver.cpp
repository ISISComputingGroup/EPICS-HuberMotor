/*
FILENAME... SMC9300Driver.cpp
USAGE...    Motor driver support for the HUBER SMC9300 controller.

Yang Dongliang
March 1, 2020

*/


#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

#include <iocsh.h>
#include <epicsThread.h>

#include <asynOctetSyncIO.h>

#include <epicsExport.h>
#include "SMC9300Driver.h"

#define STEPS_PER_EGU 10000.

#define NINT(f) (int)((f)>0 ? (f)+0.5 : (f)-0.5)

static void huberHomingThreadC(void *pPvt);

/** Creates a new SMC9300Controller object.
  * \param[in] portName          The name of the asyn port that will be created for this driver
  * \param[in] SMC9300PortName     The name of the drvAsynSerialPort that was created previously to connect to the SMC9300 controller 
  * \param[in] numAxes           The number of axes that this controller supports 
  * \param[in] movingPollPeriod  The time between polls when any axis is moving 
  * \param[in] idlePollPeriod    The time between polls when no axis is moving 
  */
SMC9300Controller::SMC9300Controller(const char *portName, const char *SMC9300PortName, int numAxes, 
                                 double movingPollPeriod, double idlePollPeriod)
  :  asynMotorController(portName, numAxes, NUM_SMC9300_PARAMS, 
                         0, // No additional interfaces beyond those in base class
                         0, // No additional callback interfaces beyond those in base class
                         ASYN_CANBLOCK | ASYN_MULTIDEVICE, 
                         1, // autoconnect
                         0, 0)  // Default priority and stack size
{
  int axis;
  asynStatus status;
  SMC9300Axis *pAxis;
  static const char *functionName = "SMC9300Controller::SMC9300Controller";

  /* Connect to SMC9300 controller */
  status = pasynOctetSyncIO->connect(SMC9300PortName, 0, &pasynUserController_, NULL);
  if (status) {
    asynPrint(this->pasynUserSelf, ASYN_TRACE_ERROR, 
      "%s: cannot connect to Huber_SMC9300 controller\n",
      functionName);
  }
  for (axis=1; axis<numAxes; axis++) {
    pAxis = new SMC9300Axis(this, axis);
  }

  startPoller(movingPollPeriod, idlePollPeriod, 2);
}


/** Creates a new SMC9300Controller object.
  * Configuration command, called directly or from iocsh
  * \param[in] portName          The name of the asyn port that will be created for this driver
  * \param[in] SMC9300PortName       The name of the drvAsynIPPPort that was created previously to connect to the SMC9300 controller 
  * \param[in] numAxes           The number of axes that this controller supports 
  * \param[in] movingPollPeriod  The time in ms between polls when any axis is moving
  * \param[in] idlePollPeriod    The time in ms between polls when no axis is moving 
  */
extern "C" int SMC9300CreateController(const char *portName, const char *SMC9300PortName, int numAxes, 
                                   int movingPollPeriod, int idlePollPeriod)
{
  SMC9300Controller *pSMC9300Controller
    = new SMC9300Controller(portName, SMC9300PortName, numAxes, movingPollPeriod/1000., idlePollPeriod/1000.);
  pSMC9300Controller = NULL;
  return(asynSuccess);
}

/** Reports on status of the driver
  * \param[in] fp The file pointer on which report information will be written
  * \param[in] level The level of report detail desired
  *
  * If details > 0 then information is printed about each axis.
  * After printing controller-specific information it calls asynMotorController::report()
  */
void SMC9300Controller::report(FILE *fp, int level)
{
  fprintf(fp, "Huber_SMC9300 motor driver %s, numAxes=%d, moving poll period=%f, idle poll period=%f\n", 
    this->portName, numAxes_, movingPollPeriod_, idlePollPeriod_);

  // Call the base class method
  asynMotorController::report(fp, level);
}

/** Returns a pointer to an SMC9300Axis object.
  * Returns NULL if the axis number encoded in pasynUser is invalid.
  * \param[in] pasynUser asynUser structure that encodes the axis index number. */
SMC9300Axis* SMC9300Controller::getAxis(asynUser *pasynUser)
{
  return static_cast<SMC9300Axis*>(asynMotorController::getAxis(pasynUser));
}

/** Returns a pointer to an SMC9300Axis object.
  * Returns NULL if the axis number encoded in pasynUser is invalid.
  * \param[in] axisNo Axis index number. */
SMC9300Axis* SMC9300Controller::getAxis(int axisNo)
{
  return static_cast<SMC9300Axis*>(asynMotorController::getAxis(axisNo));
}


// These are the SMC9300Axis methods

/** Creates a new SMC9300Axis object.
  * \param[in] pC Pointer to the SMC9300Controller to which this axis belongs. 
  * \param[in] axisNo Index number of this axis, range 0 to pC->numAxes_-1.
  * 
  * Initializes register numbers, etc.
  */
SMC9300Axis::SMC9300Axis(SMC9300Controller *pC, int axisNo)
  : asynMotorAxis(pC, axisNo),
    pC_(pC)
{  
}

/** Reports on status of the axis
  * \param[in] fp The file pointer on which report information will be written
  * \param[in] level The level of report detail desired
  *
  * After printing device-specific information calls asynMotorAxis::report()
  */
void SMC9300Axis::report(FILE *fp, int level)
{
  if (level > 0) {
    fprintf(fp, "  axis %d\n",
            axisNo_);
  }

  // Call the base class method
  asynMotorAxis::report(fp, level);
}

asynStatus SMC9300Axis::sendAccelAndVelocity(double acceleration, double velocity) 
{
  asynStatus status;
  int ival;
  // static const char *functionName = "SMC9300::sendAccelAndVelocity";

  // Send the velocity
  // ival = NINT(fabs(115200./velocity));
  // if (ival < 2) ival=5000;
  // if (ival > 2) ival=5000;
  ival = 5000;
  if (axisNo_ == 1) ival=5000;
  if (axisNo_ == 2) ival=30000;
  if (axisNo_ == 3) ival=30000;
  if (axisNo_ == 4) ival=30000;
  sprintf(pC_->outString_, "ffast%d:%d", axisNo_, ival);
  status = pC_->writeController();

  // Send the acceleration
  // acceleration is in steps/sec/sec
  // SMC is programmed with Ramp Index (R) where:
  //   dval (steps/sec/sec) = 720,000/(256-R) */
  //   or R=256-(720,000/dval) */
  // ival = NINT(256-(720000./acceleration));
  // if (ival < 1) ival=20;
  // if (ival > 1) ival=20;
  ival = 20;
  if (axisNo_ == 1) ival=20;
  if (axisNo_ == 2) ival=80;
  if (axisNo_ == 3) ival=80;
  if (axisNo_ == 4) ival=80;
  sprintf(pC_->outString_, "acc%d:%d", axisNo_, ival);
  status = pC_->writeController();
  return status;
}


asynStatus SMC9300Axis::move(double position, int relative, double minVelocity, double maxVelocity, double acceleration)
{
  asynStatus status;
  // static const char *functionName = "SMC9300Axis::move";

  // status = sendAccelAndVelocity(acceleration, maxVelocity);

  if (relative) {
    sprintf(pC_->outString_, "move%d:%f", axisNo_, position / STEPS_PER_EGU);
  } else {
    sprintf(pC_->outString_, "goto%d:%f", axisNo_, position / STEPS_PER_EGU);
  }
  status = pC_->writeController();
  return status;
}

asynStatus SMC9300Axis::home(double minVelocity, double maxVelocity, double acceleration, int forwards)
{
  asynStatus status;
  if(forwards ==1){
    this->forward = true;
  }else{
    this->forward = false;
  }
  epicsThreadCreate("HuberHoming",
                    epicsThreadPriorityLow,
                    epicsThreadGetStackSize(epicsThreadStackMedium),
                    (EPICSTHREADFUNC)huberHomingThreadC, (void *)this);
  sprintf(pC_->outString_, "?s%d", axisNo_);
  status = pC_->writeController();
  return status;
}

static void huberHomingThreadC(void *pPvt){
  SMC9300Axis *axis = (SMC9300Axis*)pPvt;
  axis->homing();
}

asynStatus SMC9300Axis::homing()
{
  asynStatus status;
  char limitDirection, referenceDirection;
  epicsFloat64 homePos = 0.0;
  asynStatus lockStatus;
  int highLimit = 0, lowLimit = 0, atRest = 0;
  if(this->forward){
    limitDirection='+';
    referenceDirection='-';
  }else{
    limitDirection='-';
    referenceDirection='+';
  }

  
  lockStatus = pC_->lock();
  sprintf(pC_->outString_, "fast%d%c", axisNo_, limitDirection);
  status = pC_->writeController();
  while(highLimit == 0 && lowLimit == 0){
    pC_->getIntegerParam(axisNo_, pC_->motorStatusHighLimit_, &highLimit);
    pC_->getIntegerParam(axisNo_, pC_->motorStatusLowLimit_, &lowLimit);    
    lockStatus = pC_->unlock();
    epicsThreadSleep(1);
    lockStatus = pC_->lock();
  }
  sprintf(pC_->outString_, "eref%d%c", axisNo_, referenceDirection);
  status = pC_->writeController();
  do{
    
    pC_->unlock();
    epicsThreadSleep(1);
    pC_->lock();
    pC_->getIntegerParam(axisNo_, pC_->motorStatusDone_, &atRest);
  } while (atRest == 0);
  
  sprintf(pC_->outString_, "pos%d:%f", axisNo_, homePos);
  status = pC_->writeController();
  pC_->unlock();
  printf("Completed Home.\n");
  return status;
}

asynStatus SMC9300Axis::moveVelocity(double minVelocity, double maxVelocity, double acceleration)
{
  asynStatus status;
  static const char *functionName = "SMC9300Axis::moveVelocity";

  asynPrint(pasynUser_, ASYN_TRACE_FLOW,
    "%s: minVelocity=%f, maxVelocity=%f, acceleration=%f\n",
    functionName, minVelocity, maxVelocity, acceleration);
    
  // status = sendAccelAndVelocity(acceleration, maxVelocity);

  /* SMC-9300 does not have jog command. Move 1 million steps */
  if (maxVelocity > 0.) {
    /* This is a positive move in SMC9300 coordinates */
    sprintf(pC_->outString_, "move%d:0.1", axisNo_);
  } else {
      /* This is a negative move in SMC9300 coordinates */
      sprintf(pC_->outString_, "move%d:-0.1", axisNo_);
  }
  status = pC_->writeController();
  return status;
}

asynStatus SMC9300Axis::stop(double acceleration )
{
  asynStatus status;
  //static const char *functionName = "SMC9300Axis::stop";

  sprintf(pC_->outString_, "q%d", axisNo_);
  status = pC_->writeController();
  return status;
}

asynStatus SMC9300Axis::setPosition(double position)
{
  asynStatus status;
  //static const char *functionName = "SMC9300Axis::setPosition";

  sprintf(pC_->outString_, "pos%d:%f", axisNo_, position / STEPS_PER_EGU);
  status = pC_->writeController();
  return status;
}

asynStatus SMC9300Axis::setClosedLoop(bool closedLoop)
{
  asynStatus status;
  //static const char *functionName = "SMC9300Axis::setClosedLoop";

  sprintf(pC_->outString_, "ecl%d:%d", axisNo_, closedLoop ? 0:1);
  status = pC_->writeController();
  return status;
}

/** Polls the axis.
  * This function reads the motor position, the limit status, the home status, the moving status, 
  * and the drive power-on status. 
  * It calls setIntegerParam() and setDoubleParam() for each item that it polls,
  * and then calls callParamCallbacks() at the end.
  * \param[out] moving A flag that is set indicating that the axis is moving (true) or done (false). */
asynStatus SMC9300Axis::poll(bool *moving)
{ 
  int done;
  int driveOn;
  int limit;
  double position;
  asynStatus comStatus;

  // Read the current motor position
  sprintf(pC_->outString_, "?p%d", axisNo_);
  do  {
    comStatus = pC_->writeReadController();
  } while (atoi(&pC_->inString_[0]) != axisNo_);
  if (comStatus) goto skip;
  // The response string is of the form "1:1.234"
  position = NINT(atof(&pC_->inString_[2]) *  STEPS_PER_EGU);
  setDoubleParam(pC_->motorPosition_, position);

  // Read the current motor position
  sprintf(pC_->outString_, "?e%d", axisNo_);
  do  {
    comStatus = pC_->writeReadController();
  } while (atoi(&pC_->inString_[0]) != axisNo_);
  if (comStatus) goto skip;
  // The response string is of the form "1:1.234"
  position = NINT(atof(&pC_->inString_[2]) *  STEPS_PER_EGU);
  setDoubleParam(pC_->motorEncoderPosition_, position);
  if(this->previousPosition > position){
    setIntegerParam(pC_->motorStatusDirection_, 0);
  }else if(this->previousPosition < position){
    setIntegerParam(pC_->motorStatusDirection_, 1);
  }
  this->previousPosition = position;

  // Read the moving status of this motor
  sprintf(pC_->outString_, "?s%d", axisNo_);
  do  {
    comStatus = pC_->writeReadController();
  } while (atoi(&pC_->inString_[0]) != axisNo_);
  if (comStatus) goto skip;
  // The response string is of the form "1:131"
  done = atoi(&pC_->inString_[2])%2 ? 1:0;
  setIntegerParam(pC_->motorStatusDone_, done);
  *moving = done ? false:true;

  // Read the limit status
  // sprintf(pC_->outString_, "?s%d", axisNo_);
  // comStatus = pC_->writeReadController();
  // if (comStatus) goto skip;
  limit = (atoi(&pC_->inString_[2])/8)%2 ? 1:0;
  setIntegerParam(pC_->motorStatusHighLimit_, limit);
  limit = (atoi(&pC_->inString_[2])/4)%2 ? 1:0;
  setIntegerParam(pC_->motorStatusLowLimit_, limit);
  limit = 0;
  setIntegerParam(pC_->motorStatusAtHome_, limit);
  
  // Read the drive power on status
  // sprintf(pC_->outString_, "?s%d", axisNo_);
  // comStatus = pC_->writeReadController();
  // if (comStatus) goto skip;
  driveOn = (atoi(&pC_->inString_[2])/128)%2 ? 1:0;
  setIntegerParam(pC_->motorStatusPowerOn_, driveOn);
  setIntegerParam(pC_->motorStatusProblem_, 0);


  skip:
  setIntegerParam(pC_->motorStatusProblem_, comStatus ? 1:0);
  callParamCallbacks();
  return comStatus ? asynError : asynSuccess;
}

/** Code for iocsh registration */
static const iocshArg SMC9300CreateControllerArg0 = {"Port name", iocshArgString};
static const iocshArg SMC9300CreateControllerArg1 = {"SMC9300 port name", iocshArgString};
static const iocshArg SMC9300CreateControllerArg2 = {"Number of axes", iocshArgInt};
static const iocshArg SMC9300CreateControllerArg3 = {"Moving poll period (ms)", iocshArgInt};
static const iocshArg SMC9300CreateControllerArg4 = {"Idle poll period (ms)", iocshArgInt};
static const iocshArg * const SMC9300CreateControllerArgs[] = {&SMC9300CreateControllerArg0,
                                                             &SMC9300CreateControllerArg1,
                                                             &SMC9300CreateControllerArg2,
                                                             &SMC9300CreateControllerArg3,
                                                             &SMC9300CreateControllerArg4};
static const iocshFuncDef SMC9300CreateControllerDef = {"SMC9300CreateController", 5, SMC9300CreateControllerArgs};
static void SMC9300CreateContollerCallFunc(const iocshArgBuf *args)
{
  SMC9300CreateController(args[0].sval, args[1].sval, args[2].ival, args[3].ival, args[4].ival);
}

static void SMC9300Register(void)
{
  iocshRegister(&SMC9300CreateControllerDef, SMC9300CreateContollerCallFunc);
}

extern "C" {
epicsExportRegistrar(SMC9300Register);
}
