import json
import socket
import sys
from concurrent.futures import ThreadPoolExecutor
import time

SERVER_DICT = {}

with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# 绑定注册中心服务端口并监听
host = CONFIG['listen']['host']
port = CONFIG['listen']['port']
reg_center_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
for tries in range(1, CONFIG['max_tries']+1):
    try:
        reg_center_listen_socket.bind((host, port))
        reg_center_listen_socket.listen()
        break
    except Exception as e:
        print('❌', f'Failed to bind to {host}:{port}, error: {e}', file=sys.stderr)
        if tries == CONFIG['max_tries']:
            print('❌', 'Aborted.', file=sys.stderr)
            exit(1)
        time.sleep(3)
print('✅', f'Register service running on {host}:{port}')

def handle_reg(msg, conn, addr):
    '''会覆盖同一IP的旧注册信息，这样就允许服务端更新端口和服务列表'''
    SERVER_DICT[addr[0]] = {
        'last_heartbeat': time.time(),
        'port': msg['port'],
        'services': msg['services']
    }
    conn.send(b'{"status": "success"}')

def handle_heartbeat(conn, addr):
    if addr[0] not in SERVER_DICT:
        conn.send(b'{"status": "fail", "error": "Server not registered"}')
        return
    SERVER_DICT[addr[0]]['last_heartbeat'] = time.time()
    conn.send(b'{"status": "success"}')

def handle_pull(conn, _addr):
    now = time.time()
    filtered = [ {'ip': k,
                  'port': v['port'],
                  'services': v['services']}
                for k, v in SERVER_DICT.items()
                    if now - v['last_heartbeat'] < 5 ]
    response = json.dumps({
        'status': 'success',
        'servers': filtered
    }).encode()
    conn.send(response)

def handle_conn(conn, addr):
    try:
        data = conn.recv(2048)
        if not data:
            conn.close()
            return
        msg = json.loads(data.decode())
        match msg['type']:
            case 'reg':
                handle_reg(msg, conn, addr)
            case 'heartbeat':
                handle_heartbeat(conn, addr)
            case 'pull':
                handle_pull(conn, addr)
            case _:
                conn.send(json.dumps({'status': 'fail', 'error': 'Type not supported'}).encode())
        conn.close()
    except Exception as e:
        print('❌', 'Error occurred:', e, file=sys.stderr)
        try:
            conn.send(json.dumps({'status': 'fail', 'error': str(e)}).encode())
            conn.close()
        except:
            pass

# 主循环，接受连接并交给线程池处理
with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
    while True:
        conn, addr = reg_center_listen_socket.accept()
        executor.submit(handle_conn, conn, addr)
