"""
An example of loading a universe config and running a ORLE process.

Ideally multiple of these programs should run at the same time simulating
multiple environments in the assigned world.
"""
import sys
sys.path.append('..')
import os
import logging

logger = logging.getLogger(__name__)

from orle import Parser, WorldBuilder, OrleProcess

if __name__ == '__main__':

    sys.argv = sys.argv + ["--config_path", "./orle_universe_viscosity.yml"]
    sys.argv = sys.argv + ["--world_id", "0"]
    args = Parser().parse()  

    # Setup logging
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=logging.INFO)

    # Load universe config and build the world
    wrld_builder = WorldBuilder(args.config_path)
    wrld_builder.setup_world(args.world_id, args.overwrite_world)
    wrld_config = wrld_builder.get_world_config(args.world_id)

    # Create ORLE process and run it
    proc = OrleProcess(wrld_config)
    proc.start()

