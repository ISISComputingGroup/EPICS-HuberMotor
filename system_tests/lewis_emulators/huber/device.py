from lewis.devices import StateMachineDevice

from lewis.core.statemachine import State


from collections import OrderedDict

from .states import MovingState

from sys import maxsize


class SimulatedHuber(StateMachineDevice):
    def _initialize_data(self):
        """
        Initialize all of the device's attributes.
        """
        self.position = 0.0
        self._target = 0.0
        self.initial_speed = 2.0
        self.current_speed = 0
        self.high_speed = 5
        self.number_axis = 3
        self.acceleration = 1
        self.positive_limit = maxsize
        self.negative_limit = -maxsize
        self.positive_limit_tripped = False
        self.negative_limit_tripped = False
        self.program_execution = False

    def _get_state_handlers(self):
        return {
            'idle': State(),
            'moving': MovingState()
        }

    def _get_initial_state(self):
        return 'idle'

    def _get_transition_handlers(self):
        return OrderedDict([
            (('idle', 'moving'), lambda: self.position != self._target),
            (('moving', 'idle'), lambda: self.position == self._target)])

    def state(self):
        return self._csm.state

    def target(self):
        return self._target

    def set_target(self, new_target):
        self._target = new_target

    def stop(self):
        self._target = self.position

        self.log.info('Stopping movement after user request.')

        return self.target, self.position
