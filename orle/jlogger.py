import os
import yaml
import logging

from dataclasses import dataclass
from typing import List
from filelock import FileLock

LOGS = {}

class JobLogger(object):
    """A small wrapper for the logger object
    to store and write job errors and post files to
    a job output file.

    """
    status: int = 1
    warnings: list = []
    errors: list = []
    files: list = []

    def __init__(
        self,
    ) -> None:
        """Constructor
        """
        self.logger = logging.getLogger(__name__)

    def clean(self) -> None:
        """Resets job log
        """
        self.status = 1
        self.warnings = []
        self.errors = []
        self.files = []

    def info(
        self,
        message: str,
        *args,
        **kwargs
    ) -> None:
        self.logger.info(message, *args, **kwargs)

    def debug(
        self,
        message: str,
        *args,
        **kwargs
    ) -> None:
        self.logger.debug(message, *args, **kwargs)

    def warning(
        self,
        message: str,
        *args,
        **kwargs
    ) -> None:
        self.warnings.append(message)
        self.logger.warning(message, *args, **kwargs)

    def error(
        self,
        message: str,
        *args,
        **kwargs
    ) -> None:
        self.status = 0
        self.errors.append(message)
        self.logger.error(message, *args, **kwargs)

    def add_output(
        self,
        file_name: str,
    ) -> None:
        self.files.append(file_name)

    def write(
        self,
        file_path: str
    ) -> None:
        """Writes job log to file

        Args:
            file_path (str): file output path
        """
        output = {"status": self.status, "warnings":self.warnings, 
                    "errors":self.errors, "files":self.files}
        with FileLock(file_path+".lock"):
            with open(file_path, 'w') as file:
                yaml.dump(output, file, default_flow_style=False)

        # Must manually delete lock on unix systems
        if os.path.exists(file_path+".lock"):
            os.remove(file_path+".lock")

def getLogger(
    key:str = 'orle',
) -> JobLogger:
    """Return a job logger with the specified name, 
    creating it if necessary.

    Args:
        key (str, optional): key of job logger. Defaults to orle.

    Returns:
        JobLog: ORLE jog logger class
    """
    if not key in LOGS.keys():
        LOGS[key] = JobLogger()

    return LOGS[key]