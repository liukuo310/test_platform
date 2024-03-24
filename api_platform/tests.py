from django.test import TestCase
def world(fn):
    print('world')
    return fn()


@world
def hello():
    print('hello')


if __name__ == '__main__':
    a = 1
    b = a
    print(id(a))
    print(id(b))
