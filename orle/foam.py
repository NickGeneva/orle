import os
import time

from typing import Dict, List, Tuple, Union 
from .jlogger import getLogger

logger = getLogger('orle')

Config = Union[Dict, List, Tuple]

class FOAMRunner(object):
    """Interfaces with OpenFOAM library
    TODO: Change config input to file path and then load it inside of class? Maybe
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
        if self.config['params']['np'] == 1:
            logger.warning('Using only 1 process, no need to decompose.')
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
        if self.config['params']['np'] == 1:
            logger.warning('Running {:s} on single thread.'.format(self.config['params']['solver']))
            owd = os.getcwd()
            os.chdir(self.dir)
            os.system("{:s} {:s}".format(self.config['params']['solver'], 
                    self.config['params']['args']))
            os.chdir(owd)
        # Parallel
        else:
            logger.warning('Running {:s} in parallel.'.format(self.config['params']['solver']))
            owd = os.getcwd()
            os.chdir(self.dir)
            os.system("mpirun -np {:d} {:s} -parallel {:s}".format(
                    self.config['params']['np'], self.config['params']['solver'], 
                    self.config['params']['args']))
            os.chdir(owd)
    
    def reconstruct(
        self
    ) -> None:
        """Reconstructs OpenFOAM field from parallel folders
        TODO: Figure out good way of controlling this (not all parallel sims need reconstruction)
        """
        if self.config['params']['np'] == 1:
            logger.warning('Using only 1 process, no need to reconstruct.')
            return
        
        owd = os.getcwd()
        os.chdir(self.dir)
        os.system("reconstructPar")
        os.chdir(owd)