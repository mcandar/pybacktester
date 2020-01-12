import sys
import numpy as np
import pandas as pd
sys.path.insert(0,'../')

from strategy_tester.account import Account
from strategy_tester.asset import AAPL
from strategy_tester.strategy import Strategy
from strategy_tester.risk_management import ConstantLots
from strategy_tester.simulate import BackTest
from strategy_tester.utils import generate_data, ROI, sharpe_ratio
import numpy as np

import time
start = time.time()
aapl = AAPL(generate_data(100000))
account = Account(initial_balance=1000,max_allowed_risk=None)
risk_man = ConstantLots(0.1)

strategy = Strategy(RiskManagement=risk_man,id=23030,name='noise_trader')
strategy = aapl.register(strategy)

sim = BackTest(Account=account,Strategy=strategy,track=[ROI,sharpe_ratio]).run(aapl)
print(sim.tracked_results)
print(sim.Account.balances)
print(sim.Account.equities)
print(sim.Account.navs)
# print(sim.Account.inactive_orders)
print(sim.Account.n_inactive_orders)
end = time.time()
print(f'{end-start} seconds elapsed.')
print(sim.Account.time)