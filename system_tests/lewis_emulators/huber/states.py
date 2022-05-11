from lewis.core.statemachine import State
from lewis.core import approaches


class MovingState(State):
    def on_entry(self, dt):
        self._context.current_speed = self._context.initial_speed

    def on_exit(self, dt):
        self._context.current_speed = 0

    def in_state(self, dt):
        old_position = self._context.position
        if self._context.positive_limit_tripped and self._context.target >= old_position:
            self._context.set_target(self._context.position)
            return
        if self._context.negative_limit_tripped and self._context.target <= old_position:
            self._context.set_target(self._context.position)
            return
        self._context.positive_limit_tripped = False
        self._context.negative_limit_tripped = False
        if self._context.current_speed + self._context.acceleration < self._context.high_speed:
            self._context.current_speed = self._context.current_speed + self._context.acceleration
        else:
            self._context.current_speed = self._context.high_speed

        self._context.position = approaches.linear(old_position, self._context.target(),
                                                   self._context.current_speed, dt)
        if self._context.negative_limit >= self._context.position:
            self._context.positive_limit_tripped = True
        if self._context.position >= self._context.positive_limit:
            self._context.negative_limit_tripped = True

        self.log.info('Moved position (%s -> %s), target=%s, speed=%s', old_position,
                      self._context.position, self._context.target(), self._context.current_speed)

