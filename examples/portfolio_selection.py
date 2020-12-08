import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "../")

from strategy_tester.account import Account
from strategy_tester.asset import Stock
from strategy_tester.strategy import Strategy
from strategy_tester.risk_management import ConstantRate
from strategy_tester.simulate import BackTest
from strategy_tester.utils import generate_data


class CustomAllocation(Strategy):
    def __init__(self, n=20, n_samples=21, max_stocks=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.n = n
        self.n_samples = n_samples
        self.max_stocks = max_stocks

        self.n_stocks = 0
        self.past_data = []
        self.last_selected = None
        self.last_t = 0

    def momentum_factor(self, past_data, n):
        """
        Choose top-n stocks out of the universe based on 1 month's momentum.
        """
        return (
            pd.DataFrame(past_data)
            .pct_change()
            .mean()
            .sort_values(ascending=False)
            .head(n)
            .index
        )

    def decide_long_open(self, tickers, Account, exog):
        output = {}
        t = tickers[0].timestamp
        if t.hour != 0 and t.minute != 0:  # run once a day at 00:00
            return None

        self.past_data.append(tickers.to_dict())

        # wait for sufficient number of samples
        if len(self.past_data) < self.n_samples:
            return None

        # choose best performing n stocks so far
        selected_ids = self.momentum_factor(self.past_data, self.n)
        selected_ids = frozenset(selected_ids)

        # for each stock this strategy is registered to work on
        for asset_id in self.on:
            # if that stock is in the received list of prices and selected for buying
            if asset_id in selected_ids:
                if self.n_stocks < self.max_stocks:
                    price = spot_price[asset_id]
                    # decide order parameters
                    args = {
                        "type": "market",
                        "size": self.RiskManagement.order_size(
                            Account, n=self.max_stocks
                        ),
                        "strike_price": price,
                    }
                    output[asset_id] = args
                    self.n_stocks += 1
        # store currently selected stocks for later comparison
        self.last_selected = selected_ids
        # remove first item (roll on a constant size)
        del self.past_data[0]

        return output

    def decide_short_open(self, tickers, Account, exog):
        "No short sells."
        return None

    def decide_long_close(self, order, tickers, Account, exog):
        t = tickers[0].timestamp
        if t.hour == 0 and t.minute == 0:
            pass

    #    def decide_long_close(self, order, tickers, Account, exog):
    #        t = tickers[0].timestamp
    #        if self.last_t != t:
    #            self.last_t = t
    #            if t.hour == 0 and t.minute == 0:
    #                self.past_data.append([ticker.price for ticker in tickers])
    #                if len(self.past_data) < self.n_samples:
    #                    return False
    #                else:
    #                    selected = self.filter_stocks(
    #                        self.past_data, self.n
    #                    )  # selected for long (that we would have selected for buying)
    #
    #                    self.selected_to_close = []
    #                    for (
    #                        stock
    #                    ) in (
    #                        self.last_selected.index
    #                    ):  # for each last chosen stocks
    #                        if stock not in selected.index:
    #                            self.selected_to_close.append(stock)
    #                    del self.past_data[0]
    #                    return (
    #                        order.asset_id in self.selected_to_close
    #                    )  # close if the order is selected for close
    #            else:
    #                return False
    #        else:
    #            return (
    #                order.asset_id in self.selected_to_close
    #            )  # close if the order is selected for close

    def decide_short_close(self, order, tickers, Account, exog):
        return False


stocks = [
    Stock(
        price=generate_data(5000, freq="B"),
        base=f"STCK_{i}",
        # short_name=f"STCK_{i}",
    )
    for i in range(500)
]  # randomly generate stock prices
account = Account()  # initialize an account with 1000 USD balance
risk_man = ConstantRate(0.05)  # constant lot size with 5% of balance each time

strategy = CustomAllocation(
    RiskManagement=risk_man, id=45450, name="custom_buyer"
)
for stock in stocks:
    strategy = stock.register(
        strategy
    )  # allow strategy to use all of them, either one or multiple

sim = BackTest(Account=account, Strategy=strategy).run(stocks)
print(sim.Account.balances)