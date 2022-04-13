from lewis.adapters.stream import StreamInterface, Cmd
from lewis.utils.command_builder import CmdBuilder
from lewis.core.logging import has_log



@has_log
class HuberStreamInterface(StreamInterface):

    def __init__(self):
        super(HuberStreamInterface, self).__init__()
        # Commands that we expect via serial during normal operation
        self.commands = {
            CmdBuilder(self.set_high_speed).escape("ffast").int().escape(":").float().eos().build(),  # Set high speed
            CmdBuilder(self.set_accel).escape("acc").int().escape(":").float().eos().build(),  # Set acceleration
            CmdBuilder(self.move).escape("move").int().escape(":").float().eos().build,  # move a set distance
            CmdBuilder(self.goto).escape("goto").int().escape(":").float().eos().build,  # move to a set point
            CmdBuilder(self.get_position).escape("?p").int(),  # query the current position of the motor
            CmdBuilder(self.get_position).escape("?e").int(),  # query the current position of the encoder
            CmdBuilder(self.get_position).escape("?e").int(),  # query the current operating state
            CmdBuilder(self.stop).escape("q").int(),  # quit current positioning task.

        }
    in_terminator = "\r"
    out_terminator = "\r"

    def handle_error(self, request, error):
        """
        If command is not recognised print and error

        Args:
            request: requested string
            error: problem

        """
        self.log.error("An error occurred at request " + repr(request) + ": " + repr(error))

    def set_high_speed(self, axis, velocity):
        """

        :param axis: The Axis to set the velocity on.
        :param velocity: The Velocity to set.
        """
        self.device.high_speed = velocity

    def set_accel(self, axis, accel):
        """

        :param axis: The Axis to set the velocity on.
        :param accel: The acceleration to set.
        """
        self.device.high_speed = accel

    def move(self, axis, distance):
        """

        :param axis: The axis to move.
        :param distance: The distance to move from the current point.
        """
        self.device.target = self.device.position + distance

    def goto(self, axis, new_position):
        """

        :param axis: The axis to move.
        :param new_position: The position to move to.
        """
        self.device.target = new_position

    def stop(self, axis):
        """

        :param axis: The Axis to stop
        """
        self.device.stop()

    def get_position(self, axis):
        """

        :param axis: The Axis to get the position of.
        """
        return f"{axis}:{self.device.position}"

    def get_state(self, axis):
        """

        :param axis: The Axis to get the position of.
        """
        return f"{axis}:{int(self.device.state()=='idle')}{0}{int(self.device.negative_limit_tripped)}" \
               f"{int(self.device.positive_limit_tripped)}{0}{0}{int(self.device.program_execution)}" \
               f"{int(self.device.state()=='idle')}{0}{0}{1}"
