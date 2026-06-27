from typing import List, Dict, Any, Optional, Union
from .pubkey_utils import try_pubkey
from .account_key_utils import get_all_account_keys

def search_for_index(data,index_number,key):
    for index_data in data:
        if str(index_data.get(key)) == str(index_number):
            return index_data
        
def search_for_account_index(data,index_number):
    return search_for_index(data,index_number,'accountIndex')

def find_log_entry(needle: str, log_entries: List[str]) -> Optional[str]:
    for log_entry in log_entries:
        if needle in log_entry:
            return log_entry
    return None

def extract_lp_initialization_log_entry_info_from_log_entry(lp_log_entry: str) -> Dict[str, Union[int, float]]:
    lp_initialization_log_entry_info_start = lp_log_entry.find('{')
    return json.loads(fix_relaxed_json_in_lp_log_entry(lp_log_entry[lp_initialization_log_entry_info_start:]))

def fix_relaxed_json_in_lp_log_entry(relaxed_json: str) -> str:
    return relaxed_json.replace(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":')

def get_associations(event, txnData):
    accountKeys = get_all_account_keys(txnData)
    key_properties = {'associatedAccounts': ['accountIndex', 'accounts'], 'programId': ['programIdIndex']}
    new_accounts = {k: None for k in key_properties}
    for key, values in key_properties.items():
        for value in values:
            subjects = event.get(value)
            if value in event and subjects is not None:
                subjects = event.get(value)
                if isinstance(subjects, list):
                    event[key] = [convert_subject(sub, accountKeys) for sub in subjects]
                else:
                    event[key] = convert_subject(subjects, accountKeys)
                    
    return event

def convert_subject(sub, accountKeys):
    return sub if try_pubkey(sub) else accountKeys[int(sub)]
