/*
FILENAME...   SMC9300Driver.h
USAGE...      Motor driver support for the HUBER SMC9300 controller.

Yang Dongliang
March 1, 2020

*/

#include "asynMotorController.h"
#include "asynMotorAxis.h"

#define MAX_SMC9300_AXES 3

// No controller-specific parameters yet
#define NUM_SMC9300_PARAMS 0  

class epicsShareClass SMC9300Axis : public asynMotorAxis
{
public:
  /* These are the methods we override from the base class */
  SMC9300Axis(class SMC9300Controller *pC, int axis);
  void report(FILE *fp, int level);
  asynStatus move(double position, int relative, double min_velocity, double max_velocity, double acceleration);
  asynStatus moveVelocity(double min_velocity, double max_velocity, double acceleration);
  asynStatus home(double min_velocity, double max_velocity, double acceleration, int forwards);
  asynStatus stop(double acceleration);
  asynStatus poll(bool *moving);
  asynStatus setPosition(double position);
  asynStatus setClosedLoop(bool closedLoop);
  asynStatus homing();

private:
  SMC9300Controller *pC_;          /**< Pointer to the asynMotorController to which this axis belongs.
                                   *   Abbreviated because it is used very frequently */
  double previousPosition;            /** The position of the axis on its last poll, used to calculate direction. */
  asynStatus sendAccelAndVelocity(double accel, double velocity);
  bool forward;
  bool stopStatus;
  
  
friend class SMC9300Controller;
};

class epicsShareClass SMC9300Controller : public asynMotorController {
public:
  SMC9300Controller(const char *portName, const char *SMC9300PortName, int numAxes, double movingPollPeriod, double idlePollPeriod);

  void report(FILE *fp, int level);
  SMC9300Axis* getAxis(asynUser *pasynUser);
  SMC9300Axis* getAxis(int axisNo);

friend class SMC9300Axis;
};
