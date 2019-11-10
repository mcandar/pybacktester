import numpy as np
import pandas as pd

def generate_data(n,start_date='2017-10-21 00:00:00',freq='1min'):
    price = np.exp(np.cumsum(np.random.laplace(0,0.02,n)))
    start = pd.to_datetime(start_date)
    end = start + (pd.Timedelta('1min')*(price.shape[0]-1))
    ts = pd.date_range(start,end,freq=freq)
    return pd.DataFrame({'timestamp':ts,'price':price})