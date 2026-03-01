from src.abstract_solana import isOnCurve
import logging,json, asyncio,os
from abstract_apis import *
logging.basicConfig(level=logging.INFO)
from abstract_utilities import get_any_value,make_list,safe_read_from_json,safe_dump_to_file
from abstract_solcatcher import call_solcatcher_db
def get_last_id_path():
    directory = os.path.dirname(os.path.abspath(__name__))
    last_id_path = os.path.join(directory,'last_id.json')
    return last_id_path
def save_last_id(last_id):
    data={"last_id":last_id}
    file_path = get_last_id_path()
    safe_dump_to_file(data=data,file_path=file_path)
def get_last_id():
    file_path = get_last_id_path()
    if not os.path.isfile(file_path):
        save_last_id(0)
    data = safe_read_from_json(file_path)
    return data.get('last_id')
async def perform_update(start=None):
    start = start or get_last_id()
    for pair_id in range(start,100000000):
        save_last_id(pair_id)
        response = postRequest('https://solcatcher.io/api/update_pair_data',data={"pair_id":pair_id})
        input(response)
def main():
    asyncio.run(perform_update())
main()
