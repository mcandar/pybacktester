from strategy_tester.utils import generate_id

# TODO: implement asset-to-balance currency conversion (assume USD account convert anything to USD) (write inside GETTER-SETTER?, every asset must have USD counterpart)
# TODO: implement dynamic slippage and spread
# TODO: implement bid,ask,spread
# TODO: Implement swap costs
# class Asset:
#     "Base financial instrument class that includes all common properties."
#     def __init__(self,data,spread=1e-4,commissions=0,lot_units=1000,type='Main',name='Base'):
#         self.data = data
#         self.spread = spread
#         self.commissions = commissions
#         self.lot_units = lot_units
#         self.type = type
#         self.name = name
#         self.id = generate_id(prefix=self.name,digits=4,timestamp=False)
#         self.registered = []
#         self.n_registered = 0
    
#     def reset(self):
#         self.__init__()

#     def features(self):
#         output = vars(self).copy()
#         del output['data']
#         return output

#     def register(self,*strategies):
#         n = len(strategies)
#         self.n_registered += n
#         for strategy in strategies:
#             strategy.on.append(self.id)
#             self.registered.append(strategy.id)
#         return strategies if n > 1 else strategies[0]

# ## NEW IMPLEMENTATION
class Asset:
    "Base financial instrument class that includes all common properties."
    def __init__(self,price,spread=0,commissions=0,slippage=0,lot_units=1,type='Main',name='Base',base='NA',quote='NA',usd_converter=None):
        # dynamic
        self.price = price
        self.spread = [spread for _ in range(price.shape[0])] if isinstance(spread,(float,int)) else spread
        self.commissions = [commissions for _ in range(price.shape[0])] if isinstance(commissions,(float,int)) else commissions
        self.slippage = [slippage for _ in range(price.shape[0])] if isinstance(slippage,(float,int)) else slippage
        if quote.upper() != 'USD':
            if usd_converter is not None:
                self.usd_equivalent = self.price * usd_converter
            else:
                raise ValueError('Argument `usd_converter` cannot be None if quote is not USD.')

        # static
        self.base = base
        self.quote = quote
        self.lot_units = lot_units
        self.type = type
        self.name = name
        self.id = generate_id(prefix=self.name,digits=4,timestamp=False)
        self.registered = []
        self.n_registered = 0
    
    def reset(self):
        self.__init__()

    def features(self):
        output = vars(self).copy()
        del output['price'], output['spread'], output['commissions'], output['slippage'], output['usd_equivalent']
        return output

    def register(self,*strategies):
        n = len(strategies)
        self.n_registered += n
        for strategy in strategies:
            strategy.on.append(self.id)
            self.registered.append(strategy.id)
        return strategies if n > 1 else strategies[0]
    
    def data(self): -> list
        return [{'timestamp':t[0],'price':t[1],'spread':t[2],'commissions':t[3],'slippage':t[4],'usd_equivalent':t[5]} for t in zip(self.price[:,0],self.price[:,1],self.spread,self.commissions,self.slippage,self.usd_equivalent)]



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