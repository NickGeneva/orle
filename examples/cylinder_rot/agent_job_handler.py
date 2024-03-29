"""
This is an example of how to set up training/testing loaders with
ORLE jobs. The job class should be modified for each specific numerical
study. Writing configs and reading output files should be handled here. 
"""
import os
import yaml
import hashlib
import logging
import random
import numpy as np

logger = logging.getLogger(__name__)

from typing import List
from filelock import FileLock
from dataclasses import dataclass
from torch.utils.data import Dataset, DataLoader, RandomSampler, SequentialSampler

class ORLEJobBase(object):

    def __init__(
        self,
        solver: str = 'pimpleFoam',
        nproc: int = 1,
        args: str = '',
        reconstruct: bool = False,
        decompose: bool = False,
        env_id: int = 0
    ):
        assert nproc > 0, 'Number of processes needs to be greater than 0.'
        self.solver = solver
        self.nproc = nproc
        self.args = args
        self.reconstruct = reconstruct
        self.decompose = decompose
        self.id = env_id
        self.job_hash = ''
        self.sha = hashlib.sha256()

    def get_env_id(
        self
    ) -> int:
        return self.id
    
    def get_hash(
        self
    ) -> str:
        return self.job_hash

    def write(
        self,
        *args,
        **kwargs
    ):
        raise NotImplementedError("Write method of ORLE job class not overloaded")

    def read(
        self,
        *args,
        **kwargs
    ):
        raise NotImplementedError("Read method of ORLE job class not overloaded")

