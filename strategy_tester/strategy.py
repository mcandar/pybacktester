import numpy as np

# TO DO: create several built-in strategies
# TO DO: edit this class to be a generic super class (make inheritable)
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
        for aid in assets:
            args[aid]['params']['strategy_id'] = self.id
            args[aid]['params']['strategy_name'] = self.name
        return args
    
    def random_decision(self,p=0.01):
        return np.random.uniform(0,1,1)[0] < p    
    
    def preprocess(self,spot_price,timestamp,Account,RiskManagement,exog=None):
        "Preprocess exogenous variables."
        return exog
    
    def postprocess(self,args):
        "Last checks and corrections."
        args = self.include_identifiers(args)
        return args

    def decide_long_open(self,spot_price,timestamp,Account,exog=None):
        output = {}
        for aid in self.on:
            if aid in spot_price.keys():
                args = {
                    'type':'market',
                    'size':self.RiskManagement.order_size(Account),
                    'strike_price':spot_price[aid],
                    'stop_loss':0.001,
                    'take_profit':0.001
                }
                output[aid] = {'decision':self.random_decision(),'params':args}
        return output

    def decide_short_open(self,spot_price,timestamp,Account,exog=None):
        output = {}
        for aid in self.on:
            if aid in spot_price.keys():
                args = {
                    'type':'market',
                    'size':self.RiskManagement.order_size(Account),
                    'strike_price':spot_price[aid],
                    'stop_loss':0.001,
                    'take_profit':0.001
                }
                output[aid] = {'decision':self.random_decision(),'params':args}
        return output
    
    # TO DO: check exog variable usage later
    def long_open(self,spot_price,timestamp,Account,exog=None):
        if exog is not None:
            exog = self.preprocess(spot_price,timestamp,Account,self.RiskManagement,exog)
        args = self.decide_long_open(spot_price=spot_price,
                                    timestamp=timestamp,
                                    Account=Account,
                                    exog=exog)
        return self.postprocess(args)
    
    def short_open(self,spot_price,timestamp,Account,exog=None):
        if exog is not None:
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
    
    def long_close(self,order,spot_price,Account,exog=None):
        if order.position != 'long':
            ValueError(f'Position is expected to be long, got {order.position}')
        return self.random_decision()

    def short_close(self,order,spot_price,Account,exog=None):
        if order.position != 'short':
            ValueError(f'Position is expected to be short, got {order.position}')
        return self.random_decision()