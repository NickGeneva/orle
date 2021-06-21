import struct
import pickle
import socket
import hashlib
import logging
import rsa
from cryptography.fernet import Fernet
from rsa import VerificationError

logger = logging.getLogger(__name__)

Socket = socket.socket
PublicKey = rsa.PublicKey
PrivateKey = rsa.PrivateKey

class SocketUtils:

    @classmethod
    def send_msg(
        cls,
        message,
        socket: Socket,
    ) -> None:
        """Serializes and sends message. Uses fixed header size to communicate message size to
        other connect.
        https://stackoverflow.com/questions/27428936/python-size-of-message-to-send-via-socket

        Args:
            clientSocket (Socket): socket connection
            message (object): Python object to send, should be encrypted and signed if needed
        """
        serial_message = pickle.dumps(message)
        header = struct.pack('>I', len(serial_message)) # Serialize header to big-endian unsigned int

        # Now we send the data
        socket.send(header)
        socket.send(serial_message)

    @classmethod
    def recv_msg(
        cls,
        socket: Socket,
    ) -> object:
        """Serializes and sends message

        Args:
            clientSocket (Socket): socket connection
        
        Returns
            (object): unserialized received message
        """
        # First we receive the header with message length
        header = socket.recv(4)
        msize = struct.unpack('>I', header)

        serial_message = socket.recv(msize)
        message = pickle.loads(serial_message)

        return message

    @classmethod
    def send_unencrypted(
        cls,
        message,
        socket: Socket,
    ) -> None:
        """Sends an unencrypted message with a SHA-256 signature.
        Should only be used to send public RSA keys

        Args:
            message (object): Python object to send
            clientSocket (Socket): socket connection
        """
        serial_message = pickle.dumps(message)
        signature_sha256 = hashlib.sha256(serial_message).hexdigest()

        signed_message = tuple(serial_message, signature_sha256)
        cls.send_msg(signed_message, socket)

    @classmethod
    def recv_unencrypted(
        cls,
        socket: Socket,
    ) -> object:
        """Receives an unencrypted message with a SHA-256 signature.

        Args:
            clientSocket (Socket): socket connection

        Returns:
            message (object): Python object to send
        """
        message = cls.recv_msg(socket)
        
        if not isinstance(message, tuple) or not len(message) == 2:
            logger.error("Received message did not include payload and signature")
            return None 
        # Verify payload with signature
        serial_message = message[0]
        signature_sha256 = message[1]
        if hashlib.sha256(serial_message).hexdigest() != signature_sha256:
            raise VerificationError("Payload has been tampered!")

        # Looks like payload and signature line up
        message = pickle.loads(serial_message)

        return message

    @classmethod
    def send_rsa(
        cls,
        message,
        public_key: PublicKey,
        private_key: PrivateKey,
        socket: Socket,
    ) -> None:
        """Sends a RSA encrypted message 

        Args:
            message (object): Python object to send
            public_key (PublicKey): RSA receiver public key
            private_key (PrivateKey): RSA sender private key
            socket (Socket): socket connection
        """
        serial_message = pickle.dumps(message)
        # First sign message
        signature_RSA = rsa.sign(serial_message, private_key, hash_method='SHA-256')
        signed_message = pickle.dumps(tuple(serial_message, signature_RSA))
        # Encrypt and send
        encrypted_message = rsa.encrypt(signed_message, public_key)
        cls.send_msg(encrypted_message, socket)

    @classmethod
    def recv_rsa(
        cls,
        public_key: PublicKey,
        private_key: PrivateKey,
        socket: Socket,
    ) -> None:
        """Receives a RSA encrypted message.

        Args:
            message (object): Python object to send
            public_key (PublicKey): RSA receiver public key
            private_key (PrivateKey): RSA sender private key
            socket (Socket): socket connection
        """
        # Receive and decrypt
        encrypted_message = cls.recv_msg(socket)
        message = rsa.decrypt(encrypted_message, private_key)
        serial_message, signature_RSA = pickle.loads(message)

        # Verify payload and signature
        rsa.verify(serial_message, signature_RSA, public_key)

        message = pickle.loads(serial_message)

        return message

    @classmethod
    def send_fernet(
        cls,
        message,
        fernet: Fernet,
        socket: Socket,
    ) -> None:
        """Sends a fernet AES-128 encrypted message with SHA-256 signature

        Args:
            message (object): Python object to send
            fernet (Fernet): Initialized Fernet encryption class
            socket (Socket): socket connection
        """
        serial_message = pickle.dumps(message)
        # First sign message with SHA-256 hash
        signature_sha256 = hashlib.sha256(serial_message).hexdigest()
        signed_message = pickle.dumps(tuple(serial_message, signature_sha256))

        # Encrypt and send
        encrypted_message = fernet.encrypt(signed_message)
        cls.send_msg(encrypted_message, socket)

    @classmethod
    def recv_fernet(
        cls,
        fernet: Fernet,
        socket: Socket,
    ) -> None:
        """Receive a fernet AES-128 encrypted message with SHA-256 signature.

        Args:
            message (object): Python object to send
            fernet (Fernet): Initialized Fernet encryption class
            socket (Socket): socket connection
        """
        # Receive and decrypt
        encrypted_message = cls.recv_msg(socket)
        message = fernet.decrypt(encrypted_message)
        serial_message, signature_sha256 = pickle.loads(message)

        # Verify payload and signature
        serial_message = message[0]
        signature_sha256 = message[1]
        if hashlib.sha256(serial_message).hexdigest() != signature_sha256:
            raise VerificationError("Payload has been tampered!")

        message = pickle.loads(serial_message)

        return message