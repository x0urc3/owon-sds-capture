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
from enum import Enum

# USB Device Identifiers
USB_VENDOR_ID = 0x5345
USB_PRODUCT_ID = 0x1234

# USB Endpoints
BULK_WRITE_ENDPOINT = 0x03
BULK_READ_ENDPOINT = 0x81

class Channel(Enum):
    """Oscilloscope channels."""
    CH1 = 0
    CH2 = 1

class Coupling(Enum):
    """Channel coupling options."""
    DC = 0
    AC = 1
    GND = 2

class ProbeScale(Enum):
    """Probe attenuation scale."""
    X1 = 0
    X10 = 1
    X100 = 2
    X1000 = 3

class VoltScale(Enum):
    """Vertical voltage scale."""
    V_2MV = 0
    V_5MV = 1
    V_10MV = 2
    V_20MV = 3
    V_50MV = 4
    V_100MV = 5
    V_200MV = 6
    V_500MV = 7
    V_1V = 8
    V_2V = 9
    V_5V = 10
    V_10V = 11

class TimeBase(Enum):
    """Horizontal timebase scale."""
    T_2NS = 0
    T_5NS = 1
    T_10NS = 2
    T_20NS = 3
    T_50NS = 4
    T_100NS = 5
    T_200NS = 6
    T_500NS = 7
    T_1US = 8
    T_2US = 9
    T_5US = 10
    T_10US = 11
    T_20US = 12
    T_50US = 13
    T_100US = 14
    T_200US = 15
    T_500US = 16
    T_1MS = 17
    T_2MS = 18
    T_5MS = 19
    T_10MS = 20
    T_20MS = 21
    T_50MS = 22
    T_100MS = 23
    T_200MS = 24
    T_500MS = 25
    T_1S = 26
    T_2S = 27
    T_5S = 28
    T_10S = 29
    T_20S = 30
    T_50S = 31
    T_100S = 32

class MemoryDepth(Enum):
    """Acquisition memory depth."""
    MEM_1K = 0
    MEM_10K = 1
    MEM_100K = 2
    MEM_1M = 3
    MEM_10M = 4

class AcquisitionMode(Enum):
    """Acquisition mode."""
    SAMPLE = 0
    PEAK_DETECT = 1
    AVERAGE = 2

class AverageSamples(Enum):
    """Number of samples for Average acquisition mode."""
    SAMPLES_4 = 0
    SAMPLES_16 = 1
    SAMPLES_64 = 2
    SAMPLES_128 = 3

class TriggerType(Enum):
    """Trigger type."""
    EDGE = 0
    VIDEO = 1
    # 'ALT' is a mode of edge trigger, not a distinct type here

class TriggerMode(Enum):
    """Trigger mode."""
    AUTO = 0
    NORMAL = 1
    ONCE = 2

class TriggerEdge(Enum):
    """Edge trigger slope."""
    RISING = 0
    FALLING = 1

class TriggerCoupling(Enum):
    """Trigger coupling options."""
    DC = 0
    AC = 1
    HF = 2 # High-frequency reject
    LF = 3 # Low-frequency reject

class VideoModulation(Enum):
    """Video trigger modulation standard."""
    NTSC = 0
    PAL = 1
    SECAM = 2

class VideoSync(Enum):
    """Video trigger sync type."""
    LINE = 0
    FIELD = 1
    ODD = 2
    EVEN = 3
    LINE_NO = 4

# --- Raw Command Bytes ---

class CMD_ACQ(Enum):
    """Data acquisition commands."""
    BMP = b'STARTBMP'
    BIN = b'STARTBIN'
    MEMDEPTH = b'STARTMEMDEPTH'
    DEBUGTXT = b'STARTDEBUGTXT'

CMD_AUTOSET           = b'\x3a\x53\x44\x53\x4c\x41\x55\x54\x23'
CMD_SELF_CAL          = b'\x3a\x53\x44\x53\x4c\x43\x52\x53\x23'
CMD_FACTORY_RESET     = b'\x3a\x53\x44\x53\x4c\x44\x46\x54\x23'
CMD_FORCE_TRIGGER     = b'\x3a\x53\x44\x53\x4c\x46\x4f\x52\x23'
CMD_SET_50PCT_TRIGGER = b'\x3a\x53\x44\x53\x4c\x46\x35\x30\x23'
CMD_SET_0_TRIGGER     = b'\x3a\x53\x44\x53\x4c\x54\x4c\x30\x23'

