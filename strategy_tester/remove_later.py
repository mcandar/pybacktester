import numpy as np
import timeit

n = 1000000                                                                                                                                               
l1 = [[-1,-2,-3] for i in range(n)]
l2 = [{'a':-1,'b':-2,'c':-3} for i in range(n)]
class foo:
    def __init__(self):
        self.first = -1
        self.second = -2
        self.third = -3
l3 = [foo() for i in range(n)]
idx = np.random.randint(0,n,100000)

def iter_l1(x,idx):
    n = 0
    for i in idx:
        tmp = x[i]
        n = (tmp[0],tmp[1],tmp[2])
    return n

def iter_l2(x,idx):
    n = 0
    for i in idx:
        tmp = x[i]
        n = (tmp['a'],tmp['b'],tmp['c'])
    return n

def iter_l3(x,idx):
    n = 0
    for i in idx:
        tmp = x[i]
        n = (tmp.first,tmp.second,tmp.third)
    return n

%%timeit
iter_l1(l1,idx)

%%timeit
iter_l2(l2,idx)

%%timeit
iter_l3(l3,idx)