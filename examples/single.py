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

aapl = AAPL(generate_data(100000).values)
account = Account(balance=1000)
risk_man = ConstantRate(0.05)

strategy = Strategy(RiskManagement=risk_man,id=23030,name='noise_trader')
strategy = aapl.register(strategy)

sma = moving_average(aapl.data[:,1],35)

sim = BackTest(Account=account,Strategy=strategy).run(aapl,exog=sma)
print(sim.Account.balances)