import logging
import threading
from logging.handlers import RotatingFileHandler

from hcli_core import config

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


class Logger:
    _instances = {}
    _lock = threading.RLock()
    _original_record_factory = logging.getLogRecordFactory()
    ROOT_LOGGER = "hcli_core"

    @classmethod
    def _custom_record_factory(cls, *args, **kwargs):
        record = cls._original_record_factory(*args, **kwargs)

        # Use the last part of the logger name for display
        record.display_name = record.name.split('.')[-1]
        return record

    def __new__(cls, name=None, log=None, *args, **kwargs):
        with cls._lock:
            if name not in cls._instances:
                instance = super(Logger, cls).__new__(cls)
                cls._instances[name] = instance
                instance.init(name, log)
            return cls._instances[name]

    def init(self, name=None, log=None, max_bytes=10485760, backup_count=5, *args, **kwargs):
        with self._lock:

            # Set custom record factory to modify display name
            logging.setLogRecordFactory(self._custom_record_factory)

            # Create logger as child of ROOT_LOGGER if name is provided
            self.name = name or self.ROOT_LOGGER
            if name and name != self.ROOT_LOGGER:
                self.logger_name = f"{self.ROOT_LOGGER}.{name}"
            else:
                self.logger_name = self.ROOT_LOGGER
            self.instance = logging.getLogger(self.logger_name)

            # Only configure handlers for the root logger if not already configured
            root_logger = logging.getLogger(self.ROOT_LOGGER)
            if not root_logger.handlers:
                date_format = "%Y-%m-%d %H:%M:%S %z"
                message_format = "[%(asctime)s] [%(levelname)-8s] [%(display_name)s] [%(filename)13s:%(lineno)-3s] %(message)s"
                formatter = logging.Formatter(fmt=message_format, datefmt=date_format)

                # Stream handler
                self.streamHandler = logging.StreamHandler()
                self.streamHandler.setFormatter(formatter)
                root_logger.addHandler(self.streamHandler)

                # File handler (if log_file is provided)
                if log == 'log':
                    log_file = config.log_file_path
                    self.fileHandler = RotatingFileHandler(
                        log_file,
                        maxBytes=max_bytes,
                        backupCount=backup_count,
                        encoding='utf-8'
                    )
                    self.fileHandler.setFormatter(formatter)
                    root_logger.addHandler(self.fileHandler)
                else:
                    root_logger.addHandler(logging.NullHandler())

            # Retrieve handlers from root logger
            self.streamHandler = next((h for h in root_logger.handlers 
                                      if isinstance(h, logging.StreamHandler)), None)
            self.fileHandler = next((h for h in root_logger.handlers
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
