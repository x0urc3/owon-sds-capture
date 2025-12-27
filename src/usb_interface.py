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
import usb.core
import usb.util
import constants
import logging

class USBInterface:
    """A class to manage USB communication with the Owon oscilloscope."""

    def __init__(self, vendor_id: int = constants.USB_VENDOR_ID, product_id: int = constants.USB_PRODUCT_ID):
        """
        Initializes the USB interface.

        Args:
            vendor_id: The USB vendor ID of the device.
            product_id: The USB product ID of the device.
        """
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = None
        self.kernel_driver_active = False

    def connect(self) -> None:
        """Finds the USB device, detaches the kernel driver if necessary, and claims the interface."""
        logging.info(f"Searching for device with VID={hex(self.vendor_id)} PID={hex(self.product_id)}...")
        self.device = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)

        if self.device is None:
            raise ConnectionError("Owon oscilloscope not found. Check connection and permissions.")

        logging.info("Device found.")

        # Detach kernel driver if active
        self.kernel_driver_active = self.device.is_kernel_driver_active(0)
        if self.kernel_driver_active:
            logging.info("Kernel driver active. Detaching...")
            self.device.detach_kernel_driver(0)
            logging.info("Driver detached.")

        # Set the active configuration. With no arguments, the first configuration will be the active one.
        cfg = self.device.get_active_configuration()
        if cfg is None:
            self.device.set_configuration()

        # Claim the interface
        usb.util.claim_interface(self.device, 0)
        logging.info("Interface claimed.")

    def disconnect(self) -> None:
        """
        Releases the USB interface and disposes of the device object.
        """
        if self.device:
            logging.info("Releasing USB interface...")
            usb.util.release_interface(self.device, 0)
            # This is particularly important on Linux where the kernel driver needs to be reattached
            if self.kernel_driver_active:
                self.device.attach_kernel_driver(0)
                logging.info("Interface released and kernel driver reattached.")
            else:
                logging.info("Interface released.")
            self.device = None
            self.kernel_driver_active = False


    def write(self, data: bytes) -> None:
        """Sends data to the device's bulk write endpoint.

        :param data: The bytes to send to the oscilloscope.
        """
        if self.device is None:
            raise ConnectionError("Device not connected. Cannot write data.")

        try:
            self.device.write(constants.BULK_WRITE_ENDPOINT, data)
        except usb.core.USBError as e:
            logging.error(f"Error writing to device: {e}")
            # Consider re-raising or handling more gracefully
            raise

    def read(self, size: int, timeout: int = 1000) -> bytes:
        """
        Reads data from the device's bulk read endpoint.

        Args:
            size: The number of bytes to read.
            timeout: The timeout for the read operation in milliseconds.

        Returns:
            The bytes read from the oscilloscope.
        """
        if self.device is None:
            raise ConnectionError("Device not connected. Cannot read data.")

        try:
            return self.device.read(constants.BULK_READ_ENDPOINT, size, timeout)
        except usb.core.USBError as e:
            # A timeout error is expected if the device has no data to send.
            # It's better to let the caller handle it.
            logging.warning(f"Error reading from device: {e}")
            raise

    def __enter__(self):
        """Context manager entry point."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        self.disconnect()
