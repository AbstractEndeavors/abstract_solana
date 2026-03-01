from .signature_data_parse import get_account_keys_from_txn,get_post_balances_from_txn,get_pre_balances_from_txn,get_post_token_balances_from_txn,get_pre_token_balances_from_txn
from .account_key_utils import get_all_account_keys
from .index_utils import search_for_account_index
from abstract_utilities import exponential,get_any_value,update_dict_value,get_value_from_path,find_paths_to_key

def get_amount_dict(amount,decimals=9):
    if amount!= None:
        if isinstance(amount,dict):
            amount_dict = get_any_value(amount,'uiTokenAmount')
            amount = get_any_value(amount_dict,'amount')
            decimals = get_any_value(amount_dict,'decimals')
        return exponential(amount,decimals,-1)
def create_token_txns(txnData):
    preTokenBalances = get_pre_token_balances_from_txn(txnData)
    postTokenBalances = get_post_token_balances_from_txn(txnData)
    account_keys = get_all_account_keys(txnData)
    pre_post_balances = {"preTokenBalances":preTokenBalances,"postTokenBalances":postTokenBalances}
    dont_use = []
    all_txns = {"accounts":[],"owner":[],'Balance Before':[],"Balance After":[],"Change":[],"mint":[],"balanceIndexs":[]}
    for key,tokenBalances in pre_post_balances.items():
        for i,tokenBalance in enumerate(tokenBalances):
            index = tokenBalance.get('accountIndex')
            if index not in dont_use:
                dont_use.append(index)
                after = get_amount_dict(search_for_account_index(postTokenBalances,index))
                change = get_amount_dict(tokenBalance)
                if after!=None and change !=None:
                    before = after-change
                    if i == 0:
                        pre_change = change
                        change = before
                        before = pre_change
                    all_txns["accounts"].append(account_keys[index])
                    all_txns["owner"].append(tokenBalance.get('owner'))
                    all_txns['Balance Before'].append(before)
                    all_txns["Balance After"].append(after)
                    all_txns["Change"].append(change)
                    all_txns["mint"].append(tokenBalance.get('mint'))
                    all_txns["balanceIndexs"].append(find_paths_to_key(txnData, key)[0]+[i])
    return all_txns
def get_solana_balances(txnData):
    balance = []
    preBalances = get_pre_balances_from_txn(txnData)
    postBalances = get_post_balances_from_txn(txnData)
    account_keys = get_all_account_keys(txnData)
    all_txns = {"accounts":[],'Balance Before':[],"Balance After":[],"Change":[]}
    for i, amt in enumerate(preBalances):
        before = exponential(amt, 9,-1)
        after = exponential(postBalances[i], 9,-1)
        address = account_keys[i]
        change = after - before
        all_txns['accounts'].append(address)
        all_txns['Balance Before'].append(before)
        all_txns['Balance After'].append(after)
        all_txns['Change'].append(change)
    return all_txns
def get_balances(txnData):
    balances = {"solana":{},"tokens":{}}
    solanaTxns = get_solana_balances(txnData)
    tokenTxns = create_token_txns(txnData)
    for i,address in enumerate(solanaTxns["accounts"]):
        balances["solana"][address]={"Balance Before":solanaTxns["Balance Before"][i],"Balance After":solanaTxns["Balance After"][i],"Change":solanaTxns["Change"][i]}
    for i,address in enumerate(tokenTxns["accounts"]):
        before = tokenTxns["Balance Before"][i]
        after = tokenTxns["Balance After"][i]
        change = after - before
        balances["tokens"][address]={"Balance Before":before,"Balance After":after,"Change":change,"mint":tokenTxns["mint"][i],"owner":tokenTxns["owner"][i],"balanceIndex":tokenTxns["balanceIndexs"][i]}
    return balances
def update_balance_data(txnData):
    balances = get_balances(txnData)
    all_txns = create_token_txns(txnData)
    for key,values in balances["tokens"].items():
        path =values.get("balanceIndex")
        tokenBalance = get_value_from_path(txnData,path)
        tokenBalance.update({key:values.get(key) for key in ["Balance Before","Balance After","Change"]})
        signature_data = update_dict_value(txnData, path, tokenBalance)
    txnData['meta']['balances']=balances
    return txnData
