from solana.rpc.core import _ClientCore
from typing import Dict, List, Optional, Sequence, Union
from solana.rpc.commitment import Commitment, Finalized
from .rate_limiter import RateLimiter
from ..abstract_solana_utils.pubKeyUtils import *
import inspect,asyncio,json,requests
from abstract_apis import *
from abstract_utilities import is_number
rate_limiter = RateLimiter()
def convert_to_lower(string_obj):
    return ''.join(f"_{char.lower()}" if char.isupper() else char for char in str(string_obj))
def convert_to_upper(string_obj):
    words = string_obj.split('_')
    return words[0] + ''.join(word.capitalize() for word in words[1:])
def convert_to_body(string_obj):
    return f"_{convert_to_lower(string_obj)}_body"
class Client(_ClientCore):
    def __init__(
        self,
        endpoint: Optional[str] = None,
        commitment: Optional[Commitment] = "confirmed",
        timeout: float = 10,
        extra_headers: Optional[Dict[str, str]] = None,
    ):
        """Init API client."""
        super().__init__(commitment)
client = Client()
def get_function(function_string):
    try:
        function = getattr(client, function_string)
    except:
        function =None
    return function
def call_function(function,*args,**kwargs):
    result = None
    if function:
        try:
            result = function(*args,**kwargs)
        except TypeError as e:
            print(f"Error calling function: {e}")
            result = None
    return result
def get_defaults():
    return {'limit':1000,'encoding': "jsonParsed",'usize': 1024,'preflightCommitment': 'confirmed','sig_verify': True,'commitment': 'confirmed','maxSupportedTransactionVersion': 0,'max_supported_transaction_version': 0,'skipPreflight': True,'opts': {'skipPreflight': True, 'preflightCommitment': 'confirmed'}}
def get_default_value(key):
    return get_defaults().get(key)
def convert_value(key,value):
    default_value = get_default_value(key)
    if value is None and default_value:
        return default_value
    pubkeys = ['address','account','pubkeys','pubkey','mint','owner','delegate']
    if key in pubkeys:
        if isinstance(value,list):
            value = [get_pubkey(pubkey) for pubkey in value]
        else:
            value = get_pubkey(value)
        return value
    signatures = ['until','before','tx_sig','signature','before','signatures']
    if key in signatures:
        if isinstance(value,list):
            value = [get_sigkey(signature) for signature in value]
        else:
            value = get_sigkey(value)
        return value
    return value
def get_conversions(variables,*args,**kwargs):
    for i,arg in enumerate(args):
        variable = variables[i]
        kwargs[variable] = arg
    for key,value in kwargs.items():
        if key in variables:
            kwargs[key] = convert_value(key,value)
            get_default_value(key)
    for variable in variables:
        if variable not in kwargs:
            kwargs[variable] = get_default_value(variable)
    return kwargs
def get_params(function):
    sig = inspect.signature(function)
    return list(sig.parameters.keys())
def get_rpc_dict(*args,**kwargs):
    body_call = convert_to_body(*args,**kwargs)
    function = get_function(body_call)
    variables = get_params(function)
    kwargs = get_conversions(variables,*args,**kwargs)
    kwargs = json.loads(str(call_function(function,**kwargs)))
    return kwargs
def make_call(url,body):
    return postRpcRequest(url=url,**body,retry_after =True,status_code=True, headers=get_headers())
def abstract_solana_rate_limited_call(method, *args, **kwargs):
    # Build the request body
    body = get_rpc_dict(method, *args, **kwargs)
    body_method = body.get('method')
    url = rate_limiter.get_url(body_method)
    response,status_code,retry_after = make_call(url,body)   
    rate_limiter.log_response(body_method, response, retry_after)
    if url == rate_limiter.url1 and status_code == 429:
        url = rate_limiter.get_url('get_url2')
        response,status_code,retry_after = make_call(url,body)
        rate_limiter.log_response(body_method, response)
    return response
