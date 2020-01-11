from datetime import datetime as dt
import numpy as np
from progressbar import ProgressBar
from strategy_tester.order import Order

# TODO: Make also time-driven
# TODO: Enable parallel computation
# TODO: Enable tracking functions, (calculate sharpe ratio, ROI, etc.)
# TODO: logging for transactions
# TODO: logging for exceptions
# TODO: PLOT and Visualizations
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
    """
    def __init__(self,Account,Strategy,spread=0.0002,slippage=0,track=None):
        self.Account = Account
        self.Strategy = Strategy
        if isinstance(Strategy,(list,tuple)) and len(Strategy) > 0:
            self.__Strategies = {strategy.id:strategy for strategy in Strategy}
        else:
            self.__Strategies = {Strategy.id:Strategy}
        self.spread = spread

        if track is not None:
            if not isinstance(track,(list,tuple)):
                raise ValueError('Argument `track` is not iterable.')
            else:
                for fun in track:
                    if not callable(fun):
                        raise ValueError('An element of `track` is not callable.')
        self.track = track
        self.tracked_results = ()
    
    def __check_long_open(self,spot_price,timestamp,Strategy,exog=None):
        args = Strategy.long_open(spot_price=spot_price,
                                    timestamp=timestamp,
                                    Account=self.Account,
                                    exog=exog)

        if args is not None:
            orders = [Order(asset_id=asset_id,position='long',timestamp=timestamp,spread=self.spread,**arg) for asset_id, arg in args.items()]
            self.Account.place_order(orders=orders,timestamp=timestamp)
        return self
            
    def __check_short_open(self,spot_price,timestamp,Strategy,exog=None):
        args = Strategy.short_open(spot_price=spot_price,
                                    timestamp=timestamp,
                                    Account=self.Account,
                                    exog=exog)
        
        if args is not None:
            orders = [Order(asset_id=asset_id,position='short',timestamp=timestamp,spread=self.spread,**arg) for asset_id, arg in args.items()]
            self.Account.place_order(orders=orders,timestamp=timestamp)
        return self

    def check_order_open(self,*args,**kwargs):
        return self.__check_long_open(*args,**kwargs).__check_short_open(*args,**kwargs)
    
    def check_order_close(self,order,spot_price,timestamp,Strategy,exog=None):
        if order.position == 'long':
            return Strategy.long_close(order=order,
                                       spot_price=spot_price,
                                       timestamp=timestamp,
                                       Account=self.Account,
                                       exog=exog)
        elif order.position == 'short':
            return Strategy.short_close(order=order,
                                        spot_price=spot_price,
                                        timestamp=timestamp,
                                        Account=self.Account,
                                        exog=exog)
    
    def order_modify(self,order,Strategy,spot_price,Account,exog=None):
        if order.position == 'long':
            return Strategy.long_modify(order=order,spot_price=spot_price,Account=Account,exog=exog)
        elif order.position == 'short':
            return Strategy.short_modify(order=order,spot_price=spot_price,Account=Account,exog=exog)
    
    def initial_checks(self,assets):
        lengths = []
        for asset in assets:
            lengths.append(asset.data.shape[0])
            if not isinstance(asset.data[0,1],(int,float)):
                raise ValueError(f'Second column of data must be price series, error received on {asset.id}')

        lengths = np.array(lengths)
        if np.any(lengths[0] != lengths):
            raise ValueError('Time series data lengths must match.')
        
        for s in self.__Strategies.values():
            s.check_registered_assets()
        
        self.num_assets = len(assets)
        self.assets_keymap = {key:val for val,key in enumerate(map(lambda x: x.id,assets))}
    
    # TODO: convert this to a warning
    def check_intersection(self,data,ts,exog):
        if self.Account.time_ticker[0]['end'] is not None:
            for time_ticker in self.Account.time_ticker:
                if np.any((time_ticker['end'] > ts) | (time_ticker['start'] < ts)):
                    idx = (ts > time_ticker['end']) | (ts < time_ticker['start'])
                    data = data[idx]
                    ts = ts[idx]
                    exog = exog[idx]
                    print('Skipping overlapping data.')
        return data,ts,exog

    def __process_ticker(self,ticker,x):
        self.Account.update(spot_price=ticker[1],timestamp=ticker[0])

        order_ids = self.Account.active_orders.keys()
        if self.Account.n_active_orders > 0:
            order_close_ids = []
            for id in order_ids:
                tmp_order = self.Account.active_orders[id]
                tmp_strategy = self.__Strategies[tmp_order.strategy_id]
                self.Account.active_orders[id] = self.order_modify(order=tmp_order,
                                                                    Strategy=tmp_strategy,
                                                                    spot_price=ticker[1],
                                                                    Account=self.Account,
                                                                    exog=x)

                if self.check_order_close(order=tmp_order,
                                            spot_price=ticker[1],
                                            timestamp=ticker[0],
                                            Strategy=tmp_strategy,
                                            exog=x):
                    order_close_ids.append(id)
            
            self.Account.close_all_orders(ids=order_close_ids,timestamp=ticker[0])

        for Strategy in self.__Strategies.values():
            self.check_order_open(spot_price=ticker[1],
                                    timestamp=ticker[0],
                                    Strategy=Strategy,
                                    exog=x)
        return self

    def run(self,assets,exog=None):
        run_start_timestamp = dt.utcnow()
        assets = assets if isinstance(assets,(list,tuple)) else [assets]
        self.initial_checks(assets)

        data = np.array([asset.data[:,1] for asset in assets]).T
        ts = assets[0].data[:,0]
        exog = np.repeat(None,data.shape[0]) if exog is None else exog

        data,ts,exog = self.check_intersection(data,ts,exog)

        _i = 0
        bar = ProgressBar(maxval = data.shape[0]).start()
        for t,d,x in zip(ts.tolist(),data.tolist(),exog):
            ticker = (t,dict(zip(self.assets_keymap.keys(),d)))
            if self.Account.is_blown:
                print('No remaining balance.')
                break
            self.__process_ticker(ticker,x)
            _i += 1
            bar.update(_i)
        self.Account.tear_down(first_timestamp=np.min(ts),last_timestamp=np.max(ts),run_start=run_start_timestamp)
        bar.finish()
        return self


class ForwardTest:
    def __init__(self):
        pass