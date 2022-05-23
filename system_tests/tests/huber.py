import unittest
from parameterized import parameterized
from random import randint
from time import sleep
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list

DEVICE_PREFIX = "HUBER_01"
EMULATOR_NAME = "huber"

MTR1 = "MTR0101"
MTR_DESC = f"{MTR1}.DESC"
MTR_JOG = f"{MTR1}.JOGF"
MTR_HLM = f"{MTR1}.HLM"
MTR_STOP = f"{MTR1}.STOP"
MTR_MOVN = f"{MTR1}.MOVN"
MTR_RBV = f"{MTR1}.RBV"
MTR_MRES = f"{MTR1}.MRES"
MTR_NAME = "Test"

POLL_RATE = 1

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HUBER"),
        "emulator": EMULATOR_NAME,
        "ioc_launcher_class": ProcServLauncher,
        "macros": {
            "MTRCTRL": "01",
            "AXIS1": "yes",
            "NUMBERAXES": "1",
        },
    },
]


TEST_MODES = [
    TestModes.DEVSIM,
]


class HUBERTests(unittest.TestCase):
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("huber", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix="MOT", default_timeout=15)
        self.ca.set_pv_value(MTR1, 0)
        self._lewis.backdoor_set_on_device("position", 0)
        self._lewis.backdoor_set_on_device("negative_limit", -1000)
        self._lewis.backdoor_set_on_device("positive_limit", 1000)
        self._lewis.backdoor_set_on_device("initial_speed", 0.01)
        self._lewis.backdoor_set_on_device("high_speed", 10)

    def test_GIVEN_move_THEN_motor_moves_to_position_over_time(self):
        self.ca.set_pv_value(MTR1, 1000)
        self.ca.assert_that_pv_is_not(f"{MTR1}.RBV", 1000)
        self.ca.assert_that_pv_is(f"{MTR1}.MOVN", 1)
        while self.ca.get_pv_value(f"{MTR1}.DMOV") == 1:
            print(self._lewis.backdoor_get_from_device("position"))
            sleep(0.01)
        self.ca.assert_that_pv_is(f"{MTR1}.RBV", float(1000))

    def test_GIVEN_move_to_limit_positive_THEN_limit_tripped(self):
        self._lewis.backdoor_set_on_device("positive_limit", 100)
        self.ca.set_pv_value(MTR1, 100)
        self.ca.assert_that_pv_is(f"{MTR1}.MOVN", 1)
        while self.ca.get_pv_value(f"{MTR1}.MOVN") == 1:
            sleep(0.01)
        self.ca.assert_that_pv_is(f"{MTR1}.HLS", 1)

    def test_GIVEN_move_to_limit_negative_THEN_limit_tripped(self):
        self._lewis.backdoor_set_on_device("negative_limit", -100)
        self.ca.set_pv_value(MTR1, -100)
        self.ca.assert_that_pv_is(f"{MTR1}.MOVN", 1)
        while self.ca.get_pv_value(f"{MTR1}.MOVN") == 1:
            sleep(0.01)
        self.ca.assert_that_pv_is(f"{MTR1}.LLS", 1)

    def test_GIVEN_move_AND_stop_THEN_stop(self):
        self.ca.set_pv_value(MTR1, 1000)
        self._lewis.backdoor_set_on_device("initial_speed", 1)
        self.ca.assert_that_pv_is(f"{MTR1}.DMOV", 1)
        sleep(0.1)
        self.ca.set_pv_value(f"{MTR1}.STOP", 1)
        self.ca.assert_that_pv_is(f"{MTR1}.DMOV", 1)
        self.ca.assert_that_pv_is_not(MTR1, float(0))

    def test_GIVEN_home_forwards_THEN_motor_moves_to_limit_at_fast_speed_THEN_motor_moves_to_eref_AND_sets_position(self):
        home = randint(-99, 99)
        self._lewis.backdoor_set_on_device("reference_point", home)
        self.ca.set_pv_value(f"{MTR1}.HOMF", 1)
        while (self.ca.get_pv_value(f"{MTR1}.HLS") == 0) and (self.ca.get_pv_value(f"{MTR1}.LLS") == 0):
            sleep(0.01)
        self.ca.assert_that_pv_is(f"{MTR1}.RBV", 1000)
        while self._lewis.backdoor_get_from_device("state") == "idle":
            sleep(0.01)
        self.ca.assert_that_pv_is_not(f"{MTR1}.RBV", 1000)
        while self.ca.get_pv_value(f"{MTR1}.DMOV") == 1:
            sleep(0.01)
        self.ca.assert_that_pv_is(f"{MTR1}.RBV", 0)

    def test_GIVEN_home_reverse_THEN_motor_moves_to_limit_at_fast_speed_THEN_motor_moves_to_eref_AND_sets_position(self):
        home = randint(-99, 99)
        self._lewis.backdoor_set_on_device("reference_point", home)
        self.ca.set_pv_value(f"{MTR1}.HOMR", 1)
        while (self.ca.get_pv_value(f"{MTR1}.HLS") == 0) and (self.ca.get_pv_value(f"{MTR1}.LLS") == 0):
            sleep(0.01)
        self.ca.assert_that_pv_is(f"{MTR1}.RBV", -1000)
        while self._lewis.backdoor_get_from_device("state") == "idle":
            sleep(0.01)
        self.ca.assert_that_pv_is_not(f"{MTR1}.RBV", -1000)
        while self.ca.get_pv_value(f"{MTR1}.DMOV") == 1:
            sleep(0.01)
        self.ca.assert_that_pv_is(f"{MTR1}.RBV", 0)

