import queue
from abc import ABC, abstractmethod
from typing import List

from data.fights import Fight
from ui.task import AsyncTask


class ActionHandler(ABC):
    """Handler interface made to separate handlers code from MainWindow and keep it cleaner
    Note that type hinting will cause circular import"""

    def __init__(self, frame):
        self._frame = frame

    def __call__(self, *args, **kwargs):
        self._handle(*args, **kwargs)

    @abstractmethod
    def _handle(self, *args, **kwargs):
        raise NotImplementedError


class FetchFightsHandler(ActionHandler):
    def _handle(self, *args, **kwargs):
        url = self._frame.get_url()
        self.task = AsyncTask(function=self._frame.connection.get_fights, args=(url,))
        self.task.start()
        self._frame.after(20, self._loop_fights_fetch)

    def _loop_fights_fetch(self):
        if self.task.is_alive():
            self._frame.after(20, self._loop_fights_fetch)
        else:
            try:
                fights: List[Fight] = self.task.get()
                self._frame.set_encounters_list(fights)
            except queue.Empty:
                # TODO: handle when queue is empty
                print("queue is empty")
