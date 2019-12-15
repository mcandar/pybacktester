import numpy as np

# TO DO: create several built-in strategies
# TO DO: use a decorator to simplify methods?
class Strategy:
    """Open, modify, and close orders. By modification, we could keep a 
    number of variables, in order to track its performance and make decisions."""
    def __init__(self,RiskManagement,id=None,name=None):
        self.RiskManagement = RiskManagement
        self.id = id
        self.name = name
        self.on = []
    
    def check_registered_assets(self):
        if len(self.on) == 0:
            raise AttributeError('No asset is registered. Set target instrument(s) to use this strategy.')

    def include_identifiers(self,args):
        assets = args.keys()
        for asset_id in assets:
            args[asset_id]['params']['strategy_id'] = self.id
            args[asset_id]['params']['strategy_name'] = self.name
        return args
    
    def random_decision(self,p=0.01):
        return np.random.uniform(0,1,1)[0] < p    
    
    def preprocess(self,spot_price,timestamp,Account,RiskManagement,exog):
        "Preprocess exogenous variables."
        return exog
    
    def postprocess(self,args):
        "Last checks and corrections."
        if args is not None:
            args = self.include_identifiers(args)
        return args
    
    def long_open(self,spot_price,timestamp,Account,exog=None):
        exog = self.preprocess(spot_price,timestamp,Account,self.RiskManagement,exog)
        args = self.decide_long_open(spot_price=spot_price,
                                     timestamp=timestamp,
                                     Account=Account,
                                     exog=exog)
        return self.postprocess(args)
    
    def short_open(self,spot_price,timestamp,Account,exog=None):
        exog = self.preprocess(spot_price,timestamp,Account,self.RiskManagement,exog)
        args = self.decide_short_open(spot_price=spot_price,
                                      Account=Account,
                                      timestamp=timestamp,
                                      exog=exog)
        return self.postprocess(args)
    
    def long_modify(self,order,spot_price,Account,exog=None):
        "Set attributes, and check order's state to track the performance."
        return order
    
    def short_modify(self,order,spot_price,Account,exog=None):
        return order
    
    def long_close(self,order,spot_price,timestamp,Account,exog=None):
        if order.position != 'long':
            AttributeError(f'Position is expected to be long, got {order.position}')
        exog = self.preprocess(spot_price,timestamp,Account,self.RiskManagement,exog)
        return self.decide_long_close(order=order,
                                      spot_price=spot_price,
                                      timestamp=timestamp,
                                      Account=Account,
                                      exog=exog)

    def short_close(self,order,spot_price,timestamp,Account,exog=None):
        if order.position != 'short':
            AttributeError(f'Position is expected to be short, got {order.position}')
        exog = self.preprocess(spot_price,timestamp,Account,self.RiskManagement,exog)
        return self.decide_short_close(order=order,
                                       spot_price=spot_price,
                                       timestamp=timestamp,
                                       Account=Account,
                                       exog=exog)

    def decide_long_open(self,spot_price,timestamp,Account,exog):
        output = {}
        for asset_id in self.on:
            if asset_id in spot_price.keys():
                args = {
                    'type':'market',
                    'size':self.RiskManagement.order_size(Account),
                    'strike_price':spot_price[asset_id],
                    'stop_loss':0.001,
                    'take_profit':0.001
                }
                output[asset_id] = {'decision':self.random_decision(),'params':args}
        return output

    def decide_short_open(self,spot_price,timestamp,Account,exog):
        output = {}
        for asset_id in self.on:
            if asset_id in spot_price.keys():
                args = {
                    'type':'market',
                    'size':self.RiskManagement.order_size(Account),
                    'strike_price':spot_price[asset_id],
                    'stop_loss':0.001,
                    'take_profit':0.001
                }
                output[asset_id] = {'decision':self.random_decision(),'params':args}
        return output

    def decide_long_close(self,order,spot_price,timestamp,Account,exog):
        return self.random_decision()
    
    def decide_short_close(self,order,spot_price,timestamp,Account,exog):
        return self.random_decision()


class MACross(Strategy):
    def decide_long_open(self,spot_price,timestamp,Account,exog):
        "Exog[0]: Slow MA, Exog[1]: Fast MA"
        output = {}
        for asset_id in self.on:
            if asset_id in spot_price.keys():
                args = {
                    'type':'market',
                    'size':self.RiskManagement.order_size(Account),
                    'strike_price':spot_price[asset_id],
                    'stop_loss':None,
                    'take_profit':None
                }
                output[asset_id] = {'decision':exog[0] > exog[1],
                               'params':args}
        return output

    def decide_short_open(self,spot_price,timestamp,Account,exog):
        "Exog[0]: Slow MA, Exog[1]: Fast MA"
        output = {}
        for asset_id in self.on:
            if asset_id in spot_price.keys():
                args = {
                    'type':'market',
                    'size':self.RiskManagement.order_size(Account),
                    'strike_price':spot_price[asset_id],
                    'stop_loss':None,
                    'take_profit':None
                }
                output[asset_id] = {'decision':exog[0] < exog[1],
                               'params':args}
        return output
    
    def decide_long_close(self,order,spot_price,timestamp,Account,exog):
        return exog[0] < exog[1]
    
    def decide_short_close(self,order,spot_price,timestamp,Account,exog):
        return exog[0] > exog[1]