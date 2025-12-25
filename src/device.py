"""
owon-sds-grok
Copyright (C) 2025 Khairulmizam <xource@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import struct
import logging
import constants
from usb_interface import USBInterface
from data_parser import OwonHeader
from acquisition import acquire_raw_data

class SDSDevice:
    """
    A high-level controller for the Owon PDS series oscilloscope.
    """

    def __init__(self):
        self.usb = USBInterface()

    def _send_command(self, command: bytes):
        """Helper to send a command and print status."""
        logging.info(f"Sending command: {command.hex(' ')}")
        self.usb.write(command)
        logging.debug("Command sent successfully.")

    def set_coupling(self, channel: constants.Channel, value: constants.Coupling):
        """Sets the coupling for a specific channel."""
        cmd = constants.TPL_COUPLING
        cmd[9] = channel.value
        cmd[11] = value.value
        self._send_command(bytes(cmd))

    def set_probe_scale(self, channel: constants.Channel, value: constants.ProbeScale):
        """Sets the probe scale for a specific channel."""
        cmd = constants.TPL_PROBE_SCALE
        cmd[9] = channel.value
        cmd[11] = value.value
        self._send_command(bytes(cmd))

    def set_volt_scale(self, channel: constants.Channel, value: constants.VoltScale):
        """Sets the voltage scale for a specific channel."""
        cmd = constants.TPL_VOLT_SCALE
        cmd[9] = channel.value
        cmd[11] = value.value
        self._send_command(bytes(cmd))

    def set_time_base(self, scale: constants.TimeBase):
        """Sets the horizontal timebase."""
        cmd = constants.TPL_TIMEBASE
        cmd[10] = scale.value
        self._send_command(bytes(cmd))

    def set_memory_depth(self, depth: constants.MemoryDepth):
        """Sets the acquisition memory depth."""
        cmd = constants.TPL_MEMORY_DEPTH
        cmd[9] = depth.value
        self._send_command(bytes(cmd))

    def set_trace_position(self, channel: constants.Channel, value: int):
        """Sets the vertical trace position."""
        if not -250 <= value <= 250:
            raise ValueError("Trace position must be between -250 and 250.")
        cmd = constants.TPL_TRACE_POS
        cmd[9] = channel.value
        # Pack as 32-bit signed little-endian integer
        struct.pack_into('<i', cmd, 11, value)
        self._send_command(bytes(cmd))

    def set_horizontal_trigger_position(self, value: int):
        """Sets the horizontal trigger position."""
        if not -10000 <= value <= 10000:
            raise ValueError("Horizontal trigger position must be between -10000 and 10000.")
        cmd = constants.TPL_HORIZ_TRIGGER_POS
        # Pack as 32-bit signed little-endian integer
        struct.pack_into('<i', cmd, 10, value)
        self._send_command(bytes(cmd))

    def set_acquisition_mode(self, mode: constants.AcquisitionMode):
        """Sets the acquisition mode (Sample or Peak Detect)."""
        if mode == constants.AcquisitionMode.AVERAGE:
            raise ValueError("For Average mode, use set_average_acquisition_mode()")
        cmd = constants.TPL_ACQU_MODE
        cmd[9] = mode.value
        self._send_command(bytes(cmd))

    def set_average_acquisition_mode(self, samples: constants.AverageSamples):
        """Sets the acquisition mode to Average with a specific sample count."""
        cmd = constants.TPL_ACQU_AVG_MODE
        cmd[10] = samples.value
        self._send_command(bytes(cmd))

    def force_trigger(self):
        """Forces a trigger event."""
        self._send_command(constants.CMD_FORCE_TRIGGER)

    def set_50pct_trigger(self):
        """Sets the trigger level to 50%."""
        self._send_command(constants.CMD_SET_50PCT_TRIGGER)

    def set_0_trigger(self):
        """Sets the trigger level to 0V."""
        self._send_command(constants.CMD_SET_0_TRIGGER)

    def autoset(self):
        """Performs an auto-set operation."""
        self._send_command(constants.CMD_AUTOSET)

    def self_calibrate(self):
        """Starts a self-calibration routine."""
        self._send_command(constants.CMD_SELF_CAL)

    def factory_reset(self):
        """Resets the device to factory defaults."""
        self._send_command(constants.CMD_FACTORY_RESET)

    def set_edge_trigger(
            self,
            channel: constants.Channel,
            mode: constants.TriggerMode,
            coupling: constants.TriggerCoupling,
            edge: constants.TriggerEdge,
            level: int,
            is_alt: bool = False):
        """
        Configures the edge trigger.

        :param channel: Trigger source channel.
        :param mode: Trigger mode (Auto, Normal, Once).
        :param coupling: Trigger coupling (DC, AC, HF, LF).
        :param edge: Trigger slope (Rising, Falling).
        :param level: Trigger level in millivolts.
        :param is_alt: Whether to use Alternate trigger mode.
        """
        if not -10000 <= level <= 10000:
            raise ValueError("Trigger level must be between -10000 and 10000.")

        cmd = constants.TPL_EDGE_TRIGGER
        trigger_type = 0x61 if is_alt else 0x73

        # Set trigger type (single/alt)
        cmd[9] = cmd[17] = cmd[25] = cmd[36] = cmd[44] = trigger_type
        # Set channel
        cmd[10] = cmd[18] = cmd[26] = cmd[37] = cmd[45] = channel.value
        # Set coupling
        cmd[13] = coupling.value
        # Set mode
        cmd[21] = mode.value
        # Set edge
        cmd[40] = edge.value
        # Set level (32-bit signed little-endian)
        struct.pack_into('<i', cmd, 48, level)

        self._send_command(bytes(cmd))

    def set_video_trigger(
            self,
            channel: constants.Channel,
            modulation: constants.VideoModulation,
            sync: constants.VideoSync,
            line: int = 1):
        """
        Configures the video trigger.

        :param channel: Trigger source channel.
        :param modulation: Video standard (NTSC, PAL, SECAM).
        :param sync: Sync type (Line, Field, etc.).
        :param line: Line number, if sync is LINE_NO.
        """
        if sync == constants.VideoSync.LINE_NO:
            if modulation == constants.VideoModulation.NTSC and not 1 <= line <= 525:
                raise ValueError("Line number for NTSC must be between 1 and 525.")
            if modulation != constants.VideoModulation.NTSC and not 1 <= line <= 625:
                raise ValueError("Line number for PAL/SECAM must be between 1 and 625.")

            cmd = constants.TPL_VIDEO_TRIGGER_LINE
            # Set channel
            cmd[10] = cmd[18] = cmd[30] = channel.value
            # Set modulation
            cmd[13] = modulation.value
            # Set line number (32-bit unsigned little-endian)
            struct.pack_into('<I', cmd, 22, line)
        else:
            cmd = constants.TPL_VIDEO_TRIGGER
            # Set channel
            cmd[10] = cmd[18] = cmd[26] = channel.value
            # Set modulation
            cmd[13] = modulation.value
            # Set sync type
            cmd[21] = sync.value

        self._send_command(bytes(cmd))

    def get_waveform(self, mode: str = 'bin') -> OwonHeader:
        """
        Acquires, parses, and returns the waveform data from the oscilloscope.

        Args:
            mode: The type of data to acquire ('bin' for waveform, 'bmp' for screenshot).

        Returns:
            An OwonHeader object containing the parsed header, channel metadata, and data points.
        """
        logging.info(f"Starting waveform acquisition in '{mode}' mode...")
        raw_data = acquire_raw_data(self.usb, mode)

        if not raw_data:
            logging.error("Failed to acquire waveform data (received empty response).")
            # Return an empty header object to avoid crashes
            return OwonHeader()

        logging.info("Raw data acquired. Parsing waveform data...")
        parsed_data = parse_waveform_data(raw_data)
        logging.info("Waveform data parsed successfully.")

        return parsed_data

    def __enter__(self):
        """Context manager entry point."""
        self.usb.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        self.usb.disconnect()
