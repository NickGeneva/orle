import os
import sys
import socket
import rsa
import threading
from cryptography.fernet import Fernet
import time
import logging
from typing import Tuple
from .socket_utils import SocketUtils
from .messages import MessageUtils as mu

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
        timeout: float = 0.25
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
        self.serverSocket.settimeout(timeout) # timeout for listening
        self.serverSocket.listen(backlog)

    def start(
        self
    ) -> None:

        # Start loop to monitor port
        while(not self.interrupt):
            try:
                # Accept socket message
                clientSocket, addr = self.serverSocket.accept()
                # Use multithread the authentication process to allow multiple
                # Clients to connect
                t = threading.Thread(target=self.authenticate_client, args=(clientSocket, addr))
                t.start()
            except socket.timeout:
                pass
            except:
                logger.error("Unexpected error, {}".format(sys.exc_info()[0]))
                raise

            time.sleep(0.1)

    def authenticate_client(
        self,
        clientSocket: Socket,
        addr: Tuple
    ) -> None:

        logger.info('Client detected from address {:s}'.format(addr[0]))
        su = SocketUtils()

        # First send and recv public keys
        SocketUtils.send_unencrypted(self.public_key.save_pkcs1(format='PEM'), clientSocket)

        client_key_bytes = SocketUtils.recv_rsa(self.public_key, self.private_key, clientSocket)
        try:
            client_key = rsa.PublicKey.load_pkcs1(client_key_bytes)
        except:
            logging.error(' Not a valid PEM rsa key, cannot authenticate client.')
            return

        # Check public sha key with saved one in file (client)

        # Wait for password
        msg = SocketUtils.recv_rsa(self.public_key, self.private_key, clientSocket)
        try:
            user, passw = mu.load_login(msg)
            # Verify password
            auth = self.client_login(user, passw)
            if not auth:
                logging.error('Username and password of client not valid.')
                SocketUtils.send_rsa({'auth_status', False}, client_key, self.private_key, clientSocket)
                return
            SocketUtils.send_rsa({'auth_status', True}, client_key, self.private_key, clientSocket)
        except:
            logging.error('Not a valid log in message.')
            return

        # Generate encryption key for fernet
        sym_key = Fernet.generate_key()

        # Send key to client
        SocketUtils.send_rsa(sym_key, client_key, self.private_key, clientSocket)

        # Recv client config from client
        config = SocketUtils.recv_fernet(sym_key, clientSocket)


        # Add client socket to either list of slaves

        # Or init a master thread to listen for configs

    def client_login(
        self,
        user: str,
        psw: str
    ) -> bool:
        """Verify client username and password

        Args:
            user (str): username
            pass (str): password

        Returns:
            bool: Client is authenticated
        """
        return (user == 'user') and (psw == 'pass')

    def stop(
        self
    ) -> None:
        self.interupt = False
