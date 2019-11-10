from strategy_tester.account import Account
from strategy_tester.order import Order
from strategy_tester.strategy import Strategy
from strategy_tester.risk_management import ConstantRate
from strategy_tester.simulate import BackTest
from strategy_tester.utils import generate_data

data     = generate_data(100000)
account  = Account(balance=1000)
risk_man = ConstantRate(0.05)
strategy = Strategy(RiskManagement=risk_man,id=23030,name='noise_trader')
sim      = BackTest(account,strategy).run(data.values)
print(sim.Account.balances)