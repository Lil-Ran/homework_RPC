import time

from client_core import MyRPC

rpc = MyRPC(debug=True)

print('======== 启动阶段 ========')
print('客户端运行到这里，服务端不一定已经注册')
print()

for i in range(3):
    print(f'第 {i+1} 次：')
    rpc.mul(6, 7)
    rpc.print_list()
    print()
    time.sleep(1)

from hashlib import md5
import random
import concurrent.futures

print()
print('======== 16 线程随机发起 100 次调用 ========')
print()

def test_mul(i):
    x = random.randint(0, 100)
    y = random.randint(0, 100)
    print(f'⏩  [TEST]  [{time.strftime("%H:%M:%S")}] 发起请求 [{i:>2}] mul({x}, {y})')
    rpc.mul(x, y)

def test_fibonacci(i):
    x = random.randint(100, 4000)
    print(f'⏩  [TEST]  [{time.strftime("%H:%M:%S")}] 发起请求 [{i:>2}] fibonacci({x})')
    rpc.fibonacci(x)

def test_md5crack(i):
    x = ''.join([str(random.randint(0, 9)) for _ in range(random.randint(5, 8))])
    target = md5(x.encode()).hexdigest()
    print(f'⏩  [TEST]  [{time.strftime("%H:%M:%S")}] 发起请求 [{i:>2}] md5crack({target[:8]}..., {len(x)}), answer should be {x}')
    rpc.md5crack(target, len(x))

choices = [test_mul] * 6 + [test_fibonacci] * 3 + [test_md5crack]
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
    futureset = {executor.submit(random.choice(choices), i) for i in range(100)}
    for future in concurrent.futures.as_completed(futureset):
        try:
            future.result()
        except Exception as e:
            print(f'❌  [ERROR]  {e}')

print()
print('======== 异常情况测试 ========')
print()

print('⏩  [TEST] 未注册的服务')

print('TRYING: rpc.unregistered_service()')
rpc.unregistered_service()
print()

print('TRYING: rpc.call("unknown_qaq", 113513)')
rpc.call("unknown_qaq", 113513)
print()

print('⏩  [TEST] 错误的参数')

print('TRYING: rpc.mul("foo", "bar")')
rpc.mul("foo", "bar")
print()

print('TRYING: rpc.fibonacci(-3.14)')
rpc.fibonacci(-3.14)
print()

print('======== 测试结束 ========')
