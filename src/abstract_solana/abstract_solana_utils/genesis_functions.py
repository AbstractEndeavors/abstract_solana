from abstract_apis import get_async_response,get_headers,get_response,get_text_response,load_inner_json
from abstract_solcatcher import call_solcatcher_db,async_call_solcatcher_py,async_make_rate_limited_call
from abstract_utilities import get_any_value,make_list
from ..rpc_utils import get_signatures,async_get_signatures
import asyncio,httpx,logging
async def call_async_function(func, *args, **kwargs):
    """Helper function to call async functions in sync or async contexts."""
    if asyncio.isrunning():
        # If an event loop is already running, use await
        return await func(*args, **kwargs)
    else:
        # If no event loop is running, use asyncio.run()
        return await asyncio.run(func(*args, **kwargs))
def get_block_time_from_txn(txnData):
    return int(get_any_value(txnData,'blockTime') or 0)
def get_error_message_from_txn(txnData):
    return make_list(get_any_value(txnData,'err'))[0]
def get_errorless_txn_from_signature_array(signatureArray):
    return [sig for sig in signatureArray or [] if get_error_message_from_txn(sig) == None]
def return_oldest_from_signature_array(signatureArray,errorless=False):
    if errorless:
        signatureArray = get_errorless_txn_from_signature_array(signatureArray)
    if signatureArray and isinstance(signatureArray,list):
        if get_block_time_from_txn(signatureArray[0])<get_block_time_from_txn(signatureArray[-1]):
            return signatureArray[0].get('signature')
        return signatureArray[-1].get('signature')
def return_oldest_last_and_original_length_from_signature_array(signatureArray):
    return {"oldest":return_oldest_from_signature_array(signatureArray),
     "oldestValid":return_oldest_from_signature_array(signatureArray,errorless=True),
     "length":len(signatureArray or '')}
async def get_first_sigs(address, until=None, limit=1000,get_signature_function=None):
    get_signature_function = get_signature_function or async_get_signatures
    original_length=None
    while True:
        signatureArray = await get_signature_function(address,until=until, limit=limit)
        if signatureArray:
            original_length = len(signatureArray)
        if original_length:
            return signatureArray
async def async_getGenesisSignature(address, limit=1000, until=None,encoding='jsonParsed',commitment=0,get_signature_function=None,errorProof=True,url_1_only=True,url_2_only=False):
    method = "getGenesisSignature"
    validBefore=None
    get_signature_function = get_signature_function or async_get_signatures
    signatureArray = await get_first_sigs(address, until=until, limit=limit,get_signature_function=get_signature_function)
    original_length=len(signatureArray)
    while True:
        if validBefore != None:
            signatureArray = await get_signature_function(address, until=until, limit=limit)
            if signatureArray:
                original_length = len(signatureArray)
            else:
                original_length = 0
        signature_array_data = return_oldest_last_and_original_length_from_signature_array(signatureArray)
        oldest = signature_array_data.get('oldest')
        validOldest = signature_array_data.get('oldestValid')
        if original_length < limit or original_length == 0 or (original_length>0 and (oldest == validOldest or oldest == validBefore) and oldest != None):
            return validOldest
        validBefore = oldest
    
def getGenesisSignature(*args,**kwargs):
    return get_async_response(async_getGenesisSignature,*args,**kwargs)




