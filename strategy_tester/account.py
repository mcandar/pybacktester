# TO DO: add NAV
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

class ECN(Account):
    def __init__(self):
        pass

class STP(Account):
    def __init__(self):
        pass