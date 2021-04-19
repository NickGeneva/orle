import os
import time
import random
import logging

logger = logging.getLogger(__name__)

from typing import Dict, List, Tuple, Union 
from filelock import Timeout, FileLock
from .builders import EnvironmentBuilder

Config = Union[Dict, List, Tuple]

class OrleProcess(object):
    """A ORLE process for running environments

    Args:
        world_config (Config): Initialized world configuration this process will operate on
    """
    def __init__(
        self,
        world_config
    ) -> None:
        """Constructor
        """
        self.config = world_config
        self.lock = None
        self.job_file = None

    def start(
        self,
        dt: int = 0.1
    ) -> None:
        """Start the process's activity

        Args:
            dt (int, optional): Sleep interval between . Defaults to 0.1.
        """
        while True:
            # Sleep process before checking for config file again
            time.sleep(dt + 0.001*random.random())
            # Check to see if job is available
            if self.search():
                # Run job
                self.run()
                # Clean up
                self.clean()

            break

    def search(
        self
    ) -> bool:
        """Searches the world's config folder for new jobs

        Returns:
            bool: If a job config was found
        """
        if not os.path.exists(self.config['job_dir']):
            logger.warning('Could not find directory for environment job files')
            return False

        for (dirpath, dirnames, filenames) in os.walk(self.config['job_dir']):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                # Only attempt to parse yml files
                if file_path.endswith('.yml'):
                    self.lock = FileLock(file_path+'.lock')
                    
                    # Call hidden function, regular .aquire() is blocking call without Timeout
                    self.lock._acquire()
                    if self.lock.is_locked:
                        self.lock.acquire()
                        self.job_file = file_path

                        logging.info('Acquired job config {:s}'.format(filename))
                        return True
        return False

    def run(
        self
    ) -> None:
        """Set up and run environment job
        """
        output_flag = self.job_setup()
        if not output_flag:
            logger.error('Failed job set up, terminating run')

        output_flag = self.job_sim()
        if not output_flag:
            logger.error('Failed job execution, terminating run')

    def clean(
        self
    ) -> None:
        """Cleans up environment and config
        TODO: Implement
        """
        pass

    def job_setup(
        self
    ) -> bool:
        """Sets up environment for running

        Returns:
            bool: Successful setup
        """
        logger.info('Setting up environment folder.')
        env_builder = EnvironmentBuilder(self.job_file, self.config)

        if not env_builder.validate_config():
            return False
        
        logger.info('Valid job config file file loaded. Building environment folder.')
        return env_builder.setup_env()

    def job_sim(
        self
    ) -> bool:
        """Runs openfoam simulation

        Returns:
            bool: Successful setup
        """

        return True