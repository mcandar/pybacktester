from strategy_tester.account import Account
from strategy_tester.asset import EURUSD, GBPUSD
from strategy_tester.strategy import Strategy
from strategy_tester.risk_management import ConstantRate
from strategy_tester.simulate import BackTest
from strategy_tester.utils import generate_data


eurusd   = EURUSD(data=generate_data(100000).values)
gbpusd   = GBPUSD(data=generate_data(100000).values)

account  = Account(balance=1000)
risk_man = ConstantRate(0.1)

strategy_1 = Strategy(RiskManagement=risk_man,id=23030,name='noise_trader')
strategy_2 = Strategy(RiskManagement=risk_man,id=23031,name='noise_trader2')
strategy_1,strategy_2 = eurusd.register(strategy_1,strategy_2)
strategy_1 = gbpusd.register(strategy_1)

sim      = BackTest(account,[strategy_1,strategy_2]).run(assets=(eurusd,gbpusd))
print(sim.Account.balances)