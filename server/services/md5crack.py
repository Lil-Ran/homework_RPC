__doc__ = 'Bruteforce an MD5 hash. (target: str, length: int) -> str'

from itertools import product
from hashlib import md5

def handler(params):
    target, length = params
    assert len(target) == 32
    assert all(c in '0123456789abcdef' for c in target)

    dic = product('0123456789', repeat=length)
    for i in dic:
        if md5(''.join(i).encode()).hexdigest() == params[0]:
            return ''.join(i)

    raise ValueError('No solution found')

if __name__ == '__main__':
    print(handler(['a14b1bbaad4c127657d9c8d907fc6a75', 7]))
