from strategy_tester.utils import generate_id

# TODO: implement asset-to-balance currency conversion (assume USD account convert anything to USD) (write inside GETTER-SETTER?, every asset must have USD counterpart)
# TODO: implement dynamic slippage and spread
# TODO: implement bid,ask,spread
# TODO: Implement swap costs
class Asset:
    "Base financial instrument class that includes all common properties."
    def __init__(self,data,spread=1e-4,commissions=0,lot_units=1000,type='Main',name='Base'):
        self.data = data
        self.spread = spread
        self.commissions = commissions
        self.lot_units = lot_units
        self.type = type
        self.name = name
        self.id = generate_id(prefix=self.name,digits=4,timestamp=False)
        self.registered = []
        self.n_registered = 0
    
    def reset(self):
        self.__init__()

    def register(self,*strategies):
        n = len(strategies)
        self.n_registered += n
        for strategy in strategies:
            strategy.on.append(self.id)
            self.registered.append(strategy.id)
        return strategies if n > 1 else strategies[0]


class Currency(Asset):
    "Currency class."
    def __init__(self,data,base,quote,spread=1e-4,commissions=0,swap=0,lot_units=1000,type='Currency',name='Base',*args,**kwargs):
        super().__init__(data=data,spread=spread,commissions=commissions,lot_units=lot_units,type=type,name=name,*args,**kwargs)
        self.base = base
        self.quote = quote
        self.swap = swap
    
class EURUSD(Currency):
    def __init__(self,*args,**kwargs):
        super().__init__(base='EUR',quote='USD',type='Currency',name='EURUSD',*args,**kwargs)

class GBPUSD(Currency):
    def __init__(self,*args,**kwargs):
        super().__init__(base='GBP',quote='USD',type='Currency',name='GBPUSD',*args,**kwargs)


class Stock(Asset):
    def __init__(self,data,short_name,spread=1e-4,commissions=0,lot_units=1,type='Stock',name='Base',*args,**kwargs):
        super().__init__(data=data,spread=spread,commissions=commissions,lot_units=lot_units,type=type,name=name,*args,**kwargs)
        self.data = data
        self.short_name = short_name

class AAPL(Stock):
    def __init__(self,*args,**kwargs):
        super().__init__(type='Stock',name='Apple',short_name='AAPL',*args,**kwargs)


class ETF:
    def __init__(self):
        pass


class Option:
    def __init__(self):
        pass


class Portfolio:
    def __init__(self):
        pass


class Market:
    def __init__(self):
        self._info = 'dummy'