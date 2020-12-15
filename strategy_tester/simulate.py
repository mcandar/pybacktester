from datetime import datetime as dt
import logging
import numpy as np
from progressbar import ProgressBar
from strategy_tester.order import Order
from strategy_tester.utils import error_logger, transaction_logger

# TODO: implement dynamic slippage and spread (Slippage modeling and market impact models)
# TODO: Make also time-driven
# TODO: Enable parallel computation
# TODO: datetime index, and datetime grouped data?

error_log = error_logger()
transaction_log = transaction_logger()


def ensure_type_strategy(x):
    if isinstance(x, (list, tuple)) and len(x) > 0:
        return {strategy.id: strategy for strategy in x}
    else:
        return {x.id: x}


class BackTest:
    """
    Perform simulations on past data. After creating trading strategies, test
    them on one or more financial assets on an account.

    Parameters
    ----------
    Account : an instance of Account Class
        Configured Account object to simulate a trading account.
    Strategy : an instance of Strategy Class
        Designed trading strategy to backtest. This could be an instance
        of any class that inherits Strategy.
    track : tuple of callable
        A series of functions to calculate performance metrics. If None,
        nothing is calculated. All functions specified to this parameter
        must take `Account` as an argument and return a value.
    """

    def __init__(
        self,
        Account,
        Strategy,
        spread=0.0002,
        slippage=0,
        track=None,
        track_freq=100,
    ):
        #        if isinstance(Strategy, (list, tuple)) and len(Strategy) > 0:
        #            self.__Strategies = {
        #                strategy.id: strategy for strategy in Strategy
        #            }
        #        else:
        #            self.__Strategies = {Strategy.id: Strategy}
        self.__Strategies = ensure_type_strategy(Strategy)

        if track is not None:
            if not isinstance(track, (list, tuple)):
                message = "Argument `track` is not iterable."
                error_log.error(message)
                raise ValueError(message)
            else:
                for fun in track:
                    if not callable(fun):
                        message = "An element of `track` is not callable."
                        error_log.error(message)
                        raise ValueError(message)

        self.Account = Account
        self.Strategy = Strategy
        self.spread = spread
        self.track = track
        self.track_freq = track_freq
        self.tracked_results = []
        error_log.info("Simulation is initialized.")

    def __check_long_open(self, tickers, Strategy, exog=None):
        args = Strategy.long_open(
            tickers=tickers,
            Account=self.Account,
            exog=exog,
        )
        timestamp = tickers[0].timestamp

        error_log.debug("Checked long order conditions.")
        if args is not None and len(args) > 0:
            orders = []
            for asset_id, arg in args.items():
                orders.append(
                    Order(
                        asset_id=asset_id,
                        position="long",
                        timestamp=timestamp,
                        asset_features=self.asset_features[asset_id],
                        leverage=self.Account.leverage,
                        **arg,
                    )
                )
            self.Account.place_order(orders=orders, timestamp=timestamp)
            error_log.info("Placed long orders.")
        return self

    def __check_short_open(self, tickers, Strategy, exog=None):
        args = Strategy.short_open(
            tickers=tickers,
            Account=self.Account,
            exog=exog,
        )
        timestamp = tickers[0].timestamp

        error_log.debug("Checked short order conditions.")
        if args is not None and len(args) > 0:
            orders = []
            for asset_id, arg in args.items():
                orders.append(
                    Order(
                        asset_id=asset_id,
                        position="short",
                        timestamp=timestamp,
                        spread=self.spread,
                        asset_features=self.asset_features[asset_id],
                        leverage=self.Account.leverage,
                        **arg,
                    )
                )
            self.Account.place_order(orders=orders, timestamp=timestamp)
            error_log.info("Placed short orders.")
        return self

    def check_order_open(self, *args, **kwargs):
        return self.__check_long_open(*args, **kwargs).__check_short_open(
            *args, **kwargs
        )

    def check_order_close(self, order, tickers, Strategy, exog=None):
        if order.position == "long":
            output = Strategy.long_close(
                order=order,
                tickers=tickers,
                Account=self.Account,
                exog=exog,
            )
            error_log.info("Checked long order close conditions.")
            return output
        elif order.position == "short":
            output = Strategy.short_close(
                order=order,
                tickers=tickers,
                Account=self.Account,
                exog=exog,
            )
            error_log.info("Checked short order close conditions.")
            return output

    def order_modify(self, order, Strategy, tickers, Account, exog=None):
        if order.position == "long":
            output = Strategy.long_modify(
                order=order, tickers=tickers, Account=Account, exog=exog
            )
        elif order.position == "short":
            output = Strategy.short_modify(
                order=order, tickers=tickers, Account=Account, exog=exog
            )
        else:
            raise AttributeError(f"Unknown poisition type {order.position}.")
        error_log.debug(f"Modified {order.position} order.")
        return output

    def initial_checks(self, assets):
        lengths = []
        for asset in assets:
            lengths.append(asset.data.shape[0])
            if not isinstance(asset.data[0, 1], (int, float)):
                message = f"Second column of data must be price series, error received on {asset.id}"
                error_log.error(message)
                raise ValueError(message)

        lengths = np.array(lengths)
        if np.any(lengths[0] != lengths):
            message = "Time series data lengths must match."
            error_log.error(message)
            raise ValueError(message)

        for s in self.__Strategies.values():
            s.check_registered_assets()

        self.num_assets = len(assets)
        self.assets_keymap = {
            key: val for val, key in enumerate(map(lambda x: x.id, assets))
        }
        error_log.info("Initial checks are completed.")

    def process_ticker(self, tickers, x):
        self.Account.update(tickers=tickers)

        order_ids = self.Account.active_orders.keys()
        if self.Account.n_active_orders > 0:
            order_close_ids = []
            for oid in order_ids:
                tmp_order = self.Account.active_orders[oid]
                tmp_strategy = self.__Strategies[tmp_order.strategy_id]

                self.Account.active_orders[oid] = self.order_modify(
                    order=tmp_order,
                    Strategy=tmp_strategy,
                    tickers=tickers,
                    Account=self.Account,
                    exog=x,
                )

                if self.check_order_close(
                    order=tmp_order,
                    tickers=tickers,
                    Strategy=tmp_strategy,
                    exog=x,
                ):
                    order_close_ids.append(oid)

            if len(order_close_ids) > 0:
                self.Account.close_all_orders(
                    ids=order_close_ids, timestamp=tickers[0].timestamp
                )

        for Strategy in self.__Strategies.values():
            self.check_order_open(
                Strategy=Strategy,
                tickers=tickers,
                exog=x,
            )
        return self

    def track_values(self, t):
        output = [t]
        output.extend([fun(self.Account) for fun in self.track])
        self.tracked_results.append(tuple(output))
        error_log.debug(
            "Calculation is completed for the metrics specified for tracking."
        )
        return True

    def run(self, assets, exog=None):
        error_log.info("Simulation run is started.")
        run_start_timestamp = dt.utcnow()

        # ensure type
        assets = assets if isinstance(assets, (list, tuple)) else [assets]

        # self.initial_checks(assets)
        error_log.info("Initial checks are passed.")
        self.asset_features = {asset.id: asset.features() for asset in assets}

        data = zip(*[asset.data() for asset in assets])
        size = len(assets[0].data())
        exog = np.repeat(None, size) if exog is None else exog

        error_log.info("Starting main loop of simulation.")

        bar = ProgressBar(maxval=size).start()
        for _i, (tickers, X) in enumerate(zip(data, exog)):
            t = tickers[0].timestamp

            if self.Account.is_blown:
                transaction_log.critical("No remaining balance.")
                break

            self.process_ticker(tickers, X)
            if _i % self.track_freq == 0:
                if self.track is not None:
                    self.track_values(t)

            bar.update(_i)

        # TODO: find an efficient way
        self.Account.tear_down(
            first_timestamp=assets[0].data()[0].timestamp,
            last_timestamp=assets[0].data()[-1].timestamp,
            run_start=run_start_timestamp,
        )
        error_log.info("Tear down performed for Account.")
        if self.track is not None:
            self.track_values(t)
        bar.finish()
        return self

    def update_strategy(self, Strategy):
        self.__Strategies = ensure_type_strategy(Strategy)
        return self

    def update_account(self, Account):
        self.Account = Account
        return self


class ForwardTest:
    def __init__(self):
        pass