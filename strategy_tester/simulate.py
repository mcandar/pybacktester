import numpy as np
from progressbar import ProgressBar
from strategy_tester.order import Order

# TO DO: Make also time-driven
# TO DO: Enable parallel computation
# TO DO: bring oninit and ondeinit back to life later
# TO DO: logging for transactions
# TO DO: logging for exceptions
# TO DO: PLOT and Visualizations
# TO DO: calculate sharpe ratio, ROI, etc.
class BackTest:
    "Main class to use all components for backtesting."
    def __init__(self,Account,Strategy,spread=0.0002,slippage=0,oninit=None,
                 ondeinit=None,preprocess=None,postprocess=None):
        self.Account = Account
        self.Strategy = Strategy
        if isinstance(Strategy,(list,tuple)) and len(Strategy) > 0:
            self.__Strategies = {strategy.id:strategy for strategy in Strategy}
        else:
            self.__Strategies = {Strategy.id:Strategy}
        self.spread = spread
        self.oninit = oninit
        self.ondeinit = ondeinit
    
    def check_order_open(self,spot_price,timestamp,Strategy,exog=None):
        open_long, kwargs_long = Strategy.long_open(spot_price=spot_price,
                                                    timestamp=timestamp,
                                                    Account=self.Account,
                                                    exog=exog)
        open_short, kwargs_short = Strategy.short_open(spot_price=spot_price,
                                                       timestamp=timestamp,
                                                       Account=self.Account,
                                                       exog=exog)
        
        if open_long:
            order = Order(position='long',timestamp=timestamp,spread=self.spread,**kwargs_long)
            self.Account.place_order(order)
        elif open_short:
            order = Order(position='short',timestamp=timestamp,spread=self.spread,**kwargs_short)
            self.Account.place_order(order)
        return self
    
    def check_order_close(self,order,spot_price,Strategy,exog=None):
        if order.position == 'long':
            return Strategy.long_close(order=order,
                                       spot_price=spot_price,
                                       Account=self.Account,
                                       exog=exog)
        elif order.position == 'short':
            return Strategy.short_close(order=order,
                                        spot_price=spot_price,
                                        Account=self.Account,
                                        exog=exog)
    
    def order_modify(self,order,Strategy,spot_price,Account,exog=None):
        if order.position == 'long':
            return Strategy.long_modify(order=order,spot_price=spot_price,Account=Account,exog=exog)
        elif order.position == 'short':
            return Strategy.short_modify(order=order,spot_price=spot_price,Account=Account,exog=exog)

    def run(self,data,exog=None):
        if not isinstance(data[0,1],(int,float)):
            raise ValueError('Second column of data must be price series.')
        exog = np.repeat(None,data.shape[0]) if exog is None else exog
        _i = 0
        bar = ProgressBar(maxval = data.shape[0]).start()
        for ticker,x in zip(data,exog):
            if self.Account.is_blown:
                print('No remaining balance.')
                break

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
                                              Strategy=tmp_strategy,
                                              exog=x):
                        order_close_ids.append(id)
                
                self.Account.close_all_orders(order_close_ids)
            for Strategy in self.__Strategies.values():
                self.check_order_open(spot_price=ticker[1],
                                      timestamp=ticker[0],
                                      Strategy=Strategy,
                                      exog=x)
            _i += 1
            bar.update(_i)
        bar.finish()
        return self


class ForwardTest:
    def __init__(self):
        pass