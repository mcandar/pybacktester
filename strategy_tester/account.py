from datetime import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from strategy_tester.utils import error_logger, transaction_logger

# TODO: add balance currency (or change other classes assuming that this will always be USD)

error_log = error_logger()
transaction_log = transaction_logger()

class Account:
    """
    A generic class to manage the operations of a trading account, store data
    and monitor the status.

    Parameters
    ----------
    initial_balance : int, float
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
    balance : float
        Current balance value.
    free_margin : float
        Current free margin value.
    equity : float
        Current equity value.
    nav : float
        Current total net asset value.
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
    navs : list of float
        History of net asset values, recorded at each order update or close.
    
    See also
    --------
    Order() and BackTest() class, they are closely related to Account().

    Notes
    -----
    
    """
    def __init__(self,initial_balance=1000,leverage=100,margin_call_level=0.3,name=None,
                 id=None,round_digits=2,max_allowed_risk=None,max_n_orders=None):
        if initial_balance < 0:
            error_log.error('Argument `initial_balance` cannot be less than zero.')
            raise ValueError('Argument `initial_balance` cannot be less than zero.')
        self.__initial_balance = initial_balance
        self.leverage = leverage
        self.margin_call_level = margin_call_level
        self.__name = name
        self.__id = id
        self.round_digits = round_digits
        self.max_allowed_risk = max_allowed_risk
        self.max_n_orders = max_n_orders
        self.currency = 'USD'

        self.is_blown = False
        self.__i = 0
        self.active_orders = {}
        self.inactive_orders = {}
        self.n_active_orders = 0
        self.n_inactive_orders = 0
        self.time = []
        self.time_ticker = []
        self.fresh_start = True
        self.n_processed_tickers = 0
        self.max_n_active_orders = 0

        self.__balance = initial_balance
        self.__balances = []
        self.__free_margin = initial_balance
        self.__free_margins = []
        self.__equity = initial_balance
        self.__equities = []
        self.__nav = 0
        self.__navs = []
        transaction_log.info('Account is initialized.')
    
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
    
    @property
    def balances(self):
        return pd.DataFrame(self.__balances,columns=['timestamp','balance'])
    
    @balances.setter
    def balances(self,value):
        self.__balances.append(value)
    
    @balances.getter
    def balances(self):
        return pd.DataFrame(self.__balances,columns=['timestamp','balance'])

    @property
    def balance(self):
        return self.__balance
    
    @balance.setter
    def balance(self,value):
        self.__balance = value
    
    @balance.getter
    def balance(self):
        return self.__balance

    @property
    def free_margins(self):
        return pd.DataFrame(self.__free_margins,columns=['timestamp','free_margin'])
    
    @free_margins.setter
    def free_margins(self,value):
        self.__free_margins.append(value)
    
    @free_margins.getter
    def free_margins(self):
        return pd.DataFrame(self.__free_margins,columns=['timestamp','free_margin'])

    @property
    def free_margin(self):
        return self.__free_margin
    
    @free_margin.setter
    def free_margin(self,value):
        self.__free_margin = value
    
    @free_margin.getter
    def free_margin(self):
        return self.__free_margin

    @property
    def equities(self):
        return pd.DataFrame(self.__equities,columns=['timestamp','equity'])
    
    @equities.setter
    def equities(self,value):
        self.__equities.append(value)
    
    @equities.getter
    def equities(self):
        return pd.DataFrame(self.__equities,columns=['timestamp','equity'])

    @property
    def equity(self):
        return self.__equity
    
    @equity.setter
    def equity(self,value):
        self.__equity = value
    
    @equity.getter
    def equity(self):
        return self.__equity
    
    @property
    def navs(self):
        return pd.DataFrame(self.__navs,columns=['timestamp','nav'])
    
    @navs.setter
    def navs(self,value):
        self.__navs.append(value)
    
    @navs.getter
    def navs(self):
        return pd.DataFrame(self.__navs,columns=['timestamp','nav'])

    @property
    def nav(self):
        return self.__nav
    
    @nav.setter
    def nav(self,value):
        self.__nav = value
    
    @nav.getter
    def nav(self):
        return self.__nav
    
    def tear_down(self,first_timestamp,last_timestamp,run_start):
        self.time.append({'start':run_start,'end':dt.utcnow()})
        self.time_ticker.append({'start':first_timestamp,'end':last_timestamp})
        self.close_all_orders(last_timestamp)
        self.fresh_start = False
        return self
    
    def __append(self,timestamp,balance=None,free_margin=None,equity=None,nav=None):
        if balance is not None:
            self.balances = timestamp, balance
        if free_margin is not None:
            self.free_margins = timestamp, free_margin
        if equity is not None:
            self.equities = timestamp, equity
        if nav is not None:
            self.navs = timestamp, nav
        return self
    
    def __place_order(self,order,timestamp):
        if self.free_margin >= order.margin:
            if self.max_allowed_risk is not None:
                if self.balance - self.free_margin < self.balance*self.max_allowed_risk: ## <------------ check later
                    transaction_log.error('Cannot place order as the risk limit reached.')
                    return False
        else:
            transaction_log.error('Cannot place order due to insufficient free margin.')
            return False
        if self.max_n_orders is not None and self.n_active_orders > self.max_n_orders:
            transaction_log.error('Cannot place order as the number of open orders limit reached.')
            return False
        self.active_orders[f'order_{self.__i}'] = order
        self.__i += 1
        self.equity += order.profit
        self.nav += order.margin
        self.free_margin -= order.margin

        self.n_active_orders += 1
        transaction_log.transaction(f'Order {id} is opened.')
        return True

    def place_order(self,orders,timestamp):
        for order in orders:
            self.__place_order(order=order,timestamp=timestamp)
        return self.__append(timestamp=timestamp,free_margin=self.free_margin,equity=self.equity,nav=self.nav)
    
    def __close_order(self,id,timestamp):
        tmp_order = self.active_orders[id].close(timestamp)
        del self.active_orders[id]
        self.inactive_orders[id] = tmp_order
        self.equity += tmp_order.profit
        self.balance += tmp_order.profit
        self.nav -= tmp_order.margin
        self.free_margin += tmp_order.margin
        self.n_active_orders -= 1
        self.n_inactive_orders += 1
        transaction_log.transaction(f'Order {id} is closed.')
        return self
    
    def close_all_orders(self,timestamp,ids=None):
        if ids is None:
            ids = list(self.active_orders.keys())
        else:
            if len(ids) == 0:
                error_log.error('Argument `ids` cannot be an empty list.')
                raise ValueError('Argument `ids` cannot be an empty list.')
        for id in ids:
            self.__close_order(id=id,timestamp=timestamp)
        return self.__append(timestamp=timestamp,balance=self.balance,free_margin=self.free_margin,equity=self.equity,nav=self.nav)
    
    def check_margin_call(self,timestamp):
        if self.equity <= self.margin_call_level*self.initial_balance:
            if self.n_active_orders > 0:
                transaction_log.warning('Stop out due to margin call.')
                self.close_all_orders(timestamp=timestamp)
        return self
    
    def __update_or_close(self,spot_price,timestamp):
        order_close_ids = []
        for id,order in self.active_orders.items():
            order.update(spot_price[order.asset_id],timestamp)
            if not order.is_active and not order.is_open: # closed due to TP, SL ### <----------- COULD THIS DELETE PENDING ORDERS???????
                order_close_ids.append(id)

        if len(order_close_ids) > 0:
            self.close_all_orders(timestamp=timestamp,ids=order_close_ids)
            
        return self
    
    def update(self,spot_price,timestamp):
        "Update account at each tick."
        self.is_blown = self.balance <= 0

        if not self.is_blown:
            if self.n_active_orders > 0:
                self.check_margin_call(timestamp).__update_or_close(spot_price,timestamp)
        else:
            transaction_log.critical('No remaining balance, account is blown.')

        if self.n_active_orders > self.max_n_active_orders:
            self.max_n_active_orders = self.n_active_orders
        self.n_processed_tickers += 1
        transaction_log.debug('Account is updated.')
        return self

    def __pprint(self):
        bal = pd.Series(self.balances['balance'],index=self.balances['timestamp'])
        fmarg = pd.Series(self.free_margins['free_margin'],index=self.free_margins['timestamp'])
        eqty = pd.Series(self.equities['equity'],index=self.equities['timestamp'])
        output = pd.concat([bal,fmarg,eqty],axis=1,join='outer')
        return output.ffill()
    
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
        df = self.__pprint()
        plt.plot(df['timestamp'],df['balance'],label='Balance')
        plt.plot(df['timestamp'],df['free_margin'],label='Free Margin')
        plt.plot(df['timestamp'],df['equity'],label='Equity')
        plt.title(f'Account ({self.name},{self.id}) Results')
        plt.legend()
        plt.show()


class ECN(Account):
    def __init__(self):
        pass

class STP(Account):
    def __init__(self):
        pass