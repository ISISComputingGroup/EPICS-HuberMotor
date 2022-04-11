from lewis.core.statemachine import State
from lewis.core import approaches


class MovingState(State):
    def on_entry(self, dt):
        self.context.current_speed = self.initial_speed

    def on_exit(self, dt):
        self.context.current_speed = 0

    def in_state(self, dt):
        old_position = self._context.position
        if self.context.current_speed + self.context.acceleration < self.context.high_speed:
            self.context.current_speed = self.context.current_speed + self.context.acceleration
        else:
            self.context.current_speed = self.context.high_speed

        self._context.position = approaches.linear(old_position, self._context.target,
                                                   self._context.speed, dt)
        self.log.info('Moved position (%s -> %s), target=%s, speed=%s', old_position,
                      self._context.position, self._context.target, self._context.speed)