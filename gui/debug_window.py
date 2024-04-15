import tkinter as tk
from tkinter import ttk, NORMAL, DISABLED
from tkinter.scrolledtext import ScrolledText

class DebugWindow:
    """The purpose of this class is to create a debug window to display messages"""
    def __init__(self, master, queue, callback):
        self._master = master
        self._root = tk.Toplevel(self._master)  # Create a new Toplevel window
        self._root.title('Debug Window')

        self._queue = queue
        self._callback_func = callback
        self._debug_window = ScrolledText(self._root)
        self._debug_window.pack(pady=10, fill=tk.BOTH, expand=True)

        self._debug_window.insert(tk.END,
                                 'Welcome to Satcom Direct Production Programs\nPlease click start when all connections are confirmed' + '\n')
        self._debug_window.config(state=tk.DISABLED)  # Start with read-only

        self._next_btn = ttk.Button(self._root, text='START', command=self._callback_func, state=DISABLED)
        self._next_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self._exit_btn = ttk.Button(self._root, text='EXIT', command=self._root.destroy, state=NORMAL)
        self._exit_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self._root.after(100, self._update_message)

    def _update_message(self):
        """Update the window message"""
        while not self._queue.empty():
            message = self._queue.get_nowait()
            self._debug_window.config(state=tk.NORMAL)
            self._debug_window.insert(tk.END, message + '\n')
            self._debug_window.config(state=tk.DISABLED)
            self._debug_window.see(tk.END)
        self._root.after(100, self._update_message)

    def change_btn_state(self,btn_num, state):
        """
        Change the state of the buttons
        :param btn_num: 0 for next button, 1 for exit button
        :param state: button state : DISABLED, NORMAL
        """
        if btn_num == 0:
            self._next_btn['state'] = state
        elif btn_num == 1:
            self._exit_btn['state'] = state
