import sys
import logging
from orle import Parser, WorldBuilder

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
    
    wrld_builder.init_world(args.world_id, args.overwrite_world)
