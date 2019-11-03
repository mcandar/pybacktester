from datetime import datetime as dt
#from functools import wraps
from progressbar import ProgressBar

import numpy as np
import pandas as pd
# Assume account is USD
# Assume trading on EURUSD

# TO DO: error logging

# class Currency:
#     def __init__(self,data,base,quote,spread=0,commissions=0,lot_units=1000):
#         self.data = data
#         self.base = base
#         self.quote = quote
    
# class EURUSD(Currency):
#     def __init__(self,*args,**kwargs):
#         super().__init__(base='EUR',quote='USD',*args,**kwargs)

# TO DO: write a summary() method
# TO DO: write a plot() method
class Order:
    """Order object for keeping track of an order, setting TP, SL levels and store history. One can
    use this class to act on it."""
    def __init__(self,position,type,size,strike_price,timestamp,spread=0.00010,leverage=100,
                 stop_loss=None,take_profit=None,trailing_stop_loss=None,
                 trailing_take_profit=None,strategy_id=None,strategy_name=None):
        if type.lower() not in ['market','pending']:
            raise ValueError('Argument `type` must be either `market` or `pending`.')
        
        self.position = position
        self.type = type
        self.size = size
        self.strike_price = strike_price
        self.spread = spread
        self.leverage = leverage
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.trailing_stop_loss = trailing_stop_loss
        self.strategy_id = strategy_id
        self.strategy_name = strategy_name

        self.is_active = True
        self.is_open = self.type != 'pending'
        self.profit = -spread*size
        self.profits = [self.profit]
        self.margin = strike_price*size*1000
        self.margins = [self.margin]
        self.pips = 0
        self.pipss = [self.pips]

        t = dt.utcnow()
        self.time = {'activated':t,
                     'opened':t if self.type != 'pending' else None,
                     'closed':None}
        self.time_ticker = {'activated':timestamp,
                            'opened':timestamp if self.type != 'pending' else timestamp,
                            'closed':None}
    
    def close(self,timestamp):
        "Use after update."
        self.is_active, self.is_open = False, False
        self.time['closed'] = dt.utcnow()
        self.time_ticker['closed'] = timestamp
        return self
    
    def check_pending_open(self,spot_price,timestamp,slippage=0):
        "Open a pending order."
        if self.is_active and not self.is_open:
            d = self.strike_price - spot_price
            if (self.position == 'long' and d <= 0) or (self.position == 'short' and d >= 0):
                self.is_open = True
                self.time['opened'] = dt.utcnow()
                self.time_ticker['opened'] = timestamp

    def check_close(self,spot_price,timestamp):
        "Runs at each tick."
        if self.is_active and self.is_open:
            if self.take_profit is not None and self.pips >= self.take_profit:
                self.close(timestamp)
            elif self.stop_loss is not None and self.pips <= -self.stop_loss:
                self.close(timestamp)
            if self.trailing_stop_loss is not None:
                self.stop_loss -= self.pips + self.stop_loss - self.trailing_stop_loss
        return self
    
    def __append_history(self,pips,profit,margin):
        self.pipss.append(pips)
        self.profits.append(profit)
        self.margins.append(margin)
        return self
    
    def __update_basics(self,spot_price):
        pips = spot_price-self.strike_price if self.position == 'long' else self.strike_price-spot_price
        profit = self.pips*self.size*1000*self.leverage
        margin = spot_price*self.size*1000 + self.profit
        return pips, profit, margin
    
    def update(self,spot_price,timestamp):
        "Use at each tick."
        if self.is_active and self.is_open:
            self.pips, self.profit, self.margin = self.__update_basics(spot_price)
            self.__append_history(self.pips,self.profit,self.margin)
            self.check_close(spot_price,timestamp)
            return True
        elif self.is_active and not self.is_open:
            self.check_pending_open(spot_price,timestamp)
            return True
        else:
            print('Cannot update an expired order.')
            return False
        
    
