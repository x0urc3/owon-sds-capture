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
import logging
import struct
import time
from usb.core import USBError

from usb_interface import USBInterface
from constants import BULK_READ_ENDPOINT, CMD_ACQ


def acquire_raw_data(usb_interface: USBInterface, mode: str = 'bin') -> bytes:
    """
    Requests and reads a raw data block (e.g., waveform) from the oscilloscope.
    This function is a Python port of the logic in `owon_usb_read` from the C project.

    Args:
        usb_interface: An active USBInterface instance.
        mode: The type of data to acquire ('bin', 'bmp', etc.).

    Returns:
        A bytes object containing the complete raw data from the device.

    Raises:
        ValueError: If the acquisition mode is invalid.
        ConnectionError: If there's a problem communicating with the device.
    """
    try:
        start_command = CMD_ACQ[mode.upper()].value
    except KeyError:
        valid_modes = [m.name.lower() for m in CMD_ACQ]
        raise ValueError(f"Invalid acquisition mode '{mode}'. Valid modes are: {valid_modes}") from None

    logging.info(f"Sending data acquisition command: {start_command.decode()}")
    usb_interface.write(start_command)

    # Allow a moment for the device to process the command before reading the header
    time.sleep(0.1)

    try:
        # Read the 12-byte response header
        header_data = usb_interface.read(12, timeout=5000)
        logging.debug(f"Received response header: {header_data.hex(' ')}")

        # Parse the header: <III (3 unsigned ints, little-endian)
        # as seen in owon_get_response and owon_usb_read in the C code.
        length, unknown, flag = struct.unpack_from('<III', header_data)
        logging.info(f"Response: length={length}, unknown={unknown}, flag={flag}")

        if length == 0:
            logging.warning("Device reported a data length of 0. Aborting.")
            return b''

        # The C code suggests a flag > 128 indicates a multi-part transfer.
        is_multipart = flag > 128
        if is_multipart:
            logging.info("Multi-part transfer detected.")

        # Read the data block
        data_buffer = bytearray()
        total_read = 0

        while total_read < length:
            bytes_to_read = min(length - total_read, 131072) # Read in chunks
            try:
                chunk = usb_interface.read(bytes_to_read, timeout=10000)
                data_buffer.extend(chunk)
                total_read += len(chunk)
                logging.debug(f"Read {len(chunk)} bytes. Total read: {total_read}/{length}")
            except USBError as e:
                if e.errno == 110: # Timeout error
                    logging.warning("Read operation timed out. The device may have sent less data than expected.")
                    break
                else:
                    raise ConnectionError(f"USB error during data read: {e}") from e

        logging.info(f"Data acquisition complete. Total bytes received: {total_read}")

        # In multi-part transfers, there might be subsequent headers.
        # The C code has a loop for this, but for now, we assume one data block
        # per command, which covers the primary use case. A simple implementation
        # is more robust for the first pass.

        return bytes(data_buffer)

    except USBError as e:
        if e.errno == 110: # Timeout error on header read
            raise ConnectionError("Timeout waiting for device response header. Is the device ready?") from e
        else:
            raise ConnectionError(f"A USB error occurred: {e}") from e
    except Exception as e:
        raise IOError(f"An unexpected error occurred during data acquisition: {e}") from e
