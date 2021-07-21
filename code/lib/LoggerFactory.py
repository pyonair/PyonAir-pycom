import loggingpycom as logging
from loggingpycom import handlers

STATUS_FMT_DEFAULT = '%(levelname)s - %(asctime)s - %(name)s - %(message)s'
DEBUG_LOG_MAX_FILE_SIZE_DEFAULT = 50 * 1024 * 1024  # 50MiB
DEBUG_LOG_ARCHIVE_COUNT_DEFAULT = 10  # How many files to keep before deletion, this is inefficient and renames all n files (dont let n get big!)


class LoggerFactory:
    def __init__(
            self,
            path='/sd/'
    ):
        print("Logger factory starting.....")
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
            maxBytes=DEBUG_LOG_MAX_FILE_SIZE_DEFAULT,
            backupCount=DEBUG_LOG_ARCHIVE_COUNT_DEFAULT,
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
        print("Logger creating .....")
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
        print("Logger created: " + name)
        return self.loggers[name]

    def set_level(self, name, level):
        """
        Set logging level
        :param name: logger name
        :type name: str
        :param level: logging level
        :type level: str
        """
        print(name, level)
        print(self.loggers.values)
        self.loggers[name].setLevel(level)
        print("DONE")
        return self.loggers[name]
