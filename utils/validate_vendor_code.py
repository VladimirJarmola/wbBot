import logging


def validation_code(code: str):
    result = True
    try:
        int(code)
    except ValueError:
        logging.error('Vendor code is not integer')
        result = False
    if len(code) < 7:
        logging.error('Code length is insufficient')
        result = False
    elif code.find(' ') >= 0:
        logging.error('Message contains more than one code')
        result = False
    return result
