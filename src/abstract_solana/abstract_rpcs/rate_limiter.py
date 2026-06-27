import time
import os
import json
from datetime import datetime

from abstract_utilities import *
from abstract_security import get_env_value
def getAbsFile():
  return os.path.abspath(__file__)
def getAbsDir():
  return os.path.dirname(getAbsFile())
def getAbsPath(path):
  return os.path.join(getAbsDir(),path)
def getSaveStatePath():
  return getAbsPath('rate_limiter_state.json')
def readSaveState(url1,url2,path=None):
  path= path or getSaveStatePath()
  if not os.path.isfile(path):
    state = {'last_method':None,'rate_limits': {url1: [], url2: []},'last_mb': {url1: {}, url2: {}},'cooldown_times': {url1: {}, url2: {}},'last_url':url1}
    safe_dump_to_file(data=state,file_path=path)
  return safe_read_from_json(path)
def is_time_interval(time_obj, interval):
    return (time.time() - time_obj) < interval-1

def get_mb(sum_list, limit, last_mb):
    return (sum_list + last_mb) > limit

def datasize(data):
    if isinstance(data, str):
        size = len(data.encode('utf-8'))
    elif isinstance(data, (bytes, bytearray)):
        size = len(data)
    elif isinstance(data, list) or isinstance(data, dict):
        size = len(json.dumps(data).encode('utf-8'))
    else:
        size = len(str(data).encode('utf-8'))
    return size/1000
class RateLimiter(metaclass=SingletonMeta):
    def __init__(self, rpc_url=None, fallback_rpc_url=None, env_directory=None,save_state_path = None):
        if not hasattr(self, 'initialized'):  # Prevent reinitialization
            self.initialized = True
            self.rpc_url = rpc_url or get_env_value(key="solana_primary_rpc_url", path=env_directory) or "https://api.mainnet-beta.solana.com"
            self.fallback_rpc_url = fallback_rpc_url or get_env_value(key="solana_fallback_rpc_url", path=env_directory)
            self.state_file = save_state_path or getSaveStatePath()
            self.url1 = self.rpc_url
            self.url2 = self.fallback_rpc_url
            self.rate_limits = {self.url1: [], self.url2: []}  # Separate rate limits for each URL
            self.last_mb = {self.url1: {}, self.url2: {}}
            self.cooldown_times = {self.url1: {}, self.url2: {}}  # Separate cooldowns for each URL
            self.last_url = None
            self.last_method = None
            self.load_state()

    def save_state(self):
        state = {
            'last_method': self.last_method,
            'rate_limits': self.rate_limits,
            'last_mb': self.last_mb,
            'cooldown_times': self.cooldown_times,
            'last_url': self.last_url
        }
        safe_dump_to_file(data=state, file_path=self.state_file)

    def load_state(self):
        state = readSaveState(self.url1,self.url2)
        self.last_method = state.get('last_method')
        self.rate_limits = state.get('rate_limits', {self.url1: [], self.url2: []})
        self.last_mb = state.get('last_mb', {self.url1: {}, self.url2: {}})
        self.cooldown_times = state.get('cooldown_times', {self.url1: {}, self.url2: {}})

    def set_cooldown(self, url, method=None, add=False):
        if method:
            if add:
                self.cooldown_times[url][method] = time.time() + add
            if method in self.cooldown_times[url] and time.time() > self.cooldown_times[url][method]:
                del self.cooldown_times[url][method]
            return method in self.cooldown_times[url]
        return False

    def get_last_rate_limit(self, url):
        if self.rate_limits[url]:
            return self.rate_limits[url][-1]
        return {}

    def is_all_limit(self, url, method):
        if method not in self.last_mb[url]:
            self.last_mb[url][method] = 0

        if self.set_cooldown(url, method):
            print(f'set_cooldown for method {method} in {url} hit')
            return True

        # Clean up expired queries for the current URL
        self.rate_limits[url] = [
            query for query in self.rate_limits[url] if is_time_interval(query.get('time') or 0, 30)
        ]
        last_rate_limit = self.get_last_rate_limit(url)

        # Check data size limits
        total_mb = sum(query.get('data', 0) for query in self.rate_limits[url])
        mb = get_mb(total_mb, 100, self.last_mb[url][method])
        if mb:
            print(f'mb {total_mb} of limit 100 hit')
            return True

        # Check if the last request for the same method was within 10 seconds
        time_rate = [
            query for query in self.rate_limits[url] if is_time_interval(query.get('time') or 0, 10)
        ]
        if len(time_rate) > 100:
            print(f'time_rate {time_rate} of timerate limit 100 hit')
            return True

        method_specific_time_rate = [
            query for query in time_rate if query['method'] == method
        ]
        if len(method_specific_time_rate) > 40:
            print(f'method_specific_time_rate {len(method_specific_time_rate)} of method_specific_time_rate limit 40 hit')
            return True

        return False

    def log_response(self, method=None, response=None, retry_after=None):
        method = method or 'default_method'
        response = response or {}
        data_size = datasize(response)
        active_url = self.last_url

        # Handle Retry-After logic
        if retry_after:
            try:
                wait_time = int(retry_after)
            except ValueError:
                retry_after_date = datetime.strptime(retry_after, '%a, %d %b %Y %H:%M:%S GMT')
                wait_time = (retry_after_date - datetime.utcnow()).total_seconds()
            self.set_cooldown(active_url, method, add=max(wait_time, 0))

        if active_url == self.url1:
            self.rate_limits[active_url].append({'method': method, 'data': data_size, 'time': time.time()})

        # Clean up expired entries for the current URL
        self.rate_limits[active_url] = [
            query for query in self.rate_limits[active_url] if is_time_interval(query['time'], 30)
        ]
        self.save_state()
    def get_cooldown_for_method(self,url,method):
        wait_time = 0
        if self.set_cooldown(url,method):
          wait_time = int(self.cooldown_times[url][method]) - time.time()
          if wait_time <= 0:
            del self.cooldown_times[url][method]
           
          else:
            return wait_time
        return False
    def get_url(self, method=None):
        method = method or 'default_method'
        wait_time = self.get_cooldown_for_method(self.url1,method)
        
        if wait_time:
          wait_time = int(self.cooldown_times[self.url1][method]) - time.time()
          if wait_time > 0:
            self.last_url = self.url2
            #retry_after_date = datetime.strptime(str(int(self.cooldown_times[method])), '%a, %d %b %Y %H:%M:%S GMT')
            print(f"{method} is on cooldown for {wait_time} more seconds")
        if method == 'get_url2':
          self.last_url = self.url2
          return self.last_url
        # If fallback URL is selected, skip all limits
 
        is_limit = self.is_all_limit(self.url1, method)
        if not is_limit:
            self.last_method = method
            self.last_url = self.url1
        print([is_limit,self.last_url])
        return self.last_url

