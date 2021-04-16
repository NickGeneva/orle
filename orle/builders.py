import os
import yaml
import logging

logger = logging.getLogger(__name__)

from typing import Dict, List, Tuple, Union 
from distutils.dir_util import copy_tree
from shutil import rmtree
from .utils import clean_config, mkdirs
from .mods import OpenFoamMods

Config = Union[Dict, List, Tuple]

class WorldBuilder(object):
    """Builds world containers to hold environments

    Args:
        config_file_path (str): path to universe configuration file
    """

    def __init__(
        self,
        config_file_path: str
    ) -> None:
        """Constructor
        """
        self.config = self.parse_config(config_file_path)

    def parse_config(
        self,
        config_file_path: str
    ) -> Config:
        """Parses the universe config file and returns a native python dictionary
        containing the configuration.

        Args:
            config_file_path (str): path to universe configuration file

        Returns:
            Config: Python config object
        """
        assert os.path.exists(config_file_path), "Configuration file does not exist."

        with open(config_file_path, 'r') as stream:
            try:
                config = yaml.safe_load(stream)
                logger.info( 'Parsed universe config file: {:s}; v.{:s}.'.format(
                        config['name'], config['version']) )
            except yaml.YAMLError as exc:
                logger.error('Error reading the universe configuration file!')
                logger.error(exc)

        return clean_config(config)

    def init_world(
        self,
        id: int,
        overwrite: bool = False
    ) -> Config:
        """Initialized the world, creates directory and env folder
        if they do not already exist.

        Args:
            id (int): World id
            overwrite (bool, optional): Recreate world directory even it exists. Defaults to False.

        Returns:
            Config: Initialized world configuration
        """
        # Get world config
        world_config = self.get_world_config(id)

        # Create world directory if not initialized
        if overwrite or not self.check_world(world_config):
            logger.warn('Cleaning and building world.')
            self.delete_world(world_config)
            self.build_world(world_config)

    def get_world_config(
        self,
        id:int
    ) -> Config:
        """Gets world configuration dictionary from universe config

        Args:
            id (int): World id

        Raises:
            LookupError: If world ID is not found in the universal config

        Returns:
            Config: World configuration
        """
        worlds = self.config['worlds']

        for world in worlds:
            if world['id'] == id:
                return world
        
        logger.error('World ID {:d} not present in universe config file.'.format(id))
        raise LookupError('Invalid id')

    def check_world(
        self,
        world_config: Config
    ) -> bool:
        """Checks if world folders are already set up

        Args:
            world_config (Config): Configuration object of the world

        Returns:
            bool: World is set up
        """
        # Check if folders exist
        if not os.path.exists(world_config['world_dir']):
            return False
        if not os.path.exists(world_config['command_dir']):
            return False
        if not os.path.exists(world_config['output_dir']):
            return False
        if not os.path.exists(os.path.join(world_config['world_dir'], 'base_files')):
            return False

        # Check environment folders
        for env in world_config['envs']:
            # Create folder
            env_dir = os.path.join(world_config['world_dir'], env['name'])
            if not os.path.exists(env_dir):
                return False

        logger.info('All world folders appear to be set-up.')
        return True

    def delete_world(
        self,
        world_config: Config
    ) -> None:
        """Deletes contents of world folder

        Args:
            world_config (Config): Configuration object of the world

        Returns:
            bool: World is set up
        """
        try:
            logger.warn('Deleting world contents.')
            rmtree(world_config['world_dir'])
        except OSError as e:
            logger.error('Error deleting world contents: {:s}'.format(e.strerror))

    def build_world(
        self,
        world_config: Config
    ) -> None:

        # Create world directory
        world_files = os.path.join(world_config['world_dir'], 'base_files')
        mkdirs(world_config['world_dir'], world_config['command_dir'], world_config['output_dir'], world_files)

        # Copy basefiles into world folder
        logger.info('Copying base files into world.')
        if os.path.exists(world_config['base_files']):
            logging.info('Copying base files to local world folder.')
            copy_tree(world_config['base_files'], world_files, update=1)
        
        # Create each environment in the world
        cleared = 1
        for env in world_config['envs']:
            logger.info('Creating environment {:d}.'.format(env['id']))
            # Create folder
            env_dir = os.path.join(world_config['world_dir'], env['name'])
            mkdirs(env_dir)
            # Copy base files into environment
            copy_tree(world_files, env_dir, update=1)
            # Now run through modifications
            for mod in env['mods']:
                # Check mod is supported
                if hasattr(OpenFoamMods, mod['func']):
                    out = getattr(OpenFoamMods, mod['func'])(**mod['params'], env_dir=env_dir)
                    cleared = cleared * out
                else:
                    logger.error('Function {:s} not supported.'.format(mod['func']))
                    cleared = 0

        if cleared:
            logger.info('Successfully set up environments.')
        else:
            logger.warn('Problem detected setting up environments.')


