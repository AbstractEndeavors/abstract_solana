from abstract_apis import get_async_response
from abstract_utilities import *
solana_rpc_url="http://api.mainnet-beta.solana.com"
fall_back_rpc = get_env_value('solana_fallback_rpc_url')
def get_rpc_url(rpc_url=None,url_1_only=True,url_2_only=False):
    if not rpc_url:
        if url_1_only:
            rpc_url = solana_rpc_url
        elif url_2_only:
            if fall_back_rpc:
                rpc_url = fall_back_rpc
    if not rpc_url:
        rpc_url = solana_rpc_url
    return rpc_url

def get_rpc_payload(method,params=None,id=None,jsonrpc=None):
    if method == None:
        return None
    params=get_if_None(params,[])
    rpc_id=int(get_if_None(id,1))
    jsonrpc=str(get_if_None(jsonrpc,"2.0"))
    return {
            "jsonrpc": jsonrpc,
            "id": rpc_id,
            "method": method,
            "params": params
        }
def get_result(response):
    try:
        response = response.json()
        result = response.get('result',response)
    except:
        result = response.text
    return result
def make_rpc_call(method, params=[],rpc_url=None):
    rpc_url = rpc_url or solana_rpc_url
    headers = {'Content-Type': 'application/json'}
    payload = get_rpc_payload(method=method, params=params)
    response = requests.post(rpc_url, data=json.dumps(payload), headers=headers)
    return response
def get_transaction(signature,url_1_only=False,url_2_only=True):
    transaction=None
    method='getTransaction'
    params=[signature,{"maxSupportedTransactionVersion": 0}]
    while True:
        response = make_rpc_call(method=method,params=params,url_1_only=url_1_only,url_2_only=url_2_only)
        transaction = get_result(response)
        if transaction:
            break
    return transaction
async def async_get_signatures(address, until=None, limit=1000,rpc_url=None,url_1_only=True,url_2_only=False,*args,**kwargs):
    rpc_url = get_rpc_url(rpc_url=rpc_url,url_1_only=url_1_only,url_2_only=url_2_only)
    method = 'getSignaturesForAddress'
    params = [address, {"until":until,"limit": limit}]
    response = make_rpc_call(method=method,params=params,rpc_url=rpc_url)
    return get_result(response)
def get_signatures(*args,**kwargs):
    return get_async_response(async_get_signatures,*args,**kwargs)