class CylinderJob(ORLEJobBase):

    def __init__(
        self,
        visc: float,
        env_id: int,
        job_dir: str,
        output_dir: str,
        start_time: float = 0.0,
        end_time: float = 1.0,
        nproc: int = 1,
        reconstruct: bool = False,
        decompose: bool = False
    ):
        assert start_time < end_time, "End time {:g} must be g.r.t. start time {:g}".format( end_time, start_time )
        super().__init__(nproc=nproc, reconstruct=reconstruct, decompose=decompose, env_id=env_id)

        self.visc = visc
        self.job_dir = job_dir
        self.output_dir = output_dir
        # Simulation time range
        self.start_time = start_time
        self.end_time = end_time
        self.stride = round(end_time - start_time, 5)

        # Jet paramters
        default_table = "table (({:g} 0.0))".format(start_time)
        self.omega_table = default_table
        self.omega_target = 0.0

        # Output of job
        self.output = None

    def set_time_range(
        self,
        start_time: float,
        end_time: float
    ):
        assert start_time < end_time, "End time {:g} must be g.r.t. start time {:g}".format( end_time, start_time )
        self.start_time = start_time
        self.end_time = end_time

    def set_time_stride(
        self,
        stride: float
    ):
        assert stride > 0, "Time stride must be greater than zero."

    def stride_time_range(
        self,
    ):
        self.start_time = round(self.end_time, 5)
        self.end_time = round(self.end_time + self.stride, 5)

    def set_omega(
        self,
        omega_end: float,
        omega_start: float = None,
        steps: int = 10
    ):
        """Set the cylinder angular velocity (rad/sec)
        """
        # If no starting velocity magnitude use the previous target
        if omega_start is None:
            omega_start = self.omega_target

        table = ""
        times = np.linspace(self.start_time, self.end_time, steps)
        mags = np.linspace(omega_start, omega_end, steps)
        for i in range(steps):
            table += '({:.04f} {:.04f})'.format(
                times[i], mags[i]
            )

        self.omega_table = "table ("+table+")"
        self.omega_target = omega_end

    def write(
        self,
        job_hash: int = None
    ):
        """Writes a job config for calculating forcing on cylinder

        Args:
            job_hash (int, optional): Unique identifier for this job. Defaults to random int.

        Returns:
            (str): job hash id
        """
        if job_hash is None:
            self.sha.update(bytes(random.randint(0, 100)))
            self.job_hash = self.sha.hexdigest()[:10]
        else:
            self.job_hash = job_hash

        # Make config object
        control_dict = {
            'func':'set_control_dict', 
            'params':{ 
                'props':{ 
                    'startTime': self.start_time, 
                    'endTime': self.end_time 
                } 
            } 
        }

        omega_dict = {
            'func': 'set_boundary', 
            'params':{ 
                'field': 'U', 
                'boundary': 'cylinder', 
                'time_step': self.start_time,
                'props': {
                    'type': 'rotatingWallVelocity',
                    'origin': '(0 0 0.005)',
                    'axis': '(0 0 1)',
                    'omega': self.omega_table
                }
            }
        }
        
        forces = {
            'func': 'get_forces',
            'params': {
                'function_name': 'forces_cylinder',
                'time_step': self.start_time
            }
        }

        coeff = {
            'func': 'get_coeff',
            'params': {
                'function_name': 'forceCoeffs_cylinder',
                'time_step': self.start_time
            }
        }

        probes = {
            'func': 'get_probes',
            'outputname': 'press',
            'params': {
                'function_name': 'probes',
                'field': 'p',
                'time_step': self.start_time
            }
        }

        time_steps = {
            'func': 'set_saved_field_times',
            'params': {
                'save_interval': 0.2,
                'save_times': [0, self.end_time]
            }
        }

        config = {
            'id': self.id,
            'name': 'cylinder',
            'hash': self.job_hash,
            'params': {'solver':self.solver, 'np':self.nproc, 'args':self.args, \
                        'decompose':self.decompose, 'reconstruct':self.reconstruct},
            'mods': [control_dict, omega_dict],
            'post': [forces, coeff, probes],
            'clean': [time_steps]
        }

        config_file = os.path.join(self.job_dir, 'cylinder_env{:d}.{:s}.yml'.format(self.id, self.job_hash))
        logger.info('Writing job config file {:s}'.format(config_file))

        lock = FileLock(config_file+'.lock')
        try:
            with lock.acquire(timeout=1):
                with open(config_file, 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
        except:
            logger.error('Failed to write config file for some reason!')

        # with FileLock(config_file+".lock"):
        #     with open(config_file, 'w') as file:
        #         yaml.dump(config, file, default_flow_style=False)


    def read(
        self
    ):
        """Check job exit status and reads the output files from job

        Returns:
            Dict: Dict of force and pressure data data arrays
        """
        output_path = os.path.join(self.output_dir, "output.{:s}.yml".format(self.job_hash))
        with open(output_path, 'r') as stream:
            try:
                output = yaml.safe_load(stream)
                logger.info( 'Loaded output file for job {:s}'.format(self.job_hash) )
                logger.info( 'Job exited with status {:d} and produced {:d} output files'.format(int(output['status']), len(output['files'])) )
            except yaml.YAMLError as exc:
                logger.error('Error reading the output file!')
                logger.error(exc)
                output = None

        # If we could read the output log and the environment ended with out errors
        # read in data files.
        outputs = {}
        if output and output['status'] == 0: # Zero status = no ORLE issues
            for file in output['files']:
                if 'forces' in file:
                    file_path = os.path.join(self.output_dir, file)
                    data = np.load(file_path, allow_pickle = True)[()]
                    outputs['forces'] = data['forces']
                if 'coeff' in file:
                    file_path = os.path.join(self.output_dir, file)
                    data = np.load(file_path, allow_pickle = True)[()]
                    outputs['coeff'] = data['coeff']
                if 'press' in file:
                    file_path = os.path.join(self.output_dir, file)
                    data = np.load(file_path, allow_pickle = True)[()]
                    outputs['press'] = data['probes']

        return outputs


class JobDataset(Dataset):
    """Creates a PyTorch dataset for ORLE job classes

    Args:
        examples (List): List to environment job objects to train with
    """
    def __init__(
        self, 
        jobs:List,
        inputs:List
    ) -> None:
        super(JobDataset).__init__()
        assert len(jobs) == len(inputs), "Inputs and examples"
        self.jobs = jobs
        self.inputs = inputs

    def __len__(self):
        return len(self.jobs)

    def __getitem__(self, i:int):
        """Returns a ORLE job object
        Args:
            i (int): Training example index
        Returns:
            tuple: input object and ORLE job object
        """
        return self.inputs[i], self.jobs[i]
        
@dataclass
class DataCollator:
    """Data collator for the JobDataset
    """
    def __call__(self, examples):
        print(examples)
        inputs = [example[0] for example in examples]
        jobs = [example[1] for example in examples]
        return {'inputs': inputs, 'jobs': jobs}

@dataclass
class InputMetrics:
    """Simple class for holding history input metrics
    of specified window size
    """
    window: int = 1

    def add(self, name, val):
        if hasattr(self, name):
            attrib = getattr(self, name)
            attrib.append(val)
            if len(attrib) > self.window:
                attrib.pop(0)
            setattr(self, name, attrib)
        else:
            setattr(self, name, [val])

    def get(self, name):
        if hasattr(self, name):
            return getattr(self, name)
        return None

    def has(self, name):
        return hasattr(self, name)

    def delete(self, name):
        if hasattr(self, name):
            delattr(self, name)


class CylinderJobHandler(object):
    """Class for building training and testing dataloaders
    of ORLE job objects

    Args:
        job_dir (str): folder to write job configs to
    """
    def __init__(
        self,
        job_dir:str,
        output_dir:str
    ):
        """Constructor
        """
        self.job_dir = job_dir
        self.output_dir = output_dir

    def create_training_dataloader(
        self,
        viscs: List,
        env_ids: List,
        start_times: List,
        end_times: List,
        nproc: int = 1,
        batch_size: int = 4,
        drop_last:bool = False
    ) -> DataLoader:

        assert len(viscs) == len(env_ids)
        assert len(viscs) == len(start_times)
        assert len(viscs) == len(end_times)

        examples = []
        inputs = []
        for i in range(len(viscs)):
            examples.append(
                CylinderJob(
                    viscs[i],
                    env_ids[i],
                    self.job_dir,
                    self.output_dir ,
                    start_time = start_times[i],
                    end_time = end_times[i],
                    nproc = nproc
                )
            )

            inputs.append(
                InputMetrics(window=5)
            )

        dataset = JobDataset(examples, inputs)

        sampler = RandomSampler(dataset)

        data_collator = DataCollator()

        data_loader = DataLoader(
            dataset,
            batch_size=batch_size,
            sampler=sampler,
            collate_fn=data_collator,
            drop_last=drop_last,
        )

        return data_loader

    def create_testing_dataloader(
        self,
        viscs: List,
        env_ids: List,
        start_times: List,
        end_times: List,
        nproc: int = 1,
        batch_size: int = 4,
        drop_last:bool = False
    ) -> DataLoader:

        assert len(viscs) == len(env_ids)
        assert len(viscs) == len(start_times)
        assert len(viscs) == len(end_times)

        examples = []
        for i in range(len(viscs)):
            examples.append(
                CylinderJob(
                    viscs[i],
                    env_ids[i],
                    self.job_dir,
                    self.output_dir ,
                    start_time = start_times[i],
                    end_time = end_times[i],
                    nproc = nproc
                )
            )

        dataset = JobDataset(examples)

        sampler = SequentialSampler(dataset)

        data_collator = DataCollator()

        data_loader = DataLoader(
            dataset,
            batch_size=batch_size,
            sampler=sampler,
            collate_fn=data_collator,
            drop_last=drop_last,
        )

        return data_loader
        
    

