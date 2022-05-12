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
            CmdBuilder(self.move_high_speed).escape("fast").int().char().eos().build(),  # travel at speed
            CmdBuilder(self.set_accel).escape("acc").int().escape(":").float().eos().build(),  # Set acceleration
            CmdBuilder(self.move).escape("move").int().escape(":").float().eos().build(),  # move a set distance
            CmdBuilder(self.goto).escape("goto").int().escape(":").float().eos().build(),  # move to a set point
            CmdBuilder(self.get_position).escape("?p").int().eos().build(),  # query the current position of the motor
            CmdBuilder(self.get_position).escape("?e").int().eos().build(),  # query the current position of the encoder
            CmdBuilder(self.get_state).escape("?s").int().eos().build(),  # query the current operating state
            CmdBuilder(self.stop).escape("q").int().eos().build(),  # quit current positioning task.
            CmdBuilder(self.goto_reference).escape("eref").int().char().eos().build(),
            CmdBuilder(self.set_position).escape("pos").int().escape(":").float().eos().build(),  # set the position
            # search for the reference position

        }
    in_terminator = "\r"
    out_terminator = "\r\n"

    def set_position(self, axis, position):
        self.device.position = position
        self.device.set_target(position)

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

    def move_high_speed(self, axis, direction):
        """

        :param axis: The Axis to move
        :param direction: The direction to move int
        """
        self.device.move_high_speed = True
        if direction == "+":
            self.device.set_target(self.device.positive_limit)
        else:
            self.device.set_target(self.device.negative_limit)

    def set_accel(self, axis, accel):
        """

        :param axis: The Axis to set the acceleration on.
        :param accel: The acceleration to set.
        """
        self.device.high_speed = accel

    def move(self, axis, distance):
        """

        :param axis: The axis to move.
        :param distance: The distance to move from the current point.
        """
        self.device.move_high_speed = False
        self.device.set_target(self.device.position() + distance)

    def goto(self, axis, new_position):
        """

        :param axis: The axis to move.
        :param new_position: The position to move to.
        """
        self.device.move_high_speed = False
        self.device.set_target(new_position)

    def stop(self, axis):
        """

        :param axis: The Axis to stop
        """
        self.device.stop()

    def get_position(self, axis):
        """

        :param axis: The Axis to get the position of.

        Returs: a string of form axis:position
        """
        return f"{axis}:{self.device.position}"

    def goto_reference(self, axis, direction):
        self.device.move_high_speed = True
        self.device.set_target(0)

    def get_state(self, axis):
        """

        :param axis: The Axis to get the position of.

        returns: an int where each bit represents a different part of the status, in little endian
            bit0: 1 axis ready (i.e. axis stopped)
            bit1: 2 reference position installed
            bit2: 4 end/limit switch EL- active
            bit3: 8 end/limit switch EL+ active
            bit4: 16 reserved
            bit5: 32 reserved
            bit6: 64 program execution in progress
            bit7: 128 controller ready (i.e. idle, all axes stopped)
            bit8: 256 oscillation in progress
            bit9: 512 oscillation positioning error (encoder)
            bit10: 1024 encoder reference (index) installed
        """
        bit_string = f"{1}{0}{0}{int(self.device.state() == 'idle')}{int(self.device.program_execution)}" \
                     f"{0}{0}{int(self.device.positive_limit_tripped)}{int(self.device.negative_limit_tripped)}" \
                     f"{0}{int(self.device.state() == 'idle')}"
        return f"{axis}:{int(bit_string, 2)}"
