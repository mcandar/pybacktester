import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, "../")

from strategy_tester.account import Account
from strategy_tester.asset import Stock
from strategy_tester.strategy import Strategy
from strategy_tester.risk_management import RiskManagement
from strategy_tester.simulate import BackTest
from strategy_tester.utils import generate_data


class CustomAllocation(Strategy):
    """
    Monthly-rebalanced, long-only 1 Year's momentum factor investing.
    """

    def __init__(self, n=20, n_samples=252, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.n = n
        self.n_samples = n_samples

        self.n_stocks = 0
        self.past_data = []
        self.last_selected = None
        self.last_t = 0
        self.last_rebalanced_t = 0

    def momentum_factor(self):
        """
        Choose top-n stocks out of the universe based on 1 month's momentum.
        """
        return (
            pd.DataFrame(self.past_data)[self.on]
            .pct_change()
            .mean()
            .sort_values(ascending=False)
            .head(self.n)
            .index
        )

    def decide_long_open(self, tickers, Account, exog):
        output = {}
        t = tickers[0].timestamp

        ticker_dict = {ticker.aid: ticker.price for ticker in tickers}
        self.past_data.append(ticker_dict)

        # run once a month
        if t.month == self.last_rebalanced_t:
            return None

        # wait for sufficient number of samples
        if len(self.past_data) < self.n_samples:
            return None

        # choose best performing n stocks so far
        selected_ids = self.momentum_factor()

        for aid in selected_ids:
            price = ticker_dict[aid]

            # decide order parameters
            args = {
                "type": "market",
                "size": self.RiskManagement.order_size(
                    Account, n=self.n, price=price
                ),
                "strike_price": price,
            }
            output[aid] = args
            self.n_stocks += 1

        # store currently selected stocks for later comparison
        self.last_selected = selected_ids
        self.last_rebalanced_t = t.month

        # remove first item (roll on a constant size)
        del self.past_data[0]

        return output

    def decide_short_open(self, tickers, Account, exog):
        "No short sells."
        return None

    def decide_long_close(self, order, tickers, Account, exog):
        t = tickers[0].timestamp

        # if a new month is started, close all positions
        if t.month != self.last_rebalanced_t:
            self.n_stocks -= 1
            return True
        else:
            return False

    def decide_short_close(self, order, tickers, Account, exog):
        return False


class EqualWeight(RiskManagement):
    def _order_size(self, Account, exog=None, n=None, price=None):
        if Account.n_active_orders == 0:
            self.investable_capital = Account.balance

        return np.floor(self.investable_capital / (n * price)).astype(int)


if __name__ == "__main__":
    path = "../data/market/"

    stocks = []
    for symbol in os.listdir(path):
        print(symbol)
        tmp = pd.read_csv(os.path.join(path, symbol), parse_dates=True)[
            ["Adj Close", "Date"]
        ]
        tmp.columns = ["close", "timestamp"]
        tmp["timestamp"] = pd.to_datetime(tmp["timestamp"])
        tmp = tmp.dropna(how="any", axis=0)
        if tmp.shape[0] > 252 * 9:
            stocks.append(Stock(price=tmp.values, base=symbol.strip(".csv")))

    # initialize an account with 1M USD balance
    account = Account()

    # set equal weights for all stocks
    risk_man = EqualWeight()

    # initialize the strategy
    strategy = CustomAllocation(
        RiskManagement=risk_man, name="momentum_factor"
    )

    # allow strategy to use all assets
    for stock in stocks:
        strategy = stock.register(strategy)

    sim = BackTest(Account=account, Strategy=strategy).run(stocks)
    sim.Strategy.save("momentum.strt")
    print(sim.Account.balances)