from lewis.devices import StateMachineDevice

from lewis.core.statemachine import State


from collections import OrderedDict

from Huber.states import MovingState


class SimulatedHuber(StateMachineDevice):
    def _initialize_data(self):
        self.position = 0.0
        self.target = 0.0
        self.initial_speed = 2.0
        self.current_speed = 0
        self.high_speed = 5
        self.number_axis = 3
        self.acceleration = 1
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
            (('idle', 'moving'), lambda: self.position != self.target),
            (('moving', 'idle'), lambda: self.position == self.target)])

    @property
    def state(self):
        return self._csm.state

    @property
    def target(self):
        return self.target

    @target.setter
    def target(self, new_target):
        self.target = new_target

    def stop(self):
        self.target = self.position

        self.log.info('Stopping movement after user request.')

        return self.target, self.position
