import queue
import tkinter as tk
from typing import List

from auth.connection import WLogConnection
from client_identity import ID, SECRET
from data.fights import Fight
from ui.task import AsyncTask

# FIXME: temporary url for fast testing
URL = "https://www.warcraftlogs.com/reports/ZmXtTNkbAxjvf1P6#fight=27&type=damage-done"


class MainWindow(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(**kw)
        self._parent = parent
        self._choice_list = tk.StringVar()
        self._list_box = tk.Listbox(self._parent, height=30, width=80, listvariable=self._choice_list)
        self._url_entry = tk.Entry(self._parent, width=50)

        self._setup_ui()
        self._connection = None

    def _setup_ui(self):
        self._parent.geometry('650x600')

        self._list_box.pack()
        self._list_box.place(x=2, y=100)

        url_entry_label = tk.Label(self._parent, text="WCL Log URL:")
        url_entry_label.pack()
        url_entry_label.place(x=0, y=0)

        self._url_entry.insert(tk.END, URL)
        self._url_entry.pack()
        self._url_entry.place(x=80, y=1)

        grab_log_button = tk.Button(self._parent, text="Grab Log", command=self._handler_button)
        grab_log_button.pack()
        grab_log_button.place(x=385)

    @property
    def connection(self) -> WLogConnection:
        if not self._connection:
            self._connection = WLogConnection(client_id=ID, client_secret=SECRET)
        return self._connection

    def _handler_button(self):
        url = self._url_entry.get()
        self.task = AsyncTask(function=self.connection.get_fights, args=(url,))
        self.task.start()
        self.after(20, self._loop_encounters_fetch)

    def _loop_encounters_fetch(self):
        if self.task.is_alive():
            self.after(20, self._loop_encounters_fetch)
            return

        else:
            try:
                fights: List[Fight] = self.task.get()
                self._choice_list.set([fight.name for fight in fights])
            except queue.Empty:
                # TODO: handle when queue is empty
                print("queue is empty")
