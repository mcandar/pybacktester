import sys
import numpy as np
import pandas as pd
sys.path.insert(0,'../')

from strategy_tester.account import Account
from strategy_tester.asset import AAPL
from strategy_tester.strategy import Strategy
from strategy_tester.risk_management import ConstantRate
from strategy_tester.simulate import BackTest
from strategy_tester.utils import generate_data, ROI, sharpe_ratio
import numpy as np

def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

class MACross(Strategy):
    def decide_long_open(self,spot_price,timestamp,Account,exog):
        "Exog[0]: Slow MA, Exog[1]: Fast MA"
        output = {}
        for asset_id in self.on:
            if asset_id in spot_price.keys():
                if exog[0] > exog[1]:
                    args = {
                        'type':'market',
                        'size':self.RiskManagement.order_size(Account),
                        'strike_price':spot_price[asset_id]
                    }
                    output[asset_id] = args
        return output

    def decide_short_open(self,spot_price,timestamp,Account,exog):
        "Exog[0]: Slow MA, Exog[1]: Fast MA"
        output = {}
        for asset_id in self.on:
            if asset_id in spot_price.keys():
                if exog[0] < exog[1]:
                    args = {
                        'type':'market',
                        'size':self.RiskManagement.order_size(Account),
                        'strike_price':spot_price[asset_id]
                    }
                    output[asset_id] = args
        return output
    
    def decide_long_close(self,order,spot_price,timestamp,Account,exog):
        return exog[0] < exog[1]
    
    def decide_short_close(self,order,spot_price,timestamp,Account,exog):
        return exog[0] > exog[1]

np.random.seed(123)
aapl = AAPL(generate_data(100000))
account = Account(initial_balance=1000)
risk_man = ConstantRate(0.01,on='free_margin')

strategy = MACross(RiskManagement=risk_man,id=45450,name='ma_cross_trader')
strategy = aapl.register(strategy)

slow_period = 45
fast_period = 35
sma = np.zeros((aapl.data.shape[0],2))
sma[(slow_period-1):,0] = moving_average(aapl.data[:,1],slow_period)
sma[(fast_period-1):,1] = moving_average(aapl.data[:,1],fast_period)

sim = BackTest(Account=account,Strategy=strategy,track=(ROI,sharpe_ratio)).run(aapl,exog=sma)
print(sim.tracked_results)
print(sim.Account.balances)
print(sim.Account.equities)
print(sim.Account.free_margins)
print(sim.Account.navs)
print(sim.Account.n_inactive_orders)
print(sim.Account.max_n_active_orders)
print(sim.Account.time)