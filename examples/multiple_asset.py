import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "../")

from strategy_tester.account import Account
from strategy_tester.asset import Currency  # EURUSD, GBPUSD
from strategy_tester.strategy import Strategy
from strategy_tester.risk_management import ConstantRate
from strategy_tester.simulate import BackTest
from strategy_tester.utils import generate_data


eurusd = Currency(price=generate_data(1000000), base="EUR", quote="USD")
gbpusd = Currency(price=generate_data(1000000), base="GBP", quote="USD")

account = Account()
risk_man = ConstantRate(0.1)

strategy_1 = Strategy(RiskManagement=risk_man, id=23030, name="noise_trader")
strategy_2 = Strategy(RiskManagement=risk_man, id=23031, name="noise_trader2")
strategy_1, strategy_2 = eurusd.register(strategy_1, strategy_2)
strategy_1 = gbpusd.register(strategy_1)

sim = BackTest(Account=account, Strategy=[strategy_1, strategy_2]).run(
    assets=(eurusd, gbpusd)
)
print(sim.Account.balances)