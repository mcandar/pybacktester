class Currency:
    def __init__(self,data,base,quote,spread=1e-4,commissions=0,lot_units=1000):
        self.data = data
        self.base = base
        self.quote = quote
        self.spread = spread
        self.commissions = commissions
        self.lot_units = lot_units
    
class EURUSD(Currency):
    def __init__(self,*args,**kwargs):
        super().__init__(base='EUR',quote='USD',*args,**kwargs)

class GBPUSD(Currency):
    def __init__(self,*args,**kwargs):
        super().__init__(base='GBP',quote='USD',*args,**kwargs)


class Stock:
    def __init__(self,data,short_name,lot_units=1):
        self.data = data
        self.short_name = short_name
        self.lot_units = lot_units


class ETF:
    def __init__(self):
        pass


class Option:
    def __init__(self):
        pass
