import os
import time
import logging
import numpy as np
logger = logging.getLogger(__name__)

from typing import Dict, List, Tuple, Union
from .post import OpenFoamPost, FILE_NAMES

Config = Union[Dict, List, Tuple]


class DataCollector(object):
    """ Collects data from OpenFOAM sim and writes it to numpy arrays
    in the specified output folder.

    Args:
        config (Config): environment job config
        foam_dir (str): directory path to OpenFOAM simulation
    """
    def __init__(
        self,
        config: Config,
        foam_dir: str,
        output_dir: str
    ) -> None:
        """Constructor
        """
        self.config = config
        self.dir = foam_dir
        self.output_dir = output_dir

    def collect(
        self,
    ) -> bool:
        """Collect post processing data

        Returns:
            bool: Successful collection of data
        """
        # Loop through each post processing function
        cleared = 1
        for post in self.config['post']:
            # Check mod is supported
            if hasattr(OpenFoamPost, post['func']):
                out = getattr(OpenFoamPost, post['func'])(**post['params'], _env_dir=self.dir)
                cleared = cleared * (not out is None)

                file_name =  FILE_NAMES[post['func']] + str(self.config['hash']) + '.npy'
                file_path = os.path.join(self.output_dir, file_name)
                if os.path.exists(file_path):
                    logger.warn('Output file {:s} exists, overwriting.'.format(file_name))
                    os.remove(file_path)
                
                logger.info('Writing {:s} to disk.'.format(file_name))
                # Save data to numpy array
                np.save(file_path, out, allow_pickle=True)

            else:
                logger.error('Function {:s} not supported.'.format(post['func']))
                cleared = 0

        return bool(cleared)