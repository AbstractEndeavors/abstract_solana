from abstract_utilities import make_list
import json,pprint
from .price_utils import *
from .signature_data_parse import get_log_messages_from_txn,get_instructions_from_txn,get_inner_instructions_from_txn
from .account_key_utils import get_all_account_keys
from .constants import TOKEN_PROGRAM_ID

def ifListGetSection(list_obj,i=0):
    if list_obj and isinstance(list_obj,list) and len(list_obj)>i:
        list_obj = list_obj[i]
    return list_obj
def get_logs_from_index(txnData,index=None):
    if index is not None:
        allLogs = get_log_messages_from_txn(txnData)
        endLog = get_end_log_index(txnData,index)
        return allLogs[index:endLog]
def get_program_ids(txnData):
    allLogs = get_log_messages_from_txn(txnData)
    return [log.split(' ')[1] for log in allLogs if 'invoke' in log]
def get_program_id_from_log(logs):
    for log in make_list(logs):
        if 'invoke' in log.lower():
            return log.split(' ')[1]
def get_stack_height_from_logs(logs):
    for log in make_list(logs):
        if 'invoke' in log.lower():
            return int(log.split(' ')[-1][1:-1])
def get_end_log_index(txnData,index):
    allLogs = get_log_messages_from_txn(txnData)
    i=0
    for i,log in enumerate(allLogs[index+1:]):
        if 'invoke' in log.lower():
            return index+1+i
    return len(allLogs)
def get_stack_height_from_logs(logs):
    for log in make_list(logs):
        if 'invoke' in log.lower():
            return int(log.split(' ')[-1][1:-1])
def get_program_id_from_log(logs):
    for log in make_list(logs):
        if 'invoke' in log.lower():
            return log.split(' ')[1]

def get_all_logs(txnData):
    logits = []
    allLogs = get_log_messages_from_txn(txnData)
    for i,log in enumerate(allLogs):
        if 'invoke' in log.lower():
            logits.append([])
        logits[-1].append(log)
    start = 0
    for i,log in enumerate(logits):    
        length = len(log)
        end = start+length
        logits[i]={"programId":get_program_id_from_log(log[0]),
                   "start":start,
                   "end":end-1,
                   'stackHeight':get_stack_height_from_logs(log[0]) or 1,
                   'events':[event.split(':')[-1] or 'unknown' for event in get_log_events(log)],
                   'vars':[event.split(':')[1:] or 'unknown' for event in get_log_events(log)],
                   'logs':log}
        start = end
    return logits
def split_log_for_instruction(log):
    return log.split('log:')[-1].split('Instruction:')[-1]
def clean_split_string(string,delim=' '):
    return delim.join([spl for spl in string.split(' ') if spl])
def get_log_events(logs=None,index=None):
    return [clean_split_string(split_log_for_instruction(log)) for log in logs if 'log:' in log.lower() or 'instruction:' in log.lower()]
def get_instruction_accounts(instruction,txnData):
    accounts = get_all_account_keys(txnData)
    return [accounts[index] for index in instruction.get('accounts',[]) if index < len(accounts)]  
def get_instruction_info(instruction,txnData,instruction_index=0):
  
    stack_height = instruction.get('stackHeight') or 1
    accounts = instruction.get('accounts',[])
    associatedAccounts = get_instruction_accounts(instruction,txnData)
    instruction_info = {'instruction_index':instruction_index,'accounts':accounts,'associatedAccounts':associatedAccounts,'instructionStackHeight':stack_height}

    instruction_info.update(get_for_program_ids_info(txnData)[instruction_index])
    return instruction_info
def process_instructions(instructions,txnData,start_index=1):
    catalog = []
    for i, inst in enumerate(instructions):
        instruction_index = start_index-1 + i
        instruction_info = get_instruction_info(inst,txnData,instruction_index)
        catalog.append(instruction_info)
    return catalog
