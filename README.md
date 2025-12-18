# OWON PDS Series Oscilloscope Controller

This project provides a Python utility for controlling OWON PDS series digital oscilloscopes via USB.

## Installation

It is recommended to install the package in a virtual environment.

```bash
# Install the package in editable mode from the project root
pip install -e .
```

### Linux USB Permissions

On Linux, you may need to grant your user permission to access the oscilloscope's USB device. Running with `sudo` is a quick workaround, but the recommended approach is to add a `udev` rule.

1.  Create a new file at `/etc/udev/rules.d/99-owon-pds.rules`.

2.  Add the following line to the file, which matches the OWON PDS series oscilloscopes:
    ```
    SUBSYSTEM=="usb", ATTR{idVendor}=="5345", ATTR{idProduct}=="1234", MODE="0666"
    ```

3.  Save the file and exit the editor.

4.  Reload the `udev` rules for the changes to take effect.
    ```bash
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    ```

5.  You may need to unplug and reconnect the oscilloscope for the new rule to be applied. After this, you should be able to run `owon-sds-capture` without `sudo`.

## Usage

The application provides a command-line interface for interacting with the oscilloscope.

**Note:** You may need to run the commands with `sudo` or set up appropriate `udev` rules to allow access to the USB device.

### Examples

```bash
# View all available commands and their arguments
owon-sds-capture --help

# Perform an auto-set
owon-sds-capture --autoset

# Revert to factory settings
owon-sds-capture --factory

# Force a trigger event
owon-sds-capture --trigger force

# Set Channel 1 coupling to AC
owon-sds-capture --coupling 1 AC

# Set the timebase to 1ms
owon-sds-capture --timebase T_1MS

# Set the vertical voltage scale for Channel 2 to 500mV
owon-sds-capture --volt-scale 2 V_500MV

# Set acquisition mode to Peak Detect
owon-sds-capture --acq-mode PEAK_DETECT

# Configure an edge trigger for Channel 1
owon-sds-capture --trigger-type 1 edge --trigger-mode SINGLE --trigger-slope FALLING
```

## Acknowledgements

The OWON SDS USB protocol command definitions were adapted from the [owoncontrol](https://github.com/7oxicshadow/owoncontrol) project by 7oxicshadow. This Python port would not have been possible without this foundational work.

