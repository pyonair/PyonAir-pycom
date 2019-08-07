import loggingpycom as logging
from loggingpycom import handlers

STATUS_FMT_DEFAULT = '%(levelname)s - %(asctime)s - %(name)s - %(message)s'
STATUS_MAX_FILE_SIZE_DEFAULT = 10 * 1024 * 1024  # 10MiB
STATUS_ARCHIVE_COUNT_DEFAULT = 10  # How many files to keep before deletion


class LoggerFactory:
    def __init__(
            self,
            path='/sd/'
    ):
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
            level=logging.INFO,
            fmt=STATUS_FMT_DEFAULT,
            filename=None,
            maxBytes=STATUS_MAX_FILE_SIZE_DEFAULT,
            backupCount=STATUS_ARCHIVE_COUNT_DEFAULT,
            terminal_out=True
    ):
        """
        Create status logger and add it to the self.loggers dictionary
        :param terminal_out: output status logger to terminal
        :type terminal_out: bool
        :param name: logger name
        :type name: str
        :param fmt: format string for the logger
        :type fmt: str
        :param filename: sensor_name for logging, if None, then does not log into file
        :type filename: str
        :param maxBytes: maximum size of log file
        :type maxBytes: int
        :param backupCount: number of archive files
        :type backupCount: int
        :return: reference to the logger stored in the class
        :rtype: object
        """
        status_logger = logging.getLogger(name)
        status_logger.setLevel(level)
        formatter = logging.Formatter(fmt=fmt)
        if terminal_out:
            sh = logging.StreamHandler()  # handler for printing to terminal
            sh.setFormatter(formatter)
            status_logger.addHandler(sh)
        if filename:
            file_handler = handlers.RotatingFileHandler(self.path + filename, maxBytes=maxBytes, backupCount=backupCount)
            file_handler.setFormatter(formatter)
            status_logger.addHandler(file_handler)
        self.loggers[name] = status_logger
        return self.loggers[name]

    def set_level(self, name, level):

        self.loggers[name].setLevel(level)
        return self.loggers[name]