# TO DO: add balance currency
# TO DO: add max number of open orders
# TO DO: add max allocated margin (or min free margin)
class Account:
    def __init__(self,balance=1000,leverage=100,margin_call_level=0.3,name=None,id=None):
        self.__initial_balance = balance
        self.balance = balance
        self.free_margin = balance
        self.leverage = leverage
        self.margin_call_level = margin_call_level # TO DO: check margin call calculation later
        self.__name = name
        self.__id = id
        self.equity = 0
        self.is_blown = False

        self.__i = 0
        self.active_orders = {}
        self.inactive_orders = {}
        self.n_active_orders = 0
        self.n_inactive_orders = 0

        self.balances = [self.balance]
        self.free_margins = [self.free_margin]
        self.equities = [self.equity]
    
    @property
    def initial_balance(self):
        return self.__initial_balance
    
    @property
    def name(self):
        return self.__name
    
    @property
    def id(self):
        return self.__id
    
    def place_order(self,order):
        if self.free_margin >= order.margin:
            self.free_margin -= order.margin
        else:
            return self # Cannot place order due to insufficient free margin.

        self.active_orders[f'order_{self.__i}'] = order
        self.__i += 1
        self.equity += order.margin

        self.n_active_orders += 1
        self.free_margins.append(self.free_margin)
        self.equities.append(self.equity)
        return self
    
    def close_order(self,id,timestamp):
        tmp_order = self.active_orders[id].close(timestamp)
        del self.active_orders[id]
        self.inactive_orders[id] = tmp_order

        self.free_margin += tmp_order.margin
        self.equity -= tmp_order.margin
        self.balance += tmp_order.profit

        self.n_active_orders -= 1
        self.n_inactive_orders += 1
        self.free_margins.append(self.free_margin)
        self.equities.append(self.equity)
        self.balances.append(self.balance)
        return self
    
    def close_all_orders(self,timestamp,ids=None):
        ids = list(self.active_orders.keys()) if ids is None else ids
        for id in ids:
            self.close_order(id=id,timestamp=timestamp)
    
    def check_margin_call(self,timestamp):
        if self.free_margin+self.equity <= self.margin_call_level*self.initial_balance:
            self.close_all_orders(timestamp=timestamp)
        return self
    
    def __update_or_close(self,spot_price,timestamp):
        order_close_ids = []
        for id,order in self.active_orders.items():
            order.update(spot_price,timestamp)
            if not order.is_active and not order.is_open: # closed due to TP, SL
                order_close_ids.append(id)
            elif order.is_active and order.is_open:
                self.equity -= order.margin
                self.equities.append(self.equity)
        
        self.close_all_orders(timestamp=timestamp,ids=order_close_ids)
        return self
    
    def update(self,spot_price,timestamp):
        "Use at each tick."
        self.is_blown = self.balance <= 0

        if not self.is_blown:
            if self.n_active_orders > 0:
                self.check_margin_call(timestamp).__update_or_close(spot_price,timestamp)

        return self
        
