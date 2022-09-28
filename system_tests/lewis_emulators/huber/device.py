from lewis.devices import StateMachineDevice
from lewis.core.statemachine import State
from collections import OrderedDict
from .states import MovingState, HighSpeedState


class SimulatedHuber(StateMachineDevice):
    def _initialize_data(self):
        """
        Initialize all of the device's attributes.
        """
        self.position = 0.0
        self._target = 0.0
        self.initial_speed = 2.0
        self.current_speed = 0
        self.high_speed = 1000
        self.high_speed_move = False
        self.number_axis = 3
        self.acceleration = 0.01
        self.positive_limit = 100000
        self.negative_limit = -100000
        self.program_execution = False
        self.reference_point = 0

    def _get_state_handlers(self):
        return {
            'idle': State(),
            'moving': MovingState(),
            'high_speed': HighSpeedState(),
        }

    def _get_initial_state(self):
        return 'idle'

    def _get_transition_handlers(self):
        return OrderedDict([
            (('idle', 'moving'), lambda: self.position != self._target and not self.high_speed_move),
            (('idle', 'high_speed'), lambda: self.position != self._target and self.high_speed_move),
            (('moving', 'idle'), lambda: self.position == self._target),
            (('high_speed', 'idle'), lambda: self.position == self._target)])

    def state(self):
        return self._csm.state

    def target(self):
        return self._target

    def set_target(self, new_target):
        self.log.error(f"setting target to {new_target}, fast move is {self.high_speed_move}")
        self._target = new_target

    def stop(self):
        self._target = self.position
        self.log.info('Stopping movement after user request.')

        return self.target, self.position

    def positive_limit_tripped(self):
        return self.position >= self.positive_limit

    def negative_limit_tripped(self):
        return self.negative_limit >= self.position
