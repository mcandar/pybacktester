import itertools, random
from datetime import datetime as dt
import numpy as np
import pandas as pd

def generate_data(n,start_date='2017-10-21 00:00:00',freq='1min',digits=5):
    price = np.round(np.exp(np.cumsum(np.random.laplace(0,0.02,n))),digits)
    start = pd.to_datetime(start_date)
    end = start + (pd.Timedelta(freq)*(price.shape[0]-1))
    ts = pd.date_range(start,end,freq=freq)
    return pd.DataFrame({'timestamp':ts,'price':price}).values

def dict_product(dicts):
    """
    >>> list(dict_product(dict(number=[1,2], character='ab')))
    [{'character': 'a', 'number': 1},
     {'character': 'a', 'number': 2},
     {'character': 'b', 'number': 1},
     {'character': 'b', 'number': 2}]
    """
    return (dict(zip(dicts, x)) for x in itertools.product(*dicts.values()))

# TO DO: apply a generic ID convention to all classes
def generate_id(prefix='',suffix='',digits=6,timestamp=True):
    ts = f'TS{int(dt.utcnow().timestamp())}' if timestamp else ''
    return f'{prefix}{random.randint(10**(digits-1),10**digits-1)}{ts}{suffix}'
