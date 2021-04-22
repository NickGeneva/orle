import os
import time
import random
import logging

from typing import Dict, List, Tuple, Union 
from filelock import Timeout, FileLock
from .builders import EnvironmentBuilder
from .foam import FOAMRunner
from .collectors import DataCollector
from .jlogger import getLogger

logger = getLogger('orle')

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
        self.job_config = None
        self.env_dir = None

    def start(
        self,
        dt: int = 0.1
    ) -> None:
        """Start the process's activity

        Args:
            dt (int, optional): Sleep interval between . Defaults to 0.1.
        """
        logger.info('Starting surveillance for job configs.')
        while True:
            # Sleep process before checking for config file again
            time.sleep(dt + 0.001*random.random())
            # Check to see if job is available
            if self.search():
                # Run job
                self.run()
                # Clean up
                self.clean()
                # All done
                logger.info('Done processing, job script, resuming surveillance.')

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

        filenames = [f for f in os.listdir(self.config['job_dir']) if os.path.isfile(os.path.join(self.config['job_dir'], f))]
        for filename in filenames:
            file_path = os.path.join(self.config['job_dir'], filename)
            # Only attempt to parse yml files
            if file_path.endswith('.yml'):
                self.lock = FileLock(file_path+'.lock')

                # Call hidden function, regular .aquire() is blocking call without Timeout
                self.lock._acquire()
                if self.lock.is_locked:
                    self.lock.acquire()
                    self.job_file = file_path

                    logger.info('Acquired job config {:s}'.format(filename))
                    return True
        
        return False

    def run(
        self
    ) -> None:
        """Set up and run environment job
        """
        # Reset output file logger
        logger.clean()

        output_flag = self.job_setup()
        if not output_flag:
            logger.error('Failed job set up, terminating run')
            return

        output_flag = self.job_sim()
        if not output_flag:
            logger.error('Failed job execution, terminating run')
            return

        output_flag = self.job_post()
        if not output_flag:
            logger.error('Failed post processing, terminating run')
            return

    def clean(
        self
    ) -> None:
        """Cleans up configs
        """
        # Rename job file to keep in history
        old_count = 0
        for (dirpath, _, filenames) in os.walk(self.config['job_dir']):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if file_path.startswith(self.job_file+".old"):
                    old_count += 1

        os.rename(self.job_file, self.job_file+".old.{:d}".format(old_count))

        # Now release lock
        # Need to force because of double acquire
        self._lock_counter = 1
        self.lock.release(force = True)
        os.remove(self.lock._lock_file)
        self.lock = None

    def job_setup(
        self
    ) -> bool:
        """Sets up environment for running

        Returns:
            bool: Successful setup
        """
        logger.info('Setting up environment folder.')
        env_builder = EnvironmentBuilder(self.job_file, self.config)
        self.env_dir = env_builder.env_dir
        self.job_config = env_builder.config
        # Make sure necessary params are in the config
        if not env_builder.validate_config():
            return False

        logger.info('Valid job config file file loaded. Setting up environment folder.')
        return env_builder.setup_env()

    def job_sim(
        self
    ) -> bool:
        """Runs openfoam simulation

        Returns:
            bool: Successful setup
        """
        runner = FOAMRunner(self.job_config, self.env_dir)
        # Decompose domain
        runner.decompose()
        # Run simulation
        runner.run()
        # Reconstruct domain if needed
        runner.reconstruct()

        return True

    def job_post(
        self
    ) -> bool:
        """Runs openfoam simulation

        Returns:
            bool: Successful setup
        """

        collector = DataCollector(self.job_config, self.env_dir, self.config['output_dir'])

        # Collect data
        out = collector.collect()



        return out