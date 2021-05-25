import os
import yaml
import logging

from dataclasses import dataclass, field
from typing import List
from filelock import FileLock

LOGS = {}


@dataclass
class RootLog:
    status: int = 1
    warnings: list = field(default_factory=lambda: [])
    errors: list = field(default_factory=lambda: [])
    files: list = field(default_factory=lambda: [])

class RootJobLogger(object):
    """Root wrapper for the logger object
    to store and write job errors and post files to
    a job output file.

    Args:
        log (RootLog): log data class
    """

    def __init__(
        self,
        log: RootLog
    ) -> None:
        self.log = log

    def clean(self) -> None:
        """Resets job log
        """
        self.log.status = 0
        self.log.warnings = []
        self.log.errors = []
        self.log.files = []

    def info(
        self,
        *args,
        **kwargs
    ) -> None:
        raise NotImplementedError("Info method of root logger not overloaded")

    def debug(
        self,
        message: str,
        *args,
        **kwargs
    ) -> None:
        raise NotImplementedError("Debug method of root logger not overloaded")

    def warning(
        self,
        *args,
        **kwargs
    ) -> None:
        raise NotImplementedError("Warning method of root logger not overloaded")

    def error(
        self,
        *args,
        **kwargs
    ) -> None:
        raise NotImplementedError("Error method of root logger not overloaded")

    def add_warning(
        self,
        message: str,
    ) -> None:
        """Adds a logged warning to warning list

        Args:
            message (str): warning message
        """
        self.log.warnings.append(message)

    def add_error(
        self,
        message: str,
    ) -> None:
        """Adds a logged error to error list

        Args:
            message (str): error message
        """
        self.log.status = 1
        self.log.errors.append(message)

    def add_output(
        self,
        file_name: str,
    ) -> None:
        """Adds output file to list

        Args:
            file_name (str): file name
        """
        self.log.files.append(file_name)

    def write(
        self,
        file_path: str
    ) -> None:
        """Writes job log to file

        Args:
            file_path (str): file output path
        """
        output = {"status": self.log.status, "warnings": self.log.warnings, 
                    "errors": self.log.errors, "files": self.log.files}
        with FileLock(file_path+".lock"):
            with open(file_path, 'w') as file:
                yaml.dump(output, file, default_flow_style=False)

        # Must manually delete lock on unix systems
        if os.path.exists(file_path+".lock"):
            os.remove(file_path+".lock")


class JobLogger(RootJobLogger):
    """Instance of job logger for specific name space

    Args:
        name (str): Instance name to give logger object
        root (RootLog): Instance of root job log
    """
    def __init__(
        self,
        name: str,
        log: RootLog
    ) -> None:
        """Constructor
        """
        super().__init__(log)
        self.logger = logging.getLogger(name)

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
        self.add_warning(message)
        self.logger.warning(message, *args, **kwargs)

    def error(
        self,
        message: str,
        *args,
        **kwargs
    ) -> None:
        self.add_error(message)
        self.logger.error(message, *args, **kwargs)


def getLogger(
    name:str, 
    root: str = 'orle',
) -> JobLogger:
    """Return a job logger with the specified name, 
    creating it if necessary.

    Args:
        name (str): Name of logging logger instance
        key (str, optional): key of job logger. Defaults to orle.

    Returns:
        JobLogger: ORLE jog logger class
    """
    if not root in LOGS.keys():
        LOGS[root] = RootLog()

    return JobLogger(name, LOGS[root])