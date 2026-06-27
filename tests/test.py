from imports import *
import pkgutil, importlib, inspect
from abstract_apis import *
##def walk_package(package):
##    results = {}
##    pkg = importlib.import_module(package)
##
##    for _, mod_name, _ in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
##        mod = importlib.import_module(mod_name)
##        results[mod_name] = dir(mod)
##
##    return results
##
##tree = walk_package("solana")
##
##for module, symbols in tree.items():
##    print(f"\n--- {module} ---")
##    for sym in symbols:
##        print(" ", sym)
import asyncio
import json
from abstract_utilities.time_utils import *

from solana.rpc.websocket_api import connect
from solana.rpc.async_api import AsyncClient
rpc_url = "https://api.mainnet-beta.solana.com"
sol_cli = Client()
rpc_cli = RPCClient(rpc_url)
rate_limiter = RateLimiter(rpc_url=rpc_url)
def call_solana(method_resp):
    return makeRpcCall(**method_resp)

# ---- your wrapper must call the proper async RPC function ----
async def async_get_block_time(slot):
    client = AsyncClient("https://api.mainnet-beta.solana.com")
    resp = await client.get_block_time(slot)
    await client.close()
    return resp["result"]

def get_block_time(slot):
    # uses your abstract_apis get_async_response()
    return get_async_response(async_get_slot_time, slot)

def get_signatures(address, *args, **kwargs):
    return get_async_response(async_get_signatures, address, *args, **kwargs)
async def watch_logs():
    async with connect("wss://api.mainnet-beta.solana.com") as ws:
        sub = await ws.logs_subscribe()
        print("Subscribed:", sub)
        
        async for msg in ws:
            for ms in msg:
                ms = json.loads(ms.to_json())
                print(f"ms == {ms}")
                result = ms["result"]
                if not is_number(result):
                    
                    
                    print(result)
                    context = result["context"]
                    print(context)
                    slot = context["slot"]
                    print(slot)
                    body = sol_cli.get_block_time(slot)
                    method = body.get('method')
                    input(method)
                    url= rate_limiter.get_url(method)
                                # --- FIXED: Fetch actual block time ---\
                    input(url)
                    block_time = make_call(url,body)[0]
                    rate_limiter.log_response(method=method,response=block_time)
                    
                    
                    input(f"Block Time: {get_convert_timestamp_to_datetime(block_time)}")
asyncio.run(watch_logs())
