import loggingpycom as logging
from loggingpycom import handlers

SENSOR_FMT_DEFAULT = '%(asctime)s - %(name)s - %(message)s'
SENSOR_MAX_FILE_SIZE_DEFAULT = 10 * 1024 * 1024  # 10MiB
SENSOR_ARCHIVE_COUNT_DEFAULT = 10  # How many files to keep before deletion


class AQLogger():
    def __init__(
            self,
            level=logging.INFO,
            sensor_fmt=SENSOR_FMT_DEFAULT
    ):
        self.level = level
        self.loggers = {}  # dictionary to store loggers

    def create_sensor_logger(
            self,
            name,
            fmt=SENSOR_FMT_DEFAULT,
            filename=None,
            maxBytes=SENSOR_MAX_FILE_SIZE_DEFAULT,
            backupCount=SENSOR_ARCHIVE_COUNT_DEFAULT
    ):
        """
        Create sensor logger and add it to the self.loggers dictionary
        :param name:
        :type name: str
        :param fmt: format string for the logger
        :type fmt: str
        :param filename: filename for logging, if None, then does not log into file
        :type filename: str
        :param maxBytes: maximum size of log file
        :type maxBytes: int
        :param backupCount: number of archive files
        :type backupCount: int
        """
        sensor_logger = logging.getLogger(name)
        formatter = logging.Formatter(fmt=fmt)
        sh = logging.StreamHandler()  # handler for printing to terminal
        sh.setFormatter(formatter)
        sensor_logger.addHandler(sh)
        if filename:
            file_handler = handlers.RotatingFileHandler(filename, maxBytes=maxBytes, backupCount=backupCount)
            file_handler.setFormatter(formatter)
            sensor_logger.addHandler(file_handler)
        self.loggers[name] = sensor_logger
