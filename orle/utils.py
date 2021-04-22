import os
import errno

from collections.abc import Iterable
from typing import Dict, List, Tuple, Union 
from .jlogger import getLogger

logger = getLogger('orle')

Config = Union[Dict, List, Tuple]

# Since $WORLD may depend on $LOCAL place it first.
CONFIG_VARS = {
    "$WORLD": os.getcwd(),
    "$LOCAL": os.getcwd()
}

def clean_config(
    config: Config
) -> Config:
    """Cleans up configuration file replacing any defined variables

    Args:
        config (Config): Parsed universe config file

    Returns:
        Config: Cleaned config
    """

    def config_search(config):
        """Simple depth first search of config object
        """
        if isinstance(config, dict):
            # If this is world dict, update path variable
            if "world_dir" in config.keys():
                CONFIG_VARS['$WORLD'] = config['world_dir']

            for k, v in config.items():
                config[k] = config_search(v)     
        elif isinstance(config, list):
            for i, v in enumerate(config):
                config[i] = config_search(v)
        else:
            if isinstance(config, str):
                for k, v in CONFIG_VARS.items():
                    config = config.replace(k, v)

        return config

    return config_search(config)


def mkdirs(
    self, 
    *directories
) -> None:
    """Makes directories if it does not exist

    Args:
        directors (str...): a sequence of strings of file paths to create 
    """
    for directory in list(directories):
        try:
            os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise