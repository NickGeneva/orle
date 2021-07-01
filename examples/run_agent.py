"""
This is an example agent script to mimic a RL model

ORLE does not provide agent functions nor should ORLE
even be imported in the agent.
"""
import sys
sys.path.append('..')
import os
import time
import logging
import random
import numpy as np

logger = logging.getLogger(__name__)

from typing import List
from filelock import FileLock
from agent_job_handler import CylinderJobHandler

class JobHelper(object):
    """Helper class for ORLE jobs

    This implementation only supports a single world folder
    """
    def __init__(
        self,
        job_dir: str,
        output_dir: str
    ):
        self.job_dir = job_dir
        self.output_dir = output_dir

    def watch(
        self,
        jobs: List,
        dt: float = 0.1
    ):
        """Watches output folder

        Args:
            jobs (List): List of job objects
            dt (float, optional): Sleep interval
        """
        logger.info('Watching for output files of {:d} jobs.'.format(len(jobs)))

        job_hashes = []
        for job in jobs:
            job_hashes.append(job.get_hash())

        while True:
            # Sleep process before checking for config file again
            time.sleep(dt + 0.001*random.random())

            if not os.path.exists(self.output_dir):
                logger.warning('Could not find directory for environment job files')
                return

            cleared = True
            filenames = [f for f in os.listdir(self.output_dir) \
                if os.path.isfile(os.path.join(self.output_dir, f))]

            output_files = ['output.{:s}.yml'.format(job_id) for job_id in job_hashes]
            for file in output_files:
                # If output file is not in output directory, we need to wait more.
                if not file in filenames:
                    cleared = False

            if cleared:
                break


class Foo_Model(object):

    vel_mags = [1, 2, 1, 2, 0, 1, 0.5, 0]

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
    job_helper = JobHelper(job_dir, output_dir)

    # Create training data-set, ensure consistency with universe config
    viscs = [0.001, 0.002]
    env_ids = [0, 1]
    start_times = [0, 0]
    end_times = [i+0.1 for i in start_times]
    nproc = 8
    job_handler = CylinderJobHandler( job_dir, output_dir )
    training_loader = job_handler.create_training_dataloader( viscs, env_ids, start_times, end_times, \
                            batch_size=1, nproc=nproc )

    # Fake RL agent
    model = Foo_Model()

    for epoch in range(len(model)):
 
        # Process batches
        for mbidx, job_batch in enumerate(training_loader):
            
            inputs = job_batch['inputs']
            jobs = job_batch['jobs']

            # Prediction from NN
            endMag = model(epoch)

            # Modify job params for next run
            for job in jobs:
                job.set_jet('jet1', endMag, steps=5)
                job.set_jet('jet4', endMag, steps=5)

            logger.info('Writing batch job configs.')
            for job in jobs:
                job.write()

            job_helper.watch(jobs)

            forces = []
            for i, job in enumerate(jobs):
                output = job.read()
                if not output is None:
                    forces.append(output['forces'])

                # Add pressure to jobs input metrics
                inputs[i].add('press', output['press'])
            
            logger.info('Lets take a look at the output press')
            print(inputs[0].get('press'))

            # Here you should calculate your loss, backprop and optimize
            # [code here]

            # Move start/stop time forward by stride for next run
            for job in jobs:
                job.stride_time_range()

        time.sleep(3.0)