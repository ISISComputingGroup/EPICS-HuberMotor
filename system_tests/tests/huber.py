import unittest
from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir, ProcServLauncher
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, parameterized_list

DEVICE_PREFIX = "HUBER_01"
EMULATOR_NAME = "huber"

MTR1 = "MTR0101"

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("HUBER"),
        "emulator": EMULATOR_NAME,
        "ioc_launcher_class": ProcServLauncher,
        "pv_for_existence": f"{MTR1}",
        "custom_prefix": "MOT",
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
        self.ca.assert_that_pv_is(f"{MTR1}.RBV", 0, timeout=30)  # ensure that position actually set.

    def test_GIVEN_move_THEN_motor_moves_to_position_over_time(self):
        self.ca.set_pv_value(MTR1, 1000)
        self.ca.assert_that_pv_is_not_number(f"{MTR1}.RBV", 1000, 1)
        self.ca.assert_that_pv_is(f"{MTR1}.MOVN", 1)
        self.ca.assert_that_pv_is_number(f"{MTR1}.RBV", 1000, 1, timeout=30)

    def test_GIVEN_move_to_limit_positive_THEN_limit_tripped(self):
        self._lewis.backdoor_set_on_device("positive_limit", 100)
        self.ca.set_pv_value(MTR1, 100)
        self.ca.assert_that_pv_is(f"{MTR1}.MOVN", 1, timeout=100)
        self.ca.assert_that_pv_is(f"{MTR1}.HLS", 1, timeout=30)

    def test_GIVEN_move_to_limit_negative_THEN_limit_tripped(self):
        self._lewis.backdoor_set_on_device("negative_limit", -100)
        self.ca.set_pv_value(MTR1, -100)
        self.ca.assert_that_pv_is(f"{MTR1}.MOVN", 1, timeout=100)
        self.ca.assert_that_pv_is(f"{MTR1}.LLS", 1, timeout=30)

    def test_GIVEN_move_AND_stop_THEN_stop(self):
        self.ca.set_pv_value(MTR1, 1000)
        self._lewis.backdoor_set_on_device("initial_speed", 1)
        self.ca.assert_that_pv_is(f"{MTR1}.DMOV", 1, timeout=30)
        self.ca.set_pv_value(f"{MTR1}.STOP", 1)
        self.ca.assert_that_pv_is(f"{MTR1}.DMOV", 1)
        self.ca.assert_that_pv_is_not(MTR1, float(0))

    def test_GIVEN_home_forwards_THEN_motor_moves_to_limit_at_fast_speed_THEN_motor_moves_to_eref_AND_sets_position(self):
        self._lewis.backdoor_set_on_device("reference_point", 0)
        self.ca.set_pv_value(f"{MTR1}.HOMF", 1)
        self.ca.assert_that_pv_is_number(f"{MTR1}.RBV", 1000, 1, timeout=30)
        self.ca.assert_that_pv_is_not_number(f"{MTR1}.RBV", 1000, 1, timeout=30)
        self.ca.assert_that_pv_is_number(f"{MTR1}.RBV", 0, 1, timeout=30)
        self.ca.assert_that_pv_is_number(f"{MTR1}.VAL", 0, 1, timeout=30)

    def test_GIVEN_home_reverse_THEN_motor_moves_to_limit_at_fast_speed_THEN_motor_moves_to_eref_AND_sets_position(self):
        self._lewis.backdoor_set_on_device("reference_point", 0)
        self.ca.set_pv_value(f"{MTR1}.HOMR", 1)
        self.ca.assert_that_pv_is_number(f"{MTR1}.RBV", -1000, 1, timeout=30)
        self.ca.assert_that_pv_is_not_number(f"{MTR1}.RBV", -1000, 1, timeout=30)
        self.ca.assert_that_pv_is_number(f"{MTR1}.RBV", 0, 1, timeout=30)
        self.ca.assert_that_pv_is_number(f"{MTR1}.VAL", 0, 1, timeout=30)

    def test_GIVEN_home_reverse_THEN_motor_moves_to_limit_at_fast_speed_THEN_stop_THEN_motor_STOPS(self):
        self._lewis.backdoor_set_on_device("reference_point", 0)
        self._lewis.backdoor_set_on_device("high_speed", 5)
        self.ca.set_pv_value(f"{MTR1}.HOMR", 1)
        self.ca.assert_that_pv_is_not_number(f"{MTR1}.RBV", 0, 1, timeout=30)
        self.ca.set_pv_value(f"{MTR1}.STOP", 1)
        self.ca.assert_that_pv_is(f"{MTR1}.DMOV", 1)
        self.ca.assert_that_pv_is_not_number(f"{MTR1}.RBV", -1000, 1, timeout=30)

    def test_GIVEN_home_reverse_THEN_motor_moves_to_limit_at_fast_speed_THEN_THEN_STOP(self):
        self._lewis.backdoor_set_on_device("reference_point", 0)
        self._lewis.backdoor_set_on_device("high_speed", 5)
        self.ca.set_pv_value(f"{MTR1}.HOMR", 1)
        self.ca.assert_that_pv_is_number(f"{MTR1}.RBV", -1000, 1, timeout=30)
        self.ca.assert_that_pv_is_not_number(f"{MTR1}.RBV", -1000, 1, timeout=30)
        self.ca.set_pv_value(f"{MTR1}.STOP", 1)
        self.ca.assert_that_pv_is(f"{MTR1}.DMOV", 1)
        self.ca.assert_that_pv_is_not_number(f"{MTR1}.RBV", 0, 1, timeout=30)

    def test_GIVEN_setpoint_WHEN_monitoring_moving_THEN_moving_changes_once(self):
        with self.ca.assert_that_pv_monitor_gets_values(f"{MTR1}.MOVN", [0,1,0]):
            self.ca.set_pv_value(MTR1, 1)
