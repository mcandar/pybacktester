import sys
import numpy as np
import pandas as pd
sys.path.insert(0,'../')

from strategy_tester.account import Account
from strategy_tester.asset import EURUSD
from strategy_tester.strategy import Strategy
from strategy_tester.risk_management import ConstantRate, KellyCriterion
from strategy_tester.simulate import BackTest
from strategy_tester.utils import generate_data


eurusd = EURUSD(generate_data(100000).values)
account = Account(balance=1000)

strategy_1 = Strategy(RiskManagement=ConstantRate(0.05),id=23030,name='noise_trader_1')
strategy_2 = Strategy(RiskManagement=KellyCriterion(n=20),id=23031,name='noise_trader_2')
strategy_1, strategy_2 = eurusd.register(strategy_1,strategy_2)

sim = BackTest(Account=account,Strategy=[strategy_1,strategy_2]).run(eurusd)
print(sim.Account.balances)