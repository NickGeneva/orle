import os
import functools
from typing import Dict, List
from shutil import rmtree
from .jlogger import getLogger

logger = getLogger(__name__)

FUNCTION_SUCCESS = True
FUNCTION_ERROR = False


def parallelmod(func):
    """Decorator for mods to edit files in parallel folders if present
    Removes requirement of decomposing/reconstructing domain between runs
    """
    @functools.wraps(func)
    def parallel_mod_wrapper(
        *args, 
        **kwargs,
    ) -> bool:
        # Modify env_dir to sub process folders
        env_dir = kwargs['env_dir']

        if not os.path.exists(env_dir):
            logger.error('Could not find environment directory.')
            return FUNCTION_ERROR

        # Get process folders 
        proc_folders = [os.path.join(env_dir, f) for f in os.listdir(env_dir) \
                         if f.startswith('processor') and os.path.isdir(os.path.join(env_dir, f))]

        # Decomposed environment
        output = FUNCTION_SUCCESS
        if len(proc_folders) > 0:
            # If process folders present loop through them
            for proc_f in proc_folders:
                logger.info( 'Modifying process folder {:s}.'.format(os.path.basename(os.path.normpath(proc_f))) )
                mkwargs = kwargs.copy()
                mkwargs['env_dir'] = proc_f

                if not func(*args, **mkwargs):
                    logger.warning( 'Failed modding process folder {:s}.'.format( proc_f ) )
                    output = FUNCTION_ERROR

        # Non-decomposed environment or failure, always try this in case of decompose force
        output_serial = func(*args, **kwargs)

        if not output:
            logger.warning( 'Failed editting process folders.' ) 
            output = output_serial

        return output

    return parallel_mod_wrapper

