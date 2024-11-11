import logging
import traceback
import os
import io
import datetime
import threading
import collections

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

class DequeHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deque = collections.deque(maxlen=100)

    def emit(self, record):
        log_entry = self.format(record)
        self.deque.append(log_entry)

    def read_and_clear(self):
        logs = list(self.deque)
        self.deque.clear()
        return logs

class Logger:
    _instances = {}
    _lock = threading.Lock()

    def __new__(cls, name=None, *args, **kwargs):
        with cls._lock:
            if name not in cls._instances:
                instance = super().__new__(cls)
                instance.init(name, *args, **kwargs)
                cls._instances[name] = instance
            return cls._instances[name]

    def init(self, name=None, *args, **kwargs):
        self.name = name or __name__
        self.instance = logging.getLogger(self.name)

        # Only add handlers if they haven't been added yet
        if not self.instance.handlers:
            date_format = "%Y-%m-%d %H:%M:%S %z"
            message_format = "[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(filename)13s:%(lineno)-3s] %(message)s"
            formatter = logging.Formatter(fmt=message_format, datefmt=date_format)

            self.streamHandler = logging.StreamHandler()
            self.streamHandler.setFormatter(formatter)
            self.instance.addHandler(self.streamHandler)

            self.clientHandler = DequeHandler()
            self.clientHandler.setFormatter(formatter)
            self.instance.addHandler(self.clientHandler)
        else:
            # If handlers exist, get the existing ones
            self.streamHandler = next((h for h in self.instance.handlers 
                                    if isinstance(h, logging.StreamHandler)), None)
            self.clientHandler = next((h for h in self.instance.handlers 
                                    if isinstance(h, DequeHandler)), None)

    def setLevel(self, level):
        self.instance.setLevel(level)

    def info(self, msg, *args, **kwargs):
        self.instance.info(msg, *args, stacklevel=2, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.instance.debug(msg, *args, stacklevel=2, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.instance.warning(msg, *args, stacklevel=2, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.instance.error(msg, *args, stacklevel=2, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.instance.critical(msg, *args, stacklevel=2, **kwargs)

    def tail(self):
        log_entries = self.clientHandler.read_and_clear()
        log_text = '\n'.join(log_entries)
        if log_text:
            log_text += '\n'  # Adds newline character at the end if there is some log_text
        return log_text.encode('utf-8')
