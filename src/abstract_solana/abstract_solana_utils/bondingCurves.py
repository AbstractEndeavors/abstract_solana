from .pubKeyUtils import get_pubkey,pubkey_find_program_address,Pubkey
from spl.token.instructions import create_associated_token_account, get_associated_token_address
from ..pumpFun import PUMP_FUN_PROGRAM
def derive_bonding_curve_accounts(mint_str: str,programId=None):
    mintPubKey = get_pubkey(mint_str)
    if not mintPubKey.is_on_curve():
        return {}
    bonding_curve, _ = derive_bonding_curve(mintPubKey,programId)
    associated_bonding_curve = get_associated_token_address(bonding_curve, mintPubKey)
    return {'bonding_curve': bonding_curve, "associated_bonding_curve": associated_bonding_curve}
def get_bonding_curve(mint:str):
    return derive_bonding_curve_accounts(mint).get('bonding_curve')
def get_associated_bonding_curve(mint:str):
    return derive_bonding_curve_accounts(mint).get("associated_bonding_curve")
def isOnCurve(obj):
    pubkey = get_pubkey(obj)
    is_on_curve = pubkey.is_on_curve()
    return is_on_curve
def derive_associated_bonding_curve(mint,programId=None):
    programId = programId or PUMP_FUN_PROGRAM
    return get_associated_token_address(derive_bonding_curve(mint,get_pubkey(programId))[0], get_pubkey(mint))
def derive_bonding_curve(mint,programId=None):
    programId = programId or PUMP_FUN_PROGRAM
    return pubkey_find_program_address("bonding-curve",mint,get_pubkey(programId))
