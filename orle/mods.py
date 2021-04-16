import os
import logging
logger = logging.getLogger(__name__)

from typing import Dict

FUNCTION_SUCCESS = True
FUNCTION_ERROR = False

class OpenFoamMods:
    
    @classmethod
    def set_viscosity(
        cls,
        visc: int,
        env_dir: str
    ) -> bool:
        """Sets the viscosity of OpenFOAM environment 

        Args:
            visc (int): Viscosity of the fluid 
            env_dir (str): Path to OpenFOAM simulation folder

        Returns:
            bool: Successfull modification
        """
        transport_file = os.path.join(env_dir, 'constant', 'transportProperties')

        if not os.path.exists(transport_file):
            logger.error('Could not find transportProperties file to edit viscosity.')
            return FUNCTION_ERROR

        # Read in lines
        with open(transport_file, 'r') as file:
            lines = file.readlines()

        # Find one with viscosity setting (nu)
        for i, line in enumerate(lines):
            if 'nu' in line:
                lines[i] = 'nu\t\t\t\t {:.08f};'.format(visc)

        # Write to file
        with open(transport_file, 'w') as file:
            file.writelines(lines)

        return FUNCTION_SUCCESS

    @classmethod
    def set_boundary(
        cls,
        field: str,
        boundary: str,
        time_step: int,
        prop: Dict,
        env_dir: str
    ) -> bool:
        """Sets mesh boundary of field to specified property

        Args:
            field (str): Name of the field to edit
            boundary (str): Name of mesh region to edit
            time_step (int): Time-step to edit
            prop (Dict): Dictionary of properties to set boundary to
            env_dir (str): Path to OpenFOAM simulation folder

        Returns:
            bool: Successfull modification
        """
        transport_file = os.path.join(env_dir, 'constant', 'transportProperties')


        return FUNCTION_SUCCESS