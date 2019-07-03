import loggingpycom as logging
from loggingpycom import handlers

fmt = '%(asctime)s - %(name)s - %(message)s'

logging.basicConfig(level=logging.INFO)
formatter = logging.Formatter(fmt=fmt)

log = logging.getLogger('test')
sh = logging.StreamHandler()
sh.setFormatter(formatter)
log.addHandler(sh)

# Uncomment to log into file
# file_handler = handlers.RotatingFileHandler('testfile.txt', maxBytes=1000, backupCount=10)
# file_handler.setFormatter(formatter)
# log.addHandler(file_handler)

log.info("Test info message")
log.error("Test message4")
log.critical("Test message5")
logging.info("Test message6")

# try:
#     1/0
# except:
#     log.exception("Some trouble (%s)", "expected")
