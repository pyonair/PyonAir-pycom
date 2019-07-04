import loggingpycom as logging
from loggingpycom import handlers

STATUS_FMT_DEFAULT = '%(levelname)s - %(asctime)s - %(name)s - %(message)s'
STATUS_MAX_FILE_SIZE_DEFAULT = 10 * 1024 * 1024  # 10MiB
STATUS_ARCHIVE_COUNT_DEFAULT = 10  # How many files to keep before deletion


class LoggerFactory():
    def __init__(
            self,
            level=logging.INFO,
    ):
        self.level = level
        self.loggers = {}  # dictionary to store loggers

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
        status_logger = logging.getLogger(name)
        formatter = logging.Formatter(fmt=fmt)
        sh = logging.StreamHandler()  # handler for printing to terminal
        sh.setFormatter(formatter)
        status_logger.addHandler(sh)
        if filename:
            file_handler = handlers.RotatingFileHandler(filename, maxBytes=maxBytes, backupCount=backupCount)
            file_handler.setFormatter(formatter)
            status_logger.addHandler(file_handler)
        self.loggers[name] = status_logger
