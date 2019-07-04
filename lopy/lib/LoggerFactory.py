import loggingpycom as logging
from loggingpycom import handlers, Handler

STATUS_FMT_DEFAULT = '%(levelname)s - %(asctime)s - %(name)s - %(message)s'
STATUS_MAX_FILE_SIZE_DEFAULT = 10 * 1024 * 1024  # 10MiB
STATUS_ARCHIVE_COUNT_DEFAULT = 10  # How many files to keep before deletion


class LoggerFactory:
    def __init__(
            self,
            level=logging.INFO,
            path='/sd/'
    ):
        self.level = level
        self.path = path
        self.loggers = {}  # dictionary to store loggers

    def get_logger(self, name):
        """
        Returns logger with given name
        :param name:
        :type name:
        :return: logger
        :rtype: object
        """
        return self.loggers[name]

    def create_status_logger(
            self,
            name,
            fmt=STATUS_FMT_DEFAULT,
            filename=None,
            maxBytes=STATUS_MAX_FILE_SIZE_DEFAULT,
            backupCount=STATUS_ARCHIVE_COUNT_DEFAULT
    ):
        """
        Create status logger and add it to the self.loggers dictionary
        :param name: logger name
        :type name: str
        :param fmt: format string for the logger
        :type fmt: str
        :param filename: filename for logging, if None, then does not log into file
        :type filename: str
        :param maxBytes: maximum size of log file
        :type maxBytes: int
        :param backupCount: number of archive files
        :type backupCount: int
        :return: reference to the logger stored in the class
        :rtype: object
        """
        status_logger = logging.getLogger(name)
        formatter = logging.Formatter(fmt=fmt)
        sh = logging.StreamHandler()  # handler for printing to terminal
        sh.setFormatter(formatter)
        status_logger.addHandler(sh)
        if filename:
            file_handler = handlers.RotatingFileHandler(self.path + filename, maxBytes=maxBytes, backupCount=backupCount)
            file_handler.setFormatter(formatter)
            status_logger.addHandler(file_handler)
        self.loggers[name] = status_logger
        return self.loggers[name]

    def create_sensor_logger(
            self,
            name,
            log_to_file=True
    ):
        """
        Create sensor logger and add it to the self.loggers dictionary
        :param name: logger name
        :type name: str
        :param log_to_file: True to log into file named name.csv.current
        :type log_to_file: bool
        :return: reference to the logger stored in the class
        :rtype: object
        """
        sensor_logger = logging.getLogger(name)
        fmt = '%(message)s'
        formatter = logging.Formatter(fmt=fmt)
        sh = logging.StreamHandler()  # handler for printing to terminal
        sh.setFormatter(formatter)
        sensor_logger.addHandler(sh)
        if log_to_file:
            file_handler = SensorFileHandler(filename=self.path + name + '.csv.current')
            file_handler.setFormatter(formatter)
            sensor_logger.addHandler(file_handler)
        self.loggers[name] = sensor_logger
        return self.loggers[name]


class SensorFileHandler(Handler):
    """
    Handler for writing one sensor reading at a time into file.
    """

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def emit(self, record):
        """Write to file."""
        msg = self.formatter.format(record)

        with open(self.filename, "a") as f:
            f.write(msg + "\n")
