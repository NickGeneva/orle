import os
import numpy as np


from typing import Dict, List, Tuple, Union
from .jlogger import getLogger

logger = getLogger(__name__)

FUNCTION_ERROR = None
FILE_NAMES = {
    'get_forces': 'forces'
}

class OpenFoamPost:

    @classmethod
    def get_forces(
        cls,
        function_name: str,
        time_step: int,
        _env_dir: str
    ) -> Union[Dict, None]:
        """Extracts forcing values from OpenFOAM files

        Args:
            function_name (str): Name of the force function in the controlDict
            time_step (int): initial time-step of simulation
            env_dir (str): Path to OpenFOAM simulation folder, (do not set this in config file)

        Returns:
            Dict: Dictionary of numpy arrays
        """
        logger.info('Getting forcing data from OpenFOAM simulation.')
        def para_search(sub_string:str) -> Tuple[List, int]:
            """Helper recurssion method for building embedded lists 
            from paranthesis sets

            Args:
                sub_string (str): current sub-string

            Returns:
                Tuple: embedded lists of extracted numbers, current index of string
            """
            list0 = []
            num_str = ""
            i = 0
            while i < len(sub_string):
                char = sub_string[i]
                if char == '(':
                    sub_list, j = para_search(sub_string[i+1:])
                    list0.append(sub_list)
                    # Jump index forward for interval we processed
                    i += j + 1
                elif char == ')':
                    if len(num_str) > 0:
                        list0.append(float(num_str))
                    return list0, i
                elif char == ' ':
                    if len(num_str) > 0:
                        list0.append(float(num_str))
                    num_str = ""
                else:
                    num_str += char
                i += 1
            return list0, _


        force_folder = os.path.join(_env_dir, 'postProcessing', function_name, '{:g}'.format(time_step))
        filenames = [os.path.join(force_folder, f) for f in os.listdir(force_folder) \
                         if f.startswith('forces')]
        # Get the latest editted force data file
        force_file = max(filenames, key=os.path.getctime)

        if not os.path.exists(force_file):
            sub_folder = os.path.join('postProcessing', function_name, 
                            '{:g}'.format(time_step))
            logger.error('Could not find forces.dat file to in {:s}.'.format(sub_folder))
            return FUNCTION_ERROR

        # Read in lines
        with open(force_file, 'r') as file:
            lines = file.readlines()

        # Extract force data
        times = []
        forces = []
        for _, line in enumerate(lines):
            # Process line if not comment and first word is a valid number (time-step)
            if not line.startswith('#') and line.split(' ')[0].replace('.','',1).isnumeric():
                # Get time-step
                times.append(float(line.split(' ')[0])) 
                
                # Build nested list of force data
                sIdx = line.find('(')
                eIdx = line.rfind(')')+1
                force_step, _ = para_search(line[sIdx:eIdx])
                forces.append( force_step )

        return {'times': np.array(times), 'forces':np.array(forces)}
                        