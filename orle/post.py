import os
import re
import numpy as np

from typing import Dict, List, Tuple, Union
from .jlogger import getLogger

logger = getLogger(__name__)

FUNCTION_ERROR = None
FILE_NAMES = {
    'get_forces': 'forces',
    'get_probes': 'probes'
}


class OpenFoamPost:

    @classmethod
    def get_forces(
        cls,
        function_name: str,
        time_step: int,
        *, env_dir: str
    ) -> Union[Dict, None]:
        """Extracts forcing values from OpenFOAM files

        Args:
            function_name (str): Name of the force function in the controlDict
            time_step (int): initial time-step of simulation
            env_dir (str): Path to OpenFOAM simulation folder. Forced keyword.

        Returns:
            Dict: Dictionary of numpy arrays
        """
        logger.info('Getting forcing data from OpenFOAM simulation.')
        def para_search(sub_string:str) -> Tuple[List, int]:
            """Helper recursion method for building embedded lists 
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


        force_folder = os.path.join(env_dir, 'postProcessing', function_name, '{:g}'.format(time_step))
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
                        
    @classmethod
    def get_probes(
        cls,
        function_name: str,
        field: str,
        time_step: int,
        *, env_dir: str
    ) -> Union[Dict, None]:
        """Extracts probing data from OpenFOAM files

        Args:
            function_name (str): Name of the force function in the controlDict
            field (str): Name of the field to get probes from
            time_step (int): initial time-step of simulation
            env_dir (str): Path to OpenFOAM simulation folder. Forced keyword.

        Returns:
            Dict: Dictionary of numpy arrays
        """

        def probe_parse(split_string:List) -> List:
            """Helper method for parsing probe data of varying dimensionality

            Args:
                split_string (List): List of words on line already split based
                    on white space
            """
            list_stack = [[]]
            i = 0
            while i < len(split_string):
                word = split_string[i]
                
                num = ""
                for j in range(len(word)):
                    letter = word[j]
                    if letter == '(':
                        list_stack.append([])
                    elif letter == ')':
                        list0 = list_stack.pop()
                        list_stack[-1].append(list0)
                    else:
                        num += letter
                        if j+1 == len(word) or word[j+1] == ")":
                            list_stack[-1].append(float(num))
                            num = ""
                i += 1
            return list_stack[0]

        probe_file = os.path.join(env_dir, 'postProcessing', function_name, '{:g}'.format(time_step), field)
        if not os.path.exists(probe_file):
            logger.error('Could not find {:s} probe file for at time-step {:s}.'.format(field, '{:g}'.format(time_step)))
            return FUNCTION_ERROR

        # Read in lines
        with open(probe_file, 'r') as file:
            lines = file.readlines()

        # Extract force data
        times = []
        probes = []
        for _, line in enumerate(lines):
            # Split line by white spaces
            line = line.lstrip()
            line = re.findall(r'\S+', line)
            if len(line) == 0:
                continue

            # Process line if not comment and first word is a valid number (time-step)
            if not line[0].startswith('#') and line[0].replace('.','',1).isnumeric():
                # Build multi-dim list based on paranthesis
                probe_step = probe_parse(line[1:])

                times.append(float(line[0]))
                probes.append(probe_step)

        return {'times': np.array(times), 'probes':np.array(probes)}
