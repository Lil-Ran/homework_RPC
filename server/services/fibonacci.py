__doc__ = 'Calculate the n-th Fibonacci number. (n: int) -> int'

from threading import Lock

CACHE = [1, 1]
LOCK = Lock()

def handler(params):
    n = params[0]
    if n < 0:
        raise ValueError('n should be non-negative')
    if n < len(CACHE):
        return CACHE[n]
    LOCK.acquire()
    if n < len(CACHE):   # 其他线程已经计算好了
        LOCK.release()
        return CACHE[n]
    for i in range(len(CACHE), n + 1):
        CACHE.append(CACHE[i - 1] + CACHE[i - 2])
    LOCK.release()
    return CACHE[n]

if __name__ == '__main__':
    print(handler([5]))
    print(handler([10000]))
    print(handler([10086]))
