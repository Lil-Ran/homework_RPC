import json
import socket
import sys
from concurrent.futures import ThreadPoolExecutor
import time

from services import service_list

with open('config.json', 'r') as f:
    CONFIG = json.load(f)

def connect_to_register_center() -> socket.socket:
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for tries in range(1, CONFIG['max_tries']+1):
        try:
            conn.connect((CONFIG['register']['host'], CONFIG['register']['port']))
            break
        except Exception as e:
            print('❌', f'Failed to connect to register center ({tries} tries), error: {e}', file=sys.stderr)
            if tries == CONFIG['max_tries']:
                print('❌', 'Aborted.', file=sys.stderr)
                exit(1)
            time.sleep(3)
    return conn

def heartbeat():
    while True:
        for tries in range(1, CONFIG['max_tries']+1):
            try:
                conn = connect_to_register_center()
                conn.send(b'{"type": "heartbeat"}')
                response = conn.recv(1024).decode()
                if json.loads(response)['status'] != 'success':
                    raise ValueError('Response not success:' + response)
                break
            except Exception as e:
                print('⚠', f'Heartbeat failed ({tries} tries), error: {e}', file=sys.stderr)
                register()
                if tries == CONFIG['max_tries']:
                    print('❌', 'Aborted.', file=sys.stderr)
                    exit(1)
        time.sleep(CONFIG['heartbeat_interval'])

def register():
    for tries in range(1, CONFIG['max_tries']+1):
        reg_msg = {
            'type': 'reg',
            'port': CONFIG['listen']['port'],
            'services': [{
                    'name': s,
                    'detail': service_list[s].__doc__,
                } for s in service_list
            ],
        }
        conn = connect_to_register_center()
        try:
            conn.send(json.dumps(reg_msg).encode())
            response = conn.recv(1024).decode()
            if json.loads(response)['status'] != 'success':
                raise ValueError('Response not success:' + response)
            break
        except Exception as e:
            print('❌', 'Failed to register services, error:', e, file=sys.stderr)
            if tries == CONFIG['max_tries']:
                print('❌', 'Aborted.', file=sys.stderr)
                exit(1)
            time.sleep(3)

def handle_conn(conn, _addr):
    '''提供服务的主要函数，会同步调用具体服务'''
    try:
        data = conn.recv(2048)
        if not data:
            conn.close()
            return
        msg = json.loads(data.decode())
        if msg['type'] != 'req':
            conn.send(b'{"status": "fail", "error": "Type not supported"}')
            conn.close()
            return
        service = msg['service']
        if service not in service_list:
            conn.send(b'{"status": "fail", "error": "Service not found"}')
            conn.close()
            return
        try:
            result = service_list[service].handler(msg['params'])
            conn.send(json.dumps({'status': 'success', 'result': result}).encode())
        except Exception as e:
            conn.send(json.dumps({'status': 'fail', 'error': str(e)}).encode())
        conn.close()
    except Exception as e:
        print('❌', 'Error occurred:', e, file=sys.stderr)
        try:
            conn.send(json.dumps({'status': 'fail', 'error': str(e)}).encode())
            conn.close()
        except:
            pass

# 绑定服务端口并监听
host = CONFIG['listen']['host']
port = CONFIG['listen']['port']
service_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
for tries in range(1, CONFIG['max_tries']+1):
    try:
        service_listen_socket.bind((host, port))
        service_listen_socket.listen()
        break
    except Exception as e:
        print('❌', f'Failed to bind or listen on {host}:{port} ({tries} tries), error: {e}', file=sys.stderr)
        if tries == CONFIG['max_tries']:
            print('❌', 'Aborted.', file=sys.stderr)
            exit(1)
        time.sleep(3)
print('✅', f'Service running on {host}:{port}')

register()

# 主循环，接受连接并交给线程池处理
with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
    executor.submit(heartbeat)
    while True:
        conn, addr = service_listen_socket.accept()
        executor.submit(handle_conn, conn, addr)