# TO DO: use a decorator to simplify methods?
class Strategy:
    """Open, modify, and close orders. By modification, we could keep a 
    number of variables, in order to track its performance and make decisions."""
    def __init__(self,RiskManagement,id=None,name=None):
        self.RiskManagement = RiskManagement
        self.id = id
        self.name = name
    
    def __include_identifiers(self,args):
        args['strategy_id'] = self.id
        args['strategy_name'] = self.name
        return args
    
    def __random_decision(self,p=0.01):
        return np.random.uniform(0,1,1)[0] < p
    
    # TO DO: bring preprocessing back to life
    def preprocess(self,spot_price,timestamp,Account,RiskManagement,exog=None):
        return exog
    
    def postprocess(self,decision,args):
        "Last checks and corrections."
        args = self.__include_identifiers(args)
        return decision, args

    def __long_open(self,spot_price,timestamp,Account,exog=None):
        args = {
        'type':'market',
        'size':self.RiskManagement.order_size(Account),
        'strike_price':spot_price,
        'stop_loss':0.001,
        'take_profit':0.001
        }
        return self.__random_decision(), args

    def __short_open(self,spot_price,timestamp,Account,exog=None):
        args = {
        'type':'market',
        'size':self.RiskManagement.order_size(Account),
        'strike_price':spot_price,
        'stop_loss':0.001,
        'take_profit':0.001
        }
        return self.__random_decision(), args
    
    # TO DO: check exog variable usage later
    def long_open(self,spot_price,timestamp,Account,exog=None):
        decision, args = self.__long_open(spot_price=spot_price,
                                          timestamp=timestamp,
                                          Account=Account,
                                          exog=exog)
        return self.postprocess(decision, args)
    
    def short_open(self,spot_price,timestamp,Account,exog=None):
        if exog is not None:
            exog = self.preprocess()
        decision, args = self.__short_open(spot_price=spot_price,
                                           Account=Account,
                                           timestamp=timestamp,
                                           exog=exog)
        return self.postprocess(decision, args)
    
    def long_modify(self,order,spot_price,Account,exog=None):
        "Set attributes, and check order's state to track the performance."
        return order
    
    def short_modify(self,order,spot_price,Account,exog=None):
        return order
    
    def long_close(self,order,spot_price,Account,exog=None):
        if order.position != 'long':
            ValueError(f'Position is expected to be long, got {order.position}')
        return self.__random_decision()

    def short_close(self,order,spot_price,Account,exog=None):
        if order.position != 'short':
            ValueError(f'Position is expected to be short, got {order.position}')
        return self.__random_decision()


class RiskManagement:
    "Apply risk management and order sizing methods."
    def __init__(self,size_min=0.01,size_max=50,digits=2):
        self.size_min = size_min
        self.size_max = size_max
        self.digits = digits

    def _order_size(self,Account,exog=None):
        return np.random.uniform(0,Account.balance/1000,1)[0]
    
    def postprocess(self,size):
        if size > self.size_max:
            size = self.size_max
        elif size < self.size_min:
            size = self.size_min
        return round(size,self.digits)
    
    def order_size(self,Account,exog=None):
        size = self._order_size(Account=Account,exog=exog)
        return self.postprocess(size)


class KellyCriterion(RiskManagement):
    def __init__(self,n=10,default_lots=0.1,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.n = 10
        self.default_lots = default_lots

    def _order_size(self,Account,exog=None):
        if Account.n_inactive_orders < self.n:
            return self.default_lots
        else:
            last_n_orders = list(Account.inactive_orders.values())[-self.n:]
            stats = np.array([[order.profit,order.size] for order in last_n_orders])
            p_lose = np.sum(stats[:,0] < 0)/self.n
            p_win = 1 - p_lose
            ave_size = np.mean(stats[:,1])
            ave_profit = np.mean(stats[:,0])
            return p_win - (p_lose/(ave_profit-ave_size))


# TO DO: Make also time-driven
# TO DO: Enable parallel computation
# TO DO: bring oninit and ondeinit back to life later
# TO DO: logging for transactions
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
        #iterator = pb(data) if exog is None else pb(zip(data,exog))
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


class GridSearch:
    def __init__(self):
        pass


if __name__ == '__main__':
    # dummy data
    price = np.exp(np.cumsum(np.random.laplace(0,0.02,100000)))
    date_start = pd.to_datetime('2017-10-21 00:00:00')
    date_end = date_start + (pd.Timedelta('1min')*(price.shape[0]-1))
    ts = pd.date_range(date_start,date_end,freq='1min')
    df = pd.DataFrame({'timestamp':ts,'price':price})


    # simulate a single strategy
    account = Account(balance=1000)
    risk_management = KellyCriterion(n=20)
    strategy = Strategy(RiskManagement=risk_management,id=23030,name='noise_trader')
    tester = BackTest(account,strategy)
    tester.run(df.values)

    # # simulate a portfolio composed of two different strategies
    # account = Account(balance=1000)
    # strategy_1 = Strategy(RiskManagement=RiskManagement(),id=23031,name='noise_trader_1')
    # strategy_2 = Strategy(RiskManagement=RiskManagement(),id=23032,name='noise_trader_2')
    # tester = BackTest(account,[strategy_1,strategy_2])
    # tester.run(df.values)
