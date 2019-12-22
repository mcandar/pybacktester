# TODO: add NAV
# TODO: add balance currency
# TODO: add visualization, plotting
# TODO: add describe or summarize method
# TODO: write a setter method for balance, free_margin euqity? (to simplify appending each time)
# TODO: add logging for orders?
# TODO: add logging for failures?
from datetime import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

class Account:
    """
    A generic class to manage the operations of a trading account, store data
    and monitor the status.

    Parameters
    ----------
    balance : int, float
        Initial value of the balance.
    leverage : int, float
        Leverage amount of the account for trading.
    margin_call_level : int, float between [0,1)
        The ratio of initial balance to apply stop-out.
    name : str
        Name of the account, or the owner.
    id : int, float, str
        Unique identifier of the account.
    round_digits : int
        Number of digits for rounding the historical data
    max_allowed_risk : float between (0,1)
        Maximum allowed total ratio of the balance to risk, at any time.
    max_n_orders : int
        Maximum allowed number of open orders, at any time.
    
    Attributes
    ----------
    equity : int, float
        Current equity value.
    is_blown : bool
        True if the current balance is <= 0.
    active_orders : dict of `Order()`
        Dict of currently opened orders.
    inactive_orders : dict of `Order()`
        Dict of past (closed, expired, deleted) orders.
    n_active_orders : int
        Number of open orders at the moment.
    n_inactive_orders : int
        Number of past (closed, expired, deleted) orders.
    time : list of dict
        UTC time that the Account is used in a backtest.
    time_ticker : list of dict
        Received ticker time that the Account is used in a backtest.
    fresh_start : bool
        True if the Account has never seen a backtest.
    n_processed_tickers : int
        The total number of tickers that the Account has ever processed.
    balances : list of float
        History of balance values, recorded at each order close.
    free_margins : list of float
        History of free margin values, recorded at each order update or close.
    equities : list of float
        History of equity values, recorded at each order update or close.
    
    See also
    --------
    Order() and BackTest() class, they are closely related to Account().

    Notes
    -----
    
    """
    def __init__(self,initial_balance=1000,leverage=100,margin_call_level=0.3,name=None,id=None,round_digits=2,max_allowed_risk=None,max_n_orders=None):
        self.__initial_balance = initial_balance
        self.balance = initial_balance
        self.free_margin = initial_balance
        self.leverage = leverage
        self.margin_call_level = margin_call_level # TO DO: check margin call calculation later
        self.__name = name
        self.__id = id
        self.round_digits = round_digits
        self.max_allowed_risk = max_allowed_risk
        self.max_n_orders = max_n_orders

        self.equity = 0
        self.is_blown = False
        self.__i = 0
        self.active_orders = {}
        self.inactive_orders = {}
        self.n_active_orders = 0
        self.n_inactive_orders = 0
        self.time = [{'start':None,'end':None}]
        self.time_ticker = [{'start':None,'end':None}]
        self.fresh_start = True
        self.n_processed_tickers = 0

        self.balances = []
        self.free_margins = []
        self.equities = []
    
    @property
    def initial_balance(self):
        return self.__initial_balance
    
    @property
    def name(self):
        return self.__name
    
    @property
    def id(self):
        return self.__id
    
    def reset(self):
        self.__init__()
    
    def __append(self,timestamp,balance=None,free_margin=None,equity=None):
        if timestamp == []:
            raise ValueError('timestamp cannot be an empty list.')
        if balance is not None:
            self.balances.append((timestamp,balance))
        if free_margin is not None:
            self.free_margins.append((timestamp,free_margin))
        if equity is not None:
            self.equities.append((timestamp,equity))
        return self
    
    def tear_down(self,first_timestamp,last_timestamp,run_start):
        self.time.append({'start':run_start,'end':dt.utcnow()})
        self.time_ticker.append({'start':first_timestamp,'end':last_timestamp})
        self.close_all_orders(last_timestamp)
        self.fresh_start = False
        return self
    
    def place_order(self,order,timestamp):
        if self.free_margin >= order.margin:
            if self.max_allowed_risk is not None:
                if self.free_margin >= self.balance - self.balance*self.max_allowed_risk:
                    self.free_margin -= order.margin
                else:
                    #print('Cannot place order as the risk limit reached.')
                    return self
            else:
                self.free_margin -= order.margin
        else:
            #print('Cannot place order due to insufficient free margin.')
            return self
        
        if self.max_n_orders is not None and self.n_active_orders > self.max_n_orders:
            #print('Cannot place order as the number of open orders limit reached.')
            return self

        self.active_orders[f'order_{self.__i}'] = order
        self.__i += 1
        self.equity += order.margin

        self.n_active_orders += 1
        return self.__append(timestamp=timestamp,free_margin=self.free_margin,equity=self.equity)
    
    def close_order(self,id,timestamp):
        tmp_order = self.active_orders[id].close(timestamp)
        del self.active_orders[id]
        self.inactive_orders[id] = tmp_order

        self.free_margin += round(tmp_order.margin,self.round_digits)
        self.equity -= round(tmp_order.margin,self.round_digits)
        self.balance += round(tmp_order.profit,self.round_digits)
        self.n_active_orders -= 1
        self.n_inactive_orders += 1
        return self.__append(timestamp=timestamp,free_margin=self.free_margin,equity=self.equity,balance=self.balance)
    
    def close_all_orders(self,timestamp,ids=None):
        ids = list(self.active_orders.keys()) if ids is None else ids
        for id in ids:
            self.close_order(id=id,timestamp=timestamp)
        return self
    
    def check_margin_call(self,timestamp):
        if self.free_margin+self.equity <= self.margin_call_level*self.initial_balance:
            self.close_all_orders(timestamp=timestamp)
        return self
    
    def __update_or_close(self,spot_price,timestamp):
        order_close_ids = []
        for id,order in self.active_orders.items():
            order.update(spot_price[order.asset_id],timestamp) # <------- TODO: correct balance (and NAV) calculation
            if not order.is_active and not order.is_open: # closed due to TP, SL
                order_close_ids.append(id)
            elif order.is_active and order.is_open:
                self.equity -= order.margin
                self.__append(timestamp=timestamp,equity=self.equity)
        
        return self.close_all_orders(timestamp=timestamp,ids=order_close_ids)
    
    def update(self,spot_price,timestamp):
        "Use at each tick."
        self.is_blown = self.balance <= 0

        if not self.is_blown:
            if self.n_active_orders > 0:
                self.check_margin_call(timestamp).__update_or_close(spot_price,timestamp)

        self.n_processed_tickers += 1
        return self
    
    def __past_info(self):
        return np.array(self.balances), np.array(self.free_margins), np.array(self.equities)

    def __pprint(self):
        bal, fmarg, eqty = self.__past_info()
        bal = pd.DataFrame(bal[:,1],index=bal[:,0],columns=['balance'])
        fmarg = pd.DataFrame(fmarg[:,1],index=fmarg[:,0],columns=['free_margin'])
        eqty = pd.DataFrame(eqty[:,1],index=eqty[:,0],columns=['equity'])
        return pd.concat([bal,fmarg,eqty],axis=1)
    
    def __repr__(self):
        if self.n_inactive_orders == 0:
            return 'No order history found.'
        else:
            return self.__pprint().__repr__()

    def __str__(self):
        if self.n_inactive_orders == 0:
            return 'No order history found.'
        else:
            return self.__pprint().__str__()
    
    def plot_results(self):
        bal, fmarg, eqty = self.__past_info()
        plt.plot(bal[:,0],bal[:,1],label='Balance')
        plt.plot(fmarg[:,0],fmarg[:,1],label='Free Margin')
        plt.plot(eqty[:,0],eqty[:,1],label='Equity')
        plt.title(f'Account ({self.name},{self.id}) Results')
        plt.legend()
        plt.show()


class ECN(Account):
    def __init__(self):
        pass

class STP(Account):
    def __init__(self):
        pass