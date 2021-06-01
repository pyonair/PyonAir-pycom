"""
    Database of sensirion error codes
    Philip Basford
    19/02/2019
"""
ERROR_CODE_NO_ERROR = b'\x00'
ERROR_CODE_WRONG_LENGTH = b'\x01'
ERROR_CODE_UNKNOWN_CMD = b'\x02'
ERROR_CODE_NO_ACCESS = b'\x03'
ERROR_CODE_ILLEGAL_CMD = b'\x04'
ERROR_CODE_ILLEGAL_ARG = b'\x28'
ERROR_CODE_CMD_NOT_ALLOWED = b'\x43'

ERROR_CODES = {
    ERROR_CODE_NO_ERROR : "OK",
    ERROR_CODE_WRONG_LENGTH : "Wrong data length for command",
    ERROR_CODE_UNKNOWN_CMD : "Unknown command",
    ERROR_CODE_NO_ACCESS : "No Access right for command",
    ERROR_CODE_ILLEGAL_CMD : "Illegal command parameter or parameter out of allowed range",
    ERROR_CODE_ILLEGAL_ARG : "Internal function argument out of range",
    ERROR_CODE_CMD_NOT_ALLOWED : "Command not allowed in current state"
}

def lookup_error_code(code):
    """
        Lookup the error code to get it's definition
    """
    return ERROR_CODES.get(code, "Unknown Error 0x%02x" % ord(code))
