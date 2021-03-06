import logging
from logging import LogRecord

import colored
from colored import stylize

logger = logging.getLogger(__name__)


class ConditionalFormatter(logging.Formatter):
    # https://stackoverflow.com/questions/1343227/can-pythons-logging-format-be-modified-depending-on-the-message-log-level
    # https://github.com/pygments/pygments
    def format(self, record: LogRecord) -> str:
        message = record.msg

        if record.levelno == logging.DEBUG:
            coloured = stylize(message, colored.fg("dark_gray"))
            return coloured
        else:
            return message


# TODO:
# Add more regex patterns to recognize more image file names and ensure the date
# Create one command that will:
#   1. Scan all images or videos in the directory
#   2. Try to parse the filename to extract timestamp.
#   3. Look data and geolocation metadata in the files.
#   4. Report:
#        - Filename and metadata match, +GPS -> OK
#        - If no GPS metadata -> Add '_nogps' at the end of the filename
#        - Filename and metadata don't match ->
