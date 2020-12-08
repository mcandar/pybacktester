from datetime import datetime as dt
from uuid import uuid4
from strategy_tester.utils import error_logger, transaction_logger

error_log = error_logger()
transaction_log = transaction_logger()


class Order:
    """Keep track of an order, set TP, SL levels and store history. One can
    use this class to act on it."""

    def __init__(
        self,
        asset_id,
        position,
        type,
        size,
        strike_price,
        timestamp,
        asset_features,
        spread=0.00010,
        leverage=100,
        stop_loss=None,
        take_profit=None,
        trailing_stop_loss=None,
        trailing_take_profit=None,
        strategy_id=None,
        strategy_name=None,
        round_digits=2,
        expiration_date=None,
        slippage=0,
    ):
        if type.lower() not in ["market", "pending"]:
            message = "Argument `type` must be either `market` or `pending`."
            error_log.error(message)
            raise ValueError(message)

        self.asset_id = asset_id
        self.position = position
        self.type = type
        self.size = size
        self.strike_price = strike_price - slippage
        self.slippage = slippage
        self.spread = spread
        self.leverage = leverage
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.trailing_stop_loss = trailing_stop_loss
        self.strategy_id = strategy_id
        self.strategy_name = strategy_name
        self.round_digits = round_digits
        self.expiration_date = expiration_date

        self.asset_features = asset_features

        self.is_active = True
        self.is_open = self.type != "pending"
        self.profit = -spread * size
        self.profits = [self.profit]
        self.margin = (
            strike_price * size * self.asset_features["lot_units"]
        ) / leverage
        self.margins = [self.margin]
        self.pips = 0
        self.pipss = [self.pips]
        self.id = uuid4()

        t = dt.utcnow()
        self.time = {
            "activated": t,
            "opened": t if self.type != "pending" else None,
            "closed": None,
        }
        self.time_ticker = {
            "activated": timestamp,
            "opened": timestamp if self.type != "pending" else timestamp,
            "closed": None,
        }

    def close(self, timestamp):
        "Use after update."
        self.is_active, self.is_open = False, False
        self.time["closed"] = dt.utcnow()
        self.time_ticker["closed"] = timestamp
        return self

    def check_pending_open(self, spot_price, timestamp):
        "Open a waiting (active) pending order."
        if self.is_active and not self.is_open:
            d = self.strike_price - spot_price
            if (self.position == "long" and d <= 0) or (
                self.position == "short" and d >= 0
            ):
                self.is_open = True
                self.time["opened"] = dt.utcnow()
                self.time_ticker["opened"] = timestamp
                transaction_log.transaction("Open a pending (active) order.")
                return True
        return False

    def check_close(self, ticker):
        "Runs at each tick."
        if self.is_active:
            if (
                self.expiration_date is not None
                and self.expiration_date <= ticker.timestamp
            ):
                self.close(ticker.timestamp)
            if self.is_open:
                if (
                    self.take_profit is not None
                    and self.pips >= self.take_profit
                ):
                    self.close(ticker.timestamp)
                elif (
                    self.stop_loss is not None and self.pips <= -self.stop_loss
                ):
                    self.close(ticker.timestamp)
                if self.trailing_stop_loss is not None:
                    self.stop_loss -= (
                        self.pips + self.stop_loss - self.trailing_stop_loss
                    )
        return self

    def __append_history(self, pips, profit, margin):
        self.pipss.append(pips)
        self.profits.append(profit)
        self.margins.append(margin)
        return self

    def __update_basics(self, ticker):
        pips = (
            ticker.price - self.strike_price
            if self.position == "long"
            else self.strike_price - ticker.price
        )
        profit = self.pips * self.size * self.asset_features["lot_units"]
        margin = (
            ticker.price * self.size * self.asset_features["lot_units"]
        )  # <------------- TODO: convert to USD
        return pips, profit, margin

    def update(self, ticker):
        "Runs at each tick. Processes just one tick."
        if self.is_active and self.is_open:
            self.pips, self.profit, self.margin = self.__update_basics(ticker)
            self.__append_history(self.pips, self.profit, self.margin)
            self.check_close(ticker)
            return True
        elif self.is_active and not self.is_open:
            return self.check_pending_open(ticker)
        else:
            error_log.error("Cannot update an expired order.")
            raise ValueError(
                "Cannot update an expired order."
            )  # <-------- TODO: check if this is the correct error type
