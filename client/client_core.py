import json
import random
import socket
import sys
import time

with open('config.json', 'r') as f:
    CONFIG = json.load(f)

class MyRPC():
    '''
    Example:

    ```python
    from client_core import MyRPC

    rpc = MyRPC()
    # rpc.pull() will be called automatically
    
    rpc.print_list()

    x = rpc.mul(6, 7)
    # or: x = rpc.call('mul', 6, 7)
    # x is 42
    ```
    '''
    
    def __init__(self, address=None, debug=False) -> None:
        self.address = address if address else (CONFIG['register']['host'], CONFIG['register']['port'])
        self.debug = debug
        self.service_list = {'last_update': 0.0, 'services': {}}
        self.last_try_pull = 0.0
        self.pull()

    def pull(self):
        if time.time() - self.last_try_pull < 1:
            time.sleep(1)
        self.last_try_pull = time.time()
        try:
            pull_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            pull_conn.connect(self.address)
            pull_conn.send(b'{"type": "pull"}')
            data = pull_conn.recv(4096)
            pull_conn.close()
        except Exception as e:
            if self.debug:
                print('⚠', f'[DEBUG] [{time.strftime('%H:%M:%S')}] Failed to pull server list, error:', e, file=sys.stderr)
            return
            # 后续发现找不到服务时会重试的
        msg = json.loads(data.decode())
        if msg['status'] != 'success':
            if self.debug:
                print('⚠', f'[DEBUG] [{time.strftime('%H:%M:%S')}] Failed to pull server list, responce:', data.decode(), file=sys.stderr)
            return
        temp_service_list = {'last_update': time.time(), 'services': {}}
        for info in msg['servers']:
            for service in info['services']:
                if service['name'] not in temp_service_list['services']:
                    temp_service_list['services'][service['name']] = {
                        'detail': service['detail'],
                        'provider': []
                    }
                temp_service_list['services'][service['name']]['provider'].append((info['ip'], info['port']))
        self.service_list = temp_service_list

    def print_list(self):
        print('[RPC] Service list:')
        print('-' * 40)
        for k, v in self.service_list['services'].items():
            print(f'{k}: {v["detail"]}')
            for provider in v['provider']:
                print(f'\t{provider[0]}:{provider[1]}')
        print('-' * 40)

    def call(self, name, *args):
        '''非调试模式下，可能向用户抛出 ModuleNotFoundError 或 ValueError 或 连接或JSON处理过程中的异常'''
        
        # 确认服务可用，否则更新服务列表
        is_in_ttl = lambda: time.time() - self.service_list['last_update'] < CONFIG['service_list_ttl']
        is_service_available = lambda: \
            (name in self.service_list['services']) \
            and (self.service_list['services'][name]['provider'])
        for tries in range(CONFIG['max_tries']):
            if is_in_ttl() and is_service_available():
                break
            self.pull()
            if tries == CONFIG['max_tries'] - 1 and not is_service_available():
                # 在无法连接注册中心的时候，过期的服务列表是可以接受的
                if self.debug:
                    print(f'❌  [DEBUG] [{time.strftime('%H:%M:%S')}] No provider for service: {name}, params: {args}', file=sys.stderr)
                    return
                else:
                    raise ModuleNotFoundError(f'No provider for service `{name}`')

        # 打乱尝试序列，并逐个尝试
        providers = self.service_list['services'][name]['provider'].copy()
        random.shuffle(providers)
        for tries in range(CONFIG['max_tries']):
            try:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                provider = providers[tries % len(providers)]
                conn.connect(provider)
                conn.send(json.dumps({
                    'type': 'req',
                    'service': name,
                    'params': args,
                }).encode())
                data = conn.recv(4096)
                conn.close()
                if not data:
                    continue
                msg = json.loads(data.decode())
                break
            except Exception as e:
                self.pull()
                if tries == CONFIG['max_tries'] - 1:
                    if self.debug:
                        print(f'❌  [DEBUG] [{time.strftime('%H:%M:%S')}] service: {name}, params: {args}, error: {e}')
                        return
                    else:
                        raise e

        if msg['status'] != 'success':
            if self.debug:
                print(f'❌  [DEBUG] [{time.strftime('%H:%M:%S')}] Service: {name}, params: {args}, response: {data.decode()}')
                return
            else:
                raise ValueError(f'Service: {name}, params: {args}, response: {data.decode()}')

        if self.debug:
            print(f'✅  [DEBUG] [{time.strftime('%H:%M:%S')}] provider: {provider}, service: {name}, params: {args}, response: {msg["result"]}')
            
        return msg['result']

    # 语法糖，提供快捷调用方式
    class __RpcActionBuilder:
        def __init__(self, name, parent) -> None:
            self.name = name
            self.parent = parent

        def __call__(self, *args):
            return self.parent.call(self.name, *args)

        # def __str__(self):
        #     return f'<RPC Service: {self.name}, desc: {self.parent.service_list["services"][self.name]["detail"]}>'

    def __getattribute__(self, name: str):
        if name in ['pull', 'print_list', 'call', 'address', 'service_list', 'debug', 'last_try_pull'] \
            or name.startswith('__'):
            return super(MyRPC, self).__getattribute__(name)
        return MyRPC.__RpcActionBuilder(name, self)

if __name__ == '__main__':    
    print('''This file is not meant to be run directly.
Please import this file in your main program.''', file=sys.stderr)
    print(MyRPC.__doc__, file=sys.stderr)
    exit(1)
