from strategy_tester.account import Account
from strategy_tester.asset import AAPL
from strategy_tester.strategy import Strategy
from strategy_tester.risk_management import ConstantRate
from strategy_tester.simulate import BackTest
from strategy_tester.utils import generate_data
import numpy as np

def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

class MACross(Strategy):
    def decide_long_open(self,spot_price,timestamp,Account,exog):
        "Exog[0]: Slow MA, Exog[1]: Fast MA"
        output = {}
        for aid in self.on:
            if aid in spot_price.keys():
                args = {
                    'type':'market',
                    'size':self.RiskManagement.order_size(Account),
                    'strike_price':spot_price[aid],
                    'stop_loss':None,
                    'take_profit':None
                }
                output[aid] = {'decision':exog[0] > exog[1],
                               'params':args}
        return output

    def decide_short_open(self,spot_price,timestamp,Account,exog):
        "Exog[0]: Slow MA, Exog[1]: Fast MA"
        output = {}
        for aid in self.on:
            if aid in spot_price.keys():
                args = {
                    'type':'market',
                    'size':self.RiskManagement.order_size(Account),
                    'strike_price':spot_price[aid],
                    'stop_loss':None,
                    'take_profit':None
                }
                output[aid] = {'decision':exog[0] < exog[1],
                               'params':args}
        return output
    
    def decide_long_close(self,order,spot_price,timestamp,Account,exog):
        return exog[0] < exog[1]
    
    def decide_short_close(self,order,spot_price,timestamp,Account,exog):
        return exog[0] > exog[1]


aapl = AAPL(generate_data(100000).values)
account = Account(balance=1000)
risk_man = ConstantRate(0.05)

strategy = MACross(RiskManagement=risk_man,id=45450,name='ma_cross_trader')
strategy = aapl.register(strategy)

slow_period = 45
fast_period = 35
sma = np.zeros((aapl.data.shape[0],2))
sma[(slow_period-1):,0] = moving_average(aapl.data[:,1],slow_period)
sma[(fast_period-1):,1] = moving_average(aapl.data[:,1],fast_period)

sim = BackTest(Account=account,Strategy=strategy).run(aapl,exog=sma)
print(sim.Account.balances)