# --- Command Templates (Mutable bytearrays for modification) ---

TPL_COUPLING = bytearray(b'\x3a\x4d\x00\x00\x00\x06\x4d\x43\x48\x00\x63\x00')
# Byte[9]: Channel (0=CH1, 1=CH2)
# Byte[11]: Coupling (0=DC, 1=AC, 2=GND)

TPL_PROBE_SCALE = bytearray(b'\x3a\x4d\x00\x00\x00\x06\x4d\x43\x48\x00\x70\x00')
# Byte[9]: Channel (0=CH1, 1=CH2)
# Byte[11]: Scale (0=x1, 1=x10, 2=x100, 3=x1000)

TPL_VOLT_SCALE = bytearray(b'\x3a\x4d\x00\x00\x00\x06\x4d\x43\x48\x00\x76\x00')
# Byte[9]: Channel (0=CH1, 1=CH2)
# Byte[11]: Volt Scale Enum

TPL_MEMORY_DEPTH = bytearray(b'\x3a\x4d\x00\x00\x00\x04\x4d\x44\x50\x00')
# Byte[9]: Memory Depth Enum

TPL_TIMEBASE = bytearray(b'\x3a\x4d\x00\x00\x00\x05\x4d\x48\x52\x62\x00')
# Byte[10]: Timebase Enum

TPL_TRACE_POS = bytearray(b'\x3a\x4d\x00\x00\x00\x09\x4d\x43\x48\x00\x7a\x00\x00\x00\x00')
# Byte[9]: Channel
# Byte[11-14]: 32-bit signed value (LSB at [14])

TPL_HORIZ_TRIGGER_POS = bytearray(b'\x3a\x4d\x00\x00\x00\x08\x4d\x48\x52\x76\x00\x00\x00\x00')
# Byte[10-13]: 32-bit signed value (LSB at [13])

TPL_ACQU_MODE = bytearray(b'\x3a\x4d\x00\x00\x00\x04\x4d\x41\x51\x00')
# Byte[9]: Acquisition Mode (0=Sample, 1=Peak)

TPL_ACQU_AVG_MODE = bytearray(b'\x3a\x4d\x00\x00\x00\x05\x4d\x41\x51\x02\x00')
# Byte[10]: Average Samples Enum

TPL_EDGE_TRIGGER = bytearray(b'\x3a\x4d\x00\x00\x00\x2e\x4d\x54\x52\x73\x00\x65\x02\x00\x4d\x54\x52\x73\x00\x65\x03\x00\x4d\x54\x52\x73\x00\x65\x04\x00\x00\x00\x01\x4d\x54\x52\x73\x00\x65\x05\x00\x4d\x54\x52\x73\x00\x65\x06\x00\x00\x00\x00')
# See C code for the many fields. This is complex.
# byte[9] & byte[17] & byte[25] & byte[36] & byte[44] -> 0x73 = single | 0x61 = alternate
# byte[10] & byte[18] & byte[26] & byte[37] & byte[45] -> Channel
# byte[40] -> Edge (Rising/Falling)
# byte[13] -> Trigger Coupling
# byte[21] -> Trigger Mode (Auto/Normal/Once)
# byte[48-51] -> Trigger value 32bit signed (LSB at [51])

TPL_VIDEO_TRIGGER = bytearray(b'\x3a\x4d\x00\x00\x00\x1b\x4d\x54\x52\x73\x00\x76\x02\x00\x4d\x54\x52\x73\x00\x76\x03\x00\x4d\x54\x52\x73\x00\x76\x04\x00\x00\x00\x01')
# byte[10] & byte[18] & byte[26] -> Channel
# byte[13] -> Video Modulation
# byte[21] -> Video Sync

TPL_VIDEO_TRIGGER_LINE = bytearray(b'\x3a\x4d\x00\x00\x00\x1f\x4d\x54\x52\x73\x01\x76\x02\x02\x4d\x54\x52\x73\x01\x76\x03\x04\x00\x00\x00\x01\x4d\x54\x52\x73\x01\x76\x04\x00\x00\x00\x01')
# byte[10] & byte[18] & byte[30] -> Channel
# byte[13] -> Video Modulation
# byte[22-25] -> Line number 32bit (LSB at [25])
