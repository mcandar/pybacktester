import sys
import numpy as np
import pandas as pd
sys.path.insert(0,'../')

from strategy_tester.account import Account
from strategy_tester.asset import Stock
from strategy_tester.strategy import Strategy
from strategy_tester.risk_management import ConstantRate
from strategy_tester.simulate import BackTest
from strategy_tester.utils import generate_data


class CustomAllocation(Strategy):
    def __init__(self,n=5,n_samples=60,max_stocks=10,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.n = n
        self.n_samples = n_samples
        self.max_stocks = max_stocks
        
        self.n_stocks = 0
        self.past_data = []
        self.last_selected = None
        self.last_t = 0
    
    def filter_stocks(self,past_data,n=5):
        df = pd.DataFrame(past_data)
        df = df.tail(100) # get most 100 of most recent prices
        r = df.diff()/df # calculate returns
        means = r.mean() # calculate means
        return means.sort_values()[-n:] # get top n of them
        
    def decide_long_open(self,spot_price,timestamp,Account,exog):
        output = {}
        t = timestamp
        if t.hour == 0 and t.minute == 0: # run once a day at 00:00
            self.past_data.append(spot_price)
            if len(self.past_data) < self.n_samples: # wait for sufficient number of samples
                output = None
            else:
                selected = self.filter_stocks(self.past_data,self.n) # choose best performing n stocks so far

                for asset_id in self.on: # for each stock this strategy is registered to work on
                    if asset_id in spot_price.keys() and asset_id in selected.index: # if that stock is in the received list of prices and selected for buying
                        if self.n_stocks < self.max_stocks:
                            # decide order parameters
                            args = {
                                'type':'market',
                                'size':self.RiskManagement.order_size(Account),
                                'strike_price':spot_price[asset_id],
                                'stop_loss':None,
                                'take_profit':None
                            }
                            output[asset_id] = {'decision':True,
                                                'params':args}
                            self.n_stocks += 1
                self.last_selected = selected # store currently selected stocks for later comparison
                del self.past_data[0] # remove first item (roll on a constant size)
        else:
            output = None
        return output

    def decide_short_open(self,spot_price,timestamp,Account,exog):
        "No short sells."
        return None
    
    def decide_long_close(self,order,spot_price,timestamp,Account,exog):
        t = timestamp
        if self.last_t != t:
            self.last_t = t
            if t.hour == 0 and t.minute == 0:
                self.past_data.append(spot_price)
                if len(self.past_data) < self.n_samples:
                    return False
                else:
                    selected = self.filter_stocks(self.past_data,self.n) # selected for long (that we would have select for buying)

                    self.selected_to_close = []
                    for stock in self.last_selected.index: # for each last chosen stocks
                        if stock not in selected.index:
                            self.selected_to_close.append(stock)
                    del self.past_data[0]
                    return order.asset_id in self.selected_to_close # close if the order is selected for close
            else:
                return False
        else:
            return order.asset_id in self.selected_to_close # close if the order is selected for close
    
    def decide_short_close(self,order,spot_price,timestamp,Account,exog):
        return False


stocks = [Stock(generate_data(10000,freq='1h').values,name=f'stock_{i}',short_name=f'STCK_{i}') for i in range(20)] # randomly generate stock prices
account = Account(balance=1000) # initialize an account with 1000 USD balance
risk_man = ConstantRate(0.05) # constant lot size with 5% of balance each time

strategy = CustomAllocation(RiskManagement=risk_man,id=45450,name='custom_buyer')
for stock in stocks:
    strategy = stock.register(strategy) # allow strategy to use all of them, either one or multiple

sim = BackTest(Account=account,Strategy=strategy).run(stocks)
print(sim.Account.balances)