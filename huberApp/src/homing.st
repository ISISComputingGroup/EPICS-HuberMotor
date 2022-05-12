program homing("MOTPV=xxx,MODE,AXIS,DEBUG,HOME")

#include "seqPVmacros.h"

%% #include "string.h"
%% #include "errlog.h"
%% #include "float.h"
%% #include "stdlib.h"
%% #include "math.h"

char* SNLtaskName;

PV(int, home_forward_pv, "{MOTPV}.HOMF", Monitor);
PV(int, home_reverse_pv, "{MOTPV}.HOMR", Monitor);
PV(int, movable, "{MOTPV}.DMOV", Monitor);
PV(int, high_limit_tripped, "{MOTPV}.HLS", Monitor);
PV(int, low_limit_tripped, "{MOTPV}.LLS", Monitor);

int axis;
int debug;
double home;
ss motor
{
    state init
    {
        when ()
        {
            axis = atoi(macValueGet("AXIS"));
            debug = atoi(macValueGet("DEBUG"));
            home = atof(macValueGet("HOME"));
            errlogSevPrintf(errlogInfo, "Sequencer: Homing mode for axis %i to %f\n", axis, home);
      
            if (debug) {
                errlogSevPrintf(errlogInfo, "Sequencer: Debug mode ON\n");
            } 
        } state ready
    }

    state ready
    {
        when (home_reverse_pv==1)
        {
            if (debug) {
                errlogSevPrintf(errlogInfo, "Sequencer: axis %i: FROM ready TO reverse_home_requested\n", axis);
            }
        } state reverse_home_requested

        when (home_forward_pv==1)
        {
            if (debug) {
                errlogSevPrintf(errlogInfo, "Sequencer: axis %i: FROM ready TO forward_home_requested\n", axis);
            }
        } state forward_home_requested
    }

    state forward_home_requested
    {
        when ()
        {
            sprintf(pC_->outString_, "fast%d+", axis);
            status = pC_->writeController();

            if (debug) {
                errlogSevPrintf(errlogInfo, "Sequencer: axis %i: FROM forward_home_requestd TO await_positive_limit\n", axis);
            } 
        } state await_positive_limit
        
    }

    state await_positive_limit
    {
        when (high_limit_tripped=1)
        {
            sprintf(pC_->outString_, "eref%d-", axis);
            status = pC_->writeController();

            if (debug) {
                errlogSevPrintf(errlogInfo, "Sequencer: axis %i: FROM await_positive_limit TO set_position\n", axis);
            }  
        } state set_position
    } 

    state reverse_home_requested
    {
        when ()
        {
            sprintf(pC_->outString_, "fast%d-", axis);
            status = pC_->writeController();

            if (debug) {
                errlogSevPrintf(errlogInfo, "Sequencer: axis %i: FROM reverse_home_requestd TO await_negative_limit\n", axis);
            } 
        } state await_negative_limit
        
    }

    state await_negative_limit
    {
        when (low_limit_tripped=1)
        {
            sprintf(pC_->outString_, "eref%d+", axis);
            status = pC_->writeController();

            if (debug) {
                errlogSevPrintf(errlogInfo, "Sequencer: axis %i: FROM await_negative_limit TO set_position\n", axis);
            }     
        } state set_position
    } 

    state set_position
    {
        when (movable=1)
        {
            sprintf(pC_->outString_, "pos%d:%f", axis, home);
            status = pC_->writeController();

            if (debug) {
                errlogSevPrintf(errlogInfo, "Sequencer: axis %i: FROM set_position TO ready\n", axis);
            } 
        } state ready
    }
}



