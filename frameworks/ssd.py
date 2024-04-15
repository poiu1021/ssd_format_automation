import subprocess
import threading
import time
import re
from tkinter import NORMAL, DISABLED

import pyudev
from loggers.logconfig import *


class SSD:
    """This class represents a connected SSD device"""

    def __init__(self, device, queue, logger):
        self._logger = logger
        self._insert = queue.put
        self.__dev = device
        self.__devpath = self.__dev.get('DEVPATH')
        self.__serial = self.__dev.get('ID_SERIAL')
        self.__vendorid = self.__dev.get('ID_VENDOR_ID')
        self.__node = self.__dev.get('DEVNAME')
        self.__con_status = False
        self.__format_status = False

    def get_dev(self):
        return self.__dev

    def get_node(self):
        return self.__node

    def get_devpath(self):
        return self.__devpath

    def get_serial(self):
        return self.__serial

    def get_vendorid(self):
        return self.__vendorid

    def on_connect(self):
        self.__con_status = True

    def formatted(self):
        self.__format_status = True

    def get_format_status(self):
        return self.__format_status

    def check_partition(self):
        """Confirm if the SSD is formatted or not"""
        partition_node = self.__node[5:]
        time.sleep(1)
        cmd = 'lsblk -f | grep \'{}1.*ext4.*MEDIA*\''.format(partition_node)
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result

    def format_ssd(self):
        """Format the SSD with parted and print out status message on the debug window"""
        node = self.__node
        serial = self.__serial
        try:
            self._insert(f'+++[{serial}] Format has started+++')
            log_data(f'{serial} : format has started', self._logger)

            if self.__format_status:
                self._insert(f'[SKIP]({serial}) : It has already been formatted.')
                log_data(f'{serial} : already formatted', self._logger)

            # --script : never prompt the user
            create_partition_table = 'echo "yes" | sudo parted --script {} mklabel msdos'.format(node)
            create_primary_partition = 'sudo parted --script {} mkpart primary ext4 0% 100%'.format(node)
            create_file_system = 'sudo mkfs.ext4 -b 4096 -L MEDIA {}1'.format(node)

            partition_table = subprocess.run(create_partition_table, shell=True, stderr=subprocess.PIPE,
                                             stdout=subprocess.PIPE)
            primary_partition = subprocess.run(create_primary_partition, shell=True, stderr=subprocess.PIPE,
                                               stdout=subprocess.PIPE)
            file_system = subprocess.run(create_file_system, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

            # check each format process
            if partition_table.returncode != 0:
                log_data(f"Error while creating partition table: {partition_table.stderr.decode()}", self._logger)
            if primary_partition.returncode != 0:
                log_data(f"Error while creating primary partition: {primary_partition.stderr.decode()}", self._logger)
            if file_system.returncode != 0:
                log_data(f"Error while creating file system: {file_system.stderr.decode()}", self._logger)


            status : ''
            is_formatted = self.check_partition()
            if is_formatted.returncode == 0:
                status = 'PASS'
                self.formatted()
                self._insert(f'[PASS]({serial}) : Format is completed')
                log_data(f'{serial} : Format succeeded', self._logger)
            else:
                status = 'FAIL'
                self._insert(f'[FAIL]({serial}) : Format is failed')
                log_data(f'{serial} : Format failed', self._logger)

            log_data(
                f'[{status}] {serial} : Format process exit code: Partition table : {partition_table.returncode}, Primary '
                f'partition : {primary_partition.returncode}, File_System : {file_system.returncode}',
                self._logger)

        except Exception as e:
            self._insert(f'[EXCEPTION] : {e} ')
            log_data(f'{serial} : EXCEPTION: {e}', self._logger)


class ConnectionMonitor:
    """This class is constructed to monitor the USB connection"""

    def __init__(self, queue, config_d):
        self._config_data = config_d
        path = self._config_data['MODULE']['SSD_FORMAT']['LOG_PATH']
        filename = self._config_data['MODULE']['SSD_FORMAT']['LOGGER']
        self._logger = create_logger(path, filename, 'SSD_FORMAT')
        log_data(f'SSD_FORMAT logger has been created.', self._logger)
        self._queue = queue
        self._insert = self._queue.put
        self._expected_venid = self._config_data['MODULE']['SSD_FORMAT']['VENDOR_ID']
        self._connected_devices = []
        self._dw = None
        self._lock = threading.Lock()
        self.__context = pyudev.Context()
        self.__monitor = pyudev.Monitor.from_netlink(self.__context)
        self.__monitor.filter_by(subsystem='block')

    def monitor_connection(self):
        """Monitor the USB connection and response accordingly"""
        for action, device in self.__monitor:
            # ignore partition device and check vendor id
            if device.device_type != 'partition' and device.get('ID_VENDOR_ID') == self._expected_venid:

                if action == 'add' and 'ID_SERIAL' in device:
                    added_ssd = SSD(device, self._queue, self._logger)
                    serial = added_ssd.get_serial()
                    # check if the device is previously formatted
                    is_formatted = added_ssd.check_partition()
                    if is_formatted.returncode == 0:
                        self._insert(
                            f'[CONNECTED][WARNING] : {serial} has been formatted.\n  Please disconnect the device. '
                            f'This device will be ignored while processing')
                        added_ssd.formatted()
                    else:  # deal with device that is not formatted
                        self._dw.change_btn_state(0, NORMAL)
                        self._insert(f'[CONNECTED] : {serial}')
                        log_data(f'{added_ssd.get_serial()}', self._logger)

                    self._lock.acquire()
                    added_ssd.on_connect()
                    self._connected_devices.append(added_ssd)
                    self._lock.release()

                elif action == 'remove':

                    removed_ssd = SSD(device, self._queue, self._logger)

                    for dev in self._connected_devices:
                        if removed_ssd.get_serial() == dev.get_serial():
                            is_formatted = dev.check_partition()
                            if not dev.get_format_status():
                                self._insert(
                                    f'[DISCONNECTED][WARNING]: {dev.get_serial()} has not formatted and disconnected')
                            else:
                                self._insert(f'[DISCONNECTED]: {dev.get_serial()}')

                            self._lock.acquire()
                            self._connected_devices.remove(dev)
                            self._lock.release()

                            if len(self._connected_devices) == 0:
                                self._dw.change_btn_state(0, DISABLED)

                            break

    def monitor(self):
        """Initiate the monitoring"""
        log_data(f'USB connection monitoring has been started', self._logger)
        self.__monitor.start()
        self.observer = pyudev.MonitorObserver(self.__monitor, self.monitor_connection())

    def start_monitor(self):
        """Start the monitor thread"""
        threading.Thread(target=self.monitor, daemon=True).start()

    def get_con_device(self):
        return self._connected_devices

    def get_dw(self, dw):
        """ Get debug window instance """
        self._dw = dw