def get_instructions_catalog(txnData,printIt=False,saveIt=False):
    instructions = get_instructions_from_txn(txnData)
    outer_instructions_catalog = process_instructions(instructions,txnData)
    inner_instructions = get_inner_instructions_from_txn(txnData)
    if inner_instructions:
        inner_instructions_catalog = process_instructions(inner_instructions,txnData,start_index=len(instructions))
    complete_catalog =  outer_instructions_catalog+inner_instructions_catalog
    if printIt:
        pprint.pprint(complete_catalog)
    if saveIt:
        with open(saveIt, 'w') as f:
            json.dump(complete_catalog, f, indent=4)
    return complete_catalog

def find_in_catalog(string,txnData,programId=None):
    complete_catalog = get_instructions_catalog(txnData)
    return [txn for txn in complete_catalog if [event for event in txn['events'] if string.lower() in event.lower()]]
def findKeyValueIdInCatalog(key,value,txnData,programId=None):
    complete_catalog = get_instructions_catalog(txnData)
    if programId:
        complete_catalog = findKeyValueIdInCatalog('programId',programId,txnData)
    return [txn for txn in make_list(complete_catalog) if txn.get(key) == value]
def find_account_in_catalog(account,catalog):
    return ifListGetSection([txn for txn in make_list(catalog) if account in txn.get('associatedAccounts')])
def associate_logs_with_instructions(txnData):
    accountKeys = get_all_account_keys(txnData)
    instructions = txnData['transaction']['message']['instructions']
    innerInstructions = txnData['meta']['innerInstructions'][0]['instructions']
    allLogs = txnData['meta']['logMessages']
    for logIndex,log in enumerate(allLogs):
        log_programId = log['programId']
        log_stackHeight = log.get('stackHeight')  # Default to 0 if stackHeight is missing
        # Search for matching instructions by programId and stackHeight
        for instIndex,allInstruction in enumerate([instructions,innerInstructions]):
            for i,instruction in enumerate(allInstruction):
                program_id_index = instruction.get('programIdIndex')
                if program_id_index is not None:
                    instruction_program_id = accountKeys[program_id_index]
                    instruction_stack_height = instruction.get('stackHeight', 1)
                    if instruction_program_id == log_programId and instruction_stack_height == log_stackHeight:
                        # Add log data to the matching instruction
                        instruction.update(log)
                        instruction['associatedAccounts'] = [accountKeys[index] for index in instruction['accounts']]
                        if instIndex == 0:
                            instructions[i] = instruction
                        else:
                            innerInstructions[i] = instruction
                        allLogs[logIndex].update(instruction)
    txnData['transaction']['message']['instructions'] = instructions
    txnData['meta']['innerInstructions'][0]['instructions'] = innerInstructions
    txnData['meta']['logMessages'] = allLogs
    return txnData
def update_initial_txnData(txnData):
    accountKeys = get_all_account_keys(txnData)
    txnData = update_balance_data(txnData)
    txnData['transaction']['message']['instructions'] = [{**inst,"instructionIndex":instIndex,"programId":accountKeys[inst.get('programIdIndex')],"stackHeight":inst.get('stackHeight', 1),"associatedAccounts":[accountKeys[index] for index in inst['accounts']]} for instIndex,inst in enumerate(txnData['transaction']['message']['instructions'])]
    txnData['meta']['innerInstructions'][0]['instructions'] = [{**inst,"instructionIndex":instIndex+len(txnData['transaction']['message']['instructions']),"programId":accountKeys[inst.get('programIdIndex')],"stackHeight":inst.get('stackHeight', 1),"associatedAccounts":[accountKeys[index] for index in inst['accounts']]} for instIndex,inst in enumerate(txnData['meta']['innerInstructions'][0]['instructions'])]
    txnData['meta']['logMessages'] = get_all_logs(txnData)
    return txnData
def get_for_program_ids_info(txnData):
    txnData = update_initial_txnData(txnData)
    txnData = associate_logs_with_instructions(txnData)
    return txnData
