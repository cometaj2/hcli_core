import logging
import traceback
import os
import io
import datetime
import threading
import collections
from logging.handlers import RotatingFileHandler

from hcli_core import config

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


class Logger:
    _instances = {}
    _lock = threading.Lock()
    ROOT_LOGGER = "hcli_core"

    def __new__(cls, name=None, *args, **kwargs):
        with cls._lock:
            if name not in cls._instances:
                instance = super(Logger, cls).__new__(cls)
                cls._instances[name] = instance
            return cls._instances[name]

    def __init__(self, name=None, log=None, max_bytes=10485760, backup_count=5, *args, **kwargs):
        with self._lock:
            self.name = name or __name__
            self.instance = logging.getLogger(self.name)

            # Only add handlers if they haven't been added yet
            if not self.instance.handlers and name == self.ROOT_LOGGER:
                date_format = "%Y-%m-%d %H:%M:%S %z"
                message_format = "[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(filename)13s:%(lineno)-3s] %(message)s"
                formatter = logging.Formatter(fmt=message_format, datefmt=date_format)

                self.streamHandler = logging.StreamHandler()
                self.streamHandler.setFormatter(formatter)
                self.instance.addHandler(self.streamHandler)

                # File handler (if log_file is provided)
                # NullHandler otherwise to prevent any output
                if log == 'log':
                    log_file = config.log_file_path
                    self.fileHandler = RotatingFileHandler(
                        log_file,
                        maxBytes=max_bytes,
                        backupCount=backup_count,
                        encoding='utf-8'
                    )
                    self.fileHandler.setFormatter(formatter)
                    self.instance.addHandler(self.fileHandler)
                else:
                    self.instance.addHandler(logging.NullHandler())

            else:
                # If handlers exist, get the existing ones
                self.streamHandler = next((h for h in self.instance.handlers 
                                        if isinstance(h, logging.StreamHandler)), None)
                self.fileHandler = next((h for h in self.instance.handlers
                                if isinstance(h, RotatingFileHandler)), None)

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
