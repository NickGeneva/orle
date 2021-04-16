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

    def setup_world(
        self,
        id: int,
        overwrite: bool = False
    ) -> bool:
        """Initialize the world, creates directory and env folder
        if they do not already exist.

        Args:
            id (int): World id
            overwrite (bool, optional): Recreate world directory even it exists. Defaults to False.

        Returns:
            bool: World is setup without issues
        """
        # Get world config
        world_config = self.get_world_config(id)

        # Create world directory if not initialized
        if overwrite or not self.check_world(world_config):
            logger.warn('Cleaning and building world.')
            self.delete_world(world_config)
            built = self.build_world(world_config)
        else:
            built = True
        
        return built

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
        if not os.path.exists(world_config['config_dir']):
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

        logger.info('All world folders appear to be setup.')
        return True

    def delete_world(
        self,
        world_config: Config
    ) -> None:
        """Deletes contents of world folder

        Args:
            world_config (Config): Configuration object of the world

        Returns:
            bool: World is built
        """
        try:
            logger.warn('Deleting world contents.')
            rmtree(world_config['world_dir'])
        except OSError as e:
            logger.error('Error deleting world contents: {:s}'.format(e.strerror))

    def build_world(
        self,
        world_config: Config
    ) -> bool:

        # Create world directory
        world_files = os.path.join(world_config['world_dir'], 'base_files')
        mkdirs(world_config['world_dir'], world_config['config_dir'], world_config['output_dir'], world_files)

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
        
        return bool(cleared)

class EnvironmentBuilder(object):
    """Builds environment for running

    Args:
        config_file_path (str): Path to environment configuration file
        world_config (Config): Initialized world configuration
    """

    def __init__(
        self,
        config_file_path: str,
        world_config: Config
    ) -> None:
        """Constructor
        """
        self.config = self.parse_config(config_file_path)
        self.get_env_dir(world_config)
        self.id = self.config['id']

    def parse_config(
        self,
        config_file_path: str
    ) -> Config:
        """Parses the environment config file and returns a native python dictionary
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
                logger.info( 'Parsed environment config file: {:s}; h.{:d}'.format(
                        config['name'], config['hash']) )
            except yaml.YAMLError as exc:
                logger.error('Error reading the environment configuration file!')
                logger.error(exc)

        return config

    def get_env_dir(
        self,
        world_config: Config
    ) -> None:
        """Gets the environment directory from  world configuration

        Args:
            world_config (Config): Initialized world configuration

        Raises:
            LookupError: If environment ID in env config is not in the world
        """
        for env in world_config['envs']:
            if env['id'] == self.config['id']:
                env_dir = os.path.join(world_config['world_dir'], env['name'])
                self.env_dir = env_dir
        
        if self.env_dir is None:
            logger.error('Environment ID {:d} not present in universe config file.'.format(self.config['id']))
            raise LookupError('Invalid id')

    def setup_env(
        self
    ) -> bool:
        """Setup the environment for simulation by updating 

        Returns:
            bool: If setup was successful
        """
        # Modify the environment files
        mod = self.mod_env()
        # Validate environment
        valid = self.validate_env()

        return (mod and valid)

    def mod_env(
        self
    ) -> bool:
        """Setup the environment for simulation by updating 

        Returns:
            Config: Initialized world configuration
        """
         # Create each environment in the world
        cleared = 1
        for mod in self.config['mods']:
            # Check mod is supported
            if hasattr(OpenFoamMods, mod['func']):
                out = getattr(OpenFoamMods, mod['func'])(**mod['params'], env_dir=self.env_dir)
                cleared = cleared * out
            else:
                logger.error('Function {:s} not supported.'.format(mod['func']))
                cleared = 0

        return bool(cleared)


    def validate_env(
        self
    ) -> bool:
        """Runs validation checks of the environment folder
        TODO: Implement

        Returns:
            bool: Validation successful
        """

        return True