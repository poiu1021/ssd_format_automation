import threading
import gui.debug_window
from tkinter import DISABLED, NORMAL


class Format:
    """The purpose of this class is to start format process for each connected SSD"""

    def __init__(self, queue, con_dev):
        self._insert = queue.put
        self._connected_dev = con_dev
        self._lock = threading.Lock()
        self._dw = None

    def format(self):
        """Format the connected SSD(s)"""
        self._dw.change_btn_state(1, DISABLED)
        if len(self._connected_dev) != 0:
            self._insert(f'Please do NOT disconnect the device(s)')
            try:
                self._lock.acquire()
                for dev in self._connected_dev:
                    if not dev.get_format_status():
                        dev.format_ssd()
                    else:
                        self._insert(f'[SKIP]({dev.get_serial()}) : It has already been formatted.')
                self._lock.release()
                self._insert(f'All processes has been finished. Now you may disconnect the device(s)')
            except RuntimeError as e:
                print(f'[EXCEPTION] : {e}')
            finally:
                self._dw.change_btn_state(1, NORMAL)
                self._dw.change_btn_state(0, DISABLED)
        else:
            self._insert(f'There is NO USB connection. Please connect at least one device to start the program')


    def start_format(self):
        """Start a thread for format process"""
        threading.Thread(target=self.format, daemon=True).start()

    def get_dw(self, dw):
        """ Get debug window instance """
        self._dw = dw
