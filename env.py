import sys
import os
import logging
from orle import Parser, WorldBuilder, OrleProcess

logger = logging.getLogger(__name__)

if __name__ == '__main__':

    sys.argv = sys.argv + ["--config_path", "./orle_universe.yml"]
    sys.argv = sys.argv + ["--world_id", "0"]
    args = Parser().parse()  

    # Setup logging
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=logging.INFO)

    wrld_builder = WorldBuilder(args.config_path)
    wrld_builder.setup_world(args.world_id, args.overwrite_world)
    wrld_config = wrld_builder.get_world_config(args.world_id)


    proc = OrleProcess(wrld_config)
    proc.start()

    # env_builder = EnvironmentBuilder(os.path.join(wrld_config['config_dir'], 'orle_env0.yml'), wrld_config)
    # out = env_builder.setup_env()
    # print(out)

