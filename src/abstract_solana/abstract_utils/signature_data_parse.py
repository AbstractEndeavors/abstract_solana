from abstract_utilities import make_list,get_any_value
def get_block_time_from_txn(txnData):
    return int(get_any_value(txnData,'blockTime') or 0)

def get_meta_from_txn(txnData):
    return txnData.get('meta',{})

def get_transaction_from_txn(txnData):
    return txnData.get('transaction', {})

def get_message_from_txn(txnData):
    return get_transaction_from_txn(txnData).get('message', {})

def get_addres_lookup_table_from_txn(txnData):
    return get_message_from_txn(txnData).get('addressTableLookups', [])

def get_account_keys_from_txn(txnData):
    return get_message_from_txn(txnData).get('accountKeys', [])

def get_loaded_addresses_from_txn(txnData):
    return get_meta_from_txn(txnData).get('loadedAddresses',{})

def get_read_only_addresses_from_txn(txnData):
    return get_any_value(txnData,'readonly') or []

def get_writable_addresses_from_txn(txnData):
    return get_any_value(txnData,'writable') or []

def get_log_messages_from_txn(txnData):
    return get_meta_from_txn(txnData).get('logMessages',[])

def get_error_message_from_txn(txnData):
    return make_list(get_any_value(txnData,'err'))[0]

def get_instructions_from_txn(txnData):
    return get_message_from_txn(txnData).get('instructions',[])

def get_inner_instructions_raw(txnData):
    return get_meta_from_txn(txnData).get('innerInstructions',[{}])

def get_inner_instructions_from_txn(txnData):
    return get_inner_instructions_raw(txnData)[0].get('instructions',[])

def get_post_token_balances_from_txn(txnData):
    return get_meta_from_txn(txnData).get('postTokenBalances', [])

def get_pre_token_balances_from_txn(txnData):
    return get_meta_from_txn(txnData).get('preTokenBalances', [])

def get_post_balances_from_txn(txnData):
    return get_meta_from_txn(txnData).get('postBalances', [])

def get_pre_balances_from_txn(txnData):
    return get_meta_from_txn(txnData).get('preBalances', [])

def get_signatures_from_txn(txnData):
    return txnData.get('signatures',{})