class OpenFoamMods:
    """Stores different modification functions for openFOAM simulations
    """
    @classmethod
    def set_control_dict(
        cls,
        props,
        *, env_dir:str
    ) -> bool:
        """Sets core parameters in the control dictionary of simulation.
        This method only edits parameters, it will not add new parameters.

        Args:
            props (Dict): Props to change in the control dict. These props
            must exist in the controlDict to be changed.
            env_dir (str): Path to OpenFOAM simulation. Forced keyword.

        Returns:
            bool: Successful modification
        """
        logger.info('Setting controlDict parameters.')

        control_file = os.path.join(env_dir, 'system', 'controlDict')

        if not os.path.exists(control_file):
            logger.error('Could not find controlDict file to edit.')
            return FUNCTION_ERROR

        # Read in lines
        with open(control_file, 'r') as file:
            lines = file.readlines() 

        # Edit props in control dict
        output = FUNCTION_SUCCESS
        for k, v in props.items():
            edited = False
            for i, line in enumerate(lines):
                if line.lstrip().startswith(k):
                    lines[i] = "{:s}\t\t\t{:s};\n".format(k, str(v))
                    edited = True
                    break

            if not edited:
                logger.warning('Prop {:s} not present in control dict.'.format(k))
                output = FUNCTION_ERROR

        # Write to file
        with open(control_file, 'w') as file:
            file.writelines(lines)

        return output

    @classmethod
    def set_decompose_dict(
        cls,
        props,
        *, env_dir:str
    ) -> bool:
        """Sets parameters in the decompose par dict for parallel simulations.
        This method only edits parameters, it will not add new parameters.

        Args:
            props (Dict): Props to change in the control dict. These props
                must exist in the decomposeParDict to be changed.
            env_dir (str): Path to OpenFOAM simulation folder. Forced keyword.

        Returns:
            bool: Successful modification
        """
        logger.info('Setting decomposeParDict parameters.')

        control_file = os.path.join(env_dir, 'system', 'decomposeParDict')

        if not os.path.exists(control_file):
            logger.error('Could not find decomposeParDict file to edit.')
            return FUNCTION_ERROR

        # Read in lines
        with open(control_file, 'r') as file:
            lines = file.readlines() 

        # Edit props in control dict
        output = FUNCTION_SUCCESS
        for k, v in props.items():
            edited = False
            for i, line in enumerate(lines):
                if line.lstrip().startswith(k):
                    lines[i] = "{:s}\t\t\t{:s};\n".format(k, str(v))
                    edited = True
                    break

            if not edited:
                logger.warning('Prop {:s} not present in decompose dict.'.format(k))
                output = FUNCTION_ERROR

        # Write to file
        with open(control_file, 'w') as file:
            file.writelines(lines)

        return output

    @classmethod
    def set_viscosity(
        cls,
        visc: int,
        *, env_dir: str
    ) -> bool:
        """Sets the viscosity of OpenFOAM environment 

        Args:
            visc (int): Viscosity of the fluid 
            env_dir (str): Path to OpenFOAM simulation folder. Forced keyword.

        Returns:
            bool: Successful modification
        """
        logger.info('Setting viscosity.')

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
    @parallelmod
    def set_boundary(
        cls,
        field: str,
        boundary: str,
        time_step: int,
        props: Dict,
        *, env_dir: str
    ) -> bool:
        """Sets mesh boundary of field to specified property

        Args:
            field (str): Name of the field to edit
            boundary (str): Name of mesh region to edit
            time_step (int): Time-step to edit
            props (Dict): Dictionary of properties to set boundary to
            env_dir (str): Path to OpenFOAM simulation folder. Forced keyword.

        Returns:
            bool: Successful modification
        """
        logger.info('Setting {:s} boundary {:s} parameters.'.format(field, boundary))

        field_file = os.path.join(env_dir, '{:g}'.format(time_step), field)

        if not os.path.exists(field_file):
            logger.warning('Could not find field file {:s} at time-step {:g} to edit.'.format(field, time_step))
            return FUNCTION_ERROR

        # Read in text
        with open(field_file, 'r') as file:
            text = file.read()

        # Find boundary to edit
        start_index = text.find(boundary)
        if start_index == -1:
            logger.error('Boundary {:s} not valid.'.format(boundary))
            return FUNCTION_ERROR
        
        # Search for closing curly bracket
        curly_stack = 0
        end_index = -1
        for i in range(start_index, len(text)):
            if text[i] == "{":
                curly_stack += 1
            elif text[i] == "}":
                curly_stack -= 1
                if curly_stack == 0:
                    end_index = i
                    break

        if end_index == -1:
            logger.error('Curly bracket problem detected.')
            return FUNCTION_ERROR

        # Create editted prop string
        new_prop = "{:s}\n\t{{\n".format(boundary)
        for k, v in props.items():
            new_prop += "\t\t{:s}\t\t{:s};\n".format(k, v)
        new_prop += "\t}"

        text = text[:start_index] + new_prop + text[end_index+1:]

        # Write text
        with open(field_file, 'w') as file:
            file.write(text)

        return FUNCTION_SUCCESS
        

    @classmethod
    @parallelmod
    def set_saved_field_times(
        cls,
        save_interval: float,
        save_times: List,
        *, env_dir: str
    ) -> bool:
        """Retains the specified time-steps that are of a given interval.
        Will delete time-step data that does not satisfy the desired. Typically
        this method should be used for clean up.

        Args:
            save_interval (float): Inteval to keep time-step data at (e.g. 0.5 will
                keep 0.0, 0.5, 1.0, 1.5, etc.)
            save_times (List): List of time-steps to keep, should likely contain the
                last simulation time-step to ensure simulation can continue.
            env_dir (str): Path to OpenFOAM simulation folder. Forced keyword.

        Returns:
            bool: Successful modification
        """
        logger.info('Cleaning up current saved time-step folders.')

        # Get saved time-steps
        time_folders = [float(f) for f in os.listdir(env_dir) if f.replace('.','',1).isnumeric() \
                        and os.path.isdir(os.path.join(env_dir, f))]
        
        # Sort and remove any time state are to be kept
        time_folders.sort()
        if not save_times is None:
            for time in save_times:
                try:
                    time_folders.remove(time)
                except ValueError:
                    pass                

        # Loop through numeric folders and delete any not on desired interval
        for time_step in time_folders:
            if not time_step % save_interval == 0:
                folder_path = os.path.join(env_dir, '{:g}'.format(time_step))
                try:
                    logger.info('Deleting time-step folder {:g}.'.format(time_step))
                    rmtree(folder_path)
                except OSError as e:
                    logger.error('Issue deleting time-step folder: {:s}'.format(e.strerror))
                    return FUNCTION_ERROR

        return FUNCTION_SUCCESS