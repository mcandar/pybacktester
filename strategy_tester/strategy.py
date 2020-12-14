import numpy as np
from uuid import uuid4
import pickle

# TODO: create several built-in strategies
# TODO: use a decorator to simplify methods?
# TODO: SIMPLIFY (for ease of use)
class Strategy:
    """
    Base strategy class.

    Open, modify, and close orders. By modification, we could keep a
    number of variables, in order to track its performance and make decisions.

    """

    def __init__(self, RiskManagement, id=None, name=None):
        self.RiskManagement = RiskManagement
        self.id = uuid4()
        self.name = name
        self.on = []

    def check_registered_assets(self):
        if len(self.on) == 0:
            raise AttributeError(
                "No asset is registered. Set target instrument(s) to use this strategy."
            )

    def include_identifiers(self, args):
        assets = args.keys()
        for asset_id in assets:
            args[asset_id]["strategy_id"] = self.id
            args[asset_id]["strategy_name"] = self.name
        return args

    def random_decision(self, p=0.01):
        "Bernoulli Process with success rate p."
        return np.random.uniform(0, 1, 1)[0] < p

    def preprocess(self, tickers, Account, RiskManagement, exog):
        "Preprocess exogenous variables."
        return exog

    def postprocess(self, args):
        "Last checks and corrections."
        if args is not None:
            args = self.include_identifiers(args)
        return args

    def long_open(self, tickers, Account, exog=None):
        exog = self.preprocess(tickers, Account, self.RiskManagement, exog)
        args = self.decide_long_open(
            tickers=tickers,
            Account=Account,
            exog=exog,
        )
        return self.postprocess(args)

    def short_open(self, tickers, Account, exog=None):
        exog = self.preprocess(tickers, Account, self.RiskManagement, exog)
        args = self.decide_short_open(
            tickers=tickers,
            Account=Account,
            exog=exog,
        )
        return self.postprocess(args)

    def long_modify(self, order, tickers, Account, exog=None):
        "Set attributes, and check order's state to track the performance."
        return order

    def short_modify(self, order, tickers, Account, exog=None):
        return order

    def long_close(self, order, tickers, Account, exog=None):
        if order.position != "long":
            AttributeError(
                f"Position is expected to be long, got {order.position}"
            )
        exog = self.preprocess(tickers, Account, self.RiskManagement, exog)
        return self.decide_long_close(
            order=order,
            tickers=tickers,
            Account=Account,
            exog=exog,
        )

    def short_close(self, order, tickers, Account, exog=None):
        if order.position != "short":
            AttributeError(
                f"Position is expected to be short, got {order.position}"
            )
        exog = self.preprocess(tickers, Account, self.RiskManagement, exog)
        return self.decide_short_close(
            order=order,
            tickers=tickers,
            Account=Account,
            exog=exog,
        )

    def decide_long_open(self, tickers, Account, exog):
        output = {}
        for ticker in tickers:
            if ticker.aid in self.on:
                if self.random_decision():
                    arg = {
                        "type": "market",
                        "size": self.RiskManagement.order_size(Account),
                        "strike_price": ticker.price,
                        "stop_loss": 0.01,
                        "take_profit": 0.01,
                    }
                    output[ticker.aid] = arg
        return output

    def decide_short_open(self, tickers, Account, exog):
        output = {}
        for ticker in tickers:
            if ticker.aid in self.on:
                if self.random_decision():
                    arg = {
                        "type": "market",
                        "size": self.RiskManagement.order_size(Account),
                        "strike_price": ticker.price,
                        "stop_loss": 0.01,
                        "take_profit": 0.01,
                    }
                    output[ticker.aid] = arg
        return output

    def decide_long_close(self, order, tickers, Account, exog):
        # return self.random_decision()
        return False

    def decide_short_close(self, order, tickers, Account, exog):
        # return self.random_decision()
        return False

    def save(self, filename):
        with open(filename, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filename):
        with open(filename, "rb") as f:
            return pickle.load(f)


class MACross(Strategy):
    def decide_long_open(self, spot_price, timestamp, Account, exog):
        "Exog[0]: Slow MA, Exog[1]: Fast MA"
        output = {}
        for asset_id in self.on:
            if asset_id in spot_price.keys():
                args = {
                    "type": "market",
                    "size": self.RiskManagement.order_size(Account),
                    "strike_price": spot_price[asset_id],
                    "stop_loss": None,
                    "take_profit": None,
                }
                output[
                    asset_id
                ] = args  # {'decision':exog[0] > exog[1],'params':args}
        return output

    def decide_short_open(self, spot_price, timestamp, Account, exog):
        "Exog[0]: Slow MA, Exog[1]: Fast MA"
        output = {}
        for asset_id in self.on:
            if asset_id in spot_price.keys():
                args = {
                    "type": "market",
                    "size": self.RiskManagement.order_size(Account),
                    "strike_price": spot_price[asset_id],
                    "stop_loss": None,
                    "take_profit": None,
                }
                output[
                    asset_id
                ] = args  # {'decision':exog[0] < exog[1],'params':args}
        return output

    def decide_long_close(self, order, spot_price, timestamp, Account, exog):
        return exog[0] < exog[1]

    def decide_short_close(self, order, spot_price, timestamp, Account, exog):
        return exog[0] > exog[1]