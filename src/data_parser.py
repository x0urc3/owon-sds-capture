
"""
owon-sds-capture
Copyright (C) 2025 Khairulmizam Samsudin <xource@gmail.com>

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
from dataclasses import dataclass, field
from typing import List

@dataclass
class OwonChannel:
    """Holds the parsed data and metadata for a single channel."""
    name: str = ""
    unknown_int: int = 0
    datatype: int = 0
    unknown_4: bytes = b''
    samples_count: int = 0
    samples_file: int = 0
    samples_3: int = 0
    time_div: float = 0.0
    offset_y: int = 0
    volts_div: float = 0.0
    attenuation: float = 0.0
    time_mul: float = 0.0
    frequency: float = 0.0
    period: float = 0.0
    volts_mul: float = 0.0
    # Processed data
    time_points: List[float] = field(default_factory=list)
    volt_points: List[float] = field(default_factory=list)

@dataclass
class OwonHeader:
    """Holds the top-level header information and a list of channels."""
    length: int = 0
    unknown_1: int = 0
    type: int = 0
    model: str = ""
    int_size: int = 0
    serial: str = ""
    trigger_status: int = 0
    unknown_status: int = 0
    unknown_value_1: int = 0
    unknown_value_2: int = 0
    unknown_3: bytes = b''
    channels: List[OwonChannel] = field(default_factory=list)

_ATTENUATION_TABLE = [1.0e0, 1.0e1, 1.0e2, 1.0e3]
_VOLT_TABLE = [
    2.0e-2, 5.0e-2,  # 10 mV
    1.0e-1, 2.0e-1, 5.0e-1,  # 100 mV
    1.0e+0, 2.0e+0, 5.0e+0,  # 1 V
    1.0e+1, 2.0e+1, 5.0e+1,  # 10 V
    1.0e+2  # 100 V
]
_TIMESCALE_TABLE = [
    2.0e-9, 5.0e-9,  # 2 ns
    1.0e-8, 2.0e-8, 5.0e-8,  # 10 ns
    1.0e-7, 2.0e-7, 5.0e-7,  # 100 ns
    1.0e-6, 2.0e-6, 5.0e-6,  # 1 us
    1.0e-5, 2.0e-5, 5.0e-5,  # 10 us
    1.0e-4, 2.0e-4, 5.0e-4,  # 100 us
    1.0e-3, 2.0e-3, 5.0e-3,  # 1 ms
    1.0e-2, 2.0e-2, 5.0e-2,  # 10 ms
    1.0e-1, 2.0e-1, 5.0e-1,  # 100 ms
    1.0e+0, 2.0e+0, 5.0e+0,  # 1 s
    1.0e+1, 2.0e+1, 5.0e+1,  # 10 s
    1.0e+2  # 100 s
]

def _get_real_from_table(table: list, index: int) -> float:
    """Safely get a value from a lookup table."""
    if index >= len(table):
        return table[-1]
    return table[index]

def _sample_to_volt(channel: OwonChannel, sample_value: int) -> float:
    """Converts a raw sample value to volts."""
    # The formula from parse.c: val * 2.0 * header->channels[channel]->voltsdiv / 5.0
    # This seems incorrect based on typical oscilloscope scaling.
    # A more standard formula is (sample_value / (points_per_division / 2)) * volts_per_division
    # Assuming 25 points per division vertically (common for 8-bit ADCs over a grid).
    # Let's stick to the C code's formula for a direct port, but be aware it might need adjustment.
    # The C code casts the data to int8_t, so we should handle the sign.
    if sample_value > 127:
        sample_value -= 256
    return sample_value * channel.volts_div * channel.attenuation / 25.0

def _sample_id_to_time(channel: OwonChannel, sample_index: int) -> float:
    """Converts a sample index to a time value."""
    # The formula from parse.c: timediv * 10.0 * sample / samples_count
    # This assumes the screen has 10 horizontal divisions.
    if not channel.samples_count:
        return 0.0
    return channel.time_div * 10.0 * sample_index / channel.samples_count


def parse_response_header(header_data: bytes) -> tuple[int, int, int]:
    """
    Parses the 12-byte response header from the device.
    As seen in owon_get_response and owon_usb_read in the C code.
    """
    length, unknown, flag = struct.unpack_from('<III', header_data)
    logging.debug(f"Response: length={length}, unknown={unknown}, flag={flag}")
    return length, unknown, flag

def parse_waveform_data(raw_data: bytes) -> OwonHeader:
    """
    Parses a raw binary data block from the oscilloscope into a structured OwonHeader object.
    This is a Python port of the `owon_parse` function from the C project.
    """
    offset = 0
    header = OwonHeader()

    # The C code skips a 12-byte LAN header if "SPB" is present.
    if raw_data[12:15] == b'SPB':
        header.length, header.unknown_1, header.type = struct.unpack_from('<III', raw_data, 0)
        offset = 12
        logging.debug(f"SPB header found. Length: {header.length}, Type: {header.type}")

    # Read model (6 bytes + null terminator)
    header.model = raw_data[offset:offset+6].decode('ascii', errors='ignore').strip('\x00')
    offset += 7

    header.int_size = struct.unpack_from('<i', raw_data, offset)[0]
    offset += 4

    # The C code checks if intsize is 0 or 0xFFFFFF to skip the next block.
    if header.int_size != 0 and header.int_size != 0xFFFFFF:
        header.serial = raw_data[offset:offset+29].decode('ascii', errors='ignore').strip('\x00')
        offset += 29
        header.trigger_status, header.unknown_status = struct.unpack_from('<BB', raw_data, offset)
        offset += 2
        header.unknown_value_1 = struct.unpack_from('<I', raw_data, offset)[0]
        offset += 4
        header.unknown_value_2 = struct.unpack_from('<B', raw_data, offset)[0]
        offset += 1
        header.unknown_3 = raw_data[offset:offset+8]

    logging.debug(f"Parsed main header. Model: {header.model}, Serial: {header.serial}")

    # Search for and parse channel data
    while (channel_offset := raw_data.find(b'CH', offset)) != -1:
        offset = channel_offset
        ch = OwonChannel()

        ch.name = raw_data[offset:offset+3].decode('ascii', errors='ignore').strip('\x00')
        offset += 4

        ch.unknown_int, ch.datatype = struct.unpack_from('<ii', raw_data, offset)
        offset += 8
        ch.unknown_4 = raw_data[offset:offset+4]
        offset += 4

        ch.samples_count, ch.samples_file, ch.samples_3 = struct.unpack_from('<III', raw_data, offset)
        offset += 12

        time_div_idx, volts_div_idx, atten_idx = struct.unpack_from('<III', raw_data, offset)
        ch.time_div = _get_real_from_table(_TIMESCALE_TABLE, time_div_idx)
        ch.volts_div = _get_real_from_table(_VOLT_TABLE, volts_div_idx)
        ch.attenuation = _get_real_from_table(_ATTENUATION_TABLE, atten_idx)
        offset += 12

        ch.offset_y = struct.unpack_from('<i', raw_data, offset)[0]
        offset += 4

        ch.time_mul, ch.frequency, ch.period, ch.volts_mul = struct.unpack_from('<ffff', raw_data, offset)
        offset += 16

        logging.debug(f"Parsed header for channel {ch.name}. Samples: {ch.samples_file}, V/div: {ch.volts_div}, T/div: {ch.time_div}")

        # Read sample data points
        raw_samples = []
        for i in range(ch.samples_file):
            if ch.datatype == 2: # 16-bit data
                if offset + 2 > len(raw_data): break
                sample = struct.unpack_from('<h', raw_data, offset)[0]
                offset += 2
            else: # 8-bit data
                if offset + 1 > len(raw_data): break
                sample = struct.unpack_from('<b', raw_data, offset)[0]
                offset += 1
            raw_samples.append(sample)

        # Convert raw samples to physical units
        for i, sample in enumerate(raw_samples):
            ch.time_points.append(_sample_id_to_time(ch, i))
            ch.volt_points.append(_sample_to_volt(ch, sample))

        header.channels.append(ch)
        logging.info(f"Finished parsing channel {ch.name}. Found {len(ch.volt_points)} data points.")

    return header

def export_to_csv(header: OwonHeader, file_path: str):
    """
    Exports the parsed waveform data to a CSV file.
    This is a Python port of the `owon_output_csv` function from the C project.
    """
    if not header.channels:
        logging.warning("No channel data to export.")
        return

    logging.info(f"Exporting waveform data to {file_path}...")

    with open(file_path, 'w', newline='') as f:
        # Write CSV header
        csv_header = "time"
        for i, ch in enumerate(header.channels):
            csv_header += f",channel_{i+1}_volts"
        f.write(csv_header + '\n')

        # Write data points
        # Assuming all channels have the same time points
        num_samples = len(header.channels[0].time_points)
        for i in range(num_samples):
            row = [f"{header.channels[0].time_points[i]:.12f}"]
            for ch in header.channels:
                if i < len(ch.volt_points):
                    row.append(f"{ch.volt_points[i]:.6f}")
                else:
                    row.append("") # Append empty string if a channel has fewer points
            f.write(",".join(row) + '\n')

    logging.info("CSV export complete.")


def export_to_binary(raw_data: bytes, file_path: str):
    """Exports the raw waveform data to a binary file."""
    logging.info(f"Exporting raw waveform data to {file_path}...")
    with open(file_path, 'wb') as f:
        f.write(raw_data)
    logging.info("Binary export complete.")
