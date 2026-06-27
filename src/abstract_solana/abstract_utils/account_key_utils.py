from .signature_data_parse import get_account_keys_from_txn,get_read_only_addresses_from_txn,get_writable_addresses_from_txn
from .pubkey_utils import get_pubkey
from abstract_utilities import is_number

def get_all_account_keys(txnData):
  accountKeys=[]
  accountKeys += get_account_keys_from_txn(txnData)
  accountKeys += get_read_only_addresses_from_txn(txnData)
  accountKeys += get_writable_addresses_from_txn(txnData)
  return accountKeys

def get_account_key(index,txnData):
    accountKeys = get_all_account_keys(txnData)
    if index is not None and accountKeys is not None and is_number(index) and len(accountKeys)>int(index):
        return accountKeys[int(index)]

def get_account_index(accountIndex,txnData):
    for i,account in enumerate(get_all_account_keys(txnData)):
        if get_pubkey(str(account)) == get_pubkey(str(accountIndex)):
            return i
