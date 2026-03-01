from solders.pubkey import Pubkey
from solders.signature import Signature
from spl.token.instructions import get_associated_token_address
TOKEN_PROGRAM_ID = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

def pubkey_find_program_address(string,address,programId):
    return Pubkey.find_program_address([str(string).encode(), bytes(get_pubkey(address))],get_pubkey(programId))

def get_pubString(obj):
    return Pubkey.from_string(str(obj))

def get_sigString(obj):
    return Signature.from_string(str(obj))

def is_sigkey(obj):
    return isinstance(obj,Signature)

def is_pubkey(obj):
    return isinstance(obj,Pubkey)

def get_pubBytes(obj):
    return Pubkey.from_bytes(obj)

def get_sigBytes(obj):
    return Signature.from_bytes(obj)

def try_pubkey(obj):
    return is_pubkey(get_pubkey(obj))

def try_sigkey(obj):
    return is_sigkey(get_sigkey(obj))

def get_pubkey(obj):
    if is_pubkey(obj):
        return obj
    address = obj
    if isinstance(obj,bytes):
        pubkey = get_pubBytes(address)
        if is_pubkey(pubkey):
            return pubkey
    if isinstance(obj,str):
        try:
            pubkey= get_pubString(obj)
        except:
            pubkey = obj
        if is_pubkey(pubkey):
            return pubkey
    return obj

def get_sigkey(obj):
    if is_sigkey(obj):
        return obj
    signature = obj
    if isinstance(signature,bytes):
        sigKey = get_sigBytes(signature)
        if is_sigkey(sigKey):
            return sigKey
    if isinstance(signature,str):
        try:
            sigKey= get_sigString(signature)
        except:
            sigKey = signature
        if is_sigkey(sigKey):
            return sigKey
    return obj

def derive_associated_bonding_curve(mint,programId=None):
    return get_associated_token_address(derive_bonding_curve(mint,programId)[0], get_pubkey(mint))

def derive_bonding_curve(mint,programId=None):
    programId = programId or TOKEN_PROGRAM_ID
    return pubkey_find_program_address("bonding-curve",mint,programId)
