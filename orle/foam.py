import os
import re
import time
from typing import Dict, List, Tuple, Union

from .jlogger import getLogger
from .mods import OpenFoamMods

logger = getLogger(__name__)

Config = Union[Dict, List, Tuple]

class FOAMRunner(object):
    """Interfaces with OpenFOAM library

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
        self,
        force: bool = False
    ) -> None:
        """Decomposes fluid simulation domain into sub folders

        Args:
            force (bool, Optional) Force domain decompose. Defaults to False.
        """
        if self.config['params']['np'] == 1:
            logger.warning('Using only 1 process, no need to decompose.')
            return
        
        # First get the start time from control dict
        start_time = self.get_start_timestep()

        # Set decomposeParDict to number of procs for consistency
        cleared = OpenFoamMods.set_decompose_dict({"numberOfSubdomains": self.config['params']['np']}, env_dir=self.dir)
        if cleared == 0:
            logger.warning('Failed to successfully modify the decomposeParDict.')

            
        # Validate the existing processor folders
        proc_folders = [os.path.join(self.dir, f) for f in os.listdir(self.dir) \
                         if f.startswith('processor') and os.path.isdir(os.path.join(self.dir, f))]

        folders = True
        if not len(proc_folders) == self.config['params']['np']:
            logger.warning( 'Inconsistent number of processor folders found, forcing decomposePar.' )
            folders = False
        else:
            # If consistent processor folders, check each for initial time-step folder
            for i in range(self.config['params']['np']):
                proc_folder = os.path.join(self.dir, 'processor{:d}'.format(i), '{:g}'.format(start_time))
                if not os.path.exists(proc_folder):
                    logger.warning( 'Necessary process folder {:s} not found, forcing decomposePar.'.format(proc_folder))
                    folders = False
                    break
        
        if not folders or self.config['params']['decompose'] or force:
            logger.warning('Decomposing domain.')
            # Run openfoam command
            owd = os.getcwd()
            os.chdir(self.dir)
            os.system("decomposePar -force -time '0, {:g}'".format(start_time))
            os.chdir(owd)

            time.sleep(0.1)

    def run(
        self,
    ) -> None:
        """Runs the OpenFOAM simulation
        """
        # Set the control application field for consistency
        OpenFoamMods.set_control_dict({'application': self.config['params']['solver']}, env_dir=self.dir)

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
        """
        if self.config['params']['np'] == 1:
            logger.warning('Using only 1 process, no need to reconstruct.')
            return

        if self.config['params']['reconstruct'] == False:
            return
        
        time = self.get_end_timestep()

        owd = os.getcwd()
        os.chdir(self.dir)
        os.system( "reconstructPar -time {:g}".format( time ) )
        os.chdir(owd)


    def get_start_timestep(
        self
    ) -> float:
        """Gets the starting timestep from controlDict

        Returns:
            float: Starting time-step
        """
        control_file = os.path.join(self.dir, 'system', 'controlDict')

        if not os.path.exists(control_file):
            logger.error('Could not find controlDict file to edit.')
            return 0

        # Read in lines
        with open(control_file, 'r') as file:
            lines = file.readlines() 

        for _, line in enumerate(lines):
            if line.lstrip().startswith("startTime"):
                start_time = float(re.findall(r'\d*\.?\d+', line)[0])
                return start_time
        
        return 0   

    def get_end_timestep(
        self
    ) -> float:
        """Gets the ending timestep from controlDict

        Returns:
            float: Ending time-step
        """
        control_file = os.path.join(self.dir, 'system', 'controlDict')

        if not os.path.exists(control_file):
            logger.error('Could not find controlDict file to edit.')
            return 0

        # Read in lines
        with open(control_file, 'r') as file:
            lines = file.readlines() 

        for _, line in enumerate(lines):
            if line.lstrip().startswith("endTime"):
                end_time = float(re.findall(r'\d*\.?\d+', line)[0])
                return end_time
        
        return 0  