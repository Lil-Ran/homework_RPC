__doc__ = 'Multiply a and b. (a: int, b: int) -> int'

def handler(params):
    return params[0] * params[1]

if __name__ == '__main__':
    print(handler([-6, -7]))
