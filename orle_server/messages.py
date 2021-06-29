import socket
import logging
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

Socket = socket.socket

class MessageUtils:

    # login json
    @classmethod
    def dump_login(cls, user: str, pass: str) -> str:
        msg = {"username": user, "password": pass}
        return json.dump(msg)

    @classmethod
    def load_login(cls, msg: str) -> Tuple[str, str]:
        login = json.loads(msg)
        if cls.verify_keys(login, ['username', 'password']):
            return login['username'], login['password']
        else:
            logger.error('Invalid login message received')
            return "Failed", "Login"

    # client config jsons
    @classmethod
    def dump_orle_client(cls, univ: str, envs: List[int]) -> str:
        msg = {"type": "orle", "univ": univ, "envs": envs}
        return json.dump(msg)

    @classmethod
    def dump_agent_client(cls) -> str:
        msg = {"type": "agent"}
        return json.dump(msg)

    @classmethod
    def load_client_config(cls, msg:str) -> Dict:
        config = json.loads(msg)
        if cls.verify_keys(config, ['type']):
            return config
        else:
            logger.error('Client config does not have defined type')
            return None


    @classmethod
    def verify_keys(cls, dct:Dict, keys:List) -> bool:
        for key in keys:
            if not key in dct.keys():
                return False
        return True