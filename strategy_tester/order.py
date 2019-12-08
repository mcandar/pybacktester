from datetime import datetime as dt

class Order:
    """Keep track of an order, set TP, SL levels and store history. One can
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
    
    def pending_open(self,spot_price,timestamp,slippage=0):
        "Open a pending order."
        if self.is_active and not self.is_open:
            d = self.strike_price - spot_price
            if (self.position == 'long' and d <= 0) or (self.position == 'short' and d >= 0):
                self.is_open = True
                self.time['opened'] = dt.utcnow()
                self.time_ticker['opened'] = timestamp
                return True
        return False

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
            return self.pending_open(spot_price,timestamp)
        else:
            print('Cannot update an expired order.')
            return False