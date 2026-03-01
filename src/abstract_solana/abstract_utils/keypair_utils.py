from abstract_security import *
from solders.keypair import Keypair
import base58
def load_from_private_key(env_key='AMM_P',path=None):
    if path:
        env_value = get_env_value(path=path,key=env_key)
    else:
        env_value = get_env_value(key=env_key)
    if env_value:
        return Keypair.from_base58_string(env_value)

def load_keypair_from_file(filename):
    curr = os.path.join(sys.path[0], 'data',  filename)
    with open(curr, 'r') as file:
        secret = json.load(file)
        secret_key = bytes(secret)
        return Keypair.from_bytete_key()
