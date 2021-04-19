import os
import time
import logging

logger = logging.getLogger(__name__)

from typing import Dict, List, Tuple, Union 

Config = Union[Dict, List, Tuple]

class FOAMRunner(object):
    """Interfaces with OpenFOAM library
    TODO: Validate parallel
    Args:
        config (Config): environment job config
        foam_dir (str): directory path to OpenFOAM simulation
    """
    def __init__(
        self,
        config: Config,
        foam_dir: str
    ) -> None:
        """Constructor
        """
        self.config = config
        self.dir = foam_dir

    def decompose(
        self
    ) -> None:
        """Decomposes fluid simulation domain into sub folders
        """
        if self.config['np'] == 1:
            logger.warn('Using only 1 process, no need to decompose.')
            return
        # Run openfoam command
        owd = os.getcwd()
        os.chdir(self.dir)
        os.system("decomposePar -force")
        os.chdir(owd)

    def run(
        self,
    ) -> None:
        """Runs the OpenFOAM simulation
        """
        # Single core
        if self.config['np'] == 1:
            logger.warn('Running {:s} on single thread.'.format(self.config['solver']))
            owd = os.getcwd()
            os.chdir(self.dir)
            os.system(self.config['solver'])
            os.chdir(owd)
        # Parallel
        else:
            logger.warn('Running {:s} in parallel.'.format(self.config['solver']))
            owd = os.getcwd()
            os.chdir(self.dir)
            os.system("mpirun -np {:d} {:s} -parallel".format(self.config['np'], self.config['solver']))
            os.chdir(owd)
    
    def reconstruct(
        self
    ) -> None:
        """Reconstructs OpenFOAM field from parallel folders
        TODO: Figure out good way of controlling this (not all parallel sims need reconstruction)
        """
        if self.config['np'] == 1:
            logger.warn('Using only 1 process, no need to reconstruct.')
            return
        
        owd = os.getcwd()
        os.chdir(self.dir)
        os.system("reconstructPar")
        os.chdir(owd)