import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "../")

from strategy_tester.account import Account
from strategy_tester.asset import Stock
from strategy_tester.strategy import Strategy
from strategy_tester.risk_management import ConstantRate
from strategy_tester.simulate import BackTest
from strategy_tester.utils import generate_data, ROI, sharpe_ratio


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1 :] / n


class MACross(Strategy):
    def decide_long_open(self, tickers, Account, exog):
        "Exog[0]: Slow MA, Exog[1]: Fast MA"
        output = {}
        #        for asset_id in self.on:
        #            if asset_id in spot_price.keys():
        #                if exog[0] > exog[1]:
        #                    args = {
        #                        "type": "market",
        #                        "size": self.RiskManagement.order_size(Account),
        #                        "strike_price": spot_price[asset_id],
        #                    }
        #                    output[asset_id] = args
        for ticker in tickers:
            if ticker.aid in self.on:
                if exog[0] > exog[1]:
                    args = {
                        "type": "market",
                        "size": self.RiskManagement.order_size(Account),
                        "strike_price": ticker.price,
                    }
                    output[ticker.aid] = args
        return output

    def decide_short_open(self, tickers, Account, exog):
        "Exog[0]: Slow MA, Exog[1]: Fast MA"
        output = {}
        #        for asset_id in self.on:
        #            if asset_id in spot_price.keys():
        #                if exog[0] < exog[1]:
        #                    args = {
        #                        "type": "market",
        #                        "size": self.RiskManagement.order_size(Account),
        #                        "strike_price": spot_price[asset_id],
        #                    }
        #                    output[asset_id] = args
        for ticker in tickers:
            if ticker.aid in self.on:
                if exog[0] < exog[1]:
                    args = {
                        "type": "market",
                        "size": self.RiskManagement.order_size(Account),
                        "strike_price": ticker.price,
                    }
                    output[ticker.aid] = args
        return output

    def decide_long_close(self, order, tickers, Account, exog):
        return exog[0] < exog[1]

    def decide_short_close(self, order, tickers, Account, exog):
        return exog[0] > exog[1]


np.random.seed(123)
aapl = Stock(price=generate_data(100000), base="AAPL")
account = Account()
risk_man = ConstantRate(0.01, on="free_margin")

strategy = MACross(RiskManagement=risk_man, id=45450, name="ma_cross_trader")
strategy = aapl.register(strategy)

slow_period = 55
fast_period = 35


def convert_ticker_data(tickers, fields=None):
    output = []
    for ticker in tickers:
        output.append(ticker.to_dict(fields))
    return pd.DataFrame(output)


d = convert_ticker_data(aapl.data(), ["price"])


sma = np.zeros((d.shape[0], 2))
sma[(slow_period - 1) :, 0] = moving_average(d.values, slow_period)
sma[(fast_period - 1) :, 1] = moving_average(d.values, fast_period)

sim = BackTest(
    Account=account, Strategy=strategy, track=(ROI, sharpe_ratio)
).run(aapl, exog=sma)

print(sim.Account.balances)
sim.Account.plot_results()