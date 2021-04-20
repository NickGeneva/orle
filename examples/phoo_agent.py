"""
This is an example agent script to mimic a RL model

For now ORLE does not provide agent functions, will
try to integrate certain methods in the future, maybe
a helper class
"""
import sys
sys.path.append('..')
import os
import random
import time
import yaml
import logging
import numpy as np

logger = logging.getLogger(__name__)

from typing import List
from filelock import FileLock

class ORLE_Helper(object):

    """Helper class for ORLE

    This implementation only supports a single world folder
    """
    def __init__(
        self,
        job_dir: str,
        output_dir: str
    ):
        self.job_dir = job_dir
        self.output_dir = output_dir
        
    def write_job(
        self,
        start_time: int,
        end_time: int,
        jet1_table: str,
        jet4_table: str,
        env_id: int = 0,
        job_hash:int = None
    ):
        """Writes a job config for calculating forcing on cylinder

        Args:
            start_time (int): Simulation start time
            end_time (int): Simulation end time
            jet1_table (str): jet 1 boundary velocity table
            jet4_table (str): jet 4 boundary velocity table
            env_id (int, optional): Environment id. Defaults to 0.
            job_hash (int, optional): Unique identifier for this job. Defaults to random int.
        """
        if job_hash is None:
            job_hash = random.randint(0, 100000)

        # Make config object
        control_dict = {
            'func':'set_control_dict', 
            'params':{ 
                'props':{ 
                    'startTime': start_time, 
                    'endTime': end_time 
                } 
            } 
        }
        set_boundary_1 = {
            'func': 'set_boundary', 
            'params':{ 
                'field': 'U', 
                'boundary': 'jet1', 
                'time_step': start_time,
                'props': {
                    'type': 'uniformFixedValue',
                    'uniformValue': jet1_table
                }
            }
        } 

        set_boundary_4 = {
            'func': 'set_boundary',
            'params':{ 
                'field': 'U', 
                'boundary': 'jet4', 
                'time_step': start_time,
                'props': {
                    'type': 'uniformFixedValue',
                    'uniformValue': jet4_table
                }
            }
        } 

        forces = {
            'func': 'get_forces',
            'params': {
                'boundary': 'cylinder',
                'time_step': start_time
            }
        }

        config = {
            'id': env_id,
            'name': 'cylinder',
            'hash': job_hash,
            'params': {'solver':'pimpleFoam', 'np':1, 'args':''},
            'mods': [control_dict, set_boundary_1, set_boundary_4],
            'post': [forces]
        }

        config_file = os.path.join(self.job_dir, 'cylinder_env{:d}.yml'.format(env_id))
        with FileLock(config_file+".lock"):
            with open(config_file, 'w') as file:
                yaml.dump(config, file, default_flow_style=False)

        output_filenames = ["forces{:d}.npy".format(job_hash)]
        return output_filenames

    def calc_velocity_table(
        self,
        start_time: float,
        end_time: float,
        start_vmag: float,
        end_vmag: float,
        steps: int ,
        normal = [1, 0, 0]
    ) -> str:
        """Creates a simple velocity ramp table for OpenFOAM boundary

        Args:
            start_time (float): [description]
            end_time (float): [description]
            start_vmag (float): [description]
            end_vmag (float): [description]
            steps (int): [description]
            normal (list, optional): [description]. Defaults to [1, 0, 0].

        Returns:
            (str): table for OpenFOAM field file
        """
        table = ""
        times = np.linspace(start_time, end_time, steps)
        mags = np.linspace(start_vmag, end_vmag, steps)
        for i in range(steps):
            table += '({:.04f} ({:.04f} {:.04f} {:.04f}))'.format(
                times[i], mags[i]*normal[0], mags[i]*normal[1], mags[i]*normal[2]
            )

        return "table ("+table+")"

    def watch(
        self,
        output_files: List,
        dt: float = 0.1
    ):
        """Watches output folder

        Args:
            output_files (List): List of file names to watch for only proceed when all are present
            dt (float, optional): Sleep interval
        """
        logger.info('Watching for output files.')

        while True:
            # Sleep process before checking for config file again
            time.sleep(dt + 0.001*random.random())

            if not os.path.exists(self.output_dir):
                logger.warning('Could not find directory for environment job files')
                return

            cleared = True
            filenames = [f for f in os.listdir(self.output_dir) \
                if os.path.isfile(os.path.join(self.output_dir, f))]

            for file in output_files:
                # If output file is not in output directory, we need to wait more.
                if not file in filenames:
                    cleared = False

            if cleared:
                break

    def read_outputs(
        self,
        file_names: List
    ) -> List:
        """Reads in numpy output files from ORLE

        Args:
            file_names (List): List of file names

        Returns:
            List: List of numpy arrays
        """
        arrays = []

        for file in file_names:
            file_path = os.path.join(self.output_dir, file)
            arrays.append(np.load(file_path, allow_pickle = True))

        return arrays


class Phoo_Model(object):

    vel_mags = [1, 2, 0]

    def __call__(self, i:int):
        return self.vel_mags[i]

    def __len__(self):
        return len(self.vel_mags)

if __name__ == '__main__':


    # Setup logging
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=logging.INFO)

    job_dir = "./world0/configs"
    output_dir = "./world0/outputs"
    orle_helper = ORLE_Helper(job_dir, output_dir)

    # Dictionary mapping between environment ID and Reynolds number
    env_dict = {0: 100, 1: 200}
    tsteps = [0., 1., 2., 3.]
    model = Phoo_Model()
    
    endMag = 0
    for i in range(len(model)):
        startMag = endMag
        endMag = model(i) # Prediction from NN

        jet1_table = orle_helper.calc_velocity_table(tsteps[i], tsteps[i+1], startMag, endMag, 10, [-1, 1, 0])
        jet4_table = orle_helper.calc_velocity_table(tsteps[i], tsteps[i+1], startMag, endMag, 10, [-1, -1, 0])
        
        # Submit both environment jobs
        output_files = []
        for j in env_dict.keys():
            output_file = orle_helper.write_job(
                tsteps[i], 
                tsteps[i+1],
                jet1_table,
                jet4_table,
                env_id=j
            )
            output_files = output_files + output_file

        # Now wait for files
        orle_helper.watch(output_files)

        files = orle_helper.read_outputs(output_files)

        logger.info("Looks like we got some data files...")
        for file in files:
            print(file)

        time.sleep(3.0)