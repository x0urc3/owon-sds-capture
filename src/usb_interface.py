"""
Handles low-level USB communication with the Owon oscilloscope using pyusb.
"""
import usb.core
import usb.util
import constants
import logging

class USBInterface:
    """
    A class to manage USB communication with the Owon oscilloscope.
    """

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
        """
        Finds the USB device, detaches the kernel driver if necessary,
        and claims the interface.
        """
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
        """
        Sends data to the device's bulk write endpoint.

        Args:
            data: The bytes to send to the oscilloscope.
        """
        if self.device is None:
            raise ConnectionError("Device not connected. Cannot write data.")
        
        try:
            self.device.write(constants.BULK_WRITE_ENDPOINT, data)
        except usb.core.USBError as e:
            logging.error(f"Error writing to device: {e}")
            # Consider re-raising or handling more gracefully
            raise

    def __enter__(self):
        """Context manager entry point."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        self.disconnect()