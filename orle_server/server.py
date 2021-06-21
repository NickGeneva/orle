import os
import socket
import rsa
import threading
import pickle
from cryptography.fernet import Fernet
import hashlib
import time
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

Socket = socket.socket

class ORLE_Server(object):
    """ORLE Jobe Server

    Args:
        object ([type]): [description]
    """
    def __init__(
        self, 
        public_rsa_file: str = None, 
        private_rsa_file: str = None, 
        addr: Tuple = ('localhost', 8080),
        backlog: int = 5,
    ) -> None:
        super().__init__()

        self.interrupt = False # Safe interrupt

        # Set up private and public RSA keys for asymmetric encryption
        # Create new keys
        if public_rsa_file is None or private_rsa_file is None:
            asyKey = rsa.newkeys(2048)
            # Public key and private key
            self.public_key = self.asyKey[0]
            self.private_key = self.asyKey[1] 
            # Save key to Privacy Enhanced Mail (PEM) files
            with open ("public_rsa.key", "w") as key_file:
                key_file.write( self.public_key.save_pkcs1(format='PEM') )

            with open ("private_rsa.key", "w") as pub_file:
                key_file.write( self.private_key.save_pkcs1(format='PEM') )
        # Load pregenerated keys from file
        else:
            if not os.path.exists(public_rsa_file) or not os.path.exists(private_rsa_file):
                raise FileNotFoundError("Provided rsa PEM files not found.")

            with open (public_rsa_file, "r") as key_file:
                self.public_key = rsa.PublicKey.load_pkcs1(key_file.read())

            with open (private_rsa_file, "r") as key_file:
                self.public_key = rsa.PrivateKey.load_pkcs1(key_file.read())
            self.private_key = rsa.PrivateKey.load_pkcs1(private_rsa_file)

        # Now we set up the servers main socket for authenticating clients
        self.serverSocket = socket.socket()
        # Bind the listening IP address and port number
        self.serverSocket.bind(addr)
        # 
        self.serverSocket.listen(backlog)

    def start(
        self
    ) -> None:

        # Start loop to monitor port
        while(True):
            # Accept socket message
            clientSocket, addr = self.serverSocket.accept()
            # Use multithread the authentication process to allow multiple
            # Clients to connect
            t = threading.Thread(target=self.authenticate_client, args=(clientSocket, addr))
            t.start()


    def authenticate_client(
        self,
        clientSocket: Socket,
        addr: Tuple
    ) -> None:

        logger.info('Client detected from address {:s}'.format(addr[0]))

        # First send and recv public keys

        # Check public sha key with saved one in file (client)

        # Wait for password

        # Verify password

        # Generate encryption key for fernet

        # Send key to client

        # Add client socket to either list of slaves

        # Or init a master thread to listen for configs




    def stop(
        self
    ) -> None:
        self.interupt = False
