import sys
import numpy as np
import pandas as pd
sys.path.insert(0,'../')

from strategy_tester.account import Account
from strategy_tester.asset import AAPL
from strategy_tester.strategy import Strategy
from strategy_tester.risk_management import ConstantRate
from strategy_tester.simulate import BackTest
from strategy_tester.utils import generate_data
import numpy as np


aapl = AAPL(generate_data(40000))
account = Account(initial_balance=1000)
risk_man = ConstantRate(0.05)

strategy = Strategy(RiskManagement=risk_man,id=23030,name='noise_trader')
strategy = aapl.register(strategy)

print()
sim = BackTest(Account=account,Strategy=strategy).run(aapl)
print(sim.Account.balances[:3])
print(sim.Account)