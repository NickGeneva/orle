import logging
import os
import time
from typing import Dict, List, Tuple, Union

import numpy as np

from .jlogger import getLogger
from .mods import OpenFoamMods

logger = getLogger(__name__)

Config = Union[Dict, List, Tuple]


class EnvironmentCleaner(object):
    """ Cleans up environment after post processing. Cleaning functions 
    are mod functions, but are ran after the simulation.

    Args:
        config (Config): environment job config
        foam_dir (str): directory path to OpenFOAM simulation
    """
    def __init__(
        self,
        config: Config,
        foam_dir: str,
    ) -> None:
        """Constructor
        """
        self.config = config
        self.dir = foam_dir

    def clean(self, ) -> bool:
        """Clean up simulation

        Returns:
            bool: Successful collection of data
        """
        if not 'clean' in self.config.keys():
            logger.info('No cleaning methods listed. Continuing.')
            return True
        # Loop through each post processing function
        cleared = 1
        for clean in self.config['clean']:
            # Check mod is supported
            if hasattr(OpenFoamMods, clean['func']):
                out = getattr(OpenFoamMods, clean['func']
                              )(**clean['params'], env_dir=self.dir)
                cleared = cleared * out
            else:
                logger.error(
                    'Function {:s} not supported.'.format(clean['func'])
                )
                cleared = 0

        return bool(cleared)
