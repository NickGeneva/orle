import argparse


class Parser(argparse.ArgumentParser):
    """Program arguments
    """
    def __init__(self):
        super(Parser, self).__init__(description='Arguments for ORLE world process')
        self.add_argument('--config_path', type=str, default=None, help='directory to universe config file')
        self.add_argument('--world_id', type=int, default=0, help='id of world')
        self.add_argument('--overwrite_world', action='store_true', help="reinitialize environment folders")

    def parse(
        self
    ) -> object:
        """Parse program arguments

        Returns:
            (object): parsed program arguments
        """
        args = self.parse_args()
        return args