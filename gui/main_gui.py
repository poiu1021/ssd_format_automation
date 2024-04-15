import tkinter as tk
from tkinter import ttk
from queue import Queue
from functools import partial
from frameworks.format import Format
from frameworks.ssd import ConnectionMonitor
from gui.debug_window import DebugWindow
from loggers.logconfig import *


class Application(tk.Tk):
    """This class starts the main GUI to start the program"""
    def __init__(self):
        #super() returns a temp obj of superclass which allow you to call its methods
        #initialize Tk, setting up the window with default setting and behaviours
        super().__init__()
        self.queue = Queue()

        self.config_data = bring_yaml()

        self.title("SD Production")
        self.geometry('300x100')

        self.label = ttk.Label(self, text='Please select one program')
        self.label.pack(pady=5)

        self.frameworks = list(self.config_data['MODULE'])
        self.combobox = ttk.Combobox(self, values=self.frameworks)
        self.combobox.pack(pady=5)

        self.next_btn = tk.Button(self, text='NEXT', command=partial(self.start_program))
        self.next_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        self.exit_btn = tk.Button(self, text='EXIT', command=self.destroy)
        self.exit_btn.pack(side=tk.RIGHT, padx=5, pady=5)

    def start_program(self):
        """Retrieve the selected program and start the process"""
        selected_event = self.combobox.get()

        if selected_event == 'SSD_FORMAT':
            con_monitor = ConnectionMonitor(self.queue, self.config_data)
            con_dev = con_monitor.get_con_device()
            format = Format(self.queue, con_dev)
            dw = DebugWindow(self, self.queue, format.start_format)
            format.get_dw(dw)
            con_monitor.get_dw(dw)
            con_monitor.start_monitor()